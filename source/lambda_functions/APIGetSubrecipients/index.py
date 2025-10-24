"""
APIGetSubrecipients

Returns a list of dictionaries of containing the organization information for rows in the
Dynamo table with the "sub-recipient" role type. If the event body contains the variable
"only_authorized" and is set to True, then only the list of authorized subrecipients of
the organization that made the call will be returned for stations in active status
"""

import json

from evchart_helper.boto3_manager import boto3_manager
from evchart_helper import aurora
from evchart_helper.api_helper import execute_query
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartDatabaseDynamoQueryError,
    EvChartDatabaseAuroraQueryError,
    EvChartMissingOrMalformedHeadersError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.session import SessionManager
from evchart_helper.station_helper import get_fed_funded_filter


@SessionManager.check_session()
def handler(event, _context):
    try:
        log_event = LogEvent(event, api="APIGetSubrecipients", action_type="Read")
        if log_event.is_auth_token_valid() is False:
            raise EvChartAuthorizationTokenInvalidError()

        dynamodb = boto3_manager.resource("dynamodb")

        auth_values = log_event.get_auth_token()
        caller_org_name = auth_values.get("org_name")
        org_id = auth_values.get("org_id")
        event_headers = event.get("headers", {})
        only_authorized = event_headers.get("only_authorized", False)
        path_parameters = event.get("queryStringParameters")
        # the event sets it to None
        if path_parameters is None:
            path_parameters = dict()

        filter_only_fed_funded = path_parameters.get("only_fed_funded", "")

        if only_authorized:
            use_fed_funded_filter = filter_only_fed_funded.lower() == "true"
            authorized_sr_ids = get_authorized_srs(org_id, use_fed_funded_filter)
            all_sr_list = get_srs(caller_org_name, dynamodb)
            print(authorized_sr_ids)
            sr_list = []
            for row in all_sr_list:
                if row["org_id"] in authorized_sr_ids:
                    sr_list.append(row)
        else:
            sr_list = get_srs(caller_org_name, dynamodb)

    except (
        EvChartAuthorizationTokenInvalidError,
        EvChartDatabaseDynamoQueryError,
        EvChartDatabaseAuroraQueryError,
    ) as e:
        log_event.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
        )
        return_obj = e.get_error_obj()

    else:
        log_event.log_successful_request(
            message="Successfully returned subrecipients", status_code=200
        )
        return_obj = {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(sr_list),
        }

    return return_obj


def get_srs(caller_org_name, dynamodb):
    try:
        table = dynamodb.Table("ev-chart_org")
        if caller_org_name == "Joint Office Direct Recipient" or caller_org_name == "JOET":
            items = table.scan(
                FilterExpression="recipient_type = :type",
                ExpressionAttributeValues={":type": "sub-recipient"},
            ).get("Items")
        else:
            items = table.scan(
                FilterExpression="recipient_type = :type AND #n <> :sr_name",
                ExpressionAttributeNames={"#n": "name"},
                ExpressionAttributeValues={
                    ":type": "sub-recipient",
                    ":sr_name": "Joint Office Sub Recipient",
                },
            ).get("Items")

        return items

    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(
            message="Could not get subrecipients from dynamo table"
        )


def get_authorized_srs(org_id, use_fed_only_filter):
    """
    Returns a list of sr ids for authorized srs with active stations or active and federally funded stations.
    """
    try:
        connection = aurora.get_connection()
        with connection.cursor() as cursor:
            join_values = ""
            fed_only_filter = ""
            station_registration_table = ModuleDataTables.RegisteredStations.value
            station_ports_table = ModuleDataTables.StationPorts.value
            station_auth_table = ModuleDataTables.StationAuthorizations.value

            if use_fed_only_filter:
                join_values = f"""
                    LEFT JOIN {station_ports_table} AS sp ON sp.station_uuid = sa.station_uuid
                    LEFT JOIN {station_registration_table} AS sr1 ON sr1.station_uuid = sa.station_uuid
                """
                fed_only_filter = get_fed_funded_filter("sr1", "sp")

            # using the station registration table with a different alias to filter on active stations
            auth_sr_query = f"""
            SELECT DISTINCT sr_id FROM {station_auth_table} AS sa
            LEFT JOIN {station_registration_table} AS sr2 ON sr2.station_uuid = sa.station_uuid
            {join_values}
            WHERE sa.dr_id=%s
            AND sr2.status = "Active"
            {fed_only_filter}
            """

            output = execute_query(
                query=auth_sr_query,
                data=(org_id,),
                cursor=cursor,
                message="Error thrown in APIGetSubrecipients on get",
            )
            aurora.close_connection()
            formatted_output = []
            for item in output:
                formatted_output.append(item["sr_id"])
            return formatted_output
    except (
        EvChartDatabaseAuroraQueryError,
        EvChartMissingOrMalformedHeadersError,
        EvChartDatabaseAuroraDuplicateItemError,
    ) as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Could not get authorized subrecipients from aurora table {e.message}"
        ) from e
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Could not get authorized subrecipients from aurora table {repr(e)}"
        ) from e
