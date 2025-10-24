"""
module_validation

A helper module that provides functions that aid in common validation processes for module data.
"""
import csv
import json
import logging
import os
import re
import sys
from collections import Counter
from datetime import datetime
from enum import Enum
from pathlib import Path

import awswrangler
import pandas
from database_central_config import DatabaseCentralConfig
from error_report_messages_enum import ErrorReportMessages
from evchart_helper import aurora
from evchart_helper.api_helper import execute_query, get_station_and_port_uuid, get_station_uuid
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseHandlerConnectionError,
    EvChartFileNotFoundError,
    EvChartMissingOrMalformedBodyError,
    EvChartModuleValidationError,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.database_tables import ModuleDataTables
from feature_toggle.feature_enums import Feature
from schema_compliance.authorization_registration import (
    stations_not_active,
    stations_not_authorized,
    stations_not_registered,
    unauthorized_stations_for_dr,
)

import_metadata = ModuleDataTables["Metadata"].value

logger = logging.getLogger("Layer_ModuleValidation")
logger.setLevel(logging.INFO)
# create empty lists to populate with appropriate headers
module_definitions = {}
module_json_object = {}


class ModuleDefinitionEnum(Enum):
    MODULE_1 = 1
    MODULE_2 = 2
    MODULE_3 = 3
    MODULE_4 = 4
    MODULE_5 = 5
    MODULE_6 = 6
    MODULE_7 = 7
    MODULE_8 = 8
    MODULE_9 = 9


def load_module_definitions(
    module_path="/opt/python/module_validation/module_definitions",
):
    try:
        # Path is set for the file structure when deployed as a Lambda layer.
        module_path = Path(module_path)
        module_files = [f for f in os.scandir(module_path) if f.name.endswith(".json")]

        for module_file in module_files:
            with open(module_file, encoding="utf-8") as module_file_raw:
                module_file_json = json.load(module_file_raw)
                module_json_object[module_file_json["module"]] = module_file_json["fields"]

            is_valid_format = all(req_key in module_file_json for req_key in ["fields", "module"])
            if is_valid_format:
                module_key = module_file_json["module"]
                module_definitions[module_key] = {
                    "required_data": [],
                    "recommended_data": [],
                }

                # iterate through data from json, add to appropriate list
                for field in module_file_json["fields"]:
                    if field["required"]:
                        module_definitions[module_key]["required_data"].append(field["field_name"])
                    else:
                        module_definitions[module_key]["recommended_data"].append(
                            field["field_name"]
                        )
    except FileNotFoundError as e:
        raise EvChartFileNotFoundError(message="Error during load_module_definitions") from e


def validate_station_id(
    df, recipient_type, connection, request_headers, feature_toggle_set=frozenset()
):
    try:
        conditions = []
        ids = get_dr_and_sr_ids(recipient_type, request_headers)
        logger.info("ids: %s", ids)
        dr_id, sr_id = ids
        with connection.cursor() as cursor:
            # checking if station_id and network_provider columns are present
            station_id_network_provider_errors = (
                validate_station_id_and_network_provider_column_in_df(df)
            )
            if station_id_network_provider_errors:
                conditions.extend(station_id_network_provider_errors)
            df = set_station_uuid(df, dr_id, cursor, conditions)
            # validating station status
            if not conditions:
                conditions.extend(stations_not_registered(df=df))

                conditions.extend(
                    stations_not_active(
                        cursor=cursor, dr_id=dr_id, df=df, feature_toggle_set=feature_toggle_set
                    )
                )

                if recipient_type == 'direct-recipient':
                    unauthorized_stations = unauthorized_stations_for_dr(cursor, dr_id, df)
                    conditions.extend(unauthorized_stations)

                if sr_id:
                    conditions.extend(
                        stations_not_authorized(cursor=cursor, dr_id=dr_id, sr_id=sr_id, df=df)
                    )
        return conditions
    except EvChartUserNotAuthorizedError as e:
        raise EvChartUserNotAuthorizedError(message="Improper recipient type") from e
    except EvChartDatabaseAuroraQueryError as e:
        raise EvChartModuleValidationError(
            message=f"Unable to validate station id's: {e.message}"
        ) from e
    except Exception as e:
        raise EvChartModuleValidationError(
            message=f"Unable to validate station id's: {repr(e)}"
        ) from e


