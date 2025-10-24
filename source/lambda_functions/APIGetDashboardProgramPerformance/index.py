"""
APIGetDashboardProgramPerformance

Generate and execute all the relevant queries necessary and provide the resulting data to the
frontend for the program performance dashboard.
"""

import json
import logging
import uuid
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from functools import cache
from statistics import StatisticsError, median, stdev

from dateutil.relativedelta import relativedelta
from evchart_helper import aurora
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartFeatureStoreConnectionError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedHeadersError,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from evchart_helper.station_helper import is_valid_station
from feature_toggle import FeatureToggleService, feature_enablement_check
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


@cache
def federally_funded_ports(cursor):
    federally_funded_ports_sql = (
        "SELECT DISTINCT station_uuid, port_id "
        f" FROM {station_ports_data} "
        " WHERE federally_funded = 1"
    )
    cursor.execute(federally_funded_ports_sql)
    return set(cursor.fetchall())


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
            cursor=cursor,
            query=station_ports_sql,
            filters=filters,
        )
    ]


def generate_query_filters(filters):
    if filters["dr_id"] == "All":
        query_filter = " AND dr_id <> '154ecdd3-d864-4110-916b-9c1287bb31e8' "
    else:
        query_filter = " AND dr_id = %(dr_id)s "
        if filters["sr_id"] != "All":
            query_filter += (
                f" AND {station_registrations_data}.station_uuid IN ( "
                f"   SELECT station_uuid from {authorized_station_data} "
                "    WHERE dr_id = %(dr_id)s and sr_id = %(sr_id)s"
                " ) "
            )
        if filters["station"] != "All":
            query_filter += f" AND {station_registrations_data}.station_uuid = " "%(station)s "
    if filters["year"] != "All":
        query_filter += " AND year = %(year)s "
    feature_toggle_service = FeatureToggleService()
    try:
        if (
            feature_toggle_service.get_feature_toggle_by_enum(Feature.SR_ADDS_STATION, logger)
            == "True"
        ):
            query_filter += f" AND {station_registrations_data}.status = 'Active' "
    except EvChartFeatureStoreConnectionError:
        logger.debug("Unable to check feature toggle")
    return query_filter


def execute_query_with_filters(cursor, query, filters, group_by=()):
    """
    when called with SQL code and a DR id and SR id, will filter results by
    DR id and/or SR id if provided,
    or not if DR or SR id is specified as 'All'
    """
    if not isinstance(group_by, (tuple, list)):
        raise EvChartMissingOrMalformedHeadersError(
            log_obj=None, message="group_by must be tuple or list"
        )
    if len(group_by) > 0:
        group_by_clause = f" GROUP BY {', '.join(group_by)} "
    else:
        group_by_clause = ""

    query += generate_query_filters(filters)
    query += f"{group_by_clause}"
    logger.debug("EXECUTE_QUERY_WITH_FILTERS %s %s", query, filters)
    cursor.execute(query, filters)
    return cursor.fetchall()


def capital_cost_stations_ports(cursor, filters):
    query_filter = generate_query_filters(filters)
    stations_ports_sql = (
        "SELECT COUNT(DISTINCT station_uuid), COUNT(DISTINCT port_uuid) "
        f"FROM {station_ports_data} "
        "WHERE station_uuid IN ("
        "  SELECT station_uuid "
        f"   FROM {module9_data} "
        f"   JOIN {station_registrations_data} USING (station_uuid) "
        f"   JOIN {import_metadata} USING (upload_id) "
        f"  WHERE submission_status in ('Approved', 'Submitted') "
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
            cursor=cursor, query=charging_sessions_sql, filters=filters
        )
    ]


def get_station_registrations(cursor, filters):
    station_registrations_sql = (
        "SELECT operational_date, station_uuid " f"FROM {station_registrations_data} " " WHERE 1=1 "
    )

    columns = ["operational_date", "station_uuid"]
    # no filtering by year for stations at the moment
    output = [
        dict(zip(columns, row))
        for row in execute_query_with_filters(
            cursor=cursor, query=station_registrations_sql, filters=filters
        )
    ]
    return output


