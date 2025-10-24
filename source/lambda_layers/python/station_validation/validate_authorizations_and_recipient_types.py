from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.api_helper import execute_query_fetchone
from evchart_helper.custom_exceptions import (
    EvChartUserNotAuthorizedError,
    EvChartDatabaseDynamoQueryError,
)

from evchart_helper.boto3_manager import boto3_manager
from feature_toggle.feature_enums import Feature

station_registrations = ModuleDataTables["RegisteredStations"].value


def validate_dr_is_authorized(validation_options):
    """
    Convenience function that checks if the current dr user sending the request is also the dr
    assigned to the station. Throws a user not authorized error if dr uuids do not match
    """
    station = validation_options.get("station")
    cursor = validation_options.get("cursor")
    auth_values = validation_options.get("auth_values")
    recipient_type = auth_values.get("recipient_type")
    org_id = auth_values.get("org_id")
    station_dr_id = ""

    if recipient_type == "direct-recipient":
        if validation_options.get("api").lower() == "post" or "dr_id" in station:
            station_dr_id = station.get("dr_id")

        elif validation_options.get("api").lower() == "patch":
            get_dr_for_station_query = f"""
                SELECT dr_id from {station_registrations} WHERE station_uuid = %s
            """
            response = execute_query_fetchone(
                query=get_dr_for_station_query,
                data=station.get(
                    "station_uuid",
                ),
                cursor=cursor,
            )
            station_dr_id = response[0]

        if org_id != station_dr_id:
            raise EvChartUserNotAuthorizedError(
                message="The direct recipient requester cannot be a different org than the dr_id associated with station"
            )
    return True


def validate_recipient_type(validation_options):
    """
    Convenience function that verifies that if a station is being added the user is a DR or an SR submitting a request
    for a station. Or if a station is being edited, then the user must be a DR. Throws a user not authorized error
    if recipient type is invalid
    """
    auth_values = validation_options.get("auth_values")
    feature_toggle_set = validation_options.get("feature_toggle_set")
    api = validation_options.get("api")
    recipient_type = auth_values.get("recipient_type")

    if api.lower() == "post":
        if recipient_type.lower() != "direct-recipient" and (
            recipient_type.lower() != "sub-recipient"
            and Feature.SR_ADDS_STATION in feature_toggle_set
        ):
            raise EvChartUserNotAuthorizedError(
                message="User must be direct recipient to post station"
            )

    elif api.lower() == "patch":
        if recipient_type != "direct-recipient":
            raise EvChartUserNotAuthorizedError(
                message="User must be direct recipient to edit station"
            )
    return True


def validate_authorized_subrecipients(validation_options):
    """
    Convenience function to check that every sr given in valid fields expecting
    sr_lists is of recipient type 'sub-recipient'. Error object is returned if not.
    Valid sr_lists are "authorized_subrecipients", "srs_added", and "srs_removed"
    """
    station = validation_options.get("station")
    sr_fields = ["authorized_subrecipients", "srs_added", "srs_removed"]
    srs_updated, non_srs = [], []
    srs_updated.extend(id for field in sr_fields if field in station for id in station[field])

    if srs_updated:
        dynamodb = boto3_manager.resource("dynamodb")
        table = dynamodb.Table("ev-chart_org")
        for sr in srs_updated:
            try:
                response = table.get_item(Key={"org_id": sr}).get("Item")
                recipient_type = response.get("recipient_type")
            except Exception as e:
                raise EvChartDatabaseDynamoQueryError(
                    message=f"Error thrown in check_sr_type(). Error querying Dynamo for SR type: {e}"
                )

            if recipient_type != "sub-recipient":
                non_srs.append(response.get("name"))

        if non_srs:
            return {
                "validate_authorized_subrecipients()": f"{non_srs} added in request body is not a sub-recipient"
            }
    return True