def get_dr_and_sr_ids(recipient_type, request_headers):
    if recipient_type == "direct-recipient":
        dr_id = request_headers["org_id"]
        sr_id = None
    elif recipient_type == "sub-recipient":
        dr_id = request_headers["parent_org"]
        sr_id = request_headers["org_id"]
    else:
        raise EvChartUserNotAuthorizedError()
    return (dr_id, sr_id)


def validate_station_id_and_network_provider_column_in_df(df):
    conditions = []
    if "station_id" not in df:
        conditions.append(
            {
                "error_row": None,
                "header_name": "station_id",
                "error_description": ErrorReportMessages.MISSING_REQUIRED_COLUMN.format(
                    column_name="station_id"
                ),
            }
        )
    if "network_provider" not in df:
        conditions.append(
            {
                "error_row": None,
                "header_name": "network_provider",
                "error_description": ErrorReportMessages.MISSING_NETWORK_PROVIDER_COLUMN.format(),
            }
        )
    return conditions


def _get_station_uuid(lookup_table, cursor, station_id, dr_id, network_provider=None):
    # Quick lookup table implementation to reduce repeated unnecessary DB calls.
    key_tuple = (station_id, dr_id, network_provider)
    if key_tuple not in lookup_table:
        logger.info("lookup miss for %s; hitting db", str(key_tuple))
        lookup_table[key_tuple] = get_station_uuid(
            cursor, station_id, network_provider
        )

    return lookup_table[key_tuple]


def set_station_uuid(df, dr_id, cursor, conditions=None):
    # TODO: update to add network provider uuid as well
    try:
        # only set the station_uuid columns
        # if the station_id and network_provider fields are present
        if not conditions:
            lookup_table = {}
            df["station_uuid"] = df.apply(
                lambda df: _get_station_uuid(
                    lookup_table, cursor, df["station_id"], dr_id, df["network_provider"]
                ),
                axis=1,
            )
        return df
    except Exception as e:
        message = f"Error setting station_uuid for dr_id {dr_id}: {repr(e)}"
        raise EvChartDatabaseAuroraQueryError(message=message) from e

def set_station_and_port_ids(df: pandas.DataFrame, cursor, conditions=None):
    try:
        if not conditions:
            # test developer calling without port_id
            for index, row in df.iterrows():
                port_id = row.get('port_id')
                station_ids_dict = get_station_and_port_uuid(cursor, row['station_id'], row['network_provider'], port_id)
                df.at[index, 'station_uuid'] = station_ids_dict.get('station_uuid')
                df.at[index, 'network_provider_uuid'] = station_ids_dict.get('network_provider_uuid')

                if port_id:
                    df.at[index, 'port_id_upload'] = port_id
                    df.at[index, 'port_uuid'] = station_ids_dict.get('port_uuid')
        return df
    except Exception as e:
        message = f"Error in set_station_and_port_ids: {repr(e)}"
        raise EvChartDatabaseAuroraQueryError(message=message) from e


def csv_to_dataframe(csv_data):
    try:
        df = pandas.DataFrame(csv_data)
        df.columns = df.loc[0]
        df = df.drop(0)
        # set df.index to match assumption of one-indexed Excel worksheet
        df.index += 1
        return drop_blank_rows(df)
    except Exception as e:
        raise EvChartModuleValidationError(message=f"Unable to convert to dataframe: {e}") from e


def get_dataframe_from_csv(body):
    try:
        raw_data = body.splitlines()
        logging.debug("raw data set: %s", raw_data)

        if not raw_data[0][0].isascii():
            raw_data[0] = raw_data[0][1:]

        return csv_to_dataframe(csv.reader(raw_data))
    except EvChartModuleValidationError as e:
        raise EvChartModuleValidationError(message=f"{e}") from e
    except Exception as e:
        raise EvChartMissingOrMalformedBodyError(message=f"Unable to read csv: {e}") from e


