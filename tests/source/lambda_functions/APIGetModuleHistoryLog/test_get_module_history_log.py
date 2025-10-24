import datetime
import json
import os
from unittest.mock import patch, MagicMock
from copy import deepcopy

import pytest
import boto3
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import EvChartUserNotAuthorizedError
from moto import mock_aws


from APIGetModuleHistoryLog.index import (
    handler as api_get_module_history,
    format_module_history_data
)


# creating users table fixture
@pytest.fixture(name="dynamodb_users")
def fixture_dynamodb_users():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName="ev-chart_users",
            KeySchema=[{"AttributeName": "identifier", "KeyType": "HASH"}],
            AttributeDefinitions=[{
                "AttributeName": "identifier", "AttributeType": "S"
            }],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield dynamodb


@pytest.fixture(name="boto3_manager_users")
def mock_boto3_manager_users(dynamodb_users):
    with patch.object(
        Boto3Manager, 'resource', return_value=dynamodb_users
    ) as mock_client:
        yield mock_client


# adding one user into the table
@pytest.fixture(name="dynamodb_valid_user")
def fixture_dynamodb_valid_user(dynamodb_users):
    table = dynamodb_users.Table("ev-chart_users")
    table.put_item(
        Item={
            "identifier": "sophia@mainedot.com",
            "account_status": "Active",
            "first_name": "Sophia",
            "last_generated": str(datetime.datetime.utcnow()),
            "last_name": "Canja",
            "org_id": "123",
            "role": "Admin",
        }
    )

    yield dynamodb_users


# creating org table fixture
@pytest.fixture(name="dynamodb_org")
def fixture_dynamodb_org():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[{"AttributeName": "org_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{
                "AttributeName": "org_id", "AttributeType": "S"
            }],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield dynamodb


@pytest.fixture(name="boto3_manager_org")
def mock_boto3_manager_org(dynamodb_org):
    with patch.object(
        Boto3Manager, 'resource', return_value=dynamodb_org
    ) as mock_client:
        yield mock_client


# adding one org into the table
@pytest.fixture(name="dynamodb_valid_org")
def fixture_dynamodb_valid_org(dynamodb_org):
    table = dynamodb_org.Table("ev-chart_org")
    table.put_item(
        Item={
            "org_id": "123",
            "name": "Maine DOT",
            "org_friendly_id": "3",
            "recipient_type": "direct-recipient"
        }
    )

    yield dynamodb_org


event = {
  "headers": {},
  "httpMethod": "GET",
  "requestContext": {
    "accountId": "414275662771",
    "authorizer": {
      "claims": {
        "org_id": "123",
        "org_friendly_id": "3",
        "org_name": "Maine DOT",
        "email": "sophia@mainedot.com",
        "scope": "direct-recipient",
        "preferred_name": "Important Direct Recipient",
        "role": "admin"
      }
    }
  },
  "queryStringParameters": {
     "upload_id": "1234567"
  }
}


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetModuleHistoryLog.index.aurora.close_connection')
@patch('APIGetModuleHistoryLog.index.aurora.get_connection')
def test_missing_upload_id_400(
    mock_aurora_get_connection, mock_close_connection
):
    invalid_event = deepcopy(event)
    invalid_event["queryStringParameters"] = {}
    response = api_get_module_history(invalid_event, None)
    assert response.get('statusCode') == 400
    assert mock_aurora_get_connection.called
    assert mock_close_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetModuleHistoryLog.index.aurora.close_connection')
@patch('APIGetModuleHistoryLog.index.is_valid_upload_id')
@patch('APIGetModuleHistoryLog.index.aurora.get_connection')
def test_malformed_upload_id_400(
    mock_aurora_get_connection, mock_valid_upload_id, mock_close_connection
):
    mock_valid_upload_id.return_value = False
    response = api_get_module_history(event, None)
    assert response.get('statusCode') == 400
    assert mock_aurora_get_connection.called
    assert mock_close_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetModuleHistoryLog.index.aurora.close_connection')
