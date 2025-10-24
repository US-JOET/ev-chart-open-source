import datetime
import json
import os
from unittest.mock import MagicMock, patch
import boto3
import pandas
import pytest
from AsyncDataValidation.index import (
    enforce_constraints_for_s2s,
    get_dataframe_from_csv,
    handler,
)
from evchart_helper.boto3_manager import Boto3Manager
from moto import mock_aws

import feature_toggle
from module_validation import load_module_definitions
from feature_toggle.feature_enums import Feature

upload_file_path = "./tests/sample_data/all_columns_module_8.csv"
upload_checksum = "0d810e7fbf2f435b93a7b51d26e7df28e3b8747a322a33dcf2a4db8dbae63ce0"
upload_key = "upload/Joint Office/852ade96-4075-4766-9b97-5e9379b31ab0.csv"
s2s_upload_key = "upload/Joint Office/952ade96-4075-4766-9b97-5e9379b31ab2.csv"
upload_bucket_name = "ev-chart-artifact-data-unit-test"
duplicate_data = "./tests/sample_data/check_duplicate_upload_mod2.csv"
invalid_file_upload_key = "bad_file.csv"
invalid_file_path = "./tests/sample_data/all_invalid_data_type_mod_9.csv"

ft_set = {
    Feature.MODULE_5_NULLS,
    Feature.UNIQUE_CONSTRAINT_MODULE_2,
    Feature.UNIQUE_CONSTRAINT_MODULE_3,
    Feature.UNIQUE_CONSTRAINT_MODULE_4,
    Feature.UNIQUE_CONSTRAINT_MODULE_5,
    Feature.UNIQUE_CONSTRAINT_MODULE_6,
    Feature.UNIQUE_CONSTRAINT_MODULE_7,
    Feature.UNIQUE_CONSTRAINT_MODULE_8,
    Feature.UNIQUE_CONSTRAINT_MODULE_9,
    Feature.ASYNC_BIZ_MAGIC_MODULE_4,
    Feature.ASYNC_BIZ_MAGIC_MODULE_3,
    Feature.ASYNC_BIZ_MAGIC_MODULE_2,
    Feature.ASYNC_BIZ_MAGIC_MODULE_5,
    Feature.ASYNC_BIZ_MAGIC_MODULE_9,
    Feature.SR_ADDS_STATION,
    Feature.CHECK_DUPLICATES_UPLOAD,
    Feature.DATABASE_CENTRAL_CONFIG
}

@pytest.fixture
def s3_client():
    with mock_aws():
        conn = boto3.resource("s3", region_name="us-east-1")
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=upload_bucket_name)

        conn.Bucket(upload_bucket_name).put_object(
            Key=upload_key,
            Body=get_file_content(upload_file_path),
            Metadata={"checksum": upload_checksum, "recipient_type": "direct-recipient"},
        )

        conn.Bucket(upload_bucket_name).put_object(
            Key=s2s_upload_key,
            Body=get_file_content(upload_file_path),
            Metadata={
                "checksum": upload_checksum,
                "recipient_type": "direct-recipient",
                "s2s_upload": "True",
            },
        )

        conn.Bucket(upload_bucket_name).put_object(
            Key=invalid_file_upload_key,
            Body=get_file_content(invalid_file_path),
            Metadata={"checksum": upload_checksum, "recipient_type": "direct-recipient"},
        )

        yield conn


@pytest.fixture
def mock_boto3_manager_s3(s3_client):
    with patch.object(Boto3Manager, "resource", return_value=s3_client) as mock_client:
        yield mock_client


def get_file_content(file_path):
    with open(file_path, "rb") as f:
        return f.read()