def drop_sample_rows(df):
    drop_df = df.copy()
    if 3 in drop_df.index and all(drop_df.loc[3].T.isin(["Required", "Recommended"])):
        drop_df = drop_df.drop(3)

    if 2 in drop_df.index and all(
        drop_df.loc[2].T.str.match(
            r"String\(|Categorical ?String\(|" r"DateTime|Decimal ?\(|Boolean|Integer\("
        )
    ):
        drop_df = drop_df.drop(2)

    return drop_df


def _get_module_fields_by_number(module_number: int, feature_toggle_set=frozenset()):
    fields = []

    if not isinstance(module_number, int):
        logger.error("Module number must be of type int")
        raise TypeError("Module number must be of type int")
    if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        config = DatabaseCentralConfig()
        fields = config.module_validation(module_number)
    else:
        if module_number in module_json_object:
            fields = module_json_object[module_number]
    if not fields:
        logger.error("Module %s does not exist.", module_number)
        raise ValueError(f"Module {module_number} does not exist.")

    return fields


def _datetime_is_valid(definition, column: pandas.Series, module_number, feature_toggle_set: set):
    field_name = definition.get("field_name")
    required = definition.get("required", False)
    required_empty_allowed = False
    is_nullable = False

    if (
        (Feature.ASYNC_BIZ_MAGIC_MODULE_4 in feature_toggle_set and int(module_number) == 4)
        or (Feature.ASYNC_BIZ_MAGIC_MODULE_2 in feature_toggle_set and int(module_number) == 2)
        or (Feature.ASYNC_BIZ_MAGIC_MODULE_3 in feature_toggle_set and int(module_number) == 3)
        or (Feature.ASYNC_BIZ_MAGIC_MODULE_5 in feature_toggle_set and int(module_number) == 5)
    ):
        required_empty_allowed = definition.get("required_empty_allowed", False)
    elif (Feature.MODULE_5_NULLS in feature_toggle_set and int(module_number) == 5):
        is_nullable = definition.get("is_nullable")
    conditions = []
    notice_conditions = []

    for index, value in column.items():

        if value == "":
            if required:
                if required_empty_allowed:
                    notice_conditions.append(
                        {
                            "error_row": index,
                            "header_name": field_name,
                            "error_description": ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                                column_name=field_name
                            ),
                        }
                    )
                    continue

                conditions.append(
                    {
                        "error_row": index,
                        "header_name": field_name,
                        "error_description": ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                            column_name=field_name
                        ),
                    }
                )
            continue

        if value.lower() == "null":
            if is_nullable:
                continue
        try:
            _ = datetime.fromisoformat(value)
        except ValueError:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.INVALID_TIMESTAMP_FORMAT.format(),
                }
            )
            continue

        # not checking for iso formatting for operational_date field in module 1: station registration
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z?$", value) and int(module_number) != ModuleDefinitionEnum.MODULE_1.value:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.INVALID_TIMESTAMP_FORMAT.format(),
                }
            )

    return (conditions, notice_conditions)


def _string_data_is_valid(
    definition, column: pandas.Series, module_number, feature_toggle_set: set
):
    field_name = definition.get("field_name")
    length = definition.get("length")
    min_length = definition.get("min_length", 1)
    max_length = definition.get("max_length", float("inf"))
    required = definition.get("required", False)
    required_empty_allowed = False
    is_nullable = False

    if (Feature.ASYNC_BIZ_MAGIC_MODULE_2 in feature_toggle_set and int(module_number) == 2) or int(module_number) == 1:
        required_empty_allowed = definition.get("required_empty_allowed", False)
    conditions = []
    notice_conditions = []

    for index, value in column.items():
        # checking 'nan' specifically for module 1 port_uuid field
        if value == "" or (int(module_number) == 1 and value == "nan"):
            if required:
                if required_empty_allowed:
                    notice_conditions.append(
                        {
                            "error_row": index,
                            "header_name": field_name,
                            "error_description": ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                                column_name=field_name
                            ),
                        }
                    )
                    continue

                conditions.append(
                    {
                        "error_row": index,
                        "header_name": field_name,
                        "error_description": ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                            column_name=field_name
                        ),
                    }
                )
            continue
        if value.lower() == "null":
            if is_nullable:
                continue
        if len(value) > max_length:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.MAX_STRING_LENGTH_EXCEEDED.format(),
                }
            )
        if len(value) < min_length:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.MIN_STRING_LENGTH_NOT_MET.format(),
                }
            )
        if length is not None and len(value) != length:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.EXACT_STRING_LENGTH_NOT_MATCHED.format(),
                }
            )
        if required and min_length > 0 and value.isspace():
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.INVALID_WHITESPACE_VALUE.format(),
                }
            )

    return (conditions, notice_conditions)


