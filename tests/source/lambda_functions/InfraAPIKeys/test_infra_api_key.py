from datetime import datetime, UTC
import hashlib
import os
from unittest.mock import patch

import boto3
import pytest
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import EvChartDatabaseDynamoQueryError
from evchart_helper.s2s_helper import get_hashed_api_key_info
from InfraAPIKeys.index import (
    add_key_to_api_key_table,
    add_key_to_secret_manager,
    add_key_to_usage_plan,
    assign_key_to_org,
    create_api_key,
    get_key_from_secret_manager,
    handler
)
from moto import mock_aws


@pytest.fixture(name="dynamodb_org")
def fixture_dynamodb_org():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        org_table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[{"AttributeName": "org_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{
                "AttributeName": "org_id",
                "AttributeType": "S"
            }],
            BillingMode="PAY_PER_REQUEST",
        )
        org_table.wait_until_exists()

        api_key_table = dynamodb.create_table(
            TableName="ev-chart_api_key",
            KeySchema=[
                {"AttributeName": "hashed_api_key", "KeyType": "HASH"},
                {"AttributeName": "environment", "KeyType": "RANGE"},
                       ],
            AttributeDefinitions=[
                {"AttributeName": "hashed_api_key", "AttributeType": "S"},
                {"AttributeName": "environment", "AttributeType": "S"},
                {"AttributeName": "org_id", "AttributeType": "S"},
                {"AttributeName": "generated_on", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi_org_id",
                    "KeySchema": [
                        {"AttributeName": "org_id", "KeyType": "HASH"},
                        {
                            "AttributeName": "hashed_api_key",
                            "KeyType": "RANGE"
                        },
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "gsi_org_id",
                    "KeySchema": [
                        {"AttributeName": "org_id", "KeyType": "HASH"},
                        {"AttributeName": "generated_on", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )

        api_key_table.wait_until_exists()

        # inserting Maine DR
        org_table.put_item(
            Item={
                "org_id": "111",
                "name": "Maine DOT",
                "HashedApiKey": "abc123"
            }
        )

        # inserting NY DR
        org_table.put_item(
            Item={"org_id": "222", "name": "NY DOT", "HashedApiKey": ""}
        )

        # inserting Sparkflow SR
        org_table.put_item(
            Item={"org_id": "333", "name": "Sparkflow", "HashedApiKey": ""}
        )

        yield dynamodb


@pytest.fixture(name="_secret_client")
def fixture_secret_client():
    with mock_aws():
        secret_client = boto3.client("secretsmanager")
        secret_client.create_secret(
            Name="evchart/api_key/123",
            Description="API key for example org",
            SecretString="abc123",
        )
        yield secret_client


@pytest.fixture(name="_api_client")
def fixture_api_client():
    with mock_aws():
        api_client = boto3.client("apigateway")
        yield api_client


@pytest.fixture(name="_mock_boto3_manager")
def fixture_boto3_manager(dynamodb_org):
    with patch.object(
        Boto3Manager, "resource", return_value=dynamodb_org
    ) as mock_client:
        yield mock_client


@pytest.fixture(name="_mock_boto3_secret_manager")
def fixture_boto3_secret_manager(_secret_client):
    with patch.object(
        Boto3Manager, "client", return_value=_secret_client
    ) as mock_client:
        yield mock_client


@pytest.fixture(name="_mock_boto3_client_manager")
def fixture_boto3_client_manager(_api_client):
    with patch.object(
        Boto3Manager, "client", return_value=_api_client
    ) as mock_client:
        yield mock_client


@pytest.mark.skip()
def test_add_new_key(_mock_boto3_manager, mock_boto3_client_manager):
    mod_event = {"org_id": "123"}
    mod_event["operation"] = "Create New Key"
    usage_plan = mock_boto3_client_manager.create_usage_plan(name="testing")
    mod_event["usage_plan_id"] = usage_plan["id"]
    mod_event["org_id"] = "222"

    handler(mod_event, None)
    assert True


def test_assigning_key_to_org(_mock_boto3_manager):
    client = _mock_boto3_manager()
    assign_key_to_org("222", "key_value")

    table = client.Table("ev-chart_org")
    org_info = table.get_item(Key={"org_id": "222"})
    org_data = org_info["Item"]

    assert org_data.get("HashedApiKey") == \
        hashlib.sha256("key_value".encode()).hexdigest()


def test_regen_key(_mock_boto3_manager):
    client = _mock_boto3_manager()
    table = client.Table("ev-chart_org")
    org_info = table.get_item(Key={"org_id": "111"})
    org_data = org_info["Item"]

    assert org_data.get("HashedApiKey") == "abc123"

    assign_key_to_org("111", "key_value")
    org_info = table.get_item(Key={"org_id": "111"})
    org_data = org_info["Item"]

    assert org_data.get("HashedApiKey") == \
        hashlib.sha256("key_value".encode()).hexdigest()


@patch("InfraAPIKeys.index.add_key_to_secret_manager")
def test_key_creation(_mock_add_key, _mock_boto3_client_manager):
    org_info = {"name": "Sparkflow"}
    key_id, key_value = create_api_key(org_info)
    assert key_id and key_value


def test_secret_manager_add_and_get(_mock_boto3_secret_manager):
    org_info = {"name": "Sparkflow", "org_id": 222}
    key = "test"
    add_key_to_secret_manager(org_info, key)
    result = get_key_from_secret_manager(222)
    # should check SM to verify it exists,
    # but there's also a reponse check in function
    assert result == key


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_add_key_to_secret_manager_add_key_to_base_env(
    _mock_boto3_secret_manager
):
    client = _mock_boto3_secret_manager()
    org_info = {"name": "Sparkflow", "org_id": 222}
    key = "test"
    expected_secret_id = f"evchart/api_key/{org_info['org_id']}"
    add_key_to_secret_manager(org_info, key)

    response = client.get_secret_value(SecretId=expected_secret_id)
    secret_string = response['SecretString']
    assert secret_string == key


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_add_key_to_secret_manager_add_key_to_sub_env(
    _mock_boto3_secret_manager
):
    client = _mock_boto3_secret_manager()
    org_info = {"name": "Sparkflow", "org_id": 222}
    key = "test"
    expected_secret_id = f"evchart/api_key/qa/{org_info['org_id']}"
    add_key_to_secret_manager(org_info, key)

    response = client.get_secret_value(SecretId=expected_secret_id)
    secret_string = response['SecretString']
    assert secret_string == key


@patch("InfraAPIKeys.index.get_usage_plan_id")
def test_add_key_to_usage_plan(
    _mock_usage_plan, _mock_boto3_client_manager, _mock_boto3_manager
):
    client = _mock_boto3_client_manager()
    usage_plan = client.create_usage_plan(name="testing")
    usage_plan_id = usage_plan["id"]
    _mock_usage_plan.return_value = usage_plan_id
    key = client.create_api_key(
        name="test",
        enabled=True,
        generateDistinctId=True,
    )
    add_key_to_usage_plan(key["id"])
    assert True


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_assign_key_to_org_given_test_env_save_hash(_mock_boto3_manager):
    org_id = "222"
    key_value = "test_hash"
    hashed_key = hashlib.sha256(key_value.encode()).hexdigest()
    assign_key_to_org(org_id, key_value)

    client = _mock_boto3_manager()
    table = client.Table("ev-chart_org")
    org_info = table.get_item(Key={"org_id": org_id})
    org_data = org_info["Item"]
    assert hashed_key == org_data["HashedApiKey"]


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_assign_key_to_org_given_qa_env_save_qahash(_mock_boto3_manager):
    org_id = "222"
    key_value = "test_hash"
    hashed_key = hashlib.sha256(key_value.encode()).hexdigest()
    assign_key_to_org(org_id, key_value)
    client = _mock_boto3_manager()
    table = client.Table("ev-chart_org")
    org_info = table.get_item(Key={"org_id": org_id})
    org_data = org_info["Item"]
    assert hashed_key == org_data["HashedApiKey"]


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_add_key_to_api_key_table_added_to_table_given_valid(
    _mock_boto3_manager
):
    org_id = "222"
    key_value = "test_hash"
    environment = "test"
    hashed_key = hashlib.sha256(key_value.encode()).hexdigest()
    generated_date = datetime.now(UTC).date()
    add_key_to_api_key_table(org_id, key_value)

    hashed_key_info = get_hashed_api_key_info(hashed_key)
    assert hashed_key_info["org_id"] == org_id
    assert environment == hashed_key_info["environment"]
    assert generated_date.strftime("%Y-%m-%d") in \
        hashed_key_info["generated_on"]


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_add_key_to_api_key_table_added_to_table_with_qa_given_valid(
    _mock_boto3_manager
):
    org_id = "222"
    key_value = "test_hash"
    environment = "qa"
    hashed_key = hashlib.sha256(key_value.encode()).hexdigest()
    generated_date = datetime.now(UTC).date()
    add_key_to_api_key_table(org_id, key_value)

    hashed_key_info = get_hashed_api_key_info(hashed_key)
    assert org_id == hashed_key_info["org_id"]
    assert environment == hashed_key_info["environment"]
    assert generated_date.strftime("%Y-%m-%d") in \
        hashed_key_info["generated_on"]


def test_add_key_to_api_key_table_raises_error_given_connection_issue():
    org_id = "222"
    key_value = "test_hash"
    with pytest.raises(EvChartDatabaseDynamoQueryError) as e:
        add_key_to_api_key_table(org_id, key_value)
    assert e