def get_event_object(key):
    body = json.dumps(
        {"key": f"{key}", "bucket": "ev-chart-artifact-data-unit-test", "recipient_type": "test"}
    )
    event_object = {
        "Records": [
            {
                "messageId": "51248983-6efb-45b0-9cda-f46361fa9d72",
                "receiptHandle": "AQEBqCbgdpKlmJL40F05hhpnE1xeptUFxy",
                "body": body,
                "attributes": {
                    "ApproximateReceiveCount": "103",
                    "AWSTraceHeader": "Root=1-668eec57-5e679a8a2d0a16b4648ed22a;Parent=6c23033f58bdb3e0;Sampled=0;Lineage=55dd22b6:0",
                    "SentTimestamp": "1720642650042",
                    "SequenceNumber": "18887228592120303616",
                    "MessageGroupId": "file-integrity",
                    "SenderId": "AIDAYRRVD2ENU4DSO2WBX",
                    "MessageDeduplicationId": "45afed0266b31e646042a6ba6df527f9f56fd03ffffe2394a25bc26c0daf1393",
                    "ApproximateFirstReceiveTimestamp": "1720642650042",
                },
                "messageAttributes": {
                    "file-integrity": {
                        "stringValue": "passed",
                        "stringListValues": [],
                        "binaryListValues": [],
                        "dataType": "String",
                    }
                },
                "md5OfBody": "4e526238faa82b32acce4a960b3ce94b",
                "md5OfMessageAttributes": "ff166bff27dc389fd27095b28acb74b8",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:414275662771:evchart-file-integrity.fifo",
                "awsRegion": "us-east-1",
            }
        ]
    }
    return event_object


upload_id_metadata = {
    "comments": None,
    "module_id": "8",
    "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    "quarter": "",
    "submission_status": "Processing",
    "upload_id": "852ade96-4075-4766-9b97-5e9379b31ab0",
    "upload_friendly_id": 44,
    "updated_by": "joshua.theisen@ee.doe.gov",
    "updated_on": datetime.datetime(2024, 7, 12, 19, 25, 38),
    "year": "2024",
}

s2s_upload_id_metadata = {
    "comments": None,
    "module_id": "8",
    "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    "quarter": "",
    "submission_status": "Processing",
    "upload_id": "952ade96-4075-4766-9b97-5e9379b31ab2",
    "upload_friendly_id": 44,
    "updated_by": "joshua.theisen@ee.doe.gov",
    "updated_on": datetime.datetime(2024, 7, 12, 19, 25, 38),
    "year": "2024",
}


def test_get_dataframe_from_csv_returns_df():
    filename = "port_id_empty_value_mod_2.csv"
    df = None
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
        df = get_dataframe_from_csv(body)

    assert df is not None


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("AsyncDataValidation.index.unique_constraint_violations_for_async")
@patch("AsyncDataValidation.index.aurora")
@patch("AsyncDataValidation.index.get_upload_metadata")
@patch("AsyncDataValidation.index.insert_errors_to_table")
@patch("AsyncDataValidation.index.send_sns_message")
@patch("module_validation.stations_not_active")  # called in validate_station_id
@patch("module_validation.get_station_uuid")  # called in validate_station_id
@patch("module_validation.metadata_update_validation_status")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_active_feature_toggles")
def test_handler_given_valid_s3_object_return_201(
    mock_feature_toggle,
    mock_module_validation,
    mock_get_station_uuid,
    mock_stations_not_active,
    mock_insert_errors_to_table,
    mock_send_sns_message,
    mock_get_upload_metadata,
    mock_aurora,
    mock_unique_constraint_violations_for_async,
    mock_boto3_manager_s3,
):
    mock_feature_toggle.return_value = ft_set
    mock_get_upload_metadata.return_value = upload_id_metadata
    mock_insert_errors_to_table.return_value = upload_id_metadata
    mock_get_station_uuid.return_value = "123"
    event_object = get_event_object(upload_key)
    results = handler(event_object, "context")

    assert results["statusCode"] == 201
    assert mock_aurora.get_connection.called
    assert mock_unique_constraint_violations_for_async.called


@patch("AsyncDataValidation.index.aurora")
@patch("AsyncDataValidation.index.get_upload_metadata")
@patch("AsyncDataValidation.index.insert_errors_to_table")
@patch("AsyncDataValidation.index.send_sns_message")
@patch("module_validation.stations_not_active")  # called in validate_station_id
@patch("module_validation.get_station_uuid")  # called in validate_station_id
@patch("module_validation.metadata_update_validation_status")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
@patch("AsyncDataValidation.index.FeatureToggleService.get_active_feature_toggles")
def test_handler_given_invalid_s3_object_return_200(
    mock_feature_toggle,
    mock_module_validation,
    mock_get_station_uuid,
    mock_stations_not_active,
    mock_send_sns_message,
    mock_insert_errors_to_table,
    mock_get_upload_metadata,
    mock_aurora,
    mock_boto3_manager_s3,
):
    mock_feature_toggle.return_value = ft_set
    mock_get_upload_metadata.return_value = upload_id_metadata
    mock_insert_errors_to_table.return_value = upload_id_metadata
    mock_get_station_uuid.return_value = "123"
    # Set to invalid record
    event_object = get_event_object(invalid_file_upload_key)
    results = handler(event_object, "context")
    body = json.loads(results["body"])
    error_count = body.get("error_count")

    assert results["statusCode"] == 200
    assert error_count > 0
    assert mock_aurora.get_connection.called

