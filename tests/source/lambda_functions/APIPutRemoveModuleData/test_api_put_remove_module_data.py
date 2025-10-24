
from unittest.mock import patch
import pytest
import json
import os
import feature_toggle

from APIPutRemoveModuleData.index import (
  handler as api_put_remove_module_data
)

@pytest.fixture(name="event")
def get_event():
  event = {
    "headers": {},
    "httpMethod": "PATCH",
    "requestContext": {
      "accountId": "414275662771",
      "authorizer": {
        "claims": {
          "org_id": "1234",
          "org_friendly_id": "1",
          "org_name": "New York DOT",
          "email": "gcostanza@gmail.com",
          "preferred_name": "George Costanza",
          "scope": "direct-recipient",
          "role": "admin"
        }
      }
    },

  "body": json.dumps({"upload_id": "123"})
  }
  return event

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIPutRemoveModuleData.index.remove_module_data')
@patch('APIPutRemoveModuleData.index.execute_query_fetchone')
@patch('APIPutRemoveModuleData.index.aurora')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_valid_dr_deleting_data_200(mock_feature_toggle, mock_aurora, mock_query, mock_remove, event):
    mock_query.return_value = ["Draft"]
    response = api_put_remove_module_data(event, None)
    assert response.get('statusCode') == 201
    assert mock_remove.called

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIPutRemoveModuleData.index.remove_module_data')
@patch('APIPutRemoveModuleData.index.execute_query_fetchone')
@patch('APIPutRemoveModuleData.index.aurora')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_valid_sr_deleting_data_200(mock_feature_toggle, mock_aurora, mock_query, mock_remove, event):
    event["requestContext"]["authorizer"]["claims"]["scope"] = "sub-recipient"
    mock_query.return_value = ["Rejected"]
    response_deleting_rejected_data = api_put_remove_module_data(event, None)
    assert mock_remove.called

    mock_query.return_value = ["Draft"]
    response_deleting_draft_data = api_put_remove_module_data(event, None)
    assert mock_remove.called
    assert response_deleting_rejected_data.get('statusCode') == 201
    assert response_deleting_draft_data.get('statusCode') == 201

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIPutRemoveModuleData.index.execute_query_fetchone')
@patch('APIPutRemoveModuleData.index.aurora')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_malformed_body_406(mock_feature_toggle, mock_aurora, mock_query, event):
    mock_query.return_value = None
    response = api_put_remove_module_data(event, None)
    assert response.get('statusCode') == 406

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIPutRemoveModuleData.index.execute_query_fetchone')
@patch('APIPutRemoveModuleData.index.aurora')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_invalid_dr_deleting_data_403(mock_feature_toggle, mock_aurora, mock_query, event):
    mock_query.return_value = ["Pending Approval"]
    response = api_put_remove_module_data(event, None)
    assert response.get('statusCode') == 403

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIPutRemoveModuleData.index.execute_query_fetchone')
@patch('APIPutRemoveModuleData.index.aurora')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_invalid_sr_deleting_data_403(mock_feature_toggle, mock_aurora, mock_query, event):
    event["requestContext"]["authorizer"]["claims"]["scope"] = "sub-recipient"
    mock_query.return_value = ["Pending Approval"]
    response = api_put_remove_module_data(event, None)
    assert response.get('statusCode') == 403
