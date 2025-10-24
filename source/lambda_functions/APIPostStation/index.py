"""
APIPostStation

This api will accept a body that will have the necessary Module 1: Station Location information.
Both direct recipients and sub-recipients are able to add a station which will add the station
information into the station_registration, station_authorization, and station_ports tables.
An email will also be sent to the subrecipients that the direct recipeient has authorized to
submit on their behalf.
"""

from datetime import datetime, UTC
import logging
import json
import re
import uuid

from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from evchart_helper import aurora
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseDynamoQueryError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedBodyError,
    EvChartUserNotAuthorizedError,
    EvChartEmailError,
    EvChartFeatureStoreConnectionError,
)
from evchart_helper.api_helper import (
    format_users,
    get_org_info_dynamo,
    get_org_users,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from evchart_helper.station_helper import (
    insert_authorized_subrecipients,
    format_operational_date,
    trigger_station_authorizes_subrecipient_email,
    handle_port_data,
)

from station_validation import common_station_validations
from pymysql.err import IntegrityError

from feature_toggle import (
    FeatureToggleService,
    Feature
)
station_registrations = ModuleDataTables["RegisteredStations"].value
network_providers = ModuleDataTables["NetworkProviders"].value

DUPLICATE_ENTRY_ERROR_CODE = 1062

logger = logging.getLogger("APIPostStation")
logger.setLevel(logging.DEBUG)


@SessionManager.check_session()
def handler(event, _context):  # pylint: disable=R0914,R0915
    log_event = LogEvent(event=event, api="APIPostStation", action_type="modify")
    connection = aurora.get_connection()

    with connection.cursor() as cursor:
        try:
            feature_toggle_set = FeatureToggleService().get_active_feature_toggles(
                log_event=log_event
            )

            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            auth_values = log_event.get_auth_token()
            recipient_type = auth_values.get("recipient_type")
            station = json.loads(event["body"])

            # any data that a validation function will requrie should be configured here.
            # individual validation functions may use or disregard these options
            validation_options = {
                "api": "post",
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

            edited_station = transform_station_data(auth_values, station)

            # adding station
            insert_station_registration(edited_station, cursor, feature_toggle_set)
            connection.commit()

            edited_station["station_uuid"] = station["station_uuid"]
            # adding ports (after station update, in case of RDS error)
            handle_port_data(station, cursor, station.get("updated_on"), station.get("updated_by"))

            save_station_authorizations(cursor, edited_station, station["authorized_subrecipients"], feature_toggle_set)

            if (
                Feature.SR_ADDS_STATION in feature_toggle_set
                and recipient_type.lower() == "sub-recipient"
            ):
                send_station_review_email(auth_values.get("org_name"), station)

        except (
            EvChartFeatureStoreConnectionError,
            EvChartDatabaseAuroraQueryError,
            EvChartUserNotAuthorizedError,
            EvChartDatabaseAuroraDuplicateItemError,
            EvChartDatabaseDynamoQueryError,
            EvChartAuthorizationTokenInvalidError,
            EvChartJsonOutputError,
            EvChartMissingOrMalformedBodyError,
            EvChartEmailError,
        ) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()
        else:
            log_event.log_successful_request(message="Success post station", status_code=201)
            return_obj = {
                "statusCode": 201,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps("Station successfully registered."),
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


def transform_station_data(auth_values, station):
    station["station_uuid"] = str(uuid.uuid4())
    station["updated_on"] = str(datetime.now(UTC))
    station["updated_by"] = auth_values.get("email")
    station["operational_date"] = format_operational_date(station["operational_date"])

    # save orginal data, clean for station update
    edited_station = station.copy()
    del edited_station["authorized_subrecipients"]

    if "fed_funded_ports" in station:
        del edited_station["fed_funded_ports"]
    if "non_fed_funded_ports" in station:
        del edited_station["non_fed_funded_ports"]
    return edited_station

def save_station_authorizations(cursor, edited_station, authorized_subrecipients, feature_toggle_set):
        # adding authorized subrecipients
    insert_authorized_subrecipients(
        authorized_subrecipients,
        edited_station.get("station_uuid"),
        edited_station.get("updated_on"),
        edited_station.get("updated_by"),
        edited_station.get("dr_id"),
        cursor,
        n_tier_enabled=Feature.N_TIER_ORGANIZATIONS in feature_toggle_set,
    )
    # triggering the email only when a DR registers a station, not when an SR does it
    if Feature.STATION_AUTHORIZES_SR_EMAIL in feature_toggle_set and edited_station["status"] == "Active":
        dr_org_name = get_org_info_dynamo(edited_station["dr_id"])["name"]
        trigger_station_authorizes_subrecipient_email(
            authorized_subrecipients,
            edited_station.get("station_id"),
            edited_station.get("nickname"),
            dr_org_name,
        )

def send_station_review_email(sr_org_name, station):
    dr_org_name = get_org_info_dynamo(station["dr_id"])["name"]
    associated_drs = get_org_users(station["dr_id"])
    formatted_drs = format_users(associated_drs)
    funding_types = []
    for funding_type in ["NEVI", "CFI", "EVC_RAA", "CMAQ", "CRP", "OTHER"]:
        if station[funding_type]:
            funding_types.append(
                funding_type.title() if funding_type == "OTHER" else re.sub("_", "-", funding_type)
            )

    for user in formatted_drs:
        if user.get("status") == "Active" and user.get("role") == "Administrator":
            trigger_email(
                {
                    "email": user.get("email").strip(),
                    "email_type": Email_Template.DR_REVIEW_SR_STATION,
                    "sr_org_name": sr_org_name,
                    "dr_org_name": dr_org_name,
                    "first_name": user.get("first_name").strip(),
                    "station_nickname": station["nickname"],
                    "station_id": station["station_id"],
                    "station_address": station["address"].title(),
                    "station_city": station["city"].title(),
                    "station_state": station["state"].upper(),
                    "station_zip": station["zip"],
                    "station_zip_extended": station["zip_extended"],
                    "station_np": station["network_provider"],
                    "station_funding_type": ", ".join(funding_types),
                    "station_afc": bool(station["AFC"]),
                    "ports_num_fed": station["num_fed_funded_ports"],
                }
            )


def insert_station_registration(station, cursor, feature_toggle_set):
    logger.info(f"station['network_provider']")
    if Feature.NETWORK_PROVIDER_TABLE in feature_toggle_set:
        cursor.execute(
            f"SELECT network_provider_uuid FROM {network_providers} " #nosec
            "WHERE network_provider_value = %s"
        , station["network_provider"])
        station["np_uuid"] = cursor.fetchone()[0]

    sql = f"""INSERT INTO {station_registrations} (
        nickname,
        station_id,
        dr_id,
        station_uuid,
        address,
        city,
        state,
        zip,
        zip_extended,
        latitude,
        longitude,
        project_type,
        network_provider,
        status,
        updated_on,
        updated_by,
        operational_date,
        num_fed_funded_ports,
        num_non_fed_funded_ports,
        AFC,
        NEVI,
        CFI,
        EVC_RAA,
        CMAQ,
        CRP,
        OTHER
        {station.get("np_uuid") and ", network_provider_uuid" or ""}

    ) VALUES (
        %(nickname)s,
        %(station_id)s,
        %(dr_id)s,
        %(station_uuid)s,
        %(address)s,
        %(city)s,
        %(state)s,
        %(zip)s,
        %(zip_extended)s,
        %(latitude)s,
        %(longitude)s,
        %(project_type)s,
        %(network_provider)s,
        %(status)s,
        %(updated_on)s,
        %(updated_by)s,
        %(operational_date)s,
        %(num_fed_funded_ports)s,
        %(num_non_fed_funded_ports)s,
        %(AFC)s,
        %(NEVI)s,
        %(CFI)s,
        %(EVC_RAA)s,
        %(CMAQ)s,
        %(CRP)s,
        %(OTHER)s
        {station.get("np_uuid") and ", %(np_uuid)s" or ""}
        )
    """
    insert_succeeded = False
    try:
        cursor.execute(sql, station)
        insert_succeeded = True
    except IntegrityError as e:
        code, message = e.args  # pylint: disable=W0632
        if code == DUPLICATE_ENTRY_ERROR_CODE and "station_registrations.NP_Station_ID" in message:
            raise EvChartDatabaseAuroraDuplicateItemError(
                message=(
                    f"Duplicate key {station.get('station_id')=}, "
                    f"{station.get('network_provider')=}"
                )
            ) from e
    if insert_succeeded is False:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Error registering station {station.get('station_id')}"
        )
