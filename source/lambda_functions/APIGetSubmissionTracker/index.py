"""
APIGetSubmissionTracker

Return the submissions status for modules for various parameters.
"""

import json
import logging
import datetime
import uuid
from functools import cache

from evchart_helper import aurora
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartAuthorizationTokenInvalidError,
    EvChartMissingOrMalformedHeadersError,
    EvChartUserNotAuthorizedError,
    EvChartJsonOutputError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from evchart_helper.station_helper import get_fed_funded_filter, is_valid_station
from evchart_helper.api_helper import execute_query

from feature_toggle import FeatureToggleService, feature_enablement_check
from feature_toggle.feature_enums import Feature

logger = logging.getLogger("APIGetDashboardSubmissionTracker")
logger.setLevel(logging.DEBUG)

station_registrations_data = ModuleDataTables["RegisteredStations"].value
authorized_station_data = ModuleDataTables["StationAuthorizations"].value
import_metadata = ModuleDataTables["Metadata"].value
station_ports_data = ModuleDataTables["StationPorts"].value

one_time_module_ids = ["6", "8", "9"]
annual_module_ids = ["5", "7"]
quarterly_module_ids = ["2", "3", "4"]

submission_status_priority = {
    "Approved": 2,
    "Submitted": 2,
    "Pending": 1,
    "Rejected": 0,
    "Error": 0,
    "Draft": 0,
    "Processing": 0,
}

module_status_priority = ["not_submitted", "pending", "submitted"]


@cache
def get_reporting_details(
    operational_date=datetime.date.today(),
    period=None,
    year=None,
    quarter=None,
    today=datetime.date.today(),
):
    window_start = datetime.date.min
    window_end = datetime.date.max
    is_applicable = True

    if period == "one_time":
        deadline = datetime.date(year=operational_date.year + 1, month=3, day=1)
    elif period == "annual":
        window_start = datetime.date(year=int(year), month=1, day=1)
        window_end = datetime.date(year=int(year), month=12, day=31)
        deadline = datetime.date(year=int(year) + 1, month=3, day=1)
    elif period == "quarterly":
        if int(quarter) == 1:
            window_start = datetime.date(year=int(year), month=1, day=1)
            window_end = datetime.date(year=int(year), month=3, day=31)
            deadline = datetime.date(year=int(year), month=4, day=30)
        elif int(quarter) == 2:
            window_start = datetime.date(year=int(year), month=4, day=1)
            window_end = datetime.date(year=int(year), month=6, day=30)
            deadline = datetime.date(year=int(year), month=7, day=31)
        elif int(quarter) == 3:
            window_start = datetime.date(year=int(year), month=7, day=1)
            window_end = datetime.date(year=int(year), month=9, day=30)
            deadline = datetime.date(year=int(year), month=10, day=31)
        elif int(quarter) == 4:
            window_start = datetime.date(year=int(year), month=9, day=1)
            window_end = datetime.date(year=int(year), month=12, day=31)
            deadline = datetime.date(year=int(year) + 1, month=1, day=31)
        else:
            raise IndexError(f"invalid reporting {quarter=}")
    else:
        raise IndexError(f"invalid reporting {period=}")

    is_applicable = operational_date <= window_end
    is_open = today > window_start
    return {"is_open": is_open, "is_applicable": is_applicable, "deadline": deadline}


def get_hover_status(
    # pylint: disable=too-many-arguments,too-many-return-statements
    # pylint: disable=too-many-positional-arguments
    module_status=None,
    operational_date=datetime.date.today(),
    period=None,
    year=None,
    quarter=None,
    today=datetime.date.today(),
):
    status_set = set(
        status for module, status in module_status.items() if module.endswith("_priority")
    )
    reporting_details = get_reporting_details(
        operational_date=operational_date, period=period, year=year, quarter=quarter, today=today
    )

    if "pending" in status_set:
        return "attention"
    if status_set == {"submitted"}:
        return "submitted"
    if not reporting_details.get("is_applicable"):
        return "not_applicable"
    if today > reporting_details.get("deadline"):
        return "attention"
    if not reporting_details.get("is_open"):
        return "not_required"
    if status_set == {"submitted", "not_submitted"}:
        return "some_submitted"
    if status_set == {"not_submitted"}:
        return "none_submitted"
    return "unknown"


