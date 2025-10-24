"""
APIGetImportErrorData

This API takes in an upload_id from the queryStringParameters and returns the data
needed to construct the error log. Errors are thrown if no upload_id was passed in
or if there are no records found within the error table.
"""

import json
import pandas as pd

from evchart_helper import aurora
from evchart_helper.api_helper import execute_query_fetchone, execute_query_df
from evchart_helper.module_helper import format_dataframe_date
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartMissingOrMalformedHeadersError,
    EvChartJsonOutputError,
    EvChartFeatureStoreConnectionError
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.presigned_url import generate_presigned_url
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

ev_error_data = ModuleDataTables["EvErrorData"].value


@SessionManager.check_session()
def handler(event, _context):
    log_event = LogEvent(event, api="APIGetImportErrorData", action_type="Read")
    connection = aurora.get_connection()

    with connection.cursor() as cursor:
        feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)
        json_output = {}
        error_df = pd.DataFrame()
        try:
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            if is_valid_upload_id(event, cursor):
                upload_id = event.get("queryStringParameters").get("upload_id")
                error_df = get_error_data_as_df(cursor, upload_id)
                format_dataframe_date(error_df, True)
                json_output = {
                    "data" : error_df.to_dict(orient="records")
                }

        except (
            EvChartFeatureStoreConnectionError,
            EvChartAuthorizationTokenInvalidError,
            EvChartMissingOrMalformedHeadersError,
            EvChartDatabaseAuroraQueryError,
            EvChartJsonOutputError,
        ) as e:
            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="APIGetImportErrorData successfully invoked",
                status_code=200
            )
            return_obj = {
                'statusCode' : 200,
                'headers': { "Access-Control-Allow-Origin": "*" },
            }

            if Feature.PRESIGNED_URL in feature_toggle_set:
                presigned_url = generate_presigned_url(
                    file={
                        "data": error_df.to_csv(index=False),
                        "name": "errors.csv",
                    },
                    transfer_type="download",
                )
                return_obj["body"] = json.dumps(presigned_url, default=str)

            else:
                return_obj["body"] = json.dumps(json_output, default=str)

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


#helper method that verifies that upload id is not missing or malformed
def is_valid_upload_id(event, cursor):
    path_parameters = event.get("queryStringParameters")
    upload_id = path_parameters.get("upload_id", []) if path_parameters else []
    if not upload_id:
        raise EvChartMissingOrMalformedHeadersError(message= "Upload ID required")

    check_upload_query = f"""
        SELECT COUNT(*)
        FROM {ev_error_data}
        WHERE upload_id=%s
    """
    result = execute_query_fetchone(
        cursor=cursor,
        query=check_upload_query,
        data=(upload_id,)
    )
    # getting the count value from query
    if result[0] == 0:
        raise EvChartMissingOrMalformedHeadersError(
            message=f"No errror records found upload_id {upload_id} "
        )
    return True


#helper method that gets the error records with the given upload_id and returns a dataframe
def get_error_data_as_df(cursor, upload_id):
    get_errors_query = f"""SELECT
        header_name as 'column',
        error_row as 'row',
        error_description as 'error',
        station_id,
        dr_org_friendly_id as dr_id,
        record as data_in_row
        FROM {ev_error_data} WHERE upload_id=%s
        """

    dataframe = execute_query_df(
        query=get_errors_query,
        data=(upload_id,),
        cursor=cursor,
        message="""Error thrown in get_error_data_as_df() when querying the ev_error_data table
            with given upload_id {upload_id}. """
    )
    return dataframe.replace({float('nan'):None})
