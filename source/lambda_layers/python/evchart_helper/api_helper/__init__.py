"""
evchart_helper.api_helper

Holds the functions that executes and returns the queries made to the Dynamo and MySql databases.
In addition, it also contains other helper functions that majority of apis use. This file is meant to store
functions that will be used repeatedly in all apis by importing the method from this file
into the desired api.
"""

import logging
from datetime import datetime
from dateutil import tz
from functools import cache
import pandas as pd
from boto3.dynamodb.conditions import Key
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseDynamoQueryError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedHeadersError,
    EvChartDatabaseAuroraDuplicateItemError,
)
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.user_enums import Roles
from evchart_helper.database_tables import ModuleDataTables
from pymysql.err import IntegrityError
from pymysql.constants.ER import DUP_ENTRY

from feature_toggle.feature_enums import Feature

import_metadata = ModuleDataTables["Metadata"].value
network_providers_table = ModuleDataTables["NetworkProviders"].value
station_registrations = ModuleDataTables["RegisteredStations"].value
station_ports_table = ModuleDataTables["StationPorts"].value

logger = logging.getLogger("Layer_APIHelper")
logger.setLevel(logging.INFO)


def execute_query_common(query, data, cursor, message=None, mode="list"):
    """
    Queries RDS based on given query and data. Parses and
    returns data based on mode passed in (list or dataframe)
    """
    if mode not in {"list", "dataframe"}:
        raise EvChartMissingOrMalformedHeadersError(
            message=f"invalid mode {mode}, must be list or dataframe"
        )

    try:
        cursor.execute(query, data)
    except IntegrityError as e:
        exception_class = EvChartDatabaseAuroraQueryError
        error_message = (
            f"Error thrown in evchart_helper file: api_helper, "
            f"execute_query_common(). Error querying the database: {repr(e)} "
        )

        e_code, e_message = e.args
        if e_code == DUP_ENTRY:
            exception_class = EvChartDatabaseAuroraDuplicateItemError
            error_message = (
                f"Error thrown in evchart_helper file: api_helper, "
                f"execute_query_common(). Duplicate entry: {e_message} "
            )
        if message is not None:
            error_message += message
        raise exception_class(message=error_message)
    except Exception as e:
        error_message = (
            f"Error thrown in evchart_helper file: api_helper, "
            f"execute_query_common(). Error querying the database: {repr(e)} "
        )
        if message is not None:
            error_message += message
        raise EvChartDatabaseAuroraQueryError(message=error_message)

    row_data = cursor.fetchall()

    if mode == "dataframe":
        column_names = [column[0] for column in cursor.description]
        dataframe = pd.DataFrame(row_data, columns=column_names)
        return dataframe
    # mode is list
    output = []
    if row_data is None or cursor.rowcount == 0:
        logger.debug(f"No data was returned from the database fetchall().")
        return output

    if cursor.rowcount > 0:
        output = [
            dict((cursor.description[i][0], value) for i, value in enumerate(row))
            for row in row_data
        ]

    return output


def execute_query(query, data, cursor, message=None):
    """
    Returns list of data, given query and data.
    """
    return execute_query_common(query=query, data=data, cursor=cursor, message=message, mode="list")


def execute_query_df(query, data, cursor, message=None):
    """
    Returns dataframe of data, given query and data.
    """
    return execute_query_common(
        query=query, data=data, cursor=cursor, message=message, mode="dataframe"
    )


def execute_query_fetchone(query, data, cursor, message=None):
    """
    Returns a list of row data from one single entry or None. Pass
    in any relevant data and cursor from parent function.
    """
    try:
        cursor.execute(query, data)

    except Exception as e:
        logger.debug(f"aurora error: {e}")
        error_message = f"Error thrown in evchart_helper file: api_helper, execute_query_fetchone(). Error querying the database: {e}"
        if message is not None:
            error_message += message
        raise EvChartDatabaseAuroraQueryError(message=error_message)

    row_data = cursor.fetchone()

    if row_data is None:
        logger.debug(f"No data returned from database fetchone().")

    return row_data


def execute_proc(procedure, data, cursor, log=None, operation=None, message=None):
    """
    Used to execute a stored procedure and return data in dictionary format. Pass
    in any relevant data and cursor from parent function. Returns None if no data
    found.
    """
    try:
        cursor.callproc(procedure, data)

    except Exception as e:
        error_message = f"Error thrown in evchart_helper file: api_helper, execute_proc(). Error querying the database: {e} "
        if message is not None:
            error_message += message
        raise EvChartDatabaseAuroraQueryError(message=error_message)

    row_data = cursor.fetchall()
    output = []
    if row_data is None or cursor.rowcount == 0:
        logger.debug(f"No data was returned from the database fetchall().")
        return output

    if cursor.rowcount > 0:
        output = [
            dict((cursor.description[i][0], value) for i, value in enumerate(row))
            for row in row_data
        ]

    return output


