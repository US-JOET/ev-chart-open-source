"""
AsyncBizMagic

Asynchronously validates module data provided against custom logic constraints that cannot be done
naturally via SQL or other means. This file will pull an existing upload from the s3 bucket, validate
its contents using module specific validation files found in lambda_layers/python/module_validation,
then transform the data into database acceptable data types found in lambda_layers/python/module_transform.
Once validation and transformation is successful, the updated data is put back into the s3 and is moved along
the async process to AsyncValidatedUpload. If the data does not align with the validation or transformation
rules set, an error will be instered into the error table and the asynchronous data validation process will
terminate, returning a 400/500 level error.
"""

import json
import logging
import hashlib
from datetime import datetime
from itertools import chain
import traceback

import pandas
from pymysql.err import Error
from botocore.exceptions import BotoCoreError

from async_utility.s3_manager import get_s3_data
from async_utility.sns_manager import process_sns_message, send_sns_message

from database_central_config import DatabaseCentralConfig
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

from evchart_helper import aurora
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.api_helper import get_upload_metadata, get_org_info_dynamo
from evchart_helper.custom_logging import LogEvent
from evchart_helper.custom_exceptions import (
    EvChartAsynchronousS3Error,
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseHandlerConnectionError,
    EvChartFileNotFoundError,
    EvChartInvalidCSVError,
    EvChartMissingOrMalformedBodyError,
    EvChartModuleValidationError,
    EvChartS3GetObjectError,
    EvChartSQSError,
    EvChartUserNotAuthorizedError,
)

from module_transform import (
    transform_m2,
    transform_m3,
    transform_m4,
    transform_m5,
    transform_m9,
)

from module_validation import (
    validate_m2,
    validate_m3,
    validate_m4,
    validate_m9,
    _get_module_fields_by_number,
    drop_sample_rows,
    get_dataframe_from_csv,
    get_dr_and_sr_ids,
    load_module_definitions,
    set_station_uuid,
)

from schema_compliance.error_table import error_table_insert

logger = logging.getLogger("AsyncBizMagic")
logger.setLevel(logging.DEBUG)

"""
Custom_validations ifo:
custom_validations - dictionary that holds the functions for business validation checks for null modules
Module 5 - bizmagic validate file does not exist because there is no business logic to verify against. "maintenance_cost_total" is the
only nullable field in the module, and is verified for correctness during custom_transformations
Module 3 - "uptime" field is only flagged as an error if the field is null and the operational_date is greater than 1 year
"""
custom_validations = {
    2: [validate_m2.validate_empty_session],
    3: [validate_m3.validate_operational_one_year],
    4: [validate_m4.validate_empty_outage],
    5: [],
    6: [],
    7: [],
    8: [],
    9: [validate_m9.validate_empty_capital_install_costs],
}

"""
custom_transformations - dictionary that holds the functions that transforms the dataframe into acceptable values for the database
ex: setting empty strings to None, setting boolean values to 0 or 1
"""
custom_transformations = {
    2: [transform_m2.allow_null_charging_sessions],
    3: [transform_m3.allow_null_uptime],
    4: [transform_m4.allow_null_outages],
    5: [transform_m5.allow_null_federal_maintenance],
    6: [],
    7: [],
    8: [],
    9: [transform_m9.allow_null_capital_install_costs],
}


def insert_errors_to_table(connection, conditions, metadata, df):
    """
    Convenience function that inserts errors found during data validation into the error table
    """
    if len(conditions) == 0:
        return
    connection.ping()
    with connection.cursor() as cursor:
        error_table_insert(
            cursor=cursor,
            upload_id=metadata["upload_id"],
            module_id=metadata["module_id"],
            org_id=metadata["org_id"],
            dr_id=metadata["parent_org"],
            condition_list=conditions,
            df=df,
        )
    connection.commit()
    raise EvChartInvalidCSVError(message="Module data is not compliant")