def _boolean_data_is_valid(
    definition, column: pandas.Series, module_number, feature_toggle_set: set
):
    field_name = definition.get("field_name")
    required = definition.get("required", False)
    required_empty_allowed = False
    is_nullable = False

    if Feature.ASYNC_BIZ_MAGIC_MODULE_9 in feature_toggle_set and int(module_number) == 9:
        required_empty_allowed = definition.get("required_empty_allowed", False)

    conditions = []
    notice_conditions = []

    for index, value in column.items():
        if value == "":
            if required:
                if required_empty_allowed:
                    notice_conditions.append(
                        {
                            "error_row": index,
                            "header_name": field_name,
                            "error_description": ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                                column_name=field_name
                            ),
                        }
                    )
                    continue

                conditions.append(
                    {
                        "error_row": index,
                        "header_name": field_name,
                        "error_description": ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                            column_name=field_name
                        ),
                    }
                )
            continue
        if value.lower() == "null":
            if is_nullable:
                continue

        if value.upper() not in {"TRUE", "FALSE"}:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.INVALID_BOOLEAN_INPUT.format(),
                }
            )

    return (conditions, notice_conditions)


def _integer_data_is_valid(
    definition, column: pandas.Series, module_number, feature_toggle_set: set
):
    field_name = definition.get("field_name")
    min_value = definition.get("min_value", float("-inf"))
    max_value = definition.get("max_value", float("inf"))
    required = definition.get("required", True)
    length = definition.get("length")

    # checking if module 1 is being validated and enabling nulls for ints because the num_fed_funded and num_non_fed_funded field can be null
    if (int(module_number) == ModuleDefinitionEnum.MODULE_1.value):
        required_empty_allowed = definition.get("required_empty_allowed", False)

    conditions = []

    for index, value in column.items():
        if value == "":
            if required:
                conditions.append(
                    {
                        "error_row": index,
                        "header_name": field_name,
                        "error_description": ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                            column_name=field_name
                        ),
                    }
                )
            continue

        if value.lower() == "none" and required_empty_allowed:
            continue
        try:
            _ = int(value)
        except ValueError:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.INVALID_INTEGER_INPUT.format(),
                }
            )
            continue

        if int(value) < min_value:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.MIN_INTEGER_LENGTH_NOT_MET.format(),
                }
            )

        if int(value) > max_value:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.MAX_INTEGER_LENGTH_NOT_MET.format(),
                }
            )

        integer_length = len(value)
        if value[0] in {"-", "+"}:
            integer_length -= 1

        if length and integer_length != length:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.EXACT_INTEGER_LENGTH_NOT_MATCHED.format(),
                }
            )
    return conditions


def get_decimal_part_lengths(value):
    integer_part, _, decimal_part = str(value).partition(".")
    return len(integer_part), len(decimal_part)


