from unittest.mock import MagicMock, patch

import pandas
import pytest

# pylint: disable=import-error
# module paths are set in conftest.py
from AsyncDataValidation.index import get_dataframe_from_csv
from feature_toggle.feature_enums import Feature
from module_validation import ModuleDefinitionEnum, validated_dataframe_by_module_id

valid_files = [
    "evchart_data_m5_valid_import.csv",
    "evchart_data_m5_valid_import_100_records.csv",
    "evchart_data_m5_valid_import_10_records.csv",
    "evchart_data_m5_valid_import_225_records.csv",
    "evchart_data_m5_valid_import_25_records.csv",
    "evchart_data_m5_valid_import_50_records.csv",
    "evchart_valid_all_columns_module_5.csv",
    "evchart_valid_all_columns_module_5_100_records.csv",
    "evchart_valid_all_columns_module_5_10_records.csv",
    "evchart_valid_all_columns_module_5_200_records.csv",
    "evchart_valid_all_columns_module_5_25_records.csv",
    "evchart_valid_all_columns_module_5_50_records.csv",
    "evchart_valid_all_required_module_5.csv",
    "all_columns_module_5.csv",
    "all_required_module_5.csv",
    "blank_row_all_required_mod_5.csv",
    "caas_false_value_mod_5.csv",
    "caas_true_value_mod_5.csv",
    "evchart_data_m5_empty_value.csv",
    "evchart_valid_all_columns_module_5_250_records.csv",
]
null_files = ["invalid_module_5_null.csv"]
biz_magic_null_files = ["valid_mod5_biz_magic.csv"]

invalid_files = [
    "all_invalid_data_type_mod_5.csv",
    "caas_invalid_data_type_string_as_a_boolean_mod_5.csv",
    "cass_invalid_column_header_name_mod_5.csv",
    "evchart_all_invalid_data_type_mod_5.csv",
    "evchart_data_m5_invalid_column_header.csv",
    "evchart_data_m5_missing_column_header.csv",
    "evchart_empty_value_for_maintenance_cost_federal_mod_5.csv",
    "evchart_empty_value_for_maintenance_report_end_mod_5.csv",
    "evchart_empty_value_for_maintenance_report_start_mod_5.csv",
    # "evchart_empty_value_for_station_id_mod_5.csv",
    "evchart_invalid_boundary_type_min_value_for_maintenance_cost_total_mod_5.csv",
    "evchart_invalid_boundary_type_min_value_maintenance_cost_federal_mod_5.csv",
    "evchart_invalid_column_header_name_for_maintenance_cost_federal_mod_5.csv",
    "evchart_invalid_column_header_name_for_maintenance_report_end_mod_5.csv",
    "evchart_invalid_column_header_name_for_maintenance_report_start_mod_5.csv",
    "evchart_invalid_column_header_name_for_station_id_mod_5.csv",
    "evchart_invalid_data_type_string_as_a_Boolean_for_caas_mod_5.csv",
    "evchart_invalid_data_type_string_as_a_datetime_for_maintenance_report_end_mod_5.csv",
    "evchart_invalid_data_type_string_as_a_datetime_for_maintenance_report_start_mod_5.csv",
    "evchart_invalid_data_type_string_as_a_decimal_for_maintenance_cost_federal_mod_5.csv",
    "evchart_invalid_data_type_string_as_a_decimal_for_maintenance_cost_total_mod_5.csv",
    "evchart_invalid_datetime_format_for_maintenance_report_end_mod_5.csv",
    "evchart_invalid_datetime_format_for_maintenance_report_start_mod_5.csv",
    "evchart_invalid_datetime_value_for_maintenance_report_end_mod_5.csv",
    "evchart_invalid_datetime_value_for_maintenance_report_start_mod_5.csv",
    # "evchart_invalid_regex_station_id_mod_5.csv",
    "evchart_missing_column_header_for_maintenance_cost_federal_mod_5.csv",
    "evchart_missing_column_header_for_maintenance_report_end_mod_5.csv",
    "evchart_missing_column_header_for_maintenance_report_start_mod_5.csv",
    # "evchart_missing_column_header_for_station_id_mod_5.csv",
    "evchart_non_required_or_recommended_column_header_module_5.csv",
    # "extra_required_column_header_mod_5.csv",
    "maintenance_cost_federal_empty_value_mod_5.csv",
    "maintenance_cost_federal_invalid_boundary_precision_mod_5.csv",
    "maintenance_cost_federal_invalid_boundary_type_max_length_mod_5.csv",
    "maintenance_cost_federal_invalid_boundary_type_min_value_mod_5.csv",
    "maintenance_cost_federal_invalid_column_header_name_mod_5.csv",
    "maintenance_cost_federal_invalid_data_type_string_as_a_decimal_mod_5.csv",
    "maintenance_cost_federal_missing_column_header_mod_5.csv",
    "maintenance_cost_tota_invalid_boundary_max_length_mod_5.csv",
    "maintenance_cost_tota_invalid_boundary_precision_mod_5.csv",
    "maintenance_cost_total_invalid_boundary_type_min_value_mod_5.csv",
    "maintenance_cost_total_invalid_data_type_string_as_a_decimal_mod_5.csv",
    "maintenance_report_end__empty_value_mod_5.csv",
    "maintenance_report_end_invalid_column_header_name_mod_5.csv",
    "maintenance_report_end_invalid_data_type_string_as_a_datetime_mod_5.csv",
    "maintenance_report_end_invalid_datetime_format_mod_5.csv",
    "maintenance_report_end_invalid_datetime_value_mod_5.csv",
    "maintenance_report_end_missing_column_header_mod_5.csv",
    "maintenance_report_start_empty_value_mod_5.csv",
    "maintenance_report_start_invalid_column_header_name_mod_5.csv",
    "maintenance_report_start_invalid_data_type_string_as_a_datetime_mod_5.csv",
    "maintenance_report_start_invalid_datetime_format_mod_5.csv",
    "maintenance_report_start_invalid_datetime_value_mod_5.csv",
    "maintenance_report_start_missing_column_header_mod_5.csv",
    "non_required_or_recommended_column_header_module_5.csv",
    # "station_id__regex_blank_space_mod_5.csv",
    # "station_id_empty_value_mod_5.csv",
    "station_id_invalid_column_header_name_mod_5.csv",
    # "station_id_missing_column_header_mod_5.csv",
    # "maintenance_cost_federal_invalid_boundary_type_mod_5.csv",
    # "maintenance_cost_tota_invalid_boundary_mod_5.csv",
]


