from unittest.mock import patch, MagicMock
import pandas
import pytest
import feature_toggle
from feature_toggle.feature_enums import Feature
from error_report_messages_enum import ErrorReportMessages
from AsyncDataValidation.index import get_dataframe_from_csv
from schema_compliance.authorization_registration import (
    get_station_auth_uuid,
    get_auth_and_unauth_stations,
    stations_not_authorized,
    stations_not_registered,
    stations_not_active,
    unauthorized_stations_for_dr
)

# global variables used throughout test cases
# pylint: disable=invalid-name
mock_cursor = MagicMock()
dr_id = "111"
sr_id = "222"

invalid_files_with_missing_network_provider_value = [
    "network_provider_empty_value_mod_3.csv",
    "network_provider_empty_value_mod_4.csv",
    "network_provider_empty_value_mod_5.csv",
    "network_provider_empty_value_mod_6.csv",
    "network_provider_empty_value_mod_7.csv",
    "network_provider_empty_value_mod_8.csv",
    "network_provider_empty_value_mod_9.csv"
]

invalid_files_with_missing_station_id_value = [
    "station_id_empty_value_mod_9.csv",
    "station_id_empty_value_mod_8.csv",
    "station_id_empty_value_mod_7.csv",
    "station_id_empty_value_mod_6.csv",
    "station_id_empty_value_mod_5.csv",
    "station_id_empty_value_mod_4.csv",
    "station_id_empty_value_mod_3.csv"
]


@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_single_station_authorized_valid_sr(mock_feature_toggle):
    # set parameters
    station_id = "1010"
    expected_uuid = "1234"

    # create mock cursor oject and set return value of cursor
    mock_cursor.fetchone.return_value = [expected_uuid]

    response = get_station_auth_uuid(
        cursor=mock_cursor,
        dr_id=dr_id,
        sr_id=sr_id,
        station_uuid=station_id
    )
    assert response == expected_uuid


@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_single_station_not_auth_not_a_valid_sr(mock_feature_toggle):
    station_uuid = "1010"
    expected_result = None
    mock_cursor.fetchone.return_value = None

    response = get_station_auth_uuid(
        cursor=mock_cursor,
        dr_id=dr_id,
        sr_id=sr_id,
        station_uuid=station_uuid
    )
    assert response == expected_result


@patch('schema_compliance.authorization_registration.get_station_auth_uuid')
def test_single_station_is_authorized_valid_sr(
    mock_check_station_authorization
):
    df = pandas.DataFrame(data={
        "station_uuid": ["123123"],
        "station_id": ["friendly station id"],
        "network_provider": ["test_np"]
    })

    mock_check_station_authorization.return_value = "0001"
    mock_cursor.fetchone.return_value = "0001"
    response = get_auth_and_unauth_stations(
        cursor=mock_cursor, dr_id=dr_id, sr_id=sr_id, df=df
    )
    assert response == ["0001"]


@patch('schema_compliance.authorization_registration.get_station_auth_uuid')
def test_single_station_not_authorized_invalid_sr(
    mock_check_station_authorization
):
    df = pandas.DataFrame(data={
        "station_id": ["friendly station id"],
        "station_uuid": ["123123"],
        "network_provider": ["test_np"]
    })

    mock_check_station_authorization.return_value = None

    response = get_auth_and_unauth_stations(
        cursor=mock_cursor, dr_id=dr_id, sr_id=sr_id, df=df
    )
    assert response == [None]


@patch(
    'schema_compliance.authorization_registration.get_auth_and_unauth_stations'
)
def test_get_conditions_list_with_3_unauth_stations(mock_station_auth):
    mock_station_auth.return_value = [None, None, None]
    df = pandas.DataFrame(data={
        "station_id": ["friendly 1", "friendly 2", "friendly 3"],
        "name": ["Sophia", "Sarah", "Ken"],
        "station_uuid": ["333", "111", "222"],
        "network_provider": ["test_np", "test_np", "test_np"]
    })

    expected_res = [
        {
            "error_row": 0,
            "header_name": "station_id",
            "error_description":
                ErrorReportMessages.SR_NOT_AUTHORIZED_TO_SUBMIT.format(station_id="friendly 1", network_provider="test_np")
        },
        {
            "error_row": 1,
            "header_name": "station_id",
            "error_description":
                ErrorReportMessages.SR_NOT_AUTHORIZED_TO_SUBMIT.format(station_id="friendly 2", network_provider="test_np")
        },
        {
            "error_row": 2,
            "header_name": "station_id",
            "error_description":
                ErrorReportMessages.SR_NOT_AUTHORIZED_TO_SUBMIT.format(station_id="friendly 3", network_provider="test_np")
        }
    ]

    response = stations_not_authorized(
        cursor=mock_cursor,
        dr_id="123",
        sr_id="222",
        df=df
    )
    assert response == expected_res