def get_official_uptime_data(cursor, filters):
    # MySQL does not support full outer join, needs to be emulated
    # https://dev.mysql.com/doc/refman/8.4/en/outer-join-simplification.html
    filter_sql = generate_query_filters(filters)
    official_port_uptime_sql = (
        f" SELECT {station_ports_data}.station_uuid, {station_ports_data}.port_uuid, {station_ports_data}.port_id, operational_date, uptime_reporting_start, uptime_reporting_end, uptime "
        f"  FROM {module3_data} "
        f"  LEFT JOIN {station_registrations_data} USING (station_uuid) "
        f"  LEFT JOIN {station_ports_data} ON {station_ports_data}.station_uuid={station_registrations_data}.station_uuid "
        f"    AND {station_ports_data}.port_id={module3_data}.port_id "
        f"  JOIN {import_metadata} using (upload_id) "
        "   WHERE submission_status in ('Approved', 'Submitted') "
        "   AND federally_funded = 1 "
        f" {filter_sql} "
        " UNION ALL "
        f" SELECT {station_ports_data}.station_uuid, {station_ports_data}.port_uuid, {station_ports_data}.port_id, operational_date, uptime_reporting_start, uptime_reporting_end, uptime "
        f"  FROM {module3_data} "
        f"  RIGHT JOIN {station_registrations_data} USING (station_uuid) "
        f"  LEFT JOIN {station_ports_data} ON {station_ports_data}.station_uuid={station_registrations_data}.station_uuid "
        f"    AND {station_ports_data}.port_id={module3_data}.port_id "
        f"  JOIN {import_metadata} using (upload_id) "
        "   WHERE submission_status in ('Approved', 'Submitted') "
        "  AND federally_funded = 1 "
        f" {filter_sql} "
        " UNION ALL "
        f" SELECT {station_ports_data}.station_uuid, {station_ports_data}.port_uuid, {station_ports_data}.port_id, operational_date, uptime_reporting_start, uptime_reporting_end, uptime "
        f"  FROM {module3_data} "
        f"  LEFT JOIN {station_registrations_data} USING (station_uuid) "
        f"  RIGHT JOIN {station_ports_data} ON {station_ports_data}.station_uuid={station_registrations_data}.station_uuid "
        f"    AND {station_ports_data}.port_id={module3_data}.port_id "
        f"  JOIN {import_metadata} using (upload_id) "
        "   WHERE submission_status in ('Approved', 'Submitted') "
        "   AND federally_funded = 1 "
        f" {filter_sql} "
        " UNION ALL "
        f" SELECT {station_ports_data}.station_uuid, {station_ports_data}.port_uuid, {station_ports_data}.port_id, operational_date, uptime_reporting_start, uptime_reporting_end, uptime "
        f"  FROM {module3_data} "
        f"  RIGHT JOIN {station_registrations_data} USING (station_uuid) "
        f"  RIGHT JOIN {station_ports_data} ON {station_ports_data}.station_uuid={station_registrations_data}.station_uuid "
        f"    AND {station_ports_data}.port_id={module3_data}.port_id "
        f"  JOIN {import_metadata} using (upload_id) "
        "   WHERE submission_status in ('Approved', 'Submitted') "
        "   AND federally_funded = 1 "
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
            cursor=cursor, query=official_port_uptime_sql, filters=filters
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
        for row in execute_query_with_filters(cursor=cursor, query=port_uptime_sql, filters=filters)
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
    )

    try:
        return round(
            float(
                execute_query_with_filters(cursor=cursor, query=outage_sql, filters=filters)[0][0]
            ),
            2,
        )
    except TypeError:
        return None


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
    )
    return [
        dict(zip(capital_costs_total_and_federal, row))
        for row in execute_query_with_filters(
            cursor=cursor, query=capital_costs_sql, filters=filters
        )
    ]


