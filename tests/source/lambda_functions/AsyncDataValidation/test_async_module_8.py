from unittest.mock import MagicMock, patch

import pandas
import pytest

# pylint: disable=import-error
# module paths are set in conftest.py
from AsyncDataValidation.index import get_dataframe_from_csv
from feature_toggle.feature_enums import Feature
from module_validation import ModuleDefinitionEnum, validated_dataframe_by_module_id

valid_files = [
    "evchart_valid_all_columns_module_8.csv",
    "evchart_valid_all_columns_module_8_100_records.csv",
    "evchart_valid_all_columns_module_8_10_records.csv",
    "evchart_valid_all_columns_module_8_200_records.csv",
    "evchart_valid_all_columns_module_8_250_records.csv",
    "evchart_valid_all_columns_module_8_25_records.csv",
    "evchart_valid_all_columns_module_8_50_records.csv",
    "evchart_valid_all_required_module_8.csv",
    "all_columns_module_8.csv",
    "all_required_module_8.csv",
    "blank_row_all_required_mod_8.csv",
    "der_onsite_false_value_mod_8.csv",
    "der_onsite_true_value_mod_8.csv",
    "der_upgrade_false_value_mod_8.csv",
    "der_upgrade_true_value_mod_8.csv",
    "valid_all_columns_module_8_100_records.csv",
    "valid_all_columns_module_8_10_records.csv",
    "valid_all_columns_module_8_250_records.csv",
    "valid_all_columns_module_8_25_records.csv",
    "valid_all_columns_module_8_50_records.csv",
]
invalid_files = [
    "all_invalid_data_type_mod_8.csv",
    "der_kw_empty_value_mod_8.csv",
    "der_kw_invalid_boundary_type_min_value_mod_8.csv",
    "der_kw_invalid_column_header_name_mod_8.csv",
    "der_kw_invalid_data_type_boolean_as_a_int_mod_8.csv",
    "der_kwh__invalid_data_type_boolean_as_a_int_mod_8.csv",
    "der_kwh_empty_value_mod_8.csv",
    "der_kwh_invalid_boundary_type_min_value_mod_8.csv",
    "der_kwh_invalid_column_header_name_mod_8.csv",
    "der_kwh_missing_column_header_mod_8.csv",
    "der_onsite_empty_value_mod_8.csv",
    "der_onsite_invalid_column_header_name_mod_8.csv",
    "der_onsite_invalid_data_type_int_as_a_boolean_mod_8.csv",
    "der_type_empty_value_mod_8.csv",
    "der_type_invalid_boundary_type_min_value_mod_8.csv",
    "der_type_invalid_column_header_name_mod_8.csv",
    "der_type_missing_column_header_mod_8.csv",
    "der_type_other_invalid_column_header_name_mod_8.csv",
    "der_type_regex_blank_space_mod_8.csv",
    "der_upgrade_invalid_column_header_name_mod_8.csv",
    "der_upgrade_invalid_data_type_int_as_a_boolean_mod_8.csv",
    "evchart_all_invalid_data_type_mod_8.csv",
    "evchart_data_m8_empty_value.csv",
    "evchart_data_m8_invalid_column_header.csv",
    "evchart_data_m8_invalid_data_type.csv",
    "evchart_data_m8_missing_column_header.csv",
    "evchart_empty_value_for_der_kw_mod_8.csv",
    "evchart_empty_value_for_der_kwh_mod_8.csv",
    "evchart_empty_value_for_der_onsite_mod_8.csv",
    "evchart_empty_value_for_der_type_mod_8.csv",
    # "evchart_empty_value_for_station_id_mod_8.csv",
    "evchart_invalid_boundary_type_min_value_for_der_kwh_mod_8.csv",
    "evchart_invalid_boundary_type_min_value_for_der_type_mod_8.csv",
    "evchart_invalid_column_header_for_der_kwh_mod_8.csv",
    "evchart_invalid_column_header_name_for_der_kwh_mod_8.csv",
    "evchart_invalid_column_header_name_for_der_onsite_mod_8.csv",
    "evchart_invalid_column_header_name_for_der_type_mod_8.csv",
    "evchart_invalid_column_header_name_for_der_type_other_mod_8.csv",
    "evchart_invalid_column_header_name_for_der_upgrade_mod_8.csv",
    "evchart_invalid_column_header_name_for_station_id_mod_8.csv",
    "evchart_invalid_data_type_boolean_as_a_int_for_der_kw_mod_8.csv",
    "evchart_invalid_data_type_boolean_as_a_int_for_der_kwh_mod_8.csv",
    "evchart_invalid_data_type_int_as_a_boolean_for_der_onsite_mod_8.csv",
    "evchart_invalid_data_type_int_as_a_boolean_for_der_upgrade_mod_8.csv",
    "evchart_missing_column_header_for_der_type_mod_8.csv",
    "evchart_non_required_or_recommended_column_header_module_8.csv",
    # "extra_required_column_header_mod_8.csv",
    "non_required_or_recommended_column_header_module_8.csv",
    # "station_id_empty_value_mod_8.csv",
    "station_id_invalid_column_header_name_mod_8.csv",
    # "station_id_missing_column_header_mod_8.csv",
    # "station_id_regex_blank_space_mod_8.csv",
    "m8_invalid_min_value_for_dew_kw.csv",
]


@pytest.mark.parametrize("filename", valid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module8_valid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_8, df, upload_id
            )

    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", invalid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module8_invalid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_8, df, upload_id
            )

    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) > 0


@pytest.mark.parametrize("filename", valid_files)
def test_csv_module8_valid_central_config(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_8, df, upload_id, {Feature.DATABASE_CENTRAL_CONFIG}
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)
