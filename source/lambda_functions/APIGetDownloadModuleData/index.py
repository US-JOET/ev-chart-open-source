"""
APIGetDownloadModuleData

This api takes in the necessary querying fields/filters in order to retrieve approved/submitted
module data for JO and DR users. It formats the fields and calls the ev_chart_download_modules
database stored procedure which returns the module data. The api generates and returns a
presigned url that contains the desired data.
"""
from datetime import datetime, timezone
from decimal import Decimal
import json
import uuid

import pandas as pd
from boto3.dynamodb.conditions import Key

from evchart_helper import aurora
from evchart_helper.api_helper import (
    execute_query_df,
    get_available_years,
    get_org_info_dynamo,
    get_orgs_by_recipient_type_dynamo,
)
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartAuthorizationTokenInvalidError,
    EvChartMissingOrMalformedHeadersError,
    EvChartUserNotAuthorizedError,
    EvChartJsonOutputError,
    EvChartDatabaseDynamoQueryError,
    EvChartFeatureStoreConnectionError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.module_helper import format_dataframe_date, format_dataframe_bool
from evchart_helper.station_helper import get_fed_funded_filter, get_non_fed_funded_filter
from evchart_helper.presigned_url import generate_presigned_url
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature
from evchart_helper.database_tables import ModuleDataTables
from database_central_config import DatabaseCentralConfig
from evchart_helper.module_enums import get_db_col_names_arr


network_providers = ModuleDataTables["NetworkProviders"].value
import_metadata = ModuleDataTables["Metadata"].value
station_registrations = ModuleDataTables["RegisteredStations"].value
station_authorizations = ModuleDataTables["StationAuthorizations"].value
station_ports = ModuleDataTables["StationPorts"].value
DEFAULT_VALUE = "-1"

@SessionManager.check_session()
def handler(event, _context):
    log_event = LogEvent(event, api="APIDownloadModuleData", action_type="READ")
    connection = aurora.get_connection(use_read_only=True)

    with connection.cursor() as cursor:
        try:
            feature_toggle_set = \
                FeatureToggleService().get_active_feature_toggles(
                    log_event=log_event
                )
            if not log_event.is_auth_token_valid():
                raise EvChartAuthorizationTokenInvalidError()
            request_fields = get_formatted_fields_from_event(event.get("queryStringParameters"), feature_toggle_set)

            # validates data passed in
            validate_fields(request_fields, cursor, feature_toggle_set)

            # validates user
            token = log_event.get_auth_token()
            validate_recipient_type(token)

            # creates sql statement and queries db
            cursor.execute("use evchart_data_v3;")

            if Feature.QUERY_DOWNLOAD_REFACTOR in feature_toggle_set:
                filters = get_query_filters(token, cursor, request_fields, feature_toggle_set)
                query_and_data = get_query_and_data(filters, request_fields, feature_toggle_set)
                statement = query_and_data["query"]
                data = query_and_data["data"]
            else:
                statement = statement_builder(feature_toggle_set)
                data = get_stored_proc_data(request_fields)

            dataframe = execute_query_df(
                query=statement,
                data=data,
                cursor=cursor,
                message="APIDownloadModuleData",
            )

            if request_fields["modules"][0] == "1":
                get_port_information(cursor, dataframe)
                get_sr_information(cursor, dataframe)

            # formatting df for output
            is_data_present = None
            if not dataframe.empty:
                format_dataframe_bool(dataframe, feature_toggle_set)
                format_dataframe_date(dataframe, True)
                dataframe = dataframe.map(
                    lambda x: str(x) if isinstance(x, Decimal) else x
                )

                # formatting uuids for drs and srs
                dataframe = format_dataframe_uuid(
                    dataframe, col_name="dr_id", recipient_type="direct-recipient"
                )
                if "sr_id" in dataframe.columns:
                    dataframe = format_dataframe_uuid(
                        dataframe, col_name="sr_id", recipient_type="sub-recipient"
                    )

                # formatting name of module
                if "module" in dataframe.columns and Feature.QUERY_DOWNLOAD_REFACTOR not in feature_toggle_set:
                    dataframe = format_dataframe_module(dataframe)

                # setting system generated key constraints to null if null module was submitted
                system_generated_fields=["outage_id", "session_id"]
                field_present = [field for field in system_generated_fields if field in dataframe.columns]
                if field_present:
                    dataframe.loc[(dataframe['user_reports_no_data'] == "TRUE") | (dataframe['user_reports_no_data'] == True), field_present] = pd.NA
                # dropping necessary columns that we don't want returned to user
                columns_to_drop = [
                    "upload_id",
                    "station_uuid",
                    "network_provider_uuid",
                    "network_provider",
                    "port_uuid",
                    "port_id_upload",
                    "user_reports_no_data",
                    "time_at_upload",
                    "updated_on",
                    "updated_by"
                ]

                dataframe = dataframe.drop(columns=[col for col in columns_to_drop if col in dataframe.columns])

                if "network_provider_value" in dataframe.columns:
                    dataframe.rename(columns={"network_provider_value": "current_network_provider"}, inplace=True)
                    if "network_provider_upload" in dataframe.columns:
                        dataframe.rename(columns={"network_provider_upload": "network_provider_at_upload"}, inplace=True)

                if "station_id_upload" in dataframe.columns:
                    dataframe.rename(columns={"station_id_upload": "station_id"}, inplace=True)

                # used to set return obj field
                is_data_present = True

            else:
                # used to set return obj field
                is_data_present = False

            # used by the FE, needed in this specific format
            # "data" and "is_data_present" is an obj attribute
            json_output = {
                "data": dataframe.to_dict(orient="records"),
                "is_data_present": is_data_present,
            }

        except (
            EvChartFeatureStoreConnectionError,
            EvChartAuthorizationTokenInvalidError,
            EvChartUserNotAuthorizedError,
            EvChartDatabaseAuroraQueryError,
            EvChartMissingOrMalformedHeadersError,
            EvChartJsonOutputError,
        ) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message="APIDownloadModuleData successfully invoked.", status_code=200
            )

            return_obj = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
            }

            # check for FT AND if there was data returned by api
            if (
                Feature.PRESIGNED_URL in feature_toggle_set
                and is_data_present
            ):
                presigned_url = generate_presigned_url(
                    file={
                        "data": dataframe.to_csv(index=False),
                        "name": "data.csv",
                    },
                    transfer_type="download",
                )
                return_obj["body"] = json.dumps(presigned_url, default=str)

            else:
                return_obj["body"] = json.dumps(json_output, default=str)

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


