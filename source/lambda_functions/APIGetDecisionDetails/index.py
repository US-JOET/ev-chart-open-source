"""
APIGetDecisionDetails

Generate and execute all the relevant queries necessary and provide the resulting data to the
frontend about the decision details for a particular module.
"""
import json

from dateutil import tz
from evchart_helper import aurora
from evchart_helper.api_helper import execute_query, get_org_info_dynamo
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedHeadersError,
    EvChartUserNotAuthorizedError
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.module_helper import is_valid_upload_id, format_fullname_from_email
from evchart_helper.session import SessionManager

import_metadata = ModuleDataTables["Metadata"].value


@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            log = LogEvent(event=event, api="APIGetDecisionDetails", action_type="Read")
            if log.is_auth_token_valid() == False:
                raise EvChartAuthorizationTokenInvalidError()

            #getting path parameters
            path_parameters = event.get("queryStringParameters")
            upload_id = path_parameters.get("upload_id", []) if path_parameters else []

            #getting auth token
            token = log.get_auth_token()
            org_id = token["org_id"]
            org_type = token["recipient_type"]

            decision_info = []
            if not upload_id or is_valid_upload_id(upload_id, cursor) is False:
                raise EvChartMissingOrMalformedHeadersError(
                    message="Missing or malformed upload_id from path parameters."
                )

            decision_info = get_decision_info(upload_id, org_id, org_type, cursor)
            formatted_data = format_data(decision_info)

        except (EvChartMissingOrMalformedHeadersError,
                EvChartAuthorizationTokenInvalidError,
                EvChartUserNotAuthorizedError,
                EvChartJsonOutputError,
                EvChartDatabaseAuroraQueryError
        )as e:

            log.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log.log_successful_request(
                message="Successfully retrieved decision details",
                status_code=200
            )
            return_obj = {
                'statusCode' : 200,
                'headers': { "Access-Control-Allow-Origin": "*" },
                'body': json.dumps(formatted_data)
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj

#get decision info and check that given org_id is associated with given upload_id
def get_decision_info(upload_id, org_id, org_type, cursor):
    try:
        if org_type.upper() != 'JOET':
            statement = f"""
                SELECT upload_id, module_id, submission_status as decision,
                        updated_on as decision_date, updated_by as reviewer, comments,
                        parent_org
                FROM {import_metadata}
                WHERE upload_id=%s AND (parent_org=%s OR org_id=%s)
                ORDER BY updated_on
                LIMIT 1
            """
            data = (upload_id, org_id, org_id)
        else:
            statement = f"""
                SELECT upload_id, module_id, submission_status as decision,
                        updated_on as decision_date, updated_by as reviewer, comments,
                        parent_org
                FROM {import_metadata}
                WHERE upload_id=%s
                ORDER BY updated_on
                LIMIT 1
            """
            data = (upload_id,)

        result = execute_query(statement, data, cursor, message="validate_org in GetDecisionDetails API")
        return result[0]

    except Exception as e:
        error_message = f"Org {org_id} not authorized to view upload {upload_id}: {e}"
        raise EvChartUserNotAuthorizedError(message=error_message)

def format_data(decision_info):
    try:
        deciding_org_name = get_org_info_dynamo(decision_info["parent_org"])["name"]
        if decision_info:
            #formatting reviewer
            decision_info["updated_by"] = decision_info["reviewer"]
            if format_fullname_from_email(decision_info):
                decision_info["reviewer"] = decision_info["updated_by"]


            #formatting decision_date
            date_obj = decision_info["decision_date"].astimezone(tz.gettz("US/Eastern"))
            decision_info["decision_date"] = str(date_obj.strftime("%m/%d/%y %-I:%M %p %Z"))
            if decision_info["decision"] == "Approved":
                decision_info["decision_explanation"] = f"Module {decision_info['module_id']} has been approved by {deciding_org_name} and now is completely submitted."
            elif decision_info["decision"] == "Rejected":
                decision_info["decision_explanation"] = f"Module {decision_info['module_id']} has been rejected by {deciding_org_name} and needs to be resubmitted."

        return decision_info
    except Exception as e:
        error_message = f"Error formatting decision details: {e}"
        raise EvChartJsonOutputError(message=error_message)
