"""
module_validation.unique_constraint

Holds functions that evaluate the unique constraints during data validatoin
for all async or S2S module imports.
"""

from database_central_config import DatabaseCentralConfig
from evchart_helper.api_helper import execute_query_df, get_upload_metadata, execute_query
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.module_helper import get_module_id
from feature_toggle.feature_enums import Feature
from error_report_messages_enum import ErrorReportMessages
from module_validation import _get_module_fields_by_number
import pandas

feature_by_module_number = [
    None,
    None,
    Feature.UNIQUE_CONSTRAINT_MODULE_2,
    Feature.UNIQUE_CONSTRAINT_MODULE_3,
    Feature.UNIQUE_CONSTRAINT_MODULE_4,
    Feature.UNIQUE_CONSTRAINT_MODULE_5,
    Feature.UNIQUE_CONSTRAINT_MODULE_6,
    Feature.UNIQUE_CONSTRAINT_MODULE_7,
    Feature.UNIQUE_CONSTRAINT_MODULE_8,
    Feature.UNIQUE_CONSTRAINT_MODULE_9,
]
metadata_table = ModuleDataTables["Metadata"].value


def get_module_constraints_by_module_id(module_id):
    """
    Returns a list of constraints given a module id
    """
    constraints = {
        "2": ["station_uuid", "port_id", "session_id"],
        "3": ["station_uuid", "port_id", "uptime_reporting_start", "uptime_reporting_end"],
        "4": ["station_uuid", "outage_id", "port_id"],
        "5": ["station_uuid", "maintenance_report_start"],
        "6": ["station_uuid", "operator_name"],
        "7": ["station_uuid", "program_report_year"],
        "8": ["station_uuid", "der_type"],
        "9": ["station_uuid"],
    }
    return constraints[module_id]


# this query is called in apiPutSubmitModuleData to check for duplicates upon module submission, however, i don't think
# this query covers all circumstances, ex: will throw duplicate error for quarterly mdoules submitted in diff years
def query_builder_module_details(source_table):
    """
    Returns the SQL query that queries for module data of an upload_id from the
    passed in desired table or metadata_table
    """
    module_query = (
        f"SELECT * FROM {source_table} "
        f"WHERE upload_id = %s "
        f"OR upload_id IN ( "
        f"  SELECT upload_id from {metadata_table} "
        f"  WHERE module_id=%s "
        f"  AND submission_status IN ('Pending', 'Submitted', 'Approved') "
        f"  AND parent_org = %s "
        f")"
    )

    return module_query


def get_duplicates_query_builder(
    module_id, constraint_columns, df_number_of_rows, is_null_data=False
):
    """
    Creates query to check for duplicates for module 4 data
    """
    source_table = ModuleDataTables[f"Module{module_id}"].value

    quarterly_and_annual_filters = ""
    # TODO: get modules correctly
    quarterly_and_annual_module_ids = ["2", "3", "4", "5"]
    if is_null_data and module_id in quarterly_and_annual_module_ids:
        quarterly_and_annual_filters = " AND year=%s AND quarter=%s "

    column_str = ", ".join(constraint_columns)
    values_placeholder = ", ".join(["%s"] * len(constraint_columns))
    in_clause = ", ".join(["(" + values_placeholder + ")"] * df_number_of_rows)

    module_query = f"""
        SELECT DISTINCT {column_str}, upload_id, station_id_upload FROM {source_table}
        WHERE upload_id = %s
        OR upload_id IN (
            SELECT upload_id FROM {metadata_table}
            WHERE module_id=%s
            AND submission_status IN ('Pending', 'Submitted', 'Approved')
            AND parent_org=%s
            {quarterly_and_annual_filters}
        )
        AND ({column_str}) IN({in_clause})
    """
    return module_query