def get_sr_information(cursor, dataframe):
    """
    Grab the subrecipient informatino in the case of Module 1 (station registration) being
    downloaded.
    """
    # This will need to be updated for N_TIER_ORGANIZATIONS
    max_sr = 0
    for station_index, station in dataframe.iterrows():
        auths_dataframe = execute_query_df(
            query=f"""
                SELECT * FROM {station_authorizations}
                WHERE station_uuid = %s
            """,
            data=station["station_uuid"],
            cursor=cursor,
            message="APIDownloadModuleData",
        )
        num_sr = len(auths_dataframe)

        if num_sr > max_sr:
            for i in range(max_sr, num_sr):
                dataframe[f"authorized_subrecipient_{i + 1}_id"] = None

            max_sr = num_sr

        for auth_index, auth in auths_dataframe.iterrows():
            dataframe.loc[
                station_index,
                f"authorized_subrecipient_{auth_index + 1}_id"
            ] = get_org_info_dynamo(auth["sr_id"]).get("org_friendly_id")


def get_port_information(cursor, dataframe):
    """
    Grab the port information in the case of Module 1 (station registration) being downloaded.
    """
    max_ports = 0

    for station_index, station in dataframe.iterrows():
        station = station.fillna(0)
        num_ports = int(station["num_fed_funded_ports"] + station["num_non_fed_funded_ports"])

        if num_ports > max_ports:
            for i in range(max_ports, num_ports):
                dataframe[f"port_{i + 1}_id"] = None
                dataframe[f"port_{i + 1}_federally_funded"] = None
                dataframe[f"port_{i + 1}_type"] = None

            max_ports = num_ports

        port_dataframe = execute_query_df(
            query=f"""
                SELECT * FROM {station_ports}
                WHERE station_uuid = %s
            """,
            data=station["station_uuid"],
            cursor=cursor,
            message="APIDownloadModuleData",
        )

        for port_index, port in port_dataframe.iterrows():
            dataframe.loc[station_index, f"port_{port_index + 1}_id"] = port["port_id"]
            dataframe.loc[station_index, f"port_{port_index + 1}_federally_funded"] = {
                0: "FALSE",
                1: "TRUE"
            }.get(port["federally_funded"], "")
            dataframe.loc[station_index, f"port_{port_index + 1}_type"] = port["port_type"]


