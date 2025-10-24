"""
APIGetDashboardPPMaintenanceCosts

Generate and execute all the relevant queries necessary and provide the resulting data to the
frontend for the program performance dashboard.
"""

import json
import logging

from evchart_helper import aurora
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedHeadersError,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.dashboard_helper import (
    execute_query_with_filters,
    get_dr_id,
    get_sr_id,
    get_station,
    get_year,
    normalized_monthly_cost,
    validate_filters,
    validate_org,
    operational_days
)
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature

logger = logging.getLogger("APIGetDashboardPPMaintenanceCosts")
logger.setLevel(logging.DEBUG)

module2_data = ModuleDataTables["Module2"].value
module3_data = ModuleDataTables["Module3"].value
module4_data = ModuleDataTables["Module4"].value
module5_data = ModuleDataTables["Module5"].value
module9_data = ModuleDataTables["Module9"].value

station_registrations_data = ModuleDataTables["RegisteredStations"].value
authorized_station_data = ModuleDataTables["StationAuthorizations"].value
import_metadata = ModuleDataTables["Metadata"].value
station_ports_data = ModuleDataTables["StationPorts"].value

MONTH_LENGTH = 365.0 / 12.0

capital_cost_categories = [
    "equipment_cost",
    "equipment_install_cost",
    "service_cost",
    "dist_sys_cost",
]


@SessionManager.check_session()
@feature_enablement_check(Feature.JO_PP_DASHBOARD)
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(
                event=event, api="APIGetDashboardPPMaintenanceCosts", action_type="READ"
            )
            logger.info(event)
            if not log_event.is_auth_token_valid():
                raise EvChartAuthorizationTokenInvalidError()

            # validates user
            token = log_event.get_auth_token()
            recipient_type = validate_org(token)

            # initializes data output
            filters = {"dr_id": "All", "sr_id": "All", "year": "All", "station": "All"}
            path_parameters = event.get("queryStringParameters")
            # applies jo and dr specific filters
            if recipient_type == "JO":
                # getting dr_id from path parameters.
                filters["dr_id"] = get_dr_id(path_parameters, filters["dr_id"])
            elif recipient_type == "DR":
                filters["dr_id"] = token.get("org_id")
                filters["station"] = get_station(path_parameters, filters["station"])
            filters["sr_id"] = get_sr_id(path_parameters, filters["sr_id"])
            filters["year"] = get_year(path_parameters, filters["year"])
            filters = validate_filters(cursor, filters)

            # handling costs
            json_output =count_section4_maintenance_cost(
                    data=maintenance_costs(cursor, filters), year=filters["year"]
                )

            # create list from json_output
            output = [json_output]

        except (
            EvChartAuthorizationTokenInvalidError,
            EvChartUserNotAuthorizedError,
            EvChartDatabaseAuroraQueryError,
            EvChartMissingOrMalformedHeadersError,
            EvChartJsonOutputError,
        ) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="Successfully retreived dashboard data.", status_code=200
            )
            return_obj = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(output, default=str),
            }

        finally:
            connection.commit()
            aurora.close_connection()
        return return_obj



def count_section4_maintenance_cost(data, year="All"):
    total_maintenance_cost = 0.0
    maintenance_cost_records = 0
    for d in data:
        days = operational_days(
            operational_date=d.get("operational_date"), reporting_year=d.get("year")
        )
        if days == 0:
            logger.debug(
                "skipping record with operational_date later than " "reporting year: %s",
                d.get("operational_date"),
            )
            continue
        if year != "All" and int(d.get("year")) != year:
            logger.debug(
                "skipping record with reporting year different " "than filtered year: %s",
                d.get("operational_date"),
            )
            continue
        maintenance_cost_records += 1
        logger.debug("MAINTENANCE COST %s", d)
        incremental_normalized_monthly_cost = normalized_monthly_cost(
            cost=d.get("maintenance_cost_total") or 0.0, days=days
        )
        logger.debug("NORMALIZED COST %s", incremental_normalized_monthly_cost)
        total_maintenance_cost += incremental_normalized_monthly_cost

    if maintenance_cost_records == 0:
        return {
            "maintenance_cost_metrics_available": False,
            "monthly_avg_maintenance_repair_cost": None,
        }

    return {
        "maintenance_cost_metrics_available": True,
        "monthly_avg_maintenance_repair_cost": round(
            total_maintenance_cost / maintenance_cost_records, 2
        ),
    }

def maintenance_costs(cursor, filters):
    maintenance_costs_sql = (
        "SELECT station_uuid, year, operational_date, "
        "       maintenance_cost_total "
        f" FROM {module5_data} "
        f" JOIN {station_registrations_data} USING (station_uuid) "
        f" JOIN {import_metadata} USING (upload_id) "
        " WHERE submission_status in ('Approved', 'Submitted') "
        " AND caas = 0 "
        """AND (
            num_fed_funded_ports > 0
            OR (
                NEVI = 1
                OR CFI = 1
                OR EVC_RAA = 1
                OR CMAQ = 1
                OR CRP = 1
                OR OTHER = 1
            )
        )"""
    )

    return [
        dict(zip(["station_uuid", "year", "operational_date", "maintenance_cost_total"], row))
        for row in execute_query_with_filters(
            cursor=cursor,
            query=maintenance_costs_sql,
            filters=filters,
            logger=logger
        )
    ]
