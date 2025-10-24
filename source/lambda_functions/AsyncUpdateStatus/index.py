"""
AsyncUpdateStatus

Asynchronously update the status of a submission as it moves through the asynchronous upload
process.  Errors are caught and emails generated as necessary.
"""
import datetime
from dateutil import tz

from database_central_config import DatabaseCentralConfig

from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from evchart_helper import aurora
from evchart_helper.api_helper import (
    execute_query_fetchone, format_users, get_org_users, get_upload_metadata, get_user_info_dynamo
)
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError, EvChartJsonOutputError
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.module_enums import ModuleFrequencyProper, ModuleNames
from async_utility.sns_manager import process_sns_message
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature
from schema_compliance.error_table import error_table_insert

import_metadata = ModuleDataTables["Metadata"].value
ev_error_data = ModuleDataTables["EvErrorData"].value


def handler(event, context):
    log_event = LogEvent(event, api="AsyncUpdateStatus", action_type="Put")
    log_event.log_info(event)
    # to set to debug
    # log_event.get_logger().set_level(logging.DEBUG)

    conn = aurora.get_connection()
    try:
        message_type = "no-key"
        is_unknown_message_type = False
        for record in event["Records"]:
            sns_message = process_sns_message(record)
            sns_attributes = list(sns_message.message_attribute.keys())

            for attribute in sns_attributes:
                if attribute not in ["is-s2s", "file-type"]:
                    message_type = attribute

            match message_type:
                case "file-integrity":
                    file_integrity(sns_message, conn, log_event)
                case "data-validation":
                    data_validation(sns_message, conn, log_event)
                case "data-uploaded":
                    data_uploaded(sns_message, conn, log_event)
                case "biz-magic":
                    biz_magic_validation(sns_message, conn, log_event)
                case _:
                    is_unknown_message_type = True
                    log_event.log_info(("unknown sns_message: %s", sns_message))

            if not is_unknown_message_type and not message_status_is_passed(sns_message, message_type):
                with conn.cursor() as cursor:
                    upload_id = sns_message.upload_id
                    error_row_already_exists = error_row_exists(cursor, upload_id)
                    if not error_row_already_exists:
                        upload_metadata = get_upload_metadata(cursor, upload_id)
                        error_message = "An internal error occurred, please try your upload again, if the issue persists, contact EV-ChART help."
                        insert_into_error_table(cursor, upload_metadata, error_message, upload_id)
                conn.commit()

    except (EvChartDatabaseAuroraQueryError,
            EvChartJsonOutputError
    ) as e:
        log_event.log_custom_exception(
            message=e.message,
            status_code=e.status_code,
            log_level=e.log_level
        )
        return_obj = e.get_error_obj()
    else:
        log_event.log_successful_request(
            message="Status successfully updated.",
            status_code=202
        )
        return_obj = {
            'statusCode' : 202,
            'headers': { "Access-Control-Allow-Origin": "*" }
        }
    finally:
        aurora.close_connection()
    return return_obj

def get_attribute_value(attribute, key):
    return attribute.get(key).get("stringValue")

def file_integrity(message, c, log_event):
    status = get_attribute_value(message.message_attribute, 'file-integrity')
    if status != 'passed':
        update_upload_status('Error', "UploadFail", message, c, log_event)

def data_validation(message, c, log_event):
    status = get_attribute_value(message.message_attribute, 'data-validation')
    if status != 'passed':
        update_upload_status('Error', "ProcessingFail", message, c, log_event)

def biz_magic_validation(message, c, log_event):
    status = get_attribute_value(message.message_attribute, 'biz-magic')
    if status != 'passed':
        update_upload_status('Error', "ProcessingFail", message, c, log_event)

def data_uploaded(message, c, log_event):
    status = get_attribute_value(message.message_attribute, 'data-uploaded')
    s2s = get_attribute_value(message.message_attribute, 'is-s2s')
    if status == 'passed':
        if s2s == 'True':
            update_upload_status('Pending', "S2SSuccess", message, c, log_event)
        else:
            update_upload_status('Draft', "Success", message, c, log_event)
    else:
        update_upload_status('Error', "RDSFail", message, c, log_event)

