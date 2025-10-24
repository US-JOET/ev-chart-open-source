"""
Scheduled lambda to send emails for past due submissions

How to trigger ScheduledSubmissionDeadlineEmail in lambda:
    Hard code the functions that get the current date, and set it to the desired date (due date for when annual/onetime modules are due)
    functions that need to be updated: get_day_of_week(), get_current_month(), get_current_day(), get_current_year()
    create a temp unit test in the lambda console trigger the lambda by running the test you just made

Hard coded values for triggering quarterly emails:
    Make sure the operational date for the station has been operational for over a year
    get_day_of_week(): return 0
    get_current_month(): return 2
    get_current_day(): return 3
    get_current_year(): return 2025 (or return the current year)

Values for triggering one time/annual emails:
    Make sure the operational date for the station has been operational for over a year
    get_day_of_week(): return 3
    get_current_month(): return 3
    get_current_day(): return 4
    get_current_year(): return 2025 (or return the current year)

Raises:
    EvChartDatabaseAuroraQueryError: _description_
    EvChartJsonOutputError: _description_

"""
from datetime import datetime
from dateutil.relativedelta import relativedelta

from database_central_config import DatabaseCentralConfig

from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from email_handler.html_templates import dr_past_due_submission

from evchart_helper import aurora
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.module_enums import ModuleNames
from evchart_helper.custom_logging import LogEvent
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartJsonOutputError,
    EvChartDatabaseDynamoQueryError,
    EvChartUnknownException,
    EvChartDatabaseHandlerConnectionError,
)
from evchart_helper.api_helper import (
    get_org_info_dynamo,
    get_org_users,
    format_users,
    execute_query_df
)
from evchart_helper.station_helper import get_fed_funded_filter
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

station_ports = ModuleDataTables["StationPorts"].value
station_registrations = ModuleDataTables['RegisteredStations'].value
import_metadata = ModuleDataTables['Metadata'].value
station_authorizations = ModuleDataTables['StationAuthorizations'].value

def handler(event, _context):
    log = LogEvent(
        event, api="ScheduledSubmissionDeadlineEmail", action_type="Read"
    )
    # If it's not a valid day, stop execution
    if not should_send_email():
        print("email not sent")
        return None
    try:
        connection = aurora.get_connection()
    except Exception:  # pylint: disable=broad-exception-caught
        return EvChartDatabaseHandlerConnectionError().get_error_obj()

    try:
        print("email sending")
        # setup
        cursor = connection.cursor()
        features = FeatureToggleService().get_active_feature_toggles(
            log_event=log
        )

        # get stations and uploads
        if Feature.REGISTER_NON_FED_FUNDED_STATION in features:
            stations_df = get_active_fed_funded_stations(cursor)
        else:
            stations_df = get_active_stations(cursor)
        uploads_df = get_submitted_uploads(cursor)

        # for each dr, collect all stations that are past due
        for dr_id in stations_df['dr_id'].unique():
            past_due_stations_dict = {}
            filtered_stations_df = stations_df[stations_df['dr_id'] == dr_id]
            filtered_uploads_df = uploads_df[uploads_df['parent_org'] == dr_id]
            for _, row in filtered_stations_df.iterrows():
                past_due_modules = []
                past_due_modules = get_past_due_modules_by_station(
                    row, filtered_uploads_df, cursor
                )
                if past_due_modules:
                    past_due_stations_dict[row.station_uuid] = past_due_modules

            if past_due_stations_dict:
                formatted_email_table = format_email_template(
                    stations_df=filtered_stations_df,
                    past_due_stations_dict=past_due_stations_dict,
                    cursor=cursor,
                    features=features
                )
                send_org_emails(dr_id, formatted_email_table)

    except (
        EvChartDatabaseAuroraQueryError,
        EvChartDatabaseDynamoQueryError,
    ) as e:
        log.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
            )
    except Exception as e:
        raise EvChartUnknownException(
            message=(
                "Unknown Exception in ScheduleSubmissionDeadlineEmail: "
                f"{repr(e)}"
            )
        ) from e
    finally:
        aurora.close_connection()

    return None


# given filtered dataframe of uploads and a station row
# return list of modules that are past due or None
def get_past_due_modules_by_station(station, uploads_df, cursor):
    operational_year = station.operational_date.year
    is_one_time = (operational_year == get_current_year() - 1)
    search_modules = get_search_modules(is_one_time)
    past_due_modules = []
    if is_station_due(station.operational_date):
        for module_id in search_modules:
            # filter dataframe for module only
            if is_one_time and module_id in get_one_time_modules():
                years = [operational_year, operational_year + 1]
            else:
                if is_yearly_or_onetime_submission() or get_quarter() == 4:
                    years = [get_current_year() - 1]
                else:
                    years = [get_current_year()]
            uploads_df['year'] = uploads_df['year'].astype(int)
            filter_df = uploads_df[uploads_df['year'].isin(years)]
            filtered_df = filter_df[filter_df['module_id'] == str(module_id)]
            upload_id_list = filtered_df['upload_id'].tolist()
            if upload_id_list:
                upload_ids = (
                    tuple(upload_id_list)
                    if (len(upload_id_list) > 1)
                    else f'("{upload_id_list[0]}")'
                )
                module_results = get_module_data(
                    module_id, station.station_uuid, upload_ids, cursor
                )
                if module_results is None:
                    past_due_modules.append(module_id)
            else:
                past_due_modules.append(module_id)

    return past_due_modules


