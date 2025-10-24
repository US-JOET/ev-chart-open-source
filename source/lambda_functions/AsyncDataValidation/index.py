"""
AsyncDataValidation

Asynchronously validate the data types provided for the relevant module data against known
constraints.
"""
import csv
import json
import logging
import traceback

import pandas

from async_utility.s3_manager import get_s3_data
from async_utility.sns_manager import process_sns_message, send_sns_message
from evchart_helper import aurora
from evchart_helper.api_helper import get_upload_metadata
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseHandlerConnectionError,
    EvChartInvalidCSVError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedBodyError,
    EvChartModuleValidationError,
    EvChartS3GetObjectError,
    EvChartSQSError,
    EvChartUserNotAuthorizedError,
    EvChartFeatureStoreConnectionError,
    EvChartDatabaseAuroraDuplicateItemError

)
from evchart_helper.custom_logging import LogEvent
from module_validation import (
    ModuleDefinitionEnum,
    csv_to_dataframe,
    drop_sample_rows,
    get_dr_and_sr_ids,
    load_module_definitions,
    validate_station_id,
    validated_dataframe_by_module_id,
)
from module_validation.unique_constraint import unique_constraint_violations_for_async
from schema_compliance.error_table import error_table_insert
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature


logger = logging.getLogger("AsyncDataValidation")
logger.setLevel(logging.INFO)

def handler(event, _context):
    log_event = LogEvent(event=event, api="AsyncDataValidation", action_type="insert")
    log_event.log_info(event)
    conditions = []
    try:
        connection = aurora.get_connection()
    except Exception:  # pylint: disable=broad-exception-caught
        return EvChartDatabaseHandlerConnectionError().get_error_obj()

    # feature must be called in the handler in order to get the
    # current value every time, and not a value persisted by Lambda warm start
    # https://docs.aws.amazon.com/lambda/latest/operatorguide/global-scope.html
    # pylint: disable=duplicate-code
    feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)
    sns_message = {}
    sns_attributes = {}
    batch_errors = []
    return_obj = {}
    conditions = []
    # when getting the SQS messasge it is in a list of records

    for record in event["Records"]:
        try:
            sns_attributes["data-validation"] = "failed"
            load_module_definitions()
            with connection.cursor() as cursor:
                # Extract message
                message = process_sns_message(record)
                key = message.key
                bucket = message.bucket
                upload_id = message.upload_id
                sns_message["key"] = key
                sns_message["bucket"] = bucket
                # Get S3 object/metadata
                s3_body, s3_metadata = get_s3_data(bucket, key)


                df = get_dataframe_from_csv(s3_body)
                log_event.log_debug(f"df: {df}")
                df = drop_sample_rows(df)
                # Get upload metadata from RDS
                upload_metadata = get_upload_metadata(cursor, upload_id)
                module_id = upload_metadata.get("module_id")
                recipient_type = s3_metadata.get("recipient_type")
                is_s2s = s3_metadata.get("s2s_upload", False)
                sns_message["recipient_type"] = recipient_type
                # for s2s uploads check unique constraints
                ids = get_dr_and_sr_ids(recipient_type, upload_metadata)
                dr_id, _ = ids
                # CHECKING STATION REGISTRATION & AUTHORIZATION & STATUS
                log_event.log_debug(f"df: {df}")
                log_event.log_debug(f"metadata: {upload_metadata}")
                conditions = validate_station_id(
                    df, recipient_type, connection, upload_metadata, feature_toggle_set
                )
                validation_response = validated_dataframe_by_module_id(
                    ModuleDefinitionEnum(int(module_id)),
                    df,
                    upload_metadata["upload_id"],
                    feature_toggle_set,
                )
                conditions.extend(validation_response.get("conditions", []))
                updated_df = validation_response.get("df", pandas.DataFrame())
            if len(conditions) == 0:
                connection.ping()
                with connection.cursor() as cursor:
                    constraint_errors = enforce_constraints_for_s2s(
                        is_s2s=is_s2s,
                        cursor=cursor,
                        log_event=log_event,
                        upload_id=upload_id,
                        dr_id=dr_id,
                        module_df=updated_df,
                        module_id=module_id,
                        feature_toggle_set=feature_toggle_set,
                    )
                    conditions.extend(constraint_errors)

            # Errors found during validation
            if len(conditions) > 0:
                connection.ping()
                with connection.cursor() as cursor:
                    insert_errors_to_table(cursor, conditions, upload_metadata, df)
                    connection.commit()
                    raise EvChartInvalidCSVError(message="Module data is not compliant")

        # Future state, split up into errors that should trigger a retry/dlq and those that shouldnt
        except (
            EvChartDatabaseHandlerConnectionError,
            EvChartMissingOrMalformedBodyError,
            EvChartUserNotAuthorizedError,
            EvChartDatabaseAuroraQueryError,
            EvChartJsonOutputError,
            EvChartModuleValidationError,
            EvChartSQSError,
            EvChartS3GetObjectError,
            EvChartDatabaseAuroraDuplicateItemError
        ) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()
            return_body = json.dumps(
                {
                    "validation_success": False,
                    "upload_id": upload_id,
                    "error": e.message,
                    "error_count": len(conditions),
                }
            )
            return_obj["body"] = return_body
            sns_message["reason"] = e.message

        except EvChartInvalidCSVError as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = {"statusCode": 200, "headers": {"Access-Control-Allow-Origin": "*"}}
            return_body = json.dumps(
                {
                    "validation_success": False,
                    "upload_id": upload_id,
                    "error_count": len(conditions),
                }
            )
            return_obj["body"] = return_body
            sns_message["reason"] = e.message

        except Exception as e:  # pylint: disable=broad-exception-caught
            log_event.log_custom_exception(
                message=f"uncaught error: {repr(e)} trace: {traceback.format_exc()}", status_code=500, log_level=3
            )

            return_obj = {
                "statusCode": 500,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(
                    {
                        "validation_success": False,
                        "upload_id": upload_id,
                        "error_count": len(conditions),
                    }
                ),
            }
            sns_message["reason"] = "uncaught error"

        else:
            log_event.log_successful_request(
                message=(f"Successfully imported module data for upload " f"{upload_id}"),
                status_code=201,
            )
            return_obj = {
                "statusCode": 201,
                "headers": {"Access-Control-Allow-Origin": "*"},
                "body": json.dumps(
                    {"upload_success": True, "upload_id": upload_id, "error_count": 0}
                ),
            }
            sns_attributes["data-validation"] = "passed"

        finally:
            if not send_sns_message(sns_attributes, sns_message):
                batch_errors.append({"itemIdentifier": record["messageId"]})

    aurora.close_connection()
    return_obj["batchItemFailures"] = batch_errors
    return return_obj

