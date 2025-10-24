import datetime
import json
from unittest.mock import patch

import boto3
import pytest
from AsyncValidatedUpload.index import handler
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartMissingOrMalformedBodyError,
    EvChartModuleValidationError,
)
from feature_toggle.feature_enums import Feature
from module_validation import load_module_definitions
from moto import mock_aws

UPLOAD_FILE_PATH_MOD_9 = "./tests/sample_data/all_columns_module_9.csv"
UPLOAD_KEY_MOD_9 = "upload/Joint Office/852ade96-4075-4766-9b97-5e9379b31ab0.csv"
UPLOAD_CHECKSUM = "0d810e7fbf2f435b93a7b51d26e7df28e3b8747a322a33dcf2a4db8dbae63ce0"
UPLOAD_BUCKET_NAME = "ev-chart-artifact-data-unit-test"

UPLOAD_FILE_PATH_MOD_2 = "./tests/sample_data/all_columns_module_2.csv"
UPLOAD_KEY_MOD_2 = "upload/Joint Office/852ade96-4075-4766-9b97-5e9379b31ab2.csv"

UPLOAD_FILE_PATH_MOD_3 = "./tests/sample_data/all_required_mod_3.csv"
UPLOAD_KEY_MOD_3 = "upload/Joint Office/852ade96-4075-4766-9b97-5e9379b31ab3.csv"

UPLOAD_FILE_PATH_MOD_4 = "./tests/sample_data/evchart_valid_all_required_module_4.csv"
UPLOAD_KEY_MOD_4 = "upload/Joint Office/852ade96-4075-4766-9b97-5e9379b31ab4.csv"

UPLOAD_JSON_KEY = "upload/Joint Office/852ade96-4075-4766-9b97-5e9379b31ab0.JSON"
UPLOAD_FILE_PATH_JSON = "./tests/sample_data/all_columns_module_4.json"

INVALID_FILE_UPLOAD_ID = "all_invalid_data_type_mod_9.csv"
INVALID_FILE_PATH = "./tests/sample_data/all_invalid_data_type_mod_9.csv"

ft_set = {
    Feature.MODULE_5_NULLS,
    Feature.BIZ_MAGIC,
}


@pytest.fixture
def s3_client():
    with mock_aws():
        conn = boto3.resource("s3", region_name="us-east-1")
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=UPLOAD_BUCKET_NAME)

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY_MOD_9,
            Body=get_file_content(UPLOAD_FILE_PATH_MOD_9),
            Metadata={"checksum": UPLOAD_CHECKSUM, "recipient_type": "direct-recipient"},
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY_MOD_2,
            Body=get_file_content(UPLOAD_FILE_PATH_MOD_2),
            Metadata={"checksum": UPLOAD_CHECKSUM, "recipient_type": "direct-recipient"},
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY_MOD_3,
            Body=get_file_content(UPLOAD_FILE_PATH_MOD_3),
            Metadata={"checksum": UPLOAD_CHECKSUM, "recipient_type": "direct-recipient"},
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY_MOD_4,
            Body=get_file_content(UPLOAD_FILE_PATH_MOD_4),
            Metadata={"checksum": UPLOAD_CHECKSUM, "recipient_type": "direct-recipient"},
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_JSON_KEY,
            Body=get_file_content(UPLOAD_FILE_PATH_JSON),
            Metadata={"checksum": UPLOAD_CHECKSUM, "recipient_type": "direct-recipient"},
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=INVALID_FILE_UPLOAD_ID,
            Body=get_file_content(INVALID_FILE_PATH),
            Metadata={"checksum": UPLOAD_CHECKSUM, "recipient_type": "direct-recipient"},
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
                    "AWSTraceHeader": (
                        "Root=1-668eec57-5e679a8a2d0a16b4648ed22a;Parent=6c23033f58bdb3e0;Sampled=0;Lineage=55dd22b6:0"
                    ),
                    "SentTimestamp": "1720642650042",
                    "SequenceNumber": "18887228592120303616",
                    "MessageGroupId": "data-validation",
                    "SenderId": "AIDAYRRVD2ENU4DSO2WBX",
                    "MessageDeduplicationId": (
                        "45afed0266b31e646042a6ba6df527f9f56fd03ffffe2394a25bc26c0daf1393"
                    ),
                    "ApproximateFirstReceiveTimestamp": "1720642650042",
                },
                "messageAttributes": {
                    "data-validation": {
                        "stringValue": "passed",
                        "stringListValues": [],
                        "binaryListValues": [],
                        "dataType": "String",
                    },
                    "file-type": {
                        "stringValue": "csv",
                        "stringListValues": [],
                        "binaryListValues": [],
                        "dataType": "String",
                    },
                },
                "md5OfBody": "4e526238faa82b32acce4a960b3ce94b",
                "md5OfMessageAttributes": "ff166bff27dc389fd27095b28acb74b8",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:414275662771:evchart-data-validation.fifo",
                "awsRegion": "us-east-1",
            }
        ]
    }
    return event_object