def get_submission_status(is_one_time, cursor, filters):
    module_union = get_table_names(is_one_time)
    submission_status_sql = (
        f"WITH station_to_upload AS ({module_union}) "
        "SELECT station_uuid, module, year, quarter, submission_status "
        f"FROM station_to_upload "
        f"JOIN {import_metadata} USING (upload_id) "
        f"JOIN {station_registrations_data} s USING (station_uuid) "
        " WHERE parent_org = %(dr_id)s "
    )
    if not is_one_time:
        submission_status_sql += " AND (year=%(year)s OR year IS NULL) "
    if filters["sr_id"] == filters["dr_id"]:
        submission_status_sql += (
            " AND station_uuid NOT IN ( "
            f"   SELECT station_uuid from {authorized_station_data} a "
            "    WHERE a.dr_id = %(dr_id)s"
            " ) "
        )
    elif filters["sr_id"] != "All":
        submission_status_sql += (
            " AND station_uuid IN ( "
            f"   SELECT station_uuid from {authorized_station_data} "
            "    WHERE s.dr_id = %(dr_id)s and sr_id = %(sr_id)s"
            " ) "
        )
    if filters["station"] != "All":
        submission_status_sql += " AND s.station_uuid = %(station)s "
    submission_status_sql += "GROUP BY station_uuid, module, year, quarter, submission_status "

    columns = ["station_uuid", "module", "year", "quarter", "submission_status"]
    logger.debug("SUBMISSION_STATUS_SQL %s %s", submission_status_sql, filters)
    cursor.execute(submission_status_sql, filters)
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_station_registrations(cursor, filters):
    sql = (
        "SELECT s.station_uuid, s.nickname, s.station_id, s.city, "
        "       s.operational_date "
        f" FROM {station_registrations_data} AS s "
        f" LEFT JOIN {authorized_station_data} AS rs "
        "       ON s.station_uuid = rs.station_uuid "
        f" LEFT JOIN {station_ports_data} AS sp"
        "       ON sp.station_uuid = s.station_uuid"
        " WHERE s.status='Active'"

    ) + get_fed_funded_filter("s", "sp")

    if filters["station"] != "All":
        sql += " AND s.station_uuid = %(station)s "
    else:
        if filters["dr_id"] == "All":
            sql += " AND s.dr_id <> '154ecdd3-d864-4110-916b-9c1287bb31e8' "
        else:
            sql += " AND s.dr_id=%(dr_id)s "
        if filters["sr_id"] == filters["dr_id"]:
            sql += (
                " AND s.station_uuid NOT IN ( "
                f"   SELECT station_uuid from {authorized_station_data} "
                "    WHERE dr_id = %(dr_id)s"
                " ) "
            )
        elif filters["sr_id"] != "All":
            sql += " AND sr_id=%(sr_id)s "

    logger.debug("STATION_REGISTRATIONS_SQL %s %s", sql, filters)
    cursor.execute(sql, filters)
    return {
        station_uuid: {
            "nickname": nickname,
            "station_id": station_id,
            "city": city,
            "operational_date": operational_date,
        }
        for station_uuid, nickname, station_id, city, operational_date in cursor.fetchall()
    }


def get_tracker_status(cursor, filters):
    tracker_status = {}
    # Get one time module data
    records = get_submission_status(True, cursor, filters)
    # get the remaining module data
    records += get_submission_status(False, cursor, filters)
    for record in records:
        year = record["year"]
        if record["module"] in one_time_module_ids:
            year = ""
        key = (record["station_uuid"], record["module"], year, record["quarter"] or "")
        tracker_status[key] = max(
            tracker_status.get(key, 0),
            submission_status_priority.get(record["submission_status"], 0),
        )
    return tracker_status


def get_response_payload(filters, tracker_status, station_registrations):
    response_payload = []
    if not filters:
        return response_payload
    for station_uuid in station_registrations:
        station_status = {"station_uuid": station_uuid}
        station_status.update(station_registrations[station_uuid])
        operational_date = station_registrations[station_uuid]["operational_date"]

        one_time_status = {}
        for module_id in one_time_module_ids:
            status = tracker_status.get((station_uuid, module_id, "", ""), 0)
            one_time_status[f"module{module_id}_priority"] = module_status_priority[status]
        one_time_status["hover_status"] = get_hover_status(
            module_status=one_time_status, operational_date=operational_date, period="one_time"
        )

        annual_status = {}
        for module_id in annual_module_ids:
            status = tracker_status.get((station_uuid, module_id, filters["year"], ""), 0)
            annual_status[f"module{module_id}_priority"] = module_status_priority[status]
        annual_status["hover_status"] = get_hover_status(
            module_status=annual_status,
            operational_date=operational_date,
            period="annual",
            year=filters["year"],
        )

        for quarter in ["1", "2", "3", "4"]:
            quarterly_status = {}
            for module_id in quarterly_module_ids:
                status = tracker_status.get((station_uuid, module_id, filters["year"], quarter), 0)
                quarterly_status[f"module{module_id}_priority"] = module_status_priority[status]
            quarterly_status["hover_status"] = get_hover_status(
                module_status=quarterly_status,
                operational_date=operational_date,
                period="quarterly",
                year=filters["year"],
                quarter=quarter,
            )
            station_status.update({f"quarter{quarter}": quarterly_status})

        station_status.update({"annual": annual_status, "one_time": one_time_status})
        response_payload.append(station_status)

    return response_payload


