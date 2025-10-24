from collections import Counter
from unittest.mock import MagicMock, patch
from pandas import DataFrame
import pymysql
import pytest
import pandas as pd

from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartUserNotAuthorizedError
)
from AsyncDataValidation.index import get_dataframe_from_csv
from feature_toggle.feature_enums import Feature
from module_validation import (
    check_duplicate_labels,
    get_dr_and_sr_ids,
    set_station_and_port_ids,
    set_station_uuid,
    upload_data_from_df,
    validate_station_id_and_network_provider_column_in_df,
    validated_dataframe,
    _get_module_fields_by_number
)
from error_report_messages_enum import ErrorReportMessages

missing_station_id_files = [
    "station_id_missing_column_header_name_mod_9.csv",
    "station_id_missing_column_header_mod_8.csv",
    "station_id_missing_column_header_mod_7.csv",
    "station_id_missing_column_header_mod_6.csv",
    "station_id_missing_column_header_mod_5.csv",
    "station_id_missing_column_header_mod_4.csv",
    "station_id_missing_column_header_mod_3.csv",
]

missing_network_provider_files = [
    "network_provider_missing_column_header_mod_3.csv",
    "network_provider_missing_column_header_mod_4.csv",
    "network_provider_missing_column_header_mod_5.csv",
    "network_provider_missing_column_header_mod_6.csv",
    "network_provider_missing_column_header_mod_7.csv",
    "network_provider_missing_column_header_mod_8.csv",
    "network_provider_missing_column_header_mod_9.csv"
]
def test_get_dr_and_sr_ids_given_direct_recipient_returns_values():
    recipient_type = "direct-recipient"
    request_headers = {
        'comments': 'uncaught error',
        'module_id': '9',
        'org_id': '3824c24b-f4fa-44bb-b030-09e99c3e4b6c',
        'parent_org': '3824c24b-f4fa-44bb-b030-09e99c3e4b6c',
        'quarter': '',
        'submission_status': 'Error',
        'upload_id': '159cb9b0-82c0-49ef-a006-7fff135b584b',
        'upload_friendly_id': 56,
        'updated_by': 'arif.rasmi@ee.doe.gov',
        'updated_on': "",
        'year': '2024'
    }
    result = get_dr_and_sr_ids(recipient_type, request_headers)
    dr_id, sr_id = result
    assert dr_id == request_headers['org_id']
    assert sr_id is None


def test_get_dr_and_sr_ids_given_sub_recipient_returns_values():
    recipient_type = "sub-recipient"
    request_headers = {
        'comments': 'uncaught error',
        'module_id': '9',
        'org_id': '3824c24b-f4fa-44bb-b030-09e99c3e4b6c',
        'parent_org': '3824c24b-f4fa-44bb-b030-09e99c3e4b6c',
        'quarter': '',
        'submission_status': 'Error',
        'upload_id': '159cb9b0-82c0-49ef-a006-7fff135b584b',
        'upload_friendly_id': 56,
        'updated_by': 'arif.rasmi@ee.doe.gov',
        'updated_on': "", 'year': '2024'
    }
    result = get_dr_and_sr_ids(recipient_type, request_headers)
    dr_id, sr_id = result
    assert dr_id == request_headers['parent_org']
    assert sr_id == request_headers['org_id']


def test_get_dr_and_sr_ids_given_no_recipient_returns_error():
    recipient_type = ""
    request_headers = {}
    with pytest.raises(EvChartUserNotAuthorizedError):
        get_dr_and_sr_ids(recipient_type, request_headers)


@patch("module_validation.get_station_uuid", side_effect=pymysql.Error)
def test_set_station_uuid_handles_error_given_get_station_uuid_raises_error(
    mock_get_station_uuid
):
    cursor = MagicMock()
    data = {
        'random': ['unit_test'],
        'network_provider': ['test_np'],
        'station_id': ['test_staiton_id']
    }
    df = DataFrame(data)
    dr_id = '3824c24b-f4fa-44bb-b030-09e99c3e4b6c'
    with pytest.raises(EvChartDatabaseAuroraQueryError):
        set_station_uuid(df, dr_id, cursor, [])
    assert mock_get_station_uuid.called


@patch("module_validation.get_station_and_port_uuid", side_effect=pymysql.Error)
def test_set_station_and_port_ids_handles_error_given_get_station_and_port_uuid_raises_error(
    mock_get_station_and_port_uuid
):
    cursor = MagicMock()
    data = {
        'random': ['unit_test'],
        'network_provider': ['test_np'],
        'station_id': ['test_staiton_id']
    }
    df = DataFrame(data)
    with pytest.raises(EvChartDatabaseAuroraQueryError):
        set_station_and_port_ids(df, cursor)
    assert mock_get_station_and_port_uuid.called


