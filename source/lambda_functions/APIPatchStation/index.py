"""
APIPatchStation

This Lambda function simply updates the station data in the database with what has just come from
the frontend.  Additionally, depending on features, this Lambda will send emails appropriate to the
context of the call to it.
"""
import datetime
import json
from dateutil import tz
from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from evchart_helper import aurora
from evchart_helper.api_helper import (
    format_users,
    get_org_info_dynamo,
    get_org_users,
)
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseDynamoQueryError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedBodyError,
    EvChartUnableToDeleteItemError,
    EvChartUserNotAuthorizedError,
    EvChartUnknownException,
    EvChartEmailError,
    EvChartFeatureStoreConnectionError
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from evchart_helper.station_helper import (
    insert_authorized_subrecipients,
    get_authorized_subrecipients,
    check_for_existing_srs,
    get_network_provider_uuid_by_network_provider_value,
    is_valid_station,
    format_operational_date,
    module_data_exists_for_ports,
    trigger_station_authorizes_subrecipient_email,
    handle_port_data,
)
from feature_toggle import (
    FeatureToggleService,
    Feature
)
from pymysql.err import IntegrityError
from station_validation import common_station_validations

station_registrations = ModuleDataTables["RegisteredStations"].value
station_authorizations = ModuleDataTables["StationAuthorizations"].value

DUPLICATE_ENTRY_ERROR_CODE = 1062

@SessionManager.check_session()
def handler(event, _context):
    log_event = LogEvent(event=event, api="APIPatchStation", action_type="modify")
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()
            auth_values = log_event.get_auth_token()
            station = json.loads(event.get("body"))

            # any data that a validation function will requrie should be configured here.
            # individual validation functions may use or disregard these options
            validation_options = {
                "api": "patch",
                "station": station,
                "auth_values": auth_values,
                "feature_toggle_set": feature_toggle_set,
                "cursor": cursor
            }

            # STATION VALIDATION: get the list of errors found from  iterating through station validation functions
            invalid_station_data = []
            for station_validation_function in common_station_validations:
                result = station_validation_function(validation_options)
                if isinstance(result, dict):
                    invalid_station_data.append(result)

            if invalid_station_data:
                raise EvChartMissingOrMalformedBodyError(
                    message= f"Invalid station data provided: {invalid_station_data}"
                )

            updated_on = str(datetime.datetime.now(tz.gettz("UTC")))
            updated_by = auth_values.get("email")
            dr_id = auth_values["org_id"]
            dr_org_name = auth_values["org_name"]
            station["dr_id"] = dr_id

            # throw error if data exists against ports trying to be removed
            if station.get("ports_removed"):
                module_data_exists_for_ports(station.get("ports_removed"), cursor)

            station_details = is_valid_station(station.get("station_uuid"), cursor)[0]
            if station.get("srs_added"):
                check_for_existing_srs(
                    station.get("srs_added"), station.get("station_uuid"), dr_id, feature_toggle_set, cursor
                )
                insert_authorized_subrecipients(
                    station.get("srs_added"),
                    station.get("station_uuid"),
                    updated_on,
                    updated_by,
                    dr_id,
                    cursor,
                    n_tier_enabled=Feature.N_TIER_ORGANIZATIONS in feature_toggle_set
                )
                if (
                    Feature.STATION_AUTHORIZES_SR_EMAIL in feature_toggle_set
                    and station_details.get("status") == "Active"
                ):
                    trigger_station_authorizes_subrecipient_email(
                        station["srs_added"],
                        station_details.get("station_id"),
                        station_details.get("nickname"),
                        dr_org_name,
                    )

                del station["srs_added"]

            if station.get("srs_removed"):
                remove_authorized_subrecipients(station, dr_id, feature_toggle_set, cursor)
                del station["srs_removed"]

            if "operational_date" in station:
                station["operational_date"] = format_operational_date(
                    station["operational_date"]
                )

            # takng out the fields that were already inserted into db,
            # save orginal data, clean for station update
            edited_station = station.copy()
            if "fed_funded_ports" in station:
                del edited_station["fed_funded_ports"]
            if "non_fed_funded_ports" in station:
                del edited_station["non_fed_funded_ports"]
            if "ports_removed" in station:
                del edited_station["ports_removed"]

            if Feature.NETWORK_PROVIDER_TABLE in feature_toggle_set:
                if "network_provider" in station:
                    np_uuid = get_network_provider_uuid_by_network_provider_value(station["network_provider"], cursor)
                    edited_station["network_provider_uuid"] = np_uuid

            # updating the fields in the station registration table
            update_station(edited_station, updated_on, updated_by, cursor)
            connection.commit()

            # adding/updating/deleting ports
            handle_port_data(station, cursor, updated_on, updated_by)

            if (
                Feature.SR_ADDS_STATION in feature_toggle_set
                and station_details.get("status") == "Pending Approval"
                and station.get("status") == "Active"
            ):
                sr_ids = get_authorized_subrecipients(station["station_uuid"], feature_toggle_set, cursor)
                send_station_approval_email(station_details, station, dr_org_name, sr_ids)

        except (
            EvChartFeatureStoreConnectionError,
            EvChartMissingOrMalformedBodyError,
            EvChartUserNotAuthorizedError,
            EvChartAuthorizationTokenInvalidError,
            EvChartDatabaseAuroraQueryError,
            EvChartDatabaseAuroraDuplicateItemError,
            EvChartDatabaseDynamoQueryError,
            EvChartJsonOutputError,
            EvChartUnknownException,
            EvChartEmailError,
            EvChartUnableToDeleteItemError,
        ) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()
        else:
            log_event.log_successful_request(
                message="Station successfully updated.", status_code=201
            )
            return_obj = {
                "statusCode": 201,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps("Station successfully updated."),
            }
        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


