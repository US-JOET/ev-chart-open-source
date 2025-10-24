from unittest.mock import patch, MagicMock
import os

from evchart_helper.custom_exceptions import EvChartDatabaseDynamoQueryError

# module paths are set in conftest.py
from APIGetOrgUserData.index import (
    handler as api_get_org_user_data,
)


event = {
  "headers": {},
  "httpMethod": "MODIFY",
  "requestContext": {
    "accountId": "414275662771",
    "authorizer": {
      "claims": {
        "org_id": "123",
        "org_friendly_id": "1",
        "org_name": "New York DOT",
        "email": "dev@ee.doe.gov",
        "scope": "direct-recipient",
        "preferred_name": "",
        "role": "admin"
      }
    }
  }
}


# Users found, return 200
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetOrgUserData.index.get_user_data')
def test_valid_200(mock_get_user_data):
  mock_get_user_data.return_value = 17

  users_response = api_get_org_user_data(event, None)
  assert users_response.get('statusCode') == 200


# 200, empty response
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetOrgUserData.index.get_user_data')
def test_valid_empty_200(mock_get_user_data):
  mock_get_user_data.return_value = 0

  users_response = api_get_org_user_data(event, None)
  assert users_response.get('statusCode') == 200


# Dynamo Query Error, return 500
# pylint: disable=invalid-name
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetOrgUserData.index.get_user_data')
def test_lambda_invalid_EvChartDatabaseDyanmoQueryError_500(mock_get_user_data):
  mock_get_user_data.side_effect = EvChartDatabaseDynamoQueryError(log_obj=MagicMock(), operation="Select")
  response = api_get_org_user_data(event, None)
  assert response.get('statusCode') == 500