@patch("AsyncDataValidation.index.unique_constraint_violations_for_async")
@patch("AsyncDataValidation.index.aurora")
@patch("AsyncDataValidation.index.get_upload_metadata")
@patch("AsyncDataValidation.index.insert_errors_to_table")
@patch("AsyncDataValidation.index.send_sns_message")
@patch("module_validation.stations_not_active")  # called in validate_station_id
@patch("module_validation.get_station_uuid")  # called in validate_station_id
@patch("module_validation.metadata_update_validation_status")
@patch("AsyncDataValidation.index.FeatureToggleService.get_active_feature_toggles")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_handler_given_valid_s3_object_with_s2s_upload_true_return_201(
    mock_feature_toggle,
    mock_module_validation,
    mock_get_station_uuid,
    mock_stations_not_active,
    mock_insert_errors_to_table,
    mock_send_sns_message,
    mock_get_upload_metadata,
    mock_aurora,
    mock_unique_constraint_violations_for_async,
    mock_boto3_manager_s3,
):
    mock_feature_toggle.return_value = ft_set
    mock_get_upload_metadata.return_value = s2s_upload_id_metadata
    mock_insert_errors_to_table.return_value = s2s_upload_id_metadata
    mock_get_station_uuid.return_value = "123"
    mock_unique_constraint_violations_for_async.return_value = {"errors": [], "df": None}
    event_object = get_event_object(s2s_upload_key)
    results = handler(event_object, "context")

    assert results["statusCode"] == 201
    assert mock_aurora.get_connection.called
    assert mock_unique_constraint_violations_for_async.called

@patch("AsyncDataValidation.index.unique_constraint_violations_for_async")
@patch("AsyncDataValidation.index.aurora")
@patch("AsyncDataValidation.index.get_upload_metadata")
@patch("AsyncDataValidation.index.insert_errors_to_table")
@patch("AsyncDataValidation.index.send_sns_message")
@patch("module_validation.stations_not_active")  # called in validate_station_id
@patch("module_validation.get_station_uuid")  # called in validate_station_id
@patch("module_validation.metadata_update_validation_status")
@patch("AsyncDataValidation.index.FeatureToggleService.get_active_feature_toggles")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_handler_given_valid_s3_object_with_s2s_upload_true_and_constraints_fail_return_200(
    mock_feature_toggle,
    mock_module_validation,
    mock_get_station_uuid,
    mock_stations_not_active,
    mock_insert_errors_to_table,
    mock_send_sns_message,
    mock_get_upload_metadata,
    mock_aurora,
    mock_unique_constraint_violations_for_async,
    mock_boto3_manager_s3,
):
    df = pandas.DataFrame()
    mock_feature_toggle.return_value = ft_set
    mock_get_upload_metadata.return_value = s2s_upload_id_metadata
    mock_insert_errors_to_table.return_value = s2s_upload_id_metadata
    mock_get_station_uuid.return_value = "123"
    mock_unique_constraint_violations_for_async.return_value = {"errors": ['an error'], "df": df}
    event_object = get_event_object(s2s_upload_key)
    results = handler(event_object, "context")

    body = json.loads(results["body"])
    error_count = body.get("error_count")

    assert results["statusCode"] == 200
    assert error_count > 0
    assert mock_aurora.get_connection.called
    assert mock_unique_constraint_violations_for_async.called


