"""
APIGetDirectRecipients

Returns a list of direct recipients and their org_id, name, and org_friendly_id depending on recipient type or
if there is a route specified. If a user is JO or an SR adding a station, the entire list of direct recipients
is returned. If a user is an sub-recipient with no route specified, the list that is returned is the
direct recipients that the sub-recipient is authorized to submit for.
"""
import json

from evchart_helper import aurora
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartJsonOutputError,
    EvChartDatabaseDynamoQueryError,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.session import SessionManager
from evchart_helper.user_helper import get_authorized_drs
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

from boto3.dynamodb.conditions import Key


@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()
    result = []
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(
                event, api="APIGetDirectRecipients", action_type="Read"
            )
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()

            features = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

            # getting path parameters if present, currently only passed in for sr adding station
            path_parameters = event.get("queryStringParameters")
            route = path_parameters.get("route", []) if path_parameters else []

            token = log_event.get_auth_token()
            recipient_type = validate_recipient_type(token)

            # if user is JO or user is SR registering a station, return all DRs
            if recipient_type == "joet" or (
                recipient_type == "sub-recipient" and route == "station_registration"
            ):
                result = get_all_drs_org_info()
            # elif an SR, get only relevant DRs
            elif recipient_type == "sub-recipient":
                list_of_drs_authd = get_authorized_drs(
                    token.get("org_id"),
                    cursor,
                    n_tier_enabled=Feature.N_TIER_ORGANIZATIONS in features
                )
                all_drs = get_all_drs_org_info()
                result = create_auth_mapping(list_of_drs_authd, all_drs)

        except (
            EvChartAuthorizationTokenInvalidError,
            EvChartDatabaseAuroraQueryError,
            EvChartDatabaseDynamoQueryError,
            EvChartJsonOutputError,
            EvChartUserNotAuthorizedError,
        ) as e:
            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="Successfully retreived all DRs", status_code=200
            )
            return_obj = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(result),
            }

    return return_obj


# map list of authd DRs to their org information
def create_auth_mapping(auth_dr_list, all_drs):
    result = []
    try:
        result = [
            {
                "org_id": org["org_id"],
                "name": org["name"],
                "org_friendly_id": org["org_friendly_id"],
            }
            for org in all_drs
            if org["org_id"] in auth_dr_list
        ]
    except Exception as e:
        raise EvChartJsonOutputError(
            message="Error thrown in create_auth_mapping()."
        ) from e

    return result


# validate that current user is JO or SR
def validate_recipient_type(token):
    # getting recipient_type from the auth token
    recipient_type = token.get("recipient_type").lower()

    if recipient_type not in {'joet', 'sub-recipient'}:
        raise EvChartUserNotAuthorizedError(
            message=(
                "User must be JO or SR user in order to retreive "
                "full list of DRs"
            )
        )

    return recipient_type


# helper method that queries the org dynamo db table for a list of all DRs
def get_all_drs_org_info():
    dynamodb = boto3_manager.resource("dynamodb")
    try:
        table = dynamodb.Table("ev-chart_org")
        response = table.query(
            IndexName="gsi_recipient_type",
            KeyConditionExpression=(
                Key("recipient_type").eq("direct-recipient")
            ),
        )
        return response["Items"]

    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(
            message=f"Could not get drs from dynamo table:{e}"
        ) from e
