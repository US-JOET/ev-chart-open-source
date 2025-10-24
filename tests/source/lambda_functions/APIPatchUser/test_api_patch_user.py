import json
import os
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import boto3
import feature_toggle
import pytest
from APIPatchUser.index import handler as api_patch_user
from APIPatchUser.index import is_valid_body, reinvite_user, remove_user
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import EvChartDatabaseDynamoQueryError
from moto import mock_aws


class EvChartDatabaseQueryError(Exception):
    pass


class EvChartUserExistsError(Exception):
    pass


# creating users table fixture
@pytest.fixture
def fixture_dynamodb_base():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        user_table = dynamodb.create_table(
            TableName="ev-chart_users",
            KeySchema=[{"AttributeName": "identifier", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "identifier", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        user_table.wait_until_exists()

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

        org_table.put_item(
            Item={
                "org_id": "123",
                "name": "Maine DOT",
                "org_friendly_id": "1",
                "recipient_type": "direct-recipient",
            }
        )

        yield dynamodb


@pytest.fixture
def mock_boto3_manager(fixture_dynamodb_base):
    with patch.object(Boto3Manager, "resource", return_value=fixture_dynamodb_base) as mock_client:
        yield mock_client


# removing user from the table
@pytest.fixture
def fixture_dynamodb_valid_user(fixture_dynamodb_base):
    table = fixture_dynamodb_base.Table("ev-chart_users")
    table.put_item(
        Item={
            "identifier": "daniel@afs.com",
            "org_id": "123",
            "account_status": "Active",
            "first_name": "first",
            "last_name": "last",
            "role": "admin",
        }
    )
    table.put_item(
        Item={
            "identifier": "josh@afs.com",
            "org_id": "999",
            "account_status": "Active",
            "first_name": "first",
            "last_name": "last",
            "role": "admin",
        }
    )
    table.put_item(
        Item={
            "identifier": "justin@afs.com",
            "org_id": "123",
            "account_status": "Expired",
            "first_name": "first",
            "last_name": "last",
            "role": "admin",
        }
    )
    yield fixture_dynamodb_base


@pytest.fixture
def fixture_dynamodb_remove_valid_user(fixture_dynamodb_base):
    table = fixture_dynamodb_base.Table("ev-chart_users")
    table.update_item(
        Key={"identifier": "daniel@afs.com"},
        UpdateExpression="set org_id=:o, last_generated=:l",
        ExpressionAttributeValues={":o": "", ":l": "timestamp"},
        ReturnValues="UPDATED_NEW",
    )
    yield fixture_dynamodb_base


def get_valid_event(email="daniel@afs.com", action="remove"):
    return {
        "headers": {},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "Pennsylania DOT",
                    "email": "ebenes@ee.doe.gov",
                    "scope": "direct-recipient",
                    "preferred_name": "Elaine Benes",
                    "role": "admin",
                }
            },
        },
        "body": json.dumps({"email": email, "action": action}),
    }


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_lambda_response_body_valid_201(
    mock_boto3_manager, fixture_dynamodb_base, fixture_dynamodb_valid_user
):
    event = get_valid_event()
    api_response = api_patch_user(event, None)
    assert api_response.get("statusCode") == 201


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_lambda_response_body_invalid_406_missing_body():
    event = get_valid_event()
    missing_parameters_body = json.dumps({})
    event["body"] = missing_parameters_body
    api_response = api_patch_user(event, None)
    assert api_response.get("statusCode") == 406
    assert "EvChartMissingOrMalformedBodyError raised." in api_response.get("body")


