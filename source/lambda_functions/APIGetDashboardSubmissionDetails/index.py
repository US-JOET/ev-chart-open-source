"""
APIGetDashboardSubmissionDetails

Generate and execute all the relevant queries necessary and provide the resulting data to the
frontend for the submission details dashboard.
"""
import json
import logging
from datetime import date
from dateutil import tz

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
from evchart_helper.module_helper import format_sub_recipient, format_module_name
from feature_toggle import feature_enablement_check, FeatureToggleService
from feature_toggle.feature_enums import Feature
from database_central_config import DatabaseCentralConfig

logger = logging.getLogger("APIGetDashboardSubmissionDetails")
logger.setLevel(logging.INFO)

module2_data = ModuleDataTables["Module2"].value
module3_data = ModuleDataTables["Module3"].value
module4_data = ModuleDataTables["Module4"].value
module5_data = ModuleDataTables["Module5"].value
module6_data = ModuleDataTables["Module6"].value
module7_data = ModuleDataTables["Module7"].value
module8_data = ModuleDataTables["Module8"].value
module9_data = ModuleDataTables["Module9"].value

station_registrations_data = ModuleDataTables["RegisteredStations"].value
authorized_station_data = ModuleDataTables["StationAuthorizations"].value
import_metadata = ModuleDataTables["Metadata"].value


capital_cost_categories = [
    "equipment_cost",
    "equipment_install_cost",
    "service_cost",
    "system_cost",
]

module_tables = [
    module2_data,
    module3_data,
    module4_data,
    module5_data,
    module6_data,
    module7_data,
    module8_data,
    module9_data,
]

one_time_tables = [
    module6_data,
    module8_data,
    module9_data
]


def get_submission_details_by_station(cursor, filters, feature_toggle_set=frozenset()):
    data = []
    for table in module_tables:
        submission_details_sql = (
            f"SELECT DISTINCT submission_status, {import_metadata}.updated_on, upload_id, parent_org, org_id, module_id, quarter, year"
            f" FROM {import_metadata} "
            f" JOIN {table} using (upload_id) "
            " WHERE submission_status in ('Pending', 'Approved', 'Rejected', 'Submitted') "
        )
        if table in one_time_tables:
            data.append(execute_query_with_filters(True, cursor, submission_details_sql, filters))
        else:
            data.append(execute_query_with_filters(False, cursor, submission_details_sql, filters))
    logger.debug(f"data from db: {data}")
    return format_data(data, feature_toggle_set)


def format_data(data, feature_toggle_set=frozenset()):
    one_time = ["6", "8", "9"]
    annual = ["5", "7"]
    quarterly = ["2", "3", "4"]
    count = {
        "quarterly": {"1": [], "2": [], "3": [], "4": []},
        "annual": [],
        "one_time": [],
    }
    config = DatabaseCentralConfig()

    for module_set in data:
        for item in module_set:
            formatted_item = format_datetime(item)
            module_id = item["module_id"]

            # formatting sub_recipient
            format_sub_recipient(formatted_item)

            # formatting module_name
            if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
                formatted_item["module_name"] = config.module_display_name(module_id)
                module_frequency = config.module_frequency(module_id)
                if module_frequency == "quarterly":
                    count["quarterly"][formatted_item["quarter"]].append(formatted_item)
                else:
                    count[module_frequency].append(formatted_item)
            else:
                format_module_name(formatted_item)

                if module_id in one_time:
                    count["one_time"].append(formatted_item)
                if module_id in annual:
                    count["annual"].append(formatted_item)
                if module_id in quarterly:
                    count["quarterly"][formatted_item["quarter"]].append(formatted_item)
    return count


def format_datetime(data):
    date_obj = data["updated_on"].astimezone(tz.gettz("US/Eastern"))
    formatted_upload_timestamp = str(date_obj.strftime("%m/%d/%y"))
    data["updated_on"] = formatted_upload_timestamp
    return data


def execute_query_with_filters(is_one_time, cursor, query, filters, group_by=()):
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
    statement_values = ()
    if filters["dr_id"] != "All":
        query += f" AND {import_metadata}.parent_org = %s "
        statement_values += (filters["dr_id"],)
    if filters["sr_id"] != "All":
        query += f" AND {import_metadata}.org_id = %s "
        statement_values += (filters["sr_id"],)
    if filters["station"] != "All":
        query += (
            f" AND station_uuid = %s "
        )
        statement_values += (filters["station"],)
    if filters["year"] != "All" and not is_one_time:
        query += (
            f" AND {import_metadata}.year = %s "
        )
        statement_values += (filters["year"],)
    query += (
        f"{group_by_clause}"
    )
    logger.debug("EXECUTE_QUERY_WITH_FILTERS %s %s", query, statement_values)
    cursor.execute(query, statement_values)
    output = [
        dict((cursor.description[i][0], value) for i, value in enumerate(row))
        for row in cursor.fetchall()
    ]
    return output


@SessionManager.check_session()
@feature_enablement_check(Feature.DR_ST_DASHBOARD)
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(
                event=event, api="APIGetDashboardSubmissionDetails", action_type="READ"
            )
            logger.info(event)
            if not log_event.is_auth_token_valid():
                raise EvChartAuthorizationTokenInvalidError()

            feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

            # validates user
            token = log_event.get_auth_token()
            recipient_type = validate_org(token)

            # initializes data output
            json_output = {}
            filters = {
                "station": "All",
                "dr_id": "All",
                "sr_id": "All",
                "year": str(date.today().year),
            }
            path_parameters = event.get("queryStringParameters")

            filters["station"] = get_station(path_parameters, filters["station"])
            if recipient_type == "DR":
                filters["dr_id"] = token.get("org_id")
            else:
                filters["dr_id"] = get_dr_id(path_parameters, filters["dr_id"])
            filters["sr_id"] = get_sr_id(path_parameters, filters["sr_id"])
            filters["year"] = get_year(path_parameters, filters["year"])
            # handling network size
            json_output.update(
                get_submission_details_by_station(cursor=cursor, filters=filters, feature_toggle_set=feature_toggle_set)
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


# helper method to validate the current user's org
# raises auth error otherwise.
def validate_org(token):
    # getting recipient_type from the auth token
    recipient_type = token.get("recipient_type")
    if recipient_type.lower() == "joet":
        return "JO"
    if recipient_type.lower() == "direct-recipient":
        return "DR"
    raise EvChartUserNotAuthorizedError(
        message="User not authorized to view dashboard data."
    )


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
