from unittest.mock import patch, MagicMock
from datetime import datetime
import pytest
import pandas
import os
import json
from dateutil import tz
from APIGetImportErrorData.index import handler as api_get_import_error_data, format_dataframe_date
from evchart_helper.custom_exceptions import EvChartDatabaseAuroraQueryError, EvChartJsonOutputError
import feature_toggle


@pytest.fixture(name="event")
def get_valid_event():
  return {
    "headers": {},
    "httpMethod": "MODIFY",
    "requestContext": {
      "accountId": "414275662771",
      "authorizer": {
        "claims": {
          "org_id": "1234",
          "org_friendly_id": "1",
          "org_name": "Utah DOT",
          "email": "dev@ee.doe.gov",
          "scope": "direct-recipient",
          "preferred_name": "",
          "role": "admin"
        }
      }
    },
    "queryStringParameters": {
      "upload_id": "0987"
    }
}

# 200, valid response
@patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetImportErrorData.index.get_error_data_as_df')
@patch('APIGetImportErrorData.index.is_valid_upload_id')
@patch('APIGetImportErrorData.index.aurora')
def test_200_valid_response(mock_aurora, mock_valid_upload, mock_df, mock_get_ft, event):
  mock_valid_upload.return_value = True
  utc_tz = tz.gettz("UTC")
  timestamp = datetime(2023, 12, 31, 23, 59, 59, tzinfo=utc_tz)
  df = pandas.DataFrame(data={
        "port_id": ["193-456-7"],
        "power_kw": ["202410.02"],
        "energy_kwh": ["20241.01"],
        "session_id": ["10001"],
        "station_id": ["StationMod2"],
        "session_end": [timestamp],
        "station_uuid": ["29a289ab-8cf3-4789-82e1-7cdc548505f6"],
        "session_error": ["ERROR1"],
        "session_start": [timestamp],
        "payment_method": ["VISA"]
    })
  mock_df.return_value = df
  response = api_get_import_error_data(event, None)
  assert response.get('statusCode') == 200


# 400, EvChartMissingOrMalformedHeadersError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetImportErrorData.index.aurora')
def test_missing_query_params_400(mock_aurora, mock_get_ft, event):
  event["queryStringParameters"] = {}
  response = api_get_import_error_data(event, None)
  assert response.get('statusCode') == 400


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetImportErrorData.index.execute_query_fetchone')
@patch('APIGetImportErrorData.index.aurora')
def test_malformed_upload_id_400(mock_aurora, mock_execute, mock_get_ft, event):
  mock_execute.return_value = (0,)
  response = api_get_import_error_data(event, None)
  assert response.get('statusCode') == 400


# 401, EvChartAuthorizationTokenInvalidError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetImportErrorData.index.aurora')
def test_invalid_auth_401(mock_aurora, mock_get_ft, event):
  del event["requestContext"]["authorizer"]["claims"]["email"]
  response = api_get_import_error_data(event, None)
  assert response.get('statusCode') == 401

# 500, EvChartDatabaseAuroraQueryError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetImportErrorData.index.execute_query_fetchone')
@patch('APIGetImportErrorData.index.aurora')
def test_invalid_database_500(mock_aurora, mock_query, mock_get_ft, event):
  mock_query.side_effect = EvChartDatabaseAuroraQueryError(operation="Select", log_obj=MagicMock())
  response = api_get_import_error_data(event, None)
  assert response.get('statusCode') == 500


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetImportErrorData.index.format_dataframe_date')
@patch('APIGetImportErrorData.index.get_error_data_as_df')
@patch('APIGetImportErrorData.index.is_valid_upload_id')
@patch('APIGetImportErrorData.index.aurora')
def test_json_error_formatting_datetime_500(
  mock_aurora,
  mock_valid_upload,
  mock_df,
  mock_format_date,
  mock_get_ft,
  event):

  mock_valid_upload.return_value = True
  mock_df.return_value =  pandas.DataFrame({"port_id": ["1001"]})
  mock_format_date.side_effect = EvChartJsonOutputError(log_obj=MagicMock())
  response = api_get_import_error_data(event, None)
  assert response.get('statusCode') == 500

@pytest.mark.skipif(os.name == "nt", reason="format_datetime_obj does not work on windows")
def test_format_dataframe_date_with_datetime_changes_timezone_and_formats():
  utc_tz = tz.gettz("UTC")
  test_data = [datetime(2023, 12, 31, 23, 59, 59, tzinfo=utc_tz)]
  column_name = "does_not_matter"
  df = pandas.DataFrame({column_name: test_data})
  format_dataframe_date(df=df)
  assert df[column_name][0] == "12/31/23 11:59 PM UTC"


# JE-5739 Ensuring that nested error messages are correctly returned to enhance debugging
# removed current nested error handling for get_error_data_as_df()
@patch.dict(os.environ, {"AWS_REGION": "us-east-1", "ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch('APIGetImportErrorData.index.execute_query_df')
@patch('APIGetImportErrorData.index.is_valid_upload_id')
@patch('APIGetImportErrorData.index.aurora')
def test_nested_error_message(mock_aurora, mock_valid_upload, mock_execute_query, mock_get_ft, event):
  mock_valid_upload.return_value = True
  mock_execute_query.side_effect = EvChartDatabaseAuroraQueryError(message="message from execute_query_df")
  response = api_get_import_error_data(event, None)
  assert response.get('statusCode') == 500
  assert response.get('body') == json.dumps("EvChartDatabaseAuroraQueryError raised. message from execute_query_df")