def get_constraints_conditions(log_event, submission_upload_id, constraints):
    """
    Returns a list of error objects regarding duplicate records found within the system
    or within the upload, given a log event, submission_upload, and module constraints
    """
    conditions = []
    constraint_names = constraints.index.names
    for constraint_values, constraint_violation_upload_ids in constraints.items():
        conflict_details = [
            f"{field.removesuffix('_upload')}={value}"
            for field, value in zip(constraint_names, constraint_values)
            if field != "station_uuid"
        ]

        other_upload_ids = constraint_violation_upload_ids - {submission_upload_id}

        if other_upload_ids == set():
            conditions.append(
                {
                    "error_description": ErrorReportMessages.DUPLICATE_RECORD_IN_SAME_UPLOAD.format(
                        fields=conflict_details
                    ),
                    "header_name": "N/A",
                    "error_row": None,
                }
            )
        else:
            if submission_upload_id in constraint_violation_upload_ids:
                conditions.append(
                    {
                        "error_description": ErrorReportMessages.DUPLICATE_RECORD_IN_SYSTEM.format(
                            upload_id=other_upload_ids, fields=conflict_details
                        ),
                        "header_name": "N/A",
                        "error_row": None,
                    }
                )
            else:
                log_event.log_custom_exception(
                    message=(
                        "Review the following upload_ids for pre-existing "
                        "unique key constraints: "
                        f"{','.join(constraint_violation_upload_ids)}"
                    ),
                    status_code=200,
                    log_level=4,
                )
    return conditions


def check_constraints_in_data(df, unique_constraint, feature_toggle_set=frozenset()):
    """
    Returns a dataframe with the upload_ids of the uploads that violate unique_constraints,
    if all upload_ids satisfy the unique_constraints, then function returns an empty response
    """
    constraint_df = df.copy()

    extra_merge_fields = ["station_id_upload", "network_provider_upload"]
    # extra_merge_fields = ["station_id_upload"]
    size_df = constraint_df.groupby(unique_constraint).size()
    merge_df = constraint_df.merge(
        size_df.rename("duplicate_count"), left_on=unique_constraint, right_index=True
    )

    return (
        merge_df[merge_df["duplicate_count"] > 1]
        .groupby(unique_constraint + extra_merge_fields)["upload_id"]
        .apply(set)
    )


def unique_constraint_violations(
    cursor, upload_id, dr_id, log_event, feature_toggle_set=frozenset()
):
    """
    Returns a dictionary of an errors list and dataframe that holds the invalid key constraint
    errors. If no errors are found, an empty dictionary is returned
    """
    module_id = get_module_id(cursor=cursor, upload_id=upload_id)
    if feature_by_module_number[int(module_id)] not in feature_toggle_set:
        return {"errors": [], "df": None}

    source_table = ModuleDataTables[f"Module{module_id}"].value
    module_query = query_builder_module_details(source_table)
    module_df = execute_query_df(
        query=module_query, data=(upload_id, module_id, dr_id), cursor=cursor
    )

    if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        config = DatabaseCentralConfig()
        unique_constraint = config.unique_key_constraints(module_id)
    else:
        unique_constraint = get_module_constraints_by_module_id(module_id)

    constraints_found = check_constraints_in_data(
        df=module_df,
        unique_constraint=unique_constraint,
        feature_toggle_set=feature_toggle_set,
    )
    if constraints_found.empty:
        return {"errors": [], "df": module_df}
    errors = get_constraints_conditions(
        log_event=log_event, submission_upload_id=upload_id, constraints=constraints_found
    )
    return {"errors": errors, "df": None}