@patch('APIGetModuleHistoryLog.index.aurora.get_connection')
def test_invalid_auth_token_401(
    mock_aurora_get_connection, mock_close_connection
):
    invalid_event = deepcopy(event)
    del invalid_event["requestContext"]["authorizer"]["claims"]["org_id"]
    response = api_get_module_history(invalid_event, None)
    assert response.get('statusCode') == 401
    assert mock_aurora_get_connection.called
    assert mock_close_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetModuleHistoryLog.index.org_is_authorized')
@patch('APIGetModuleHistoryLog.index.upload_id_is_verified')
@patch('APIGetModuleHistoryLog.index.aurora.close_connection')
@patch('APIGetModuleHistoryLog.index.aurora.get_connection')
def test_unauthorized_org_403(
    mock_aurora_get_connection,
    mock_close_connection,
    mock_verified,
    mock_authorized
):
    mock_verified.return_value = True
    mock_authorized.side_effect = \
        EvChartUserNotAuthorizedError(log_obj=MagicMock())
    response = api_get_module_history(event, None)
    assert response.get('statusCode') == 403
    assert mock_aurora_get_connection.called
    assert mock_close_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetModuleHistoryLog.index.format_fullname_from_email')
@patch('APIGetModuleHistoryLog.index.format_org_name_from_email')
@patch('APIGetModuleHistoryLog.index.format_datetime_obj')
@patch('APIGetModuleHistoryLog.index.get_module_history')
@patch('APIGetModuleHistoryLog.index.org_is_authorized')
@patch('APIGetModuleHistoryLog.index.upload_id_is_verified')
@patch('APIGetModuleHistoryLog.index.aurora.close_connection')
@patch('APIGetModuleHistoryLog.index.aurora.get_connection')
def test_formatting_error_500(
    # pylint: disable=too-many-arguments
    mock_aurora_get_connection,
    mock_close_connection,
    mock_upload_id_verified,
    mock_org_auth,
    mock_module_history,
    mock_datetime,
    mock_org_name,
    mock_full_name
):

    mock_upload_id_verified.return_value = True
    mock_org_auth.return_value = True
    mock_org_name.return_value = None
    mock_full_name.return_value = None
    mock_datetime.return_value = None
    mock_module_history.return_value = [
        {
            "updated_by": "sophia@mainedot.com"
        }
    ]
    response = api_get_module_history(event, None)
    assert response.get('statusCode') == 500
    assert mock_aurora_get_connection.called
    assert mock_close_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetModuleHistoryLog.index.format_datetime_obj')
@patch('APIGetModuleHistoryLog.index.get_module_history')
@patch('APIGetModuleHistoryLog.index.org_is_authorized')
@patch('APIGetModuleHistoryLog.index.upload_id_is_verified')
@patch('APIGetModuleHistoryLog.index.aurora.close_connection')
@patch('APIGetModuleHistoryLog.index.aurora.get_connection')
def test_valid_api_response_200(
    # pylint: disable=too-many-arguments,unused-argument
    mock_aurora_get_connection,
    mock_close_connection,
    mock_upload_id_verified,
    mock_org_auth,
    mock_module_history,
    mock_datetime,
    boto3_manager_users,
    boto3_manager_org,
    dynamodb_org,
    dynamodb_users,
    dynamodb_valid_org,
    dynamodb_valid_user
):
    mock_upload_id_verified.return_value = True
    mock_org_auth.return_value = True
    mock_datetime.return_value = None
    mock_module_history.return_value = [
        {
            "updated_by": "sophia@mainedot.com",
            "changed_data": json.dumps({
                "comments": "Good mod",
                "submission_status": "Submitted"
            })
        }
    ]

    expected_formatted_data = [
        {
            "organization": "Maine DOT",
            "updated_by": "Sophia Canja",
            "changed_data": json.dumps({
                "comments": "Good mod",
                "submission_status": "Submitted"
            }),
            "comments": "Good mod",
            "submission_status": "Submitted"
        }
    ]
    response = api_get_module_history(event, None)
    assert response.get('statusCode') == 200
    assert json.loads(response.get('body')) == expected_formatted_data
    assert mock_aurora_get_connection.called
    assert mock_close_connection.called


