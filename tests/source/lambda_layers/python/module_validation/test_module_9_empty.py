import os
from unittest.mock import patch

from database_central_config import DatabaseCentralConfig
from module_validation import validate_m9
from error_report_messages_enum import ErrorReportMessages
from feature_toggle.feature_enums import Feature
from AsyncDataValidation.index import get_dataframe_from_csv


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


invalid_missing_values_files = [
    "der_cost_total_empty_value_mod_9.csv",
    "der_install_cost_total_empty_value_mod_9.csv",
    "real_property_cost_total_empty_value_mod_9.csv",
    "equipment_cost_total_empty_value_mod_9.csv",
    "equipment_install_cost_total_empty_value_mod_9.csv",
    "real_real_property_cost_total_empty_value_mod_9.csv",
    "dist_sys_cost_total_mod_empty_value_9.csv",
    "service_cost_total_empty_value_mod_9.csv",

]

empty_install_costs_df = pandas.DataFrame(
    {
        "station_id": ["s1", "s2", "s3", "s4"],
        "project_id": ["p1", "p2", "p3", "p4"],
        "station_upgrade": [False, False, False, False],
        "real_property_acq_date": [
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
        ],
        "real_property_acq_owned": [False, False, False, False],
        "real_property_cost_total": ["", "", "", 7800.89],
        "real_property_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_acq_date": [
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
        ],
        "equipment_acq_owned": [False, False, False, False],
        "equipment_cost_total": ["", "", 6800.89, 7800.89],
        "equipment_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_install_date": [
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
        ],
        "equipment_install_cost_total": ["", "", 6800.89, 7800.89],
        "equipment_install_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_install_cost_elec": ["", "", 6800.89, 7800.89],
        "equipment_install_cost_const": ["", "", 6800.89, 7800.89],
        "equipment_install_cost_labor": ["", "", 6800.89, 7800.89],
        "der_acq_owned": ["", "", False, False],
        "der_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "der_cost_total": ["", "", 6800.89, 7800.89],
        "der_install_cost_total": ["", "", 6800.89, ""],
        "der_install_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "dist_sys_cost_total": ["", "", 6800.89, 7800.89],
        "dist_sys_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "service_cost_total": ["", "", 6800.89, 7800.89],
        "service_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_install_cost_other": ["", "", 6800.89, 7800.89],
    }
)

empty_install_costs_invalid_df = pandas.DataFrame(
    {
        "station_id": ["daniel-test-no-sr"],
        "network_provider": ["chargie"],
        "project_id": ["be1044a8-9217-49a5-84b2-e4984e8cc0bb"],
        "station_upgrade": ["TRUE"],
        "real_property_acq_date": ["2023-08-30T03:59:18Z"],
        "real_property_acq_owned": ["TRUE"],
        "real_property_cost_total": [""],
        "real_property_cost_federal": ["36911.93"],
        "equipment_acq_date": ["2022-12-16T12:22:16Z"],
        "equipment_acq_owned": ["TRUE"],
        "equipment_cost_total": [""],
        "equipment_cost_federal": ["64194.12"],
        "equipment_install_date": ["2022-12-16T12:22:16Z"],
        "equipment_install_cost_total": [""],
        "equipment_install_cost_federal": ["260392.93"],
        "equipment_install_cost_elec": ["176046.38"],
        "equipment_install_cost_const": [""],
        "equipment_install_cost_labor": ["109975.23"],
        "der_acq_owned": ["TRUE"],
        "der_cost_federal": ["373081.59"],
        "der_cost_total": ["638649.01"],
        "der_install_cost_total": ["373081.59"],
        "der_install_cost_federal": ["270054.53"],
        "dist_sys_cost_total": ["441890.51"],
        "dist_sys_cost_federal": ["270054.53"],
        "service_cost_total": ["441890.51"],
        "service_cost_federal": ["316828.27"],
        "equipment_install_cost_other": ["139472.04"],
    }
)

m9_only_required_values_df = pandas.DataFrame(
    {
        "station_id": ["s1", "s2", "s3", "s4"],
        "project_id": ["p1", "p2", "p3", "p4"],
        "real_property_cost_total": [4800.89, 5800.89, 6800.89, ""],
        "real_property_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_install_cost_total": [4800.89, "", 6800.89, 7800.89],
        "equipment_install_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "der_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "der_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "der_install_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "der_install_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "dist_sys_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "dist_sys_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "service_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "service_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
    }
)

