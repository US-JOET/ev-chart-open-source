import os
from unittest.mock import patch

from database_central_config import DatabaseCentralConfig
import pandas
import pytest
from pandas.testing import assert_frame_equal, assert_series_equal

from feature_toggle.feature_enums import Feature
from module_transform.transform_m9 import allow_null_capital_install_costs


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


unchanged_fields = [
    "station_id",
    "project_id",
    "station_upgrade",
    "real_property_acq_date",
    "real_property_acq_owned",
    "real_property_cost_federal",
    "equipment_acq_date",
    "equipment_acq_owned",
    "equipment_cost_federal",
    "equipment_install_date",
    "equipment_install_cost_federal",
    "der_cost_federal",
    "der_install_cost_federal",
    "dist_sys_cost_federal",
    "service_cost_federal",
]


def test_allow_null_capital_install_costs():
    source_record = {
        "station_id": ["s1"],
        "project_id": ["p1"],
        "station_upgrade": [False],
        "real_property_acq_date": ["2024-01-20T00:00:00Z"],
        "real_property_acq_owned": [False],
        "real_property_cost_total": [""],
        "real_property_cost_federal": [4800.89],
        "equipment_acq_date": ["2024-01-20T00:00:00Z"],
        "equipment_acq_owned": [False],
        "equipment_cost_total": [""],
        "equipment_cost_federal": [4800.89],
        "equipment_install_date": ["2024-01-20T00:00:00Z"],
        "equipment_install_cost_total": [""],
        "equipment_install_cost_federal": [4800.89],
        "equipment_install_cost_elec": [""],
        "equipment_install_cost_const": [""],
        "equipment_install_cost_labor": [""],
        "der_acq_owned": [""],
        "der_cost_federal": [4800.89],
        "der_cost_total": [""],
        "der_install_cost_total": [""],
        "der_install_cost_federal": [4800.89],
        "dist_sys_cost_total": [""],
        "dist_sys_cost_federal": [4800.89],
        "service_cost_total": [""],
        "service_cost_federal": [4800.89],
        "equipment_install_cost_other": [""],
    }
    df = pandas.DataFrame(source_record)
    response = allow_null_capital_install_costs({Feature.ASYNC_BIZ_MAGIC_MODULE_9}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])

    assert_series_equal(
        response["real_property_cost_total"],
        pandas.Series(
            [None], dtype=pandas.Int64Dtype, name="real_property_cost_total"
        ),
    )
    assert_series_equal(
        response["equipment_cost_total"],
        pandas.Series([None], dtype=pandas.Int64Dtype, name="equipment_cost_total"),
    )


def test_only_required_fields():
    source_record = {
        "station_id": ["s1"],
        "project_id": ["p1"],
        "station_upgrade": [False],
        "real_property_acq_date": ["2024-01-20T00:00:00Z"],
        "real_property_acq_owned": [False],
        "real_property_cost_total": [4800.89],
        "real_property_cost_federal": [4800.89],
        "equipment_acq_date": ["2024-01-20T00:00:00Z"],
        "equipment_acq_owned": [False],
        "equipment_cost_total": [4800.89],
        "equipment_cost_federal": [4800.89],
        "equipment_install_date": ["2024-01-20T00:00:00Z"],
        "equipment_install_cost_total": [4800.89],
        "equipment_install_cost_federal": [4800.89],
        "der_cost_federal": [4800.89],
        "der_cost_total": [4800.89],
        "der_install_cost_total": [4800.89],
        "der_install_cost_federal": [4800.89],
        "dist_sys_cost_total": [4800.89],
        "dist_sys_cost_federal": [4800.89],
        "service_cost_total": [4800.89],
        "service_cost_federal": [4800.89],
    }
    df = pandas.DataFrame(source_record)
    response = allow_null_capital_install_costs({Feature.ASYNC_BIZ_MAGIC_MODULE_9}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])

    assert_series_equal(
        response["real_property_cost_total"],
        pandas.Series(
            [4800.89], dtype=pandas.Float64Dtype, name="real_property_cost_total"
        ),
    )
    assert_series_equal(
        response["equipment_cost_total"],
        pandas.Series([4800.89], dtype=pandas.Float64Dtype, name="equipment_cost_total"),
    )


