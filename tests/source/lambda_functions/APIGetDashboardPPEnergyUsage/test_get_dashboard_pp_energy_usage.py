import json
from unittest.mock import patch, MagicMock
import os
import feature_toggle
import pytest

from APIGetDashboardPPEnergyUsage.index import handler as api_get_dashboard_program_performance


@pytest.fixture(name="event")
def get_valid_event():
    return {
        "headers": {},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "JOET",
                    "email": "dev@ee.doe.gov",
                    "scope": "joet",
                    "role": "admin",
                }
            },
        },
        "queryStringParameters": {
            "dr_id": "All",
        },
    }


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIGetDashboardPPEnergyUsage.index.aurora")
def test_valid_200_as_jo(
    mock_aurora,
    mock_get_feature_by_enum,
    event,
):
    mock_get_feature_by_enum.return_value = {
        "Name": "jo-pp-dashboard",
        "Value": "True",
    }
    mock_aurora.get_connection.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = (
        1,
        2,
    )

    response = api_get_dashboard_program_performance(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200
    response_body = json.loads(response.get("body"))[0]
    assert len(response_body) == 9
    assert "energy_metrics_available"in response_body
    assert "total_charging_sessions"in response_body
    assert "cumulative_energy_federal_ports"in response_body
    assert "dispensing_150kw_sessions"in response_body
    assert "median_charging_session"in response_body
    assert "mode_charging_session"in response_body
    assert "average_charging_power"in response_body
    assert "percentage_nevi_dispensing_150kw"in response_body
    assert "stdev_charging_session"in response_body


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("evchart_helper.custom_logging.LogEvent.get_auth_token")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIGetDashboardPPEnergyUsage.index.aurora")
def test_valid_200_as_dr(mock_aurora, mock_get_feature_by_enum, mock_auth, event):
    mock_get_feature_by_enum.return_value = {
        "Name": "jo-pp-dashboard",
        "Value": "True",
    }
    mock_aurora.get_connection.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = (
        1,
        2,
    )

    mock_auth.return_value = {
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "recipient_type": "direct-recipient",
        "name": "DR",
        "org_friendly_id": "99",
    }

    response = api_get_dashboard_program_performance(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200
    response_body = json.loads(response.get("body"))[0]
    assert len(response_body) == 9
    assert "energy_metrics_available"in response_body
    assert "total_charging_sessions"in response_body
    assert "cumulative_energy_federal_ports"in response_body
    assert "dispensing_150kw_sessions"in response_body
    assert "median_charging_session"in response_body
    assert "mode_charging_session"in response_body
    assert "average_charging_power"in response_body
    assert "percentage_nevi_dispensing_150kw"in response_body
    assert "stdev_charging_session"in response_body



@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("evchart_helper.custom_logging.LogEvent.get_auth_token")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("evchart_helper.dashboard_helper.is_valid_station")
@patch("APIGetDashboardPPEnergyUsage.index.aurora")
def test_valid_200_as_dr_with_station(
    mock_aurora, mock_is_valid_station, mock_get_feature_by_enum, mock_auth, event
):
    event["queryStringParameters"] = {
        "station": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    }
    mock_get_feature_by_enum.return_value = {
        "Name": "jo-pp-dashboard",
        "Value": "True",
    }
    mock_is_valid_station.return_value = []

    mock_auth.return_value = {
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "recipient_type": "direct-recipient",
        "name": "DR",
        "org_friendly_id": "99",
    }
    mock_aurora.get_connection.return_value.cursor.return_value.__enter__.return_value.fetchone.return_value = (
        1,
        2,
    )

    response = api_get_dashboard_program_performance(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200
    response_body = json.loads(response.get("body"))[0]
    assert len(response_body) == 9
    assert "energy_metrics_available"in response_body
    assert "total_charging_sessions"in response_body
    assert "cumulative_energy_federal_ports"in response_body
    assert "dispensing_150kw_sessions"in response_body
    assert "median_charging_session"in response_body
    assert "mode_charging_session"in response_body
    assert "average_charging_power"in response_body
    assert "percentage_nevi_dispensing_150kw"in response_body
    assert "stdev_charging_session"in response_body


# 401, EvChartAuthorizationTokenInvalidError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(target=feature_toggle.FeatureToggleService, attribute="get_feature_toggle_by_enum")
@patch("APIGetDashboardPPEnergyUsage.index.aurora")
def test_lambda_invalid_token_401(mock_aurora, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {
        "Name": "jo-pp-dashboard",
        "Value": "True",
    }
    mock_aurora.return_value = MagicMock()

    response = api_get_dashboard_program_performance({"headers": {}}, None)
    assert response.get("statusCode") == 401


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(target=feature_toggle.FeatureToggleService, attribute="get_feature_toggle_by_enum")
@patch("APIGetDashboardPPEnergyUsage.index.aurora")
def test_invalid_403_user_not_authorized(mock_aurora, mock_get_feature_by_enum, event):
    mock_get_feature_by_enum.return_value = {
        "Name": "jo-pp-dashboard",
        "Value": "True",
    }
    event["requestContext"]["authorizer"]["claims"]["scope"] = "sub-recipient"

    response = api_get_dashboard_program_performance(event, None)
    assert response.get("statusCode") == 403
    assert mock_aurora.get_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(target=feature_toggle.FeatureToggleService, attribute="get_feature_toggle_by_enum")
@patch("APIGetDashboardPPEnergyUsage.index.aurora")
def test_validate_org_false(mock_aurora, mock_auth, event):
    event["requestContext"]["authorizer"]["claims"]["scope"] = "subrecipient"
    response = api_get_dashboard_program_performance(event, None)
    assert response.get("statusCode") == 403
    assert mock_aurora.get_connection.called
    assert mock_auth.called
