"""
AsyncFileIntegrity

Asynchronously validate that the file uploaded to S3 matches the checksum generated prior to upload.
"""
import hashlib
import json
from pathlib import Path
from urllib import parse

from async_utility.s3_manager import get_s3_data
from async_utility.sns_manager import send_sns_message
from evchart_helper import aurora
from evchart_helper.api_helper import get_upload_metadata
from evchart_helper.custom_exceptions import (
    EvChartDatabaseHandlerConnectionError,
    EvChartS3CorruptedObjectError,
    EvChartS3GetObjectError,
)
from evchart_helper.custom_logging import LogEvent
from schema_compliance.error_table import error_table_insert


def handler(event, _context):
    log_event = LogEvent(event=event, api="AsyncFileIntegrity", action_type="insert")
    log_event.log_info(event)
    sns_message = {}
    sns_attributes = {}
    batch_errors = []

    for record in event["Records"]:
        error_message = None
        upload_id = None
        upload_metadata = None

        try:
            connection = aurora.get_connection()
        except Exception:  # pylint: disable=broad-exception-caught
            return EvChartDatabaseHandlerConnectionError().get_error_obj()

        try:
            sns_attributes["file-integrity"] = "failed"
            # Should always exist if being triggered by S3
            bucket = record["s3"]["bucket"]["name"]
            key = parse.unquote_plus(record["s3"]["object"]["key"])
            upload_id = Path(key).stem
            sns_message["key"] = key
            sns_message["bucket"] = bucket

            body, metadata = get_s3_data(bucket, key)
            initial_checksum = metadata["checksum"]

            sns_message["recipient_type"] = metadata.get("recipient_type")

            file_checksum = hash_data(body)
            upload_successful = check_hash(initial_checksum, file_checksum)

            if upload_successful:
                sns_attributes["file-integrity"] = "passed"
            else:
                raise EvChartS3CorruptedObjectError(
                    message=f"Provided checksum \
                    {initial_checksum} does not match calculated checksum {file_checksum}"
                )
        except EvChartS3GetObjectError as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()
            return_obj["body"] = json.dumps({"upload_success": False, "key": key})
            sns_attributes["file-integrity"] = "failed"
            error_message = "An internal server error occured, please try again."
        except EvChartS3CorruptedObjectError as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"integrity_check_passed": False, "upload_id": upload_id}),
            }
            sns_attributes["file-integrity"] = "failed"
            error_message = "File recieved does not match expected file. This could be due to corruption caused during upload. Please try uploading the file again, and if the issue persists, contact us."
        else:
            log_event.log_successful_request(
                message=(f"Confirmed successful upload" f"{key}"), status_code=200
            )
            return_obj = {
                "statusCode": 200,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps({"integrity_check_passed": True, "upload_id": upload_id}),
            }
        finally:
            # An error could occur when connecting to server
            if error_message:
                try:
                    with connection.cursor() as cursor:
                        upload_metadata = get_upload_metadata(cursor, upload_id)
                        insert_into_error_table(cursor, upload_metadata, error_message, upload_id)
                    connection.commit()
                # Not sure what errors can occur
                except (TypeError, Exception) as e:  # pylint: disable=broad-exception-caught
                    error = EvChartS3CorruptedObjectError(message=repr(e))
                    log_event.log_level3_error(error)

            aurora.close_connection()

            if not send_sns_message(sns_attributes, sns_message):
                batch_errors.append({"itemIdentifier": record["messageId"]})

    return_obj["batchItemFailures"] = batch_errors
    return return_obj


def hash_data(file_content):
    checksum = None
    if file_content is not None:
        sha256_hash = hashlib.sha256()
        if type(file_content) is not bytes:
            sha256_hash.update(bytes(file_content, encoding="utf-8"))
        else:
            sha256_hash.update(file_content)
        checksum = sha256_hash.hexdigest()
    return checksum


def check_hash(metadata_hash, calculated_hash):
    return metadata_hash == calculated_hash


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