@patch("module_transform.transform_m9.DatabaseCentralConfig")
def test_only_required_fields_cc(mock_database_central_config, config):
    mock_database_central_config.return_value = config
    source_record = {
        "station_id": ["s1"],
        "project_id": ["p1"],
        "station_upgrade": [False],
        "real_property_acq_date": ["2024-01-20T00:00:00Z"],
        "real_property_acq_owned": [False],
        "real_property_cost_total": [4800.89],
        "real_property_cost_federal": [4800.89],
        "equipment_acq_date": ["2024-01-20T00:00:00Z"],
        "equipment_acq_owned": [False],
        "equipment_cost_total": [4800.89],
        "equipment_cost_federal": [4800.89],
        "equipment_install_date": ["2024-01-20T00:00:00Z"],
        "equipment_install_cost_total": [4800.89],
        "equipment_install_cost_federal": [4800.89],
        "der_cost_federal": [4800.89],
        "der_cost_total": [4800.89],
        "der_install_cost_total": [4800.89],
        "der_install_cost_federal": [4800.89],
        "dist_sys_cost_total": [4800.89],
        "dist_sys_cost_federal": [4800.89],
        "service_cost_total": [4800.89],
        "service_cost_federal": [4800.89],
    }
    df = pandas.DataFrame(source_record)
    response = allow_null_capital_install_costs({Feature.DATABASE_CENTRAL_CONFIG, Feature.ASYNC_BIZ_MAGIC_MODULE_9}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])

    assert_series_equal(
        response["real_property_cost_total"],
        pandas.Series(
            [4800.89], dtype=pandas.Float64Dtype, name="real_property_cost_total"
        ),
    )
    assert_series_equal(
        response["equipment_cost_total"],
        pandas.Series([4800.89], dtype=pandas.Float64Dtype, name="equipment_cost_total"),
    )


def test_allow_empty_charging_sessions():
    source_record = {
        "station_id": ["s1", "s2"],
        "project_id": ["p1", "p2"],
        "station_upgrade": [False, False],
        "real_property_acq_date": [
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
        ],
        "real_property_acq_owned": [False, False],
        "real_property_cost_total": ["", 5800.89],
        "real_property_cost_federal": [4800.89, 5800.89],
        "equipment_acq_date": [
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
        ],
        "equipment_acq_owned": [False, False],
        "equipment_cost_total": ["", 5800.89],
        "equipment_cost_federal": [4800.89, 5800.89],
        "equipment_install_date": [
            "2024-01-20T00:00:00Z",
            "2024-01-20T00:00:00Z",
        ],
        "equipment_install_cost_total": ["", 5800.89],
        "equipment_install_cost_federal": [4800.89, 5800.89],
        "equipment_install_cost_elec": ["", 5800.89],
        "equipment_install_cost_const": ["", 5800.89],
        "equipment_install_cost_labor": ["", 5800.89],
        "der_acq_owned": ["", False],
        "der_cost_federal": [4800.89, 5800.89],
        "der_cost_total": ["", 5800.89],
        "der_install_cost_total": ["", 5800.89],
        "der_install_cost_federal": [4800.89, 5800.89],
        "dist_sys_cost_total": ["", 5800.89],
        "dist_sys_cost_federal": [4800.89, 5800.89],
        "service_cost_total": ["", 5800.89],
        "service_cost_federal": [4800.89, 5800.89],
        "equipment_install_cost_other": ["", 5800.89],
    }
    df = pandas.DataFrame(source_record)
    response = allow_null_capital_install_costs({Feature.ASYNC_BIZ_MAGIC_MODULE_9}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])
    assert_series_equal(
        response["real_property_cost_total"],
        pandas.Series(
            [None, 5800.89], dtype=pandas.Float64Dtype, name="real_property_cost_total"
        ),
    )
    assert_series_equal(
        response["equipment_install_cost_elec"],
        pandas.Series(
            [None, 5800.89],
            dtype=pandas.Float64Dtype,
            name="equipment_install_cost_elec",
        ),
    )
    assert response.loc[0, "user_reports_no_data"] == 1
    assert response.loc[1, "user_reports_no_data"] == 0
