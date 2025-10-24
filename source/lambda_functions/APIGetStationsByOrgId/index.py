"""
APIGetStationsByOrgId

This api returns the active and pending station information from a given organization id. It takes in an optional query string parameter
where if the 'status' is 'active' then only the active stations are returned. If no 'status' parameter is given, then all pending
and active stations are returned. Another optional query string parameter is 'federal_funding_status'
with options:'fed_funded', 'non_fed_funded', or 'all'. This will return the stations that are federally funded, non federally funded, or both.
If a call is made by a subrecipient, the api returns the stations that the subrecipient organization is authorized to submit for.
"""
import json
from evchart_helper import aurora
from evchart_helper.api_helper import (
    get_org_info_dynamo,
    execute_query,
    execute_query_df
)
from evchart_helper.station_helper import (
    get_fed_funded_filter,
    get_non_fed_funded_filter,
    get_removable_stations_by_dr_id,
    get_all_federally_funded_stations
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseDynamoQueryError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedPathParameterError
)
from evchart_helper.session import SessionManager
from evchart_helper.database_tables import ModuleDataTables
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

station_registrations_table = ModuleDataTables["RegisteredStations"].value
station_authorizations_table = ModuleDataTables["StationAuthorizations"].value
station_ports_table = ModuleDataTables["StationPorts"].value

@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()

    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(event, api="APIGetStationsByOrgId", action_type="READ")
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            features = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

            token = log_event.get_auth_token()
            org_id = token.get("org_id")
            output = []

            recipient_type = token.get("recipient_type").lower()

            # getting status if present in querystring parameters
            path_parameters = event.get("queryStringParameters")
            station_filters = {
                "station_status": "",
                "federal_funding_status": "",
            }


            if path_parameters:
                validate_path_parameters(path_parameters)
                station_filters["station_status"] = path_parameters.get("status", "")
                station_filters["federal_funding_status"] = path_parameters.get("federal_funding_status", "")

            output = get_stations(recipient_type, org_id, station_filters, features, cursor)

        except (
            EvChartDatabaseAuroraQueryError,
            EvChartAuthorizationTokenInvalidError,
            EvChartDatabaseDynamoQueryError,
            EvChartJsonOutputError,
            EvChartMissingOrMalformedPathParameterError
        ) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="APIGetStationsByOrgId successfully invoked", status_code=200
            )
            return_obj = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(output),
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


def validate_path_parameters(path_parameters):
    valid_station_status = ["active"]
    valid_funding_status = ["fed_funded", "non_fed_funded", "all", ""]
    if path_parameters.get("station_status"):
        status = path_parameters.get("station_status")
        if status.lower() not in valid_station_status:
            raise EvChartMissingOrMalformedPathParameterError(
                message="Invalid station_status given. Station must be 'active', but received {status}"
            )

    if path_parameters.get("federal_funding_status"):
        funding_status = path_parameters.get("federal_funding_status")
        if funding_status.lower() not in valid_funding_status:
            raise EvChartMissingOrMalformedPathParameterError(
                message="Invalid federal_funding_status given. Status must be 'fed_funded', 'non_fed_funded', or 'all', but received {funding_status}"
            )
    return True


def get_sr_names_by_station_id(sr_ids_list):
    sr_names = {}
    for sr_id in sr_ids_list:
        if sr_id.get("sr_id") != "":
            sr_names.setdefault(sr_id["station_uuid"], []).append(
                get_org_info_dynamo(sr_id["sr_id"])["name"]
            )
        else:
            station_uuid = sr_id.get("station_uuid")
            raise EvChartJsonOutputError(message=
                f"Error thrown in get_sr_names_by_station_id(). "
                f"sr_id expected for station {station_uuid} but received an empty string"
            )

    return sr_names


