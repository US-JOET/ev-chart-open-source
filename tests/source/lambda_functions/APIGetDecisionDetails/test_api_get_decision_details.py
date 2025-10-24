from unittest.mock import patch, MagicMock
from copy import deepcopy
from evchart_helper.custom_exceptions import EvChartUserNotAuthorizedError, EvChartJsonOutputError
from APIGetDecisionDetails.index import (
    handler as api_get_decision_details
)
import os

event = {
  "headers": {},
  "httpMethod": "GET",
  "requestContext": {
    "accountId": "414275662771",
    "authorizer": {
      "claims": {
        "org_id": "10001",
        "org_friendly_id": "1",
        "org_name": "Illinois",
        "email": "importantdr@yahoo.com",
        "scope": "direct-recipient",
        "preferred_name": "Important Direct Recipient",
        "role" : "admin"
      }
    }
  },
  "queryStringParameters":{
     "upload_id": "1234567"
  }
}


# 200, success
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('evchart_helper.api_helper.execute_query')
@patch('APIGetDecisionDetails.index.is_valid_upload_id')
@patch('APIGetDecisionDetails.index.format_data')
@patch('APIGetDecisionDetails.index.get_org_info_dynamo')
@patch('APIGetDecisionDetails.index.aurora')
@patch('APIGetDecisionDetails.index.get_decision_info')
def test_valid_200( mock_get_decision_info, mock_aurora, mock_get_org_info_dynamo, mock_format_data, mock_valid_upload_id, mock_execute_query):
  mock_valid_upload_id.return_value = True
  mock_execute_query.return_value = ["123"]

  mock_get_decision_info.return_value = {
  "upload_id": "106",
  "module_id": "3",
  "decision": "Approved",
  "decision_date": "2024-03-29 20:17:26",
  "reviewer": "Important DR",
  "comments": "",
  }
  mock_format_data.return_value = {
  "upload_id": "106",
  "module_id": "3",
  "decision": "Approved",
  "decision_date": "2024-03-29 20:17:26",
  "reviewer": "Important DR",
  "comments": "",
  "decision_explanation": "It is good data"
  }
  mock_get_org_info_dynamo.return_value = {"name": "New York DOT"}

  response = api_get_decision_details(event, None)
  assert response.get('statusCode') == 200
  assert mock_aurora.get_connection.called

# 400, EvChartMissingOrMalformedBodyError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetDecisionDetails.index.aurora')
def test_missing_upload_id(mock_aurora):
  missing_upload_id_event = deepcopy(event)
  missing_upload_id_event["queryStringParameters"]["upload_id"] = []
  response = api_get_decision_details(missing_upload_id_event, None)
  assert response.get('statusCode') == 400

# 400, EvChartMissingOrMalformedBodyError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetDecisionDetails.index.is_valid_upload_id')
@patch('APIGetDecisionDetails.index.aurora')
def test_invalid_upload_id(mock_aurora, mock_is_valid_upload_id):
  mock_is_valid_upload_id.return_value = False
  response = api_get_decision_details(event, None)
  assert response.get('statusCode') == 400

# 403, EvChartUserNotAuthorizedError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetDecisionDetails.index.get_decision_info')
@patch('APIGetDecisionDetails.index.is_valid_upload_id')
@patch('APIGetDecisionDetails.index.aurora')
def test_invalid_403(mock_aurora, mock_is_valid_upload_id, mock_get_decision_info):
  mock_get_decision_info.side_effect = EvChartUserNotAuthorizedError(log_obj=MagicMock())
  mock_is_valid_upload_id.return_value = True
  response = api_get_decision_details(event, None)
  assert response.get('statusCode') == 403

# 500, EvChartJsonOutputError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetDecisionDetails.index.get_org_info_dynamo')
@patch('APIGetDecisionDetails.index.get_decision_info')
@patch('APIGetDecisionDetails.index.is_valid_upload_id')
@patch('APIGetDecisionDetails.index.format_data')
@patch('APIGetDecisionDetails.index.aurora')
def test_invalid_formatting_of_decision_500(
  mock_auth,
  mock_format_data,
  mock_is_valid_upload_id,
  mock_get_decision_info,
  mock_org_info
  ):
  mock_is_valid_upload_id.return_value = True
  mock_get_decision_info.return_value = [{"decision": "rejected"}]
  mock_org_info.return_value = [{"name": "Penn DOT"}]
  mock_format_data.side_effect = EvChartJsonOutputError(log_obj=MagicMock())
  response = api_get_decision_details(event, None)
  assert response.get('statusCode') == 500

# 401, EvChartAuthorizationTokenInvalidError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetDecisionDetails.index.aurora')
def test_invalid_auth_token_401(mock_aurora):
  invalid_event = {
    "headers": {},
    "httpMethod": "GET",
    "requestContext": {
      "accountId": "414275662771",
      "authorizer": {
        "claims": {
          "org_id": "10001",
          "org_friendly_id": "1",
          "org_name": "Illinois",
          "email": "importantdr@yahoo.com",
        }
      }
    },
    "queryStringParameters":{
      "upload_id": "1234567"
    }
  }
  response = api_get_decision_details(invalid_event, None)
  assert response.get('statusCode') == 401
