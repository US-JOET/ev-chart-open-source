"""
APIToken

This function takes the one-time authentication code generated via Cognito after successful OIDC
login and gives it to the Cognito OIDC token endpoint to generate a JWT.  The session ID is also
retrieved from the subsequent token and set as a cookie in the response.
"""
import base64
import json
import hashlib
import hmac
import logging
import os

from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.cognito import cognito
import urllib3

cognito_client = boto3_manager.client("cognito-idp")
dynamodb_resource = boto3_manager.resource("dynamodb")
ssm_client = boto3_manager.client("ssm")
sts_client = boto3_manager.client("sts")

if os.environ.get("NETWORKPROXY"):
    http = urllib3.ProxyManager(
        os.environ["NETWORKPROXY"],
        ca_certs=f"/opt{os.environ['NETWORKPROXYCERT']}" if os.environ.get("NETWORKPROXYCERT") else None
    )
else:
    http = urllib3.PoolManager()

logger = logging.getLogger("APIToken")
logger.setLevel(logging.DEBUG)


def decode_id_token(id_token_jwt):
    payload = id_token_jwt.split(".")[1]
    payload_padded = payload + "=" * (4 - len(payload) % 4)
    id_token = base64.b64decode(payload_padded).decode("utf-8")

    return json.loads(id_token)


def update_user_refresh_token(email, refresh_token):
    try:
        table = dynamodb_resource.Table("ev-chart_users")
        table.update_item(
            ExpressionAttributeNames={
                "#RT": "refresh_token"
            },
            ExpressionAttributeValues={
                ":rt": refresh_token
            },
            Key={
                "identifier": email.lower()
            },
            UpdateExpression="SET #RT = :rt"
        )

    except Exception as e: # pylint: disable=broad-exception-caught
        logger.debug(str(e))


def valid_env_for_query_string_login():
    return sts_client.get_caller_identity()["Account"] in [
        "414275662771", #Dev
        "030628784534"  #Test
    ]


def handler(event, _context):
    log_data = {
        "headers": event.get("headers"),
        "query_string_params": list(event["queryStringParameters"].keys())
    }

    parameters = event["queryStringParameters"]

    query_code = parameters.get("code")
    query_refresh = parameters.get("refresh")
    query_username = parameters.get("username")
    query_password = parameters.get("password")

    response = {
        "body": json.dumps({
            "error": "invalid_request"
        }),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        },
        "statusCode": 400
    }

    if valid_env_for_query_string_login() and query_username and query_password:
        try:
            cognito_response = cognito_client.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "PASSWORD": query_password,
                    "SECRET_HASH": base64.b64encode(hmac.new(
                        bytes(cognito.client_secret, "utf-8"),
                        bytes(f"{query_username}{cognito.client_id}", "utf-8"),
                        digestmod=hashlib.sha256
                    ).digest()).decode(),
                    "USERNAME": query_username
                },
                ClientId=cognito.client_id
            ).get("AuthenticationResult")

        except Exception as e: # pylint: disable=broad-exception-caught
            logger.debug(json.dumps(log_data | {"message": str(e)}))

        else:
            mapped_response = {
                "access_token": cognito_response["AccessToken"],
                "expires_in": cognito_response["ExpiresIn"],
                "id_token": cognito_response["IdToken"],
                "refresh_token": cognito_response["RefreshToken"],
                "token_type": cognito_response["TokenType"]
            }

            response["body"] = json.dumps(mapped_response)
            response["statusCode"] = 200

    elif bool(query_code) ^ bool(query_refresh): # XOR here because both cannot be used
        request_body = "grant_type="
        if query_code:
            request_body = (
                f"{request_body}authorization_code&code={query_code}&"
                f"redirect_uri={cognito.callback_urls[0]}"
            )

        elif query_refresh:
            request_body = f"{request_body}refresh_token&refresh_token={query_refresh}"

        cognito_response = http.request(
            "POST",
            (
                f"https://{cognito.domain}"
                f".auth-fips.{os.environ['AWS_REGION']}.amazoncognito.com/oauth2/token"
            ),
            body=request_body,
            headers={
                "Authorization": f"Basic {cognito.get_basic_auth_string()}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        response = {
            "body": cognito_response.data,
            "headers": response["headers"] | dict(cognito_response.headers.items()),
            "statusCode": cognito_response.status
        }

    # The assumption here is that if the statusCode is 200 at this point, we have a valid login and
    # JWT, so we are able to pull the session id and store the refresh_token.
    if response["statusCode"] == 200:
        jwt = json.loads(response["body"])

        id_token = decode_id_token(jwt.get("id_token"))
        if id_token.get("scope"):
            update_user_refresh_token(id_token["email"], jwt.get("refresh_token"))

        log_data |= {
            "identifier": id_token["email"]
        }

        response["headers"] |= {
            "Set-Cookie": (
                f"__Host-session_id={id_token.get('session_id', '')}; "
                "Path=/; SameSite=Strict; Secure; HttpOnly"
            )
        }

    logger.debug(json.dumps(log_data))
    return response
