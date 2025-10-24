from unittest.mock import MagicMock, patch

import pandas
import pytest

# pylint: disable=import-error
# module paths are set in conftest.py
from AsyncDataValidation.index import get_dataframe_from_csv
from feature_toggle.feature_enums import Feature
from module_validation import ModuleDefinitionEnum, validated_dataframe_by_module_id

valid_files = [
    "evchart_data_m6_valid_import.csv",
    "evchart_data_m6_valid_import_100_records.csv",
    "evchart_data_m6_valid_import_10_records.csv",
    "evchart_data_m6_valid_import_225_records.csv",
    "evchart_data_m6_valid_import_25_records.csv",
    "evchart_data_m6_valid_import_50_records.csv",
    "evchart_valid_all_columns_module_6.csv",
    "evchart_valid_all_columns_module_6_100_records.csv",
    "evchart_valid_all_columns_module_6_10_records.csv",
    "evchart_valid_all_columns_module_6_200_records.csv",
    "evchart_valid_all_columns_module_6_25_records.csv",
    "evchart_valid_all_columns_module_6_50_records.csv",
    "evchart_valid_all_required_module_6.csv",
    "evchart_valid_all_required_module_6_with_blank_lines.csv",
    "all_columns_module_6.csv",
    "all_required_module_6.csv",
    "blank_row_all_required_mod_6.csv",
    "evchart_data_m6_empty_value.csv",
    "valid_all_columns_module_6_100_records.csv",
    "valid_all_columns_module_6_10_records.csv",
    "valid_all_columns_module_6_250_records.csv",
    "valid_all_columns_module_6_25_records.csv",
    "valid_all_columns_module_6_50_records.csv",
]
invalid_files = [
    "all_invalid_data_type_mod_6.csv",
    "evchart_all_invalid_data_type_mod_6.csv",
    "evchart_data_m6_invalid_column_header.csv",
    "evchart_data_m6_missing_column_header.csv",
    "evchart_empty_value_for_operator_address_mod_6.csv",
    "evchart_empty_value_for_operator_name_mod_6.csv",
    "evchart_empty_value_for_operator_state_mod_6.csv",
    "evchart_empty_value_for_operator_zip_mod_6.csv",
    # "evchart_empty_value_for_station_id_mod_6.csv",
    "evchart_invalid_boundary_type_Exact_Length_for_operator_state_mod_6.csv",
    "evchart_invalid_boundary_type_Exact_Length_for_operator_zip__mod_6.csv",
    "evchart_invalid_boundary_type_Exact_Length_for_operator_zip_extended_mod_6.csv",
    "evchart_invalid_boundary_type_for_operator_state_mod_6.csv",
    "evchart_invalid_boundary_type_for_operator_zip_extended_mod_6.csv",
    "evchart_invalid_boundary_type_for_operator_zip_mod_6.csv",
    "evchart_invalid_column_header_name_for_operator_address_mod_6.csv",
    "evchart_invalid_column_header_name_for_operator_name_mod_6.csv",
    "evchart_invalid_column_header_name_for_operator_state_mod_6.csv",
    "evchart_invalid_column_header_name_for_operator_zip_mod_6.csv",
    "evchart_invalid_column_header_name_for_operator_zip_operator_extended_mod_6.csv",
    "evchart_invalid_column_header_name_for_station_id_mod_6.csv",
    "evchart_invalid_regex_operator_address_mod_6.csv",
    "evchart_invalid_regex_operator_city_mod_6.csv",
    "evchart_invalid_regex_operator_name_mod_6.csv",
    "evchart_invalid_regex_operator_state_mod_6.csv",
    "evchart_invalid_regex_operator_zip_mod_6.csv",
    # "evchart_invalid_regex_station_id_mod_6.csv",
    "evchart_missing_column_header_for_operator_address_mod_6.csv",
    "evchart_missing_column_header_for_operator_name_mod_6.csv",
    "evchart_missing_column_header_for_operator_state_mod_6.csv",
    "evchart_missing_column_header_for_operator_zip_mod_6.csv",
    # "evchart_missing_column_header_for_station_id_mod_6.csv",
    "evchart_non_required_or_recommended_column_header_module_6.csv",
    # "extra_required_column_header_mod_6.csv",
    "non_required_or_recommended_column_header_module_6.csv",
    "operator_address_empty_value_mod_6.csv",
    "operator_address_invalid_column_header_name_mod_6.csv",
    "operator_address_missing_column_header_mod_6.csv",
    "operator_address_regex_blank_space_mod_6.csv",
    "operator_city_regex_blank_space_mod_6.csv",
    "operator_name_empty_value_mod_6.csv",
    "operator_name_invalid_column_header_name_mod_6.csv",
    "operator_name_missing_column_header_mod_6.csv",
    "operator_name_regex_blank_space_mod_6.csv",
    "operator_state_empty_value_mod_6.csv",
    "operator_state_invalid_boundary_type_Exact_Length_mod_6.csv",
    "operator_state_invalid_column_header_name_mod_6.csv",
    "operator_state_missing_column_header_mod_6.csv",
    "operator_state_regex_mod_6.csv",
    "operator_zip_empty_value_mod_6.csv",
    "operator_zip_extended_invalid_boundary_type_Exact_Length_mod_6.csv",
    "operator_zip_extended_invalid_column_header_name_mod_6.csv",
    "operator_zip_invalid_boundary_mod_6.csv",
    "operator_zip_invalid_boundary_type_Exact_Length_mod_6.csv",
    "operator_zip_invalid_column_header_name_mod_6.csv",
    "operator_zip_missing_column_header_mod_6.csv",
    "operator_zip_regex_blank_space_mod_6.csv",
    # "station_id_empty_value_mod_6.csv",
    "station_id_invalid_column_header_name_mod_6.csv",
    # "station_id_missing_column_header_mod_6.csv",
    # "station_id_regex_blank_space_mod_6.csv",
]
skipped_expected_fail_actual_pass = [
    "evchart_data_m6_empty_value.csv",
]


@pytest.mark.parametrize("filename", valid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module6_valid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_6, df, upload_id
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", invalid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module6_invalid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_6, df, upload_id
            )
    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) > 0


@pytest.mark.parametrize("filename", valid_files)
def test_csv_module6_valid_central_config(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_6, df, upload_id, {Feature.DATABASE_CENTRAL_CONFIG}
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)
