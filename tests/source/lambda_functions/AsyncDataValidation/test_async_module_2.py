from unittest.mock import MagicMock, patch

import pandas
import pytest

# pylint: disable=import-error
# module paths are set in conftest.py
from AsyncDataValidation.index import get_dataframe_from_csv
from feature_toggle.feature_enums import Feature
from module_validation import ModuleDefinitionEnum, validated_dataframe_by_module_id

valid_files = [
    "evchart_valid_all_columns_module_2_100_records.csv",
    "evchart_valid_all_columns_module_2_10_records.csv",
    "evchart_valid_all_columns_module_2_200_records.csv",
    "evchart_valid_all_columns_module_2_250_records.csv",
    "evchart_valid_all_columns_module_2_25_records.csv",
    "evchart_valid_all_columns_module_2_50_records.csv",
    "evchart_valid_all_columns_module_2.csv",
    "evchart_valid_all_required_module_2.csv",
    "all_columns_module_2.csv",
    "all_required_module_2.csv",
    "blank_row_all_required_mod_2.csv",
    "valid_all_columns_module_2_10_records.csv",
    "valid_all_columns_module_2_250_records.csv",
    "valid_all_columns_module_2_25_records.csv",
    "valid_all_columns_module_2_50_records.csv",
]
valid_null_files = [
    "valid_mod2_submitting_null.csv",
    "energy_kwh_empty_value_mod_2.csv",
    "payment_method_empty_value_mod_2.csv",
    "power_kw_empty_value_mod_2.csv",
]
valid_bizmagic_files = ["valid_mod2_biz_magic.csv"]
invalid_files = [
    "evchart_empty__value_for_session_start_mod_2.csv",
    "evchart_empty_value_for_session_start_mod_2.csv",
    "all_invalid_data_type_mod_2.csv",
    "charger_id_invalid_column_header_name_mod_2.csv",
    "connector_id_invalid_column_header_name_mod_2.csv",
    "energy_kwh_invalid_boundary_max_length_mod_2.csv",
    "energy_kwh_invalid_boundary_min_value_mod_2.csv",
    "energy_kwh_invalid_boundary_precision_mod_2.csv",
    "energy_kwh_invalid_column_header_name_mod_2.csv",
    "energy_kwh_invalid_data_type_string_as_a_datetime_mod_2.csv",
    "energy_kwh_missing_column_header_mod_2.csv",
    "energy_kwh_regex_blank_space_mod_2.csv",
    "error_other_invalid_column_header_name_mod_2.csv",
    "evchart_all_invalid_data_type_mod_2.csv",
    "evchart_data_m2_invalid_column_header.csv",
    "evchart_data_m2_invalid_data_type.csv",
    "evchart_data_m2_invalid_data_type_updated_1.25.24.csv",
    "evchart_invalid_boundary_type_for_power_kw_mod_2.csv",
    "evchart_invalid_column_header_for_session_error_data_mod_2.csv",
    "evchart_invalid_data_type_datetime_as_a_string_for_session_end_mod_2.csv",
    "evchart_invalid_data_type_string_as_a_datetime_for_energy_kwh_mod_2.csv",
    "evchart_invalid_data_type_string_as_a_datetime_for_power_kwh_mod_2.csv",
    "evchart_invalid_data_type_string_as_a_datetime_for_session_end_mod_2.csv",
    "evchart_invalid_data_type_string_as_a_datetime_for_session_start_mod_2.csv",
    "evchart_non_required_or_recommended_column_header_module_2.csv",
    # "extra_required_column_header_mod_2.csv",
    "non_required_or_recommended_column_header_module_2.csv",
    "payment_method_invalid_column_header_name_mod_2.csv",
    "provider_id_invalid_column_header_name_mod_2.csv",
    "payment_method_missing_column_header_mod_2.csv",
    "payment_method_regex_blank_space_mod_2.csv",
    "payment_other_invalid_column_header_name_mod_2.csv",
    "port_id_invalid_column_header_name_mod_2.csv",
    "port_id_missing_column_header_mod_2.csv",
    "port_id_regex_blank_space_mod_2.csv",
    "power_kw_invalid_boundary_max_length_mod_2.csv",
    "evchart_missing_column_header_charger_id_mod_2.csv",
    "port_id_empty_value_mod_2.csv",
    "mod2_invalid_submitting_null.csv",
]


@pytest.mark.parametrize("filename", invalid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module2_invalid(mock_feature_toggle, filename):
    mock_feature_toggle.return_value = "True"
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()

    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_2,
                df,
                upload_id,
                {Feature.ASYNC_BIZ_MAGIC_MODULE_2, Feature.DATABASE_CENTRAL_CONFIG},
            )

    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) > 0


@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_maxlength(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"
    df = pandas.DataFrame(
        data={
            "port_id": ["193-456-7"],
            "power_kw": ["202410.02"],
            "energy_kwh": ["20241.01"],
            "session_id": ["10001"],
            "station_id": ["StationMod2"],
            "session_end": ["2024-01-20T00:00:00Z"],
            "station_uuid": ["29a289ab-8cf3-4789-82e1-7cdc548505f6"],
            "session_error": ["ERROR1"],
            "session_start": ["2024-01-01T00:00:00Z"],
            "payment_method": ["VISA"],
        }
    )
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_2, df, upload_id
            )

    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) == 1


@pytest.mark.parametrize("filename", valid_files + valid_bizmagic_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module2_valid_biz_magic(mock_feature_toggle, filename):
    mock_feature_toggle.return_value = "True"
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_2, df, upload_id, {Feature.ASYNC_BIZ_MAGIC_MODULE_2}
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", valid_files + valid_bizmagic_files + valid_null_files)
def test_csv_module2_valid_biz_magic_and_central_config(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_2,
                df,
                upload_id,
                {Feature.ASYNC_BIZ_MAGIC_MODULE_2, Feature.DATABASE_CENTRAL_CONFIG},
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)