def unique_constraint_violations_for_async(
    cursor,
    upload_id: str,
    dr_id: str,
    log_event,
    df,
    module_id: str,
    feature_toggle_set: set = frozenset(),
) -> dict:
    """
    Returns a dictionary of an errors list and dataframe that holds the invalid key constraint
    errors for async/s2s. If no errors are found, an empty dictionary is returned
    """
    # pylint: disable=too-many-positional-arguments
    async_df = df.copy()
    async_df.rename({"network_provider": "network_provider_upload"}, axis="columns", inplace=True)
    if feature_by_module_number[int(module_id)] not in feature_toggle_set or async_df.empty:
        return {"errors": [], "df": None}

    if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        config = DatabaseCentralConfig()
        constraints = config.unique_key_constraints(module_id)
        required_empty_allowed_fields = config.required_empty_allowed_fields(int(module_id))
    else:
        constraints = get_module_constraints_by_module_id(module_id)
        required_empty_allowed_fields = set(
            get_requried_and_requried_empty_allowed_fields_from_module_definitions(
                module_id, feature_toggle_set
            )
        )

    constraints.append("network_provider_upload")

    null_duplicates_df = pandas.DataFrame()
    non_null_duplicates_df = pandas.DataFrame()
    duplicate_in_db = pandas.DataFrame()

    # replaces empty strings and null values as NA in the df
    async_df.replace(["", None], pandas.NA, inplace=True, regex=True)

    # filter df between null and non-null unique constraints
    # separating the df will allow us to check against unique constraints for null and non null data
    nullable_constraints = list(set(constraints) & required_empty_allowed_fields)

    df_with_null_data = async_df[
        async_df[nullable_constraints].isnull().all(axis=1)
        | (async_df[nullable_constraints] == "").all(axis=1)
    ]

    df_without_null_data = async_df[
        ~(
            async_df[nullable_constraints].isnull().any(axis=1)
            | (async_df[nullable_constraints] == "").any(axis=1)
        )
    ]

    # query against the db for duplicates
    if not df_with_null_data.empty:
        df_with_null_data = df_with_null_data.copy()
        null_duplicates_df = get_duplicate_within_db(
            cursor, upload_id, dr_id, module_id, constraints, df_with_null_data, is_null_data=True
        )

    if not df_without_null_data.empty:
        df_without_null_data = df_without_null_data.copy()
        non_null_duplicates_df = get_duplicate_within_db(
            cursor,
            upload_id,
            dr_id,
            module_id,
            constraints,
            df_without_null_data,
            is_null_data=False,
        )

    # combining the df to get all duplicates found in the db
    if non_null_duplicates_df.empty:
        duplicate_in_db = null_duplicates_df
    elif null_duplicates_df.empty:
        duplicate_in_db = non_null_duplicates_df
    else:
        duplicate_in_db = pandas.concat(
            [non_null_duplicates_df, null_duplicates_df], ignore_index=False
        )

    try:
        # check for duplicate rows within file, if present, format df into 2 columns: primary keys and upload_id
        duplicate_in_data = get_duplicate_within_df(
            upload_id=upload_id, df=async_df, constraints=constraints
        )

        # check for duplicate rows within db, if present, format df into 2 columns: primary keys and upload_id
        if not duplicate_in_db.empty:
            duplicate_in_db = duplicate_in_db.groupby(constraints + ["station_id_upload"])[
                "upload_id"
            ].apply(set)
            duplicate_in_db = pandas.concat(
                [duplicate_in_db, duplicate_in_data], ignore_index=False
            )
        else:
            duplicate_in_db = duplicate_in_data

    except Exception as e:
        # debug error occuring intermitently during groupby
        message = f"Thrownm in unique_constraint_violations_for_async() \
            Exception: {repr(e)}\nexisting rows headers: {list(duplicate_in_db)}"
        log_event.log_custom_exception(message, 500, 4)
        raise e

    # If rows exist then there were duplicates, add upload id to all rows
    # this is to conform to existing logic
    errors = []
    if not (duplicate_in_db is None or duplicate_in_db.empty):
        duplicate_in_db = duplicate_in_db.apply(lambda x: x | {upload_id})
        errors.extend(
            get_constraints_conditions(
                log_event=log_event, submission_upload_id=upload_id, constraints=duplicate_in_db
            )
        )
    if errors:
        return {"errors": errors, "df": None}
    return {"errors": [], "df": df}


