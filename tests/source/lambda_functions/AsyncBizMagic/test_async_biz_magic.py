import datetime
import json
import os
from unittest.mock import MagicMock, patch

import boto3
import pandas
import pytest

from database_central_config import DatabaseCentralConfig
from AsyncBizMagic.index import (
    handler as async_biz_magic,
    insert_errors_to_table,
    upload_transform_df,
    set_datatype
)
from moto import mock_aws
from async_utility.s3_manager import get_s3_data
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import (
    EvChartAsynchronousS3Error,
    EvChartInvalidCSVError
)
import feature_toggle
from feature_toggle.feature_enums import Feature
from module_validation import load_module_definitions
from AsyncDataValidation.index import get_dataframe_from_csv


UPLOAD_FILE_PATH = "./tests/sample_data/all_columns_module_9.csv"
UPLOAD_CHECKSUM = \
    "0d810e7fbf2f435b93a7b51d26e7df28e3b8747a322a33dcf2a4db8dbae63ce0"
UPLOAD_KEY = "upload/Joint Office/852ade96-4075-4766-9b97-5e9379b31ab0.csv"
UPLOAD_BUCKET_NAME = "ev-chart-artifact-data-unit-test"
#JSON_UPLOAD_FILE_PATH = "./tests/sample_data/evchart_valid_all_columns_module_4_10_records.csv"
UPLOAD_KEY_M4 = "upload/Joint Office/852ade96-9b97-9b97-9b97-5e9379b31ab0.csv"
UPLOAD_KEY_M2 = "upload/Joint Office/852ade96-4766-4766-4766-5e9379b31ab0.csv"
UPLOAD_KEY_M2_HAPPY = "upload/Joint Office/852ade96-2222-2222-2222-5e9379b31ab0.csv"
UPLOAD_KEY_M2_INVALID_TIMES = "upload/Joint Office/852ade96-1111-1111-1111-5e9379b31ab0.csv"
UPLOAD_FILE_PATH_M4 = "./tests/sample_data/biz_magic_not_all_empty_mod_4.csv"
UPLOAD_FILE_PATH_M2 = "./tests/sample_data/biz_magic_not_all_empty_mod_2.csv"
UPLOAD_FILE_PATH_M2_HAPPY = "./tests/sample_data/valid_mod2_biz_magic_np.csv"
UPLOAD_FILE_PATH_M2_INVALID_TIMES = "./tests/sample_data/biz_magic_m2_invalid_start_after_end.csv"

INVALID_FILE_UPLOAD_ID = "all_invalid_data_type_mod_9.csv"
INVALID_FILE_PATH = "./tests/sample_data/all_invalid_data_type_mod_9.csv"

valid_modules_with_required_fields_only = [
    "all_required_module_2.csv",
    "all_required_mod_3.csv",
    "evchart_valid_all_required_module_4.csv",
    "all_required_module_5.csv",
    "all_required_module_6.csv",
    "all_required_mod_7.csv",
    "all_required_module_8.csv",
    "all_required_module_9.csv",
]

mock_custom_validation_module_9 = MagicMock(return_value={'conditions': []})

@pytest.fixture(name='s3_client')
def fixture_s3_client():
    with mock_aws():
        conn = boto3.resource("s3", region_name="us-east-1")
        # We need to create the bucket since
        # this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=UPLOAD_BUCKET_NAME)

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY,
            Body=get_file_content(UPLOAD_FILE_PATH),
            Metadata={
                "checksum": UPLOAD_CHECKSUM,
                "recipient_type": "direct-recipient"
            },
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY_M4,
            Body=get_file_content(UPLOAD_FILE_PATH_M4),
            Metadata={
                "checksum": UPLOAD_CHECKSUM,
                "recipient_type": "direct-recipient"
            },
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY_M2,
            Body=get_file_content(UPLOAD_FILE_PATH_M2),
            Metadata={
                "checksum": UPLOAD_CHECKSUM,
                "recipient_type": "direct-recipient"
            },
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY_M2_INVALID_TIMES,
            Body=get_file_content(UPLOAD_FILE_PATH_M2_INVALID_TIMES),
            Metadata={
                "checksum": UPLOAD_CHECKSUM,
                "recipient_type": "direct-recipient"
            },
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY_M2_HAPPY,
            Body=get_file_content(UPLOAD_FILE_PATH_M2_HAPPY),
            Metadata={
                "checksum": UPLOAD_CHECKSUM,
                "recipient_type": "direct-recipient"
            },
        )

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=INVALID_FILE_UPLOAD_ID,
            Body=get_file_content(INVALID_FILE_PATH),
            Metadata={
                "checksum": UPLOAD_CHECKSUM,
                "recipient_type": "direct-recipient"
            },
        )

        yield conn