@patch("module_validation.get_station_and_port_uuid")
def test_set_station_and_port_ids_handles_error_given_no_port_info_returned_dont_set_port_uuid(
    mock_get_station_and_port_uuid
):
    expected_station_uuid = '123'
    expected_network_provider_uuid = '111'
    port_id = 'My port'

    mocked_return_dict = {
        'station_uuid': expected_station_uuid,
        'network_provider_uuid': expected_network_provider_uuid,
        'port_uuid': None,
        'port_id': None
    }

    mock_get_station_and_port_uuid.return_value = mocked_return_dict

    df = pd.DataFrame({
        'station_id': ['1'],
        'network_provider': ['1'],
        'port_id': [port_id]
    })

    cursor = MagicMock()
    result = set_station_and_port_ids(df, cursor)

    assert result.loc[0,'station_uuid'] == expected_station_uuid
    assert result.loc[0, 'network_provider_uuid'] == expected_network_provider_uuid
    assert result.loc[0, 'port_id_upload'] == port_id
    assert result.loc[0, 'port_uuid'] is None

@patch("module_validation.get_station_and_port_uuid")
def test_set_station_and_port_ids_handles_error_given_port_info_returned_set_port_uuid(
    mock_get_station_and_port_uuid
):
    expected_station_uuid = '123'
    expected_port_uuid = '999'
    expected_network_provider_uuid = '111'
    port_id = 'My port'

    mocked_return_dict = {
        'station_uuid': expected_station_uuid,
        'network_provider_uuid': expected_network_provider_uuid,
        'port_uuid': expected_port_uuid,
        'port_id': port_id
    }

    mock_get_station_and_port_uuid.return_value = mocked_return_dict

    df = pd.DataFrame({
        'station_id': ['1'],
        'network_provider': ['1'],
        'port_id': [port_id]
    })

    cursor = MagicMock()
    result = set_station_and_port_ids(df, cursor)

    assert result.loc[0,'station_uuid'] == expected_station_uuid
    assert result.loc[0, 'network_provider_uuid'] == expected_network_provider_uuid
    assert result.loc[0, 'port_id_upload'] == port_id
    assert result.loc[0, 'port_uuid'] is expected_port_uuid

@patch("module_validation.get_station_and_port_uuid")
def test_set_station_and_port_ids_handles_error_given_dataframe_with_no_port_id_set_no_port_values(
    mock_get_station_and_port_uuid
):
    expected_station_uuid = '123'
    expected_network_provider_uuid = '111'

    mocked_return_dict = {
        'station_uuid': expected_station_uuid,
        'network_provider_uuid': expected_network_provider_uuid,
        'port_uuid': None,
        'port_id': None
    }

    mock_get_station_and_port_uuid.return_value = mocked_return_dict

    df = pd.DataFrame({
        'station_id': ['1'],
        'network_provider': ['1']
    })

    cursor = MagicMock()
    result = set_station_and_port_ids(df, cursor)

    assert result.loc[0,'station_uuid'] == expected_station_uuid
    assert result.loc[0, 'network_provider_uuid'] == expected_network_provider_uuid
    assert 'port_id_upload' not in result.columns
    assert 'port_uuid' not in result.columns

def test_df_network_provider_missing():
    test_df = DataFrame({'station_id': ['test_staiton_id'], 'port_id': ['port_id']})
    expected_conditions = \
        [{
            'error_row': None,
            'header_name': 'network_provider',
            'error_description': ErrorReportMessages.MISSING_NETWORK_PROVIDER_COLUMN.format()
        }]
    response_conditions = validate_station_id_and_network_provider_column_in_df(test_df)
    assert expected_conditions == response_conditions


@patch("module_validation.adjust_for_booleans")
@patch("awswrangler.mysql.to_sql")
def test_upload_data_from_df_check_boolean_default(
    mock_to_sql, mock_adjust_for_booleans
):
    upload_data_from_df(
        connection=MagicMock(),
        module_number=2,
        df=DataFrame(),
    )
    assert mock_to_sql.called
    assert mock_adjust_for_booleans.called


@patch("module_validation.adjust_for_booleans")
@patch("awswrangler.mysql.to_sql")
def test_upload_data_from_df_check_boolean_false(
    mock_to_sql, mock_adjust_for_booleans
):
    upload_data_from_df(
        connection=MagicMock(),
        module_number=2,
        df=DataFrame(),
        check_boolean=False
    )
    assert mock_to_sql.called
    assert not mock_adjust_for_booleans.called



