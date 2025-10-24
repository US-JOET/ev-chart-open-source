import datetime
import json
from unittest.mock import MagicMock, patch

import boto3
import pytest
from AsyncFileIntegrity.index import (check_hash, handler, hash_data,
                                      insert_into_error_table)
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_logging import LogEvent
from moto import mock_aws

#pylint: disable=redefined-outer-name

@pytest.fixture(name="fixture_ssm_base")
def fixture_ssm_base():
    with mock_aws():
        ssm = boto3.client("ssm")
        ssm.put_parameter(Name="/ev-chart/some_var", Value="true", Type="String")
        yield ssm


@pytest.fixture(name="fixture_ssm_add_true")
def fixture_ssm_add_true(fixture_ssm_base):
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/s3/async-artifact-bucket-name",
        Value="ev-chart-artifact-data",
        Type="String",
    )
    yield fixture_ssm_base


@pytest.fixture(name="mock_boto3_manager")
def mock_boto3_manager(fixture_ssm_add_true):
    with patch.object(Boto3Manager, "client", return_value=fixture_ssm_add_true) as mock_client:
        yield mock_client


UPLOAD_FILE_PATH = "./tests/sample_data/all_columns_module_9.csv"
UPLOAD_CHECKSUM = "bb5733b5ff890016964c3cf3ee8ecbfb4fceb9ceb888d1554d684d9e65ba439a"
UPLOAD_KEY = "upload/Joint Office/123.csv"
S3_EVENT_KEY = "upload/Joint+Office/123.csv"
UPLOAD_BUCKET_NAME = "ev-chart-artifact-data"


@pytest.fixture(name="s3_client")
def s3_client():
    with mock_aws():
        conn = boto3.resource("s3", region_name="us-east-1")
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=UPLOAD_BUCKET_NAME)

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY,
            Body=get_file_content(UPLOAD_FILE_PATH),
            Metadata={"checksum": UPLOAD_CHECKSUM},
        )
        yield conn


@pytest.fixture(name="_mock_boto3_manager_s3")
def mock_boto3_manager_s3(s3_client): # [redefined-outer-name]
    with patch.object(Boto3Manager, "resource", return_value=s3_client) as mock_client:
        yield mock_client


@pytest.fixture(name="s3_client_corrupted_checksum")
def s3_client_corrupted_checksum():
    with mock_aws():
        conn = boto3.resource("s3", region_name="us-east-1")
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=UPLOAD_BUCKET_NAME)

        conn.Bucket(UPLOAD_BUCKET_NAME).put_object(
            Key=UPLOAD_KEY,
            Body=get_file_content(UPLOAD_FILE_PATH),
            Metadata={"checksum": "corrupted"},
        )
        yield conn


@pytest.fixture(name="_mock_boto3_manager_s3_corrupted")
def mock_boto3_manager_s3_corrupted(s3_client_corrupted_checksum):
    with patch.object(
        Boto3Manager, "resource", return_value=s3_client_corrupted_checksum
    ) as mock_client:
        yield mock_client


def get_file_content(file_path):
    with open(file_path, "rb") as f:
        return f.read()


def get_event_object(key=S3_EVENT_KEY, upload_bucket=UPLOAD_BUCKET_NAME):
    return {
        "Records": [
            {
                "eventVersion": "2.0",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "1970-01-01T00:00:00.000Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {"principalId": "EXAMPLE"},
                "requestParameters": {"sourceIPAddress": "127.0.0.1"},
                "responseElements": {
                    "x-amz-request-id": "EXAMPLE123456789",
                    "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH",
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "testConfigRule",
                    "bucket": {
                        "name": f"{upload_bucket}",
                        "ownerIdentity": {"principalId": "EXAMPLE"},
                        "arn": "arn:aws:s3:::DOC-EXAMPLE-BUCKET",
                    },
                    "object": {
                        "key": f"{key}",
                        "size": 1024,
                        "eTag": "0123456789abcdef0123456789abcdef",
                        "sequencer": "0A1B2C3D4E5F678901",
                    },
                },
            }
        ]
    }


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