def update_upload_status(submission_status, status_type, message, connection, log_event):
    cursor = connection.cursor()
    try:
        upload_id = message.upload_id
        comments = ""
        if submission_status == 'Error':
            comments = f"Error in upload or processing: {status_type}"
        upload_metadata = get_upload_metadata(cursor, upload_id)
        log_event.log_info(("async update metadata upload_id: %s status: %s", upload_id, submission_status))
        if upload_metadata.get('submission_status') != submission_status:
            updates = {}
            updates["submission_status"] = submission_status
            updates["updated_on"] = str(datetime.datetime.now(tz.gettz("UTC")))
            updates["comments"] = comments
            updates["upload_id"] =  upload_id
            query = f"""
                    UPDATE {import_metadata}
                    SET submission_status = %(submission_status)s,
                        updated_on = %(updated_on)s,
                        comments = %(comments)s
                    WHERE upload_id = %(upload_id)s
                    """
            cursor.execute(query, updates)

            feature_toggle_set = \
                FeatureToggleService().get_active_feature_toggles(
                    log_event=log_event
                )
            # TODO: repetitive code in each of the match-case statements can
            #       be refactored as lookup function.  See JE-6353
            match status_type:
                case "UploadFail":
                    if Feature.FILE_UPLOAD_FAIL_EMAIL in feature_toggle_set:
                        log_event.log_debug(f"Email Info: upload_metadata - {upload_metadata}, status_type = {status_type}, message - {message}")
                        send_email(upload_metadata, status_type, message)
                case "RDSFail":
                    if Feature.INSERT_RDS_FAIL_EMAIL in feature_toggle_set:
                        log_event.log_debug(f"Email Info: upload_metadata - {upload_metadata}, status_type = {status_type}, message - {message}")
                        send_email(upload_metadata, status_type, message)
                case "ProcessingFail":
                    if Feature.DATA_PROCESSING_FAIL_EMAIL in feature_toggle_set:
                        log_event.log_debug(f"Email Info: upload_metadata - {upload_metadata}, status_type = {status_type}, message - {message}")
                        send_email(upload_metadata, status_type, message)
                case "Success":
                    if Feature.DATA_PROCESSING_SUCCESS_EMAIL in feature_toggle_set:
                        log_event.log_debug(f"Email Info: upload_metadata - {upload_metadata}, status_type = {status_type}, message - {message}")
                        send_email(upload_metadata, status_type, message)
                case "S2SSuccess":
                    if Feature.DATA_PROCESSING_SUCCESS_EMAIL in feature_toggle_set:
                        log_event.log_debug(f"Email Info: upload_metadata - {upload_metadata}, status_type = {status_type}, message - {message}")
                        send_email(upload_metadata, status_type, message)

                    if Feature.DATA_AWAITING_REVIEW_EMAIL in feature_toggle_set:
                        log_event.log_debug(f"Email Info: upload_metadata - {upload_metadata}, status_type = {status_type}, message - {message}")
                        send_awaiting_review_email(upload_metadata, message)
        else:
            log_event.log_info(("Status already set, skipping update/email."))
    except Exception as err:
        raise EvChartDatabaseAuroraQueryError(
            message=(
                f"Error updating submission_status in AsyncUpdateStatus "
                f"import_metadata: {err}"
            )
        ) from err
    finally:
        connection.commit()

