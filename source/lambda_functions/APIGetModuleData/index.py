"""
APIGetModuleData

Return requested module data in a format that is to be used by the frontend in order to display
inline in the application.
"""
import logging
import json
import pandas as pd
from pymysql.err import OperationalError

from database_central_config import DatabaseCentralConfig
from evchart_helper import aurora
from evchart_helper.api_helper import get_headers, get_upload_metadata, get_org_info_dynamo
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseHandlerConnectionError,
    EvChartUserNotAuthorizedError,
    EvChartMissingOrMalformedHeadersError,
    EvChartDatabaseAuroraQueryError,
    EvChartJsonOutputError,
    EvChartUnknownException,
    EvChartFeatureStoreConnectionError
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.module_enums import ModulePrimary, get_db_col_names_arr, get_UI_col_names_map
from evchart_helper.module_helper import (
    validate_headers,
    format_dataframe_date,
    format_dataframe_bool,
    get_module_id
)
from evchart_helper.presigned_url import generate_presigned_url
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

station_registrations = ModuleDataTables["RegisteredStations"].value

logger = logging.getLogger("APIGetModuleData")
logger.setLevel(logging.INFO)

BAD_FIELD_ERROR = 1054


# TODO: refactor so pylint disable isn't needed
# TODO: refactor to use Central config for getting display names, nulls, etc
@SessionManager.check_session()
def handler(event, _context): # pylint: disable=too-many-locals
    log_event = LogEvent(
        event=event, api="APIGetModuleData", action_type="Read"
    )
    logging.debug(event)

    try:
        connection = aurora.get_connection()
    except Exception:
        return EvChartDatabaseHandlerConnectionError().get_error_obj()

    with connection.cursor() as cursor:
        try:
            # feature must be called in the handler in order to get the
            # current value every time, and not a value persisted by Lambda warm start
            # https://docs.aws.amazon.com/lambda/latest/operatorguide/global-scope.html
            # pylint: disable=duplicate-code
            feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            # getting necessary headers from event
            event_headers = get_headers(event=event, headers=["upload_id", "download"])
            upload_id = event_headers.get("upload_id")
            is_download = {"True": True, "False": False}.get(
                event_headers.get("download").capitalize()
            )

            # getting necessary parameters from auth token
            token = log_event.get_auth_token()
            org_id = token.get("org_id")
            recipient_type = token.get("recipient_type")
            json_output = {}

            # helper function in module_helper file that checks if upload_id
            # is a valid entry and if current org is authorized to view
            # the data, else throws malformed error
            validate_headers(
                upload_id, org_id, recipient_type, cursor
            )
            logger.debug(
                "Retrieving module data for Upload ID: %s "
                "Org ID: %s "
                "Recipient Type: %s",
                upload_id, org_id, recipient_type
            )

            # retrieves the module id from the upload_id
            # which is used to query module data tables
            module_id = get_module_id(upload_id, cursor)

            # gets the module table name from the given module id
            # which will be used to query the right module table
            module_table_name = \
                get_table_name_by_module_id(module_id)
            # sets module_id which is needed for output
            output_module_id = "M" + str(module_id)

            config = DatabaseCentralConfig()
            if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
                grid_headers = config.module_grid_display_headers(module_id)
                output_left_headers = grid_headers['left_grid_headers']
                output_right_headers = grid_headers['right_grid_headers']
                if ((Feature.ASYNC_BIZ_MAGIC_MODULE_4 in feature_toggle_set and int(module_id) == 4) or
                    (Feature.ASYNC_BIZ_MAGIC_MODULE_3 in feature_toggle_set and int(module_id) == 3) or
                    (Feature.ASYNC_BIZ_MAGIC_MODULE_2 in feature_toggle_set and int(module_id) == 2) or
                    (Feature.ASYNC_BIZ_MAGIC_MODULE_5 in feature_toggle_set and int(module_id) == 5) or
                    (Feature.ASYNC_BIZ_MAGIC_MODULE_9 in feature_toggle_set and int(module_id) == 9)
                ):
                    output_right_headers.append("user_reports_no_data")
            else:
                # sets left headers which is needed to identify
                # the pinned column variable
                output_left_headers = \
                    [ModulePrimary["Module" + str(module_id)].value]

                # sets right headers which is needed to identify
                # the rest of the column variables
                output_right_headers = get_right_headers(
                    module_id,
                    output_left_headers[0],
                    feature_toggle_set
                )

            # adds row data from module table to the output
            output = get_module_data_by_table_name(
                upload_id=upload_id,
                left_header=output_left_headers[0],
                right_headers=output_right_headers,
                db_table=module_table_name,
                cursor=cursor,
                is_download=is_download,
                feature_toggle_set=feature_toggle_set
            )
            output_dataframe = output["data"]

            # set null data
            is_submitting_null = False
            if (
                (Feature.MODULE_5_NULLS in feature_toggle_set and int(module_id) == 5) or
                (Feature.ASYNC_BIZ_MAGIC_MODULE_4 in feature_toggle_set and int(module_id) == 4) or
                (Feature.ASYNC_BIZ_MAGIC_MODULE_3 in feature_toggle_set and int(module_id) == 3) or
                (Feature.ASYNC_BIZ_MAGIC_MODULE_2 in feature_toggle_set and int(module_id) == 2) or
                (Feature.ASYNC_BIZ_MAGIC_MODULE_5 in feature_toggle_set and int(module_id) == 5) or
                (Feature.ASYNC_BIZ_MAGIC_MODULE_9 in feature_toggle_set and int(module_id) == 9)
            ):
                output_dataframe = set_null_data(feature_toggle_set, module_id, output_dataframe)

                if int(module_id) == 9:
                    output_dataframe = convert_empty_datetime(output_dataframe)
                is_submitting_null = check_submitting_null(output_dataframe, is_submitting_null, module_id)

            if "network_provider_upload" in output_dataframe.columns:
                output_dataframe.rename(columns={"network_provider_upload": "network_provider"}, inplace=True)

            if "station_id_upload" in output_dataframe.columns:
                output_dataframe.rename(columns={"station_id_upload": "station_id"}, inplace=True)

            if "user_reports_no_data" in output_dataframe.columns:
                output_dataframe = output_dataframe.drop("user_reports_no_data", axis=1)
                output_right_headers.remove("user_reports_no_data")

            if is_download and "dr_id" not in output_dataframe.columns:
                dr_id = get_upload_metadata(cursor, upload_id).get("parent_org")
                output_dataframe["dr_id"] = get_org_info_dynamo(dr_id).get("org_friendly_id")

            if Feature.PRESIGNED_URL in feature_toggle_set and is_download:
                presigned_url = generate_presigned_url(
                    file={
                        "data": output_dataframe.to_csv(index=False),
                        "name": "data.csv",
                    },
                    transfer_type="download",
                )
                json_output |= presigned_url

            else:
                output_data = output_dataframe.to_dict(orient="records")

                if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
                    output_header_text = \
                        config.module_field_display_names(module_id)
                else:
                    # sets header text which is needed for the
                    # column headings for the table
                    output_header_text = get_UI_col_names_map(
                        mod_num=int(module_id),
                        fields=output_left_headers + output_right_headers
                    )

                header_map = {
                    "station_id_upload": "station_id",
                    "network_provider_upload": "network_provider",
                }
                for i, header in enumerate(output_left_headers):
                    output_left_headers[i] = header_map.get(header, header)

                for i, header in enumerate(output_right_headers):
                    output_right_headers[i] = header_map.get(header, header)

                ui_headers = {}
                for header, header_text in output_header_text.items():
                    ui_headers[header_map.get(header, header)] = header_text

                # builds the json dictionary that is returned to the frontend
                json_output |= build_json_output(
                    output_module_id,
                    output_left_headers,
                    output_right_headers,
                    ui_headers,
                    output_data,
                    output["is_truncated"],
                    is_submitting_null
                )

        except (
            EvChartFeatureStoreConnectionError,
            EvChartAuthorizationTokenInvalidError,
            EvChartUserNotAuthorizedError,
            EvChartJsonOutputError,
            EvChartMissingOrMalformedHeadersError,
            EvChartDatabaseAuroraQueryError,
            EvChartUnknownException,
        ) as e:
            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="Successfully retreived module data", status_code=200
            )
            return_obj = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(json_output, default=str),
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


