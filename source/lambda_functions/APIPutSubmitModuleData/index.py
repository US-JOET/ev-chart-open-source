"""
APIPutSubmitModuleData

Updates the requested module submission to the Pending status after validating the provided
organization and user details, along with the current module status.  An email will be sent to the
relevant users indicating this status has changed.
"""
import datetime
import json
import logging
import pandas as pd
from dateutil import tz
from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from evchart_helper import aurora
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseDynamoQueryError,
    EvChartDatabaseHandlerConnectionError,
    EvChartMissingOrMalformedBodyError,
    EvChartUserNotAuthorizedError,
    EvChartJsonOutputError,
    EvChartDatabaseAuroraDuplicateItemError
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.module_enums import ModuleFrequencyProper, ModuleNames
from evchart_helper.module_helper import is_valid_upload_id, get_module_id
from evchart_helper.api_helper import (
    execute_query,
    format_users,
    get_org_info_dynamo,
    get_org_users,
)
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature
from schema_compliance.error_table import error_table_insert
from module_validation.unique_constraint import unique_constraint_violations
from database_central_config import DatabaseCentralConfig

from pymysql.err import Error
from botocore.exceptions import BotoCoreError

logger = logging.getLogger("APIPutSubmitModuleData")
logger.setLevel(logging.DEBUG)

metadata_table = ModuleDataTables["Metadata"].value