def upload_transform_df(
    bucket, upload_id, recipient_type, df, new_file_name, s2s_upload
):
    """
    Convenience function that uploads the validated and transformed dataframe as a json object to the s3 bucket
    """
    json_payload = bytes(df.to_json(orient="table"), encoding="utf-8")
    s3 = boto3_manager.resource("s3")
    custom_metadata = {
        "checksum": hashlib.sha256(json_payload).hexdigest(),
        "recipient_type": recipient_type,
    }

    if s2s_upload == "True":
        custom_metadata["s2s_upload"] = s2s_upload

    try:
        s3.Bucket(bucket).put_object(
            Key=f"{new_file_name}", Body=json_payload, Metadata=custom_metadata
        )
    except Exception as e:
        raise EvChartAsynchronousS3Error(
            message=f"Error uploading {upload_id} to S3 bucket: {repr(e)}"
        ) from e


def get_return_object(log_event, message, my_status_code, upload_success, upload_id=""):
    """
    Convenience function that logs the successful api execution and returns the successful payload for the frontend
    """
    log_event.log_successful_request(
        message=message,
        status_code=my_status_code,
    )
    return_obj = {
        "statusCode": my_status_code,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(
            {"upload_success": upload_success, "upload_id": upload_id, "error_count": 0}
        ),
    }

    return return_obj


def set_datatype(df, module_id, feature_toggle_set=frozenset()):
    """
    Convenience function that converts the expected boolean, numeric, and datetime datatypes for each column in the dataframe
    """
    adjusted_df = df.copy()
    if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        config = DatabaseCentralConfig()
        boolean_fields = {
            field
            for field in config.validated_boolean_fields(module_id)
            if field in adjusted_df.columns
        }
        numeric_fields = {
            field
            for field in config.validated_numeric_fields(module_id)
            if field in adjusted_df.columns
        }
        datetime_fields = {
            field
            for field in config.validated_datetime_fields(module_id)
            if field in adjusted_df.columns
        }
    else:
        module_fields = _get_module_fields_by_number(module_id)
        boolean_fields = [
            m.get("field_name")
            for m in module_fields
            if (m.get("datatype") == "boolean" and m.get("field_name") in df.columns)
        ]
        numeric_fields = [
            m.get("field_name")
            for m in module_fields
            if (
                m.get("datatype") in {"decimal", "integer"}
                and m.get("field_name") in df.columns
            )
        ]
        datetime_fields = [
            m.get("field_name")
            for m in module_fields
            if (m.get("datatype") == "datetime" and m.get("field_name") in df.columns)
        ]

    for field in boolean_fields:
        try:
            adjusted_df[field] = (
                adjusted_df[field]
                .str.upper()
                .map({"TRUE": 1, "FALSE": 0})
                .convert_dtypes()
            )
        except AttributeError:
            # AttributeError is raised if value has already been converted
            # from string to integer
            pass

    for field in numeric_fields:
        adjusted_df[field] = pandas.to_numeric(
            adjusted_df[field], errors="coerce"
        ).convert_dtypes()

    for field in datetime_fields:
        adjusted_df[field] = pandas.to_datetime(
            adjusted_df[field], format="ISO8601", errors="coerce"
        ).convert_dtypes()

    return adjusted_df