def get_formatted_fields_from_event(json_event, feature_toggle_set):
    """
    Converts query string parameters that were passed in from json to workable datatype list
    """
    try:
        # extracts object from queryStringParameters
        request_fields = {}
        for key, val in json_event.items():
            request_fields[key] = json.loads(val)

        # if param was not passed in by FE then we assume user clicked select all, so we set dict
        # value to -1

        req_data = [
            "modules",
            "years",
            "quarters",
            "network_providers",
            "drs",
            "srs",
            "stations",
        ]

        if Feature.REGISTER_NON_FED_FUNDED_STATION in feature_toggle_set:
            req_data.append("federal_funding_status")

        for item in req_data:
            if item not in request_fields:
                request_fields[item] = [DEFAULT_VALUE]

            # setting the default value to federal_funding_status when the field has both boolean options selected
            if Feature.REGISTER_NON_FED_FUNDED_STATION in feature_toggle_set and item == "federal_funding_status":
                if "0" in request_fields["federal_funding_status"] and "1" in request_fields["federal_funding_status"]:
                    request_fields["federal_funding_status"] = [DEFAULT_VALUE]

        return request_fields

    except Exception as e:
        raise EvChartMissingOrMalformedHeadersError(
            message=(
                "Error thrown in get_fromatted_fields_from_event(). "
                f"Issue formatting data given by the FE for query: {e}"
            )
        ) from e


def validate_recipient_type(token):
    """
    Checks if user has a valid recipient_type
    """
    valid_recipient_types = ["joet", "direct-recipient"]
    recipient_type = token.get("recipient_type")
    if recipient_type.lower() not in valid_recipient_types:
        raise EvChartUserNotAuthorizedError(
            message="Error thrown in validate_recipient_type(). User not authorized to download."
        )


def validate_fields(body, cursor, feature_toggle_set):
    """
    Helper method for validating that whatever data is required to run the SQL call is present
    """
    expected_fields = ["modules", "quarters", "network_providers", "drs", "srs", "stations", "years"]
    expected_fields.append("federal_funding_status") if Feature.REGISTER_NON_FED_FUNDED_STATION in feature_toggle_set else None
    provided_fields = body.keys()

    unknown_fields = set(provided_fields) - set(expected_fields)
    if unknown_fields:
        raise EvChartMissingOrMalformedHeadersError(
                message=f"Unknown fields provided in body: {unknown_fields}"
            )

    for item in body["modules"]:
        if item not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            raise EvChartMissingOrMalformedHeadersError(
                message=f"Improper data in modules: {item}"
            )

    for item in body["quarters"]:
        if item not in ["-1", "1", "2", "3", "4"]:
            raise EvChartMissingOrMalformedHeadersError(
                message=f"Improper data in quarter: {item}"
            )

    if Feature.REGISTER_NON_FED_FUNDED_STATION in feature_toggle_set:
        for item in body["federal_funding_status"]:
            if item not in ["1", "0", DEFAULT_VALUE]:
                raise EvChartMissingOrMalformedHeadersError(
                        message=f"Improper data in federal funding status: {item}"
                    )

    for item in body["network_providers"]:
        if item != "-1":
            # verify passed in np against nps in database
            db_network_providers = get_network_providers_from_db(cursor, feature_toggle_set)
            if item not in db_network_providers:
                raise EvChartMissingOrMalformedHeadersError(
                    message=f"Improper data in network providers: {item}"
                )

    try:
        for item in body["drs"]:
            if item != "-1":
                uuid.UUID(str(item))
        for item in body["srs"]:
            if item != "-1":
                uuid.UUID(str(item))
        for item in body["stations"]:
            if item != "-1":
                uuid.UUID(str(item))

    except ValueError as e:
        raise EvChartMissingOrMalformedHeadersError(
            message=f"Invalid uuid in body: {e}"
        ) from e
    try:
        for item in body["years"]:
            if item != "-1":
                datetime(year=int(item), month=1, day=1)
    except ValueError as e:
        raise EvChartMissingOrMalformedHeadersError(
            message=f"Invalid year in body: {e}"
        ) from e

    return True