def get_new_connection():
    aurora.close_connection()
    try:
        connection = aurora.get_connection()
    except Exception as e:  # pylint: disable=broad-exception-caught
        raise EvChartDatabaseHandlerConnectionError(message=f"issue creating connection {repr(e)}") from e
    return connection

def get_dataframe_from_csv(body):
    try:
        raw_data = body.splitlines()
        logging.debug("raw data set: %s", raw_data)

        if not raw_data[0][0].isascii():
            raw_data[0] = raw_data[0][1:]

        return csv_to_dataframe(csv.reader(raw_data))
    except EvChartModuleValidationError as e:
        raise EvChartModuleValidationError(message=f"{repr(e)}") from e
    except Exception as e:
        raise EvChartMissingOrMalformedBodyError(message=f"Unable to read csv: {repr(e)}") from e


def insert_errors_to_table(cursor, conditions, metadata, df):
    error_table_insert(
        cursor=cursor,
        upload_id=metadata["upload_id"],
        module_id=metadata["module_id"],
        org_id=metadata["org_id"],
        dr_id=metadata["parent_org"],
        condition_list=conditions,
        df=df,
    )


def enforce_constraints_for_s2s(
    is_s2s,
    cursor,
    log_event,
    upload_id,
    dr_id,
    module_df,
    module_id,
    feature_toggle_set=frozenset(),
):
    unique_constraint_response_errors = []
    if is_s2s or Feature.CHECK_DUPLICATES_UPLOAD in feature_toggle_set:
        unique_constraint_response = unique_constraint_violations_for_async(
            cursor=cursor,
            upload_id=upload_id,
            dr_id=dr_id,
            df=module_df,
            log_event=log_event,
            module_id=module_id,
            feature_toggle_set=feature_toggle_set,
        )
        unique_constraint_response_errors = unique_constraint_response.get("errors", [])

    return unique_constraint_response_errors
