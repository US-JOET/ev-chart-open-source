"""
APIGetDashboardPPFederallyFundedNetworkSize

Generate and execute all the relevant queries necessary and provide the resulting data to the
frontend for the program performance dashboard Federally Funded Network Size.
"""

from datetime import date
import json
import logging
from collections import Counter
from dateutil.relativedelta import relativedelta

from evchart_helper import aurora
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedHeadersError,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.dashboard_helper import (
    execute_query_with_filters,
    generate_query_filters,
    get_dr_id,
    get_prior_quarter_window,
    get_sr_id,
    get_station,
    validate_filters,
    validate_org,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from evchart_helper.station_helper import (
    get_fed_funded_filter,
)
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature

logger = logging.getLogger("APIGetDashboardPPReliability")
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


@SessionManager.check_session()
@feature_enablement_check(Feature.JO_PP_DASHBOARD)
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(
                event=event, api="APIGetDashboardPPReliability", action_type="READ"
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

            most_recent_port_data = count_section3_uptime_most_recent(
                get_official_uptime_data(cursor, filters), filters["year"]
            )
            json_output = {"official_uptime": {}, "unofficial_uptime": {}}
            json_output["official_uptime"].update(
                count_section3_official_reliability(most_recent_port_data)
            )
            json_output["unofficial_uptime"].update(
                count_section3_reliability(get_unofficial_port_uptime_data(cursor, filters))
            )

            json_output.update({"avg_outage": get_outage_data(cursor, filters)})

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


def count_section3_reliability(port_uptime_data):
    window = get_prior_quarter_window(date.today())

    port_outage_duration = Counter()
    port_operational_date = {}
    port_type = {}
    count = Counter(
        {
            "num_ports_meeting_uptime_req": 0,
            "num_l2_chargers_not_meeting_req": 0,
            "num_dcfc_chargers_not_meeting_req": 0,
            "total_ports_with_uptime_activity": 0,
        }
    )

    for d in port_uptime_data:
        if d.get("outage_id").date() > window["end"]:
            continue
        if d.get("outage_id").date() < window["start"]:
            continue
        if d.get("outage_duration") is None:
            continue
        port_uuid = d.get("port_uuid")
        port_outage_duration[port_uuid] += d.get("outage_duration")
        port_operational_date[port_uuid] = d.get("operational_date")
        port_type[port_uuid] = d.get("port_type")

    for port_uuid, outage_duration in port_outage_duration.items():
        uptime_window = window["end"] - port_operational_date[port_uuid]
        uptime_max_minutes = uptime_window.days * 1440
        if uptime_max_minutes > 0:
            count["total_ports_with_uptime_activity"] += 1
            if outage_duration / uptime_max_minutes <= 0.03:
                count["num_ports_meeting_uptime_req"] += 1
            else:
                if port_type[port_uuid] == "L2":
                    count["num_l2_chargers_not_meeting_req"] += 1
                elif port_type[port_uuid] == "DCFC":
                    count["num_dcfc_chargers_not_meeting_req"] += 1

    if count["total_ports_with_uptime_activity"] == 0:
        return {
            "reliability_metrics_available": False,
            "total_ports_with_uptime_activity": 0,
            "percentage_ports_not_meeting_uptime_req": None,
            "percentage_ports_meeting_uptime_req": None,
        }

    count["percentage_ports_meeting_uptime_req"] = round(
        number=float(count["num_ports_meeting_uptime_req"] / len(port_outage_duration)), ndigits=2
    )
    count["percentage_ports_not_meeting_uptime_req"] = round(
        number=(1.0 - count["percentage_ports_meeting_uptime_req"]), ndigits=2
    )

    return {"reliability_metrics_available": True} | count


def count_section3_official_reliability(port_uptime_data):
    port_uptime_duration = Counter()
    port_operational_date = {}
    port_type = {}
    count = Counter(
        {
            "num_ports_meeting_uptime_req": 0,
            "num_l2_chargers_not_meeting_req": 0,
            "num_dcfc_chargers_not_meeting_req": 0,
            "total_ports_with_uptime_activity": 0,
        }
    )
    for row in port_uptime_data:
        data = port_uptime_data[row]
        if data.get("uptime") == "" or data.get("uptime") is None:
            continue
        port_uuid = data.get("port_uuid")
        port_uptime_duration[port_uuid] += data.get("uptime")
        port_operational_date[port_uuid] = data.get("operational_date")
        port_type[port_uuid] = data.get("port_type")
    for port_uuid, uptime in port_uptime_duration.items():
        count["total_ports_with_uptime_activity"] += 1
        if uptime >= 97:
            count["num_ports_meeting_uptime_req"] += 1
        else:
            if port_type[port_uuid] == "L2":
                count["num_l2_chargers_not_meeting_req"] += 1
            elif port_type[port_uuid] == "DCFC":
                count["num_dcfc_chargers_not_meeting_req"] += 1
    if count["total_ports_with_uptime_activity"] == 0:
        return {
            "reliability_metrics_available": False,
            "total_ports_with_uptime_activity": 0,
            "percentage_ports_not_meeting_uptime_req": None,
            "percentage_ports_meeting_uptime_req": None,
        }
    count["percentage_ports_meeting_uptime_req"] = round(
        number=float(count["num_ports_meeting_uptime_req"] / len(port_uptime_duration)), ndigits=2
    )
    count["percentage_ports_not_meeting_uptime_req"] = round(
        number=(1.0 - count["percentage_ports_meeting_uptime_req"]), ndigits=2
    )
    return {"reliability_metrics_available": True} | count


def count_section3_uptime_most_recent(port_uptime_data, reporting_year=date.today().year):
    most_recent_data = {}
    # today = date.today()

    if reporting_year == "All":
        reporting_year = date.today().year
    for d in port_uptime_data:
        operational_date = d.get("operational_date")
        uptime_reporting_start = d.get("uptime_reporting_start")
        uptime_reporting_end = d.get("uptime_reporting_end")
        uptime_reporting_end_year = uptime_reporting_end.year

        reporting_start_plus_1_year = (
            uptime_reporting_start + relativedelta(years=1) - relativedelta(days=1)
        )  # inclusive
        uptime_reporting_is_at_least_1_year = uptime_reporting_end >= reporting_start_plus_1_year

        year_after_operational_date = (
            operational_date + relativedelta(years=1) - relativedelta(days=1)
        )  # inclusive

        has_been_operating_plus_1_year = uptime_reporting_end.date() >= year_after_operational_date

        if (
            has_been_operating_plus_1_year
            and uptime_reporting_end_year <= reporting_year
            and uptime_reporting_is_at_least_1_year
        ):
            if most_recent_data.get((d.get("station_uuid"), d.get("port_id"))):
                if uptime_reporting_end < most_recent_data.get(
                    (d.get("station_uuid"), d.get("port_id")), {}
                ).get("uptime_reporting_end"):
                    continue
            most_recent_data[(d.get("station_uuid"), d.get("port_id"))] = d
    return most_recent_data


def get_official_uptime_data(cursor, filters):
    # MySQL does not support full outer join, needs to be emulated
    # https://dev.mysql.com/doc/refman/8.4/en/outer-join-simplification.html
    filter_sql = generate_query_filters(filters, logger)
    filter_sql += f" {get_fed_funded_filter(station_registrations_data, station_ports_data)}"
    official_port_uptime_sql = (
        f" SELECT {station_ports_data}.station_uuid, {station_ports_data}.port_uuid, {station_ports_data}.port_id, operational_date, uptime_reporting_start, uptime_reporting_end, uptime "
        f"  FROM {module3_data} "
        f"  LEFT JOIN {station_registrations_data} USING (station_uuid) "
        f"  LEFT JOIN {station_ports_data} ON {station_ports_data}.station_uuid={station_registrations_data}.station_uuid "
        f"    AND {station_ports_data}.port_id={module3_data}.port_id "
        f"  JOIN {import_metadata} using (upload_id) "
        "   WHERE submission_status in ('Approved', 'Submitted') "
        " AND federally_funded = 1 "
        f" {filter_sql} "
        " UNION ALL "
        f" SELECT {station_ports_data}.station_uuid, {station_ports_data}.port_uuid, {station_ports_data}.port_id, operational_date, uptime_reporting_start, uptime_reporting_end, uptime "
        f"  FROM {module3_data} "
        f"  RIGHT JOIN {station_registrations_data} USING (station_uuid) "
        f"  LEFT JOIN {station_ports_data} ON {station_ports_data}.station_uuid={station_registrations_data}.station_uuid "
        f"    AND {station_ports_data}.port_id={module3_data}.port_id "
        f"  JOIN {import_metadata} using (upload_id) "
        "   WHERE submission_status in ('Approved', 'Submitted') "
        " AND federally_funded = 1 "
        f" {filter_sql} "
        " UNION ALL "
        f" SELECT {station_ports_data}.station_uuid, {station_ports_data}.port_uuid, {station_ports_data}.port_id, operational_date, uptime_reporting_start, uptime_reporting_end, uptime "
        f"  FROM {module3_data} "
        f"  LEFT JOIN {station_registrations_data} USING (station_uuid) "
        f"  RIGHT JOIN {station_ports_data} ON {station_ports_data}.station_uuid={station_registrations_data}.station_uuid "
        f"    AND {station_ports_data}.port_id={module3_data}.port_id "
        f"  JOIN {import_metadata} using (upload_id) "
        "   WHERE submission_status in ('Approved', 'Submitted') "
        " AND federally_funded = 1 "
        f" {filter_sql} "
        " UNION ALL "
        f" SELECT {station_ports_data}.station_uuid, {station_ports_data}.port_uuid, {station_ports_data}.port_id, operational_date, uptime_reporting_start, uptime_reporting_end, uptime "
        f"  FROM {module3_data} "
        f"  RIGHT JOIN {station_registrations_data} USING (station_uuid) "
        f"  RIGHT JOIN {station_ports_data} ON {station_ports_data}.station_uuid={station_registrations_data}.station_uuid "
        f"    AND {station_ports_data}.port_id={module3_data}.port_id "
        f"  JOIN {import_metadata} using (upload_id) "
        "   WHERE submission_status in ('Approved', 'Submitted') "
        " AND federally_funded = 1 "
        f"  {filter_sql} "
    )
    columns = [
        "station_uuid",
        "port_uuid",
        "port_id",
        "operational_date",
        "uptime_reporting_start",
        "uptime_reporting_end",
        "uptime",
    ]
    return [
        dict(zip(columns, row))
        for row in execute_query_with_filters(
            cursor=cursor, query=official_port_uptime_sql, filters=filters, logger=logger
        )
    ]


def get_unofficial_port_uptime_data(cursor, filters):
    port_uptime_sql = (
        f"SELECT station_uuid, {station_ports_data}.port_uuid, port_type, "
        "       operational_date, outage_id, outage_duration "
        f"  FROM {module4_data} "
        f"  JOIN {station_ports_data} USING (station_uuid, port_id) "
        f"  JOIN {station_registrations_data} using (station_uuid) "
        f"  JOIN {import_metadata} using (upload_id) "
        "   WHERE submission_status in ('Approved', 'Submitted') "
        "     AND federally_funded = 1 "
        "     AND operational_date <= outage_id "
    )

    columns = [
        "station_uuid",
        "port_uuid",
        "port_type",
        "operational_date",
        "outage_id",
        "outage_duration",
    ]
    return [
        dict(zip(columns, row))
        for row in execute_query_with_filters(
            cursor=cursor, query=port_uptime_sql, filters=filters, logger=logger
        )
    ]


def get_outage_data(cursor, filters):
    outage_sql = (
        "SELECT SUM(outage_duration)/COUNT(outage_duration) "
        f" FROM {module4_data} "
        f" JOIN {station_registrations_data} using (station_uuid) "
        f" JOIN {station_ports_data} USING (station_uuid, port_id) "
        f" JOIN {import_metadata} using (upload_id) "
        "WHERE outage_duration > 0 "
        "AND submission_status in ('Approved', 'Submitted') "
        "AND federally_funded = 1 "
    )

    try:
        return round(
            float(
                execute_query_with_filters(cursor=cursor, query=outage_sql, filters=filters, logger=logger)[0][0]
            ),
            2,
        )
    except TypeError:
        return None
