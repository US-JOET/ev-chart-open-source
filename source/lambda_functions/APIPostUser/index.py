"""
APIPostUser

Takes the provided user information from the frontend, validates it, and then creates a new user for
the provided organization.
"""
import datetime
import json

from boto3.dynamodb.conditions import Attr
from dateutil import tz
from email_handler import trigger_email, validate_email_address_format
from email_handler.email_enums import Email_Template
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseDynamoDuplicateItemError,
    EvChartDatabaseDynamoQueryError,
    EvChartEmailError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedBodyError,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService, feature_enablement_check
from feature_toggle.feature_enums import Feature
from user_enums import Roles


@SessionManager.check_session()
@feature_enablement_check(Feature.ADD_USER)
def handler(event, _context):
    dynamodb = boto3_manager.resource("dynamodb")
    output = ""

    try:
        log_event = LogEvent(event=event, api="APIPostUser", action_type="write")
        if not log_event.is_auth_token_valid():
            raise EvChartAuthorizationTokenInvalidError()
        auth_token = log_event.get_auth_token()
        org_id = auth_token.get("org_id")

        feature_toggle_service = FeatureToggleService()
        new_user_info = json.loads(event["body"])
        is_valid_body(new_user_info, org_id)
        # After verifying email field exists, strip spaces
        new_user_info["email"] = new_user_info["email"].strip()
        validate_email_address_format(new_user_info["email"], log_event)
        if user_does_not_exist(new_user_info, dynamodb):
            if add_new_user(new_user_info, dynamodb):
                output = "Successfully added new user into DynamoDB table."
        else:
            email = new_user_info["email"]
            reactivate_user(email, dynamodb)

        # Send email as long as user has been created or updated
        if (
                feature_toggle_service.get_feature_toggle_by_enum(
                    Feature.NEW_USER_EMAIL, log_event
                )
                == "True"
            ):
                send_new_user_email(new_user_info)

    except (
        EvChartAuthorizationTokenInvalidError,
        EvChartMissingOrMalformedBodyError,
        EvChartDatabaseDynamoQueryError,
        EvChartDatabaseDynamoDuplicateItemError,
        EvChartUserNotAuthorizedError,
        EvChartJsonOutputError,
        EvChartEmailError,
    ) as err:
        log_event.log_custom_exception(
            message=err.message, status_code=err.status_code, log_level=err.log_level
        )
        return_obj = err.get_error_obj()

    else:
        log_event.log_successful_request(message="Success post user", status_code=201)
        return_obj = {
            "statusCode": 201,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(output),
        }

    return return_obj


# helper function that returns True if all required body parameters were passed in
def is_valid_body(new_user_info, org_id):
    required_parameters = {"org_name", "org_id", "first_name", "last_name", "email", "role"}
    parameter_count = 0
    for key in new_user_info.keys():
        if key in required_parameters:
            parameter_count += 1

    if parameter_count != len(required_parameters):
        raise EvChartMissingOrMalformedBodyError(
            message="Not all required parameters were passed in."
        )

    if new_user_info["role"] not in ["viewer", "admin"]:
        raise EvChartMissingOrMalformedBodyError(message="Malformed data in role")

    if new_user_info["org_id"] != org_id:
        raise EvChartMissingOrMalformedBodyError(message="Malformed data in org_id")

    return True


# helper function that returns True if user's email is not in the users table,
# throws an error if user exists
def user_does_not_exist(new_user_info, dynamodb):
    email = new_user_info.get("email")

    # TODO changing this to use get_user_info_dynamo will cause unit tests for
    #      APIUpdateAccountStatus to break.  May require unit test refactor.

    evchart_users_table = dynamodb.Table("ev-chart_users")
    response = evchart_users_table.scan(FilterExpression=Attr("identifier").eq(email.lower()))

    # if user is not in the table (no items were returned from the get call), return false
    if response.get("Count") == 0:
        return True
    if response["Items"][0]["account_status"] in ["Deactivated", "Expired", "Removed"]:
        return False
    # if user is in the table, throw an error because this means there is a duplicate.
    # user exists arleady

    error_message = f"Existing email: {email.lower()} already in DynamoDB."
    raise EvChartDatabaseDynamoDuplicateItemError(message=error_message)


# helper function that inserts the user info into dynamo db table
def add_new_user(new_user_info, dynamodb):
    account_created = str(datetime.datetime.now(tz.gettz("UTC")))
    status = "Pending"

    try:
        evchart_users_table = dynamodb.Table("ev-chart_users")
        response = evchart_users_table.put_item(
            Item={
                "identifier": new_user_info.get("email").lower(),
                "account_status": status,
                "first_name": new_user_info.get("first_name"),
                "last_generated": account_created,
                "last_name": new_user_info.get("last_name"),
                "org_id": new_user_info.get("org_id"),
                "role": new_user_info.get("role"),
            }
        )
    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(
            message="Error inserting new user into dynamo db Users table."
        ) from e

    if response is None:
        raise EvChartUserNotAuthorizedError(
            message="Current organization not authorized to add a user"
        )

    if response is not None:
        return True


def reactivate_user(user_email, dynamodb):
    try:
        account_added = str(datetime.datetime.now(tz.gettz("UTC")))

        evchart_users_table = dynamodb.Table("ev-chart_users")
        response = evchart_users_table.update_item(
            Key={"identifier": user_email.lower()},
            UpdateExpression="set account_status=:o, last_generated=:l",
            ExpressionAttributeValues={":o": "Pending", ":l": account_added},
            ReturnValues="UPDATED_NEW",
        )
        if response is None:
            raise EvChartDatabaseDynamoQueryError(message="Error querying Dynamo DB.")

        if response is not None:
            return True

    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(
            message="Error inserting new user into dynamo db Users table."
        ) from e


@feature_enablement_check(Feature.NEW_USER_EMAIL)
def send_new_user_email(new_user_info):
    try:
        email_values = {}
        email_values["email_type"] = Email_Template.NEW_USER
        email_values["email"] = new_user_info["email"]
        email_values["first_name"] = new_user_info["first_name"]
        email_values["org_name"] = new_user_info["org_name"]
        email_values["role"] = Roles[new_user_info["role"]].value

        trigger_email(email_values)

    except Exception as err:
        raise EvChartJsonOutputError(
            message=f"Error formatting fields for email handler: {repr(err)}"
        ) from err
