import os

from database_central_config import DatabaseCentralConfig

import pytest


@pytest.fixture(name="config")
def fixture_config():
    # pylint: disable=duplicate-code
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


def test_database_central_config(config):
    assert "ev_error_data" in config
    assert isinstance(config['ev_error_data'], dict)
    assert isinstance(config['ev_error_data']['schema'], dict)
    assert config.skip_validation("module2_data_v3") == \
        config.skip_validation(2)


def test_module_number_name_equivalents(config):
    assert config.module_config(2) == config.module_config("2")
    assert config.module_config(3) == config.module_config("module3_data_v3")


def test_required_empty_allowed_fields_m2(config):
    response = config.required_empty_allowed_fields(2)
    assert response == {
        "session_id",
        "session_start",
        "session_end",
        "session_error",
        "energy_kwh",
        "power_kw",
        "payment_method"
    }

def test_module_validation_definition_m2(config):
    response = config.module_validation(2)
    expected_keys = ('energy_kwh','charger_id','payment_method','power_kw','session_end','session_error',
                     'session_id','session_start', 'port_id', 'connector_id',
                     'error_other', 'payment_other')
    for column in expected_keys:
        assert column in response


def test_module_frequency(config):
    assert config.module_frequency(2) == "quarterly"
    assert config.module_frequency(3) == "quarterly"
    assert config.module_frequency(4) == "quarterly"
    assert config.module_frequency(5) == "annual"
    assert config.module_frequency(6) == "one_time"
    assert config.module_frequency(7) == "annual"
    assert config.module_frequency(8) == "one_time"
    assert config.module_frequency(9) == "one_time"


def test_module_frequency_proper(config):
    assert config.module_frequency_proper(2) == "Quarterly"
    assert config.module_frequency_proper(3) == "Quarterly"
    assert config.module_frequency_proper(4) == "Quarterly"
    assert config.module_frequency_proper(5) == "Annual"
    assert config.module_frequency_proper(6) == "One-Time"
    assert config.module_frequency_proper(7) == "Annual"
    assert config.module_frequency_proper(8) == "One-Time"
    assert config.module_frequency_proper(9) == "One-Time"


def test_module_grid_display_headers(config):
    assert config.module_grid_display_headers(4) == {
        "left_grid_headers": ["station_id_upload"],
        "right_grid_headers": [
            "port_id",
            "outage_id",
            "network_provider_upload",
            "outage_duration",
            "excluded_outage",
            "excluded_outage_reason",
            "excluded_outage_notes"
        ]
    }


def test_rds_boolean_fields(config):
    assert config.rds_boolean_fields("import_metadata") == set()
    assert config.rds_boolean_fields(2) == {"user_reports_no_data"}
    assert config.rds_boolean_fields(3) == {"user_reports_no_data"}
    assert config.rds_boolean_fields(4) == {"excluded_outage", "user_reports_no_data"}
    assert config.rds_boolean_fields(6) == set()
    assert config.rds_boolean_fields(7) == set()

    assert config.rds_boolean_fields(5) == {"caas", "user_reports_no_data"}
    assert config.rds_boolean_fields(8) == {
        "der_upgrade", "der_onsite"
    }
    assert config.rds_boolean_fields(9) == {
        "station_upgrade",
        "real_property_acq_owned",
        "equipment_acq_owned",
        "der_acq_owned",
        "user_reports_no_data"
    }
    assert config.rds_boolean_fields("station_registrations") == {
        "NEVI", "CFI", "EVC_RAA", "CMAQ", "CRP", "OTHER", "AFC",
    }
    assert config.rds_boolean_fields("station_ports") == {"federally_funded"}


