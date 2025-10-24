"""
evchart_helper.module_helepr

Common helper functions that support multiple module related APIs
"""

from functools import cache
from dateutil import tz
from database_central_config import DatabaseCentralConfig

from evchart_helper.api_helper import (
    execute_query,
    execute_query_fetchone,
    get_org_info_dynamo,
    get_user_info_dynamo,
)
from evchart_helper.module_enums import (
    ModuleFrequencyProper, ModuleNames, get_list_of_boolean_columns
)
from evchart_helper.custom_exceptions import (
    EvChartUserNotAuthorizedError,
    EvChartMissingOrMalformedHeadersError,
    EvChartJsonOutputError,
    EvChartDatabaseDynamoQueryError,
)
from evchart_helper.database_tables import ModuleDataTables
from feature_toggle.feature_enums import Feature
from feature_toggle import feature_enablement_check

import pandas as pd

# pylint: disable=invalid-name
import_metadata = ModuleDataTables.Metadata.value
station_authorizations = ModuleDataTables.StationAuthorizations.value


def validate_headers(upload_id, org_id, recipient_type, cursor):
    """
        Convenience function that verifies the upload_id is vlaid and the
        current organization is authorized to view the data. An error is
        raised if either of these cases fail.
    """
    # checking for malformed upload_id
    error_message = ""
    if not is_valid_upload_id(upload_id, cursor):
        error_message = (
            "Error thrown in validate_headers(). "
            f"Malformed upload_id: {upload_id}"
        )
        raise EvChartMissingOrMalformedHeadersError(message=error_message)

    # checking if current org can view data of upload_id
    if not is_org_authorized_to_view_data(
        upload_id, org_id, recipient_type, cursor
    ):
        error_message = (
            "Error thrown in validate_headers(). "
            f"Current org_id: {org_id} is not permitted to view data "
            f"associated with upload id: {upload_id}"
        )
        raise EvChartUserNotAuthorizedError(message=error_message)

    return True


def get_module_details(upload_id, org_id, recipient_type, cursor, logger=None):
    """
        Returns the module data associated with the given upload_id and org_id
    """
    get_details_query = ""
    module_details = {}
    error_message = "Error thrown in helper function: get_module_details()."

    # DR view
    if recipient_type == "direct-recipient":
        get_details_query = (
            f"SELECT * FROM {import_metadata} "
            "WHERE parent_org=%s and upload_id=%s"
        )
        query_data = (org_id, upload_id)
        module_details = execute_query(
            query=get_details_query,
            data=query_data,
            cursor=cursor,
            message=error_message,
        )

    # SR view
    elif recipient_type == "sub-recipient":
        get_details_query = (
            f"SELECT * FROM {import_metadata} WHERE org_id=%s and upload_id=%s"
        )
        query_data = (org_id, upload_id)
        module_details = execute_query(
            query=get_details_query,
            data=query_data,
            cursor=cursor,
            message=error_message,
        )

    # JO view
    elif recipient_type == "joet":
        get_details_query = \
            f"SELECT * FROM {import_metadata} WHERE upload_id =%s"
        module_details = execute_query(
            query=get_details_query,
            data=(upload_id,),
            cursor=cursor,
            message=error_message,
        )

    # debugging purposes
    if logger and len(module_details) > 0:
        logger.debug("Rows returned from database: %s", module_details)
    elif logger and len(module_details) == 0:
        logger.debug(
            "No module details found for upload_id: %s for the org: %s",
            upload_id,
            org_id
        )

    return module_details


def format_metadata(recipient_type, output):
    """
        Convenience function that updates the given output object with the
        correct formatting needed to display to the user
    """
    for module_details_dict in output:
        # formatting uploaded_on and submitted_on datetime obj
        format_datetime_obj(module_details_dict)

        # formatting direct_recipient
        format_direct_recipient(module_details_dict)

        # formatting module_name
        format_module_name(module_details_dict)

        # formatting module_frequency
        format_module_frequency(module_details_dict)

        # formatting updated_by
        format_fullname_from_email(module_details_dict)

        # formatting sub_recipient for DR and JO view
        if recipient_type != "sub-recipient":
            format_sub_recipient(module_details_dict)

    return output