@patch(
    'schema_compliance.authorization_registration.get_auth_and_unauth_stations'
)
def test_get_conditions_list_with_unauth_stations_nps(mock_station_auth):
    mock_station_auth.return_value = [None]
    df = pandas.DataFrame(data={
        "station_id": ["friendly 1"],
        "network_provider": ["test_np"],
        "name": ["Ken"],
        "station_uuid": ["abc123"]
    })

    expected_response = [
        {
            "error_row": 0,
            "header_name": "station_id",
            "error_description":
                ErrorReportMessages.SR_NOT_AUTHORIZED_TO_SUBMIT.format(station_id="friendly 1", network_provider="test_np")
        }
    ]

    response = stations_not_authorized(
        cursor=mock_cursor,
        dr_id="123",
        sr_id="222",
        df=df,
    )
    assert response == expected_response


@patch(
    'schema_compliance.authorization_registration.get_auth_and_unauth_stations'
)
def test_no_unauth_stations(mock_station_auth):
    mock_station_auth.return_value = ["123", "346", "234"]
    df = pandas.DataFrame(data={
        "station_id": ["friendly 1", "friendly 2", "friendly 3"],
        "name": ["Sophia", "Sarah", "Ken"],
        "station_uuid": ["333", "111", "222"]
    })

    expected_res = []
    response = stations_not_authorized(
        cursor=mock_cursor,
        dr_id="123",
        sr_id="222",
        df=df
    )
    assert response == expected_res


@patch(
    'schema_compliance.authorization_registration.get_auth_and_unauth_stations'
)
def test_appending_to_conditions_with_list_of_unauthorized_stations(
    mock_stations_list
):
    mock_stations_list.return_value = [None, "123", None]
    df = pandas.DataFrame(data={
        "station_id": ["friendly 1", "friendly 2", "friendly 3"],
        "name": ["Sophia", "Sarah", "Ken"],
        "station_uuid": ['', "111", "222"],
        "network_provider": ["test_np", "test_np", "test_np"]
    })
    expected_res = [{
        'error_row': 2,
        'header_name': 'station_id',
        'error_description':
            ErrorReportMessages.SR_NOT_AUTHORIZED_TO_SUBMIT.format(station_id="friendly 3", network_provider="test_np")
    }]
    response = stations_not_authorized(mock_cursor, dr_id, sr_id, df)
    assert response == expected_res


def test_all_stations_registered():
    df = pandas.DataFrame(data={
        "station_id": ["friendly 1", "friendly 2", "friendly 3"],
        "name": ["Sophia", "Sarah", "Ken"],
        "station_uuid": ['123', "111", "222"],
        "network_provider": ["test_np", "test_np", "test_np"]
    })
    response = stations_not_registered(df)
    assert not response


def test_all_stations_unregistered():
    df = pandas.DataFrame(data={
        "station_id": ["friendly 1", "friendly 2", "friendly 3"],
        "name": ["Sophia", "Sarah", "Ken"],
        "station_uuid": [None, None, None],
        "network_provider": ["test_np", "test_np", "test_np"]

    })
    response = stations_not_registered(df)
    assert response == [
        {
            'error_row': 0,
            'header_name': 'station_id',
            'error_description':
                ErrorReportMessages.STATION_NOT_REGISTERED.format(station_id="friendly 1", network_provider="test_np")
        },
        {
            'error_row': 1,
            'header_name': 'station_id',
            'error_description':
                ErrorReportMessages.STATION_NOT_REGISTERED.format(station_id="friendly 2", network_provider="test_np")
        },
        {
            'error_row': 2,
            'header_name': 'station_id',
            'error_description':
                ErrorReportMessages.STATION_NOT_REGISTERED.format(station_id="friendly 3", network_provider="test_np")
        }
    ]


def test_all_stations_with_np_unregistered():
    df = pandas.DataFrame(data={
        "station_id": ["friendly 1"],
        "network_provider": ["test_np"],
        "name": ["Ken"],
        "station_uuid": [None]
    })
    response = stations_not_registered(df)
    assert response == [
        {
            'error_row': 0,
            'header_name': 'station_id',
            'error_description':
                ErrorReportMessages.STATION_NOT_REGISTERED.format(station_id="friendly 1", network_provider="test_np")
        }
    ]