@pytest.mark.parametrize("filename", missing_station_id_files)
def test_missing_station_id_columns(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
        df = get_dataframe_from_csv(body)
        conditions = \
            validate_station_id_and_network_provider_column_in_df(
                df=df,
            )
    expected_conditions = \
        [{
            'error_row': None,
            'header_name': 'station_id',
            'error_description': ErrorReportMessages.MISSING_REQUIRED_COLUMN.format(column_name='station_id')
        }]
    assert len(conditions) > 0
    assert conditions == expected_conditions


@pytest.mark.parametrize("filename", missing_network_provider_files)
def test_missing_network_provider_columns(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
        df = get_dataframe_from_csv(body)
        conditions = \
            validate_station_id_and_network_provider_column_in_df(
                df=df,
            )
    expected_conditions = \
        [{
            'error_row': None,
            'header_name': 'network_provider',
            'error_description': ErrorReportMessages.MISSING_NETWORK_PROVIDER_COLUMN.format(column_name='network_provider')
        }]
    assert len(conditions) > 0
    assert conditions == expected_conditions


# JE-6897 Critical bug found in 8_3_Release where error reports are generating "An internal error occured". This was generating because
# "header_name" in the conditions list was set to None. Main issue was because the definitions variable in validated_dataframe() was being
# set incorrectly when the central-config ft was on. This test ensures that the correct header_name is being returned in the conditions object
@patch("module_validation.get_validation_records_status")
def test_validated_dataframe_with_errors_when_central_config_true(mock_get_validation_records_status, mock_config):
    df = pd.DataFrame({
        'station_id': ['lemon'],
        'port_id': ['123-456-7'],
        'network_provider': ['blink'],
        'charger_id': ['100'],
        'session_id': ['10001'],
        # invalid datatype for connector_id, must be decimal
        'connector_id': ['abc1'],
        'session_start': ['abc'],
        'session_end': ['2024-01-20T00:00:00Z'],
        'session_error': ['ERROR1'],
        'error_other': ['DETAILS'],
        # invalid number of decimal places for energy_kwh
        'energy_kwh': ['20241.0112'],
        'power_kw': ['20241.02'],
        'payment_method': ['VISA'],
        'payment_other': ['PAYMENTDETAILS'],
        'station_uuid': ['5015cfe1-3b70-43f2-9861-8a819c4b52db']
    })
    feature_toggle_set = {Feature.DATABASE_CENTRAL_CONFIG, Feature.ASYNC_BIZ_MAGIC_MODULE_2}
    module_number = 2
    upload_id = "123"
    module_fields = _get_module_fields_by_number(module_number, feature_toggle_set)

    response = validated_dataframe(module_fields, module_number, df, upload_id, feature_toggle_set)
    conditions = response.get("conditions")
    for error_obj in conditions:
        assert error_obj.get("header_name") is not None
        assert error_obj.get("header_name") in ["session_start", "energy_kwh"]


# JE-6897 Critical bug found in 8_3_Release. This test is to make sure the conditions object is set properly with central-config turned off
@patch("module_validation.get_validation_records_status")
def test_validated_dataframe_with_errors_when_central_config_false(mock_get_validation_records_status):
    df = pd.DataFrame({
        'station_id': ['lemon'],
        'port_id': ['123-456-7'],
        'network_provider': ['blink'],
        'charger_id': ['100'],
        'session_id': ['10001'],
        # invalid datatype for connector_id, must be decimal
        'connector_id': ['abc1'],
        'session_start': ['abc'],
        'session_end': ['2024-01-20T00:00:00Z'],
        'session_error': ['ERROR1'],
        'error_other': ['DETAILS'],
        # invalid number of decimal places for energy_kwh
        'energy_kwh': ['20241.0112'],
        'power_kw': ['20241.02'],
        'payment_method': ['VISA'],
        'payment_other': ['PAYMENTDETAILS'],
        'station_uuid': ['5015cfe1-3b70-43f2-9861-8a819c4b52db']
    })
    feature_toggle_set = {Feature.ASYNC_BIZ_MAGIC_MODULE_2}
    module_number = 2
    upload_id = "123"
    module_fields = _get_module_fields_by_number(module_number, feature_toggle_set)

    response = validated_dataframe(module_fields, module_number, df, upload_id, feature_toggle_set)
    conditions = response.get("conditions")
    for error_obj in conditions:
        assert error_obj.get("header_name") is not None
        assert error_obj.get("header_name") in ["session_start", "energy_kwh"]
