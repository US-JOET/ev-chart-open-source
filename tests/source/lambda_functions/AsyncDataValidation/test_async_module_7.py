from unittest.mock import MagicMock, patch

import pandas
import pytest

# pylint: disable=import-error
# module paths are set in conftest.py
from AsyncDataValidation.index import get_dataframe_from_csv
from feature_toggle.feature_enums import Feature
from module_validation import ModuleDefinitionEnum, validated_dataframe_by_module_id

valid_files = [
    "evchart_data_m7_valid_import.csv",
    "evchart_data_m7_valid_import_100_records.csv",
    "evchart_data_m7_valid_import_10_records.csv",
    "evchart_data_m7_valid_import_225_records.csv",
    "evchart_data_m7_valid_import_25_records.csv",
    "evchart_data_m7_valid_import_50_records.csv",
    "evchart_valid_all_columns_module_7.csv",
    "evchart_valid_all_columns_module_7_100_records.csv",
    "evchart_valid_all_columns_module_7_10_records.csv",
    "evchart_valid_all_columns_module_7_200_records.csv",
    "evchart_valid_all_columns_module_7_25_records.csv",
    "evchart_valid_all_columns_module_7_50_records.csv",
    "evchart_valid_all_required_module_7.csv",
    "all_columns_mod_7.csv",
    "all_required_mod_7.csv",
    "blank_row_all_required_mod_7.csv",
    "evchart_data_m7_empty_values.csv",
    "evchart_valid_all_columns_module_7_250_records.csv",
]
invalid_files = [
    "all_invalid_data_type_mod_7.csv",
    "evchart_all_invalid_data_type_mod_7.csv",
    "evchart_data_m7_invalid_column_header.csv",
    "evchart_data_m7_invalid_data_type.csv",
    "evchart_empty_value_for_opportunity_program_mod_7.csv",
    "evchart_empty_value_for_program_report_year_mod_7.csv",
    # "evchart_empty_value_for_station_id_mod_7.csv",
    "evchart_invalid_boundary_Exact_Length_type_for_program_report_year_mod_7.csv",
    "evchart_invalid_boundary_type_for_program_report_year_mod_7.csv",
    "evchart_invalid_column_header_name_for_opportunity_program_mod_7.csv",
    "evchart_invalid_column_header_name_for_program_descript_mod_7.csv",
    "evchart_invalid_column_header_name_for_program_report_year_mod_7.csv",
    "evchart_invalid_column_header_name_for_station_id_mod_7.csv",
    "evchart_invalid_data_type_string_as_a_int_for_program_report_year_mod_7.csv",
    # "evchart_invalid_regex_station_id_mod_7.csv",
    "evchart_missing_column_header_for_opportunity_program_mod_7.csv",
    "evchart_missing_column_header_for_program_report_year_mod_7.csv",
    # "evchart_missing_column_header_for_station_id_mod_7.csv",
    "evchart_non_required_or_recommended_column_header_module_7.csv",
    # "extra_required_column_header_mod_7.csv",
    "non_required_or_recommended_column_header_module_7.csv",
    "opportunity_progra_missing_column_header_mod_7.csv",
    "opportunity_program_empty_value_mod_7.csv",
    "opportunity_program_invalid_column_header_name_mod_7.csv",
    "opportunity_program_regex_blank_space_mod_7.csv",
    "program_descript_invalid_column_header_name_mod_7.csv",
    "program_report_year_empty_value_mod_7.csv",
    "program_report_year_invalid_boundary_Exact_Length_mod_7.csv",
    "program_report_year_invalid_column_header_name_mod_7.csv",
    "program_report_year_invalid_data_type_string_as_a_int_mod_7.csv",
    "program_report_year_missing_column_header_mod_7.csv",
    # "station_id_empty_value_mod_7.csv",
    "station_id_invalid_column_header_name_mod_7.csv",
    # "station_id_missing_column_header_mod_7.csv",
    # "station_id_regex_blank_space_mod_7.csv",
]


@pytest.mark.parametrize("filename", valid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module7_valid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_7, df, upload_id
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", invalid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module7_invalid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_7, df, upload_id
            )
    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) > 0


@pytest.mark.parametrize("filename", valid_files)
def test_csv_module7_valid_central_config(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_7, df, upload_id, {Feature.DATABASE_CENTRAL_CONFIG}
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)