def send_station_approval_email(station_details, new_details, dr_org_name, sr_ids):
    station_nickname = station_details["nickname"]
    station_id = station_details["station_id"]

    if new_details.get("nickname"):
        station_nickname = f"{new_details['nickname']}</strong> (Previous Nickname: {station_nickname})<strong>"
    if new_details.get("station_id"):
        station_id = f"{new_details['station_id']}</strong> (Previous Station ID: {station_id})<strong>"

    try:
        for sr_org_id in sr_ids:
            sr_org_name = get_org_info_dynamo(sr_org_id)["name"]
            associated_srs = get_org_users(sr_org_id)
            formatted_srs = format_users(associated_srs)
            for user in formatted_srs:
                if user.get("status") == "Active" and user.get("role") == "Administrator":
                    trigger_email({
                        "email": user.get("email").strip(),
                        "email_type": Email_Template.DR_APPROVE_SR_STATION,
                        "sr_org_name": sr_org_name,
                        "dr_org_name": dr_org_name,
                        "first_name": user.get("first_name").strip(),
                        "station_nickname": station_nickname,
                        "subject_station_nickname":
                            new_details.get("nickname") or station_details["nickname"],
                        "station_id": station_id,
                    })
    except (
        EvChartDatabaseDynamoQueryError,
        EvChartJsonOutputError,
        EvChartMissingOrMalformedBodyError,
        EvChartEmailError
    )as e:
        e.message += "Error thrown in send_station_approval_email()."
        raise e
    except Exception as e:
        raise EvChartUnknownException(
            message=f"Error thrown in send_station_approval_email(). Error formatting fields for email handler: {e}"
        ) from e


# builds sql call and updates table, throws a duplicate item error or aurora db error
def update_station(station, updated_on, updated_by, cursor):
    query = update_station_sql_builder(station, updated_on, updated_by)
    try:
        # executing sql call
        cursor.execute(query, station)
        insert_succeeded = True

    except IntegrityError as e:
        code, message = e.args
        if (
            code == DUPLICATE_ENTRY_ERROR_CODE
            and "station_registrations.NP_Station_ID" in message
        ):
            raise EvChartDatabaseAuroraDuplicateItemError(
                message=(
                    f"Duplicate key {station.get('station_id')=}, "
                    f"{station.get('network_provider')=}"
                )
            ) from e
    if insert_succeeded is False:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Error updating Aurora for Station {station.get('station_id')}"
        )


# removing srs from station_authorizations table
def remove_authorized_subrecipients(station, dr_id, features, cursor):
    authorizer_column = "dr_id"
    authorizee_column = "sr_id"

    if Feature.N_TIER_ORGANIZATIONS in features:
        authorizer_column = "authorizer"
        authorizee_column = "authorizee"

    query = (
        f"DELETE FROM {station_authorizations} WHERE " # nosec - no SQL injection possible
        f"{authorizee_column}=%s AND {authorizer_column}=%s " # nosec - no SQL injection possible
        "AND station_uuid=%s"
    )
    for sr in station["srs_removed"]:
        try:
            cursor.execute(query, (sr, dr_id, station["station_uuid"]))

        except Exception as e:
            raise EvChartDatabaseAuroraQueryError(
                message=(
                    f"Error removing from {station_authorizations}: "
                    f"{repr(e)}"
                )
            ) from e


def update_station_sql_builder(station, updated_on, updated_by):
    try:
        # building sql call
        # station_col lists the names of the columns in the station_registration table
        # ensures that only fields in station table are being updated
        station_col = {
            "nickname",
            "station_id",
            "address",
            "city",
            "state",
            "zip",
            "zip_extended",
            "latitude",
            "longitude",
            "project_type",
            "network_provider",
            "network_provider_uuid",
            "status",
            "operational_date",
            "num_fed_funded_ports",
            "num_non_fed_funded_ports",
            "updated_on",
            "updated_by",
            "AFC",
            "NEVI",
            "CFI",
            "EVC_RAA",
            "CMAQ",
            "CRP",
            "OTHER",
        }
        station["updated_on"] = updated_on
        station["updated_by"] = updated_by
        if station.get("nickname"):
            station["nickname"] = station["nickname"].replace("'", "")

        # creating the set part of sql with %s as placeholders on the fields that are passed in
        updated_fields = station_col & station.keys()
        set_clause = ", ".join([f"{key} = %({key})s" for key in updated_fields])

        # creating condition by updating on station_uuid
        condition = "station_uuid = %(station_uuid)s"

        # constructing entire query
        query = f"UPDATE {station_registrations} SET {set_clause} WHERE {condition}" # nosec - SQL injection not possible
        return query
    except Exception as e:
        raise EvChartJsonOutputError(
            message=f"Error bulding sql call to update station information: {e}"
        ) from e