def test_validated_boolean_fields(config):
    assert config.validated_boolean_fields(2) == set()
    assert config.validated_boolean_fields(3) == set()
    assert config.validated_boolean_fields(4) == {"excluded_outage"}
    assert config.validated_boolean_fields(6) == set()
    assert config.validated_boolean_fields(7) == set()

    assert config.validated_boolean_fields(5) == {"caas"}
    assert config.validated_boolean_fields(8) == {
        "der_upgrade", "der_onsite"
    }
    assert config.validated_boolean_fields(9) == {
        "station_upgrade",
        "real_property_acq_owned",
        "equipment_acq_owned",
        "der_acq_owned"
    }


def test_validated_datetime_fields(config):
    assert config.validated_datetime_fields(6) == set()
    assert config.validated_datetime_fields(4) == {'outage_id'}


def test_validated_numeric_fields(config):
    assert config.validated_numeric_fields(4) == {'outage_duration', 'excluded_outage_reason'}


def test_unique_key_constraints(config):
    assert config.unique_key_constraints(2) == \
        ["station_uuid", "port_id", "session_id"]
    assert config.unique_key_constraints(3) == [
        "station_uuid",
        "port_id",
        "uptime_reporting_start",
        "uptime_reporting_end"
    ]
    assert config.unique_key_constraints(4) == \
        ["station_uuid", "outage_id", "port_id"]
    assert config.unique_key_constraints(5) == \
        ["station_uuid", "maintenance_report_start"]
    assert config.unique_key_constraints(6) == \
        ["station_uuid", "operator_name"]
    assert config.unique_key_constraints(7) == \
        ["station_uuid", "program_report_year"]
    assert config.unique_key_constraints(8) == ["station_uuid", "der_type"]
    assert config.unique_key_constraints(9) == ["station_uuid"]


def test_module_field_display_names(config):
    assert config.module_field_display_names(4) == {
        "outage_id": "Outage ID",
        "station_id_upload": "Station ID",
        "network_provider_upload": "Network Provider",
        "port_id": "Port ID",
        "outage_duration": "Outage Duration",
        "excluded_outage": "Excluded Outage",
        "excluded_outage_reason": "Excluded Outage Reason",
        "excluded_outage_notes": "Excluded Outage Notes"
    }


def test_table_description(config):
    assert config.table_description(4) == "Outages"


def test_module_frequency_quarter(config):
    assert config.module_frequency_quarter(1) == "Quarter 1 (Jan-Mar)"
    assert config.module_frequency_quarter("1") == "Quarter 1 (Jan-Mar)"
    assert config.module_frequency_quarter(2) == "Quarter 2 (Apr-Jun)"
    assert config.module_frequency_quarter("2") == "Quarter 2 (Apr-Jun)"
    assert config.module_frequency_quarter(3) == "Quarter 3 (Jul-Sep)"
    assert config.module_frequency_quarter("3") == "Quarter 3 (Jul-Sep)"
    assert config.module_frequency_quarter(4) == "Quarter 4 (Oct-Dec)"
    assert config.module_frequency_quarter("4") == "Quarter 4 (Oct-Dec)"
    assert config.module_frequency_quarter(0) == "INVALID QUARTER"


def test_quarterly_module_ids(config):
    assert config.quarterly_module_ids() == ["2", "3", "4"]


def test_one_time_module_ids(config):
    assert config.onetime_module_ids() == ["6", "8", "9"]


def test_annual_module_ids(config):
    assert config.annual_module_ids() == ["5", "7"]


def test_module_display_name(config):
    assert config.module_display_name("4") == "Module 4: Outages"


def test_rds_boolean_fields_all(config):
    assert config.rds_boolean_fields() == {
        "caas",
        "der_upgrade",
        "der_onsite",
        "station_upgrade",
        "real_property_acq_owned",
        "equipment_acq_owned",
        "der_acq_owned",
        "NEVI",
        "CFI",
        "EVC_RAA",
        "CMAQ",
        "CRP",
        "OTHER",
        "AFC",
        "federally_funded",
        "user_reports_no_data",
        "is_active",
        "excluded_outage"
    }