def get_stations(recipient_type, org_id, station_filters, features, cursor):
    # updated query for dr and sr to prevent 413 error on stations summary page
    station_status = station_filters["station_status"]
    station_federal_funding_status = station_filters["federal_funding_status"]
    query, output = "", {}

    if recipient_type.lower() == "direct-recipient":
        query = query_builder(recipient_type, station_status, station_federal_funding_status, features)

        output_df = execute_query_df(
            query, (org_id,), cursor, message=f"get_stations for DR: {org_id}"
        )
        # adding 2 more fields to output: authorized srs, station removal status
        if not output_df.empty:
            add_authorized_srs_to_dataframe(org_id, cursor, output_df)
            add_removable_status_to_dataframe(cursor, org_id, output_df)

    elif recipient_type.lower() == "sub-recipient":
        query = query_builder(recipient_type, station_status, station_federal_funding_status, features)
        output_df = execute_query_df(
            query, (org_id,), cursor, message=f"get_stations for SR: {org_id}"
        )
        if not output_df.empty:
            output_df["dr_name"] = output_df["dr_id"].apply(lambda dr_id: get_org_info_dynamo(dr_id)["name"])

    # updating query to only select variables needed for jo query and download
    # necessary for avoiding 413 error from jo download form
    elif recipient_type.lower() == "joet":
        query = query_builder(recipient_type, station_status, station_federal_funding_status, features)
        output_df = execute_query_df(
            query, None, cursor, message=f"get_stations for JO: {org_id}"
        )
        if not output_df.empty:
            output_df["dr_name"] = output_df["dr_id"].apply(lambda dr_id: get_org_info_dynamo(dr_id)["name"])

    # adding federally funded status for the station table in stations tab, which is needed for JO, SRs, and DRs
    if not output_df.empty and Feature.REGISTER_NON_FED_FUNDED_STATION in features:
        output_df = add_federally_funded_status_to_dataframe(cursor, output_df)

    output = output_df.to_dict(orient="records")
    return output

# helper function that returns the sql query depending on recipient-type and station status
def query_builder(recipient_type, station_status, federal_funding_status, features):
    authorizee_column = "sr_id"

    if Feature.N_TIER_ORGANIZATIONS in features:
        authorizee_column = "authorizee"

    # filter on federally funded stations
    join_ports_string = ""
    fed_funded_status_filter = ""
    if federal_funding_status.lower() == "fed_funded":
        join_ports_string = f"LEFT JOIN {station_ports_table} AS sp ON sp.station_uuid = s.station_uuid"
        fed_funded_status_filter = get_fed_funded_filter("s", "sp")


    # filter on non federally funded stations
    if federal_funding_status.lower() == "non_fed_funded":
        join_ports_string = f"LEFT JOIN {station_ports_table} AS sp ON sp.station_uuid = s.station_uuid"
        fed_funded_status_filter = get_non_fed_funded_filter("s", "sp")


    # filter on active stations if needed
    station_active_filter = ""
    if station_status.lower() == "active":
        station_active_filter = ' AND s.status="Active"'

    query = ""
    if recipient_type.lower() == "direct-recipient":
        query = f"""
            SELECT DISTINCT s.station_uuid, s.nickname, s.station_id, s.status
            FROM {station_registrations_table} AS s
            {join_ports_string}
            WHERE dr_id=%s
            {fed_funded_status_filter}
            {station_active_filter}
        """

    elif recipient_type.lower() == "sub-recipient":
        query = f"""
            SELECT DISTINCT s.station_uuid, s.nickname, s.station_id, s.status, s.dr_id
            FROM {station_registrations_table} s
            INNER JOIN {station_authorizations_table} rs ON s.station_uuid = rs.station_uuid
            {join_ports_string}
            WHERE rs.{authorizee_column} = %s
            {fed_funded_status_filter}
            {station_active_filter}
        """

    elif recipient_type.lower() == "joet":
        query = f"""
            SELECT DISTINCT s.dr_id, s.station_uuid, s.station_id, s.nickname
            FROM {station_registrations_table} AS s
            {join_ports_string}
            WHERE status="Active"
            {fed_funded_status_filter}
        """

    return query


# sets the authorized_srs field in the dataframe
def add_authorized_srs_to_dataframe(org_id, cursor, output_df):
    sr_ids_query = f"""
                SELECT station_uuid, sr_id
                FROM {station_registrations_table}
                  JOIN {station_authorizations_table}
                    USING (station_uuid)
                WHERE station_registrations.dr_id=%s
            """
    sr_ids_list = execute_query(
        query=sr_ids_query,
        data=(org_id,),
        cursor=cursor,
        message=f"get_stations for DR: {org_id}",
    )
    sr_names = get_sr_names_by_station_id(sr_ids_list)
    output_df["authorized_subrecipients"] = output_df["station_uuid"].apply(
        lambda station_uuid: ", ".join(sr_names.get(station_uuid, []))
    )
    return output_df


# sets the removable field in the dataframe to true or false
def add_removable_status_to_dataframe(cursor, dr_id, output_df):
    output_df["removable"] = False
    removable_stations = get_removable_stations_by_dr_id(cursor, dr_id)
    if removable_stations:
        output_df.loc[output_df["station_uuid"].isin(removable_stations), "removable"] = True
    return output_df


# sets the federally_funded field in the dataframe to true or false
def add_federally_funded_status_to_dataframe(cursor, output_df):
    output_df["federally_funded"] = False
    federally_funded_stations = get_all_federally_funded_stations(cursor)
    if federally_funded_stations:
        output_df.loc[output_df["station_uuid"].isin(set(federally_funded_stations)), "federally_funded"] = True
    return output_df