@patch("AsyncDataValidation.index.validated_dataframe_by_module_id")
@patch("AsyncDataValidation.index.unique_constraint_violations_for_async")
@patch("AsyncDataValidation.index.aurora")
@patch("AsyncDataValidation.index.get_upload_metadata")
@patch("AsyncDataValidation.index.insert_errors_to_table")
@patch("AsyncDataValidation.index.send_sns_message")
@patch("module_validation.stations_not_active")  # called in validate_station_id
@patch("module_validation.get_station_uuid")  # called in validate_station_id
@patch("module_validation.metadata_update_validation_status")
@patch("AsyncDataValidation.index.FeatureToggleService.get_active_feature_toggles")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_handler_given_invalid_s3_object_with_s2s_upload_does_not_check_constraints(
    mock_feature_toggle,
    mock_module_validation,
    mock_get_station_uuid,
    mock_stations_not_active,
    mock_insert_errors_to_table,
    mock_send_sns_message,
    mock_get_upload_metadata,
    mock_aurora,
    mock_unique_constraint_violations_for_async,
    mock_validated_dataframe_by_module_id,
    mock_boto3_manager_s3,
):
    df = pandas.DataFrame()
    mock_feature_toggle.return_value = ft_set
    mock_get_upload_metadata.return_value = s2s_upload_id_metadata
    mock_insert_errors_to_table.return_value = s2s_upload_id_metadata
    mock_get_station_uuid.return_value = "123"
    mock_validated_dataframe_by_module_id.return_value = {"conditions": ['an error'], "df": df}
    event_object = get_event_object(s2s_upload_key)
    results = handler(event_object, "context")

    body = json.loads(results["body"])
    error_count = body.get("error_count")

    assert results["statusCode"] == 200
    assert error_count > 0
    assert mock_aurora.get_connection.called
    assert not mock_unique_constraint_violations_for_async.called

@patch("AsyncDataValidation.index.aurora")
@patch("AsyncDataValidation.index.get_upload_metadata")
@patch("AsyncDataValidation.index.insert_errors_to_table")
@patch("AsyncDataValidation.index.send_sns_message")
@patch("module_validation.get_station_uuid")  # called in validate_station_id
@patch("module_validation.metadata_update_validation_status")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
@patch("AsyncDataValidation.index.FeatureToggleService.get_active_feature_toggles")
def test_handler_given_invalid_s3_object_send_failed_validation_message(
    mock_feature_toggle,
    mock_module_validation,
    mock_get_station_uuid,
    mock_send_sns_message,
    mock_insert_errors_to_table,
    mock_get_upload_metadata,
    mock_aurora,
    mock_boto3_manager_s3,
):
    mock_feature_toggle.return_value = ft_set
    mock_get_upload_metadata.return_value = upload_id_metadata
    mock_insert_errors_to_table.return_value = upload_id_metadata
    mock_get_station_uuid.return_value = "123"
    # Set to invalid record
    event_object = get_event_object(invalid_file_upload_key)
    handler(event_object, "context")
    args, _ = mock_send_sns_message.call_args
    assert args[0].get("data-validation") == "failed"


@patch("AsyncDataValidation.index.get_upload_metadata")
@patch("AsyncDataValidation.index.insert_errors_to_table")
@patch("AsyncDataValidation.index.send_sns_message")
@patch("module_validation.get_station_uuid")  # called in validate_station_id
@patch("module_validation.metadata_update_validation_status")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_handler_failed_to_connect_to_aurora_return_500(
    mock_feature_toggle,
    mock_module_validation,
    mock_get_station_uuid,
    mock_send_sns_message,
    mock_insert_errors_to_table,
    mock_get_upload_metadata,
    mock_boto3_manager_s3,
):
    mock_feature_toggle.return_value = ft_set
    mock_get_upload_metadata.return_value = upload_id_metadata
    mock_insert_errors_to_table.return_value = upload_id_metadata
    mock_get_station_uuid.return_value = "123"

    # Set to invalid record
    event_object = get_event_object(invalid_file_upload_key)
    results = handler(event_object, "context")

    body = results["body"]
    assert results["statusCode"] == 500
    assert "EvChartDatabaseHandlerConnectionError" in body



@patch("AsyncDataValidation.index.unique_constraint_violations_for_async")
def test_enforce_constraints_for_s2s_given_s2s_false_do_nothing(
    mock_unique_constraint_violations_for_async,
):
    is_s2s = False
    cursor = MagicMock()
    log_event = MagicMock()
    upload_id = handler(mock_unique_constraint_violations_for_async, "context")
    df = pandas.DataFrame()
    dr_id = 1
    module_id = 5

    enforce_constraints_for_s2s(is_s2s, cursor, log_event, upload_id, dr_id, df, module_id)
    assert not mock_unique_constraint_violations_for_async.called