def test_hash_data_creates_hash_from_s3_file_body():
    # hash file with frontend code, use hash to verify backend code
    # load csv used for hash
    # send to function
    frontend_hash = "bb5733b5ff890016964c3cf3ee8ecbfb4fceb9ceb888d1554d684d9e65ba439a"
    file_content = get_file_content("./tests/sample_data/all_columns_module_9.csv")

    new_hash = hash_data(file_content)

    assert frontend_hash == new_hash


def test_hash_data_returns_empty_string_with_no_body():
    body = None
    results = hash_data(body)
    assert results is None


def test_hash_data_returns_empty_string_with_empty_string_body():
    body = b""
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    result = hash_data(body)
    assert result == expected


def test_check_hash_parameters_match_return_true():
    assert check_hash("1", "1") is True


def test_check_hash_parameters_mismatch_returnfalse():
    assert check_hash("1", "2") is False


def test_check_hash_paremeters_with_none():
    assert check_hash(None, "2") is False


@patch("AsyncFileIntegrity.index.aurora")
@patch("AsyncFileIntegrity.index.send_sns_message")
@patch("AsyncFileIntegrity.index.error_table_insert")
def test_handler_returns_200_on_success(
    mock_error_table_insert, mock_send_sns_message, _mock_aurora, _mock_boto3_manager_s3
):
    event_object = get_event_object()
    result = handler(event_object, "")
    result_status = result.get("statusCode")
    result_body = json.loads(result.get("body"))
    integrity_check_passed = result_body.get("integrity_check_passed")
    assert result_status == 200
    assert integrity_check_passed is True
    assert mock_send_sns_message.called
    assert not mock_error_table_insert.called


@patch("AsyncFileIntegrity.index.aurora")
@patch("AsyncFileIntegrity.index.send_sns_message")
def test_handler_sends_passed_to_sns_on_success(
    mock_send_sns_message, _mock_aurora, _mock_boto3_manager_s3
):
    event_object = get_event_object()
    handler(event_object, "")
    args, _ = mock_send_sns_message.call_args
    assert args[0].get("file-integrity") == "passed"


@patch("AsyncFileIntegrity.index.aurora")
@patch("AsyncFileIntegrity.index.send_sns_message")
def test_handler_returns_500_on_bad_key(
    mock_send_sns_message, _mock_aurora, _mock_boto3_manager_s3
):
    event_object = get_event_object(key="Bad_Key")
    result = handler(event_object, "")
    assert result.get("statusCode") == 500
    assert mock_send_sns_message.called


@patch("AsyncFileIntegrity.index.aurora")
@patch("AsyncFileIntegrity.index.send_sns_message")
def test_handler_sends_failed_to_sns_on_bad_key(
    mock_send_sns_message, _mock_aurora, _mock_boto3_manager_s3
):
    event_object = get_event_object(key="Bad_Key")
    handler(event_object, "")
    args, _ = mock_send_sns_message.call_args
    assert args[0].get("file-integrity") == "failed"


@patch("AsyncFileIntegrity.index.aurora")
@patch("AsyncFileIntegrity.index.send_sns_message")
@patch("AsyncFileIntegrity.index.error_table_insert")
@patch("AsyncFileIntegrity.index.get_upload_metadata")
def test_handler_returns_200_with_corrupted_data(
    mock_get_upload_metadata,
    mock_error_table_insert,
    mock_send_sns_message,
    _mock_aurora,
    _mock_boto3_manager_s3_corrupted,
):
    event_object = get_event_object()
    mock_get_upload_metadata.return_value = get_upload_id_metadata()
    result = handler(event_object, "")
    result_status = result.get("statusCode")
    result_body = json.loads(result.get("body"))
    integrity_check_passed = result_body.get("integrity_check_passed")
    assert result_status == 200
    assert integrity_check_passed is False
    assert mock_send_sns_message.called
    assert mock_error_table_insert.called


@patch("AsyncFileIntegrity.index.aurora")
@patch("AsyncFileIntegrity.index.send_sns_message")
@patch("AsyncFileIntegrity.index.error_table_insert")
@patch("AsyncFileIntegrity.index.get_upload_metadata")
def test_handler_returns_200_with_corrupted_data_no_metadata(
    mock_get_upload_metadata,
    mock_error_table_insert,
    mock_send_sns_message,
    _mock_aurora,
    _mock_boto3_manager_s3_corrupted,
):
    event_object = get_event_object()
    mock_get_upload_metadata.return_value = None
    result = handler(event_object, "")
    result_status = result.get("statusCode")
    result_body = json.loads(result.get("body"))
    integrity_check_passed = result_body.get("integrity_check_passed")
    assert result_status == 200
    assert integrity_check_passed is False
    assert mock_send_sns_message.called
    assert mock_error_table_insert.called