def get_duplicate_within_db(
    cursor, upload_id, dr_id, module_id, constraints, async_df, is_null_data: bool
):
    """
    Returns a dataframe with the duplicates present within the databse. The constraints are updated for the query if the
    current module has key constraints that are allowed to be null due to null ack (currently only for mod 2 & 4)
    These constraints are removed for the query, and then "" are filled in to signify that a null was provided for that
    column. The query also properly checks for duplicates depending on module frequency.
    """
    # have to remove key constraints that are auto generated in the db when querying null modules
    if is_null_data and (module_id == "2" or module_id == "4"):
        system_generated_unique_key_constraints = ["outage_id", "session_id"]
        for key_constraint in system_generated_unique_key_constraints:
            if key_constraint in constraints:
                constraints.remove(key_constraint)

    # TODO: get quarterly and annual module ids correctly
    quarterly_and_annual_module_ids = ["2", "3", "4", "5"]
    quarter = ""
    # replaces empty strings and null values as NA in the df
    async_df.replace(["", None, "(?i)null"], pandas.NA, inplace=True, regex=True)

    # getting metadata values
    upload_metadata = get_upload_metadata(cursor, upload_id)
    year = upload_metadata.get("year")
    quarter = upload_metadata.get("quarter")

    # calling query builder
    df_number_of_rows = len(async_df)
    query = get_duplicates_query_builder(module_id, constraints, df_number_of_rows, is_null_data)

    # preparing query data
    query_values_list = [upload_id, module_id, dr_id]
    # adding in quarterly or annual filters
    if is_null_data and module_id in quarterly_and_annual_module_ids:
        query_values_list.extend([year, quarter])

    # adding in query values from the df
    df_query_values = async_df[constraints].fillna("NULL").values.flatten().tolist()
    query_values_list.extend(df_query_values)
    query_values_tuple = tuple(query_values_list)
    duplicates_from_db = execute_query_df(query=query, data=query_values_tuple, cursor=cursor)

    # updating outage_id (module 4) and session_id (module 2) values to "" for key constraints if null modules
    # and adding these keys back to constraints list so that it can be properly evaluated when creating error mesage
    if is_null_data and module_id == "2":
        duplicates_from_db["session_id"] = ""
        constraints.append("session_id")
    elif is_null_data and module_id == "4":
        duplicates_from_db["outage_id"] = ""
        constraints.append("outage_id")

    return duplicates_from_db


def get_duplicate_within_df(upload_id, constraints, df):
    """
    Convenience function that checks for duplicate rows present in the dataframe.
    This function groups the rows of duplicate data based on its unique constraints
    and the station_id_upload and upload_id and returns the result as a set object.
    """
    duplicates = df[df.duplicated(subset=constraints, keep=False)]
    if len(duplicates) > 0:
        # updating column names and adding in upload_id to match fields returned by get_duplicates_from_db
        # this will allow us to concanetate the results from both functions
        duplicates = duplicates.rename(columns={"station_id": "station_id_upload"})
        duplicates = duplicates.assign(upload_id=upload_id)
        duplicates_grouped = duplicates.groupby(constraints + ["station_id_upload"])[
            "upload_id"
        ].apply(set)
        return duplicates_grouped
    return None


def get_requried_and_requried_empty_allowed_fields_from_module_definitions(
    module_id, feature_toggle_set
):
    """
    Returning the nullable required fields by module_id from module definitions
    """
    required_empty_allowed_fields = []
    module_field_list = _get_module_fields_by_number(int(module_id), feature_toggle_set)
    for field_obj in module_field_list:
        if field_obj.get("required") == True and field_obj.get("required_empty_allowed") == True:
            required_empty_allowed_fields.append(field_obj.get("field_name"))

    return required_empty_allowed_fields