# this test pulls out the comments and submission_status variables
# from the changed_data nested dict and puts it into the module_history dict
@patch('APIGetModuleHistoryLog.index.format_fullname_from_email')
@patch('APIGetModuleHistoryLog.index.format_org_name_from_email')
@patch('APIGetModuleHistoryLog.index.format_datetime_obj')
def test_formatting_output_changed_data_variables(
    mock_datetime, mock_org_name, mock_fullname
):
    mock_datetime.return_value = None
    mock_org_name.return_value = None
    mock_fullname.return_value = None
    module_history = [
        {
            "changed_data": json.dumps({
                "submission_status": "Pending"
            })
        },
        {
            "changed_data": json.dumps({
                "comments": "",
                "submission_status": "Submitted"
            })
        }
    ]

    expected_formatted_response = [
        {
            "changed_data": json.dumps({
                "submission_status": "Pending"
            }),
            "submission_status": "Pending"
        },
        {
            "changed_data": json.dumps({
                "comments": "",
                "submission_status": "Submitted"
            }),
            "comments": "",
            "submission_status": "Submitted"
        }
    ]

    response = format_module_history_data(module_history=module_history)
    assert response == expected_formatted_response


@patch('APIGetModuleHistoryLog.index.format_var_in_changed_data')
@patch('APIGetModuleHistoryLog.index.format_datetime_obj')
def test_formatting_org_name_and_full_name(
    # pylint: disable=too-many-arguments,unused-argument
    mock_datetime,
    mock_changed_data,
    dynamodb_users,
    boto3_manager_users,
    boto3_manager_org,
    dynamodb_valid_user,
    dynamodb_org,
    dynamodb_valid_org
):
    mock_datetime.return_value, mock_changed_data.return_value = None, None
    module_history = [
        {"updated_by": "sophia@mainedot.com"}
    ]

    expected_formatted_response = [
        {
            "organization": "Maine DOT",
            "updated_by": "Sophia Canja",
            "submission_status": "Processing"
        }
    ]
    response = format_module_history_data(module_history=module_history)
    assert response == expected_formatted_response


@patch('APIGetModuleHistoryLog.index.format_var_in_changed_data')
@patch('APIGetModuleHistoryLog.index.format_datetime_obj')
def test_preserve_missing_submission_status(
    # pylint: disable=too-many-arguments,unused-argument
    mock_datetime,
    mock_changed_data,
    dynamodb_users,
    boto3_manager_users,
    boto3_manager_org,
    dynamodb_valid_user,
    dynamodb_org,
    dynamodb_valid_org
):
    mock_datetime.return_value = None
    mock_changed_data.return_value = None
    module_history = [
        {"updated_by": "sophia@mainedot.com"},
        {"updated_by": "sophia@mainedot.com", "submission_status": "Rejected"},
        {"updated_by": "sophia@mainedot.com", "comments": "still rejected"}
    ]

    expected_formatted_response = [
        {
            "organization": "Maine DOT",
            "updated_by": "Sophia Canja",
            "submission_status": "Processing"
        },
        {
            "organization": "Maine DOT",
            "updated_by": "Sophia Canja",
            "submission_status": "Rejected"
        },
        {
            "organization": "Maine DOT",
            "updated_by": "Sophia Canja",
            "submission_status": "Rejected",
            "comments": "still rejected"
        }
    ]
    response = format_module_history_data(module_history=module_history)
    assert response == expected_formatted_response
