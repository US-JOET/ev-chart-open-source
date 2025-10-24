from unittest.mock import MagicMock, patch

import pandas
import pytest

# pylint: disable=import-error
# module paths are set in conftest.py
from AsyncDataValidation.index import get_dataframe_from_csv
from feature_toggle.feature_enums import Feature
from module_validation import ModuleDefinitionEnum, validated_dataframe_by_module_id

valid_biz_magic_file = ["bizmagic_mod4_valid.csv"]
valid_files = [
    "evchart_valid_all_columns_module_4_100_records.csv",
    "evchart_valid_all_columns_module_4_10_records.csv",
    "evchart_valid_all_columns_module_4_200_records.csv",
    "evchart_valid_all_columns_module_4_250_records.csv",
    "evchart_valid_all_columns_module_4_25_records.csv",
    "evchart_valid_all_columns_module_4_50_records.csv",
    "evchart_valid_all_required_module_4.csv",
    "blank_row_all_required_mod_4.csv",
]
valid_null_files = [
    "valid_module_4_nulls.csv",
]
invalid_files = [
    "all_invalid_data_type_mod_4.csv",
    "evchart_all_invalid_data_type_mod_4.csv",
    "evchart_data_m4_invalid_column_header.csv",
    "evchart_data_m4_invalid_data_type.csv",
    "evchart_data_m4_missing_column_header.csv",
    "evchart_empty_value_for_outage_duration_mod_4.csv",
    "evchart_empty_value_for_outage_id_mod_4.csv",
    "evchart_empty_value_for_port_id_mod_4.csv",
    # "evchart_empty_value_for_station_id_mod_4.csv",
    "evchart_invalid_boundary_type_for_outage_duration_mod_4.csv",
    "evchart_invalid_column_header_name_for_outage_duration_mod_4.csv",
    "evchart_invalid_column_header_name_for_outage_id_mod_4.csv",
    "evchart_invalid_column_header_name_for_port_id_mod_4.csv",
    "evchart_invalid_column_header_name_for_station_id_mod_4.csv",
    "evchart_invalid_data_type_datetime_as_a_string_for_maintenance_report_start_mod_4.csv",
    "evchart_invalid_data_type_datetime_as_a_string_for_outage_id_mod_4.csv",
    "evchart_invalid_data_type_decimal_as_a_string_for_outage_id_mod_4.csv",
    "evchart_invalid_datetime_format_for_outage_id_start_mod_4.csv",
    "evchart_invalid_datetime_value_for_outage_id_start_mod_4.csv",
    "evchart_invalid_min_value_for_outage_duration_mod_4.csv",
    "evchart_invalid_regex_port_id_mod_4.csv",
    # "evchart_invalid_regex_station_id_mod_4.csv",
    "evchart_missing_column_header_for_maintenance_report_start_mod_4.csv",
    "evchart_missing_column_header_for_outage_duration_mod_4.csv",
    "evchart_missing_column_header_for_outage_id_mod_4.csv",
    "evchart_missing_column_header_for_port_id_mod_4.csv",
    # "evchart_missing_column_header_for_station_id_mod_4.csv",
    "evchart_non_required_or_recommended_column_header_module_4.csv",
    # "extra_required_column_header_mod_4.csv",
    "non_required_or_recommended_column_header_module_4.csv",
    "outage_duration_empty_value_mod_4.csv",
    "outage_duration_invalid_boundary_max_length_mod_4.csv",
    "outage_duration_invalid_boundary_min_value_mod_4.csv",
    "outage_duration_invalid_boundary_precision_mod_4.csv",
    "outage_duration_invalid_column_header_name_mod_4.csv",
    "outage_duration_invalid_min_value_mod_4.csv",
    "outage_duration_missing_column_header_mod_4.csv",
    "outage_id__invalid_datetime_value_mod_4.csv",
    "outage_id_empty_value_mod_4.csv",
    "outage_id_invalid_column_header_name_mod_4.csv",
    "outage_id_invalid_data_type_datetime_as_a_string_mod_4.csv",
    "outage_id_invalid_data_type_decimal_as_a_string_mod_4.csv",
    "outage_id_invalid_datetime_format_mod_4.csv",
    "outage_id_missing_column_header_mod_4.csv",
    "port_id_empty_value_mod_4.csv",
    "port_id_invalid_column_header_name_mod_4.csv",
    "port_id_missing_column_header_mod_4.csv",
    "port_id_regex_blank_space_mod_4.csv",
    # "station_id_empty_value_mod_4.csv",
    "station_id_invalid_column_header_name_mod_4.csv",
    # "station_id_missing_column_header_mod_4.csv",
    # "station_id_regex_blank_space_mod_4.csv",
    "invalid_module_4_null_outageid.csv",
    "invalid_module_4_null_excluded_outage.csv",
    "invalid_module_4_invalid_excluded_outage.csv",
    "invalid_module_4_null_excluded_outage_reason.csv",
    "invalid_module_4_invalid_excluded_outage_reason_min_value.csv",
    "invalid_module_4_invalid_excluded_outage_reason_max_value.csv",
    "invalid_module_4_null_outageduration.csv",
]


@pytest.mark.parametrize("filename", valid_files)
def test_csv_module4_valid(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as _mock_query:
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                module_number=ModuleDefinitionEnum.MODULE_4,
                df=df,
                upload_id=upload_id,
                feature_toggle_set={Feature.DATABASE_CENTRAL_CONFIG},
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", invalid_files)
def test_csv_module4_invalid(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                module_number=ModuleDefinitionEnum.MODULE_4,
                df=df,
                upload_id=upload_id,
                feature_toggle_set={},
            )
    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) > 0


@pytest.mark.parametrize("filename", valid_files + valid_biz_magic_file + valid_null_files)
def test_csv_module4_valid_biz_magic_and_central_config(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_4,
                df,
                upload_id,
                {Feature.ASYNC_BIZ_MAGIC_MODULE_4, Feature.DATABASE_CENTRAL_CONFIG},
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)
