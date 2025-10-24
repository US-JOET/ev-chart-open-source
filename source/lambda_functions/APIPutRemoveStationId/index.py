"""
APIPutRemoveStationId

This api deletes the station data from the station_registration, station_authorization, station_ports,
and station_registrations_history table for the provided station_uuid. In order for the station data
to be deleted, the org_id from the token must match the dr_id associated with the station_uuid in the
station_registration table and no other module data associated with that uuid should be present in
module tables 2-9 or the error table.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
import json
import re

from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from evchart_helper import aurora
from evchart_helper.session import SessionManager
from evchart_helper.api_helper import (
    execute_query,
    format_users,
    get_org_info_dynamo,
    get_org_users,
    get_user_org_id,
)
from evchart_helper.station_helper import (
    remove_station,
    get_formatted_station_ports,
)
from feature_toggle import (
    FeatureToggleService,
    feature_enablement_check,
)
from feature_toggle.feature_enums import Feature
from evchart_helper.database_tables import ModuleDataTables


from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartMissingOrMalformedBodyError,
    EvChartUserNotAuthorizedError,
)

from evchart_helper.custom_logging import LogEvent

STATION_REGISTRATIONS = ModuleDataTables["RegisteredStations"].value
STATION_AUTHORIZATIONS = ModuleDataTables["StationAuthorizations"].value
STATION_PORTS = ModuleDataTables["StationPorts"].value
NETWORK_PROVIDERS = ModuleDataTables["NetworkProviders"].value


@SessionManager.check_session()
@feature_enablement_check(Feature.REMOVE_STATION)
def handler(event, _context):
    log_event = LogEvent(event, api="APIPutRemoveStationId", action_type="PUT")
    if not log_event.is_auth_token_valid():
        raise EvChartAuthorizationTokenInvalidError()

    token = log_event.get_auth_token()
    feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            verify_recipient_type(token)
            station_uuid = get_station_uuid_from_event(event)
            # station_details = is_valid_station(station_uuid, cursor)[0]
            station_details = get_station_details(station_uuid, cursor)[0]
            verify_station_ownership(cursor, token.get("org_id"), station_uuid)

            if (
                Feature.SR_ADDS_STATION in feature_toggle_set
                and station_details.get("status") == "Pending Approval"
            ):
                send_station_reject_email(
                    station_details, cursor, token, json.loads(event["body"]).get("comments")
                )

            remove_station(station_uuid, cursor)

        except (
            EvChartAuthorizationTokenInvalidError,
            EvChartDatabaseAuroraQueryError,
            EvChartDatabaseAuroraDuplicateItemError,
            EvChartMissingOrMalformedBodyError,
            EvChartUserNotAuthorizedError,
        ) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="APIPutRemoveStationId successfully invoked", status_code=201
            )
            return_obj = {
                "statusCode": 201,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps("Station successfully deleted"),
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


def send_station_reject_email(station_details, cursor, token, comments):
    sr_org_id = get_user_org_id(station_details["updated_by"])
    sr_org_name = get_org_info_dynamo(sr_org_id)["name"]
    associated_srs = get_org_users(sr_org_id)
    formatted_srs = format_users(associated_srs)
    funding_types = []
    for funding_type in ["NEVI", "CFI", "EVC_RAA", "CMAQ", "CRP", "OTHER"]:
        if station_details[funding_type]:
            funding_types.append(
                funding_type.title() if funding_type == "OTHER" else re.sub("_", "-", funding_type)
            )

    for user in formatted_srs:
        if user.get("status") == "Active" and user.get("role") == "Administrator":
            trigger_email(
                {
                    "email": user.get("email").strip(),
                    "email_type": Email_Template.DR_REJECTS_SR_STATION,
                    "sr_org_name": sr_org_name,
                    "dr_org_name": token["org_name"],
                    "first_name": user.get("first_name").strip(),
                    "station_nickname": station_details["nickname"],
                    "station_id": station_details["station_id"],
                    "updated_on": datetime.now(ZoneInfo("America/New_York")),
                    "updated_by": token["name"],
                    "feedback": comments,
                    "station_address": station_details["address"].title(),
                    "station_city": station_details["city"].title(),
                    "station_state": station_details["state"].upper(),
                    "station_zip": station_details["zip"],
                    "station_zip_extended": station_details["zip_extended"],
                    "station_lat": station_details["latitude"],
                    "station_long": station_details["longitude"],
                    "station_np": station_details["network_provider"],
                    "station_project_type": station_details["project_type"],
                    "station_operational_date": station_details["operational_date"],
                    "station_funding_type": ", ".join(funding_types),
                    "station_afc": bool(station_details["AFC"]),
                    "ports_num_fed": station_details["num_fed_funded_ports"],
                    "ports_num_non_fed": station_details["num_non_fed_funded_ports"],
                    "ports_fed": get_formatted_station_ports(
                        station_details["station_uuid"], cursor
                    ),
                    "station_is_federally_funded": station_details["is_federally_funded"],
                }
            )


# returns station_uuid if found in body of event, else throws error
def get_station_uuid_from_event(event):
    request_body = json.loads(event["body"])
    if "station_uuid" not in request_body:
        raise EvChartMissingOrMalformedBodyError(message="Missing from body: station_uuid")
    return request_body["station_uuid"]


# returns true if user is direct-recipient
def verify_recipient_type(token):
    if token.get("recipient_type").lower() != "direct-recipient":
        raise EvChartAuthorizationTokenInvalidError(
            message="Error thrown in verify_recipient_type(). Only DRs can delete a station."
        )
    return True


# throws an error if the station_uuid is not associated with the dr_id from the token
def verify_station_ownership(cursor, dr_id, station_uuid):
    station_registration_table = ModuleDataTables["RegisteredStations"].value
    query = f"SELECT * FROM {station_registration_table} where dr_id=%s and station_uuid=%s"
    output = execute_query(query=query, data=(dr_id, station_uuid), cursor=cursor)
    if not output:
        raise EvChartUserNotAuthorizedError(
            message=f"Organization {dr_id} does not have authority to delete station {station_uuid}"
        )
    return True


def get_station_details(station_uuid, cursor, feature_toggle_set=frozenset()):
    """
    Convenience function that returns station details that
    reflects if a station is federally funded the same way as
    program performance dashboard.
    """
    query = f"""
        SELECT sr.*, MAX(
        (sr.num_fed_funded_ports IS NOT NULL AND sr.num_fed_funded_ports > 0)
        OR sp.federally_funded = 1
        OR (
        sr.NEVI = 1
        OR sr.CFI = 1
        OR sr.EVC_RAA = 1
        OR sr.CMAQ = 1
        OR sr.CRP = 1
        OR sr.OTHER = 1
        ))  AS is_federally_funded 
        FROM {STATION_REGISTRATIONS} AS sr
        LEFT JOIN {STATION_PORTS} AS sp ON sp.station_uuid = sr.station_uuid
        WHERE sr.station_uuid=%s
        GROUP BY sr.station_uuid;"""  # nosec - SQL injection not possible
    data = (station_uuid,)
    output = execute_query(query, data, cursor)
    if output:
        return output
    raise EvChartMissingOrMalformedBodyError(
        message=f"Error thrown in is_valid_station(). No station found for station uuid {station_uuid}."
    )