def send_email(metadata, status_type, message, feature_toggle_set=frozenset()):
    try:
        email_values = {}
        email_values["email"] = metadata.get("updated_by")
        email_values["module_number"] = metadata.get("module_id")

        if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
            config = DatabaseCentralConfig()
            email_values["module_name"] = \
                config.module_display_name(metadata.get('module_id'))
        else:
            full_mod_id = f'Module{metadata.get("module_id")}'
            email_values["module_name"] = ModuleNames[full_mod_id].value

        email_values["reporting_year"] = metadata.get("year")
        email_values["updated_on"] = metadata.get("updated_on")
        email_values["updated_by"] = metadata.get("updated_by")
        email_values["upload_id"] = metadata.get("upload_id")

        user_info = get_user_info_dynamo(metadata.get("updated_by"))
        email_values["first_name"] = user_info.get("first_name")

        if(message.recipient_type == "sub-recipient"):
            email_values["dr_name"] = message.parent_org
            email_values["sr_name"] = message.org_name
        else:
            email_values["dr_name"] = message.org_name
            email_values["sr_name"] = "N/A"

        match status_type:
            case "UploadFail":
                email_values["email_type"] = Email_Template.FILE_UPLOAD_FAIL
            case "RDSFail":
                email_values["email_type"] = Email_Template.INSERT_RDS_FAIL
            case "ProcessingFail":
                email_values["email_type"] = Email_Template.DATA_PROCESSING_FAIL
            case "Success":
                email_values["email_type"] = Email_Template.DATA_PROCESSING_SUCCESS
            case "S2SSuccess":
                email_values["email_type"] = Email_Template.S2S_PROCESSING_SUCCESS

        trigger_email(email_values)
    except Exception as err:
        raise EvChartJsonOutputError(message=f"Error formatting fields for data processing fail email: {err}")

def send_awaiting_review_email(metadata, message, feature_toggle_set=frozenset()):
    try:
        dr_org_name = message.parent_org
        sr_org_name = message.org_name
        associated_drs = get_org_users(metadata.get("parent_org"))
        formatted_drs = format_users(associated_drs)

        email_values = {}
        email_values["email_type"] = Email_Template.DR_APPROVAL
        email_values["sr_org_name"] = sr_org_name
        email_values["dr_org_name"] = dr_org_name
        email_values["module_number"] = metadata.get("module_id")

        if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
            config = DatabaseCentralConfig()
            email_values["module_name"] = \
                config.table_description(metadata.get('module_id'))
            email_values["reporting_period"] = \
                config.module_frequency_proper(metadata.get('module_id'))
        else:
            full_mod_id = f'Module{metadata.get("module_id")}'
            email_values["module_name"] = ModuleNames[full_mod_id].value
            email_values["reporting_period"] = \
                ModuleFrequencyProper[full_mod_id].value

        email_values["last_updated_by"] = metadata.get("updated_by")
        email_values["last_updated_on"] = str(datetime.datetime.now(tz.gettz("UTC")))
        email_values["reporting_year"] = metadata.get("year")
        email_values["upload_id"] = metadata.get("upload_id")

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
            message=f"Error formatting fields for email handler: {repr(e)}"
        ) from e


def message_status_is_passed(message, attribute_type):
    status = get_attribute_value(message.message_attribute, attribute_type)
    is_passed = status == 'passed'
    return is_passed


def error_row_exists(cursor, upload_id):
    check_error_query = f"""
        SELECT COUNT(*)
        FROM {ev_error_data}
        WHERE upload_id=%s
    """
    result = execute_query_fetchone(
        cursor=cursor,
        query=check_error_query,
        data=(upload_id,)
    )
    return result[0] > 0

def insert_into_error_table(cursor, upload_metadata, message, upload_id=None):
    conditions = [{"error_row": None, "error_description": message, "header_name": ""}]

    if upload_metadata is None and upload_id:
        upload_metadata = {}
        upload_metadata["upload_id"] = upload_id
        upload_metadata["module_id"] = ""
        upload_metadata["org_id"] = ""
        upload_metadata["parent_org"] = ""
        message += " No upload metadata matching this upload id found."

    error_table_insert(
        cursor=cursor,
        upload_id=upload_metadata["upload_id"],
        module_id=upload_metadata["module_id"],
        org_id=upload_metadata["org_id"],
        dr_id=upload_metadata["parent_org"],
        condition_list=conditions,
        df=None,
    )