def get_network_providers_from_db(cursor, feature_toggle_set):
    """
    Returns a list of network_provider_values from the database
    """
    if Feature.QUERY_DOWNLOAD_REFACTOR in feature_toggle_set:
        query = f"SELECT network_provider_uuid FROM {network_providers}"
    else:
        query = f"SELECT network_provider_value FROM {network_providers}"

    cursor.execute(query)
    rows = cursor.fetchall()
    network_providers_arr = [row[0] for row in rows]
    return network_providers_arr


def statement_builder(feature_toggle_set):
    return "call ev_chart_download_modules2(%s,%s,%s,%s,%s,%s,%s)"


def get_stored_proc_data(request_fields):
    """
    Putting the keys from request field as keys into new stored_procedure_parameters
    and assigning values to None
    """
    stored_procedure_parameters = request_fields.fromkeys(request_fields.keys(), None)
    db_table_map = {
        "1": "station_registrations",
        "2": "module2_data_v3",
        "3": "module3_data_v3",
        "4": "module4_data_v3",
        "5": "module5_data_v3",
        "6": "module6_data_v3",
        "7": "module7_data_v3",
        "8": "module8_data_v3",
        "9": "module9_data_v3",
    }

    # formats the data from request_fields
    for key,val in request_fields.items():
        if key == "modules":
            stored_procedure_parameters[key] = db_table_map[val[0]]
        elif val[0] == "-1":
            stored_procedure_parameters[key] = "-1"
        else:
            stored_procedure_parameters[key] = ", ".join(f"'{data}'" for data in request_fields.get(key))

    # has to be returned in this order because that is the order of the parameters for the stored proc
    #  modules,years,quarters,network_providers,stations,drs,srs
    data = (
        stored_procedure_parameters.get("modules"),
        stored_procedure_parameters.get("years"),
        stored_procedure_parameters.get("quarters"),
        stored_procedure_parameters.get("network_providers"),
        stored_procedure_parameters.get("stations"),
        stored_procedure_parameters.get("drs"),
        stored_procedure_parameters.get("srs")
    )
    return data


def format_dataframe_uuid(dataframe, col_name, recipient_type):
    """
    Helper function that makes 1 db call to get a specific recipient type and maps it to the
    corresponding org_id
    """
    dynamodb = boto3_manager.resource("dynamodb")

    try:
        table = dynamodb.Table("ev-chart_org")
        response = table.query(
            IndexName="gsi_recipient_type",
            KeyConditionExpression=Key("recipient_type").eq(recipient_type),
        )
        items = response["Items"]
        uuid_mapping = pd.DataFrame(items)
        dataframe.rename(columns={col_name: "org_id"}, inplace=True)
        dataframe = dataframe.merge(
            uuid_mapping[["org_id", "org_friendly_id"]], on="org_id", how="left"
        )
        dataframe = dataframe.drop(columns=["org_id"])
        dataframe.rename(columns={"org_friendly_id": col_name}, inplace=True)
        # Resultant NaNs are causing issues in React
        dataframe = dataframe.replace(float("nan"), None)
        return dataframe

    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(
            message=f"Could not get drs from dynamo table: {e}"
        ) from e


def format_dataframe_module(dataframe):
    """
    Helper function that formats module column and maps table name to module id
    """
    try:
        module_name_to_id = {
            "station_registrations": "1",
            "module2_data_v3": "2",
            "module3_data_v3": "3",
            "module4_data_v3": "4",
            "module5_data_v3": "5",
            "module6_data_v3": "6",
            "module7_data_v3": "7",
            "module8_data_v3": "8",
            "module9_data_v3": "9",
        }

        dataframe["module"] = dataframe["module"].apply(lambda x: module_name_to_id[x])
        return dataframe
    except Exception as e:
        raise EvChartJsonOutputError(
            message=f"Error in format_dataframe_module(),error formatting table name to module id: {e}"
        ) from e


# TODO figure out if you want to use module data tables & central config
def get_table_name_from_module_num(module_num):
    """
    Returns db table name depending on the module number that was passed in
    """
    module_id_to_table = {
            "1": "station_registrations",
            "2": "module2_data_v3",
            "3": "module3_data_v3",
            "4": "module4_data_v3",
            "5": "module5_data_v3",
            "6": "module6_data_v3",
            "7": "module7_data_v3",
            "8": "module8_data_v3",
            "9": "module9_data_v3",
        }
    table_name = module_id_to_table.get(module_num)
    return table_name


