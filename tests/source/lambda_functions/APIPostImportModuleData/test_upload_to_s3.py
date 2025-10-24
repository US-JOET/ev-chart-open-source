import hashlib
from unittest.mock import patch

import boto3
import pytest
# pylint: disable=import-error
# module paths are set in conftest.py
from APIPostImportModuleData.index import (get_async_bucket,
                                           upload_to_s3_from_raw)
from evchart_helper import boto3_manager
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import \
    EvChartMissingOrMalformedHeadersError
from moto import mock_aws


@pytest.fixture
def fixture_ssm_base():
    with mock_aws():
        ssm = boto3.client("ssm")
        ssm.put_parameter(Name="/ev-chart/some_var", Value="true", Type="String")
        yield ssm


@pytest.fixture
def fixture_ssm_add_true(fixture_ssm_base):
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/s3/async-artifact-bucket-name",
        Value="ev-chart-artifact-data",
        Type="String",
    )
    yield fixture_ssm_base


@pytest.fixture
def mock_boto3_manager(fixture_ssm_add_true):
    with patch.object(Boto3Manager, "client", return_value=fixture_ssm_add_true) as mock_client:
        yield mock_client


@pytest.fixture
def s3_client():
    with mock_aws():
        bucket_name= 'ev-chart-artifact-data'
        conn = boto3.resource("s3", region_name="us-east-1")
        # We need to create the bucket since this is all in Moto's 'virtual' AWS account
        conn.create_bucket(Bucket=bucket_name)
        yield conn

@pytest.fixture
def mock_boto3_manager_s3(s3_client):
    with patch.object(Boto3Manager, "resource", return_value=s3_client) as mock_client:
        yield mock_client

def test_upload_to_s3_from_raw_uploads_csv(mock_boto3_manager, mock_boto3_manager_s3):
    body = None
    s3_resource = boto3_manager.resource("s3")
    bucket_name = get_async_bucket()

    with open(
        f"./tests/sample_data/evchart_valid_all_columns_module_2_100_records.csv",
        "r",
        encoding="utf-8",
    ) as fh:
        body = fh.read()

    checksum = hash_data(body.encode('utf-8'))
    request_headers = {"checksum": checksum}
    upload_id = 987
    recipient_type = "test"
    token = {}
    token['recipient_type'] = recipient_type
    token['org_name'] = "test org"
    uploaded = upload_to_s3_from_raw(body, upload_id, request_headers, token)
    obj = s3_resource.Object(bucket_name, f"testing/test org/{upload_id}.csv")
    response = obj.get()
    metadata = response["Metadata"]
    downloaded_csv = response["Body"].read()
    downloaded_checksum = hash_data(downloaded_csv)
    bucket_list = list_items_in_bucket(s3_resource, bucket_name)
    print(bucket_list)

    assert metadata['checksum'] == checksum
    assert metadata['recipient_type'] == recipient_type
    assert uploaded is True
    assert downloaded_checksum == checksum


def test_upload_to_s3_errors_with_no_checksum(mock_boto3_manager, mock_boto3_manager_s3):
    body = None
    request_headers = {"year": "2024"}

    with open(
        f"./tests/sample_data/evchart_valid_all_columns_module_2_100_records.csv",
        "r",
        encoding="utf-8",
    ) as fh:
        body = fh.read()
    upload_id = 987
    recipient_type = "test"
    token = {}
    token['recipient_type'] = recipient_type
    token['org_name'] = "test org"
    with pytest.raises(EvChartMissingOrMalformedHeadersError):
        upload_to_s3_from_raw(body, upload_id, request_headers, token)


def list_items_in_bucket(s3_resource, bucket_name):
    bucket = s3_resource.Bucket(bucket_name)
    return [obj.key for obj in bucket.objects.all()]


def hash_data(file_content):
    checksum = None
    if file_content is not None:
        sha256_hash = hashlib.sha256()
        sha256_hash.update(file_content)
        checksum = sha256_hash.hexdigest()
    return checksum