@patch("AsyncFileIntegrity.index.aurora")
@patch("AsyncFileIntegrity.index.send_sns_message")
@patch("AsyncFileIntegrity.index.error_table_insert", side_effect=TypeError)
@patch("AsyncFileIntegrity.index.get_upload_metadata")
@patch.object(LogEvent, "log_level3_error")
def test_handler_returns_200_when_error_occurs_on_insert_error_table(
    mock_log_error,
    mock_get_upload_metadata,
    mock_error_table_insert,
    mock_send_sns_message,
    _mock_aurora,
    _mock_boto3_manager_s3_corrupted,
):
    event_object = get_event_object()
    mock_get_upload_metadata.return_value = None
    result = handler(event_object, "")
    result_status = result.get("statusCode")
    result_body = json.loads(result.get("body"))
    integrity_check_passed = result_body.get("integrity_check_passed")
    assert result_status == 200
    assert integrity_check_passed is False
    assert mock_send_sns_message.called
    assert mock_error_table_insert.called
    assert mock_log_error.called


@patch("AsyncFileIntegrity.index.aurora")
@patch("AsyncFileIntegrity.index.send_sns_message")
def test_handler_sends_failed_to_sns_with_corrupted_data(
    mock_send_sns_message, _mock_aurora, _mock_boto3_manager_s3_corrupted
):
    event_object = get_event_object()
    handler(event_object, "")
    args, _ = mock_send_sns_message.call_args
    assert args[0].get("file-integrity") == "failed"



@patch("AsyncFileIntegrity.index.send_sns_message")
def test_handler_failed_to_connect_to_aurora_return_500(
    mock_send_sns_message, _mock_boto3_manager_s3
):
    event_object = get_event_object()
    results = handler(event_object, "")

    body = results["body"]
    assert results["statusCode"] == 500
    assert "EvChartDatabaseHandlerConnectionError" in body

@patch("AsyncFileIntegrity.index.error_table_insert")
def test_insert_into_error_table_given_checksum_failed(mock_error_table_insert):
    cursor = MagicMock()
    metadata = {"upload_id": "123", "module_id": "2", "org_id": "1", "parent_org": "1"}
    message = "File recieved does not match expected file. This could be due to corruption caused during upload. Please try uploading the file again, and if the issue persists, contact us."
    insert_into_error_table(cursor, metadata, message)
    conditions = [{"error_row": None, "error_description": message, "header_name": ""}]

    # use kwargs instead of args since I used named(key word) args
    _, kwargs = mock_error_table_insert.call_args
    assert mock_error_table_insert.called
    assert kwargs["cursor"] == cursor
    assert kwargs["upload_id"] == metadata["upload_id"]
    assert kwargs["module_id"] == metadata["module_id"]
    assert kwargs["org_id"] == metadata["org_id"]
    assert kwargs["dr_id"] == metadata["parent_org"]
    assert kwargs["condition_list"] == conditions
    assert kwargs["df"] is None


@patch("AsyncFileIntegrity.index.error_table_insert")
def test_insert_into_error_table_given_none(mock_error_table_insert):
    cursor = MagicMock()
    upload_id = "123"
    metadata = None
    message = "an error occured"
    conditions = [{"error_row": None, "error_description": message, "header_name": ""}]

    insert_into_error_table(cursor, metadata, message, upload_id)
    _, kwargs = mock_error_table_insert.call_args

    assert mock_error_table_insert.called
    assert kwargs["cursor"] == cursor
    assert kwargs["upload_id"] == upload_id
    assert kwargs["module_id"] == ""
    assert kwargs["org_id"] == ""
    assert kwargs["dr_id"] == ""
    assert kwargs["condition_list"] == conditions
    assert kwargs["df"] is None


def test_insert_into_error_table_given_none_and_no_upload_id_raise_error():
    cursor = MagicMock()
    metadata = None
    message = "an error occured"
    with pytest.raises(TypeError) as e:
        insert_into_error_table(cursor, metadata, message)
    assert e