# testing dynamo db
def test_remove_user_valid(
    fixture_dynamodb_base, fixture_dynamodb_valid_user, fixture_dynamodb_remove_valid_user
):
    boto3_session = boto3.session.Session()
    dynamodb = boto3_session.resource("dynamodb")

    event = get_valid_event()
    user_data = json.loads(event["body"])

    remove_user(user_data, dynamodb)

    # retrieve item from dynamo db table
    table = fixture_dynamodb_base.Table("ev-chart_users")
    response = table.get_item(Key={"identifier": user_data["email"]})
    new_user = response.get("Item")
    assert new_user is not None
    assert new_user["identifier"] == "daniel@afs.com"
    assert new_user["account_status"] == "Removed"


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_lambda_response_406_adding_existing_user(
    mock_boto3_manager, fixture_dynamodb_base, fixture_dynamodb_valid_user
):
    event = get_valid_event()
    event["body"] = json.dumps({"email": "test@afs.com", "action": "remove"})

    response = api_patch_user(event, None)
    assert response.get("statusCode") == 406
    assert "EvChartMissingOrMalformedBodyError raised." in response.get("body")
    assert response.get("body") == json.dumps(
        "EvChartMissingOrMalformedBodyError raised. Error, user doesn't exist: Email test@afs.com not in DynamoDB."
    )


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_handler_given_admin_not_in_same_org_as_user_throw_error(
    mock_boto3_manager, fixture_dynamodb_base, fixture_dynamodb_valid_user
):
    out_of_org_email = "josh@afs.com"
    event = get_valid_event(email=out_of_org_email)
    response = api_patch_user(event, None)
    assert response.get("statusCode") == 403
    assert "EvChartUserNotAuthorizedError raised." in response.get("body")


@patch("APIPatchUser.index.trigger_email")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_handler_given_re_invite_request_success_return_201_sends_email(
    mock_get_feature_by_enum,
    mock_trigger_email,
    mock_boto3_manager,
    fixture_dynamodb_base,
    fixture_dynamodb_valid_user,
):
    mock_get_feature_by_enum.return_value = {"Name": "new-user-email", "Value": "True"}
    event = get_valid_event(email="justin@afs.com", action="reinvite")
    api_response = api_patch_user(event, None)
    assert api_response.get("statusCode") == 201
    assert mock_trigger_email.called


def test_reinvite_user_success(fixture_dynamodb_base, fixture_dynamodb_valid_user):
    event = get_valid_event(email="justin@afs.com", action="reinvite")
    user_data = json.loads(event["body"])

    result = reinvite_user(user_data, fixture_dynamodb_base)
    assert result

    # retrieve item from dynamo db table
    table = fixture_dynamodb_base.Table("ev-chart_users")
    response = table.get_item(Key={"identifier": user_data["email"]})
    new_user = response.get("Item")
    todays_date = datetime.now(UTC).date()
    assert new_user is not None
    assert new_user["identifier"] == "justin@afs.com"
    assert new_user["account_status"] == "Pending"
    assert todays_date.strftime("%Y-%m-%d") in new_user["last_generated"]


def test_reinvite_user_failure(fixture_dynamodb_base, fixture_dynamodb_valid_user):
    event = get_valid_event(action="reinvite")
    user_data = json.loads(event["body"])

    with pytest.raises(EvChartDatabaseDynamoQueryError) as exception:
        reinvite_user(user_data, fixture_dynamodb_base)
    assert exception.value.message


def test_reinvite_user_dynamodb_no_credentials_raise_error():
    boto3_session = boto3.session.Session()
    dynamodb = boto3_session.resource("dynamodb")
    body = {"email": "test@afs.com", "action": "remove"}
    with pytest.raises(EvChartDatabaseDynamoQueryError) as exception:
        reinvite_user(body, dynamodb)
    assert exception.value.message


def test_reinvite_user_dynamodb_fails_raise_error():
    body = {"email": "test@afs.com", "action": "remove"}
    mock_dynamodb = MagicMock()
    mock_dynamodb_table = mock_dynamodb.Table.return_value
    mock_dynamodb_table.update_item.return_value = None
    with pytest.raises(EvChartDatabaseDynamoQueryError) as exception:
        reinvite_user(body, mock_dynamodb)
    assert exception.value.message


def test_is_valid_body_given_valid_body():
    body = {"email": "daniel@afs.com", "action": "remove"}
    result = is_valid_body(body)
    assert len(result) == 0


def test_is_valid_body_given_no_email_return_error():
    body = {"action": "remove"}
    result = is_valid_body(body)
    assert len(result) == 1


def test_is_valid_body_given_invalid_email_return_error():
    body = {"email": "daniel", "action": "remove"}
    result = is_valid_body(body)
    assert len(result) == 1


def test_is_valid_body_given_no_action_return_error():
    body = {
        "email": "daniel@afs.com",
    }
    result = is_valid_body(body)
    assert len(result) == 1


def test_is_valid_body_given_invalid_action_return_error():
    body = {"email": "daniel@afs.com", "action": "dance"}
    result = is_valid_body(body)
    assert len(result) == 1


def test_is_valid_body_given_no_action_and_no_email_return_errors():
    body = {}
    result = is_valid_body(body)
    assert len(result) == 2