def _decimal_data_is_valid(
    decimal_definition, column: pandas.Series, module_number, feature_toggle_set: set
):
    field_name = decimal_definition.get("field_name")
    max_precision = decimal_definition.get("max_precision", 11)
    max_scale = decimal_definition.get("max_scale", 2)
    min_value = decimal_definition.get("min_value", float("-inf"))
    max_value = decimal_definition.get("max_value", float("inf"))
    required = decimal_definition.get("required")
    required_empty_allowed = False
    is_nullable = False


    # both configs use required_empty_allowed
    can_be_nullable = decimal_definition.get("required_empty_allowed", False)

    if (
        (Feature.ASYNC_BIZ_MAGIC_MODULE_4 in feature_toggle_set and int(module_number) == 4)
        or (Feature.ASYNC_BIZ_MAGIC_MODULE_3 in feature_toggle_set and int(module_number) == 3)
        or (Feature.ASYNC_BIZ_MAGIC_MODULE_2 in feature_toggle_set and int(module_number) == 2)
        or (Feature.ASYNC_BIZ_MAGIC_MODULE_5 in feature_toggle_set and int(module_number) == 5)
        or (Feature.ASYNC_BIZ_MAGIC_MODULE_9 in feature_toggle_set and int(module_number) == 9)
    ):
        required_empty_allowed = can_be_nullable
    elif (
        Feature.MODULE_5_NULLS in feature_toggle_set and int(module_number) == 5
    ):
        is_nullable = can_be_nullable
    conditions = []
    notice_conditions = []

    for index, value in column.items():
        if value == "":
            if required:
                if required_empty_allowed:
                    notice_conditions.append(
                        {
                            "error_row": index,
                            "header_name": field_name,
                            "error_description": ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                                column_name=field_name
                            ),
                        }
                    )
                    continue

                conditions.append(
                    {
                        "error_row": index,
                        "header_name": field_name,
                        "error_description": ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                            column_name=field_name
                        ),
                    }
                )
            continue

        if int(module_number) == 5:
            if value.lower() == "null":
                if is_nullable:
                    continue

        try:
            _ = float(value)
        except ValueError:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.INVALID_DECIMAL_INPUT.format(),
                }
            )
            continue

        integer_length, decimal_length = get_decimal_part_lengths(value)

        if value[0] in {"-", "+"}:
            integer_length -= 1

        if integer_length > max_precision - max_scale:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.MAX_DECIMAL_LENGTH_EXCEEDED.format(),
                }
            )
        if decimal_length > max_scale:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.MAX_DECIMAL_PLACES_EXCEEDED.format(),
                }
            )
        if float(value) < min_value:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.MIN_DECIMAL_LENGTH_NOT_MET.format(),
                }
            )
        if float(value) > max_value:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": field_name,
                    "error_description": ErrorReportMessages.MAX_DECIMAL_LENGTH_NOT_MET.format(),
                }
            )

    return (conditions, notice_conditions)


def validated_field(
    definition: dict, data: pandas.Series, module_number, feature_toggle_set=frozenset()
) -> pandas.Series:
    conditions = []
    notice_conditions = []
    converted_data = None
    match str.lower(definition["datatype"]):
        case "decimal":
            conditions, notice_conditions = _decimal_data_is_valid(definition, data, module_number, feature_toggle_set)
            converted_data = pandas.to_numeric(data.copy(), errors="coerce").convert_dtypes()
        case "integer":
            conditions = _integer_data_is_valid(definition, data, module_number, feature_toggle_set)
            converted_data = pandas.to_numeric(data.copy(), errors="coerce").convert_dtypes()
        case "string":
            conditions, notice_conditions = _string_data_is_valid(definition, data, module_number, feature_toggle_set)
            converted_data = data.copy().convert_dtypes()
        case "boolean":
            conditions, notice_conditions = _boolean_data_is_valid(definition, data, module_number, feature_toggle_set)
            converted_data = (
                data.copy().str.upper().map({"TRUE": True, "FALSE": False}).convert_dtypes()
            )
        case "datetime":
            conditions, notice_conditions = _datetime_is_valid(definition, data, module_number, feature_toggle_set)
            converted_data = pandas.to_datetime(
                data.copy(), format="ISO8601", errors="coerce", utc=True
            ).convert_dtypes()
        case _:
            conditions = {
                "error_row": None,
                "field_name": definition["field_name"],
                "error_description": ErrorReportMessages.UNKNOWN_DATATYPE.format(
                    column_name=definition["datatype"]
                ),
            }
            converted_data = data.copy().convert_dtypes()

    return {"conditions": conditions, "converted_data": converted_data, "notice_conditions": notice_conditions}


def drop_blank_rows(df):
    not_blank_index = df.fillna("").apply("".join, axis=1).apply(lambda x: x != "")
    return df[not_blank_index]

