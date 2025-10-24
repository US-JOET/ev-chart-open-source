"""
APIGetStationsById

Return a list of authorized stations given a station ID.  Authorized subrecipients for a station are
also returned for requests depending on organization type.
"""
import json
import logging
from zoneinfo import ZoneInfo

from evchart_helper import aurora
from evchart_helper.api_helper import (execute_query,
                                       get_org_info_dynamo)
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError, EvChartDatabaseAuroraQueryError,
    EvChartJsonOutputError, EvChartMissingOrMalformedBodyError,
    EvChartUserNotAuthorizedError, EvChartDatabaseDynamoQueryError,
    EvChartUnknownException)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from evchart_helper.station_helper import is_valid_org
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

station_registrations = ModuleDataTables["RegisteredStations"].value
station_authorizations = ModuleDataTables["StationAuthorizations"].value
station_ports = ModuleDataTables["StationPorts"].value
network_providers = ModuleDataTables["NetworkProviders"].value

logger = logging.getLogger("APIGetStationsById")
logger.setLevel(logging.INFO)

@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()

    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(event, api="APIGetStationsById", action_type="Read")
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            feature_toggle_service = FeatureToggleService()
            feature_toggle_set = feature_toggle_service.get_active_feature_toggles(log_event=log_event)

            output = []
            query_params = event.get("queryStringParameters")
            token = log_event.get_auth_token()
            org_id = token.get("org_id")
            recipient_type = token.get("recipient_type")
            if query_params:
                station_uuid = query_params.get("station_uuid", [])
                if len(station_uuid) == 0 or len(org_id) == 0:
                    raise EvChartMissingOrMalformedBodyError(
                        message="Missing station id from query string parameters"
                    )
            else:
                raise EvChartMissingOrMalformedBodyError(message="Missing query string parameters")

            #gets data related to specific station id if station_id is provided
            if is_valid_org(org_id, recipient_type, station_uuid, cursor, feature_toggle_set):
                output = get_station_details(station_uuid, org_id, recipient_type, cursor, feature_toggle_set)
                output = format_erroneous_fields(output)
                output = get_port_details(output, station_uuid, cursor)

        except (EvChartAuthorizationTokenInvalidError,
                EvChartMissingOrMalformedBodyError,
                EvChartUserNotAuthorizedError,
                EvChartDatabaseAuroraQueryError,
                EvChartJsonOutputError,
                EvChartDatabaseDynamoQueryError,
                EvChartUnknownException
        ) as e:
            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="APIGetStationsbyId successfully invoked",
                status_code=200
            )
            return_obj = {
                'statusCode' : 200,
                'headers': { "Access-Control-Allow-Origin": "*" },
                'body': json.dumps(output)
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


# helper function that returns the data from passed in station_id and adds authorized subrecipients
# to output if the user is a DR
def get_station_details(station_uuid, org_id, recipient_type, cursor, feature_toggle_set):
    if Feature.NETWORK_PROVIDER_TABLE in feature_toggle_set:
        query = f"""SELECT address, city, dr_id, station_uuid, latitude, longitude, nickname,
        project_type, station_id, state, status, sr.updated_by, sr.updated_on, zip, zip_extended,
        operational_date, NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER, AFC, num_fed_funded_ports,
        num_non_fed_funded_ports, np.network_provider_value AS network_provider
        FROM {station_registrations} sr
        INNER JOIN {network_providers} np on sr.network_provider_uuid = np.network_provider_uuid
        WHERE station_uuid=%s"""
    else:
        query = f"SELECT * FROM {station_registrations} WHERE station_uuid=%s"
    output = execute_query(
        query, (station_uuid,), cursor,
        message=f"get_station_details for station_uuid: {station_uuid}"
    )
    if not output:
        raise EvChartMissingOrMalformedBodyError(message=f"Station {station_uuid} does not exist")

    station = output[0]

    srs = get_authorized_subrecipients(station, org_id, recipient_type, feature_toggle_set, cursor)
    station["authorized_subrecipients"] = srs

    return station


def get_authorized_subrecipients(
    station, org_id, recipient_type, features, cursor
): # pylint: disable=R0914
    authorizer_column = "dr_id"
    authorizee_column = "sr_id"

    if Feature.N_TIER_ORGANIZATIONS in features:
        authorizer_column = "authorizer"
        authorizee_column = "authorizee"

    try:
        query = f"SELECT * FROM {station_authorizations} WHERE station_uuid = %s" # nosec - no SQL injection possible
        parameters = [station["station_uuid"]]

        if recipient_type != "joet":
            query += f" AND {authorizer_column} = %s" # nosec - no SQL injection possible
            parameters.append(org_id)

        sr_ids = execute_query(
            query, parameters, cursor,
            message=f"get_authorized_subrecipients for org {org_id}"
        )

        #format authorized sr names
        authorized_srs = {}
        if sr_ids:
            for auth in sr_ids:
                sr_id = auth[authorizee_column]
                sr_name = get_org_info_dynamo(sr_id)["name"]
                authorized_srs[sr_id] = sr_name
        return authorized_srs

    except EvChartDatabaseDynamoQueryError as e:
        e.message += "Error thrown in get_authorized_subrecipients()."
        raise e
    except EvChartDatabaseAuroraQueryError as e:
        e.message += "Error thrown in get_authorized_subrecipients()."
        raise e
    except Exception as e:
        raise EvChartUnknownException(
            message=(
                "Error thrown in get_authorized_subrecipients(). "
                f"Could not retrieve list of authorized recipients: {e}"
            )
        ) from e


def format_erroneous_fields(station):
    try:
        updated_on = station["updated_on"].astimezone(ZoneInfo("America/New_York"))
        formatted_upload_timestamp = str(updated_on.strftime("%m/%d/%y %-I:%M %p %Z"))
        station["updated_on"] = formatted_upload_timestamp
        station["latitude"] = str(station["latitude"])
        station["longitude"] = str(station["longitude"])
        if station["operational_date"] is not None:
            formatted_operational_date = str(station["operational_date"])
            station["operational_date"] = formatted_operational_date
        return station
    except Exception as e:
        raise EvChartJsonOutputError(message=f"Error processing the datetime object: {e}") from e

#helper function that returns a list of the non-fed-funded and fed-funded port obj
def get_port_details(output, station_uuid,cursor):
    query_fed_funded= (
        f"SELECT port_uuid, port_id, port_type FROM {station_ports} " # nosec - no SQL injection possible
        "WHERE station_uuid=%s AND federally_funded='1'"
    )
    output["fed_funded_ports"] = execute_query(query_fed_funded, data=station_uuid, cursor=cursor)

    query_non_fed_funded= (
        f"SELECT port_uuid, port_id, port_type FROM {station_ports} " # nosec - no SQL injection possible
        "WHERE station_uuid=%s AND federally_funded='0'"
    )
    output["non_fed_funded_ports"] = execute_query(
        query_non_fed_funded, data=station_uuid, cursor=cursor
    )

    return output