@SessionManager.check_session()
@feature_enablement_check(Feature.DR_ST_DASHBOARD)
def handler(event, _context):
    connection = aurora.get_connection()
    try:
        log_event = LogEvent(
            event=event, api="APIGetDashboardSubmissionTracker", action_type="READ"
        )
        logger.info(event)
        if not log_event.is_auth_token_valid():
            raise EvChartAuthorizationTokenInvalidError()

        features = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

        token = log_event.get_auth_token()
        org_id = token.get("org_id")
        recipient_type = token.get("recipient_type")

        if recipient_type != "direct-recipient":
            raise EvChartUserNotAuthorizedError(
                message=("Only direct recipients are auhthorized to " "view submission tracker.")
            )

        path_parameters = event.get("queryStringParameters")
        filters = {
            "dr_id": org_id,
            "sr_id": path_parameters.get("sr_id", "All"),
            "year": path_parameters.get("year", str(datetime.date.today().year)),
            "station": path_parameters.get("station", "All"),
        }

        with connection.cursor() as cursor:
            filters = validate_filters(cursor, filters, features)
            tracker_status = get_tracker_status(cursor, filters)
            station_registrations = get_station_registrations(cursor, filters)

        response_payload = get_response_payload(filters, tracker_status, station_registrations)
    except EvChartMissingOrMalformedHeadersError:
        log_event.log_successful_request(message="Invalid or empty data.", status_code=204)
        return_obj = {
            "statusCode": 204,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps([], default=str),
        }
    except (
        EvChartAuthorizationTokenInvalidError,
        EvChartUserNotAuthorizedError,
        EvChartDatabaseAuroraQueryError,
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
            "body": json.dumps(response_payload, default=str),
        }

    finally:
        connection.commit()
        aurora.close_connection()

    return return_obj


def get_table_names(is_one_time):
    """
    Returning the sql statement that returns the station_uuid, upload_id, and module_id from either
    one-time module data tables or annual and quarterly module data tables
    """
    module_union = ""
    if is_one_time:
        # setting module_tables to the module tables holding one time data
        module_tables = {
            6: ModuleDataTables.Module6,
            8: ModuleDataTables.Module8,
            9: ModuleDataTables.Module9,
        }
    else:
        module_tables = {
            2: ModuleDataTables.Module2,
            3: ModuleDataTables.Module3,
            4: ModuleDataTables.Module4,
            5: ModuleDataTables.Module5,
            7: ModuleDataTables.Module7,
        }

    module_union = " UNION ".join(
        [
            (
                f"SELECT station_uuid, upload_id, '{module_id}' AS module "
                f"FROM {module_table.value}"
            )
            for module_id, module_table in module_tables.items()
        ]
    )
    return module_union


def validate_filters(cursor, filters, features):
    try:
        if filters["station"] == "":
            filters["station"] = "All"
        elif filters["station"] != "All":
            is_valid_station(filters["station"], cursor)

        if filters["sr_id"] == "None":
            filters["sr_id"] = filters["dr_id"]
        elif filters["sr_id"] != "All":
            uuid.UUID(str(filters["sr_id"]))
        datetime.datetime.strptime(filters["year"], "%Y")

        if not get_authorized_stations(cursor, filters, features):
            raise EvChartMissingOrMalformedHeadersError()
        logger.debug("Filters: %s", filters)
        return filters
    except Exception as e:
        raise EvChartMissingOrMalformedHeadersError(f"Unable to validate filters: {repr(e)}") from e


def get_authorized_stations(cursor, filters, features):
    authorizer_column = "dr_id"
    authorizee_column = "sr_id"

    if Feature.N_TIER_ORGANIZATIONS in features:
        authorizer_column = "authorizer"
        authorizee_column = "authorizee"

    if filters["station"] == "All":
        return True
    authorized_sr_query = f"""
        SELECT * FROM {station_registrations_data} r
        LEFT JOIN {authorized_station_data} using (station_uuid)
        WHERE r.dr_id=%(dr_id)s AND station_uuid=%(station)s
    """
    if filters["sr_id"] == filters["dr_id"]:
        authorized_sr_query += (
            " AND r.station_uuid NOT IN ( "
            f"   SELECT station_uuid from {authorized_station_data} "
            f"    WHERE {authorizer_column} = %(dr_id)s"
            " ) "
        )
    elif filters["sr_id"] != "All":
        authorized_sr_query += f""" AND {authorizee_column}=%(sr_id)s"""
    result_arr = execute_query(
        query=authorized_sr_query,
        data=filters,
        cursor=cursor,
        message=(
            "Error thrown in authorization_registration helper file: " "check_authorized_sr()"
        ),
    )
    if result_arr is None or len(result_arr) == 0:
        return False
    return True
