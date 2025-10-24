"""
APIGetDashboardProgramPerformance

Generate and execute all the relevant queries necessary and provide the resulting data to the
frontend for the program performance dashboard.
"""

import json
import logging

from collections import Counter

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
    generate_query_filters,
    get_dr_id,
    get_sr_id,
    get_station,
    get_year,
    validate_filters,
    validate_org,
)
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature

logger = logging.getLogger("APIGetDashboardProgramPerformance")
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
                event=event, api="APIGetDashboardProgramPerformance", action_type="READ"
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
            json_output = count_section4_capital_cost(data=capital_costs(cursor, filters))

            json_output.update(capital_cost_stations_ports(cursor, filters))

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


def capital_cost_stations_ports(cursor, filters):
    query_filter = generate_query_filters(filters, logger=logger)
    stations_ports_sql = (
        "SELECT COUNT(DISTINCT station_uuid), COUNT(DISTINCT port_uuid) "
        f"FROM {station_ports_data} "
        "WHERE station_uuid IN ("
        "  SELECT station_uuid "
        f"   FROM {module9_data} "
        f"   JOIN {station_registrations_data} USING (station_uuid) "
        f"   JOIN {import_metadata} USING (upload_id) "
        f"  WHERE submission_status in ('Approved', 'Submitted') "
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
        "     AND equipment_cost_total is NOT NULL "
        "     AND equipment_install_cost_total is NOT NULL "
        "     AND service_cost_total is NOT NULL "
        "     AND dist_sys_cost_total is NOT NULL "
        f"    {query_filter} "
        ") "
    )
    logger.debug("STATIONS_PORTS QUERY %s %s", stations_ports_sql, filters)
    cursor.execute(stations_ports_sql, filters)
    stations, ports = cursor.fetchone()
    return {
        "capital_cost_stations_count": stations,
        "capital_cost_ports_count": ports,
    }

def capital_costs(cursor, filters):
    capital_costs_total_and_federal = ["station_uuid", "nevi"]
    for ccc in capital_cost_categories:
        capital_costs_total_and_federal.extend([f"{ccc}_total", f"{ccc}_federal"])

    capital_costs_sql = (
        f"SELECT {','.join(capital_costs_total_and_federal)} "
        f"  FROM {module9_data} "
        f"  JOIN {station_registrations_data} USING (station_uuid) "
        f"  JOIN {import_metadata} USING (upload_id) "
        " WHERE submission_status in ('Approved', 'Submitted') "
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
        dict(zip(capital_costs_total_and_federal, row))
        for row in execute_query_with_filters(
            cursor=cursor, query=capital_costs_sql, filters=filters, logger=logger
        )
    ]

def count_section4_capital_cost(data):
    count = Counter({"unique_nevi_stations": 0})

    for d in data:
        if any(d.get(f"{ccc}_total") is None for ccc in capital_cost_categories):
            continue

        incremental_total = sum(d.get(f"{ccc}_total") for ccc in capital_cost_categories)
        incremental_federal = sum(d.get(f"{ccc}_federal") for ccc in capital_cost_categories)
        incremental_nonfederal = sum(
            d.get(f"{ccc}_total") - d.get(f"{ccc}_federal")
            for ccc in capital_cost_categories
            if d.get(f"{ccc}_total") > d.get(f"{ccc}_federal")
        )

        count["deployment_cost"] += incremental_total
        count["federal_funding"] += incremental_federal
        count["nonfederal_funding"] += incremental_nonfederal

        if d.get("nevi") == 1:
            count["unique_nevi_stations"] += 1
            count["capital_costs_total_nevi"] += incremental_total

    if count["unique_nevi_stations"] == 0:
        count["capital_cost_metrics_available"] = False
        count["average_nevi_capital_cost"] = None
    else:
        count["capital_cost_metrics_available"] = True
        count["average_nevi_capital_cost"] = round(
            float(count["capital_costs_total_nevi"] / count["unique_nevi_stations"]), 2
        )

    for category in [
        "federal_funding",
        "capital_costs_total_nevi",
        "nonfederal_funding",
        "deployment_cost",
    ]:
        count[category] = float(count[category])
    return count
