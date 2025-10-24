import json
import os
from unittest.mock import MagicMock, patch

import boto3
import pytest
from APIGetSubrecipients.index import handler as api_get_subrecipients
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import (EvChartDatabaseAuroraQueryError)
from moto import mock_aws


@pytest.fixture(name="event")
def get_valid_event():
    valid_event = {
        "body": {},
        "headers": {},
        "httpMethod": "GET",
        "queryStringParameters": None,
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
    }
    return valid_event


@pytest.fixture(name="invalid_event")
def get_invalid_event():
    invalid_event = {
        "headers": {},
        "httpMethod": "GET",
        "queryStringParameters": None,
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_name": "Pennsylania DOT",
                    "email": "ebenes@ee.doe.gov",
                    "scope": "direct-recipient",
                    "preferred_name": "Elaine Benes",
                }
            },
        },
    }
    return invalid_event


# creating org table fixture
@pytest.fixture(name="_dynamodb_org")
def fixture_dynamodb_org():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[
                {"AttributeName": "org_id", "KeyType": "HASH"},
                {"AttributeName": "recipient_type", "KeyType": "RANGE"},
            ],
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
        table.wait_until_exists()

        # inserting Maine DR
        table.put_item(
            Item={
                "org_id": "1",
                "name": "Maine DOT",
                "recipient_type": "direct-recipient",
                "org_friendly_id": "1",
            }
        )

        # inserting Spark09 SR
        table.put_item(
            Item={
                "org_id": "2",
                "name": "Spark09",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "2",
            }
        )

        # inserting Sparkflow SR
        table.put_item(
            Item={
                "org_id": "3",
                "name": "Sparkflow",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "3",
            }
        )

        # inserting Evgo SR
        table.put_item(
            Item={
                "org_id": "4",
                "name": "Evgo",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "4",
            }
        )

        yield dynamodb


@pytest.fixture(name="_mock_boto3_manager")
def fixture_mock_boto3_manager(_dynamodb_org):
    with patch.object(Boto3Manager, "resource", return_value=_dynamodb_org) as mock_client:
        yield mock_client


# Users found, return 200
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_valid_return_all_subrecipients_200(event, _mock_boto3_manager, _dynamodb_org):
    result = api_get_subrecipients(event, None)
    assert result.get("statusCode") == 200
    assert json.loads(result.get("body")) == [
        {
            "org_id": "2",
            "recipient_type": "sub-recipient",
            "name": "Spark09",
            "org_friendly_id": "2",
        },
        {
            "org_id": "3",
            "recipient_type": "sub-recipient",
            "name": "Sparkflow",
            "org_friendly_id": "3",
        },
        {"org_id": "4", "recipient_type": "sub-recipient", "name": "Evgo", "org_friendly_id": "4"},
    ]


# Users found, return 200, only return authorized sr's
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetSubrecipients.index.execute_query")
@patch("APIGetSubrecipients.index.aurora")
def test_valid_return_authorized_subrecipients_200(
    mock_aurora, mock_query, _mock_boto3_manager, _dynamodb_org, event
):
    mock_aurora.return_value = MagicMock()
    mock_query.return_value = [{"sr_id": "2"}, {"sr_id": "4"}]
    new_event = event
    new_event["headers"]["only_authorized"] = True
    expected_body = [
        {
            "org_id": "2",
            "recipient_type": "sub-recipient",
            "name": "Spark09",
            "org_friendly_id": "2",
        },
        {"org_id": "4", "recipient_type": "sub-recipient", "name": "Evgo", "org_friendly_id": "4"},
    ]

    users_response = api_get_subrecipients(new_event, None)
    assert users_response.get("statusCode") == 200
    assert json.loads(users_response["body"]) == expected_body
    kwargs = mock_query.call_args.kwargs
    query = kwargs.get('query')
    count = query.count("LEFT JOIN")
    assert "LEFT JOIN" in query
    assert count == 1


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetSubrecipients.index.execute_query")
@patch("APIGetSubrecipients.index.aurora")
def test_valid_only_fed_funded_200(mock_aurora, mock_query, _mock_boto3_manager, event):
    mock_aurora.return_value = MagicMock()
    mock_query.return_value = [{"sr_id": "4"}]
    new_event = event
    new_event["headers"]["only_authorized"] = True
    event["queryStringParameters"] = {"only_fed_funded": "true"}
    expected_body = [
        {"org_id": "4", "recipient_type": "sub-recipient", "name": "Evgo", "org_friendly_id": "4"},
    ]

    users_response = api_get_subrecipients(new_event, None)
    assert users_response.get("statusCode") == 200
    assert json.loads(users_response["body"]) == expected_body
    kwargs = mock_query.call_args.kwargs
    query = kwargs.get('query')
    count = query.count("LEFT JOIN")
    assert "LEFT JOIN" in query
    assert count == 3


# 200, empty response
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetSubrecipients.index.get_srs")
def test_valid_empty_200(mock_get_srs, event):
    mock_get_srs.return_value = []

    users_response = api_get_subrecipients(event, None)
    assert users_response.get("statusCode") == 200
    assert users_response["body"] == "[]"


# dont mock dynamo to cause a failure
# 500, EvChartDatabaseDynamoQueryError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_invalid_500(event):

    users_response = api_get_subrecipients(event, None)
    assert users_response.get("statusCode") == 500
    assert "EvChartDatabaseDynamoQueryError raised." in json.loads(users_response["body"])


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_invalid_auth_token_401(invalid_event):
    return_obj = api_get_subrecipients(invalid_event, None)
    assert return_obj.get("statusCode") == 401


# #JE-6587 Testing when an event does not send back a body
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_no_body_valid_200(event, _mock_boto3_manager, _dynamodb_org):
    event_with_no_body = event
    event_with_no_body["body"] = None
    users_response = api_get_subrecipients(event_with_no_body, None)
    assert users_response.get("statusCode") == 200


# 500, EvChartDatabaseAuroraQueryError
@patch("APIGetSubrecipients.index.get_authorized_srs")
def test_invalid_from_sql_500(mock_get_srs, event):
    mock_get_srs.side_effect = EvChartDatabaseAuroraQueryError
    headers = {"only_authorized": "True"}
    event["headers"] = headers

    with pytest.raises(Exception):
        users_response = api_get_subrecipients(event, None)
        assert users_response.get("statusCode") == 500
        assert users_response["body"] == "Error querying Dynamo"