def maintenance_costs(cursor, filters):
    maintenance_costs_sql = (
        "SELECT station_uuid, year, operational_date, "
        "       maintenance_cost_total "
        f" FROM {module5_data} "
        f" JOIN {station_registrations_data} USING (station_uuid) "
        f" JOIN {import_metadata} USING (upload_id) "
        " WHERE submission_status in ('Approved', 'Submitted') "
        " AND caas = 0 "
    )

    return [
        dict(zip(["station_uuid", "year", "operational_date", "maintenance_cost_total"], row))
        for row in execute_query_with_filters(
            cursor=cursor,
            query=maintenance_costs_sql,
            filters=filters,
        )
    ]


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
        uptime_reporting_is_at_least_1_year = (
            uptime_reporting_end >= reporting_start_plus_1_year
        )

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
            json_output = {"official_uptime": {}, "unofficial_uptime": {}}
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
            filter_year = filters["year"]
            filters["year"] = "All"
            # handling network size
            json_output.update(
                count_section2_network(
                    station_registrations=get_station_registrations(cursor, filters),
                    station_ports=get_federally_funded_station_ports(cursor, filters),
                )
            )
            filters["year"] = filter_year

            # handling reliability
            most_recent_port_data = count_section3_uptime_most_recent(
                get_official_uptime_data(cursor, filters), filters["year"]
            )
            json_output["official_uptime"].update(
                count_section3_official_reliability(most_recent_port_data)
            )
            json_output["unofficial_uptime"].update(
                count_section3_reliability(get_unofficial_port_uptime_data(cursor, filters))
            )

            json_output.update({"avg_outage": get_outage_data(cursor, filters)})

            # handling costs
            json_output.update(count_section4_capital_cost(data=capital_costs(cursor, filters)))
            json_output.update(
                count_section4_maintenance_cost(
                    data=maintenance_costs(cursor, filters), year=filters["year"]
                )
            )
            json_output.update(capital_cost_stations_ports(cursor, filters))

            json_output.update(
                count_section5_energy(cursor=cursor, data=charging_sessions(cursor, filters))
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


# helper method to validate that current user is JO.
# raises auth error otherwise.
def validate_org(token):
    # getting recipient_type from the auth token
    recipient_type = token.get("recipient_type")
    if recipient_type.lower() == "joet":
        return "JO"
    if recipient_type.lower() == "direct-recipient":
        return "DR"
    raise EvChartUserNotAuthorizedError(message="User not authorized to view dashboard data.")


# helper method that gets the dr_id from path parameters.
# sets it to default_dr_id if dr_id is not provided
def get_dr_id(path_parameters, default_dr_id):
    if path_parameters:
        return path_parameters.get("dr_id", default_dr_id)
    return default_dr_id


def get_station(path_parameters, default_station):
    if path_parameters:
        return path_parameters.get("station", default_station)
    return default_station


# helper method that gets the sr_id from path parameters.
# sets it to default_sr_id if sr_id is not provided
def get_sr_id(path_parameters, default_sr_id):
    if path_parameters:
        return path_parameters.get("sr_id", default_sr_id)
    return default_sr_id


# helper method that gets the year from path parameters.
# sets it to default_year if dr_id is not provided
def get_year(path_parameters, default_year):
    if path_parameters:
        return path_parameters.get("year", default_year)
    return default_year


@cache
def operational_days(operational_date, reporting_year):
    date_range_start = max(operational_date, date(year=int(reporting_year), month=1, day=1))
    date_range_end = date(year=int(reporting_year), month=12, day=31)
    delta = date_range_end - date_range_start

    operational_days_inclusive = delta.days + 1
    operational_days_inclusive = max(operational_days_inclusive, 0)
    operational_days_inclusive = min(operational_days_inclusive, 365)

    return operational_days_inclusive


@cache
def normalized_monthly_cost(cost, days):
    return float(cost) / (days / MONTH_LENGTH)


@cache
def get_prior_quarter_window(today):
    if today.month in {1, 2, 3}:
        start = date(year=today.year - 1, month=1, day=1)
        end = date(year=today.year - 1, month=12, day=31)
    elif today.month in {4, 5, 6}:
        start = date(year=today.year - 1, month=4, day=1)
        end = date(year=today.year, month=3, day=31)
    elif today.month in {7, 8, 9}:
        start = date(year=today.year - 1, month=7, day=1)
        end = date(year=today.year, month=6, day=30)
    else:
        start = date(year=today.year - 1, month=10, day=1)
        end = date(year=today.year, month=9, day=30)

    return {"start": start, "end": end}


def validate_filters(cursor, filters):
    try:
        if filters["station"] != "All":
            is_valid_station(filters["station"], cursor)
        if filters["sr_id"] != "All":
            uuid.UUID(str(filters["sr_id"]))
        if filters["dr_id"] != "All":
            uuid.UUID(str(filters["dr_id"]))
        if filters["year"] != "All":
            datetime.strptime(filters["year"], "%Y")
            filters["year"] = int(filters["year"])
        logger.debug("Filters: %s", filters)
        return filters
    except Exception as e:
        raise EvChartMissingOrMalformedHeadersError(f"Unable to validate filters: {e}") from e