# helper function that returns the corresponding database table name
# that holds data for the given module_id
def get_table_name_by_module_id(module_id):
    try:
        enum_key_for_db_table = "Module" + module_id
        db_table = ModuleDataTables[enum_key_for_db_table].value
        return db_table

    except Exception as e:
        error_message = (
            f"Error thrown in get_table_name_by_module_id(). "
            f"Error referencing helper file and retrieving "
            f"database table name with module ID {module_id}: {e}"
        )
        raise EvChartJsonOutputError(
            message=error_message
        ) from e


# helper function that formats the module's row data in a specific way
# so that the FE can display the data
def get_module_data_by_table_name(
        upload_id, left_header, right_headers, db_table, cursor, is_download, feature_toggle_set=frozenset()
):
    try:
        if left_header in right_headers:
            query_headers = right_headers
        else:
            query_headers = [left_header] + right_headers
        # query the respective module table with given upload id
        #  to grab module data
        df = get_dataframe(
            upload_id=upload_id,
            db_table=db_table,
            headers=query_headers,
            cursor=cursor
        )

    except Exception as e:
        error_message = f"Error thrown in get_module_data_by_table_name(): {repr(e)}"
        raise EvChartDatabaseAuroraQueryError(
            message=error_message
        ) from e

    try:
        output = {}
        if not is_download and len(df.index) > 1000:
            df = df.iloc[:1000]
            output["is_truncated"] = True
        else:
            output["is_truncated"] = False

        # format for bool
        format_dataframe_bool(df,feature_toggle_set)

        # format date
        format_dataframe_date(df, is_download)

        # set left column
        first_column = df.pop(left_header)
        df.insert(0, left_header, first_column)

        output["data"] = df

        # data_as_dict = df.to_dict(orient='records')
        return output

    except EvChartJsonOutputError as e:
        e.message += "Error thrown in get_module_data_by_table_name()"
        raise e

    except Exception as e:
        raise EvChartUnknownException(
            message=(
                "Error thrown in get_module_data_by_table_name(): "
                f"{repr(e)}"
            )
        ) from e


