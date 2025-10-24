import datetime
import os
from unittest.mock import patch
import boto3
from moto import mock_aws
import pytest

from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import EvChartDynamoConnectionError, EvChartInvalidAPIKey
from evchart_helper.s2s_helper import (
    API_KEY_EXPIRATION_DAYS,
    get_environment_name,
    get_expiring_api_keys,
    get_hashed_api_key_info,
    get_keys_by_org,
    get_newest_api_key,
    get_org_by_api_key,
    get_org_from_api_key_info,
    get_org_from_hash_handler,
    scan_org_by_hashed_key,
)


@pytest.fixture(name="dynamodb_tables")
def fixture_dynamodb_tables():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        org_table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[{"AttributeName": "org_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "org_id", "AttributeType": "S"},
                {"AttributeName": "recipient_type", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi_recipient_type",
                    "KeySchema": [{"AttributeName": "recipient_type", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        org_table.wait_until_exists()

        # inserting Maine DR
        org_table.put_item(
            Item={
                "org_id": "123-456",
                "name": "Maine DOT",
                "org_friendly_id": "123",
                "recipient_type": "direct-recipient",
            }
        )

        org_table.put_item(
            Item={
                "org_id": "111-222",
                "name": "API Client",
                "org_friendly_id": "111",
                "recipient_type": "sub-recipient",
                "HashedApiKey": "123",
            }
        )

        user_table = dynamodb.create_table(
            TableName="ev-chart_users",
            KeySchema=[{"AttributeName": "identifier", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "identifier", "AttributeType": "S"},
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "org_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi_org_id",
                    "KeySchema": [
                        {"AttributeName": "org_id", "KeyType": "HASH"},
                        {"AttributeName": "identifier", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "gsi_session_id",
                    "KeySchema": [{"AttributeName": "session_id", "KeyType": "HASH"}],
                    "Projection": {
                        "ProjectionType": "INCLUDE",
                        "NonKeyAttributes": ["refresh_token"],
                    },
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        user_table.wait_until_exists()

        current_datetime = datetime.datetime.now()
        api_key_valid_number_of_days = API_KEY_EXPIRATION_DAYS
        five_days_until_expired = 5

        # add 1 to days until expired because API_KEY_EXPIRATION_DAYS is an exclusive >
        days_to_subtract = (api_key_valid_number_of_days + 1) - five_days_until_expired
        soon_to_expire_datetime = current_datetime - datetime.timedelta(days=days_to_subtract)
        # expires tomorrow
        expiring_datetime = current_datetime - datetime.timedelta(days=API_KEY_EXPIRATION_DAYS)

        user_table.put_item(
            Item={
                "identifier": "ev-chart-user@ee.doe.gov",
                "account_status": "Active",
                "first_name": "Jane",
                "last_generated": str(current_datetime),
                "last_name": "Doe",
                "org_id": "111-222",
            }
        )

        user_table.put_item(
            Item={
                "identifier": "expired@gmail.com",
                "account_status": "Deactivated",
                "first_name": "John",
                "last_generated": str(current_datetime),
                "last_name": "Doe",
                "org_id": "111-222",
            }
        )

        user_table.put_item(
            Item={
                "identifier": "MaineDot@gmail.com",
                "account_status": "Active",
                "first_name": "DR",
                "last_generated": str(current_datetime),
                "last_name": "Org",
                "org_id": "123-456",
            }
        )

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
                        {"AttributeName": "hashed_api_key", "KeyType": "RANGE"},
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

        api_key_table.put_item(
            Item={
                "hashed_api_key": "999",
                "environment": "test",
                "org_id": "123",
                "generated_on": str(current_datetime),
            }
        )

        api_key_table.put_item(
            Item={
                "hashed_api_key": "777",
                "environment": "qa",
                "org_id": "123",
                "generated_on": str(current_datetime),
            }
        )

        api_key_table.put_item(
            Item={
                "hashed_api_key": "111",
                "environment": "test",
                "org_id": "111-222",
                "generated_on": str(soon_to_expire_datetime),
            }
        )

        api_key_table.put_item(
            Item={
                "hashed_api_key": "222",
                "environment": "qa",
                "org_id": "111-222",
                "generated_on": str(expiring_datetime),
            }
        )

        api_key_table.put_item(
            Item={
                "hashed_api_key": "333",
                "environment": "qa",
                "org_id": "123",
                "generated_on": str(expiring_datetime),
            }
        )

        yield dynamodb


@pytest.fixture(name="_mock_boto3_manager")
def mock_boto3_manager(dynamodb_tables):
    with patch.object(Boto3Manager, "resource", return_value=dynamodb_tables) as mock_resource:
        yield mock_resource


def test_scan_org_by_hashed_key_throws_error_when_boto3_connection_fails():
    hashed_key = "123"
    with pytest.raises(EvChartDynamoConnectionError) as raised_error:
        scan_org_by_hashed_key(hashed_key)
    assert hashed_key in raised_error.value.message


def test_scan_org_by_hashed_key_returns_org_when_hash_found(_mock_boto3_manager):
    hashed_key = "123"
    result = scan_org_by_hashed_key(hashed_key)
    assert result["org_id"] == "111-222"


def test_scan_org_by_hashed_key_returns_nothing_when_org_not_found(_mock_boto3_manager):
    hashed_key = "111"
    result = scan_org_by_hashed_key(hashed_key)
    assert result is None


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_org_from_api_key_info_returns_org_id_when_found(_mock_boto3_manager):
    hashed_key = "999"
    org_id = get_org_from_api_key_info(hashed_key)
    assert org_id == "123"


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_get_org_from_api_key_info_returns_org_id_when_found_in_sub_env(_mock_boto3_manager):
    hashed_key = "777"
    org_id = get_org_from_api_key_info(hashed_key)
    assert org_id == "123"


def test_get_org_from_api_key_info_raises_error_when_no_org_found(_mock_boto3_manager):
    hashed_key = "missing"
    with pytest.raises(EvChartInvalidAPIKey) as raised_error:
        get_org_from_api_key_info(hashed_key)
    assert raised_error.value.message


@patch("evchart_helper.s2s_helper.get_hash_from_api_key")
@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_org_by_api_key_with_new_api_key_return_org_id(
    mock_hashed_api_key, _mock_boto3_manager
):
    api_key = "new api key"
    hashed_key = "999"
    expected_org_id = "123"
    mock_hashed_api_key.return_value = hashed_key

    result = get_org_by_api_key(api_key)
    assert expected_org_id == result


@patch("evchart_helper.s2s_helper.get_hash_from_api_key")
@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_org_by_api_key_with_old_api_key_return_org_id(
    mock_hashed_api_key, _mock_boto3_manager
):
    api_key = "old api key"
    hashed_key = "123"
    expected_org_id = "111-222"
    mock_hashed_api_key.return_value = hashed_key

    result = get_org_by_api_key(api_key)
    assert expected_org_id == result


@patch("evchart_helper.s2s_helper.get_hash_from_api_key")
@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_org_by_api_key_with_no_api_key_raise_error(mock_hashed_api_key, _mock_boto3_manager):
    api_key = "bad key"
    hashed_key = "bad key"
    mock_hashed_api_key.return_value = hashed_key

    with pytest.raises(EvChartInvalidAPIKey) as e:
        get_org_by_api_key(api_key)
    assert "No organization associated with given api key" in e.value.message


def test_get_org_from_hash_handler_returns_org_id_when_found(_mock_boto3_manager):
    hashed_key = "123"
    org_id = get_org_from_hash_handler(hashed_key)
    assert org_id == "111-222"


def test_get_org_from_hash_handler_raises_error_when_no_org_found(_mock_boto3_manager):
    hashed_key = "missing"
    with pytest.raises(EvChartInvalidAPIKey) as raised_error:
        get_org_from_hash_handler(hashed_key)
    assert "No organization associated with given api key" in raised_error.value.message


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_environment_name_return_env_name():
    name = get_environment_name()
    assert name == "test"


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_get_environment_name_return_sub_env_name():
    name = get_environment_name()
    assert name == "qa"


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_hashed_api_key_info(_mock_boto3_manager):
    environment = "test"
    hashed_api_key = "999"
    org_id = "123"
    info = get_hashed_api_key_info(hashed_api_key)

    assert hashed_api_key == info["hashed_api_key"]
    assert environment == info["environment"]
    assert org_id == info["org_id"]
    assert info["generated_on"]


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_get_hashed_api_key_info_for_sub(_mock_boto3_manager):
    environment = "qa"
    hashed_api_key = "777"
    org_id = "123"
    info = get_hashed_api_key_info(hashed_api_key)

    assert hashed_api_key == info["hashed_api_key"]
    assert environment == info["environment"]
    assert org_id == info["org_id"]
    assert info["generated_on"]


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_hashed_api_key_raise_error():
    hashed_api_key = "777"
    with pytest.raises(EvChartDynamoConnectionError) as raised_error:
        get_hashed_api_key_info(hashed_api_key)
    assert "issue verifying api key" in raised_error.value.message

@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_expiring_api_keys_given_exact_day_until_expired_returns_key(_mock_boto3_manager):
    days_until_expired = 5
    result = get_expiring_api_keys(days_until_expired)
    assert result
    assert len(result) == 1
    assert result[0]["hashed_api_key"] == "111"

@patch.dict(os.environ, {"ENVIRONMENT": "qa"})
def test_get_expiring_api_keys_given_exact_day_until_expired_returns_multiple_keys(_mock_boto3_manager):
    days_until_expired = 1
    result = get_expiring_api_keys(days_until_expired)
    assert result
    assert len(result) == 2
    assert result[0]["hashed_api_key"] == "222"
    assert result[1]["hashed_api_key"] == "333"

@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_get_expiring_api_keys_given_environment_with_no_match_return_None(_mock_boto3_manager):
    days_until_expired = 5
    result = get_expiring_api_keys(days_until_expired)
    assert result is None

@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_expiring_api_keys_given_day_over_expired_returns_None(_mock_boto3_manager):
    days_until_expired = 6
    result = get_expiring_api_keys(days_until_expired)
    assert result is None

@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_keys_by_org_get_one_key(_mock_boto3_manager):
    org_id = "111-222"
    results = get_keys_by_org(org_id)
    assert len(results) == 1

@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_get_keys_by_org_get_two_key(_mock_boto3_manager):
    org_id = "123"
    results = get_keys_by_org(org_id)
    assert len(results) == 2

@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_keys_by_org_get_none(_mock_boto3_manager):
    org_id = "000"
    results = get_keys_by_org(org_id)
    assert results is None

@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_get_newest_api_key(_mock_boto3_manager):
    org_id = "123"
    result = get_newest_api_key(org_id)
    assert result
    assert result["hashed_api_key"] == "777"

@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_get_newest_api_key_return_None(_mock_boto3_manager):
    org_id = "000"
    result = get_newest_api_key(org_id)
    assert result is None