def check_df_required_fields(df, module_fields, feature_toggle_set=frozenset()):
    conditions = []
    for field in module_fields:
        if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
            if module_fields[field].get("required", False) and field not in df.columns:
                conditions.append(
                    {
                        "error_description": ErrorReportMessages.MISSING_REQUIRED_COLUMN.format(
                            column_name=field
                        ),
                        "header_name": field,
                        "error_row": None,
                    }
                )

        elif field.get("required", False) and field.get("field_name") not in df.columns:
            conditions.append(
                {
                    "error_description": ErrorReportMessages.MISSING_REQUIRED_COLUMN.format(
                        column_name=field.get("field_name")
                    ),
                    "header_name": field.get("field_name"),
                    "error_row": None,
                }
            )

    if df.empty:
        conditions.append(
            {
                "error_description": ErrorReportMessages.CSV_EMPTY.format(),
                "header_name": "NOT_APPLICABLE",
                "error_row": None,
            }
        )
    return conditions


def check_duplicate_labels(column_label_count, module_number, feature_toggle_set=frozenset()):
    conditions = []
    error = False
    for duplicated_column_label in [c for c in column_label_count if column_label_count[c] > 1]:
        conditions.append(
            {
                "error_description": ErrorReportMessages.DUPLICATE_COLUMN.format(
                    column_name=duplicated_column_label
                ),
                "header_name": duplicated_column_label,
                "error_row": None,
            }
        )

    return {"conditions": conditions, "error": error}


def validated_dataframe(
    module_fields: list,
    module_number: int,
    df: pandas.DataFrame,
    upload_id: str,
    feature_toggle_set=frozenset(),
) -> dict:
    """
        module_fields: list of objects containing field_name, datatype,
                       and additional validation information
        df: payload for the module import in Pandas dataframe format
        feature_toggle_set: feature toggles that are enabled and need to be
            evaluated

    Returns an object with key/value pairs:
        is_compliant (boolean): whether or not df is compliant with
                                the provided list of module_fields
        total_records (int): count of all records found in df
        valid_records (int): count of valid records found in df
        rejected_rcords (int): count of invalid records found in df
        conditions (list of objects): all validation errors found in df
        df: type-converted dataframe

    Condition object key/value pairs:
        error_description (str)
        header_name (str)
        error_row (int for cell-level error, None for column-level error)
    """
    validated_df = pandas.DataFrame().reindex_like(df)
    conditions = check_df_required_fields(df, module_fields, feature_toggle_set)
    logger.info("validated_df: %s", validated_df.to_string())
    column_label_count = Counter(df.columns)
    duplicate_check_status = check_duplicate_labels(
        column_label_count, module_number, feature_toggle_set
    )
    conditions.extend(duplicate_check_status.get("conditions", []))
    if duplicate_check_status.get("error", False):
        return {
            "is_compliant": False,
            "total_records": len(df.index),
            "valid_records": 0,
            "rejected_records": len(df.index),
            "conditions": conditions,
            "df": pandas.DataFrame(),
        }
    validation_not_required = {"station_id", "station_uuid"}

    validation_not_required.add("network_provider")
    logger.debug("validation not required: %s", validation_not_required)

    if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        # adding "field_name" into the definitions dict so that if errors are generated,
        # it will use field_name to get the column name
        definition = module_fields.copy()
        for column_label in module_fields.keys():
            definition[column_label]["field_name"] = column_label
    else:
        definition = {m["field_name"]: m for m in module_fields}
    notice_conditions = []
    for column_label, column_series in df.items():
        if column_label not in definition:
            # station_id and station_uuid are used in
            # registration/authorization validation logic
            # does not need to be separately validated for schema compliance
            if column_label in validation_not_required:
                validated_df[column_label] = column_series
                continue
            conditions.append(
                {
                    "error_description": ErrorReportMessages.UNKNOWN_COLUMN.format(
                        column_name=column_label
                    ),
                    "header_name": column_label,
                    "error_row": None,
                }
            )
            continue

        to_be_validated = column_series

        # validating each field in the module
        response = validated_field(
            definition=definition[column_label],
            data=to_be_validated,
            module_number=module_number,
            feature_toggle_set=feature_toggle_set,
        )
        conditions.extend(response.get("conditions", []))
        notice_conditions.extend(response.get("notice_conditions", []))
        if column_label_count[column_label] == 1:
            validated_df[column_label] = response.get("converted_data")
        else:
            logger.debug("skipping validated_df update of duplicate column: %s", column_label)
        logger.debug("validated data: %s", validated_df[column_label])
    validated_df.drop(["considered_null"], axis=1, errors="ignore", inplace=True)

    if conditions and notice_conditions:
        conditions.extend(notice_conditions)

    records_status = get_validation_records_status(df, upload_id, conditions)
    return {
        "is_compliant": len(conditions) == 0,
        "total_records": records_status["total"],
        "valid_records": records_status["valid"],
        "rejected_records": records_status["rejected"],
        "conditions": conditions,
        "df": validated_df,
    }


