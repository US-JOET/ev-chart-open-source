import json
import os
from unittest.mock import patch

import feature_toggle
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import EvChartDatabaseDynamoQueryError
from APIGetDirectRecipients.index import (
    handler as api_get_direct_recipients,
    create_auth_mapping,
)

from moto import mock_aws
import boto3
import pytest


# creating org table fixture
@pytest.fixture(name="dynamodb_org")
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
                    "KeySchema": [
                        {"AttributeName": "recipient_type", "KeyType": "HASH"}
                    ],
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

        # inserting NY DR
        table.put_item(
            Item={
                "org_id": "2",
                "name": "NY DOT",
                "recipient_type": "direct-recipient",
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

        yield dynamodb


@pytest.fixture(name="mock_boto3_manager")
def fixture_mock_boto3_manager(dynamodb_org):
    with patch.object(
        Boto3Manager, "resource", return_value=dynamodb_org
    ) as mock_client:
        yield mock_client


@pytest.fixture(name="sr_event")
def get_sr_event():
    sr_event = {
        "headers": {},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "987",
                    "org_friendly_id": "3",
                    "org_name": "SR Org",
                    "email": "sr@gmail.com",
                    "preferred_name": "Sub Recipient",
                    "scope": "sub-recipient",
                    "role": "admin",
                }
            },
        },
    }
    return sr_event


@pytest.fixture(name="joet_event")
def get_jo_event():
    joet_event = {
        "headers": {},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "JOET",
                    "email": "gcostanza@gmail.com",
                    "preferred_name": "George Costanza",
                    "scope": "joet",
                    "role": "admin",
                }
            },
        },
    }
    return joet_event


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDirectRecipients.index.aurora")
def test_valid_recipient_type_jo_200(
    mock_aurora, mock_get_feature_by_enum, mock_boto3_manager, joet_event
):
    response = api_get_direct_recipients(joet_event, None)
    expected_res = [
        {
            "org_id": "1",
            "recipient_type": "direct-recipient",
            "name": "Maine DOT",
            "org_friendly_id": "1",
        },
        {
            "org_id": "2",
            "recipient_type": "direct-recipient",
            "name": "NY DOT",
            "org_friendly_id": "2",
        },
    ]
    assert json.loads(response.get("body")) == expected_res


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDirectRecipients.index.get_authorized_drs")
@patch("APIGetDirectRecipients.index.aurora")
def test_valid_recipient_sr_200(
    mock_aurora,
    mock_get_auth,
    mock_feature_toggle,
    mock_boto3_manager,
    dynamodb_org,
    sr_event,
):
    response = api_get_direct_recipients(sr_event, None)
    assert response.get("statusCode") == 200


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIGetDirectRecipients.index.aurora")
def test_invalid_token_401(
    mock_aurora, mock_get_feature_by_enum, mock_boto3_manager, joet_event
):
    del joet_event["requestContext"]["authorizer"]["claims"]["org_id"]
    response = api_get_direct_recipients(joet_event, None)
    assert response.get("statusCode") == 401


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDirectRecipients.index.aurora")
def test_invalid_recipient_type_dr_403(
    mock_aurora, mock_get_feature_by_enum, mock_boto3_manager, joet_event
):
    joet_event["requestContext"]["authorizer"]["claims"]["scope"] = "direct-recipient"
    response = api_get_direct_recipients(joet_event, None)
    assert response.get("statusCode") == 403


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetDirectRecipients.index.get_all_drs_org_info")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDirectRecipients.index.aurora")
def test_invalid_dynamo_query_500(
    mock_aurora,
    mock_get_feature_by_enum,
    mock_get_all_drs_org_info,
    mock_boto3_manager,
    dynamodb_org,
    joet_event,
):
    mock_get_all_drs_org_info.side_effect = EvChartDatabaseDynamoQueryError()
    response = api_get_direct_recipients(joet_event, None)
    assert response.get("statusCode") == 500


