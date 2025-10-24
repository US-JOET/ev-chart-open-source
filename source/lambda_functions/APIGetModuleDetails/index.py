"""
APIGetModuleDetails

This function returns the general metadata related to a module submission for the
station details page. It will receive an upload_id from the frontend,  it will
verify that the module has the correct status, and it will validate that the
appropriate role type is viewing the data.
"""
import json
import logging
from evchart_helper import aurora
from evchart_helper.api_helper import get_headers
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartMissingOrMalformedHeadersError,
    EvChartUserNotAuthorizedError,
    EvChartDatabaseAuroraQueryError,
    EvChartJsonOutputError,
    EvChartModuleStatusError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.module_helper import format_metadata, get_module_details, validate_headers
from evchart_helper.session import SessionManager

logger = logging.getLogger("APIGetModuleDetails")
logger.setLevel(logging.INFO)


@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(event=event, api="APIGetModuleDetails", action_type="Read")
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            # parsing request headers
            headers = get_headers(event=event, headers=["upload_id"])
            upload_id = headers.get("upload_id")

            # parsing variables needed from auth token
            token = log_event.get_auth_token()
            org_id = token.get("org_id")
            recipient_type = token.get("recipient_type")
            role_type = token.get("role")
            logger.debug("recipient_type %s, upload_id %s", recipient_type, upload_id)

            # validating if upload_id exists in database and the current recipient can view the data
            validate_headers(upload_id, org_id, recipient_type, cursor)

            # retrieving module data
            module_details = get_module_details(upload_id, org_id, recipient_type, cursor, logger)

            # checking for valid status and role type
            check_valid_status(module_details)
            check_valid_role_type(role_type, module_details)

            # formatting module data
            format_metadata(recipient_type, module_details)
            logger.debug("Formatted data: %s", module_details)

        except (
            EvChartMissingOrMalformedHeadersError,
            EvChartAuthorizationTokenInvalidError,
            EvChartUserNotAuthorizedError,
            EvChartDatabaseAuroraQueryError,
            EvChartJsonOutputError,
            EvChartModuleStatusError,
        ) as e:

            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="Successfully retreived module details.",
                status_code=200,
                module_info=f"Upload ID: {upload_id}",
            )
            return_obj = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(module_details),
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


def check_valid_status(module_details):
    status = module_details[0]["submission_status"]
    if status in ["Processing", "Error"]:
        raise EvChartModuleStatusError(message=f"Module has {status} status and cannot be viewed.")


# helper function that checks that viewer role types can only view submitted/approved modules
def check_valid_role_type(role_type, module_details):
    status = module_details[0]["submission_status"]
    if role_type.lower() == "viewer" and (
        status.lower() != "approved" and status.lower() != "submitted"
    ):
        raise EvChartUserNotAuthorizedError(
            message="Viewer role types can only view submitted or approved modules."
        )
