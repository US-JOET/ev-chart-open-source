from unittest.mock import patch, MagicMock
import os
import pytest

from APIGetStationsById.index import get_authorized_subrecipients
from APIGetStationsById.index import handler as api_get_stations_by_id, get_station_details
from evchart_helper.custom_exceptions import (EvChartJsonOutputError,
                                              EvChartMissingOrMalformedBodyError,
                                              EvChartUserNotAuthorizedError,
                                              EvChartUnknownException,
                                              EvChartDatabaseAuroraQueryError)
import feature_toggle
from feature_toggle.feature_enums import Feature

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
  },
  "queryStringParameters": {
    "station_uuid": "123"
  }
}

invalid_event = {
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

# 200, valid response
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetStationsById.index.get_port_details')
@patch('APIGetStationsById.index.format_erroneous_fields')
@patch('APIGetStationsById.index.is_valid_org')
@patch('APIGetStationsById.index.get_authorized_subrecipients')
@patch('APIGetStationsById.index.get_station_details')
@patch('APIGetStationsById.index.aurora')
def test_valid_200(mock_aurora, mock_get_station_details,
                   mock_get_authorized_subrecipients, mock_is_valid_org,
                   mock_format_erroneous_fields,
                   mock_ports,
                   mock_toggle_set
                   ):
  mock_toggle_set.return_value = { Feature.NETWORK_PROVIDER_TABLE }
  mock_get_station_details.return_value = {"station_id": "123", "dr_id": "123"}
  mock_get_authorized_subrecipients.return_value = "Sparkflow"
  mock_is_valid_org.return_value = True
  mock_format_erroneous_fields.return_value = {}
  mock_ports.return_value = []

  response = api_get_stations_by_id(event, None)
  assert mock_aurora.get_connection.called
  assert response.get('statusCode') == 200

# 401, EvChartAuthorizationTokenInvalidError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetStationsById.index.aurora')
def test_lambda_response_body_invalid_token_401(mock_aurora, mock_toggle_set):
  mock_toggle_set.return_value = { Feature.NETWORK_PROVIDER_TABLE }
  mock_aurora.return_value = MagicMock()

  response = api_get_stations_by_id({"headers":{}}, None)
  assert response.get('statusCode') == 401

# 406, EvChartMissingOrMalformedBodyError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetStationsById.index.aurora')
def test_missing_station_id_406(mock_aurora, mock_toggle_set):
  mock_toggle_set.return_value = { Feature.NETWORK_PROVIDER_TABLE }
  response = api_get_stations_by_id(invalid_event, None)
  assert response.get('statusCode') == 406

# 406, EvChartMissingOrMalformedBodyError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetStationsById.index.is_valid_org')
@patch('APIGetStationsById.index.aurora')
def test_malformed_station_id_406(mock_aurora, mock_is_valid_org, mock_toggle_set):
  mock_toggle_set.return_value = { Feature.NETWORK_PROVIDER_TABLE }
  mock_is_valid_org.side_effect = EvChartMissingOrMalformedBodyError()
  response = api_get_stations_by_id(event, None)
  assert response.get('statusCode') == 406

# 500, EvChartJsonOutputError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetStationsById.index.aurora')
def test_invalid_status_json_formatting_error_500(mock_aurora, mock_toggle_set):
  mock_toggle_set.return_value = { Feature.NETWORK_PROVIDER_TABLE }
  get_authorized_subrecipients.side_effect = EvChartJsonOutputError()
  response = api_get_stations_by_id(event, None)
  assert response.get('statusCode') == 403

# 403, EvChartUserNotAuthorizedError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetStationsById.index.is_valid_org')
@patch('APIGetStationsById.index.aurora')
def test_user_not_authorized_403(mock_aurora, mock_is_valid_org, mock_toggle_set):
  mock_toggle_set.return_value = { Feature.NETWORK_PROVIDER_TABLE }
  mock_is_valid_org.side_effect = EvChartUserNotAuthorizedError()
  response = api_get_stations_by_id(event, None)
  assert response.get('statusCode') == 403

@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetStationsById.index.get_authorized_subrecipients')
@patch('APIGetStationsById.index.execute_query')
@patch('APIGetStationsById.index.aurora')
def test_get_station_details_for_joet(mock_aurora, mock_execute, mock_get_auth, mock_toggle_set):
  mock_toggle_set.return_value = { Feature.NETWORK_PROVIDER_TABLE }
  mock_execute.return_value = [{"station_uuid": "123"}]
  mock_get_auth.return_value = {"222": "Sparkflow", "333" : "Spark09"}
  expected_res = {
    "station_uuid" : "123",
    "authorized_subrecipients" : {"222": "Sparkflow","333" : "Spark09"}
  }
  response = get_station_details(station_uuid="123", org_id="111", recipient_type="joet", cursor=MagicMock(), feature_toggle_set=MagicMock())
  assert response == expected_res

@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetStationsById.index.get_org_info_dynamo')
@patch('APIGetStationsById.index.execute_query')
@patch('APIGetStationsById.index.aurora')
def test_get_station_details_for_sr(mock_aurora, mock_execute, mock_org_info, mock_feature_toggle):
  mock_execute.return_value = [{"station_uuid": "123", "sr_id": "266a780c-a78e-446a-af26-d2b154e88fc2"}]
  mock_org_info.return_value = {"name": "Org Name"}
  expected_res = {
    'authorized_subrecipients': {
      '266a780c-a78e-446a-af26-d2b154e88fc2': 'Org Name'
    },
    'sr_id': '266a780c-a78e-446a-af26-d2b154e88fc2',
    "station_uuid" : "123"
}
  response = get_station_details(station_uuid="123", org_id="111", recipient_type="sub-recipient", cursor=MagicMock(), feature_toggle_set=mock_feature_toggle)
  assert response == expected_res


@patch('APIGetStationsById.index.get_org_info_dynamo')
@patch('APIGetStationsById.index.execute_query')
def test_get_authorized_subrecipients_unknown_exception_500(mock_execute, mock_get_org_info):
	mock_execute.side_effect = ValueError()
	with pytest.raises(EvChartUnknownException) as e:
		get_authorized_subrecipients({}, "org-id", "recipient-type", {}, MagicMock())
	assert e.value.message == (
   "EvChartUnknownException raised. Error thrown in get_authorized_subrecipients(). "
   "Could not retrieve list of authorized recipients: 'station_uuid'"
  )


@patch('APIGetStationsById.index.execute_query')
def test_get_authorized_subrecipients_aurora_db_error_500(mock_execute):
	mock_execute.side_effect = EvChartDatabaseAuroraQueryError(message="test error message ")
	with pytest.raises(EvChartDatabaseAuroraQueryError) as e:
		get_authorized_subrecipients({"station_uuid": "123"}, "org-id", "recipient-type", {}, MagicMock())
	assert e.value.message == (
   "EvChartDatabaseAuroraQueryError raised. test error message "
   "Error thrown in get_authorized_subrecipients()."
  )