def get_query_and_data(filters, request_fields, feature_toggle_set):
    """
    Returns a dictionary with the correct query and data values needed to execute the sql statement.
    Primarily checks if the user has specified in the request_fields if they are querying
    for specific srs, drs, or if they are doing a general query with default values and returns the
    sql statement and data values that satisfies the criteria
    """
    config = DatabaseCentralConfig()
    query_and_data = {}
    module_id = request_fields["modules"][0]
    sr_specified_in_request_field = bool(request_fields["srs"][0] != DEFAULT_VALUE)

    # setting the data field
    data_for_dr_or_default_selected = filters["network_providers"] + filters["stations"] + filters["drs"]
    data_for_sr_selected = data_for_dr_or_default_selected + filters["srs"]

    # setting the query field
    # if mod 1 selected
    if module_id == "1":
        # sr selected
        if sr_specified_in_request_field:
            query_and_data["query"] = station_registration_query_builder_for_sr_selected(filters)
            query_and_data["data"] = data_for_sr_selected
        # default or dr selected
        else:
            query_and_data["query"] = station_registration_query_builder_for_dr_selected_or_default(filters)
            query_and_data["data"] = data_for_dr_or_default_selected

    # setting up the annual, one-time, quarterly ids
    if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        one_time_module_ids = config.onetime_module_ids()
        annual_module_ids = config.annual_module_ids()
        quarterly_module_ids = config.quarterly_module_ids()
    else:
        one_time_module_ids =  ["6", "8", "9"]
        annual_module_ids = ["5", "7"]
        quarterly_module_ids = ["2", "3", "4"]

    # if one time modules selected
    if module_id in one_time_module_ids:
        # sr selected
        if sr_specified_in_request_field:
            query_and_data["query"] = one_time_query_builder_for_sr_selected(filters)
            query_and_data["data"] = data_for_sr_selected
        # dr or default selected
        else:
            query_and_data["query"] = one_time_query_builder_for_dr_or_default_selected(filters)
            query_and_data["data"] = data_for_dr_or_default_selected

    # if annual modules selected
    if module_id in annual_module_ids:
        # sr selected
        if sr_specified_in_request_field:
            query_and_data["query"] = annual_query_builder_for_sr_selected(filters)
            query_and_data["data"] = data_for_sr_selected + filters["years"]
        # dr or default selected
        else:
            query_and_data["query"] = annual_query_builder_for_dr_or_default_selected(filters)
            query_and_data["data"] = data_for_dr_or_default_selected + filters["years"]

    # if quarterly modules selected
    if module_id in quarterly_module_ids:
        # sr selected
        if sr_specified_in_request_field:
            query_and_data["query"] = quarter_query_builder_for_sr_selected(filters)
            query_and_data["data"] = data_for_sr_selected + filters["years"] + filters["quarters"]
        # dr or default selected
        else:
            query_and_data["query"] = quarter_query_builder_for_dr_or_default_selected(filters)
            query_and_data["data"] = data_for_dr_or_default_selected + filters["years"] + filters["quarters"]

    # adding the sql statement to filter for federal or non federally funded stations
    if Feature.REGISTER_NON_FED_FUNDED_STATION in feature_toggle_set and DEFAULT_VALUE not in filters["federal_funding_status"]:
        federal_status_filter_statement = " "
        # add federal filter
        if "1" in filters["federal_funding_status"]:
            federal_status_filter_statement = get_fed_funded_filter("sr", "sp")

        # add non_fed filter
        if "0" in filters["federal_funding_status"]:
            federal_status_filter_statement = get_non_fed_funded_filter("sr", "sp")

        query_and_data["query"] += federal_status_filter_statement

    return query_and_data