@cache
def _get_org_info_dynamo_cache(org_id):
    """
    Queries Dynamo Org table given an org_id.
    """
    dynamodb = boto3_manager.resource("dynamodb")

    table = dynamodb.Table("ev-chart_org")
    return table.get_item(Key={"org_id": org_id})


def get_org_info_dynamo(org_id, log=None):
    """
    Returns all fields from Org table in Dynamo
    based off a given org_id or errors if no org is present.
    """
    try:
        org_response = _get_org_info_dynamo_cache(org_id)

        if not org_response.get("Item"):
            error_message = f"No data returned from Dynamo " f"for given org_id {org_id}"
            raise EvChartDatabaseDynamoQueryError(message=error_message)

    except Exception as err:
        error_message = f"Error retrieving org {org_id} from Dynamo: {err}"
        raise EvChartDatabaseDynamoQueryError(message=error_message)
    return org_response.get("Item")


def get_orgs_by_recipient_type_dynamo(recipient_type):
    """
        Returns all the organization info for organizations with the passed in recipient_type
    """
    _recipient_type = recipient_type.replace("_","-")
    try:
        dynamodb = boto3_manager.resource("dynamodb")

        table = dynamodb.Table("ev-chart_org")
        response = table.query(
            KeyConditionExpression=Key("recipient_type").eq(recipient_type), IndexName="gsi_recipient_type"
        )
        return response["Items"]

    except Exception as err:
        error_message = f"Error retrieving {_recipient_type} organizations from Dynamo: {err}"
        raise EvChartDatabaseDynamoQueryError(message=error_message)


def get_user_org_id(identifier):
    """
    Returns identifier from Dynamo User table. Used in cases where
    there is an email for a user not found through the auth token and
    the organization ID is needed for that user.
    """
    dynamodb = boto3_manager.resource("dynamodb")
    table = dynamodb.Table("ev-chart_users")

    try:
        return table.get_item(Key={"identifier": identifier.lower()})["Item"]["org_id"]

    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(message=f'Error in "get_user_org_id()".: {e}')


def get_org_users(org_id, log_event=None):
    """
    Queries Dynamo User table for all users
    in a given organization, based on org_id.
    """
    try:
        dynamodb = boto3_manager.resource("dynamodb")

        table = dynamodb.Table("ev-chart_users")
        users_response = table.query(
            KeyConditionExpression=Key("org_id").eq(org_id), IndexName="gsi_org_id"
        )
        return users_response
    except Exception as err:
        raise EvChartDatabaseDynamoQueryError(
            operation="select",
            log_obj=log_event,
            message=f"Error querying DynamoDB for users in org {org_id}: {err}",
        )


def format_users(org_users):
    """
    Formats users that are grabbed from the Dynamo table,
    checks that fields are present.
    """
    try:
        formatted_users = []
        for row in org_users["Items"]:
            user = {}
            user["first_name"] = row.get("first_name")
            user["last_name"] = row.get("last_name")
            role = row.get("role")
            try:
                user["role"] = Roles[role].value
            except KeyError:
                user["role"] = "Not Defined"
            user["email"] = row.get("identifier")
            user["status"] = row.get("account_status")
            formatted_users.append(user)
        return formatted_users
    except Exception as err:
        raise EvChartJsonOutputError(message=f"Error formatting users: {err}")


def get_headers(log=None, event={}, headers=[]):
    """
    Returns dictionary of correct headers parsed from event. Error is
    thrown if header is incorrect.
    """
    try:
        header_dict = {}
        for variable in headers:
            header_dict[variable] = event["headers"][variable]

        return header_dict

    except Exception as e:
        error_message = (
            f"Error thrown in evchart_helper file: api_helper, get_headers(). Error: {e}"
        )
        raise EvChartMissingOrMalformedHeadersError(message=error_message)


def query_builder_station_uuid(station_id, network_provider):
    """
    Queries station_registrations table for staiton_uuid based on given
    station_id, dr_id, and (if FT on), network_provider.
    """
    station_registrations_table = ModuleDataTables["RegisteredStations"].value

    station_uuid_query = (
        f"SELECT station_uuid FROM {station_registrations_table} sr "
        f"INNER JOIN {network_providers_table} np ON sr.network_provider_uuid = np.network_provider_uuid "
        f"WHERE station_id=%s and np.network_provider_value=%s"
    )
    data = (station_id, network_provider)

    return station_uuid_query, data


