"""
APIPatchUser

updates user based email and on action passed.
With this endpoint a user can be removed or re-invited by an org admin.
body
- email <string>
- action <string> "remove/reinvite"

returns
status 201/401/403/406/409/500
"""

import json
import logging
import re
from datetime import UTC, datetime

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import NoCredentialsError, ClientError
from email_handler import get_email_regex, trigger_email
from email_handler.email_enums import Email_Template
from evchart_helper.api_helper import get_user_info_dynamo
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseDynamoDuplicateItemError,
    EvChartDatabaseDynamoQueryError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedBodyError,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.session import SessionManager
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature
from user_enums import Roles

logger = logging.getLogger("APIPatchUser")
logger.setLevel(logging.INFO)


@SessionManager.check_session()
def handler(event, _context):
    dynamodb = boto3_manager.resource("dynamodb")
    output = ""

    try:
        log_event = LogEvent(event, api="APIPatchUser", action_type="Modfiy")
        if not log_event.is_auth_token_valid():
            raise EvChartAuthorizationTokenInvalidError()

        request_body = json.loads(event["body"])

        errors = is_valid_body(request_body)
        if len(errors) > 0:
            error_str = "\n".join(errors)
            raise EvChartMissingOrMalformedBodyError(message=f"Errors in body. {error_str}")

        claims = get_claims(event)
        if claims is None:
            raise EvChartUserNotAuthorizedError(message="missing claims")

        user_info = get_user_info(request_body)
        user_info["org_name"] = claims.get("org_name")
        check_permissions(claims, user_info)
        if user_info:
            action = request_body.get("action").lower()
            if action == "remove":
                if remove_user(request_body, dynamodb):
                    output = "Successfully removed user from DynamoDB table."
            if action == "reinvite":
                if reinvite_user(request_body, dynamodb):
                    email = request_body.get("email")
                    output = f"Successfully reinvited user {email}"
                    send_new_user_email(user_info)

    except (
        EvChartAuthorizationTokenInvalidError,
        EvChartMissingOrMalformedBodyError,
        EvChartDatabaseDynamoDuplicateItemError,
        EvChartDatabaseDynamoQueryError,
        EvChartUserNotAuthorizedError,
    ) as e:
        log_event.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
        )
        return_obj = e.get_error_obj()

    else:
        log_event.log_successful_request(message="Successfully removed user", status_code=201)
        return_obj = {
            "statusCode": 201,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(output),
        }

    logger.info(return_obj)
    return return_obj


# helper function that returns error list if an error is found an empty list if no errors exist
def is_valid_body(body):
    error_list = []
    if body.get("email") is None:
        error_list.append("Missing required field email in request body.")
    else:
        email = body.get("email")
        email_regex = get_email_regex()
        if re.fullmatch(email_regex, email) is None:
            error_list.append(f"The given email {email} is invalid.")
    if body.get("action") is None:
        error_list.append("Missing required field action in request body.")
    else:
        action = body.get("action").lower()
        if action not in ["remove", "reinvite"]:
            error_list.append(f"The given action {action} is invalid.")

    return error_list


def get_user_info(body):
    user_info = None
    email = body.get("email")
    user_info = get_user_info_dynamo(email)

    if user_info is None:
        error_message = f"Error, user doesn't exist: Email {email} not in DynamoDB."
        raise EvChartMissingOrMalformedBodyError(message=error_message)

    return user_info


# helper function that edits the user info in dynamo db table
def remove_user(user_info, dynamodb):
    account_removed = str(datetime.now(UTC))

    evchart_users_table = dynamodb.Table("ev-chart_users")
    response = evchart_users_table.update_item(
        Key={"identifier": user_info.get("email").lower()},
        UpdateExpression=(
            "set account_status=:o, last_generated=:l " "remove session_id, refresh_token"
        ),
        ExpressionAttributeValues={":o": "Removed", ":l": account_removed},
        ReturnValues="UPDATED_NEW",
    )

    if response is None:
        raise EvChartDatabaseDynamoQueryError(message="Error querying Dynamo DB.")

    return True


def reinvite_user(user_info, dynamodb):
    response = None
    try:
        reset_date = str(datetime.now(UTC))

        evchart_users_table = dynamodb.Table("ev-chart_users")
        response = evchart_users_table.update_item(
            Key={"identifier": user_info.get("email").lower()},
            UpdateExpression=(
                "set account_status=:o, last_generated=:l remove session_id, refresh_token"
            ),
            ConditionExpression=~Attr("account_status").is_in(["Active"]),
            ExpressionAttributeValues={":o": "Pending", ":l": reset_date},
            ReturnValues="UPDATED_NEW",
        )
        if response is None:
            raise EvChartDatabaseDynamoQueryError(message="Error querying Dynamo DB.")
    except NoCredentialsError as e:
        raise EvChartDatabaseDynamoQueryError(message="Error querying Dynamo DB.") from e
    except ClientError as e:
        if e.response['Error']['Code']=='ConditionalCheckFailedException':
            raise EvChartDatabaseDynamoQueryError(message="Error querying Dynamo DB.") from e

    return response


@feature_enablement_check(Feature.NEW_USER_EMAIL)
def send_new_user_email(user_info):
    try:
        email_values = {}
        email_values["email_type"] = Email_Template.NEW_USER
        email_values["email"] = user_info["identifier"]
        email_values["first_name"] = user_info["first_name"]
        email_values["org_name"] = user_info["org_name"]
        email_values["role"] = Roles[user_info["role"]].value

        trigger_email(email_values)

    except Exception as err:
        raise EvChartJsonOutputError(
            message=f"Error formatting fields for email handler: {repr(err)}"
        ) from err


def check_permissions(claims, user_info):
    if not claims.get("org_id") == user_info.get("org_id"):
        raise EvChartUserNotAuthorizedError()


def get_claims(event):
    claims = None
    if "claims" in event["requestContext"]["authorizer"]:
        claims = event["requestContext"]["authorizer"]["claims"]
    return claims
