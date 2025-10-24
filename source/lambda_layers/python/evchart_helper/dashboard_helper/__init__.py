from datetime import date, datetime
import uuid
from functools import cache

from evchart_helper.custom_exceptions import (
    EvChartFeatureStoreConnectionError,
    EvChartMissingOrMalformedHeadersError,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.station_helper import is_valid_station
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

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


def validate_filters(cursor, filters):
    try:
        if filters["station"] != "All":
            is_valid_station(filters["station"], cursor)
        if filters["dr_id"] != "All":
            uuid.UUID(str(filters["dr_id"]))
        if filters["sr_id"] != "All" and filters["sr_id"] != "None":
            uuid.UUID(str(filters["sr_id"]))
        if filters["year"] != "All":
            datetime.strptime(filters["year"], "%Y")
            filters["year"] = int(filters["year"])
        return filters
    except Exception as e:
        raise EvChartMissingOrMalformedHeadersError(f"Unable to validate filters: {e}") from e


def execute_query_with_filters(cursor, query, filters, logger, group_by=()):
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

    query += generate_query_filters(filters, logger)
    query += f"{group_by_clause}"

    logger.debug("EXECUTE_QUERY_WITH_FILTERS %s %s", query, filters)
    cursor.execute(query, filters)
    return cursor.fetchall()


def generate_query_filters(filters, logger):
    if filters["dr_id"] == "All":
        query_filter = " AND dr_id <> '154ecdd3-d864-4110-916b-9c1287bb31e8' "
        if filters["sr_id"] == "None":
            query_filter += (
                f" AND {station_registrations_data}.station_uuid NOT IN ( "
                f"   SELECT station_uuid from {authorized_station_data} "
                " ) "
            )
    else:
        query_filter = " AND dr_id = %(dr_id)s "
        if filters["sr_id"] != "All":
            if filters["sr_id"] != "None":
                query_filter += (
                    f" AND {station_registrations_data}.station_uuid IN ( "
                    f"   SELECT station_uuid from {authorized_station_data} "
                    "    WHERE dr_id = %(dr_id)s and sr_id = %(sr_id)s"
                    " ) "
                )
            else:
                query_filter += (
                    f" AND {station_registrations_data}.station_uuid NOT IN ( "
                    f"   SELECT station_uuid from {authorized_station_data} "
                    "    WHERE dr_id = %(dr_id)s"
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