def get_module_data(module_id, station_uuid, upload_ids, cursor):
    full_mod_id = f"Module{module_id}"
    mod_table_query = (
        f"SELECT 1 FROM {ModuleDataTables[full_mod_id].value} md "
        f"WHERE md.station_uuid = '{station_uuid}' "
        f"AND md.upload_id IN {upload_ids} "
    )
    try:
        cursor.execute(mod_table_query)
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Error in get_past_due_modules_by_station(): {repr(e)}"
        ) from e
    return cursor.fetchone()


# returns dataframe of all (valid) active stations
def get_active_stations(cursor):
    get_stations_query = (
        "SELECT rs.dr_id, rs.station_uuid, rs.nickname, "
        "  rs.station_id, rs.operational_date "
        f"FROM {station_registrations} rs "
        "WHERE rs.status='Active' "
        "AND rs.dr_id != '154ecdd3-d864-4110-916b-9c1287bb31e8'"
    )

    df = execute_query_df(
        query=get_stations_query,
        data=None,
        cursor=cursor,
        message="Error thrown in get_active_stations()"
    )
    return df

# returns dataframe of all (valid) active and federally funded stations
def get_active_fed_funded_stations(cursor):
    get_stations_query = (
        "SELECT DISTINCT rs.dr_id, rs.station_uuid, rs.nickname, "
        "  rs.station_id, rs.operational_date "
        f" FROM {station_registrations} AS rs "
        f" LEFT JOIN {station_ports} AS sp"
        " ON sp.station_uuid = rs.station_uuid"
        " WHERE rs.status='Active' "
        " AND rs.dr_id != '154ecdd3-d864-4110-916b-9c1287bb31e8' "
    ) + get_fed_funded_filter("rs", "sp")

    df = execute_query_df(
        query= get_stations_query,
        data=None,
        cursor=cursor,
        message="Error thrown in get_active_fed_funded_stations(). "
    )
    return df

def get_station_authorized(station_uuid, cursor, features):
    column_name = "sr_id"

    if Feature.N_TIER_ORGANIZATIONS in features:
        column_name = "authorizee"

    get_authorized_query = (
        f"SELECT {column_name} AS sr_id "
        f"FROM {station_authorizations} sa "
        f"WHERE sa.station_uuid = '{station_uuid}'"
    )

    df = execute_query_df(
        query=get_authorized_query,
        data=None,
        cursor=cursor,
        message="Error thrown in get_station_authorized(). "
    )
    return df


# returns dataframe of all uploads for reporting period
# that are approved/submitted
def get_submitted_uploads(cursor):
    module_ids = get_search_modules()
    filter_year = get_current_year()
    filter_years = (filter_year, filter_year - 1)
    quarter = get_quarter()

    if not quarter:
        quarter_query = "''"
    else:
        quarter_query = f"'{quarter}'"

    get_uploads_query = (
        "SELECT "
        "  im.parent_org, im.upload_id, im.module_id, im.year, im.quarter "
        f"FROM  {import_metadata} im "
        f"WHERE im.year IN {filter_years} "
        f"AND im.module_id IN {module_ids} AND im.quarter = {quarter_query} "
        "AND (im.submission_status = 'Approved' OR "
        "     im.submission_status = 'Submitted')"
    )

    df = execute_query_df(
        query=get_uploads_query,
        data=None,
        cursor=cursor,
        message="Error thrown in get_submitted_uploads(). "
    )
    return df


# given station row
# return tuple of modules to search uploads
def get_search_modules(is_one_time=None):
    modules = []
    if is_yearly_or_onetime_submission():
        if is_one_time is None or is_one_time is True:
            modules += [6, 8, 9]
        modules += [5, 7]
    if is_quarterly_submission():
        modules += [2, 3, 4]

    return tuple(modules)


def get_one_time_modules():
    return (6, 8, 9)


def get_quarter():
    quarter = 0
    if is_yearly_or_onetime_submission():
        quarter = ''
    if is_quarterly_submission():
        match get_current_month():
            case 2:
                quarter = 4
            case 5:
                quarter = 1
            case 8:
                quarter = 2
            case 11:
                quarter = 3
    return quarter


def get_quarter_string():
    match get_quarter():
        case 1:
            return_string = "Quarter 1 (Jan-Mar)"
        case 2:
            return_string = "Quarter 2 (Apr-Jun)"
        case 3:
            return_string = "Quarter 3 (Jul-Sep)"
        case 4:
            return_string = "Quarter 4 (Oct-Dec)"
        case '':
            return_string = "One-Time/Annual"
        case _:
            return_string = "N/A"

    return return_string


