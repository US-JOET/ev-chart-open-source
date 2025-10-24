from unittest.mock import patch, MagicMock
import os
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
import feature_toggle
from APIGetStationsByOrgId.index import (
    handler as api_get_stations_by_org_id,
    get_sr_names_by_station_id,
    add_authorized_srs_to_dataframe,
    add_removable_status_to_dataframe,
    add_federally_funded_status_to_dataframe,
)
from evchart_helper.custom_exceptions import EvChartJsonOutputError

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


invalid_event = {
    "headers": {},
    "httpMethod": "MODIFY",
    "requestContext": {
        "accountId": "414275662771",
        "authorizer": {
            "claims": {
                "org_friendly_id": "1",
                "org_name": "New York DOT",
                "email": "dev@ee.doe.gov",
                "scope": "direct-recipient",
                "preferred_name": "",
                "role": "admin",
                "org_id": "123",
            }
        },
    },
}


# 200, valid response
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetStationsByOrgId.index.get_stations")
@patch("APIGetStationsByOrgId.index.aurora")
def test_valid_200(mock_aurora, mock_get_stations, mock_feature_toggle, event):
    mock_get_stations.return_value = {"station_id": "123", "dr_id": "123"}

    response = api_get_stations_by_org_id(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200

# 200, valid response with query string parameters status = Active
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetStationsByOrgId.index.get_stations")
@patch("APIGetStationsByOrgId.index.aurora")
def test_valid_200_with_status_filter(mock_aurora, mock_get_stations, mock_feature_toggle, event):
    event["queryStringParameters"] = {"status": "Active"}
    mock_get_stations.return_value = {"station_id": "123", "dr_id": "123"}

    response = api_get_stations_by_org_id(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200

# 200, valid response with query string parameters status = Active
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetStationsByOrgId.index.get_stations")
@patch("APIGetStationsByOrgId.index.aurora")
def test_valid_200_with_status_filter(mock_aurora, mock_get_stations, mock_get_feature_toggles, event):
    event["queryStringParameters"] = {"status": "Active"}
    mock_get_stations.return_value = {"station_id": "123", "dr_id": "123"}

    response = api_get_stations_by_org_id(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 200

# 200, valid response for JO recipient type
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetStationsByOrgId.index.execute_query")
@patch("APIGetStationsByOrgId.index.aurora")
def test_valid_jo_200(mock_aurora, mock_execute_query, mock_feature_toggle, event):
    event["requestContext"]["authorizer"]["claims"]["scope"] = "JOET"
    mock_execute_query.return_value = [
        {"dr_id": "123", "station_uuid": "11-11", "station_id": "1"}
    ]
    api_get_stations_by_org_id(event, None)
    assert mock_aurora.get_connection.called

# 401, EvChartAuthorizationTokenInvalidError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetStationsByOrgId.index.aurora")
def test_lambda_response_body_invalid_token_401(mock_aurora):
    mock_aurora.return_value = MagicMock()
    response = api_get_stations_by_org_id({"headers":{}}, None)
    assert response.get("statusCode") == 401

# 400, EvChartMalformedPathParameterError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@pytest.mark.parametrize(
    "status,federal_funding_status,expected",
    [
        ("pending", "all", 400),
        ("pending", "", 400),
        ("active", "all", 200),
        (None, "true", 400),
        (None, "false", 400),
        (None, "fed_funded", 200),
        (None, "non_fed_funded", 200),
        (None, "all", 200),
    ]
)
@patch("APIGetStationsByOrgId.index.get_stations")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetStationsByOrgId.index.aurora")
def test_invalid_path_parameters_passed_in(mock_aurora, mock_feature_toggle, mock_get_stations, status, federal_funding_status, expected, event):
    event["queryStringParameters"] = {
        "station_status": status,
        "federal_funding_status": federal_funding_status,
    }
    mock_get_stations.return_value = []
    response = api_get_stations_by_org_id(event, None)
    assert response.get("statusCode") == expected

def mock_dynamodb_org(org_id):
    org_map = {"1": {"name": "one"}, "2": {"name": "two"}, "3": {"name": "three"}}
    return org_map.get(org_id)


@patch("APIGetStationsByOrgId.index.get_org_info_dynamo", wraps=mock_dynamodb_org)
def test_station_name_mapping(mock_dynamo):
    output = [
        {"station_uuid": "a", "sr_id": "1"},
        {"station_uuid": "a", "sr_id": "2"},
        {"station_uuid": "b", "sr_id": "3"},
    ]

    sr_names = get_sr_names_by_station_id(output)
    assert sr_names.get("a") == ["one", "two"]
    assert sr_names.get("b") == ["three"]
    assert not sr_names.get("c")


def get_station_df():
    synthetic_data = {
        "station_uuid": ["1-1","2-2","3-3"],
        "nickname":["one","two","three"],
        "station_id":["1","2","3"]
    }

    df = pd.DataFrame(synthetic_data)
    return df

@patch("APIGetStationsByOrgId.index.get_sr_names_by_station_id")
@patch("APIGetStationsByOrgId.index.execute_query")
def test_verify_add_authorized_srs_to_dataframe(mock_query_df, mock_sr_names):
    mock_sr_names.return_value = {
        "1-1": "a",
        "2-2": ["b","a"],
        "3-3": ["c","a"],
    }
    df = get_station_df()
    result_df = add_authorized_srs_to_dataframe("org-id", cursor=MagicMock(), output_df=df)

    expected_df = pd.DataFrame({
        "station_uuid": ["1-1", "2-2", "3-3"],
        "nickname":["one","two","three"],
        "station_id":["1","2","3"],
        "authorized_subrecipients": ["a", "b, a", "c, a"]
    })
    assert_frame_equal(result_df, expected_df)


@patch("APIGetStationsByOrgId.index.get_removable_stations_by_dr_id")
def test_verify_add_removable_status_to_dataframe_stations_returned(mock_get_removable):
    mock_get_removable.return_value = ["1-1", "3-3"]
    df = get_station_df()
    expected_df = pd.DataFrame({
        "station_uuid": ["1-1", "2-2", "3-3"],
        "nickname":["one","two","three"],
        "station_id":["1","2","3"],
        "removable": [True, False,True]
    })
    result_df = add_removable_status_to_dataframe(cursor=MagicMock(), dr_id="dr_id", output_df=df)
    assert_frame_equal(result_df, expected_df)


@patch("APIGetStationsByOrgId.index.get_removable_stations_by_dr_id")
def test_verify_add_removable_status_to_dataframe_no_stations_returned(mock_get_removable):
    mock_get_removable.return_value = []
    df = get_station_df()
    expected_df = pd.DataFrame({
        "station_uuid": ["1-1", "2-2", "3-3"],
        "nickname":["one","two","three"],
        "station_id":["1","2","3"],
        "removable": [False, False,False]
    })
    result_df = add_removable_status_to_dataframe(cursor=MagicMock(), dr_id="dr_id", output_df=df)
    assert_frame_equal(result_df, expected_df)


# this issue came up probably from the switch to the new authorization tables for n-tier
# this should gracefully catch the error if an sr was authorized for a station but somehow
# the sr_id was not retained
@patch("APIGetStationsByOrgId.index.get_org_info_dynamo")
def test_get_get_sr_names_by_station_id_sr_id_missing(mock_get_org_info):
    invalid_sr_list = [
        {'station_uuid': '345', 'sr_id': '333'},
        {'station_uuid': '123', 'sr_id': ''},
        {'station_uuid': '1234', 'sr_id': '111'}
    ]
    with pytest.raises(EvChartJsonOutputError) as e:
        get_sr_names_by_station_id(invalid_sr_list)

    assert e.value.message == (
        "EvChartJsonOutputError raised. Error thrown in get_sr_names_by_station_id(). "
        "sr_id expected for station 123 but received an empty string"
    )


@patch("APIGetStationsByOrgId.index.get_all_federally_funded_stations")
def test_add_federally_funded_status_to_dataframe(mock_get_all_federally_funded_stations):
    mock_get_all_federally_funded_stations.return_value = ["1-1", "3-3"]
    df = get_station_df()
    expected_df = pd.DataFrame({
        "station_uuid": ["1-1", "2-2", "3-3"],
        "nickname":["one","two","three"],
        "station_id":["1","2","3"],
        "federally_funded": [True, False,True]
    })
    result_df = add_federally_funded_status_to_dataframe(cursor=MagicMock(), output_df=df)
    assert_frame_equal(result_df, expected_df)