"""
APIPutRemoveModuleData

Enable the user to request deletion of module data that is in error, been rejected, or in the Draft
status.  Accepted module data cannot be deleted.
"""
import json
import logging
from evchart_helper import aurora
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartAuthorizationTokenInvalidError,
    EvChartMissingOrMalformedBodyError,
    EvChartUserNotAuthorizedError,
    EvChartJsonOutputError
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.module_helper import get_module_id
from evchart_helper.api_helper import execute_query_fetchone
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature

logger = logging.getLogger("APIPutRemoveModuleData")
logger.setLevel(logging.DEBUG)

metadata_table = ModuleDataTables["Metadata"].value
error_table = ModuleDataTables["EvErrorData"].value

@SessionManager.check_session()
@feature_enablement_check(Feature.REMOVE_MODULE_DATA)
def handler(event, _context):
    connection = aurora.get_connection()

    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(
                event, api="APIPutRemoveModuleData", action_type="MODIFY"
            )
            if not log_event.is_auth_token_valid():
                raise EvChartAuthorizationTokenInvalidError()

            request_body = json.loads(event['body'])
            if "upload_id" not in request_body:
                raise EvChartMissingOrMalformedBodyError(
                    message="Missing from body: upload_id"
                )

            upload_id = request_body['upload_id']
            token = log_event.get_auth_token()
            recipient_type = token.get("recipient_type")

            #get status of upload_id
            get_upload_id_query = f"SELECT submission_status FROM {metadata_table} WHERE upload_id=%s"
            status = execute_query_fetchone(query=get_upload_id_query, data=(upload_id,), cursor=cursor, message="Error thrown in APIPutRemoveModuleData.")

            # check if valid upload_id
            if status is None:
                raise EvChartMissingOrMalformedBodyError(
                    message="Malformed upload_id"
                )
            else:
                status = status[0].lower()
                #check if recipient is allowed to delete current upload_id
                if recipient_type == "direct-recipient" and (status in ["draft", "error"]):
                    remove_module_data(upload_id, cursor)
                elif recipient_type == "sub-recipient" and (status in ["draft", "rejected", "error"]):
                    remove_module_data(upload_id, cursor)
                else:
                    raise EvChartUserNotAuthorizedError(message="User must be a DR deleting draft uploads or an SR deleting draft of rejected uploads.")

        except (
            EvChartMissingOrMalformedBodyError,
            EvChartAuthorizationTokenInvalidError,
            EvChartDatabaseAuroraQueryError,
            EvChartUserNotAuthorizedError,
            EvChartJsonOutputError
        ) as e:
            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="APISubmitModuleData successfully invoked",
                status_code=201
            )
            return_obj = {
                'statusCode': 201,
                'headers': {"Access-Control-Allow-Origin": "*"},
                'body': json.dumps("Module data successfully submitted")
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj

#helper method that removes rows with the passed in upload_id from metadata table and module table
def remove_module_data(upload_id, cursor):
    try:
        module_id = "Module" + get_module_id(upload_id, cursor)
        module_table = ModuleDataTables[module_id].value
    except Exception as e:
        raise EvChartJsonOutputError(message=f"Error in remove_module_data(). Error getting module table from module_id {e}")

    try:
        query_data = (upload_id)

        remove_queries = [
            f"DELETE FROM {module_table} WHERE upload_id=%s",
            f"DELETE FROM {error_table} WHERE upload_id=%s",
            f"DELETE FROM {metadata_table} WHERE upload_id=%s",
        ]

        for remove_query in remove_queries:
            cursor.execute(remove_query, query_data)

        return True
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(message=f"Error thrown in remove_module_data(). Could not delete records from module and metadata table: {e}")