def query_builder_station_with_ports(station_id, network_provider):
    """
    Queries station_registrations table for staiton_uuid based on given
    station_id, dr_id, and (if FT on), network_provider.
    if no ports exists station will be returned and port_uuid and port_id
    will be null
    """
    station_registrations_table = ModuleDataTables["RegisteredStations"].value

    station_uuid_query = (
        f"SELECT sr.station_uuid, sr.network_provider_uuid, sp.port_uuid, sp.port_id "
        f"FROM {station_registrations_table} sr "
        f"INNER JOIN {network_providers_table} np ON sr.network_provider_uuid = np.network_provider_uuid "
        f"LEFT JOIN {station_ports_table} sp ON sr.station_uuid = sp.station_uuid "
        f"WHERE station_id=%s and np.network_provider_value=%s"
    )
    data = (station_id, network_provider)

    return station_uuid_query, data


def get_station_and_port_uuid(cursor, station_id, network_provider, port_id=None):
    """
    Returns single station_uuid, and port_uuid from station_registrations table
    joined with station_ports table
    based on given inputs.
    """
    station_and_port_query, data = query_builder_station_with_ports(station_id, network_provider)

    result_df = execute_query_df(
        query=station_and_port_query,
        data=data,
        cursor=cursor,
        message=("Error thrown in authorization_registration helper file: " "get_station_uuid()"),
    )

    df_row = pd.DataFrame(columns=result_df.columns)
    # get row with port_id if none return row without port_uuid
    if not result_df.empty:
        if port_id is not None:
            df_row = result_df.loc[result_df["port_id"] == port_id]

        if df_row.empty:
            df_row.at[0, "station_uuid"] = result_df.loc[0, "station_uuid"]
            df_row.at[0, "network_provider_uuid"] = result_df.loc[0, "network_provider_uuid"]
            df_row.at[0, "port_uuid"] = None
            df_row.at[0, "port_id"] = None

        return_dict = df_row.iloc[0].to_dict()
    else:
        raise EvChartDatabaseAuroraQueryError(
            message=(
                f"Error thrown in evchart_helper file: get_station_and_port_uuid, "
                f"execute_query_df() returned no data for (station_id, network provieder): ({station_id}, {network_provider})"
            )
        )

    return return_dict


def get_station_uuid(cursor, station_id, network_provider=None):
    """
    Returns single station_uuid from station_registrations table
    based on given inputs.
    """
    station_uuid_query, data = query_builder_station_uuid(
        station_id, network_provider
    )
    logger.debug(f"station uuid query: {station_uuid_query}")
    result_arr = execute_query_fetchone(
        query=station_uuid_query,
        data=data,
        cursor=cursor,
        message=("Error thrown in authorization_registration helper file: " "get_station_uuid()"),
    )
    logger.debug(f"result arr: {result_arr}")
    if result_arr is None or len(result_arr) == 0:
        return None

    return result_arr[0]


def get_upload_metadata(cursor, upload_id):
    """
    Returns all fields from import_metadata table
    based on upload_id, or None if there are no matches.
    """
    # raise NotImplementedError()
    select_statement = f"""
        SELECT *
        FROM {import_metadata}
        WHERE upload_id=%s
        """
    result = execute_query(
        query=select_statement,
        data=upload_id,
        cursor=cursor,
        message="get_upload_metadata AsyncDataValidation",
    )

    if result is None or len(result) == 0:
        logger.info("upload id returned no results: %s", upload_id)
        return None
    return result[0]


@cache
def _get_user_info_dynamo_cache(user_id):
    """
    Queries Dynamo users table, returns entire
    User object.
    """
    dynamodb = boto3_manager.resource("dynamodb")

    table = dynamodb.Table("ev-chart_users")
    return table.get_item(Key={"identifier": user_id.lower()})


def get_user_info_dynamo(user_id, log=None):
    """
    Returns resulting Item (user) object
    from Dynamo query based on user_id.
    """
    try:
        user_response = _get_user_info_dynamo_cache(user_id)
    except Exception as err:
        error_message = f"Error retrieving user {user_id} from Dynamo: {err}"
        raise EvChartDatabaseDynamoQueryError(message=error_message)
    return user_response.get("Item")


def get_validated_dt():
    """
    Returns UTC formatted DateTime, now.
    """
    date_obj = datetime.now(tz.gettz("UTC"))
    formatted_date = str(date_obj.strftime("%Y-%m-%dT%H:%M:%SZ"))

    return formatted_date


def get_available_years(todays_date):
    year_list = []
    starting_year = 2023
    ending_year = todays_date.year

    if todays_date.month < 4:
        ending_year = ending_year - 1

    for year in range(starting_year, ending_year + 1):
        string_year = str(year)
        year_list.append(string_year)
    year_list.reverse()
    return year_list
