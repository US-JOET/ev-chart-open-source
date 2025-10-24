"""
APIPutSubmissionApproval

Updates the requested module submission to the Approved status after validating the provided
organization and user details, along with the current module status.  An email will be sent to the
relevant users indicating this status has changed.
"""
import json
import datetime
import logging
from dateutil import tz
from boto3.dynamodb.conditions import Key

from database_central_config import DatabaseCentralConfig
from feature_toggle.feature_enums import Feature
from feature_toggle import FeatureToggleService

from email_handler import trigger_email
from email_handler.email_enums import Email_Template

from evchart_helper import aurora
from evchart_helper.api_helper import execute_query, get_org_info_dynamo
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.module_enums import ModuleFrequencyProper, ModuleNames
from evchart_helper.session import SessionManager
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartMissingOrMalformedBodyError,
    EvChartInvalidDataError,
    EvChartDatabaseAuroraQueryError,
    EvChartUserNotAuthorizedError,
    EvChartJsonOutputError,
    EvChartDatabaseDynamoQueryError,
    EvChartEmailError
)

import_metadata = ModuleDataTables["Metadata"].value

logger = logging.getLogger("APIPutSubmissionApproval")
logger.setLevel(logging.DEBUG)


@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            feature_toggle_service = FeatureToggleService()
            log_event = LogEvent(
                event=event,
                api="APIPutSubmissionApproval",
                action_type="Modify")
            if not log_event.is_auth_token_valid():
                raise EvChartAuthorizationTokenInvalidError()
            token = log_event.get_auth_token()

            request_body = json.loads(event['body'])
            validate_recipient_type(token)
            validate_body(request_body)
            validate_submission_status(request_body['submission_status'])
            upload_info = validate_upload_id(
                request_body["upload_id"], cursor, token
            )

            set_submission_status(request_body, cursor, token)
            use_central_config = \
                feature_toggle_service.get_feature_toggle_by_enum(
                    Feature.DATABASE_CENTRAL_CONFIG, log_event
            ) == "True"

            if feature_toggle_service.get_feature_toggle_by_enum(
                Feature.DATA_APPROVAL_REJECTION_EMAIL, log_event
            ) == "True":
                send_submission_status_email(
                    token, request_body, upload_info, use_central_config
                )

        except (
            EvChartAuthorizationTokenInvalidError,
            EvChartMissingOrMalformedBodyError,
            EvChartInvalidDataError,
            EvChartDatabaseAuroraQueryError,
            EvChartUserNotAuthorizedError,
            EvChartJsonOutputError,
            EvChartDatabaseDynamoQueryError,
            EvChartEmailError
        ) as e:
            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()
        else:
            log_event.log_successful_request(
                message="Submission status successfully updated",
                status_code=200
            )
            return_obj = {
                'statusCode': 201,
                'headers': {"Access-Control-Allow-Origin": "*"},
                'body': json.dumps("Submission status successfully updated")
            }
        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


def validate_body(request_body):
    missing_fields = []
    req_headers = {"upload_id", "submission_status", "comments"}
    for key in req_headers:
        if key not in request_body:
            missing_fields.append(key)
        elif not key:
            missing_fields.append(key)
    if len(missing_fields) != 0:
        raise EvChartMissingOrMalformedBodyError(
            message=f"Missing or empty fields: {missing_fields}"
        )


def validate_submission_status(submission_status):
    valid_states = ["Approved", "Rejected"]
    if submission_status not in valid_states:
        raise EvChartInvalidDataError(
            message=(
                f"Submission status {submission_status} can only be "
                f"Approved or Rejected"
            )
        )


def validate_upload_id(upload_id, cursor, token):
    query = f"SELECT * from {import_metadata} WHERE upload_id=%s" # nosec - SQL injection not possible
    output = execute_query(
        query=query,
        data=(upload_id,),
        cursor=cursor,
        message="validate_upload_id"
    )
    if not output or output is None:
        raise EvChartInvalidDataError(
            message=f"Given upload_id {upload_id} does not exist"
        )

    upload_info = output[0]
    org_id = token.get("org_id")
    if upload_info.get('parent_org') != org_id:
        raise EvChartUserNotAuthorizedError(
            message=f"Org {org_id} is not authorized on upload {upload_id}"
        )

    return upload_info


