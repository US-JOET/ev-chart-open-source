from unittest.mock import patch
import datetime
import json
import os
import pytest
from moto import mock_aws
import boto3
import feature_toggle
from evchart_helper.boto3_manager import Boto3Manager
from APIPostUser.index import handler as api_post_user, add_new_user, reactivate_user


# creating users table fixture
@pytest.fixture(name="dynamodb_base")
def fixture_dynamodb_base():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName="ev-chart_users",
            KeySchema=[{"AttributeName": "identifier", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "identifier", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield dynamodb


@pytest.fixture(name="_mock_boto3_manager_users")
def mock_boto3_manager_users(dynamodb_base):
    with patch.object(Boto3Manager, "resource", return_value=dynamodb_base) as mock_client:
        yield mock_client


# adding one active and one removed user into the table
@pytest.fixture(name="dynamodb_valid_user")
def fixture_dynamodb_valid_user(dynamodb_base):
    table = dynamodb_base.Table("ev-chart_users")
    table.put_item(
        Item={
            "identifier": "sophia@mainedot.com",
            "account_status": "Active",
            "first_name": "Sophia",
            "last_generated": str(datetime.datetime.utcnow()),
            "last_name": "Hernandez",
            "org_id": "123",
        }
    )

    table.put_item(
        Item={
            "identifier": "joshua@mainedot.com",
            "account_status": "Removed",
            "first_name": "Joshua",
            "last_generated": str(datetime.datetime.utcnow()),
            "last_name": "Theisen",
            "org_id": "123",
        }
    )

    yield dynamodb_base


@pytest.fixture(name="_mock_boto3_manager_valid_users")
def mock_boto3_manager_valid_users(dynamodb_valid_user):
    with patch.object(Boto3Manager, "resource", return_value=dynamodb_valid_user) as mock_client:
        yield mock_client


# adding one user into the table
@pytest.fixture(name="dynamodb_removed_user")
def fixture_dynamodb_removed_user(dynamodb_base):
    table = dynamodb_base.Table("ev-chart_users")
    table.put_item(
        Item={
            "identifier": "joshua@mainedot.com",
            "account_status": "Removed",
            "first_name": "Joshua",
            "last_generated": str(datetime.datetime.utcnow()),
            "last_name": "Theisen",
            "org_id": "123",
        }
    )

    yield dynamodb_base


def get_valid_event():
    return {
        "headers": {},
        "httpMethod": "POST",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "New York DOT",
                    "email": "gcostanza@gmail.com",
                    "preferred_name": "George Costanza",
                    "scope": "direct-recipient",
                    "role": "admin",
                }
            },
        },
        "body": json.dumps(
            {
                "org_name": "NY DOT",
                "org_id": "123",
                "first_name": "Sophia",
                "last_name": "Canja",
                "email": "sophia@nydot.com",
                "role": "admin",
            }
        ),
    }


