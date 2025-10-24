import os
import pytest
import json
from unittest.mock import MagicMock, patch
from feature_toggle.feature_enums import Feature

# module paths are set in conftest.py
from APIGetNetworkProviders.index import (
    get_network_providers,
    handler as api_get_network_providers,
)
import feature_toggle


@pytest.fixture(name="event")
def get_event():
    return {
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
                    "role": "admin",
                }
            },
        },
    }


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetNetworkProviders.index.execute_query")
@patch("APIGetNetworkProviders.index.aurora")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_valid_200(mock_feature_toggle, mock_aurora, mock_execute_query, event):
    mock_aurora.return_value = MagicMock()
    mock_feature_toggle.return_value = {Feature.NETWORK_PROVIDER_TABLE}
    mock_execute_query.return_value = {
        "beta_technologies": "Beta Technologies"
    }
    response = api_get_network_providers(event, None)
    response_dict = json.loads(response.get("body"))
    assert isinstance(response_dict, dict)
    assert response_dict.get("beta_technologies") == "Beta Technologies"
    assert response.get("statusCode") == 200


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetNetworkProviders.index.aurora")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_invalid_auth_token_401(mock_feature_toggle, mock_aurora):
    mock_aurora.return_value = MagicMock()
    mock_feature_toggle.get_feature_toggle_by_enum.side_effect = "True"
    invalid_event = {"headers": {}}
    response = api_get_network_providers(invalid_event, None)
    assert response.get("statusCode") == 401


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetNetworkProviders.index.execute_query')
@patch('APIGetNetworkProviders.index.aurora')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_get_network_providers(mock_feature_toggle, mock_aurora, mock_execute_query):
    mock_aurora.return_value = MagicMock()
    mock_feature_toggle.get_feature_toggle_by_enum.side_effect = "True"
    mock_execute_query.return_value = \
        [
            {'network_provider_uuid': '123', 'network_provider_value': 'petro_canada', 'description': 'Petro-Canada'},
            {'network_provider_uuid': '234', 'network_provider_value': 'abm', 'description': 'ABM'}
        ]
    expected = [
            {'network_provider_uuid': '123', 'network_provider_value': 'petro_canada', 'description': 'Petro-Canada'},
            {'network_provider_uuid': '234', 'network_provider_value': 'abm', 'description': 'ABM'}
        ]

    response = get_network_providers(MagicMock())
    assert response == expected