def get_query_filters(token, cursor, request_fields, feature_toggle_set):
    """
    Queries the database to get info from fields like column_names, quarters, years, uuids depending
    on the request_fields passed in by the user. Returns a dictionary containing the different fields
    as the keys, and the data of each field as the values. This dictionary will be used as
    parameterized data when executing the sql query
    """
    # sets other names that will be referenced when building sql query
    filters = {}
    filters["table_name"] = get_table_name_from_module_num(request_fields["modules"][0])
    filters["modules"] = request_fields["modules"][0]
    filters["column_names"] = get_column_names(cursor, filters, request_fields, feature_toggle_set)

    if request_fields["quarters"][0] == DEFAULT_VALUE:
        filters["quarters"] = ["1", "2", "3", "4"]
    else:
        filters["quarters"] = request_fields["quarters"]

    if request_fields["years"][0] == DEFAULT_VALUE:
        todays_date = datetime.now(timezone.utc).date()
        filters["years"] = get_available_years(todays_date)
    else:
        filters["years"] = request_fields["years"]

    if request_fields["network_providers"][0] == DEFAULT_VALUE:
        filters["network_providers"] = get_all_network_provider_uuids(cursor)
    else:
        filters["network_providers"] = request_fields["network_providers"]

    if Feature.REGISTER_NON_FED_FUNDED_STATION in feature_toggle_set:
        filters["federal_funding_status"] = request_fields["federal_funding_status"]

    # handles case where DR is calling api
    if token.get("recipient_type").lower == "direct-recipient":
        filters["drs"] = token.get("org_id")

    # handles case where JOET is calling api
    else:
        if request_fields["drs"][0] == DEFAULT_VALUE:
            org_info_arr = get_orgs_by_recipient_type_dynamo("direct-recipient")
            filters["drs"] = [org_info["org_id"] for org_info in org_info_arr]
        else:
            filters["drs"] = request_fields["drs"]

    if request_fields["srs"][0] == DEFAULT_VALUE:
        org_info_arr = get_orgs_by_recipient_type_dynamo("sub-recipient")
        filters["srs"] = [org_info["org_id"] for org_info in org_info_arr]
    else:
        filters["srs"] = request_fields["srs"]

    if request_fields["stations"][0] == DEFAULT_VALUE:
        filters["stations"] = get_all_station_uuids(cursor, filters["drs"])
    else:
        filters["stations"] = request_fields["stations"]

    return filters


def get_all_network_provider_uuids(cursor):
    """
    Returns all the network providers present in network provider table
    """
    query = f"SELECT DISTINCT network_provider_uuid FROM {network_providers}"
    cursor.execute(query, None)
    result = [row[0] for row in cursor.fetchall()]
    return result


def get_all_station_uuids(cursor, drs):
    """
    Returns all station uuids from station registration table given an array of dr uuids
    """
    query = f"SELECT DISTINCT station_uuid FROM {station_registrations} WHERE dr_id IN ({', '.join(['%s'] * len(drs))})"
    cursor.execute(query, drs)
    result = [row[0] for row in cursor.fetchall()]
    return result


def get_column_names(cursor, filters, request_fields, feature_toggle_set):
    """
    Returns all database column names for the specific module in the request_fields
    """
    module_id = request_fields["modules"][0]
    module_ids_that_allow_nulls = ["4", "3", "2", "5", "9"]
    # gets column names from station registration table
    if module_id == "1":
        get_column_names_query = """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = %s
        """
        cursor.execute(get_column_names_query, (filters["table_name"],))
        column_names = [row[0] for row in cursor.fetchall()]

    # gets column names from config file
    elif Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        config = DatabaseCentralConfig()
        grid_headers = config.module_grid_display_headers(module_id)
        column_names = grid_headers['left_grid_headers'] + grid_headers['right_grid_headers']
        # TODO: add user_reports_no_data as a central config right header when async biz magic module FT is removed
        if module_id in module_ids_that_allow_nulls:
            column_names.append("user_reports_no_data")

    # gets column names from module enums
    else:
        column_names = get_db_col_names_arr(int(module_id))
        # TODO: add user_reports_no_data as a central config right header when async biz magic module FT is removed
        if module_id in module_ids_that_allow_nulls:
            column_names.append("user_reports_no_data")

    return column_names


def station_registration_query_builder_for_dr_selected_or_default(filters):
    """
    Returns query to retrieve module 1 station data when drs were selected or default values were used
    """
    formatted_column_names = [f"md.{column}" for column in filters["column_names"]]
    statement = f"""
        SELECT DISTINCT np.network_provider_value, {', '.join(formatted_column_names)}
        FROM {filters["table_name"]} md
        INNER JOIN {station_registrations} sr ON sr.station_uuid = md.station_uuid
        INNER JOIN {station_ports} sp ON sr.station_uuid = sp.station_uuid
        INNER JOIN {network_providers} np ON sr.network_provider_uuid = np.network_provider_uuid
        WHERE md.network_provider_uuid IN ({', '.join(['%s'] * len(filters["network_providers"]))})
        AND md.station_uuid IN ({', '.join(['%s'] * len(filters["stations"]))})
        AND sr.dr_id IN ({', '.join(['%s'] * len(filters["drs"]))})
        AND md.status = 'Active'
    """


    return statement