m9_only_required_values_df_with_nulls = pandas.DataFrame(
    {
        "station_id": ["s1", "s2", "s3", "s4"],
        "project_id": ["p1", "p2", "p3", "p4"],
        "station_upgrade": ["", "", "", ""],
        "real_property_acq_date": ["", "", "", ""],
        "real_property_acq_owned": ["", "", "", ""],
        "real_property_cost_total": [4800.89, 5800.89, 6800.89, ""],
        "real_property_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_acq_date": ["", "", "", ""],
        "equipment_acq_owned": ["", "", "", ""],
        "equipment_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_install_date": ["", "", "", ""],
        "equipment_install_cost_total": [4800.89, "", 6800.89, 7800.89],
        "equipment_install_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_install_cost_elec": ["", "", "", ""],
        "equipment_install_cost_const": ["", "", "", ""],
        "equipment_install_cost_labor": ["", "", "", ""],
        "der_acq_owned": ["", "", "", ""],
        "der_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "der_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "der_install_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "der_install_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "dist_sys_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "dist_sys_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "service_cost_total": [4800.89, 5800.89, 6800.89, 7800.89],
        "service_cost_federal": [4800.89, 5800.89, 6800.89, 7800.89],
        "equipment_install_cost_other": ["", "", "", ""],
    }
)


def test_records_with_empty_values():
    df = empty_install_costs_df
    validation_options = {
        "feature_toggle_set": set([Feature.ASYNC_BIZ_MAGIC_MODULE_9]),
        "df": df,
    }
    response = validate_m9.validate_empty_capital_install_costs(validation_options)
    error_row_set = {r["error_row"] for r in response.get("conditions", [])}

    assert {2, 3} == error_row_set
    assert {0, 1}.intersection(error_row_set) == set()

    assert len(response.get("conditions", [])) == 2
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='real_property_cost_total')
    assert response['conditions'][0]['header_name'] == 'real_property_cost_total'
    assert response['conditions'][1]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='der_install_cost_total')
    assert response['conditions'][1]['header_name'] == 'der_install_cost_total'



@patch("module_validation.validate_m9.DatabaseCentralConfig")
def test_records_with_empty_values_cc(
    mock_database_central_config, config
):
    df = empty_install_costs_df
    validation_options = {
        "feature_toggle_set": set([Feature.ASYNC_BIZ_MAGIC_MODULE_9, Feature.DATABASE_CENTRAL_CONFIG]),
        "df": df,
    }
    mock_database_central_config.return_value = config
    response = validate_m9.validate_empty_capital_install_costs(validation_options)
    error_row_set = {r["error_row"] for r in response.get("conditions", [])}

    assert {2, 3} == error_row_set
    assert {0, 1}.intersection(error_row_set) == set()

    assert len(response.get("conditions", [])) == 2
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='real_property_cost_total')
    assert response['conditions'][0]['header_name'] == 'real_property_cost_total'
    assert response['conditions'][1]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='der_install_cost_total')
    assert response['conditions'][1]['header_name'] == 'der_install_cost_total'


def test_records_with_empty_values_invalid():
    df = empty_install_costs_invalid_df
    validation_options = {
        "feature_toggle_set": set([Feature.ASYNC_BIZ_MAGIC_MODULE_9]),
        "df": df,
    }
    response = validate_m9.validate_empty_capital_install_costs(validation_options)
    error_row_set = {r["error_row"] for r in response.get("conditions", [])}

    assert {0} == error_row_set
    assert len(response.get("conditions", [])) == 3
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='real_property_cost_total')
    assert response['conditions'][0]['header_name'] == 'real_property_cost_total'
    assert response['conditions'][1]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='equipment_cost_total')
    assert response['conditions'][1]['header_name'] == 'equipment_cost_total'
    assert response['conditions'][2]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='equipment_install_cost_total')
    assert response['conditions'][2]['header_name'] == 'equipment_install_cost_total'


@patch("module_validation.validate_m9.DatabaseCentralConfig")
def test_records_with_empty_values_invalid_cc(
    mock_database_central_config, config
):
    df = empty_install_costs_invalid_df
    validation_options = {
        "feature_toggle_set": set([Feature.ASYNC_BIZ_MAGIC_MODULE_9, Feature.DATABASE_CENTRAL_CONFIG]),
        "df": df,
    }
    mock_database_central_config.return_value = config
    response = validate_m9.validate_empty_capital_install_costs(validation_options)
    error_row_set = {r["error_row"] for r in response.get("conditions", [])}

    assert {0} == error_row_set
    assert len(response.get("conditions", [])) == 3
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='real_property_cost_total')
    assert response['conditions'][0]['header_name'] == 'real_property_cost_total'
    assert response['conditions'][1]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='equipment_cost_total')
    assert response['conditions'][1]['header_name'] == 'equipment_cost_total'
    assert response['conditions'][2]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='equipment_install_cost_total')
    assert response['conditions'][2]['header_name'] == 'equipment_install_cost_total'


