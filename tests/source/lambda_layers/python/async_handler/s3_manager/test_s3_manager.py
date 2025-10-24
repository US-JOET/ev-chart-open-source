from unittest.mock import patch
import boto3
import pytest
from async_utility.s3_manager import get_s3_object
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import EvChartS3GetObjectError
from moto import mock_aws

upload_file_path = "./tests/sample_data/all_columns_module_9.csv"
upload_checksum = "0d810e7fbf2f435b93a7b51d26e7df28e3b8747a322a33dcf2a4db8dbae63ce0"
upload_key = "upload/Joint Office/852ade96-4075-4766-9b97-5e9379b31ab0.csv"
upload_bucket_name = "ev-chart-artifact-data-unit-test"

invalid_file_upload_id = "bad_file.csv"
invalid_file_path = "./tests/sample_data/all_invalid_data_type_mod_9.csv"

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
            Key=invalid_file_upload_id,
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

def test_get_s3_object_when_object_exists(mock_boto3_manager_s3):
    response = get_s3_object(upload_bucket_name, upload_key)
    metadata = response['Metadata']
    checksum = metadata['checksum']

    body = response['Body'].read().decode('utf-8')
    assert checksum == upload_checksum
    file_content = get_file_content(upload_file_path)
    assert len(body) == len(file_content)

def test_get_s3_object_when_object_not_found(mock_boto3_manager_s3):
    with pytest.raises(EvChartS3GetObjectError):
        get_s3_object(upload_bucket_name, "bad_key")

def test_get_s3_object_when_s3_connection_failed():
    with pytest.raises(EvChartS3GetObjectError):
        get_s3_object(upload_bucket_name, upload_key)
