from unittest.mock import patch, MagicMock
import os
import datetime
import feature_toggle
from feature_toggle.feature_enums import Feature
import pytest

from APIGetDashboardSubmissionDetails.index import (
    handler as api_get_dashboard_submission_details,
    format_data,
    validate_org,
    get_station,
    get_dr_id,
    get_sr_id,
    get_year
)

from evchart_helper.module_enums import ModuleNames

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
                    "scope": "direct_recipient",
                    "role": "admin",
                }
            },
        },
        "queryStringParameters": {
            "station": "123",
        },
    }

def get_db_data():
    return {
        {
            "submission_status": "Approved",
            "updated_on": datetime(2024, 10, 3, 14, 53, 15, 160182),
            "upload_id": "123",
            "sr_id": "123abc",
            "dr_id": "123abc",
            "module_id": "5",
            "quarter": "",
            "year": 2023
         }
    }

def get_data_for_format():
    data_date = datetime.datetime(2024, 10, 3, 10, 28, 50)
    return [
        [{
            "upload_id": "2",
            "updated_on": data_date,
            "module_id": "2",
            "quarter": "1",
            "org_id": "1234"
        }],
        [{
            "upload_id": "3",
            "updated_on": data_date,
            "module_id": "3",
            "quarter": "2",
            "org_id": "1234"
        }],
        [{
            "upload_id": "4",
            "updated_on": data_date,
            "module_id": "4",
            "quarter": "3",
            "org_id": "1234"
        }],
        [{
            "upload_id": "5",
            "updated_on": data_date,
            "module_id": "5",
            "org_id": "1234"
        }],
        [{
            "upload_id": "6",
            "updated_on": data_date,
            "module_id": "6",
            "org_id": "1234"
        }],
        [{
            "upload_id": "7",
            "updated_on": data_date,
            "module_id": "7",
            "org_id": "1234"
        }],
        [{
            "upload_id": "7",
            "updated_on": data_date,
            "module_id": "7",
            "org_id": "1234"
        }],
        [{
            "upload_id": "8",
            "updated_on": data_date,
            "module_id": "8",
            "org_id": "1234"
        }],
        [{
            "upload_id": "9",
            "updated_on": data_date,
            "module_id": "9",
            "org_id": "1234"
        }]
    ]

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetDashboardSubmissionDetails.index.DatabaseCentralConfig")
@patch('evchart_helper.custom_logging.LogEvent.get_auth_token')
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_feature_toggle_by_enum"
)
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("APIGetDashboardSubmissionDetails.index.aurora")
def test_valid_200_as_dr(
    mock_aurora,
    mock_get_feature_toggle_set,
    mock_get_feature_by_enum,
    mock_auth,
    mock_database_central_config,
    event
):
    mock_get_feature_by_enum.return_value = {
        "Name": "dr-st-dashboard",
        "Value": "True",
    }
    mock_get_feature_toggle_set.return_value = frozenset()

    mock_auth.return_value = {
        "org_id": "1234",
        "recipient_type": "direct-recipient",
        "name": "DR",
        "org_friendly_id": "99",
    }

    response = api_get_dashboard_submission_details(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetDashboardSubmissionDetails.index.DatabaseCentralConfig")
@patch('evchart_helper.custom_logging.LogEvent.get_auth_token')
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_feature_toggle_by_enum"
)
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("APIGetDashboardSubmissionDetails.index.aurora")
def test_valid_200_as_dr_with_station(
    mock_aurora,
    mock_get_feature_toggle_set,
    mock_get_feature_by_enum,
    mock_auth,
    mock_database_central_config,
    event
):
    event["queryStringParameters"] = {
        "station": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
    }
    mock_get_feature_by_enum.return_value = {
        "Name": "dr-st-dashboard",
        "Value": "True",
    }
    mock_get_feature_toggle_set.return_value = frozenset()

    mock_auth.return_value = {
        "org_id": "1234",
        "recipient_type": "direct-recipient",
        "name": "DR",
        "org_friendly_id": "99",
    }

    response = api_get_dashboard_submission_details(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200


# 401, EvChartAuthorizationTokenInvalidError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
@patch("APIGetDashboardSubmissionDetails.index.aurora")
def test_lambda_invalid_token_401(mock_aurora, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {
        "Name": "dr-st-dashboard",
        "Value": "True",
    }
    mock_aurora.return_value = MagicMock()

    response = api_get_dashboard_submission_details({"headers": {}}, None)
    assert response.get("statusCode") == 401


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetDashboardSubmissionDetails.index.DatabaseCentralConfig")
@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("APIGetDashboardSubmissionDetails.index.aurora")
def test_invalid_403_user_not_authorized(
    mock_aurora,
    mock_get_feature_toggle_set,
    mock_get_feature_by_enum,
    mock_database_central_config,
    event
):
    mock_get_feature_by_enum.return_value = {
        "Name": "dr-st-dashboard",
        "Value": "True",
    }
    mock_get_feature_toggle_set.return_value = frozenset()
    event["requestContext"]["authorizer"]["claims"]["scope"] = \
        "sub-recipient"

    response = api_get_dashboard_submission_details(event, None)
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
@patch("APIGetDashboardSubmissionDetails.index.DatabaseCentralConfig")  
@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
@patch("APIGetDashboardSubmissionDetails.index.aurora")
def test_validate_org_false(mock_aurora, mock_get_feature_toggle_set, mock_auth, mock_database_central_config, event):
    event["requestContext"]["authorizer"]["claims"]["scope"] = "subrecipient"
    mock_get_feature_toggle_set.return_value = frozenset()
    response = api_get_dashboard_submission_details(event, None)
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
    station = get_station(path_parameters=path_parameters, default_station=default_station)

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
    "get_active_feature_toggles"
)
@patch("APIGetDashboardSubmissionDetails.index.DatabaseCentralConfig")
@patch('evchart_helper.module_helper.get_org_info_dynamo')
def test_format_data_no_config_ft(mock_org_info, mock_database_central_config, mock_get_feature_toggle_set):
    data = get_data_for_format()
    mock_org_info.return_value = {
        "recipient_type": "sub-recipient",
        "name": "Sparkflow",
    }
    mock_get_feature_toggle_set.return_value = frozenset()
    result = format_data(data)
    assert result["quarterly"]["1"][0]["upload_id"] == "2"
    assert result["quarterly"]["2"][0]["upload_id"] == "3"
    assert result["quarterly"]["3"][0]["upload_id"] == "4"
    assert result["annual"][0]["upload_id"] == "5"
    assert result["annual"][1]["upload_id"] == "7"
    assert result["one_time"][0]["upload_id"] == "6"
    assert result["one_time"][1]["upload_id"] == "8"
    assert result["one_time"][2]["upload_id"] == "9"
    assert result["quarterly"]["1"][0]["module_name"] == f"Module 2: {ModuleNames['Module2'].value}"
    assert result["quarterly"]["2"][0]["module_name"] == f"Module 3: {ModuleNames['Module3'].value}"
    assert result["quarterly"]["3"][0]["module_name"] == f"Module 4: {ModuleNames['Module4'].value}"
    assert result["annual"][0]["module_name"] == f"Module 5: { ModuleNames['Module5'].value}"
    assert result["annual"][1]["module_name"] == f"Module 7: {ModuleNames['Module7'].value}"
    assert result["one_time"][0]["module_name"] == f"Module 6: {ModuleNames['Module6'].value}"
    assert result["one_time"][1]["module_name"] == f"Module 8: {ModuleNames['Module8'].value}"
    assert result["one_time"][2]["module_name"] == f"Module 9: {ModuleNames['Module9'].value}"


@patch("APIGetDashboardSubmissionDetails.index.DatabaseCentralConfig")
@patch('evchart_helper.module_helper.get_org_info_dynamo')
def test_format_data_with_config_ft(mock_org_info, mock_database_central_config):
    data = get_data_for_format()
    mock_org_info.return_value = {
        "recipient_type": "sub-recipient",
        "name": "Sparkflow",
    }
    mock_database_central_config().module_display_name.side_effect = [
        "Module 2: Charging Sessions","Module 3: Uptime","Module 4: Outages",
        "Module 5: Maintenance Costs","Module 6: Station Operator Identity",
        "Module 7: Station Operator Program", "Module 7: Station Operator Program",
        "Module 8: DER Information","Module 9: Capital and Installation Costs"
        ]
    mock_database_central_config().module_frequency.side_effect = [
        "quarterly","quarterly","quarterly","annual","one_time","annual","annual","one_time","one_time"
    ]
    result = format_data(data, {Feature.DATABASE_CENTRAL_CONFIG})
    assert result["quarterly"]["1"][0]["upload_id"] == "2"
    assert result["quarterly"]["2"][0]["upload_id"] == "3"
    assert result["quarterly"]["3"][0]["upload_id"] == "4"
    assert result["annual"][0]["upload_id"] == "5"
    assert result["annual"][1]["upload_id"] == "7"
    assert result["one_time"][0]["upload_id"] == "6"
    assert result["one_time"][1]["upload_id"] == "8"
    assert result["one_time"][2]["upload_id"] == "9"
    assert result["quarterly"]["1"][0]["module_name"] == f"Module 2: {ModuleNames['Module2'].value}"
    assert result["quarterly"]["2"][0]["module_name"] == f"Module 3: {ModuleNames['Module3'].value}"
    assert result["quarterly"]["3"][0]["module_name"] == f"Module 4: {ModuleNames['Module4'].value}"
    assert result["annual"][0]["module_name"] == f"Module 5: { ModuleNames['Module5'].value}"
    assert result["annual"][1]["module_name"] == f"Module 7: {ModuleNames['Module7'].value}"
    assert result["one_time"][0]["module_name"] == f"Module 6: {ModuleNames['Module6'].value}"
    assert result["one_time"][1]["module_name"] == f"Module 8: {ModuleNames['Module8'].value}"
    assert result["one_time"][2]["module_name"] == f"Module 9: {ModuleNames['Module9'].value}"