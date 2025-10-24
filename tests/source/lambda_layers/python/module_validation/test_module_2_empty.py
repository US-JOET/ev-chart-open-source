import os
from unittest.mock import patch

from database_central_config import DatabaseCentralConfig
from module_validation import validate_m2
from error_report_messages_enum import ErrorReportMessages
from feature_toggle.feature_enums import Feature

import pandas
import pytest


@pytest.fixture(name="config")
def fixture_config():
    return DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json"
        )
    )


def test_records_with_empty_values():
    df = pandas.DataFrame({
        'station_id': ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10"],
        'network_provider': ["np1", "np2", "np3", "np4", "np5", "np6", "np7", "np8", "np9", "np10"],
        'port_id': ["port1", "port2", "port3", "port4", "port5", "port6", "port7", "port8", "port9", "port10"],
        'charger_id': ["", "charger_id_2", "", "", "", "", "", "", "", ""],
        'session_id': ["", "session_id_2", "session_id_3", "session_id_4", "", "", "", "", "", ""],
        'connector_id': ["", "connector_id_2", "", "", "", "", "", "", "", ""],
        'session_start': ["", '2023-07-03T12:51:48Z', "2023-07-03T12:51:48Z", "", "2023-07-03T12:51:48Z", "", "", "", "", ""],
        'session_end': ["", '2023-07-07T12:53:48Z', "2023-07-03T12:53:48Z", "", "", "2023-07-03T12:53:48Z", "", "", "", ""],
        'session_error': ["", 'session_error_2', "session_error_3", "", "", "", "session_error_3", "", "", ""],
        'error_other': ["", "error_other_2", "", "", "", "", "", "", "", ""],
        'energy_kwh': ["", '1.23', "2.23", "", "", "", "", "3.23", "", ""],
        'power_kw': ["", '1.56', "2.56", "", "", "", "", "", "3.56", ""],
        'payment_method': ["", "visa", "visa", "", "", "", "", "", "", "visa"],
        'payment_other': ["", "other", "", "", "", "", "", "", "", ""]
    })

    validation_options = {
        "feature_toggle_set": set([Feature.BIZ_MAGIC]),
        "df": df
    }
    response = validate_m2.validate_empty_session(validation_options)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {3, 4, 5, 6, 7, 8, 9} == error_row_set
    assert {0, 1}.intersection(error_row_set) == set()

    assert len(response.get('conditions', [])) == 42
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='session_start')
    assert response['conditions'][0]['header_name'] == 'session_start'


def test_biz_magic_ft_off():
    validation_options = {
        "feature_toggle_set": set(),
        "df": pandas.DataFrame()
    }
    response = validate_m2.validate_empty_session(validation_options)
    assert response.get('conditions') == []

def test_record_with_only_required_values():
    df = pandas.DataFrame({
        'station_id': ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10"],
        'network_provider': ["np1", "np2", "np3", "np4", "np5", "np6", "np7", "np8", "np9", "np10"],
        'port_id': ["port1", "port2", "port3", "port4", "port5", "port6", "port7", "port8", "port9", "port10"],
        'session_id': ["", "session_id_2", "session_id_3", "session_id_4", "", "", "", "", "", ""],
        'session_start': ["", '2023-07-03T12:51:48Z', "2023-07-03T12:51:48Z", "", "2023-07-03T12:51:48Z", "", "", "", "", ""],
        'session_end': ["", '2023-07-07T12:53:48Z', "2023-07-03T12:53:48Z", "", "", "2023-07-03T12:53:48Z", "", "", "", ""],
        'session_error': ["", 'session_error_2', "session_error_3", "", "", "", "session_error_3", "", "", ""],
        'energy_kwh': ["", '1.23', "2.23", "", "", "", "", "3.23", "", ""],
        'power_kw': ["", '1.56', "2.56", "", "", "", "", "", "3.56", ""],
        'payment_method': ["", "visa", "visa", "", "", "", "", "", "", "visa"],
    })

    validation_options = {
        "feature_toggle_set": set([Feature.BIZ_MAGIC]),
        "df": df
    }
    response = validate_m2.validate_empty_session(validation_options)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {3, 4, 5, 6, 7, 8, 9} == error_row_set
    assert {0, 1}.intersection(error_row_set) == set()

    assert len(response.get('conditions', [])) == 42
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='session_start')
    assert response['conditions'][0]['header_name'] == 'session_start'

