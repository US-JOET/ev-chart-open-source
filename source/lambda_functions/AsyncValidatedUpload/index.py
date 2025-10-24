"""
AsyncValidatedUpload

Asynchronously monitor that a requested upload import into the system has happened and update the
status of the module accordingly.
"""

import json
from datetime import datetime, timedelta
from io import StringIO
from dateutil import tz

from numpy import nan as NaN
import pandas

from async_utility.s3_manager import get_s3_data
from async_utility.sns_manager import process_sns_message, send_sns_message
from evchart_helper import aurora
from evchart_helper.api_helper import execute_query_fetchone, get_upload_metadata
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseHandlerConnectionError,
    EvChartFeatureStoreConnectionError,
    EvChartFileNotFoundError,
    EvChartMissingOrMalformedBodyError,
    EvChartModuleValidationError,
    EvChartS3GetObjectError,
    EvChartSQSError,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature
from module_validation import (
    drop_sample_rows,
    get_dataframe_from_csv,
    load_module_definitions,
    set_station_and_port_ids,
    upload_data_from_df,
)


def handler(event, _context):
    log_event = LogEvent(event=event, api="AsyncValidatedUpload", action_type="insert")
    log_event.log_info(event)

    # feature must be called in the handler in order to get the
    # current value every time, and not a value persisted by Lambda warm start
    # https://docs.aws.amazon.com/lambda/latest/operatorguide/global-scope.html
    # pylint: disable=duplicate-code
    feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)
    try:
        connection = aurora.get_connection()
    except Exception:
        return EvChartDatabaseHandlerConnectionError().get_error_obj()

    sns_message = {}
    sns_attributes = {}
    batch_errors = []

    for record in event["Records"]:
        try:
            sns_attributes["data-uploaded"] = "failed"
            load_module_definitions()
            with connection.cursor() as cursor:
                # Extract message
                message = process_sns_message(record)
                key = message.key
                bucket = message.bucket
                upload_id = message.upload_id
                attributes = message.message_attribute
                sns_message["key"] = key
                sns_message["bucket"] = bucket

                # Get S3 object/metadata
                s3_body, s3_metadata = get_s3_data(bucket, key)
                recipient_type = s3_metadata.get("recipient_type")
                sns_attributes["is-s2s"] = s3_metadata.get("s2s_upload", "no")
                sns_message["recipient_type"] = recipient_type
                file_type = attributes.get("file-type").get("stringValue")

                if file_type == "json" and Feature.BIZ_MAGIC in feature_toggle_set:
                    df = pandas.read_json(StringIO(s3_body), orient="table")
                else:
                    df = get_dataframe_from_csv(s3_body)
                df = drop_sample_rows(df)

                upload_metadata = get_upload_metadata(cursor, upload_id)

                if upload_metadata is None:
                    message = "Error getting upload metadata, no record found for %s", upload_id
                    raise EvChartDatabaseAuroraQueryError(message=message)

                module_id = upload_metadata.get("module_id")
                df["upload_id"] = upload_metadata["upload_id"]

                module_table = ModuleDataTables[f"Module{module_id}"].value
                skip_upload = data_already_exists_in_rds(cursor, module_table, upload_id)

                if skip_upload:
                    return_message = f"data has already been uploaded for upload_id: {upload_id}"
                    return_obj = get_return_object(
                        log_event, return_message, 200, True, upload_id=""
                    )
                else:
                    df = set_station_and_port_ids(df, cursor)

                    if file_type == "json" and Feature.BIZ_MAGIC in feature_toggle_set:
                        upload_data_from_df(
                            connection=connection,
                            module_number=module_id,
                            df=df,
                            check_boolean=False,
                        )
                    elif ((Feature.MODULE_5_NULLS in feature_toggle_set and int(module_id) == 5)):
                        adjusted_df = adjust_for_nulls(feature_toggle_set, module_id, df)
                        upload_data_from_df(connection, module_id, adjusted_df, feature_toggle_set)
                    else:
                        upload_data_from_df(connection, module_id, df, feature_toggle_set)

        # Errors after getting upload_id
        except (
            EvChartDatabaseAuroraQueryError,
            EvChartModuleValidationError,
            EvChartMissingOrMalformedBodyError,
            EvChartUserNotAuthorizedError,
        ) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()
            return_body = json.dumps(
                {"upload_success": False, "upload_id": upload_id, "error": e.message}
            )
            return_obj["body"] = return_body
            sns_message["reason"] = e.message

        # Errors before getting upload_id
        except (EvChartFileNotFoundError, EvChartSQSError, EvChartS3GetObjectError) as e:
            log_event.log_custom_exception(
                message=e.message, status_code=e.status_code, log_level=e.log_level
            )
            return_obj = e.get_error_obj()
            return_body = json.dumps({"upload_success": False, "error": e.message})
            return_obj["body"] = return_body
            sns_message["reason"] = e.message

        else:
            if not skip_upload:
                log_event.log_successful_request(
                    message=(f"Successfully validated upload: " f"{upload_id}"),
                    status_code=201,
                )
                return_obj = {
                    "statusCode": 201,
                    "headers": {"Access-Control-Allow-Origin": "*"},
                    "body": json.dumps(
                        {"upload_success": True, "upload_id": upload_id, "error_count": 0}
                    ),
                }
            sns_attributes["data-uploaded"] = "passed"

        finally:
            if not send_sns_message(sns_attributes, sns_message):
                batch_errors.append({"itemIdentifier": record["messageId"]})

    return_obj["batchItemFailures"] = batch_errors
    aurora.close_connection()
    return return_obj


def get_return_object(log_event, message, my_status_code, upload_success, upload_id=""):
    log_event.log_successful_request(
        message=(message),
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


def data_already_exists_in_rds(cursor, module_table, upload_id):
    select_statement = f"""
        SELECT COUNT(*)
        FROM {module_table}
        WHERE upload_id=%s
        """
    result = execute_query_fetchone(
        query=select_statement,
        data=upload_id,
        cursor=cursor,
        message="data_already_exists_in_rds AsyncValidatedUpload",
    )
    return result[0] > 0


def adjust_for_nulls(feature_toggle_set, module_id, df):
    try:
        if int(module_id) == 5 and Feature.MODULE_5_NULLS in feature_toggle_set:
            correct_nulls = df["maintenance_cost_total"].astype(str).str.lower() == "null"
            df.loc[correct_nulls, ["maintenance_cost_total"]] = None

        return df
    except Exception as e:
        raise EvChartModuleValidationError(
            message=f"Error adjusting for nulls: {e}",
        ) from e