@pytest.mark.parametrize("filename", invalid_files_with_missing_station_id_value)
def test_missing_station_id_value_in_csv(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
        df = get_dataframe_from_csv(body)
        df["station_uuid"] = None
        conditions = \
            stations_not_registered(
                df=df,
            )
    expected_conditions = \
        [{
            'error_row': 2,
            'header_name': 'station_id',
            'error_description': ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='station_id')
        }]
    assert len(conditions) > 0
    assert conditions == expected_conditions


@pytest.mark.parametrize("filename", invalid_files_with_missing_network_provider_value)
def test_missing_network_provider_value_in_csv(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
        df = get_dataframe_from_csv(body)
        df["station_uuid"] = None
        conditions = \
            stations_not_registered(
                df=df,
            )
    expected_conditions = \
        [{
            'error_row': 2,
            'header_name': 'network_provider',
            'error_description': ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='network_provider')
        }]
    assert len(conditions) > 0
    assert conditions == expected_conditions


@patch("schema_compliance.authorization_registration.execute_query_df")
def test_stations_not_active_error_present(mock_execute_query_df):
    df = pandas.DataFrame({
        'station_uuid': ['unit_test', 'unit_test3'],
        "network_provider": ['np_test', 'np_test'],
        "station_id": ["friendly 1", "friendly 2"],
    })

    pending_stations_df = pandas.DataFrame({
        'station_uuid': ['unit_test', 'unit_test2', 'unit_test3'],
    })

    mock_execute_query_df.return_value = pending_stations_df
    ft_set = {Feature.SR_ADDS_STATION}
    response = stations_not_active(
        cursor=MagicMock(),
        dr_id="mock_id",
        df=df,
        feature_toggle_set=ft_set
    )
    assert response == [
        {
            'error_row': 0,
            'header_name': 'station_id',
            'error_description':
                ErrorReportMessages.INVALID_STATION_STATUS_PENDING_APPROVAL.format()
        },
        {
            'error_row': 1,
            'header_name': 'station_id',
            'error_description':
                ErrorReportMessages.INVALID_STATION_STATUS_PENDING_APPROVAL.format()
        }
    ]


def test_unauthorized_stations_for_dr_given_empyt_df_returns_empty_array():
    df = pandas.DataFrame({
        'station_uuid': [],
        "network_provider": [],
        "station_id": [],
    })

    result = unauthorized_stations_for_dr(
        cursor=MagicMock(),
        dr_id=dr_id,
        df= df)

    assert not result

@patch("schema_compliance.authorization_registration.execute_query_df")
def test_unauthorized_stations_for_dr_given_valid_import_returns_empty_array(mock_execute_query_df):
    df = pandas.DataFrame({
        'station_uuid': ['unit_test', 'unit_test3'],
        "network_provider": ['np_test', 'np_test'],
        "station_id": ["friendly 1", "friendly 2"],
    })

    pending_stations_df = pandas.DataFrame({
        'station_uuid': [],
    })

    mock_execute_query_df.return_value = pending_stations_df
    response = unauthorized_stations_for_dr(
        cursor=MagicMock(),
        dr_id=dr_id,
        df=df
    )
    assert not response

@patch("schema_compliance.authorization_registration.execute_query_df")
def test_unauthorized_stations_for_dr_given_unauthorized_stations_in_df_returns_error_array(mock_execute_query_df):
    df = pandas.DataFrame({
        'station_uuid': ['unit_test', 'unit_test3', 'two', 'three'],
        "network_provider": ['np_test', 'np_test', 'np_test_2', 'np_test'],
        "station_id": ["friendly 1", "friendly 2", "friendly 3", "friendly 4"],
    })

    pending_stations_df = pandas.DataFrame({
        'station_uuid': ["two", "three"],
    })

    mock_execute_query_df.return_value = pending_stations_df
    response = unauthorized_stations_for_dr(
        cursor=MagicMock(),
        dr_id=dr_id,
        df=df
    )
    assert response == [
        {
            'error_row': 2,
            'header_name': 'station_id',
            'error_description':
                ErrorReportMessages.DR_NOT_AUTHORIZED_TO_SUBMIT.format(station_id=df.iloc[2]["station_id"], network_provider=df.iloc[2]["network_provider"])
        },
        {
            'error_row': 3,
            'header_name': 'station_id',
            'error_description':
                ErrorReportMessages.DR_NOT_AUTHORIZED_TO_SUBMIT.format(station_id=df.iloc[3]["station_id"], network_provider=df.iloc[3]["network_provider"])
        }
    ]