@patch("module_validation.validate_m2.DatabaseCentralConfig")
def test_central_config_true(
    mock_database_central_config, config
):
    df = pandas.DataFrame({
        'station_id': [f"s{i}" for i in range(1, 11)],
        'network_provider': [f"np{i}" for i in range(1, 11)],
        'port_id': [f"port{i}" for i in range(1, 11)],
        'session_id': [
            "",
            "session_id_2",
            "session_id_3",
            "session_id_4",
            "",
            "",
            "",
            "",
            "",
            ""
        ],
        'session_start': [
            "",
            '2023-07-03T12:51:48Z',
            "2023-07-03T12:51:48Z",
            "",
            "2023-07-03T12:51:48Z",
            "",
            "",
            "",
            "",
            ""
        ],
        'session_end': [
            "",
            '2023-07-07T12:53:48Z',
            "2023-07-03T12:53:48Z",
            "",
            "",
            "2023-07-03T12:53:48Z",
            "",
            "",
            "",
            ""
        ],
        'session_error': [
            "",
            'session_error_2',
            "session_error_3",
            "",
            "",
            "",
            "session_error_3",
            "",
            "",
            ""
        ],
        'energy_kwh': ["", '1.23', "2.23", "", "", "", "", "3.23", "", ""],
        'power_kw': ["", '1.56', "2.56", "", "", "", "", "", "3.56", ""],
        'payment_method': ["", "visa", "visa", "", "", "", "", "", "", "visa"],
    })

    mock_database_central_config.return_value = config
    validation_options = {
        "feature_toggle_set": {
            Feature.BIZ_MAGIC, Feature.DATABASE_CENTRAL_CONFIG
        },
        "df": df
    }
    response = validate_m2.validate_empty_session(validation_options)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {3, 4, 5, 6, 7, 8, 9} == error_row_set
    assert {0, 1}.intersection(error_row_set) == set()

    assert len(response.get('conditions', [])) == 42
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='session_start')
    assert response['conditions'][0]['header_name'] == 'session_start'
    assert mock_database_central_config.called



@patch("module_validation.validate_m2.DatabaseCentralConfig")
def test_central_config_false(
    mock_database_central_config, config
):
    df = pandas.DataFrame({
        'station_id': [f"s{i}" for i in range(1, 11)],
        'network_provider': [f"np{i}" for i in range(1, 11)],
        'port_id': [f"port{i}" for i in range(1, 11)],
        'session_id': [
            "",
            "session_id_2",
            "session_id_3",
            "session_id_4",
            "",
            "",
            "",
            "",
            "",
            ""
        ],
        'session_start': [
            "",
            '2023-07-03T12:51:48Z',
            "2023-07-03T12:51:48Z",
            "",
            "2023-07-03T12:51:48Z",
            "",
            "",
            "",
            "",
            ""
        ],
        'session_end': [
            "",
            '2023-07-07T12:53:48Z',
            "2023-07-03T12:53:48Z",
            "",
            "",
            "2023-07-03T12:53:48Z",
            "",
            "",
            "",
            ""
        ],
        'session_error': [
            "",
            'session_error_2',
            "session_error_3",
            "",
            "",
            "",
            "session_error_3",
            "",
            "",
            ""
        ],
        'energy_kwh': ["", '1.23', "2.23", "", "", "", "", "3.23", "", ""],
        'power_kw': ["", '1.56', "2.56", "", "", "", "", "", "3.56", ""],
        'payment_method': ["", "visa", "visa", "", "", "", "", "", "", "visa"],
    })

    mock_database_central_config.return_value = config
    validation_options = {
        "feature_toggle_set": {Feature.BIZ_MAGIC},
        "df": df
    }
    response = validate_m2.validate_empty_session(validation_options)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {3, 4, 5, 6, 7, 8, 9} == error_row_set
    assert {0, 1}.intersection(error_row_set) == set()

    assert len(response.get('conditions', [])) == 42
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='session_start')
    assert response['conditions'][0]['header_name'] == 'session_start'
    assert not mock_database_central_config.called
