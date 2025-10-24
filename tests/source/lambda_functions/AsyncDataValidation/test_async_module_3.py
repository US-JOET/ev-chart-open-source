from unittest.mock import MagicMock, patch

import pandas
import pytest

# pylint: disable=import-error
# module paths are set in conftest.py
from AsyncDataValidation.index import get_dataframe_from_csv
from feature_toggle.feature_enums import Feature
from module_validation import ModuleDefinitionEnum, validated_dataframe_by_module_id

valid_files = [
    "evchart_data_m3_valid_import.csv",
    "evchart_data_m3_valid_import_100_records.csv",
    "evchart_data_m3_valid_import_10_records.csv",
    "evchart_data_m3_valid_import_225_records.csv",
    "evchart_data_m3_valid_import_25_records.csv",
    "evchart_data_m3_valid_import_50_records.csv",
    "evchart_valid_all_columns_module_3_100_records.csv",
    "evchart_valid_all_columns_module_3_10_records.csv",
    "evchart_valid_all_columns_module_3_250_records.csv",
    "evchart_valid_all_columns_module_3_25_records.csv",
    "evchart_valid_all_columns_module_3_50_records.csv",
    "evchart_valid_all_required_module_3.csv",
    "all_required_mod_3.csv",
    "blank_row_all_required_mod_3.csv",
    "evchart_data_m3_empty_values.csv",
    "valid_all_columns_module_3_100_records.csv",
    "valid_all_columns_module_3_10_records.csv",
    "valid_all_columns_module_3_250_records.csv",
    "valid_all_columns_module_3_25_records.csv",
    "valid_all_columns_module_3_50_records.csv",
]
valid_biz_magic_file = ["valid_m3_biz_magic.csv"]
invalid_files = [
    "all_invalid_data_type_mod_3.csv",
    "evchart_data_m3_invalid__data_type.csv",
    "evchart_data_m3_invalid_column_header.csv",
    "evchart_data_m3_missing_headers.csv",
    "evchart_empty__value_for_uptime_mod_3.csv",
    "evchart_empty_value_for_port_id_mod_3.csv",
    # "evchart_empty_value_for_station_id_mod_3.csv",
    "evchart_empty_value_for_total_outage_excl_mod_3.csv",
    "evchart_empty_value_for_total_outage_mod_3.csv",
    "evchart_empty_value_for_uptime_reporting_end_mod_3.csv",
    "evchart_empty_value_for_uptime_reporting_start_mod_3.csv",
    "evchart_invalid_boundary_type_for_total_outage_excl_mod_3.csv",
    "evchart_invalid_boundary_type_for_total_outage_mod_3.csv",
    "evchart_invalid_boundary_type_for_uptime_mod_3.csv",
    "evchart_invalid_column_header_name_for_port_id_mod_3.csv",
    "evchart_invalid_column_header_name_for_station_id_mod_3.csv",
    "evchart_invalid_column_header_name_for_total_outage_excl_mod_3.csv",
    "evchart_invalid_column_header_name_for_total_outage_mod_3.csv",
    "evchart_invalid_column_header_name_for_uptime_mod_3.csv",
    "evchart_invalid_column_header_name_for_uptime_reporting_end_mod_3.csv",
    "evchart_invalid_column_header_name_for_uptime_reporting_start_mod_3.csv",
    "evchart_invalid_data_type_decimal_as_a_Boolean_for_uptime_total_outage_mod_3.csv",
    "evchart_invalid_data_type_string_as_a_datetime_for_uptime_reporting_end_mod_3.csv",
    "evchart_invalid_data_type_string_as_a_datetime_for_uptime_reporting_start_mod_3.csv",
    "evchart_invalid_data_type_string_as_a_decimal_for_total_outage_mod_3.csv",
    "evchart_invalid_data_type_string_as_a_decimal_for_uptime_reporting_end_mod_3.csv",
    "evchart_invalid_datetime_formart_for_uptime_reporting_start_mod_3.csv",
    "evchart_invalid_datetime_format_for_uptime_reporting_start_mod_3.csv",
    "evchart_invalid_datetime_value_for_uptime_reporting_start_mod_3.csv",
    "evchart_invalid_datetime_vaule_uptime_reporting_end_mod_3.csv",
    "evchart_missing_column_header_for_port_id_mod_3.csv",
    # "evchart_missing_column_header_for_station_id_mod_3.csv",
    "evchart_missing_column_header_for_total_outage_excl_mod_3.csv",
    "evchart_missing_column_header_for_total_outage_mod_3.csv",
    "evchart_missing_column_header_for_uptime_mod_3.csv",
    "evchart_missing_column_header_for_uptime_reporting_end_mod_3.csv",
    "evchart_missing_column_header_for_uptime_reporting_start_mod_3.csv",
    "evchart_non_required_or_recommended_column_header_module_3.csv",
    # "extra_required_column_header_mod_3.csv",
    "non_required_or_recommended_column_header_mod_3.csv",
    "port_id_empty_value_mod_3.csv",
    "port_id_invalid_column_header_name_mod_3.csv",
    "port_id_missing_column_header_mod_3.csv",
    "port_id_regex_blank_space_mod_3.csv",
    # "station_id_empty_value_mod_3.csv",
    "station_id_invalid_column_header_name_mod_3.csv",
    # "station_id_missing_column_header_mod_3.csv",
    # "station_id_regex_blank_space_mod_3.csv",
    "total_outage_empty_value_mod_3.csv",
    "total_outage_excl_empty_vaule_mod_3.csv",
    "total_outage_excl_invalid_boundary_max_length_mod_3.csv",
    "total_outage_excl_invalid_boundary_min_value_mod_3.csv",
    "total_outage_excl_invalid_boundary_precision _mod_3.csv",
    "total_outage_excl_invalid_column_header_name_mod_3.csv",
    "total_outage_excl_missing_column_header_mod_3.csv",
    "total_outage_invalid_boundary_max_length _mod_3.csv",
    "total_outage_invalid_boundary_min_value_mod_3.csv",
    "total_outage_invalid_boundary_precision _mod_3.csv",
    "total_outage_invalid_column_header_name_mod_3.csv",
    "total_outage_invalid_data_type_string_as_a_decimal_mod_3.csv",
    "total_outage_missing_column_header_mod_3.csv",
    "uptime_empty_value_mod_3.csv",
    "uptime_invalid_boundary_max_length_mod_3.csv",
    "uptime_invalid_boundary_min_value_mod_3.csv",
    "uptime_invalid_boundary_precision_mod_3.csv",
    "uptime_invalid_column_header_name_mod_3.csv",
    "uptime_missing_column_header_mod_3.csv",
    "uptime_reporting_end_empty_value_mod_3.csv",
    "uptime_reporting_end_invalid_column_header_name_mod_3.csv",
    "uptime_reporting_end_invalid_data_type_string_as_a_datetime_mod_3.csv",
    "uptime_reporting_end_invalid_datetime_format_uptime_reporting_end_mod_3.csv",
    "uptime_reporting_end_invalid_datetime_vaule_uptime_reporting_end_mod_3.csv",
    "uptime_reporting_end_missing_column_header_mod_3.csv",
    "uptime_reporting_start_empty_value_mod_3.csv",
    "uptime_reporting_start_invalid_column_header_name_mod_3.csv",
    "uptime_reporting_start_invalid_data_type_string_as_a_datetime_mod_3.csv",
    "uptime_reporting_start_invalid_datetime_formart_mod_3.csv",
    "uptime_reporting_start_invalid_datetime_value_mod_3.csv",
    "uptime_reporting_start_missing_column_header_mod_3.csv",
    "uptime_total_outage_invalid_data_type_decimal_as_a_boolean_mod_3.csv",
]
skipped_expected_pass_actual_fail = [
    "evchart_valid_all_columns_module_3_200_records.csv",
]


@pytest.mark.parametrize("filename", valid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module3_valid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_3, df, upload_id
            )

    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", valid_files + valid_biz_magic_file)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module3_valid_bizmagic(mock_feature_toggle, filename):
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
                module_number=ModuleDefinitionEnum.MODULE_3,
                df=df,
                upload_id=upload_id,
                feature_toggle_set={Feature.ASYNC_BIZ_MAGIC_MODULE_3},
            )

    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", invalid_files)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module3_invalid(mock_feature_toggle, filename):
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
                ModuleDefinitionEnum.MODULE_3, df, upload_id
            )

    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) > 0


@pytest.mark.parametrize("filename", valid_files + valid_biz_magic_file)
def test_csv_module3_valid_biz_magic_and_central_config(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_3,
                df,
                upload_id,
                {Feature.ASYNC_BIZ_MAGIC_MODULE_3, Feature.DATABASE_CENTRAL_CONFIG},
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)