def test_biz_magic_ft_off():
    validation_options = {"feature_toggle_set": set(), "df": pandas.DataFrame()}
    response = validate_m9.validate_empty_capital_install_costs(validation_options)
    assert response.get("conditions") == []


def test_record_with_only_required_values():
    df = m9_only_required_values_df_with_nulls
    validation_options = {
        "feature_toggle_set": set([Feature.ASYNC_BIZ_MAGIC_MODULE_9]),
        "df": df,
    }
    response = validate_m9.validate_empty_capital_install_costs(validation_options)
    error_row_set = {r["error_row"] for r in response.get("conditions", [])}
    assert {1, 3} == error_row_set
    assert {0, 2}.intersection(error_row_set) == set()

    assert len(response.get("conditions", [])) == 2
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='equipment_install_cost_total')
    assert response['conditions'][0]['header_name'] == 'equipment_install_cost_total'
    assert response['conditions'][1]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='real_property_cost_total')
    assert response['conditions'][1]['header_name'] == 'real_property_cost_total'


@patch("module_validation.validate_m9.DatabaseCentralConfig")
def test_record_with_only_required_values_cc(
    mock_database_central_config, config
):
    df = m9_only_required_values_df_with_nulls
    validation_options = {
        "feature_toggle_set": set([Feature.ASYNC_BIZ_MAGIC_MODULE_9, Feature.DATABASE_CENTRAL_CONFIG]),
        "df": df,
    }
    mock_database_central_config.return_value = config
    response = validate_m9.validate_empty_capital_install_costs(validation_options)
    error_row_set = {r["error_row"] for r in response.get("conditions", [])}
    assert {1, 3} == error_row_set
    assert {0, 2}.intersection(error_row_set) == set()

    assert len(response.get("conditions", [])) == 2
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='equipment_install_cost_total')
    assert response['conditions'][0]['header_name'] == 'equipment_install_cost_total'
    assert response['conditions'][1]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='real_property_cost_total')
    assert response['conditions'][1]['header_name'] == 'real_property_cost_total'


def test_record_with_only_required_values_no_nulls():
    df = m9_only_required_values_df
    validation_options = {
        "feature_toggle_set": set([Feature.ASYNC_BIZ_MAGIC_MODULE_9]),
        "df": df,
    }
    response = validate_m9.validate_empty_capital_install_costs(validation_options)
    error_row_set = {r["error_row"] for r in response.get("conditions", [])}
    assert {1, 3} == error_row_set
    assert {0, 2}.intersection(error_row_set) == set()

    assert len(response.get("conditions", [])) == 2
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='equipment_install_cost_total')
    assert response['conditions'][0]['header_name'] == 'equipment_install_cost_total'
    assert response['conditions'][1]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='real_property_cost_total')
    assert response['conditions'][1]['header_name'] == 'real_property_cost_total'


@patch("module_validation.validate_m9.DatabaseCentralConfig")
def test_record_with_only_required_values_no_nulls_cc(
    mock_database_central_config, config
):
    df = m9_only_required_values_df
    validation_options = {
        "feature_toggle_set": set([Feature.ASYNC_BIZ_MAGIC_MODULE_9, Feature.DATABASE_CENTRAL_CONFIG]),
        "df": df,
    }
    mock_database_central_config.return_value = config
    response = validate_m9.validate_empty_capital_install_costs(validation_options)
    error_row_set = {r["error_row"] for r in response.get("conditions", [])}
    assert {1, 3} == error_row_set
    assert {0, 2}.intersection(error_row_set) == set()

    assert len(response.get("conditions", [])) == 2
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='equipment_install_cost_total')
    assert response['conditions'][0]['header_name'] == 'equipment_install_cost_total'
    assert response['conditions'][1]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='real_property_cost_total')
    assert response['conditions'][1]['header_name'] == 'real_property_cost_total'


@pytest.mark.parametrize("filename", invalid_missing_values_files)
@patch("module_validation.validate_m9.DatabaseCentralConfig")
def test_records_with_missing_required_values_but_not_valid_null_modules(mock_database_central_config, filename, config):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()

        df = get_dataframe_from_csv(body)
        validation_options = {
            "feature_toggle_set": set([Feature.ASYNC_BIZ_MAGIC_MODULE_9, Feature.DATABASE_CENTRAL_CONFIG]),
            "df": df,
        }
        mock_database_central_config.return_value = config
        response = validate_m9.validate_empty_capital_install_costs(validation_options)

        assert len(response.get("conditions", [])) == 1