@patch("AsyncDataValidation.index.unique_constraint_violations_for_async")
def test_enforce_constraints_for_s2s_given_s2s_true_calls_unique_constraints_violations(
    mock_unique_constraint_violations_for_async,
):
    is_s2s = True
    cursor = MagicMock()
    log_event = MagicMock()
    upload_id = handler(mock_unique_constraint_violations_for_async, "context")
    df = pandas.DataFrame()
    dr_id = 1
    module_id = 5

    enforce_constraints_for_s2s(is_s2s, cursor, log_event, upload_id, dr_id, df, module_id)
    assert mock_unique_constraint_violations_for_async.called


@patch("AsyncDataValidation.index.unique_constraint_violations_for_async")
def test_enforce_constraints_for_s2s_given_invalid_return_error_list(
    mock_unique_constraint_violations_for_async,
):
    df = pandas.DataFrame(
        data={
            "upload_id": ["b2_submitted", "b2_submitted", "b2_submitted", "c3_approved"],
            "station_uuid": ["123", "456", "789", "1001"],
            "station_id_upload": ["123", "456", "789", "1001"],
            "session_id": ["1", "4", "7", "11"],
            "port_id": ["1", "2", "3", "4"],
        }
    )

    errors = [
        {
            "error_description": "This is a duplicative record against upload a1_draft on fields port_id=3, session_id=7, station_id=789",
            "header_name": "N/A",
            "error_row": None,
        }
    ]

    mock_unique_constraint_violations_for_async.return_value = {"errors": errors, "df": None}

    is_s2s = True
    cursor = MagicMock()
    log_event = MagicMock()
    upload_id = "a1_draft"
    dr_id = 1
    module_id = 5

    errors = enforce_constraints_for_s2s(is_s2s, cursor, log_event, upload_id, dr_id, df, module_id)
    assert len(errors) == 1

def test_enforce_constraints_for_s2s_given_valid_return_empty_list():
    df = pandas.DataFrame(
        data={
            "upload_id": ["a1_draft", "a1_draft", "b2_submitted", "c3_approved"],
            "station_uuid": ["123", "456", "789", "1001"],
            "station_id_upload": ["1", "4", "7", "11"],
            "favorite_color": ["red", "green", "blue", "purple"],
        }
    )

    is_s2s = True
    cursor = MagicMock()
    log_event = MagicMock()
    upload_id = handler(df, "context")
    dr_id = 1
    module_id = 5
    errors = enforce_constraints_for_s2s(is_s2s, cursor, log_event, upload_id, dr_id, df, module_id)
    assert len(errors) == 0

@patch("AsyncDataValidation.index.unique_constraint_violations_for_async")
@patch("AsyncDataValidation.index.aurora")
@patch("AsyncDataValidation.index.get_upload_metadata")
@patch("AsyncDataValidation.index.insert_errors_to_table")
@patch("AsyncDataValidation.index.send_sns_message")
@patch("module_validation.stations_not_active")  # called in validate_station_id
@patch("module_validation.get_station_uuid")  # called in validate_station_id
@patch("module_validation.metadata_update_validation_status")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
@patch("AsyncDataValidation.index.FeatureToggleService.get_active_feature_toggles")
def test_enforce_s2s(
    mock_feature_toggle,
    mock_module_validation,
    mock_get_station_uuid,
    mock_stations_not_active,
    mock_insert_errors_to_table,
    mock_send_sns_message,
    mock_get_upload_metadata,
    mock_aurora,
    mock_unique_constraint_violations_for_async,
    mock_boto3_manager_s3,
):
    mock_feature_toggle.return_value = ft_set
    mock_get_upload_metadata.return_value = upload_id_metadata
    mock_insert_errors_to_table.return_value = upload_id_metadata
    mock_get_station_uuid.return_value = "123"
    event_object = get_event_object(upload_key)
    results = handler(event_object, "context")

    assert results["statusCode"] == 201
    assert mock_aurora.get_connection.called
