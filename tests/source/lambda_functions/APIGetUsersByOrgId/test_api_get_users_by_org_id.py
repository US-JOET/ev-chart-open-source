import os
from unittest.mock import patch, MagicMock

from evchart_helper.custom_exceptions import (
                                              EvChartDatabaseDynamoQueryError,
                                              EvChartJsonOutputError)

# module paths are set in conftest.py
from APIGetUsersByOrgId.index import (
    handler as api_get_users_by_org_id,
    format_users,
    get_org_users
)

import pytest

event = {
  "headers": {},
  "httpMethod": "GET",
  "requestContext": {
    "accountId": "414275662771",
    "authorizer": {
      "claims": {
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "org_friendly_id": "1",
        "org_name": "Pennsylvania DOT",
        "email": "dev@ee.doe.gov",
        "scope": "direct-recipient",
        "preferred_name": "",
        "role": "admin"
      }
    }
  }
}


# 200, valid response
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetUsersByOrgId.index.get_org_users')
@patch('APIGetUsersByOrgId.index.format_users')
def test_valid_200(mock_format_users, mock_get_org_users):
    mock_get_org_users.return_value = {
        "Items": [
            {
                "first_name": "Jerry",
                "last_name": "Seinfeld",
                "identifier": "jseinfeld@gmail.com"
            }, {
                "first_name": "George",
                "last_name": "Costanza",
                "identifier": "gcostanza@gmail.com"
            }
        ]
    }
    mock_format_users.return_value = [
        {
          "first_name": "Jerry",
          "last_name": "Seinfeld",
          "email": "jseinfeld@gmail.com",
          "role": "",
          "status": "Active"
        }, {
            "first_name": "George",
            "last_name": "Costanza",
            "email": "gcostanza@gmail.com",
            "role": "",
            "status": "Active"
        }
    ]

    users_response = api_get_users_by_org_id(event, None)
    assert users_response.get('statusCode') == 200


# 200, empty response
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetUsersByOrgId.index.get_org_users')
@patch('APIGetUsersByOrgId.index.format_users')
def test_valid_empty_200(mock_format_users, mock_get_org_users):
    mock_get_org_users.return_value = {"Items": []}
    mock_format_users.return_value = []

    users_response = api_get_users_by_org_id(event, None)
    assert users_response.get('statusCode') == 200


# 500, EvChartDatabaseDynamoQueryError
def test_invalid_dynamo_500():
    with pytest.raises(EvChartDatabaseDynamoQueryError):
        log = MagicMock()
        response = get_org_users("123", log)
        assert response.get('statusCode') == 500


# 500, EvChartJsonOutputError
def test_invalid_json_500():
    with pytest.raises(EvChartJsonOutputError):
        format_users([])