def get_upload_id_metadata(status="Processing"):
    upload_id_metadata = {
        "comments": None,
        "module_id": "9",
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "quarter": "",
        "submission_status": status,
        "upload_id": "852ade96-4075-4766-9b97-5e9379b31ab0",
        "upload_friendly_id": 44,
        "updated_by": "joshua.theisen@ee.doe.gov",
        "updated_on": datetime.datetime(2024, 7, 12, 19, 25, 38),
        "year": "2024",
    }
    return upload_id_metadata


def mock_set_station_id_func(df, dr_id, cursor, feature_toggle_set):
    df["station_uuid"] = "Unit_Test"
    return df


def mock_set_station_and_port_ids_func(df, cursor):
    df["station_uuid"] = "Unit_Test"
    df["network_provider_uuid"] = "np_uuid"
    df["port_uuid"] = "port_uuid"
    df["port_id_upload"] = "port_id"
    return df


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
def test_asyncvalidatedupload_handler_no_connection_to_rds_return_500(
    mock_get_active_feature_toggles,
):
    # mock_get_upload_metadata.return_value = upload_id_metadata
    event_object = get_event_object(UPLOAD_KEY_MOD_9)
    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert (
        "EvChartDatabaseHandlerConnectionError raised, unable to connect to RDS." in results["body"]
    )