def test_create_auth_mapping_single():
    auth_dr_list = {"222": "Pennsylvania DOT"}
    all_drs = [
        {
            "org_id": "111",
            "recipient_type": "direct-recipient",
            "name": "Vermont DOT",
            "org_friendly_id": "6",
        },
        {
            "org_id": "222",
            "recipient_type": "direct-recipient",
            "name": "Pennsylvania DOT",
            "org_friendly_id": "5",
        },
        {
            "org_id": "333",
            "recipient_type": "direct-recipient",
            "name": "Washington DOT",
            "org_friendly_id": "12",
        },
    ]
    expected = [{"org_id": "222", "name": "Pennsylvania DOT", "org_friendly_id": "5"}]
    response = create_auth_mapping(auth_dr_list, all_drs)
    assert response == expected


def test_create_auth_mapping_multiple():
    auth_dr_list = {"222": "Pennsylvania DOT", "555": "Oregon DOT"}
    all_drs = [
        {
            "org_id": "111",
            "recipient_type": "direct-recipient",
            "name": "Vermont DOT",
            "org_friendly_id": "6",
        },
        {
            "org_id": "222",
            "recipient_type": "direct-recipient",
            "name": "Pennsylvania DOT",
            "org_friendly_id": "5",
        },
        {
            "org_id": "555",
            "recipient_type": "direct-recipient",
            "name": "Oregon DOT",
            "org_friendly_id": "4",
        },
    ]
    expected = [
        {"org_id": "222", "name": "Pennsylvania DOT", "org_friendly_id": "5"},
        {"org_id": "555", "name": "Oregon DOT", "org_friendly_id": "4"},
    ]
    response = create_auth_mapping(auth_dr_list, all_drs)
    assert response == expected


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDirectRecipients.index.get_authorized_drs")
@patch("APIGetDirectRecipients.index.aurora")
def test_get_authorized_drs_as_an_sr_valid_200(
    mock_aurora,
    mock_get_auth,
    mock_feature_toggle,
    mock_boto3_manager,
    dynamodb_org,
    sr_event,
):
    mock_get_auth.return_value = {"1": "Maine DOT"}
    expected_body = [
        {
            "org_id": "1",
            "name": "Maine DOT",
            "org_friendly_id": "1",
        }
    ]
    response = api_get_direct_recipients(sr_event, None)
    assert response.get("statusCode") == 200
    assert response.get("body") == json.dumps(expected_body)

    mock_boto3_manager.assert_called_once_with("dynamodb")
    assert isinstance(dynamodb_org, boto3.resources.base.ServiceResource)


def test_event_call(sr_event, joet_event):
    expected_sr = {
        "headers": {},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "987",
                    "org_friendly_id": "3",
                    "org_name": "SR Org",
                    "email": "sr@gmail.com",
                    "preferred_name": "Sub Recipient",
                    "scope": "sub-recipient",
                    "role": "admin",
                }
            },
        },
    }

    expected_jo = {
        "headers": {},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "JOET",
                    "email": "gcostanza@gmail.com",
                    "preferred_name": "George Costanza",
                    "scope": "joet",
                    "role": "admin",
                }
            },
        },
    }

    assert expected_sr == sr_event
    assert expected_jo == joet_event


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDirectRecipients.index.get_authorized_drs")
@patch("APIGetDirectRecipients.index.aurora")
def test_get_all_dr_for_sr_adds_station(
    mock_aurora, mock_get_auth_drs, mock_ft, mock_boto3_manager, dynamodb_org, sr_event
):
    sr_event["queryStringParameters"] = {"route": "station_registration"}
    res = api_get_direct_recipients(sr_event, None)
    expected = [
        {
            "org_id": "1",
            "name": "Maine DOT",
            "recipient_type": "direct-recipient",
            "org_friendly_id": "1",
        },
        {
            "org_id": "2",
            "name": "NY DOT",
            "recipient_type": "direct-recipient",
            "org_friendly_id": "2",
        },
    ]
    assert res.get("body") == json.dumps(expected)
    mock_get_auth_drs.assert_not_called()