def get_validation_records_status(df, upload_id, conditions):
    total_records = len(df.index)
    errow_row_set = {c["error_row"] for c in conditions}
    if errow_row_set == set():
        rejected_records = 0
        valid_records = total_records
        upload_status = "Valid"
    elif None in errow_row_set:
        # an error_row value of None indicates column-level error, such as
        # missing or duplicate.  Consider all rows to be invalid.
        valid_records = 0
        rejected_records = total_records
        upload_status = "Invalid"
    else:
        rejected_records = len(errow_row_set)
        valid_records = total_records - rejected_records
        upload_status = "Invalid"
    metadata_update_validation_status(upload_id, upload_status)
    return {"total": total_records, "rejected": rejected_records, "valid": valid_records}


def validated_dataframe_by_module_id(module_number, df, upload_id, feature_toggle_set=frozenset()):
    return validated_dataframe(
        _get_module_fields_by_number(module_number.value, feature_toggle_set),
        upload_id=upload_id,
        df=df,
        module_number=module_number.value,
        feature_toggle_set=feature_toggle_set,
    )


def metadata_update_validation_status(upload_id, status):
    try:
        connection = aurora.get_connection()
        with connection.cursor() as cursor:
            update_query = f"""
                UPDATE {import_metadata}
                SET submission_status = %(status)s
                WHERE upload_id = "%(upload_id)s"
            """
            execute_query(
                query=update_query,
                data={"upload_id": upload_id, "status": status},
                cursor=cursor,
                message=(
                    "Error thrown in module_validation"
                    ".metadata_update_validation_status on update"
                ),
            )
            connection.commit()
    except Exception as e:
        raise EvChartDatabaseHandlerConnectionError(
            message=(f"Error updating validation status of {upload_id} " f"to {status}: {e}")
        ) from e


def add_upload_suffixes():
    columns_to_rename = {
        "station_id": "station_id_upload",
        "network_provider": "network_provider_upload",
    }
    return columns_to_rename


def upload_data_from_df(
    connection, module_number, df, check_boolean=True, feature_toggle_set=frozenset()
):
    if check_boolean:
        upload_df = adjust_for_booleans(df, module_number, feature_toggle_set).rename(
            columns=add_upload_suffixes()
        )
    else:
        upload_df = df.rename(columns=add_upload_suffixes())
    try:
        # https://aws-sdk-pandas.readthedocs.io/en/stable/stubs/awswrangler.mysql.to_sql.html#awswrangler.mysql.to_sql
        awswrangler.mysql.to_sql(
            df=upload_df,
            table=f"module{module_number}_data_v3",
            schema="evchart_data_v3",
            con=connection,
            use_column_names=True,
        )
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Failed to submit data submission: {e}",
        ) from e


def adjust_for_booleans(df, module_id, feature_toggle_set=frozenset()):
    adjusted_df = df.copy()
    module_fields = _get_module_fields_by_number(int(module_id), feature_toggle_set)
    boolean_fields = [
        m.get("field_name")
        for m in module_fields
        if (m.get("datatype") == "boolean" and m.get("field_name") in df.columns)
    ]

    adjusted_df[boolean_fields] = df[boolean_fields].map(
        lambda bf: {"TRUE": True, "FALSE": False}.get(str(bf).upper())
    )

    return adjusted_df