def handler(event, _context):
    log_event = LogEvent(event=event, api="AsyncBizMagic", action_type="insert")
    logger.info(event)

    return_obj = {}
    conditions = []

    # feature must be called in the handler in order to get the
    # current value every time, and not a value persisted by Lambda warm start
    # https://docs.aws.amazon.com/lambda/latest/operatorguide/global-scope.html
    # pylint: disable=duplicate-code
    feature_toggle_set = FeatureToggleService().get_active_feature_toggles(
        log_event=log_event
    )

    # SQS should only send one record.  If not, this will send to DLQ
    if len(event.get("Records", [])) != 1:
        return EvChartSQSError().get_error_obj()

    try:
        connection = aurora.get_connection()
    except (Error, BotoCoreError):
        return EvChartDatabaseHandlerConnectionError().get_error_obj()
    except Exception as e:
        logger.debug("non-database error encountered: %s", repr(e))
        raise

    sns_message = {}
    record = event["Records"][0]
    sns_attributes = {"biz-magic": "failed", "file-type": "json"}
    load_module_definitions()

    try:
        # Extract message
        message = process_sns_message(record)
        upload_id = message.upload_id
        sns_message.update(key=message.key, bucket=message.bucket)

        logger.debug(
            "Custom validation and transformation for upload_id: %s", upload_id
        )

        # Get S3 object/metadata
        s3_body, s3_metadata = get_s3_data(message.bucket, message.key)
        recipient_type = s3_metadata.get("recipient_type")
        sns_attributes["is-s2s"] = s3_metadata.get("s2s_upload", "False")
        sns_message["recipient_type"] = recipient_type

        df = get_dataframe_from_csv(s3_body)
        df = drop_sample_rows(df)
        with connection.cursor() as cursor:
            upload_metadata = get_upload_metadata(cursor, upload_id)

            if upload_metadata is None:
                raise EvChartDatabaseAuroraQueryError(
                    message=(
                        "Error getting upload metadata, "
                        f"no record found for {upload_id}"
                    )
                )
            module_id = int(upload_metadata.get("module_id"))
            df["upload_id"] = upload_metadata["upload_id"]

            df = set_station_uuid(
                df=df,
                dr_id=get_dr_and_sr_ids(recipient_type, upload_metadata)[0],
                cursor=cursor,
            )

            # any data that a validation function will require should be
            # configured here.  individual validation functions may use
            # or disregard these options
            validation_options = {
                "cursor": cursor,
                "feature_toggle_set": feature_toggle_set,
                "df": df,
                "today": datetime.now(),
            }

            # get the list of errors found within the dataframe after each custom_validation
            # function has been run for that module
            conditions = list(
                chain.from_iterable(
                    cv(validation_options).get("conditions", [])
                    for cv in custom_validations[module_id]
                )
            )
            if Feature.BIZ_MAGIC in feature_toggle_set:
                insert_errors_to_table(connection, conditions, upload_metadata, df)

                for ct in custom_transformations[module_id]:
                    df = ct(feature_toggle_set, df)

                df = set_datatype(df, module_id, feature_toggle_set)
                org_name = get_org_info_dynamo(upload_metadata["org_id"])["name"]

                # setting file path based on recipient type
                if recipient_type == "direct-recipient":
                    new_file_name = f"transformed/{org_name}/{upload_id}.json"
                elif recipient_type == "sub-recipient":
                    parent_name = get_org_info_dynamo(upload_metadata["parent_org"])[
                        "name"
                    ]
                    new_file_name = (
                        f"transformed/{parent_name}/{org_name}/{upload_id}.json"
                    )
                else:
                    new_file_name = f"transformed/testing/{org_name}/{upload_id}.json"
                sns_message["key"] = new_file_name

                # uploading the transformed dataframe which has been verified and updated to meet db datatypes into s3 bucket
                upload_transform_df(
                    bucket=message.bucket,
                    upload_id=upload_id,
                    recipient_type=recipient_type,
                    df=df,
                    new_file_name=new_file_name,
                    s2s_upload=sns_attributes["is-s2s"],
                )
            return_obj = get_return_object(
                log_event=log_event,
                message=f"Successfully transformed upload: {upload_id}",
                my_status_code=201,
                upload_success=True,
                upload_id=upload_id,
            )
        sns_attributes["biz-magic"] = "passed"
    except (
        EvChartDatabaseAuroraQueryError,
        EvChartModuleValidationError,
        EvChartMissingOrMalformedBodyError,
        EvChartUserNotAuthorizedError,
        EvChartFileNotFoundError,
        EvChartS3GetObjectError,
        EvChartAsynchronousS3Error,
        EvChartInvalidCSVError,
    ) as e:
        log_event.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
        )
        return_obj = e.get_error_obj()
        return_obj.update(
            body=json.dumps(
                {"upload_success": False, "upload_id": upload_id, "error": e.message}
            )
        )
        sns_message["reason"] = e.message
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_event.log_custom_exception(
            message=f"uncaught error: {repr(e)} trace: {traceback.format_exc()}",
            status_code=500,
            log_level=3,
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
    finally:
        if send_sns_message(sns_attributes, sns_message):
            return_obj.update(batchItemFailures=[])
        else:
            return_obj.update(
                batchItemFailures=[{"itemIdentifier": record["messageId"]}]
            )

    aurora.close_connection()
    return return_obj