def get_removed_user_event():
    return {
        "headers": {},
        "httpMethod": "POST",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "New York DOT",
                    "email": "gcostanza@gmail.com",
                    "preferred_name": "George Costanza",
                    "scope": "direct-recipient",
                    "role": "admin",
                }
            },
        },
        "body": json.dumps(
            {
                "org_name": "NY DOT",
                "org_id": "123",
                "first_name": "Joshua",
                "last_name": "Theisen",
                "email": "joshua@mainedot.com",
                "role": "admin",
            }
        ),
    }


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPostUser.index.send_new_user_email")
def test_lambda_response_body_valid_201(
    mock_send_new_user_email, 
    mock_get_feature_by_enum, 
    _mock_boto3_manager_users
    ):
    mock_get_feature_by_enum.return_value = "True"
    event = get_valid_event()
    api_response = api_post_user(event, None)
    assert api_response.get("statusCode") == 201
    assert mock_send_new_user_email.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_lambda_response_body_invalid_406_missing_body(mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {"Name": "STATION_AUTHORIZES_SR_EMAIL", "Value": "True"}
    event = get_valid_event()
    missing_parameters_body = json.dumps(
        {"org_name": "NY DOT", "org_id": "123", "first_name": "Sophia", "last_name": "Canja"}
    )
    event["body"] = missing_parameters_body
    api_response = api_post_user(event, None)
    assert api_response.get("statusCode") == 406


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_lambda_response_body_invalid_406_malformed_role_in_body(mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {"Name": "Add_User", "Value": "True"}
    event = get_valid_event()
    improper_role_body = json.dumps(
        {
            "org_name": "NY DOT",
            "org_id": "123",
            "first_name": "Sophia",
            "last_name": "Canja",
            "role": "improper_role",
            "email": "sophia@nydot.com",
        }
    )
    event["body"] = improper_role_body
    api_response = api_post_user(event, None)
    assert api_response.get("statusCode") == 406
    assert api_response.get("body") == json.dumps(
        "EvChartMissingOrMalformedBodyError raised. Malformed data in role"
    )


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_lambda_response_body_invalid_406_malformed_orgid_in_body(mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {"Name": "Add_User", "Value": "True"}
    event = get_valid_event()
    improper_role_body = json.dumps(
        {
            "org_name": "NY DOT",
            "org_id": "abc",
            "first_name": "Sophia",
            "last_name": "Canja",
            "role": "admin",
            "email": "sophia@nydot.com",
        }
    )
    event["body"] = improper_role_body
    api_response = api_post_user(event, None)
    assert api_response.get("statusCode") == 406
    assert api_response.get("body") == json.dumps(
        "EvChartMissingOrMalformedBodyError raised. Malformed data in org_id"
    )


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIPostUser.index.add_new_user")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_lmabda_response_body_invalid_500_error_adding_user(
    mock_add_new_user, mock_get_feature_by_enum
):
    mock_get_feature_by_enum.return_value = {"Name": "Add_User", "Value": "True"}
    event = get_valid_event()
    mock_add_new_user.side_effect = KeyError("Error occurred.")

    with pytest.raises(KeyError, match="Error occurred.."):
        api_post_user(event, None)


# testing dynamo db
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_add_new_user_valid(mock_get_feature_by_enum, dynamodb_base):
    mock_get_feature_by_enum.return_value = {"Name": "Add_User", "Value": "True"}
    boto3_session = boto3.session.Session()
    dynamodb = boto3_session.resource("dynamodb")

    event = get_valid_event()
    user_data = json.loads(event["body"])

    add_new_user(user_data, dynamodb)

    # retrieve item from dynamo db table
    table = dynamodb_base.Table("ev-chart_users")
    response = table.get_item(Key={"identifier": user_data["email"]})
    new_user = response.get("Item")
    assert new_user is not None
    assert new_user["identifier"] == "sophia@nydot.com"
    assert new_user["account_status"] == "Pending"
    assert new_user["first_name"] == "Sophia"
    assert new_user["last_name"] == "Canja"
    assert new_user["org_id"] == "123"
    assert new_user["role"] == "admin"


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("evchart_helper.custom_logging.LogEvent.get_auth_token")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPostUser.index.send_new_user_email")
def test_lambda_response_409_adding_existing_user(
    mock_send_new_user_email,
    mock_get_feature_by_enum, 
    mock_auth, 
    _mock_boto3_manager_valid_users
):
    mock_auth.return_value = {
        "org_id": "123",
        "org_name": "New York DOT",
        "recipient_type": "direct-recipient",
    }
    event = get_valid_event()
    event["body"] = json.dumps(
        {
            "org_name": "NY DOT",
            "org_id": "123",
            "first_name": "Sophia",
            "last_name": "Canja",
            "email": "sophia@mainedot.com",
            "role": "admin",
        }
    )
    mock_get_feature_by_enum.return_value = "True"

    response = api_post_user(event, None)
    assert response.get("statusCode") == 409
    assert not mock_send_new_user_email.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_lambda_response_given_false_feature_flag_status_403(mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = "False"
    event = get_valid_event()
    api_response = api_post_user(event, None)
    assert api_response.get("statusCode") == 403


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_lambda_response_given_true_feature_flag_status_201(
    mock_get_feature_by_enum, _mock_boto3_manager_users
):
    mock_get_feature_by_enum.return_value = {"Name": "Add_User", "Value": "True"}
    event = get_valid_event()
    api_response = api_post_user(event, None)
    assert api_response.get("statusCode") == 201


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_lambda_response_given_none_return_500(mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = None
    event = get_valid_event()
    api_response = api_post_user(event, None)
    assert api_response.get("statusCode") == 500


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_lambda_response_given_connection_error_return_():
    event = get_valid_event()
    api_response = api_post_user(event, None)
    assert api_response.get("statusCode") == 500


def test_reactivate_user_given_a_removed_user(_mock_boto3_manager_valid_users, dynamodb_base):
    email = "joshua@mainedot.com"

    table = dynamodb_base.Table("ev-chart_users")
    dynamo_response = table.get_item(Key={"identifier": email})
    new_user = dynamo_response.get("Item")
    assert new_user is not None
    assert new_user["identifier"] == email
    assert new_user["account_status"] == "Removed"

    boto3_session = boto3.session.Session()
    dynamodb = boto3_session.resource("dynamodb")
    response = reactivate_user(email, dynamodb)

    dynamo_response = table.get_item(Key={"identifier": email})
    new_user = dynamo_response.get("Item")
    assert response
    assert new_user is not None
    assert new_user["identifier"] == email
    assert new_user["account_status"] == "Pending"


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPostUser.index.send_new_user_email")
def test_handler_given_a_removed_user_email_return_201(
    mock_send_new_user_email,
    mock_get_feature_by_enum, 
    _mock_boto3_manager_valid_users, dynamodb_base
):
    mock_get_feature_by_enum.return_value = "True"
    table = dynamodb_base.Table("ev-chart_users")
    email = "joshua@mainedot.com"

    response = table.get_item(Key={"identifier": email})
    removed_user = response.get("Item")
    assert removed_user is not None
    assert removed_user["identifier"] == email
    assert removed_user["account_status"] == "Removed"

    event = get_removed_user_event()
    api_response = api_post_user(event, None)
    assert api_response.get("statusCode") == 201

    table = dynamodb_base.Table("ev-chart_users")
    response = table.get_item(Key={"identifier": email})
    reactivated_user = response.get("Item")
    assert reactivated_user is not None
    assert reactivated_user["identifier"] == email
    assert reactivated_user["account_status"] == "Pending"
    assert mock_send_new_user_email.called
