"""
APIGetSubmittingNullData

Return true if the module data contains nulls or if the user_reports_no_data flag is True.
Triggers FE to prompt user to confirm that they are submitting null or no data
"""

import logging
from evchart_helper import aurora
from evchart_helper.custom_logging import LogEvent
from evchart_helper.api_helper import get_headers, execute_query
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartFeatureStoreConnectionError,
    EvChartMissingOrMalformedHeadersError,
)
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

module2 = ModuleDataTables["Module2"].value
module3 = ModuleDataTables["Module3"].value
module4 = ModuleDataTables["Module4"].value
module5 = ModuleDataTables["Module5"].value
module9 = ModuleDataTables["Module9"].value

logger = logging.getLogger("APIGetSubmittingNullData")
logger.setLevel(logging.DEBUG)


@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(
                event=event, api="APIGetSubmittingNullData", action_type="Read"
            )
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            # check if headers are valid and parse the event headers
            headers = get_headers(event=event, headers=["upload_id", "module_id"])
            upload_id = headers.get("upload_id")
            module_id = headers.get("module_id")
            feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

            if (Feature.BIZ_MAGIC in feature_toggle_set) and (
                (Feature.ASYNC_BIZ_MAGIC_MODULE_2 in feature_toggle_set and int(module_id) == 2) or
                (Feature.ASYNC_BIZ_MAGIC_MODULE_3 in feature_toggle_set and int(module_id) == 3) or
                (Feature.ASYNC_BIZ_MAGIC_MODULE_4 in feature_toggle_set and int(module_id) == 4) or
                (Feature.ASYNC_BIZ_MAGIC_MODULE_5 in feature_toggle_set and int(module_id) == 5)or
                (Feature.ASYNC_BIZ_MAGIC_MODULE_9 in feature_toggle_set and int(module_id) == 9)
            ):
                is_submitting_null = biz_magic_check(upload_id, module_id, cursor)

            elif (Feature.MODULE_5_NULLS in feature_toggle_set and int(module_id) == 5):
                is_submitting_null = check_nulls(upload_id, module_id, cursor)

            else:
                is_submitting_null = False

        except (
            EvChartAuthorizationTokenInvalidError,
            EvChartMissingOrMalformedHeadersError,
            EvChartDatabaseAuroraQueryError,
        ) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="Successfully determined if submitting null data",
                status_code=200,
            )
            return_obj = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": is_submitting_null,
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


def check_nulls(upload_id, module_id, cursor):
    try:
        is_submitting_null = False
        if int(module_id) == 9:
            query = f"""SELECT real_property_cost_total,
                                equipment_cost_total,
                                equipment_install_cost_total,
                                der_cost_total,
                                der_install_cost_total,
                                dist_sys_cost_total,
                                service_cost_total
                        FROM {module9}
                        WHERE upload_id=%s"""
            cursor.execute(query, (upload_id,))
            sql_output = cursor.fetchall()
        elif int(module_id) == 3:
            query = f"SELECT uptime FROM {module3} WHERE upload_id=%s" ""
            cursor.execute(query, (upload_id,))
            sql_output = cursor.fetchall()
        elif int(module_id) == 2:
            query = f"""SELECT session_start,
                            session_end,
                            session_error,
                            energy_kwh,
                            power_kw,
                            payment_method
                        FROM {module2} WHERE upload_id=%s"""
            cursor.execute(query, (upload_id,))
            sql_output = cursor.fetchall()
        elif int(module_id) == 5:
            query = (
                f"SELECT maintenance_cost_total FROM {module5} WHERE upload_id=%s" ""
            )
            cursor.execute(query, (upload_id,))
            sql_output = cursor.fetchall()
        else:
            return is_submitting_null

        for val in sql_output:
            if None in val:
                return True

        return is_submitting_null
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Error querying for null columns: {repr(e)}"
        ) from e


def biz_magic_check(upload_id, module_id, cursor):
    try:
        module_id = f"Module{module_id}"
        module_table = ModuleDataTables[module_id].value
        query = f"SELECT * FROM {module_table} WHERE upload_id=%s"
        sql_output = execute_query(query, (upload_id,), cursor)
        for item in sql_output:
            if item.get("user_reports_no_data", 0) == 1:
                return True
        return False

    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Error querying for user_reports_no_data columns: {repr(e)}"
        ) from e