def get_dataframe(upload_id, db_table, headers, cursor):
    dataframe = None
    try:
        get_data_query = (
            f"SELECT {', '.join(headers)} "
            f"FROM {db_table} "
            f"WHERE upload_id=%s"
        )
        cursor.execute(get_data_query, (upload_id,))
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]
        dataframe = pd.DataFrame(rows, columns=column_names)

    except OperationalError as e:
        # fallback if station_id_upload is not in table
        # should not happen but attempting to be graceful anyway
        error_code, error_message = e.args # pylint: disable=unbalanced-tuple-unpacking
        if (
            error_code == BAD_FIELD_ERROR and
            "'station_id_upload'" in error_message
        ):
            get_data_query = (
                f"SELECT {', '.join(headers)} FROM {db_table} "
                f"JOIN {station_registrations} "
                f"USING (station_uuid) WHERE upload_id=%s"
            )
            logger.debug("Query used to grab data based on upload id: %s", get_data_query)
            cursor.execute(get_data_query, (upload_id,))
            rows = cursor.fetchall()
            column_names = [column[0] for column in cursor.description]
            dataframe = pd.DataFrame(rows, columns=column_names)
            logger.debug("DF of module data %s", dataframe)

    logger.debug(
        "Number of module data rows returned: %s",
        len(dataframe.index)
    )
    return dataframe


# helper function that references the module_enum folder to get
# the column names of db fields for right headers
def get_right_headers(module_id, left_header, feature_toggle_set):
    column_names_arr = get_db_col_names_arr(int(module_id))

    if ((Feature.ASYNC_BIZ_MAGIC_MODULE_4 in feature_toggle_set and module_id == '4') or
        (Feature.ASYNC_BIZ_MAGIC_MODULE_3 in feature_toggle_set and module_id == '3') or
        (Feature.ASYNC_BIZ_MAGIC_MODULE_2 in feature_toggle_set and module_id == '2') or
        (Feature.ASYNC_BIZ_MAGIC_MODULE_5 in feature_toggle_set and module_id == '5') or
        (Feature.ASYNC_BIZ_MAGIC_MODULE_9 in feature_toggle_set and module_id == '9')
    ):
        column_names_arr.append("user_reports_no_data")
    if left_header in column_names_arr:
        column_names_arr.remove(left_header)
    return column_names_arr

def build_json_output(
    module_id, left_headers, right_headers, header_text, data, is_truncated, is_submitting_null
):
    json_output = {}
    json_output["moduleId"] = module_id
    json_output["leftHeaders"] = left_headers
    json_output["rightHeaders"] = right_headers
    json_output["headerText"] = header_text
    json_output["data"] = data
    json_output["truncated"] = is_truncated
    json_output["is_submitting_null"] = is_submitting_null
    return json_output