# returns number between 0 (Monday) and 6 (Sunday)
def get_day_of_week():
    return datetime.today().weekday()


# returns current month (1 - 12)
def get_current_month():
    return datetime.now().date().month


def get_current_day():
    return datetime.now().date().day


def get_current_year():
    return datetime.now().date().year


# checks if is for quarterly submission
def is_quarterly_submission():
    return (get_current_month() in [2, 5, 8, 11])


# checks if is for yearly or one-time submission
def is_yearly_or_onetime_submission():
    return get_current_month() == 3


def is_weekday():
    return (get_day_of_week() in [0, 1, 2, 3, 4])


def is_station_due(operational_date):
    is_due = False
    # if quarterly submission and operational for over 1 month then station is due
    if is_quarterly_submission():
        today = datetime(get_current_year(), get_current_month(), 1)
        date_limit = today - relativedelta(months=1)
        is_due = operational_date < date_limit.date()
    if is_yearly_or_onetime_submission():
        is_due = operational_date.year < get_current_year()
    return is_due


def should_send_email():
    if is_weekday():
        if is_quarterly_submission():
            if (
                get_current_day() in range(3, 6) or
                get_current_day() in range(21, 24)
            ):
                return (get_day_of_week() == 0 or get_current_day() in [3, 21])
        if is_yearly_or_onetime_submission():
            if (
                get_current_day() in range(4, 7) or
                get_current_day() in range(22, 25)
            ):
                return (get_day_of_week() == 0 or get_current_day() in [4, 22])
    return False


# returns concatenated html table. Goes through all past due stations and formats the overdue email
# to have a list of stations along with their authorized srs and overdue modules
def format_email_template(
    stations_df, past_due_stations_dict, cursor, features
):
    stations_list_item = str(dr_past_due_submission.stations_list_item)
    authorized_sr_present = str(dr_past_due_submission.authorized_sr_present)
    sr_list_item = str(dr_past_due_submission.sr_list_item)
    overdue_module_item = str(dr_past_due_submission.overdue_module_item)
    full_station_table = ""

    for station_uuid in past_due_stations_dict:
        filtered_station_df = \
            stations_df[stations_df['station_uuid'] == station_uuid]

        authorized_srs = ""
        sr_list_table = ""
        overdue_module_table = ""

        sr_ids_df = get_station_authorized(station_uuid, cursor, features)

        # only create the authorized srs section in the email if curr station has authorized srs
        if not sr_ids_df.empty:
            # iterate through df and get the sr name and add it to the authorized srs section in email
            for _, sr_id in sr_ids_df.iterrows():
                new_table_row = sr_list_item
                sr_name = get_org_info_dynamo(sr_id.sr_id).get("name")
                # creating/formatting the bulleted list of srs
                sr_list_table += new_table_row.format(sr_name=sr_name)

            # creating/formatting the authorized subrecipients section given the formatted list of srs
            authorized_srs += authorized_sr_present.format(sr_list=sr_list_table)

        # creating the overdue modules list
        for module_id in past_due_stations_dict[station_uuid]:
            new_table_row = overdue_module_item
            if Feature.DATABASE_CENTRAL_CONFIG in features:
                module_name = DatabaseCentralConfig().module_display_name(module_id)
            else:
                full_mod_id = f"Module{module_id}"
                module_name = ModuleNames[full_mod_id].value

            overdue_module_table += new_table_row.format(
                mod_id=module_id,
                module_name=module_name
                )

        # creating the stations_list_item which holds the station's authorized srs and overdue modules
        for station in filtered_station_df.itertuples():
            new_table_row = stations_list_item
            full_station_table += new_table_row.format(
                station_name=station.nickname,
                station_id=station.station_id,
                authorized_sr_section=authorized_srs,
                overdue_module_list=overdue_module_table
            )

    return full_station_table


def send_org_emails(org_id, formatted_email_table):
    try:
        email_values = {}
        email_values["email_type"] = Email_Template.DR_PAST_DUE_SUBMISSION
        email_values["station_list"] = formatted_email_table
        dr_org_name = get_org_info_dynamo(org_id).get("name")
        email_values["dr_org_name"] = dr_org_name

        email_values["reporting_period"] = get_quarter_string()
        year = get_current_year()
        if get_quarter() == 4 or is_yearly_or_onetime_submission():
            year -= 1
        email_values["year"] = year

        org_users = get_org_users(org_id)
        formatted_users = format_users(org_users)
        for user in formatted_users:
            if (
                user.get("status") == "Active" and
                user.get("role") == "Administrator"
            ):
                email_values["first_name"] = user.get("first_name").strip()
                email_values["email"] = user.get("email").strip()
                trigger_email(email_values)
    except EvChartJsonOutputError as e:
        raise EvChartJsonOutputError(
            message=f"Error formatting fields for email handler: {repr(e)}"
        ) from e
    except EvChartDatabaseDynamoQueryError as e:
        raise EvChartJsonOutputError(
            message=f"Error with dynamo query in send_org_emails():  {e}"
        ) from e
