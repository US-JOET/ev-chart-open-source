from unittest.mock import patch

import os
import pytest
from evchart_helper.custom_logging import LogEvent

import feature_toggle


# module paths are set in conftest.py
from APIFeatureFlags.index import handler

# TODO: update data to properly reflect return object


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_all_feature_toggles")
@patch.object(LogEvent, "is_auth_token_valid")
def test_handler_returns_list_of_features(mock_get_all_features, mock_log_token_auth):
    mock_get_all_features.return_value = [
        {"Name": "feature1", "Value": "False"},
        {"Name": "feature2", "Value": "False"},
        {"Name": "feature3", "Value": "True"},
    ]
    mock_log_token_auth.return_value = True
    response = handler({"headers":{}}, 1)
    assert response.get("statusCode") == 200
    # assert len(response.get('body')) == 3


# test returns None
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_all_feature_toggles")
@patch.object(LogEvent, "is_auth_token_valid")
def test_handler_returns_None(mock_get_all_features, mock_log_token_auth):
    mock_get_all_features.return_value = {}
    mock_log_token_auth.return_value = True
    response = handler({"headers":{}}, "")
    assert response.get("statusCode") == 200
    # assert len(response.get('body')) == 0


# test connection issue
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(LogEvent, "is_auth_token_valid")
def test_handler_when_no_parameter_store_return_error_status(mock_log_token_auth):
    mock_log_token_auth.return_value = True
    response = handler({"headers":{}}, "")
    assert response.get("statusCode") == 500
    assert (
        response.get("body")
        == '"EvChartFeatureStoreConnectionError raised, unable to connect to parameter store. "'
    )

@patch.object(LogEvent, "is_auth_token_valid")
@pytest.mark.skip(reason="the code block this was testing makes it imposible to use during development, skipping until we resolve this issue")
def test_handler_when_token_validation_fails(mock_log_token_auth):
    mock_log_token_auth.return_value = False
    response = handler("", "")
    assert response.get("statusCode") == 401
    assert response.get("body") == '"EvChartAuthorizationTokenInvalidError raised. "'
