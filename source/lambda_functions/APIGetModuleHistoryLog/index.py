"""
APIGetModuleHistoryLog

Return the import and approval history for a particular application module submission.
"""
import json
import logging

from evchart_helper import aurora
from evchart_helper.api_helper import execute_query
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError, EvChartDatabaseAuroraQueryError,
    EvChartDatabaseDynamoQueryError, EvChartJsonOutputError,
    EvChartMissingOrMalformedHeadersError, EvChartUserNotAuthorizedError)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.module_helper import (format_datetime_obj,
                                          format_fullname_from_email,
                                          format_org_name_from_email,
                                          is_valid_upload_id)
from evchart_helper.session import SessionManager

import_metadata = ModuleDataTables["Metadata"].value
import_metadata_history = ModuleDataTables["MetadataHistory"].value

logger = logging.getLogger("APIGetModuleHistoryLog")
logger.setLevel(logging.DEBUG)


@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            formatted_data = {}
            log_event = LogEvent(
                event=event, api="APIGetModuleHistoryLog", action_type="Read"
            )
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            # getting upload_id from path parameters
            path_parameters = event.get("queryStringParameters")
            upload_id = path_parameters.get(
                "upload_id", []
            ) if path_parameters else []

            # getting org_id from token
            token = log_event.get_auth_token()
            org_id = token["org_id"]

            if (
                upload_id_is_verified(cursor, upload_id) and
                org_is_authorized(cursor, org_id, upload_id)
            ):
                module_history = get_module_history(cursor, upload_id)
                formatted_data = format_module_history_data(module_history)

        except (
            EvChartMissingOrMalformedHeadersError,
            EvChartAuthorizationTokenInvalidError,
            EvChartUserNotAuthorizedError,
            EvChartJsonOutputError,
            EvChartDatabaseAuroraQueryError,
            EvChartDatabaseDynamoQueryError
        )as e:

            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="Successfully retreived history log",
                status_code=200
            )

            return_obj = {
                'statusCode': 200,
                'headers': {"Access-Control-Allow-Origin": "*"},
                'body': json.dumps(formatted_data)
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


# helper function that returns true if upload_id exists in table
# else throws an malformed headers
def upload_id_is_verified(cursor, upload_id):
    if not upload_id or is_valid_upload_id(upload_id, cursor) is False:
        raise EvChartMissingOrMalformedHeadersError(
            message=(
                "Thrown in handler(). "
                "Missing or malformed path parameters for upload_id."
            )
        )
    return True


# helper function that returns true if org can view history log,
# else throws a user not authorized error
def org_is_authorized(cursor, org_id, upload_id):
    verify_org_query = f"""
        SELECT * FROM {import_metadata}
        WHERE upload_id=%s and (org_id=%s or parent_org=%s)
    """
    query_data = (upload_id, org_id, org_id)
    result = execute_query(
        query=verify_org_query,
        data=query_data,
        cursor=cursor,
        message="Error thrown in org_is_authorized()."
    )
    if not result or result is None:
        raise EvChartUserNotAuthorizedError(
            message="Current org is not allowed to view history of module."
        )
    return True


# helper function that queries the module history table and
# returns a list of dict for all updates made to passed in upload id
def get_module_history(cursor, upload_id):
    get_history_query = f"""
        SELECT * from {import_metadata_history}
        WHERE upload_id=%s
        ORDER BY updated_on
    """
    query_data = (upload_id,)
    history_data = execute_query(
        query=get_history_query,
        data=query_data,
        cursor=cursor,
        message="Error thrown in get_module_history()"
    )
    return history_data


def format_module_history_data(module_history):
    fallback_status = "Processing"
    for module_history_dict in module_history:
        if "submission_status" in module_history_dict:
            fallback_status = module_history_dict["submission_status"]
        else:
            module_history_dict["submission_status"] = fallback_status

        # formats organization name
        format_org_name_from_email(module_history_dict)

        # formats updated_by to users first and last name
        format_fullname_from_email(module_history_dict)

        # formats the updated_on column
        format_datetime_obj(module_history_dict)

        # formatting submission_status since it is in a nested dict
        format_var_in_changed_data("submission_status", module_history_dict)

        # formatting comments since it is in a nested dict
        format_var_in_changed_data("comments", module_history_dict)

    return module_history


# helper function that takes in a target_variable
# checks if it is a key within the nested dict (changed_data)
# then sets it as a key to the module_history_dict
def format_var_in_changed_data(target_variable, module_history_dict):
    try:
        changed_data = module_history_dict.get("changed_data")
        # parsing the changed_data dict from json format
        changed_data = json.loads(changed_data)
        # if add "comments" to dict if they are present in changed_data
        if target_variable in changed_data.keys():
            module_history_dict[target_variable] = \
                changed_data.get(target_variable)

        return module_history_dict

    except Exception as e:
        logger.debug("exception prior to re-raise: %s", repr(e))
        raise EvChartJsonOutputError(
            message=(
                "Error thrown in format_comments() when trying to format "
                f"{target_variable} from module history query: {e}"
            )
        ) from e
