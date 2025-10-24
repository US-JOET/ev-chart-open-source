"""
CognitoPreTokenGenTrigger

This function adds useful application-specific information to the JWT that is issued by Cognito.
It also will generate and update the user's session ID in DynamoDB to validate against the related
browser cookie.  Other updates to the user's DynamoDB entry include tracking the last time the JWT
was generated (used to determine inactivity) as well as ensuring the user's status is "Active".
"""
from datetime import datetime, UTC
import json
import logging
import os
import secrets

from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.cognito import cognito
import urllib3

dynamodb_resource = boto3_manager.resource("dynamodb")

if os.environ.get("NETWORKPROXY"):
    http = urllib3.ProxyManager(
        os.environ["NETWORKPROXY"],
        ca_certs=f"/opt{os.environ['NETWORKPROXYCERT']}" if os.environ.get("NETWORKPROXYCERT") else None
    )
else:
    http = urllib3.PoolManager()

logger = logging.getLogger("CognitoPreTokenGenTrigger")
logger.setLevel(logging.DEBUG)


def get_user_attributes(user_data):
    org_id = ""
    org_name = "Not Specified"
    org_type = ""
    org_friendly_id = ""

    account_status = user_data.get("account_status", "")
    if account_status not in ["Deactivated", "Expired", "Removed"]:
        org_id = user_data.get("org_id", "")
        if org_id:
            table = dynamodb_resource.Table("ev-chart_org")
            org_data = table.get_item(
                ExpressionAttributeNames={
                    "#n": "name"
                },
                Key={
                    "org_id": org_id
                },
                ProjectionExpression="#n, org_friendly_id, recipient_type"
            ).get("Item")

            org_name = org_data.get("name", "")
            org_type = org_data.get("recipient_type", "")
            org_friendly_id = org_data.get("org_friendly_id", "")

    preferred_name = ""
    if user_data.get("first_name") and user_data.get("last_name"):
        preferred_name = f"{user_data['first_name']} {user_data['last_name']}"

    role = user_data.get("role", "")
    role = "viewer" if role not in ["admin"] else role

    return {
        "id_token": {
            "account_status": account_status,
            "org_id": org_id,
            "org_friendly_id": org_friendly_id,
            "org_name": org_name,
            "preferred_name": preferred_name,
            "role": role,
            "scope": org_type
        },
        "access_token": {
            "role": role
        }
    }


def get_user_data(email):
    table = dynamodb_resource.Table("ev-chart_users")
    return table.get_item(
        ExpressionAttributeNames={
            "#r": "role"
        },
        Key={
            "identifier": email.lower()
        },
        ProjectionExpression="account_status, first_name, last_name, org_id, #r, refresh_token"
    ).get("Item")


def revoke_refresh_token(refresh_token):
    if not refresh_token:
        return

    cognito_response = http.request(
        "POST",
        (
            f"https://{cognito.domain}"
            f".auth-fips.{os.environ['AWS_REGION']}.amazoncognito.com/oauth2/revoke"
        ),
        body=f"token={refresh_token}",
        headers={
            "Authorization": f"Basic {cognito.get_basic_auth_string()}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )

    if cognito_response.status != 200:
        logger.debug(str(cognito_response.read()))


def set_user_details(email, session_id):
    table = dynamodb_resource.Table("ev-chart_users")
    table.update_item(
        ExpressionAttributeNames={
            "#TS": "last_generated",
            "#SID": "session_id",
            "#S": "account_status"
        },
        ExpressionAttributeValues={
            ":ts": str(datetime.now(UTC)),
            ":sid": session_id,
            ":s": "Active"
        },
        Key={
            "identifier": email.lower()
        },
        UpdateExpression="SET #TS = :ts, #SID = :sid, #S = :s"
    )


def handler(event, _context):
    log_data = {
        "request": event["request"]
    }

    event_user_attributes = event["request"]["userAttributes"]
    email = event_user_attributes["email"]
    user_full_name = event_user_attributes.get("name")

    try:
        user_data = get_user_data(email)
        user_attributes = get_user_attributes(user_data)

        log_data |= {
            "user_attributes": user_attributes,
            "user_data": {
                key: value
                for key, value in user_data.items() if key not in ["refresh_token"]
            }
        }

    except Exception as e: # pylint: disable=broad-exception-caught
        logger.debug(json.dumps(log_data | {"message": str(e)}))

    else:
        revoke_refresh_token(user_data.get("refresh_token"))

        session_id = secrets.token_urlsafe(32)
        if user_attributes["id_token"]["account_status"] in ["Active", "Pending"]:
            set_user_details(email, session_id)
            user_attributes["id_token"]["account_status"] = "Active"

        log_data |= {
            "session_id": session_id
        }

        user_names = {}
        if not event_user_attributes.get("given_name"):
            if user_data.get("first_name"):
                user_names["given_name"] = user_data["first_name"]
        if not event_user_attributes.get("family_name"):
            if user_data.get("last_name"):
                user_names["family_name"] = user_data["last_name"]

        id_token_add = {
            "idTokenGeneration": {
                "claimsToAddOrOverride": user_attributes["id_token"] | {
                    "session_id": session_id,
                } | user_names
            }
        }

        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_name = f"-{sub_environment}" if sub_environment else ""

        access_token_add = {
            "accessTokenGeneration": {
                "claimsToAddOrOverride": {
                    "account_status": user_attributes["id_token"]["account_status"],
                    "email": email,
                    "name": user_full_name or user_attributes["id_token"]["preferred_name"],
                    "org_id": user_attributes["id_token"]["org_id"],
                    "org_friendly_id": user_attributes["id_token"]["org_friendly_id"],
                    "org_name": user_attributes["id_token"]["org_name"],
                    # The "scope" claim is protected in the access_token context.
                    "org_type": user_attributes["id_token"]["scope"],
                    "role": user_attributes["access_token"].get("role", ""),
                    "session_id": session_id
                },
                "scopesToAdd": [
                    # The access_token "scope" claim is reserved purely for OIDC-related access
                    # contexts.
                    (
                        f"gov.driveelectric.evchart{sub_environment_name}"
                        f"/{user_attributes['access_token']['role']}"
                    )
                ] if user_attributes["access_token"]["role"] else []
            }
        }

        event["response"]["claimsAndScopeOverrideDetails"] = id_token_add | access_token_add

    logger.debug(json.dumps(log_data))
    return event