@pytest.fixture(name='mock_boto3_manager_s3')
def fixture_mock_boto3_manager_s3(s3_client):
    with patch.object(
        Boto3Manager, "resource", return_value=s3_client
    ) as mock_client:
        yield mock_client


def get_file_content(file_path):
    with open(file_path, "rb") as f:
        return f.read()


def get_event_object(key):
    body = json.dumps({
        "key": key,
        "bucket": "ev-chart-artifact-data-unit-test",
        "recipient_type": "test"
    })
    event_object = {
        "Records": [
            {
                "messageId": "51248983-6efb-45b0-9cda-f46361fa9d72",
                "receiptHandle": "AQEBqCbgdpKlmJL40F05hhpnE1xeptUFxy",
                "body": body,
                "attributes": {
                    "ApproximateReceiveCount": "103",
                    "AWSTraceHeader": (
                        "Root=1-668eec57-5e679a8a2d0a16b4648ed22a;"
                        "Parent=6c23033f58bdb3e0;Sampled=0;"
                        "Lineage=55dd22b6:0"
                    ),
                    "SentTimestamp": "1720642650042",
                    "SequenceNumber": "18887228592120303616",
                    "MessageGroupId": "data-validation",
                    "SenderId": "AIDAYRRVD2ENU4DSO2WBX",
                    "MessageDeduplicationId": (
                        "45afed0266b31e646042a6ba6df527f9"
                        "f56fd03ffffe2394a25bc26c0daf1393"
                    ),
                    "ApproximateFirstReceiveTimestamp": "1720642650042",
                },
                "messageAttributes": {
                    "data-validation": {
                        "stringValue": "passed",
                        "stringListValues": [],
                        "binaryListValues": [],
                        "dataType": "String",
                    }
                },
                "md5OfBody": "4e526238faa82b32acce4a960b3ce94b",
                "md5OfMessageAttributes": "ff166bff27dc389fd27095b28acb74b8",
                "eventSource": "aws:sqs",
                "eventSourceARN": (
                    "arn:aws:sqs:us-east-1:414275662771:"
                    "evchart-data-validation.fifo"
                ),
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


# helper function used in all the tests to load the csv file from sample data folder
# and correctly set the station_uuid as the system would before entering data validation
def get_df_from_sample_data_csv(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
        async_df = get_dataframe_from_csv(body)
        async_df['station_uuid'] = "temp_uuid"
    return async_df


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
def test_null_args_error_state(mock_get_active_feature_toggles):
    response = async_biz_magic({'Records': []}, "context")
    assert response.get('statusCode') == 500
    assert mock_get_active_feature_toggles.called


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
def test_aurora_fail(mock_get_active_feature_toggles):
    response = async_biz_magic({'Records': [None]}, "context")
    assert response.get('statusCode') == 500
    assert mock_get_active_feature_toggles.called


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.get_org_info_dynamo")
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_happy_path(
    mock_aurora,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_get_org_info,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3
):
    mock_get_active_feature_toggles.return_value = {Feature.BIZ_MAGIC}
    mock_get_org_info.return_value = {"name": "Org Name"}
    event_object = get_event_object(UPLOAD_KEY)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()

    response = async_biz_magic(event_object, None)
    assert response.get('statusCode') == 201

    execute_args, _ = mock_send_sns_message.call_args
    sns_attributes = execute_args[0]
    sns_message = execute_args[1]
    assert sns_attributes.get("biz-magic") == "passed"
    assert sns_message.get("key") == \
        "transformed/Org Name/852ade96-4075-4766-9b97-5e9379b31ab0.json"
    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_send_sns_message_fail(
    mock_aurora,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3
):
    event_object = get_event_object(UPLOAD_KEY)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    mock_send_sns_message.return_value = False

    response = async_biz_magic(event_object, None)
    assert len(response.get('batchItemFailures', [])) > 0
    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called
    assert mock_get_active_feature_toggles.called


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_upload_metadata_none(
    mock_aurora,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3
):
    event_object = get_event_object(UPLOAD_KEY)
    mock_get_upload_metadata.return_value = None

    response = async_biz_magic(event_object, None)
    assert response.get('statusCode') == 500
    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called
    assert mock_send_sns_message.called
    assert mock_get_active_feature_toggles.called


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.aurora")
def test_aurora_non_db_error(
    mock_aurora,
    mock_get_active_feature_toggles
):
    event_object = get_event_object(UPLOAD_KEY)
    mock_aurora.get_connection.side_effect = ZeroDivisionError

    with pytest.raises(ZeroDivisionError):
        _ = async_biz_magic(event_object, None)
    assert mock_get_active_feature_toggles.called


@patch.dict(
    "AsyncBizMagic.index.custom_validations",
    {9: [mock_custom_validation_module_9]}
)
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.get_org_info_dynamo")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_feature_toggle(
    # pylint: disable=too-many-positional-arguments,too-many-arguments
    mock_aurora,
    mock_get_org_info,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3
):
    event_object = get_event_object(UPLOAD_KEY)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    mock_get_active_feature_toggles.return_value = {Feature.ASYNC_BIZ_MAGIC_MODULE_9}
    mock_get_org_info.return_value = {"name": "Org Name"}

    response = async_biz_magic(event_object, None)
    assert response.get('statusCode') == 201

    execute_args, _ = mock_custom_validation_module_9.call_args
    validation_options = execute_args[0]
    assert Feature.ASYNC_BIZ_MAGIC_MODULE_9 in \
        validation_options.get('feature_toggle_set')
    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called
    assert mock_send_sns_message.called


def test_coverage_upload_transform_df_raised_error(mock_boto3_manager_s3):
    with pytest.raises(EvChartAsynchronousS3Error):
        upload_transform_df(
            bucket="bucket_that_does_not_exist",
            upload_id="upload_id",
            recipient_type="direct-recipient",
            df=pandas.DataFrame(),
            new_file_name="file_path",
            s2s_upload = False
        )

    assert mock_boto3_manager_s3.called

def test_coverage_upload_transform_df_with_s2s_upload(mock_boto3_manager_s3):
    key = "my_file_name"
    upload_transform_df(
        bucket=UPLOAD_BUCKET_NAME,
        upload_id="upload_id",
        recipient_type="direct-recipient",
        df=pandas.DataFrame(),
        new_file_name=key,
        s2s_upload= "True"
    )

    _, s3_metadata = get_s3_data(UPLOAD_BUCKET_NAME, key)
    assert "s2s_upload" in s3_metadata
    assert s3_metadata["s2s_upload"] == 'True'
    assert mock_boto3_manager_s3.called

def test_coverage_upload_transform_df_with_False_s2s_upload(mock_boto3_manager_s3):
    key = "my_file_name"
    upload_transform_df(
        bucket=UPLOAD_BUCKET_NAME,
        upload_id="upload_id",
        recipient_type="direct-recipient",
        df=pandas.DataFrame(),
        new_file_name=key,
        s2s_upload= False
    )

    _, s3_metadata = get_s3_data(UPLOAD_BUCKET_NAME, key)
    assert "s2s_upload" not in s3_metadata
    assert mock_boto3_manager_s3.called


@patch("AsyncBizMagic.index.error_table_insert")
def test_coverage_insert_errors_to_table(mock_error_table_insert):
    with pytest.raises(EvChartInvalidCSVError):
        metadata = {
            'upload_id': 'upload_id',
            'module_id': 9,
            'org_id': 'org1',
            'parent_org': 'org2'
        }
        insert_errors_to_table(MagicMock(), [None], metadata, None)
    assert mock_error_table_insert.called


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.get_org_info_dynamo")
@patch("AsyncBizMagic.index.error_table_insert")
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_happy_path_biz_magic_4(
    mock_aurora,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_error_table_insert,
    mock_get_org_info,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3
):
    mock_error_table_insert.return_value = "True"
    mock_get_active_feature_toggles.return_value = {
        Feature.BIZ_MAGIC, Feature.ASYNC_BIZ_MAGIC_MODULE_4
    }
    mock_get_org_info.return_value = {"name": "Org Name"}
    event_object = get_event_object(UPLOAD_KEY_M4)
    metadata = get_upload_id_metadata()
    metadata["module_id"] = "4"
    mock_get_upload_metadata.return_value = metadata

    response = async_biz_magic(event_object, None)
    assert response.get('statusCode') == 406
    assert mock_aurora.get_connection.called
    assert mock_send_sns_message.called
    assert mock_boto3_manager_s3.called


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.get_org_info_dynamo")
@patch("AsyncBizMagic.index.error_table_insert")
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_unhappy_path_biz_magic_2(
    mock_aurora,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_error_table_insert,
    mock_get_org_info,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3
):
    mock_error_table_insert.return_value = "True"
    mock_get_active_feature_toggles.return_value = {
        Feature.BIZ_MAGIC, Feature.ASYNC_BIZ_MAGIC_MODULE_2
    }
    mock_get_org_info.return_value = {"name": "Org Name"}
    event_object = get_event_object(UPLOAD_KEY_M2)
    metadata = get_upload_id_metadata()
    metadata["module_id"] = "2"
    mock_get_upload_metadata.return_value = metadata

    response = async_biz_magic(event_object, None)
    assert response.get('statusCode') == 406
    assert mock_aurora.get_connection.called
    assert mock_send_sns_message.called
    assert mock_boto3_manager_s3.called


# Test to validate JE-6272
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.get_org_info_dynamo")
@patch("AsyncBizMagic.index.error_table_insert")
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_happy_path_biz_magic_2(
    mock_aurora,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_error_table_insert,
    mock_get_org_info,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3
):
    mock_error_table_insert.return_value = "True"
    mock_get_active_feature_toggles.return_value = {
        Feature.BIZ_MAGIC, Feature.ASYNC_BIZ_MAGIC_MODULE_2
    }
    mock_get_org_info.return_value = {"name": "Org Name"}
    event_object = get_event_object(UPLOAD_KEY_M2_HAPPY)
    metadata = get_upload_id_metadata()
    metadata["module_id"] = "2"
    mock_get_upload_metadata.return_value = metadata

    response = async_biz_magic(event_object, None)
    assert response.get('statusCode') == 201
    assert mock_aurora.get_connection.called
    assert mock_send_sns_message.called
    assert mock_boto3_manager_s3.called

# Test to validate JE-6508
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.get_org_info_dynamo")
@patch("AsyncBizMagic.index.error_table_insert")
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_biz_magic_2_duration_less_than_zero_returns_201(
    mock_aurora,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_error_table_insert,
    mock_get_org_info,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3
):
    mock_error_table_insert.return_value = "True"
    mock_get_active_feature_toggles.return_value = {
        Feature.BIZ_MAGIC, Feature.ASYNC_BIZ_MAGIC_MODULE_2
    }
    mock_get_org_info.return_value = {"name": "Org Name"}
    event_object = get_event_object(UPLOAD_KEY_M2_INVALID_TIMES)
    metadata = get_upload_id_metadata()
    metadata["module_id"] = "2"
    mock_get_upload_metadata.return_value = metadata

    response = async_biz_magic(event_object, None)
    assert response.get('statusCode') == 201
    assert mock_aurora.get_connection.called
    assert mock_send_sns_message.called
    assert mock_boto3_manager_s3.called


@pytest.fixture(name="cc_config")
def fixture_config():
    return DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json"
        )
    )


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("module_transform.transform_m9.DatabaseCentralConfig")
@patch("AsyncBizMagic.index.DatabaseCentralConfig")
@patch("AsyncBizMagic.index.get_org_info_dynamo")
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_central_config_ft_true(
    mock_aurora,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_get_org_info,
    mock_database_central_config,
    mock_m9_transform_cc,
    mock_get_active_feature_toggles,
    cc_config,
    mock_boto3_manager_s3
):
    mock_m9_transform_cc.return_value = cc_config
    mock_get_active_feature_toggles.return_value = {
        Feature.BIZ_MAGIC, Feature.DATABASE_CENTRAL_CONFIG
    }
    mock_get_org_info.return_value = {"name": "Org Name"}
    event_object = get_event_object(UPLOAD_KEY)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()

    response = async_biz_magic(event_object, None)
    assert response.get('statusCode') == 201

    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called
    assert mock_send_sns_message.called
    assert mock_database_central_config.called


@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("AsyncBizMagic.index.DatabaseCentralConfig")
@patch("AsyncBizMagic.index.get_org_info_dynamo")
@patch("AsyncBizMagic.index.send_sns_message")
@patch("AsyncBizMagic.index.get_upload_metadata")
@patch("AsyncBizMagic.index.aurora")
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_central_config_ft_false(
    mock_aurora,
    mock_get_upload_metadata,
    mock_send_sns_message,
    mock_get_org_info,
    mock_database_central_config,
    mock_get_active_feature_toggles,
    mock_boto3_manager_s3
):
    mock_get_active_feature_toggles.return_value = {Feature.BIZ_MAGIC}
    mock_get_org_info.return_value = {"name": "Org Name"}
    event_object = get_event_object(UPLOAD_KEY)
    mock_get_upload_metadata.return_value = get_upload_id_metadata()

    response = async_biz_magic(event_object, None)
    assert response.get('statusCode') == 201

    assert mock_aurora.get_connection.called
    assert mock_boto3_manager_s3.called
    assert mock_send_sns_message.called
    assert not mock_database_central_config.called

# JE-6765 Ensuring that modules with no recommended fields can still go through bizmagic workflow
@pytest.mark.parametrize("module_id", ["2","3","4","5","6","7","8","9"])
@pytest.mark.parametrize("filename", valid_modules_with_required_fields_only)
@patch("AsyncBizMagic.index.DatabaseCentralConfig")
def test_set_datatype_central_config_true_modules_with_required_fields_only(mock_database_central_config, filename, module_id, cc_config):
    mock_database_central_config.return_value = cc_config
    df = get_df_from_sample_data_csv(filename)
    feature_toggle_set = {Feature.DATABASE_CENTRAL_CONFIG}
    df = set_datatype(df, module_id, feature_toggle_set)
    assert df.equals(df)