# update dataframe based on specific module NULL data guidance
def set_null_data(feature_toggle_set, module_id, df):
    try:
        if int(module_id) == 2 and Feature.ASYNC_BIZ_MAGIC_MODULE_2 in feature_toggle_set:
            nullable_rows = (df['user_reports_no_data'] == "TRUE")
            nullable_fields = [
                'session_id',
                'charger_id',
                'connector_id',
                'session_start',
                'session_end',
                'session_error',
                'error_other',
                'energy_kwh',
                'power_kw',
                'payment_method',
                'payment_other']
            df.loc[nullable_rows, nullable_fields] = ""
            df.fillna('', inplace=True)
        elif int(module_id) == 3 and Feature.ASYNC_BIZ_MAGIC_MODULE_3 in feature_toggle_set:
            nullable_fields = (df['user_reports_no_data'] == "TRUE")
            df.loc[nullable_fields, ['uptime']] = ""

        elif int(module_id) == 4 and Feature.ASYNC_BIZ_MAGIC_MODULE_4 in feature_toggle_set:
            optional_fields = ["excluded_outage", "excluded_outage_reason", "excluded_outage_notes"]
            df[optional_fields] = df[optional_fields].fillna(value="")
            # this field is TRUE or FALSE
            nullable_fields = (df['user_reports_no_data'] == "TRUE")
            nullable_columns = ['outage_id', 'outage_duration']
            df[nullable_columns] = df[nullable_columns].astype(str)
            df.loc[nullable_fields, nullable_columns] = ""

        elif (
            int(module_id) == 9
            and Feature.ASYNC_BIZ_MAGIC_MODULE_9 in feature_toggle_set
        ):
            nullable_fields = df["user_reports_no_data"] == "TRUE"
            df.loc[
                nullable_fields,
                [
                    "real_property_cost_total",
                    "equipment_cost_total",
                    "equipment_install_cost_total",
                    "equipment_install_cost_elec",
                    "equipment_install_cost_const",
                    "equipment_install_cost_labor",
                    "equipment_install_cost_other",
                    "der_acq_owned",
                    "der_cost_total",
                    "der_install_cost_total",
                    "dist_sys_cost_total",
                    "service_cost_total",
                ],
            ] = ""

        elif int(module_id) == 5 and Feature.ASYNC_BIZ_MAGIC_MODULE_5 in feature_toggle_set:
            nullable_fields = (df['user_reports_no_data'] == "TRUE")
            df.loc[nullable_fields, ['maintenance_cost_total']] = ""
        elif int(module_id) == 5 and Feature.MODULE_5_NULLS in feature_toggle_set:
            df.fillna({"maintenance_cost_total":"NULL"}, inplace = True)

        return df
    except Exception as e:
        raise EvChartJsonOutputError(message=f"Error converting null data: {e}") from e

# TODO: REMOVE FUNCTION WHEN MODULE_9_NULLS AND MODULE_5_NULLS ARE REMOVED
# TODO: also remove all references to is_submitting_null as it is the old way of interpreting null data
def check_submitting_null(df, is_submitting_null, module_id):
    try:
        if int(module_id) == 9:
            nullable_fields = ["real_property_cost_total",
                               "equipment_cost_total",
                               "equipment_install_cost_total",
                               "der_cost_total",
                               "der_install_cost_total",
                               "dist_sys_cost_total",
                               "service_cost_total"]
            valid_df = df[df.columns.intersection(nullable_fields)]
            is_submitting_null = (valid_df.values == 'NULL').any()
        elif int(module_id) == 3:
            uptime = df["uptime"].astype(str)
            is_submitting_null = uptime.str.contains("").any()
        elif int(module_id) == 4:
            is_submitting_null = (df.values == '').any()
        elif int(module_id) == 2:
            nullable_fields = ["session_start",
                               "session_end",
                               "session_error",
                               "energy_kwh",
                               "power_kw",
                               "payment_method"]
            valid_df = df[df.columns.intersection(nullable_fields)]
            is_submitting_null = (valid_df.values == '').any()
        elif int(module_id) == 5:
            maintenance_cost_total = df["maintenance_cost_total"].astype(str)
            is_submitting_null = maintenance_cost_total.str.contains("NULL").any()
        return is_submitting_null
    except Exception as e:
        raise EvChartJsonOutputError(message=f"Error checking for nulls: {e}") from e

def convert_empty_datetime(df):
    try:
        df.replace('0000-00-00 00:00:00', "", inplace=True)

        return df
    except Exception as e:
        raise EvChartJsonOutputError(message=f"Error converting empty datetimes: {e}") from e