def is_valid_upload_id(upload_id, cursor):
    """
        Convenience function referenced in validate_headers() that returns
        True or False if upload_id is present in the import_metadata table
    """
    # verifies if upload id exists in database
    get_upload_id_query = (
        f"SELECT upload_id FROM {import_metadata} "
        "WHERE upload_id=%s"
    )
    upload_info = execute_query(
        query=get_upload_id_query,
        data=(upload_id,),
        cursor=cursor,
        message="Error thrown in module_helper is_valid_upload_id(). ",
    )

    if len(upload_info) > 0:
        return True

    return False


def is_org_authorized_to_view_data(upload_id, org_id, recipient_type, cursor):
    """
        Conveniecne function referenced in validate_headers() that returns
        True or False if the current org can view the uploaded data
    """
    module_orgs = get_upload_info(upload_id, cursor)
    module_org_id = module_orgs[0]
    module_parent_org = module_orgs[1]
    submission_status = module_orgs[2]
    error_message = ""

    # Validate DR
    if recipient_type.lower() == "direct-recipient":
        # checks if DR is viewing another DR's data
        if module_parent_org != org_id:
            error_message = (
                "Error thrown in is_org_authorized_to_view_data(). "
                "Current direct recipient is not authorized to view data."
            )

        # checks if DR is viewing SR draft data
        if (
            submission_status.lower() == "draft" and
            module_org_id != module_parent_org
        ):
            error_message = (
                "Error thrown in is_org_authorized_to_view_data()."
                "DR's cannot view SR drafts."
            )

    # Validate SR
    elif recipient_type.lower() == "sub-recipient":
        if module_org_id != org_id:
            error_message = (
                "Error thrown in is_org_authorized_to_view_data(). "
                "SR's cannot view other SR data."
            )

    # Validate JOET
    elif recipient_type.lower() == "joet":
        if submission_status.lower() not in {"submitted", "approved"}:
            error_message = (
                "Error thrown in is_org_authorized_to_view_data(). "
                "JO cannnot view data without submitted or approved status."
            )

    if len(error_message) > 0:
        return False

    return True


# used to get info: org_id, parent_org, submission for the current module
def get_upload_info(upload_id, cursor):
    """
        Convenience function that returns a list of the org_id, parent_org,
        and submission_status of the current upload_id

    """
    get_upload_info_query = f"""
        SELECT m.org_id, m.parent_org, i.submission_status
        FROM {import_metadata} m
        INNER JOIN {import_metadata} i
        ON m.upload_id = i.upload_id
        WHERE m.upload_id=%s
    """

    module_orgs = execute_query_fetchone(
        query=get_upload_info_query,
        data=(upload_id,),
        cursor=cursor,
        message="Error thrown in module_helper get_upload_info(). ",
    )
    return module_orgs


def format_sub_recipient(module_data_dict):
    """
        Convenience function that takes in a dictionary containing module data
        and sets the value of the sub_recipient to either their name or None
        depending on the owner of the module's data
    """
    try:
        org_info = get_org_info_dynamo(module_data_dict["org_id"])
        curr_recipient = org_info.get("recipient_type")
        sr_name = org_info.get("name")
        # if module data was uploaded by a DR, then sub_recipient is set to NA
        if curr_recipient.lower() == "direct-recipient":
            module_data_dict["sub_recipient"] = "N/A"

        # if module data was uploaded by an SR,
        # then sub_recipient is set to the SR name
        elif curr_recipient.lower() == "sub-recipient":
            module_data_dict["sub_recipient"] = sr_name

        return module_data_dict

    except EvChartDatabaseDynamoQueryError as e:
        e.message += " Error thrown in format_sub_recipient()"
        raise e
    except Exception as e:
        error_message = (
            " Error thrown in format_sub_recipient() when formatting "
            f"sub_recipient variable: {e}"
        )
        raise EvChartJsonOutputError(message=error_message) from e


