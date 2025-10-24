"""
APIGetDashboardPPEnergyUsage

Generate and execute all the relevant queries necessary and provide the resulting data to the
frontend for the program performance dashboard.
"""

from collections import Counter
from decimal import Decimal
import json
import logging
from statistics import StatisticsError, median, stdev

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
    federally_funded_ports,
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

logger = logging.getLogger("APIGetDashboardPPEnergyUsage")
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
                event=event, api="APIGetDashboardPPEnergyUsage", action_type="READ"
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
            json_output = count_section5_energy(
                cursor=cursor, data=charging_sessions(cursor, filters)
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


def charging_sessions(cursor, filters):
    charging_sessions_sql = (
        "SELECT TIMESTAMPDIFF(minute, session_start, session_end) "
        "       AS session_duration, session_id, "
        "          energy_kwh, power_kw, port_id, station_uuid, nevi "
        f" FROM {module2_data} "
        f" JOIN {station_registrations_data} USING (station_uuid) "
        f" JOIN {station_ports_data} USING (station_uuid, port_id) "
        f" JOIN {import_metadata} USING (upload_id) "
        " WHERE submission_status in ('Approved', 'Submitted') "
        " AND federally_funded = 1 "
        f"""AND (
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

    columns = [
        "session_duration",
        "session_id",
        "energy_kwh",
        "power_kw",
        "port_id",
        "station_uuid",
        "nevi",
    ]
    return [
        dict(zip(columns, row))
        for row in execute_query_with_filters(
            cursor=cursor, query=charging_sessions_sql, filters=filters, logger=logger
        )
    ]


def count_section5_energy(cursor, data):
    if len(data) == 0:
        return {
            "energy_metrics_available": False,
            "total_charging_sessions": 0,
            "cumulative_energy_federal_ports": 0.0,
            "dispensing_150kw_sessions": 0,
            "median_charging_session": None,
            "mode_charging_session": None,
            "average_charging_power": None,
            "percentage_nevi_dispensing_150kw": None,
            "stdev_charging_session": None,
        }

    count = Counter(
        {
            "total_charging_sessions": 0,
            "cumulative_energy_federal_ports": Decimal(0.0),
            "dispensing_150kw_sessions": 0,
        }
    )
    session_durations = []
    for d in data:
        # (None or -1) resolves to -1
        session_duration = d.get("session_duration") or -1
        if session_duration < 0 or session_duration > 1440:
            continue
        count["total_charging_sessions"] += 1
        count["total_duration"] += d.get("session_duration") or 0
        session_durations.append(d.get("session_duration") or 0)

        power_kwh = d.get("power_kw") or 0
        count["total_charging_power"] += power_kwh
        if (d.get("station_uuid"), d.get("port_id")) in federally_funded_ports(cursor):
            count["cumulative_energy_federal_ports"] += d.get("energy_kwh") or 0

        if d.get("nevi") == 1 and power_kwh > 150:
            count["dispensing_150kw_sessions"] += 1

    # Only negatives were in data Calculation Error due to bad data
    if len(session_durations) == 0:
        return {
            "energy_metrics_available": False,
            "total_charging_sessions": 0,
            "cumulative_energy_federal_ports": 0.0,
            "dispensing_150kw_sessions": 0,
            "median_charging_session": None,
            "mode_charging_session": None,
            "average_charging_power": None,
            "percentage_nevi_dispensing_150kw": None,
            "stdev_charging_session": None,
        }

    count["energy_metrics_available"] = True
    count["median_charging_session"] = median(session_durations)

    try:
        count["stdev_charging_session"] = round(stdev(session_durations), 2)
    except StatisticsError:
        count["stdev_charging_session"] = None
    count["average_charging_duration"] = round(
        float(count["total_duration"] / count["total_charging_sessions"]), 2
    )
    count["average_charging_power"] = round(
        number=float(count["total_charging_power"] / count["total_charging_sessions"]), ndigits=2
    )
    count["percentage_nevi_dispensing_150kw"] = round(
        number=float(count["dispensing_150kw_sessions"] / count["total_charging_sessions"]),
        ndigits=2,
    )

    count["total_charging_power"] = float(count["total_charging_power"])
    return count
