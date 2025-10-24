import os
from unittest.mock import patch, MagicMock
from evchart_helper.custom_exceptions import EvChartDatabaseAuroraQueryError
import feature_toggle
from APIGetAuthorizations.index import (
    handler as api_get_authorizations,
    drs_exist
)

event = {
  "headers": {},
  "httpMethod": "GET",
  "requestContext": {
    "accountId": "414275662771",
    "authorizer": {
      "claims": {
        "org_id": "100",
        "org_friendly_id": "100",
        "org_name": "Sparkflow",
        "email": "spark@gmail.com",
        "scope": "sub-recipient",
        "preferred_name": "",
        "role" : "admin"
      }
    }
  }
}

invalid_event = {
  "headers": {},
  "httpMethod": "GET",
  "requestContext": {
    "accountId": "414275662771",
    "authorizer": {
      "claims": {
        "org_id": "500",
        "org_friendly_id": "500",
        "org_name": "Florida DOT",
        "email": "dr@gmail.com",
        "scope": "direct-recipient",
        "preferred_name": "",
        "role" : "admin"
      }
    }
  }
}


# 200, success
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetAuthorizations.index.drs_exist')
@patch('APIGetAuthorizations.index.aurora')
def test_valid_200(mock_aurora, mock_drs_exist, mock_feature_toggle):
    mock_drs_exist.return_value = True
    response = api_get_authorizations(event, None)
    assert response.get('statusCode') == 200
    assert mock_aurora.get_connection.called


# 400, EvChartMissingOrMalformedHeadersError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetAuthorizations.index.aurora')
def test_invalid_400(mock_aurora, mock_feature_toggle):
    # with pytest.raises(Exception):
    response = api_get_authorizations(invalid_event, None)
    assert response.get('statusCode') == 400
    assert mock_aurora.get_connection.called


# 500, EvChartDatabaseAuroraQueryError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetAuthorizations.index.drs_exist')
@patch('APIGetAuthorizations.index.aurora')
def test_invalid_500(mock_aurora, mock_drs_exist, mock_feature_toggle):
  mock_drs_exist.side_effect = EvChartDatabaseAuroraQueryError(log_obj=MagicMock(), operation="Select")
  response = api_get_authorizations(event, None)
  assert response.get('statusCode') == 500
  assert mock_aurora.get_connection.called


@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetAuthorizations.index.execute_query')
def test_drs_exist_response_true(mock_execute_query, mock_feature_toggle):
    mock_execute_query.return_value = [{'dr_id': 'dr123'}]
    response = drs_exist(org_id='dr123', features=mock_feature_toggle, cursor=MagicMock())
    assert response