def station_registration_query_builder_for_sr_selected(filters):
    """
    Returns the query to retreive module 1 station data when specific srs were selected
    """
    formatted_column_names = [f"md.{column}" for column in filters["column_names"]]
    statement = f"""
        SELECT DISTINCT sa.sr_id, np.network_provider_value, {', '.join(formatted_column_names)}
        FROM {filters["table_name"]} md
        INNER JOIN {station_registrations} sr ON sr.station_uuid = md.station_uuid
        INNER JOIN {station_ports} sp ON sr.station_uuid = sp.station_uuid
        INNER JOIN {network_providers} np ON sr.network_provider_uuid = np.network_provider_uuid
        INNER JOIN {station_authorizations} sa ON (sa.station_uuid = md.station_uuid and sa.dr_id = md.dr_id)
        WHERE md.network_provider_uuid IN ({', '.join(['%s'] * len(filters["network_providers"]))})
        AND sa.station_uuid IN ({', '.join(['%s'] * len(filters["stations"]))})
        AND sa.dr_id IN ({', '.join(['%s'] * len(filters["drs"]))})
        AND sa.sr_id IN ({', '.join(['%s'] * len(filters["srs"]))})
        AND md.status = 'Active'
    """
    return statement


def one_time_query_builder_for_dr_or_default_selected(filters):
    """
    Returns the query to retreive module 6,8,9 station data when drs were selected or default values were used
    """
    formatted_column_names = [f"md.{column}" for column in filters["column_names"]]
    statement = f"""
        SELECT DISTINCT im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value, {', '.join(formatted_column_names)}
        FROM {filters["table_name"]} md
        INNER JOIN {import_metadata} im ON md.upload_id = im.upload_id
        INNER JOIN {station_registrations} sr ON sr.station_uuid = md.station_uuid
        INNER JOIN {station_ports} sp ON sr.station_uuid = sp.station_uuid
        INNER JOIN {network_providers} np ON sr.network_provider_uuid = np.network_provider_uuid
        WHERE md.network_provider_uuid IN ({', '.join(['%s'] * len(filters["network_providers"]))})
        AND md.station_uuid IN ({', '.join(['%s'] * len(filters["stations"]))})
        AND im.parent_org IN ({', '.join(['%s'] * len(filters["drs"]))})
        AND (im.submission_status = 'Submitted' OR im.submission_status = 'Approved')
    """
    return statement


def one_time_query_builder_for_sr_selected(filters):
    """
    Returns the query to retreive module 6,8,9 station data when specific srs were selected
    """
    formatted_column_names = [f"md.{column}" for column in filters["column_names"]]
    statement = f"""
        SELECT DISTINCT im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value, {', '.join(formatted_column_names)}
        FROM {filters["table_name"]} md
        INNER JOIN {import_metadata} im ON md.upload_id = im.upload_id
        INNER JOIN {station_registrations} sr ON sr.station_uuid = md.station_uuid
        INNER JOIN {station_ports} sp ON sr.station_uuid = sp.station_uuid
        INNER JOIN {network_providers} np ON sr.network_provider_uuid = np.network_provider_uuid
        WHERE md.network_provider_uuid IN ({', '.join(['%s'] * len(filters["network_providers"]))})
        AND md.station_uuid IN ({', '.join(['%s'] * len(filters["stations"]))})
        AND im.parent_org IN ({', '.join(['%s'] * len(filters["drs"]))})
        AND im.org_id IN ({', '.join(['%s'] * len(filters["srs"]))})
        AND im.submission_status='Approved'
    """
    return statement


# TODO parameterize other tables?
def annual_query_builder_for_dr_or_default_selected(filters):
    """
    Returns the query to retreive module 5,7 station data when drs were selected or default values were used
    """
    formatted_column_names = [f"md.{column}" for column in filters["column_names"]]
    statement = f"""
        SELECT DISTINCT im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value, {', '.join(formatted_column_names)}
        FROM {filters["table_name"]} md
        INNER JOIN {station_registrations} sr ON sr.station_uuid = md.station_uuid
        INNER JOIN {station_ports} sp ON sr.station_uuid = sp.station_uuid
        INNER JOIN {network_providers} np ON sr.network_provider_uuid = np.network_provider_uuid
        INNER JOIN {import_metadata} im ON md.upload_id = im.upload_id
        WHERE md.network_provider_uuid IN ({', '.join(['%s'] * len(filters["network_providers"]))})
        AND md.station_uuid IN ({', '.join(['%s'] * len(filters["stations"]))})
        AND im.parent_org IN ({', '.join(['%s'] * len(filters["drs"]))})
        AND year IN ({', '.join(['%s'] * len(filters["years"]))})
        AND (im.submission_status = 'Submitted' OR im.submission_status = 'Approved')
	"""
    return statement


