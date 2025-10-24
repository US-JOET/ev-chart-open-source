"""
APIGetOrgUserData

Returns a dictionary with the name of the current organization that called the endpoint,
and the number of users in the Dynamo database associated with the same organization
"""

import json

from boto3.dynamodb.conditions import Attr
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError, EvChartDatabaseDynamoQueryError)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.session import SessionManager


@SessionManager.check_session()
def handler(event, _context):
    try:
        log_event = LogEvent(event, api="APIGetOrgUserData", action_type="Read")
        if log_event.is_auth_token_valid() is False:
            raise EvChartAuthorizationTokenInvalidError()
        output = {}

        token = log_event.get_auth_token()
        org_id = token["org_id"]
        org_name = token["org_name"]

        user_data = get_user_data(org_id)
        if user_data >= 0:
            output["user_count"] = user_data
        output["org_name"] = org_name

    except (EvChartAuthorizationTokenInvalidError,
            EvChartDatabaseDynamoQueryError
    ) as e:
        log_event.log_custom_exception(
            message=e.message,
            status_code=e.status_code,
            log_level=e.log_level
        )
        return_obj = e.get_error_obj()

    else:
        log_event.log_successful_request(
            message="Successfully returned number of users in org",
            status_code=200
        )
        return_obj = {
            'statusCode' : 200,
            'headers': { "Access-Control-Allow-Origin": "*" },
            'body': json.dumps(output)
        }

    return return_obj

def get_user_data(org_id):
    try:
        dynamodb = boto3_manager.resource("dynamodb")

        table = dynamodb.Table("ev-chart_users")
        users_response = table.scan(FilterExpression=Attr('org_id').eq(org_id), Select="COUNT")

        return users_response.get('Count')
    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(message="Error querying DynamoDB.")
