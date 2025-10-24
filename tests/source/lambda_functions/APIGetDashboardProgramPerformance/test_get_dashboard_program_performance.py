from unittest.mock import patch, MagicMock
import os
import feature_toggle
import pytest

from APIGetDashboardProgramPerformance.index import (
    get_sr_id,
    get_year,
    handler as api_get_dashboard_program_performance,
    validate_org,
    get_dr_id,
    get_station,
    generate_query_filters
)


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
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_feature_toggle_by_enum"
)
@patch("APIGetDashboardProgramPerformance.index.aurora")
def test_valid_200_as_jo(
    mock_aurora,
    mock_get_feature_by_enum,
    event,
):
    mock_get_feature_by_enum.return_value = {
        "Name": "jo-pp-dashboard",
        "Value": "True",
    }
    mock_aurora.get_connection.return_value.cursor.return_value\
        .__enter__.return_value.fetchone.return_value = (1, 2)

    response = api_get_dashboard_program_performance(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('evchart_helper.custom_logging.LogEvent.get_auth_token')
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_feature_toggle_by_enum"
)
@patch("APIGetDashboardProgramPerformance.index.aurora")
def test_valid_200_as_dr(
    mock_aurora,
    mock_get_feature_by_enum,
    mock_auth,
    event
):
    mock_get_feature_by_enum.return_value = {
        "Name": "jo-pp-dashboard",
        "Value": "True",
    }
    mock_aurora.get_connection.return_value.cursor.return_value\
        .__enter__.return_value.fetchone.return_value = (1, 2)

    mock_auth.return_value = {
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "recipient_type": "direct-recipient",
        "name": "DR",
        "org_friendly_id": "99",
    }
    
    response = api_get_dashboard_program_performance(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('evchart_helper.custom_logging.LogEvent.get_auth_token')
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_feature_toggle_by_enum"
)
@patch("APIGetDashboardProgramPerformance.index.is_valid_station")
@patch("APIGetDashboardProgramPerformance.index.aurora")
def test_valid_200_as_dr_with_station(
    mock_aurora,
    mock_is_valid_station,
    mock_get_feature_by_enum,
    mock_auth,
    event
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
    mock_aurora.get_connection.return_value.cursor.return_value\
        .__enter__.return_value.fetchone.return_value = (1, 2)

    response = api_get_dashboard_program_performance(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200


# 401, EvChartAuthorizationTokenInvalidError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
@patch("APIGetDashboardProgramPerformance.index.aurora")
def test_lambda_invalid_token_401(mock_aurora, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {
        "Name": "jo-pp-dashboard",
        "Value": "True",
    }
    mock_aurora.return_value = MagicMock()

    response = api_get_dashboard_program_performance({"headers": {}}, None)
    assert response.get("statusCode") == 401


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
@patch("APIGetDashboardProgramPerformance.index.aurora")
def test_invalid_403_user_not_authorized(
    mock_aurora,
    mock_get_feature_by_enum,
    event
):
    mock_get_feature_by_enum.return_value = {
        "Name": "jo-pp-dashboard",
        "Value": "True",
    }
    event["requestContext"]["authorizer"]["claims"]["scope"] = \
        "sub-recipient"

    response = api_get_dashboard_program_performance(event, None)
    assert response.get("statusCode") == 403
    assert mock_aurora.get_connection.called


@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
def test_validate_org_jo(mock_auth):
    mock_auth = {
        "org_id": "1234",
        "recipient_type": "joet",
        "name": "JOET",
        "org_friendly_id": "99",
    }
    statement = validate_org(mock_auth)
    assert statement == "JO"


@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
def test_validate_org_dr(mock_auth):
    mock_auth = {
        "org_id": "1234",
        "recipient_type": "direct-recipient",
        "name": "DR",
        "org_friendly_id": "99",
    }
    statement = validate_org(mock_auth)
    assert statement == "DR"


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
@patch("APIGetDashboardProgramPerformance.index.aurora")
def test_validate_org_false(mock_aurora, mock_auth, event):
    event["requestContext"]["authorizer"]["claims"]["scope"] = "subrecipient"
    response = api_get_dashboard_program_performance(event, None)
    assert response.get("statusCode") == 403
    assert mock_aurora.get_connection.called
    assert mock_auth.called


@pytest.mark.parametrize("default_dr_id", ["All"])
def test_get_dr_id(default_dr_id, event):
    event["queryStringParameters"] = {
        "dr_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    }
    path_parameters = event["queryStringParameters"]
    dr_id = get_dr_id(path_parameters, default_dr_id)

    expected_dr_id = "3824c24b-f4fa-44bb-b030-09e99c3e4b6c"
    assert expected_dr_id == dr_id


# test get_dr_id where no query parameters are provided
@pytest.mark.parametrize("path_parameters", [{}])
@pytest.mark.parametrize("default_dr_id", ["All"])
def test_get_dr_id_with_no_path_parameters(
    default_dr_id, path_parameters
):
    dr_id = get_dr_id(path_parameters, default_dr_id)

    expected_dr_id = default_dr_id
    assert expected_dr_id == dr_id


@pytest.mark.parametrize("default_sr_id", ["All"])
def test_get_sr_id(default_sr_id, event):
    event["queryStringParameters"] = {
        "sr_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    }
    path_parameters = event["queryStringParameters"]
    sr_id = get_sr_id(path_parameters, default_sr_id)

    expected_sr_id = "3824c24b-f4fa-44bb-b030-09e99c3e4b6c"
    assert expected_sr_id == sr_id


@pytest.mark.parametrize("default_sr_id", ["All"])
def test_get_sr_id_no_parameters(default_sr_id):
    sr_id = get_sr_id(None, default_sr_id)

    assert default_sr_id == sr_id


@pytest.mark.parametrize("default_year", ["2024"])
def test_get_year(default_year, event):
    event["queryStringParameters"] = {
        "year": "2023",
    }
    path_parameters = event["queryStringParameters"]
    year = get_year(path_parameters=path_parameters, default_year=default_year)

    expected_year = "2023"
    assert expected_year == year


@pytest.mark.parametrize("path_parameters", [{}])
@pytest.mark.parametrize("default_year", ["2024"])
def test_get_year_with_no_path_parameters(
    default_year, path_parameters
):
    year = get_year(path_parameters, default_year)

    expected_sr_id = default_year
    assert expected_sr_id == year


@pytest.mark.parametrize("default_station", ["123"])
def test_get_station(default_station, event):
    event["queryStringParameters"] = {
        "year": "2023",
    }
    path_parameters = event["queryStringParameters"]
    station = get_station(
        path_parameters=path_parameters, default_station=default_station
    )

    expected_station = "123"
    assert expected_station == station


@pytest.mark.parametrize("path_parameters", [{}])
@pytest.mark.parametrize("default_station", ["123"])
def test_get_station_with_no_path_parameters(
    default_station, path_parameters
):
    station = get_station(path_parameters, default_station)

    expected_station = default_station
    assert expected_station == station


def test_default_dr_id():
    assert get_dr_id(None, "ALL") == "ALL"

@patch.object(
    feature_toggle.FeatureToggleService,
    "get_feature_toggle_by_enum"
)
def test_generate_filters_ft_on(
    mock_get_feature_by_enum
):
    mock_get_feature_by_enum.return_value = "True"
    filters = {"dr_id": "All", "year": "2024"}
    response = generate_query_filters(filters)
    assert "status = 'Active'" in response

def test_generate_filters_ft_off():
    filters = {"dr_id": "All", "year": "2024"}
    response = generate_query_filters(filters)
    assert "status = 'Active'" not in response