def annual_query_builder_for_sr_selected(filters):
    """
    Returns the query to retreive module 5,7 station data when drs were selected or default values were used
    """
    formatted_column_names = [f"md.{column}" for column in filters["column_names"]]
    statement = f"""
        SELECT DISTINCT im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value, {', '.join(formatted_column_names)}
        FROM {filters["table_name"]} md
        INNER JOIN {import_metadata} im ON md.upload_id = im.upload_id
        INNER JOIN {station_registrations} sr ON sr.station_uuid = md.station_uuid
        INNER JOIN {station_ports} sp ON sr.station_uuid = sp.station_uuid
        INNER JOIN {network_providers} np ON sr.network_provider_uuid = np.network_provider_uuid
        WHERE md.network_provider_uuid IN ({', '.join(['%s'] * len(filters["network_providers"]))})
        AND md.station_uuid IN ({', '.join(['%s'] * len(filters["stations"]))})
        AND im.parent_org IN ({', '.join(['%s'] * len(filters["drs"]))})
        AND im.org_id IN ({', '.join(['%s'] * len(filters["srs"]))})
        AND year IN ({', '.join(['%s'] * len(filters["years"]))})
        AND im.submission_status='Approved'
	"""
    return statement


def quarter_query_builder_for_dr_or_default_selected(filters):
    """
    Returns the query to retreive module 2,3,4 station data when drs were selected or default values were used
    """
    formatted_column_names = [f"md.{column}" for column in filters["column_names"]]
    statement = f"""
        SELECT DISTINCT im.parent_org AS dr_id, im.org_id AS sr_id,year,quarter,np.network_provider_value, {', '.join(formatted_column_names)}
        FROM {filters["table_name"]} md
        INNER JOIN {import_metadata} im ON md.upload_id = im.upload_id
        INNER JOIN {station_registrations} sr on sr.station_uuid = md.station_uuid
        INNER JOIN {station_ports} sp ON sr.station_uuid = sp.station_uuid
        INNER JOIN {network_providers} np on sr.network_provider_uuid = np.network_provider_uuid
        WHERE md.network_provider_uuid IN ({', '.join(['%s'] * len(filters["network_providers"]))})
        AND md.station_uuid IN ({', '.join(['%s'] * len(filters["stations"]))})
        AND im.parent_org IN ({', '.join(['%s'] * len(filters["drs"]))})
        AND year IN ({', '.join(['%s'] * len(filters["years"]))})
        AND quarter IN ({', '.join(['%s'] * len(filters["quarters"]))})
        AND (im.submission_status = 'Submitted' OR im.submission_status = 'Approved')
    """
    return statement


def quarter_query_builder_for_sr_selected(filters):
    """
    Returns the query to retreive module 5,7 station data when drs were selected or default values were used
    """
    formatted_column_names = [f"md.{column}" for column in filters["column_names"]]
    statement = f"""
        SELECT DISTINCT im.parent_org AS dr_id, im.org_id AS sr_id, np.network_provider_value, {', '.join(formatted_column_names)}
        FROM {filters["table_name"]} md
        INNER JOIN {import_metadata} im ON md.upload_id = im.upload_id
        INNER JOIN {station_registrations} sr on sr.station_uuid = md.station_uuid
        INNER JOIN {station_ports} sp ON sr.station_uuid = sp.station_uuid
        INNER JOIN {network_providers} np on sr.network_provider_uuid = np.network_provider_uuid
        WHERE md.network_provider_uuid IN ({', '.join(['%s'] * len(filters["network_providers"]))})
        AND md.station_uuid IN ({', '.join(['%s'] * len(filters["stations"]))})
        AND im.parent_org IN ({', '.join(['%s'] * len(filters["drs"]))})
        AND im.org_id IN ({', '.join(['%s'] * len(filters["srs"]))})
        AND year IN ({', '.join(['%s'] * len(filters["years"]))})
        AND quarter IN ({', '.join(['%s'] * len(filters["quarters"]))})
        AND im.submission_status='Approved'
    """
    return statement