def validate_recipient_type(token):
    recipient_type = token.get("recipient_type")

    if recipient_type != "direct-recipient":
        raise EvChartUserNotAuthorizedError(
            message=(
                "Only direct recipients are authorized to "
                "update submission status"
            )
        )


def set_submission_status(request_body, cursor, token):
    try:
        updates = {}
        updates["submission_status"] = request_body["submission_status"]
        updates["updated_by"] = token.get("email")
        updates["updated_on"] = str(datetime.datetime.now(tz.gettz("UTC")))
        updates["comments"] = request_body["comments"]
        updates["upload_id"] = request_body["upload_id"]
        query = f"""
                UPDATE {import_metadata}
                SET submission_status = %(submission_status)s,
                    updated_by = %(updated_by)s,
                    updated_on = %(updated_on)s,
                    comments = %(comments)s
                WHERE upload_id = %(upload_id)s
                """
        cursor.execute(query, updates)
    except Exception as err:
        logger.debug("exception prior to re-raise: %s", repr(err))
        raise EvChartDatabaseAuroraQueryError(
            message=(
                f"Error updating submission_status in "
                f"import_metadata: {err}"
            )
        ) from err


def get_user_info(user_email):
    try:
        dynamodb = boto3_manager.resource("dynamodb")

        table = dynamodb.Table("ev-chart_users")
        items = table.query(
            KeyConditionExpression=Key('identifier').eq(user_email.lower()),
        )
        response = items["Items"][0]
        return response
    except Exception as err:
        logger.debug("exception prior to re-raise: %s", repr(err))
        raise EvChartDatabaseDynamoQueryError(
            message=f"Error querying DynamoDB for users {user_email.lower()}: {err}"
        ) from err


def send_submission_status_email(
    token, request_body, upload_info, use_central_config=False
):
    try:
        dr_email = token.get("email")
        sr_email = upload_info.get("updated_by")
        sr_info = get_user_info(sr_email)
        dr_info = get_user_info(dr_email)
        sr_org_info = get_org_info_dynamo(upload_info.get("org_id"))

        email_values = {}
        email_values["email"] = sr_email
        email_values["dr_org_name"] = token.get("org_name")
        email_values["sr_org_name"] = sr_org_info.get("name")
        email_values["sr_first_name"] = sr_info.get("first_name")
        email_values["dr_name"] = \
            f"{dr_info.get('first_name')} {dr_info.get('last_name')}"
        email_values["module_number"] = upload_info.get("module_id")
        email_values["module_last_updated_by"] = upload_info.get("updated_by")
        email_values["module_last_updated_on"] = format_datetime_obj(upload_info.get("updated_on"))
        email_values["reporting_year"] = upload_info.get("year")

        email_values["decision_date"] = email_values["module_last_updated_on"]
        email_values["feedback"] = request_body["comments"]
        email_values["upload_id"] = request_body["upload_id"]

        if use_central_config:
            config = DatabaseCentralConfig()
            email_values["module_name"] = config.module_display_name(upload_info.get('module_id'))
            email_values["reporting_period"] = \
                config.module_frequency_proper(upload_info.get('module_id'))
        else:
            full_mod_id = "Module" + upload_info.get('module_id')
            email_values["module_name"] = ModuleNames[full_mod_id].value
            email_values["reporting_period"] = \
                ModuleFrequencyProper[full_mod_id].value

        if (request_body['submission_status']) == "Approved":
            email_values["email_type"] = Email_Template.SR_APPROVED
            trigger_email(email_values)
        else:
            email_values["email_type"] = Email_Template.SR_REJECTED
            trigger_email(email_values)

    except Exception as err:
        logger.debug("exception prior to re-raise: %s", repr(err))
        raise EvChartJsonOutputError(
            message=f"Error formatting fields for email handler: {err}"
        ) from err


def format_datetime_obj(datetime_obj):
    try:
        as_timezone = datetime_obj.astimezone(tz.gettz("US/Eastern"))
        formatted_upload_timestamp = \
            str(as_timezone.strftime("%m/%d/%y %-I:%M %p %Z"))

        return formatted_upload_timestamp

    except Exception as e:
        logger.debug("exception prior to re-raise: %s", repr(e))
        error_message = (
            "Error thrown in format_datetime_obj() when "
            f"formatting datetime_obj: {repr(e)}"
        )
        raise EvChartJsonOutputError(message=error_message) from e
