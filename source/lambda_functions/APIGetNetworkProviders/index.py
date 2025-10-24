"""
APIGetNetworkProviders

Return a list of valid network providers for the frontend to display.
"""
import json
from evchart_helper import aurora
from evchart_helper.api_helper import execute_query
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.custom_exceptions import EvChartAuthorizationTokenInvalidError, EvChartDatabaseAuroraQueryError, EvChartFeatureStoreConnectionError
from evchart_helper.network_provider import network_providers_internal
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

network_providers = ModuleDataTables["NetworkProviders"].value


@SessionManager.check_session()
def handler(event, _context):
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            log_event = LogEvent(event, api="APIGetNetworkProviders", action_type="Read")
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()
            feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

            if (Feature.NETWORK_PROVIDER_TABLE in feature_toggle_set):
                output = get_network_providers(cursor)
            else:
                output = network_providers_internal

        except (EvChartAuthorizationTokenInvalidError,
                EvChartFeatureStoreConnectionError,
                EvChartDatabaseAuroraQueryError) as e:
            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="Successfully retrieved Network Providers",
                status_code=200
            )
            return_obj = {
                'statusCode' : 200,
                'headers': { "Access-Control-Allow-Origin": "*" },
                'body': json.dumps(output)
            }

        return return_obj

def get_network_providers(cursor):
    try:
        query = f"""
            SELECT network_provider_uuid, network_provider_value, description
            FROM {network_providers} ORDER BY network_provider_value ASC
        """ # nosec - SQL injection not possible
        output = execute_query(query=query, data=None, cursor=cursor, message=f"get network providers")
        return output
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Error retrieving network providers: {e}"
        ) from e