def format_direct_recipient(module_data_dict):
    """
        Convenience function that updates the passed in dictionary and formats
        the module data's direct_recipient
    """
    try:
        org_info = get_org_info_dynamo(module_data_dict["parent_org"])
        dr_name = org_info.get("name")
        module_data_dict["direct_recipient"] = dr_name
        return module_data_dict
    except EvChartDatabaseDynamoQueryError as e:
        e.message += "Error thrown in format_direct_recipient()"
        raise e


def format_module_frequency(module_data_dict):
    """
        Convenience function that updates the passed in dictionary and formats
        the module_frequency for annual, one-time, and quarterly data by
        referencing ModuleFrequencyProper enum
    """
    try:
        module_id = str(module_data_dict["module_id"])
        module_frequency = ModuleFrequencyProper["Module" + module_id].value

        # handles one-time and annual frequency
        if module_frequency.lower() != "quarterly":
            module_data_dict["module_frequency"] = module_frequency

        # handles quarter frequency to display correct quarter
        else:
            quarter_id = module_data_dict["quarter"]

            quarter_types = {
                "1": "Quarter 1 (Jan-Mar)",
                "2": "Quarter 2 (Apr-Jun)",
                "3": "Quarter 3 (Jul-Sep)",
                "4": "Quarter 4 (Oct-Dec)",
            }
            module_data_dict["module_frequency"] = \
                quarter_types.get(quarter_id, "INVALID QUARTER")

        return module_data_dict

    except Exception as e:
        raise EvChartJsonOutputError(
            message=f"Error thrown in format_module_frequency(): {e}"
        ) from e


def format_module_name(module_data_dict):
    """
        Convenience function that updates the passed in dictionary and
        formats the module_name by referencing ModuleNames enum file
    """
    try:
        module_id = str(module_data_dict["module_id"])
        full_mod_id = f"Module{module_id}"

        if "module_name" not in module_data_dict:
            module_name = (
                f"Module {module_id}: "
                f"{ModuleNames[full_mod_id].value}"
            )
            module_data_dict["module_name"] = module_name

        return module_data_dict

    except Exception as e:
        error_message = (
            "Error thrown in format_module_name() when formatting "
            f"module_name from the evchart helper files: {e}"
        )
        raise EvChartJsonOutputError(message=error_message) from e


def format_datetime_obj(module_data_dict):
    """
        Convenience function that updates the passed in dictionary and
        formats the updated_on and uploaded_on timestamp to a readable,
        user friendly date
    """
    try:
        # checks if updated_on is in module_data_dict
        if module_data_dict["updated_on"]:
            date_obj = module_data_dict["updated_on"].astimezone(
                tz.gettz("US/Eastern")
            )
            formatted_upload_timestamp = \
                str(date_obj.strftime("%m/%d/%y %-I:%M %p %Z"))
            # setting this parameter so that it does not break FE
            module_data_dict["uploaded_on"] = formatted_upload_timestamp
            module_data_dict["updated_on"] = formatted_upload_timestamp

        return module_data_dict

    except Exception as e:
        error_message = (
            f"Error thrown in format_datetime_obj() when formatting "
            f"uploaded_on and/or submitted_on variables: {e}"
        )
        raise EvChartJsonOutputError(message=error_message) from e


def format_fullname_from_email(module_data_dict):
    """
        Convenience function that updates the passed in dictionary's
        updated_by field from an email to the users first and last name
    """
    try:
        if module_data_dict.get("updated_by") is None:
            module_data_dict["updated_by"] = ""
            return module_data_dict
        user_info = get_user_info_dynamo(module_data_dict["updated_by"])

        if user_info:
            module_data_dict["updated_by"] = (
                f'{user_info.get("first_name", "")} '
                f'{user_info.get("last_name", "")}'
            )
        return module_data_dict
    except EvChartDatabaseDynamoQueryError as e:
        e.message += " Error thrown in format_fullname_from_email()"
        raise e
    except Exception as e:
        raise EvChartJsonOutputError(
            message=f"Error thrown in format_fullname_from_email(): {repr(e)}."
        ) from e