@SessionManager.check_session()
def handler(event, _context):
    try:
        connection = aurora.get_connection()
    except (Error, BotoCoreError):
        return EvChartDatabaseHandlerConnectionError().get_error_obj()
    except Exception as e:
        logger.debug("non-database error encountered: %s", repr(e))
        raise

    log_event = LogEvent(
        event, api="APIPutSubmitModuleData", action_type="MODIFY"
    )
    feature_toggle_set = FeatureToggleService().get_active_feature_toggles(
        log_event=log_event
    )

    with connection.cursor() as cursor:
        try:
            if not log_event.is_auth_token_valid():
                raise EvChartAuthorizationTokenInvalidError()

            request_body = json.loads(event['body'])
            if "upload_id" not in request_body:
                raise EvChartMissingOrMalformedBodyError(
                    message="Missing from body: upload_id"
                )

            upload_id = request_body['upload_id']
            token = log_event.get_auth_token()
            submitted_by = token.get("email")
            org_id = token.get("org_id")
            recipient_type = token.get("recipient_type")
            submitted_on = datetime.datetime.now(tz.gettz("UTC"))
            request_body["org_name"] = token.get("org_name")

            # check if valid upload_id
            if is_valid_upload_id(upload_id, cursor) is False:
                raise EvChartMissingOrMalformedBodyError(
                    message="Malformed upload_id"
                )

            # check if user is authorized to submit module
            metadata_info = is_user_authorized_to_submit(
                log_event, upload_id, org_id, cursor
            )
            if metadata_info is False:
                raise EvChartUserNotAuthorizedError(
                    message=(
                        "Current organization not authorized to "
                        "submit module data"
                    )
                )

            check_unique_submission(
                cursor=cursor,
                log_event=log_event,
                upload_id=upload_id,
                org_id=org_id,
                dr_id=metadata_info.get("parent_org", "DR NOT SPECIFIED"),
                feature_toggle_set=feature_toggle_set
            )

            query_data = ()
            update_query = f"""
                UPDATE {metadata_table}
                SET updated_on=%s, updated_by=%s, submission_status=%s
                WHERE upload_id=%s and org_id=%s
            """
            # if user is a DR, this updates and ensures that the
            # parent org is their DR org_id
            if recipient_type == "direct-recipient":
                query_data = (
                    submitted_on, submitted_by, "Submitted", upload_id, org_id
                )

            elif recipient_type == "sub-recipient":
                query_data = (
                    submitted_on, submitted_by, "Pending", upload_id, org_id
                )

            execute_query(
               query=update_query,
               data=query_data,
               cursor=cursor,
               message="Error thrown in APISubmitModuleData."
            )
            if Feature.DATA_AWAITING_REVIEW_EMAIL in feature_toggle_set:
                if recipient_type == "sub-recipient":
                    send_awaiting_review_email(
                        upload_id=upload_id,
                        metadata_info=metadata_info,
                        request_body=request_body,
                        feature_toggle_set=feature_toggle_set
                    )

        except (
            EvChartMissingOrMalformedBodyError,
            EvChartAuthorizationTokenInvalidError,
            EvChartDatabaseAuroraQueryError,
            EvChartUserNotAuthorizedError,
            EvChartJsonOutputError,
            EvChartDatabaseAuroraDuplicateItemError,
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
                message="APISubmitModuleData successfully invoked",
                status_code=201
            )
            return_obj = {
                'statusCode': 201,
                'headers': {"Access-Control-Allow-Origin": "*"},
                'body': json.dumps("Module data successfully submitted")
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


def is_user_authorized_to_submit(log_event, upload_id, org_id, cursor):
    # verifies if org is viewing own module
    check_auth_query = (
        f"SELECT * FROM {metadata_table} "
        f"WHERE upload_id=%s and org_id=%s"
    )
    result = execute_query(
        query=check_auth_query,
        data=(upload_id, org_id),
        cursor=cursor,
        message=(
            "Error thrown in module_helper is_user_authorized_to_submit(). "
        )
    )

    # if nothing was returned, then user is not submitting their own module,
    # return false
    if not result:
        return False
    return {"module_id": result[0]["module_id"],
            "updated_by": result[0]["updated_by"],
            "updated_on": result[0]["updated_on"],
            "year": result[0]["year"],
            "parent_org": result[0]["parent_org"]}


def check_unique_submission(
    cursor,
    log_event,
    upload_id,
    org_id,
    dr_id,
    feature_toggle_set=frozenset()
):
    unique_constraint_response = unique_constraint_violations(
        cursor=cursor,
        upload_id=upload_id,
        dr_id=dr_id,
        log_event=log_event,
        feature_toggle_set=feature_toggle_set
    )
    if len(unique_constraint_response.get('errors', [])) > 0:
        error_table_insert(
            cursor=cursor,
            upload_id=upload_id,
            module_id=get_module_id(cursor=cursor, upload_id=upload_id),
            org_id=org_id,
            dr_id=dr_id,
            condition_list=unique_constraint_response.get('errors'),
            df=unique_constraint_response.get('df')
        )
        update_upload_error_status(cursor, log_event, upload_id)
        raise EvChartDatabaseAuroraDuplicateItemError(
            operation="Insert",
            message="duplicate data found in upload"
        )
    return True


def update_upload_error_status(cursor, log_event, upload_id):
    execute_query(
        query=(
            f"UPDATE {metadata_table} "
            f"SET submission_status='Error' WHERE upload_id=%s"
        ),
        data=(upload_id,),
        cursor=cursor,
    )


def send_awaiting_review_email(
    upload_id: str,
    metadata_info: dict,
    request_body: dict,
    feature_toggle_set: frozenset = frozenset()
):
    try:
        dr_org_name = get_org_info_dynamo(metadata_info["parent_org"])["name"]
        associated_drs = get_org_users(metadata_info["parent_org"])
        formatted_drs = format_users(associated_drs)

        email_values = {}
        email_values["email_type"] = Email_Template.DR_APPROVAL
        email_values["sr_org_name"] = request_body["org_name"]
        email_values["dr_org_name"] = dr_org_name
        email_values["module_number"] = metadata_info["module_id"]
        email_values["last_updated_by"] = metadata_info["updated_by"]
        email_values["last_updated_on"] = \
            format_timezone(metadata_info["updated_on"])
        email_values["reporting_year"] = metadata_info["year"]
        if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
            config = DatabaseCentralConfig()
            email_values["module_name"] = config.module_display_name(metadata_info.get('module_id'))
            email_values["reporting_period"] = \
                config.module_frequency_proper(metadata_info.get('module_id'))
        else:
            full_mod_id = f'Module{metadata_info["module_id"]}'
            email_values["module_name"] = ModuleNames[full_mod_id].value
            email_values["reporting_period"] = \
                ModuleFrequencyProper[full_mod_id].value
        email_values["upload_id"] = upload_id

        for user in formatted_drs:
            if user.get("status") == "Active" and user.get("role") == "Administrator":
                email_values["first_name"] = user.get("first_name").strip()
                email_values["email"] = user.get("email").strip()
                trigger_email(email_values)
    except EvChartJsonOutputError as e:
        raise e
    except Exception as e:
        raise EvChartJsonOutputError(
            log_obj=None,
            message=f"Error formatting fields for email handler: {e}"
        ) from e


def format_timezone(existing):
    try:
        eastern = tz.gettz("US/Eastern")
        date_format = "%m/%d/%y %I:%M %p %Z"

        correct_format = pd.to_datetime(existing, utc=True).tz_convert(eastern)
        added_zone = correct_format.strftime(date_format).replace(
            r"\b0(\d:\d{2} [AP]M)", r"\1"
        )

        return added_zone
    except Exception as e:
        raise EvChartJsonOutputError(
            log_obj=None, message=f"Error formatting timezone for: {e}"
        ) from e
