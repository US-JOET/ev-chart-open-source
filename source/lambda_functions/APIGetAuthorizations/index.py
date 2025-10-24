"""
APIGetAuthorizations

Return the set of station authorizations for a given authorizer (typically a DR but not always) and
authorizee (always an SR).
"""
import json

from evchart_helper import aurora
from evchart_helper.api_helper import execute_query
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartMissingOrMalformedHeadersError
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature


@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(event, api="APIGetAuthorizations", action_type="Read")
            if not log_event.is_auth_token_valid():
                raise EvChartAuthorizationTokenInvalidError()

            features = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

            auth_values = log_event.get_auth_token()
            org_id = auth_values.get("org_id")
            recipient_type = auth_values.get("recipient_type")
            if recipient_type != "sub-recipient":
                raise EvChartMissingOrMalformedHeadersError(
                    message="Only sub-recipients are currently implemented for APIGetAuthorizations"
                )
            output = drs_exist(org_id, features, cursor)

        except (EvChartAuthorizationTokenInvalidError,
                EvChartMissingOrMalformedHeadersError,
                EvChartDatabaseAuroraQueryError
        ) as e:
            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="Successfully retrieved authorization boolean",
                status_code=200
            )
            return_obj = {
                'statusCode' : 200,
                'headers': { "Access-Control-Allow-Origin": "*" },
                'body': json.dumps(output)
            }
        aurora.close_connection()
        return return_obj


def drs_exist(org_id, features, cursor):
    table = ModuleDataTables.StationAuthorizations.value
    authorizer_column = "dr_id"
    authorizee_column = "sr_id"

    if Feature.N_TIER_ORGANIZATIONS in features:
        authorizer_column = "authorizer"
        authorizee_column = "authorizee"

    query = (
        f"SELECT {authorizer_column} from {table} " # nosec - no SQL injection possible
        f"WHERE {authorizee_column}=%s" # nosec - no SQL injection possible
    )
    output = execute_query(
        query=query,
        data=(org_id,),
        cursor=cursor,
        message=f"get authorized orgs for SR {org_id}"
    )

    return bool(output)