def format_org_name_from_email(module_dict):
    """
        Convenience function that updates the passed in dictionary's
        organization field
        with the users organization name
    """
    try:
        user_info = get_user_info_dynamo(module_dict["updated_by"])
        if user_info:
            org_id = user_info.get("org_id")
            org_info = get_org_info_dynamo(org_id)
            org_name = org_info.get("name")
            module_dict["organization"] = org_name

        return module_dict
    except EvChartDatabaseDynamoQueryError as e:
        e.message += " Error thrown in format_org_name_from_email()"
        raise e


def format_dataframe_date(df, is_download=False):
    """
        Convenience function that takes in a dataframe and formats the
        timestamp column
    """
    try:
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ" if is_download else "%m/%d/%y %-I:%M %p %Z"
        for column, _ in df.dtypes.items():
            if pd.api.types.is_datetime64_any_dtype(df[column]):
                df[column] = pd.to_datetime(
                    df[column], utc=True
                )
                df[column] = df[column].dt.strftime(date_format)
    except Exception as e:
        raise EvChartJsonOutputError(
            message=(
                f"Error formatting datetime obj from errors dataframe: {e}"
            )
        ) from e


def format_dataframe_bool(df, feature_toggle_set=frozenset()):
    """
        Convenience function that takes in a dataframe and formats the
        boolean values present
    """
    try:
        if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
            config = DatabaseCentralConfig()
            boolean_columns = config.rds_boolean_fields()
        else:
            boolean_columns = get_list_of_boolean_columns()
        for column in boolean_columns:
            if column in df.columns:
                df[column] = (
                    df[column]
                    .astype(float)
                    .apply(lambda x: {1.0: "TRUE", 0.0: "FALSE"}.get(x, ""))
                )
    except Exception as e:
        raise EvChartJsonOutputError(
            message=f"Error formatting bool values from dataframe: {e}"
        ) from e


@cache
def get_module_id(upload_id, cursor):
    """
        Convenience function that returns a module id number from
        the given upload_id
    """
    get_module_id_query = (
        f"SELECT module_id FROM {import_metadata} "
        "WHERE upload_id=%s"
    )
    module_id = execute_query_fetchone(
        query=get_module_id_query,
        data=(upload_id,),
        cursor=cursor,
        message="Helper method: get_module_id(). ",
    )
    return module_id[0]


@feature_enablement_check(Feature.N_TIER_ORGANIZATIONS)
def get_approval_chain(cursor, curr_org, station_uuid):
    """
        Convenience function that returns an ordered list of the org_ids
        that need to approve module data for the given station uuid. This
        function is aligned with the work done for the n_tier_organizations
        feature, references to the new columns in the
        station_authroizations table
    """
    approval_chain = []
    next_reviewer = get_next_reviewer(cursor, curr_org, station_uuid)
    # checks for 2 tier approval
    if next_reviewer:
        approval_chain.append(next_reviewer)
        next_next_reviewer = get_next_reviewer(
            cursor, next_reviewer, station_uuid
        )
        # checks for 3 tier approval
        if next_next_reviewer:
            approval_chain.append(next_next_reviewer)
    return approval_chain


@feature_enablement_check(Feature.N_TIER_ORGANIZATIONS)
def get_next_reviewer(cursor, curr_org, station_uuid):
    """
        Convenience function returns the org_id of the authorizer, the
        organization who authorized the org that was passed in. This
        function is aligned with the work done for the n_tier_organizations
        feature, references to the new columns in the
        station_authroizations table
    """
    get_next_reviewer_query = f"""
        SELECT authorizer FROM {station_authorizations}
        WHERE station_uuid = %s AND authorizee = %s
    """
    result = execute_query_fetchone(
        query=get_next_reviewer_query,
        data=(station_uuid, curr_org),
        cursor=cursor,
        message="Error thrown in get_next_reviewer()"
    )
    if result:
        return result[0]
    return result
