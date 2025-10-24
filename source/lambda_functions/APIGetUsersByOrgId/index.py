"""
APIGetUsersByOrgId

Returns all the users from the Dynamo table with the same org_id from the
authorization token that made the call
"""
import json
from evchart_helper.api_helper import format_users, get_org_users
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError, EvChartDatabaseDynamoQueryError,
    EvChartJsonOutputError)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.session import SessionManager


@SessionManager.check_session()
def handler(event, _context):
    try:
        log_event = LogEvent(event, api="APIGetUsersByOrgId", action_type="READ")
        if log_event.is_auth_token_valid() == False:
            raise EvChartAuthorizationTokenInvalidError(log_obj= log_event)

        auth_token = log_event.get_auth_token()
        org_id = auth_token["org_id"]

        output = []
        org_users = get_org_users(org_id, log_event)
        if org_users:
            output = format_users(org_users)

    except (EvChartAuthorizationTokenInvalidError,
            EvChartDatabaseDynamoQueryError,
            EvChartJsonOutputError
            ) as e:
        return_obj = e.get_error_obj()

    else:
        log_event.log_successful_request(message="Logging Success Message", status_code=200)
        return_obj = {
            'statusCode' : 200,
            'headers': { "Access-Control-Allow-Origin": "*" },
            'body': json.dumps(output)
        }
    return return_obj