@pytest.mark.parametrize("filename", valid_files + biz_magic_null_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module5_valid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_5,
                df,
                upload_id,
                feature_toggle_set={Feature.ASYNC_BIZ_MAGIC_MODULE_5},
            )

    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", valid_files + biz_magic_null_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module5_valid_with_biz_magic_and_central_config(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_5,
                df,
                upload_id,
                feature_toggle_set={
                    Feature.ASYNC_BIZ_MAGIC_MODULE_5,
                    Feature.DATABASE_CENTRAL_CONFIG,
                },
            )

    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", invalid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module5_invalid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_5,
                df,
                upload_id,
                feature_toggle_set={Feature.MODULE_5_NULLS},
            )

    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) > 0


# JE-6524, make sure if both null ack and biz magic
# feature toggles are enabled, nulls are handled correctly
# Original file will error with biz_magic_on
@pytest.mark.parametrize("filename", null_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module5_invalid_nulls_both_feature_toggles(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_5,
                df,
                upload_id,
                feature_toggle_set={
                    Feature.MODULE_5_NULLS,
                    Feature.ASYNC_BIZ_MAGIC_MODULE_5,
                    Feature.BIZ_MAGIC,
                },
            )
    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) > 0


@pytest.mark.parametrize("filename", valid_files + biz_magic_null_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module5_valid_biz_magic(mock_feature_toggle, filename):
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
                module_number=ModuleDefinitionEnum.MODULE_5,
                df=df,
                upload_id=upload_id,
                feature_toggle_set={Feature.ASYNC_BIZ_MAGIC_MODULE_5},
            )

    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", valid_files + biz_magic_null_files)
def test_csv_module5_valid_biz_magic_and_central_config(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_5,
                df,
                upload_id,
                {Feature.ASYNC_BIZ_MAGIC_MODULE_5, Feature.DATABASE_CENTRAL_CONFIG},
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)
