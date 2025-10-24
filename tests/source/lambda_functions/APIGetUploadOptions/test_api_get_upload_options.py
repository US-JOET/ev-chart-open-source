import os
from unittest.mock import patch

import feature_toggle
import pytest
from APIGetUploadOptions.index import handler as api_get_upload_options
from database_central_config import DatabaseCentralConfig
from evchart_helper.custom_exceptions import EvChartDatabaseAuroraQueryError
from feature_toggle.feature_enums import Feature

event = {
    "headers": {},
    "httpMethod": "SELECT",
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
                "role": "admin",
            }
        },
    },
}

jo_event = {
    "headers": {},
    "httpMethod": "SELECT",
    "requestContext": {
        "accountId": "414275662771",
        "authorizer": {
            "claims": {
                "org_id": "1234",
                "org_friendly_id": "2",
                "org_name": "JOET",
                "email": "joet@ee.doe.gov",
                "scope": "joet",
                "preferred_name": "",
                "role": "admin",
            }
        },
    },
}


@pytest.fixture(name="config")
def fixture_config():
    return DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json",
        )
    )


# 200, valid response
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetUploadOptions.index.aurora")
@patch("APIGetUploadOptions.index.get_authorized_drs")
def test_valid_200(mock_get_auth_drs, mock_aurora, mock_feature_toggle):
    mock_get_auth_drs.return_value = {"123": "NYC DOT", "456": "Pennsylvania DOT"}

    response = api_get_upload_options(event, None)
    assert response.get("statusCode") == 200


# 500, EvChartDatabaseAuroraQueryError
@patch("APIGetUploadOptions.index.get_authorized_drs")
def test_invalid_EvChartDatabaseAuroraQueryError_500(mock_get_auth_drs):
    mock_get_auth_drs.side_effect = EvChartDatabaseAuroraQueryError

    with pytest.raises(Exception):
        response = api_get_upload_options(event, None)
        assert response.get("statusCode") == 500


# 403, EvChartUserNotAuthorizedError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetUploadOptions.index.aurora")
def test_invalid_EvChartUserNotAuthorizedError_403(mock_aurora, mock_feature_toggle):

    response = api_get_upload_options(jo_event, None)
    assert response.get("statusCode") == 403


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetUploadOptions.index.aurora")
@patch("APIGetUploadOptions.index.DatabaseCentralConfig")
@patch("APIGetUploadOptions.index.get_authorized_drs")
def test_central_config_ft_true(
    mock_get_authorized_drs,
    mock_database_central_config,
    mock_aurora,
    mock_get_active_feature_toggles,
    config,
):
    mock_database_central_config.return_value = config
    mock_get_active_feature_toggles.return_value = {Feature.DATABASE_CENTRAL_CONFIG}
    mock_get_authorized_drs.return_value = {"123": "NYC DOT", "456": "Pennsylvania DOT"}

    response = api_get_upload_options(event, None)
    assert response.get("statusCode") == 200
    assert mock_database_central_config.called
    assert mock_aurora.get_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetUploadOptions.index.aurora")
@patch("APIGetUploadOptions.index.DatabaseCentralConfig")
@patch("APIGetUploadOptions.index.get_authorized_drs")
def test_central_config_ft_false(
    mock_get_authorized_drs,
    mock_database_central_config,
    mock_aurora,
    mock_get_active_feature_toggles,
    config,
):
    mock_database_central_config.return_value = config
    mock_get_active_feature_toggles.return_value = set()
    mock_get_authorized_drs.return_value = {"123": "NYC DOT", "456": "Pennsylvania DOT"}

    response = api_get_upload_options(event, None)
    assert response.get("statusCode") == 200
    assert not mock_database_central_config.called
    assert mock_aurora.get_connection.called