@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
def test_asyncvalidatedupload_handler_failed_to_loaddefinitions_returns_500(
    mock_get_active_feature_toggles, mock_send_sns_message, mock_aurora
):
    mock_send_sns_message.return_value = "message_id"
    event_object = get_event_object(UPLOAD_KEY_MOD_9)
    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert "EvChartFileNotFoundError" in results["body"]
    assert mock_aurora.get_connection.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_failed_to_process_sns_message_returns_500(
    mock_send_sns_message, mock_aurora, mock_get_active_feature_toggles
):
    mock_send_sns_message.return_value = "message_id"
    event_object = get_event_object(UPLOAD_KEY_MOD_9)
    # deleting this triggers a key error
    del event_object["Records"][0]["body"]

    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert "EvChartSQSError" in results["body"]
    assert mock_aurora.get_connection.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@pytest.mark.skip("how to trigger an error?")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_failed_to_get_upload_id_from_s3_key_returns_500(
    mock_send_sns_message, mock_aurora, mock_get_active_feature_toggles
):
    mock_send_sns_message.return_value = "message_id"
    event_object = get_event_object(123)

    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert "EvChartSQSError" in results["body"]
    assert mock_aurora.get_connection.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_failed_to_connect_to_s3_returns_500(
    mock_send_sns_message, mock_aurora, mock_get_active_feature_toggles
):
    mock_send_sns_message.return_value = "message_id"
    event_object = get_event_object(UPLOAD_KEY_MOD_9)

    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert "EvChartS3GetObjectError" in results["body"]
    assert mock_aurora.get_connection.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_failed_to_get_s3_data_returns_500(
    mock_send_sns_message, mock_aurora, mock_get_active_feature_toggles, mock_boto3_manager_s3
):
    mock_send_sns_message.return_value = "message_id"
    event_object = get_event_object("invalid_key")

    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert "EvChartS3GetObjectError" in results["body"]
    assert mock_aurora.get_connection.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_dataframe_from_csv")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_get_dataframe_from_csv_returns_EvChartModuleValidationError(
    mock_get_dataframe_from_csv,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_send_sns_message.return_value = "message_id"
    mock_get_dataframe_from_csv.side_effect = EvChartModuleValidationError("")
    event_object = get_event_object(UPLOAD_KEY_MOD_9)

    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert "EvChartModuleValidationError" in results["body"]
    assert mock_aurora.get_connection.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_dataframe_from_csv")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_get_dataframe_from_csv_returns_EvChartMissingOrMalformedBodyError(
    mock_get_dataframe_from_csv,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_send_sns_message.return_value = "message_id"
    mock_get_dataframe_from_csv.side_effect = EvChartMissingOrMalformedBodyError(
        message="Unable to read csv:"
    )
    event_object = get_event_object(UPLOAD_KEY_MOD_9)

    results = handler(event_object, "context")

    assert results["statusCode"] == 406
    assert "EvChartMissingOrMalformedBodyError" in results["body"]
    assert mock_aurora.get_connection.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.drop_sample_rows")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_failed_to_drop_sample_rows_returns_500(
    mock_drop_sample_rows,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_send_sns_message.return_value = "message_id"
    mock_drop_sample_rows.side_effect = EvChartModuleValidationError(
        message="Error when attempting to drop sample rows"
    )
    event_object = get_event_object(UPLOAD_KEY_MOD_9)

    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert "EvChartModuleValidationError" in results["body"]
    assert mock_aurora.get_connection.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_failed_to_upload_data_from_df_returns_500(
    mock_data_already_exists_in_rds,
    mock_upload_data_from_df,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_get_active_feature_toggles.return_value = ft_set
    mock_send_sns_message.return_value = "message_id"
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    mock_upload_data_from_df.side_effect = EvChartDatabaseAuroraQueryError(
        message="Failed to submit data submission:"
    )
    mock_data_already_exists_in_rds.return_value = False
    event_object = get_event_object(UPLOAD_KEY_MOD_9)

    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert "EvChartDatabaseAuroraQueryError" in results["body"]
    assert mock_aurora.get_connection.called


@pytest.mark.skip("Still discussing required behavior")
@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
# @patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_failed_to_connect_to_sns_returns_500(
    mock_data_already_exists_in_rds,
    mock_upload_data_from_df,
    mock_get_upload_metadata,
    # mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    # mock_send_sns_message.return_value = "message_id"
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    # mock_upload_data_from_df.side_effect = EvChartDatabaseAuroraQueryError(message="Failed to submit data submission:")
    event_object = get_event_object(UPLOAD_KEY_MOD_9)
    mock_data_already_exists_in_rds.return_value = False
    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert "EvChartDatabaseAuroraQueryError" in results["body"]
    assert mock_aurora.get_connection.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch(
    "AsyncValidatedUpload.index.set_station_and_port_ids",
    side_effect=mock_set_station_and_port_ids_func,
)
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_given_upload_successful_return_201(
    mock_set_station_and_port_ids,
    mock_data_already_exists_in_rds,
    mock_upload_data_from_df,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_get_active_feature_toggles.return_value = ft_set
    event_object = get_event_object(UPLOAD_KEY_MOD_9)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    mock_data_already_exists_in_rds.return_value = False
    results = handler(event_object, "context")

    args, kwargs = mock_upload_data_from_df.call_args
    called_df = args[2]
    df_columns = called_df.columns
    assert results["statusCode"] == 201
    assert "upload_id" in df_columns
    assert "station_uuid" in df_columns


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_given_status_processing_and_data_already_uploaded_return_200_and_send_message(
    mock_data_already_exists_in_rds,
    mock_upload_data_from_df,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_data_already_exists_in_rds.return_value = True
    event_object = get_event_object(UPLOAD_KEY_MOD_9)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    results = handler(event_object, "context")

    assert results["statusCode"] == 200
    assert mock_send_sns_message.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch(
    "AsyncValidatedUpload.index.set_station_and_port_ids",
    side_effect=EvChartDatabaseAuroraQueryError(""),
)
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_given_failed_to_set_station_and_port_ids_return_500(
    _mock_set_station_and_port_ids,
    mock_data_already_exists_in_rds,
    _mock_upload_data_from_df,
    mock_get_upload_metadata,
    mock_send_sns_message,
    _mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_data_already_exists_in_rds.return_value = False
    event_object = get_event_object(UPLOAD_KEY_MOD_9)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    results = handler(event_object, "context")

    assert results["statusCode"] == 500
    assert mock_send_sns_message.called


def raise_error(exception):
    raise exception


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch(
    "AsyncValidatedUpload.index.set_station_and_port_ids",
    side_effect=mock_set_station_and_port_ids_func,
)
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_no_features_return_201_mod_9(
    mock_set_station_and_port_ids,
    mock_data_already_exists_in_rds,
    mock_upload_data_from_df,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_get_active_feature_toggles.return_value = ft_set
    event_object = get_event_object(UPLOAD_KEY_MOD_9)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    mock_data_already_exists_in_rds.return_value = False
    results = handler(event_object, "context")

    args, _ = mock_upload_data_from_df.call_args
    called_df = args[2]
    df_columns = called_df.columns
    assert results["statusCode"] == 201
    assert "upload_id" in df_columns
    assert "station_uuid" in df_columns
    # assert "network_provider_uuid" in df_columns

    assert mock_set_station_and_port_ids.called
    assert mock_send_sns_message.called
    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch(
    "AsyncValidatedUpload.index.set_station_and_port_ids",
    side_effect=mock_set_station_and_port_ids_func,
)
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_no_features_return_201_mod_2(
    mock_set_station_and_port_ids,
    mock_data_already_exists_in_rds,
    mock_upload_data_from_df,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_get_active_feature_toggles.return_value = ft_set
    event_object = get_event_object(UPLOAD_KEY_MOD_2)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    mock_data_already_exists_in_rds.return_value = False
    results = handler(event_object, "context")

    args, _ = mock_upload_data_from_df.call_args
    called_df = args[2]
    df_columns = called_df.columns
    assert results["statusCode"] == 201
    assert "upload_id" in df_columns
    assert "station_uuid" in df_columns
    assert "port_id_upload" in df_columns
    assert "port_uuid" in df_columns

    assert mock_set_station_and_port_ids.called
    assert mock_send_sns_message.called
    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch(
    "AsyncValidatedUpload.index.set_station_and_port_ids",
    side_effect=mock_set_station_and_port_ids_func,
)
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_no_features_return_201_mod_3(
    mock_set_station_and_port_ids,
    mock_data_already_exists_in_rds,
    mock_upload_data_from_df,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_get_active_feature_toggles.return_value = ft_set
    event_object = get_event_object(UPLOAD_KEY_MOD_3)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    mock_data_already_exists_in_rds.return_value = False
    results = handler(event_object, "context")

    args, _ = mock_upload_data_from_df.call_args
    called_df = args[2]
    df_columns = called_df.columns
    assert results["statusCode"] == 201
    assert "upload_id" in df_columns
    assert "station_uuid" in df_columns

    assert mock_send_sns_message.called
    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch(
    "AsyncValidatedUpload.index.set_station_and_port_ids",
    side_effect=mock_set_station_and_port_ids_func,
)
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_asyncvalidatedupload_handler_no_features_return_201_mod_4(
    mock_set_station_and_port_ids,
    mock_data_already_exists_in_rds,
    mock_upload_data_from_df,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_get_active_feature_toggles.return_value = ft_set
    event_object = get_event_object(UPLOAD_KEY_MOD_4)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    mock_data_already_exists_in_rds.return_value = False
    results = handler(event_object, "context")

    args, _ = mock_upload_data_from_df.call_args
    called_df = args[2]
    df_columns = called_df.columns
    assert results["statusCode"] == 201
    assert "upload_id" in df_columns
    assert "station_uuid" in df_columns

    assert mock_set_station_and_port_ids.called
    assert mock_send_sns_message.called
    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called


@patch("AsyncValidatedUpload.index.FeatureToggleService.get_active_feature_toggles")
@patch("AsyncValidatedUpload.index.aurora")
@patch("AsyncValidatedUpload.index.send_sns_message")
@patch("AsyncValidatedUpload.index.get_upload_metadata")
@patch("AsyncValidatedUpload.index.upload_data_from_df")
@patch("AsyncValidatedUpload.index.data_already_exists_in_rds")
@patch(
    "AsyncValidatedUpload.index.set_station_and_port_ids",
    side_effect=mock_set_station_and_port_ids_func,
)
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_json_asyncvalidatedupload_handler_given_upload_successful_return_201(
    _mock_set_station_and_port_ids,
    mock_data_already_exists_in_rds,
    mock_upload_data_from_df,
    mock_get_upload_metadata,
    _mock_send_sns_message,
    _mock_aurora,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3,
):
    mock_get_active_feature_toggles.return_value = ft_set
    event_object = get_event_object(UPLOAD_JSON_KEY)
    (event_object["Records"][0]["messageAttributes"]["file-type"]["stringValue"]) = "json"
    m4_metadata = get_upload_id_metadata()
    m4_metadata["module_id"] = "4"
    mock_get_upload_metadata.return_value = m4_metadata
    mock_data_already_exists_in_rds.return_value = False
    results = handler(event_object, "context")

    _, kwargs = mock_upload_data_from_df.call_args
    assert results["statusCode"] == 201
    assert "upload_id" in kwargs.get("df")
    assert "station_uuid" in kwargs.get("df")
    assert kwargs.get("check_boolean") is False
