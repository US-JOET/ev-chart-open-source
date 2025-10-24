"""
APIGetDashboardPPFederallyFundedNetworkSize

Generate and execute all the relevant queries necessary and provide the resulting data to the
frontend for the program performance dashboard Federally Funded Network Size.
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
    get_station,
    validate_filters,
)
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from evchart_helper.dashboard_helper import validate_org, get_dr_id, get_sr_id
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature

logger = logging.getLogger("APIGetDashboardPPFederallyFundedNetworkSize")
logger.setLevel(logging.DEBUG)

station_registrations_data = ModuleDataTables["RegisteredStations"].value
authorized_station_data = ModuleDataTables["StationAuthorizations"].value
station_ports_data = ModuleDataTables["StationPorts"].value


@SessionManager.check_session()
@feature_enablement_check(Feature.JO_PP_DASHBOARD)
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(
                event=event, api="APIGetDashboardPPFederallyFundedNetworkSize", action_type="READ"
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
            filters = validate_filters(cursor, filters)

            # Filter year was always set to ALL for this call so I removed setting it.
            # handling network size
            json_output = count_section2_network(
                station_registrations=get_station_registrations(cursor, filters),
                station_ports=get_federally_funded_station_ports(cursor, filters),
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


def count_section2_network(station_registrations, station_ports):
    count = Counter(
        {
            "total_stations": 0,
            "total_ports": 0,
            "undefined_ports": 0,
            "l2_ports": 0,
            "dcfc_ports": 0,
        }
    )

    if len(station_registrations) == 0:
        count["station_data_available"] = False
    else:
        count["station_data_available"] = True

    for _ in station_registrations:
        count["total_stations"] += 1

    for sp in station_ports:
        count["total_ports"] += 1
        if sp.get("port_type") == "L2":
            count["l2_ports"] += 1
        elif sp.get("port_type") == "DCFC":
            count["dcfc_ports"] += 1
        elif sp.get("port_type") == "":
            count["undefined_ports"] += 1

    return count


def get_station_registrations(cursor, filters):
    station_registrations_sql = (
        "SELECT operational_date, station_uuid "
        f"FROM {station_registrations_data} "
        """WHERE (
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

    columns = ["operational_date", "station_uuid"]
    # no filtering by year for stations at the moment
    output = [
        dict(zip(columns, row))
        for row in execute_query_with_filters(
            cursor=cursor, query=station_registrations_sql, filters=filters, logger=logger
        )
    ]
    return output


def get_federally_funded_station_ports(cursor, filters):
    station_ports_sql = (
        "SELECT operational_date, port_type, port_uuid "
        f" FROM {station_registrations_data} "
        f" JOIN {station_ports_data} USING (station_uuid) "
        " WHERE federally_funded = 1 "
    )

    columns = ["operational_date", "port_type", "port_uuid"]
    return [
        dict(zip(columns, row))
        for row in execute_query_with_filters(
            cursor=cursor, query=station_ports_sql, filters=filters, logger=logger
        )
    ]
