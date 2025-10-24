from unittest.mock import MagicMock, patch

import pandas
import pytest

# pylint: disable=import-error
# module paths are set in conftest.py
from AsyncDataValidation.index import get_dataframe_from_csv
from feature_toggle.feature_enums import Feature
from module_validation import ModuleDefinitionEnum, validated_dataframe_by_module_id

valid_files = [
    "all_columns_module_9.csv",
    "all_required_module_9.csv",
    "blank_row_all_required_mod_9.csv",
    "der_acq_type_false_value_mod_9.csv",
    "der_acq_type_true_value_mod_9.csv",
    "valid_all_columns_module_9_100_records.csv",
    "valid_all_columns_module_9_10_records.csv",
    "valid_all_columns_module_9_250_records.csv",
    "valid_all_columns_module_9_25_records.csv",
    "valid_all_columns_module_9_50_records.csv",
    "station_upgrade_false_value_mod_9.csv",
    "station_upgrade_true_value_mod_9.csv",
    "equipment_acq_type_false_value_mod_9.csv",
    "equipment_acq_type_true_value_mod_9.csv",
    "real_property_acq_type_false_value_mod_9.csv",
    "real_property_acq_type_true_value_mod_9.csv",
]
null_files = ["invalid_module_9_nulls.csv", "invalid_module_9_required_nulls.csv"]
valid_biz_magic_file = ["valid_module_9_biz_magic.csv"]
invalid_files = [
    "all_invalid_data_type_mod_9.csv",
    "der_acq_type_invalid_column_header_name_mod_9.csv",
    "der_acq_type_invalid_data_type_int_as_a_boolean_mod_9.csv",
    "der_cost_federal_blank_space_mod_9.csv",
    "der_cost_federal_invalid_boundary_max_length_mod_9.csv",
    "der_cost_federal_invalid_boundary_min_value_mod_9.csv",
    "der_cost_federal_invalid_boundary_precision_mod_9.csv",
    "der_cost_federal_invalid_column_header_name_mod_9.csv",
    "der_cost_federal_missing_column_header_mod_9.csv",
    # "der_cost_total_invalid_boundary_max_length_mod_9.csv",
    "der_cost_total_invalid_boundary_min_value_mod_9.csv",
    "der_cost_total_invalid_boundary_precision_mod_9.csv",
    "der_cost_total_invalid_column_header_name_mod_9.csv",
    "der_cost_total_missing_column_header_name_mod_9.csv",
    "der_cost_total_regex_blank_space_mod_9.csv",
    "der_install_cost_federal_blank_space_mod_9.csv",
    "der_install_cost_federal_empty_value_mod_9.csv",
    "der_install_cost_federal_invalid_boundary_max_length_mod_9.csv",
    "der_install_cost_federal_invalid_boundary_min_value_mod_9.csv",
    "der_install_cost_federal_invalid_boundary_precision_mod_9.csv",
    "der_install_cost_federal_invalid_column_header_name_mod_9.csv",
    "der_install_cost_federal_missing_column_header_mod_9.csv",
    "der_install_cost_total_blank_space_mod_9.csv",
    "der_install_cost_total_invalid_boundary_max_length_mod_9.csv",
    "der_install_cost_total_invalid_boundary_min_value_mod_9.csv",
    "der_install_cost_total_invalid_boundary_precision_mod_9.csv",
    "der_install_cost_total_invalid_column_header_name_mod_9.csv",
    "dist_sys_cost_federal_empty_value_mod_9.csv",
    "dist_sys_cost_federal_invalid_boundary_max_length_mod_9.csv",
    "dist_sys_cost_federal_invalid_boundary_min_value_mod_9.csv",
    "dist_sys_cost_federal_invalid_boundary_precision_mod_9.csv",
    "dist_sys_cost_federal_invalid_column_header_name_mod_9.csv",
    "dist_sys_cost_federal_missing_column_header_mod_9.csv",
    "dist_sys_cost_federal_missing_column_header_name_mod_9.csv",
    "dist_sys_cost_total_invalid_boundary_max_length_mod_9.csv",
    "dist_sys_cost_total_invalid_boundary_min_value_mod_9.csv",
    "dist_sys_cost_total_invalid_column_header_name_mod_9.csv",
    "dist_sys_cost_total_missing_column_header_name_mod_9.csv",
    "dist_sys_cost_total_regex_blank_space_mod_9.csv",
    "equipment_acq_date_invalid_column_header_name_mod_9.csv",
    "equipment_acq_date_invalid_datetime_format_mod_9.csv",
    "equipment_acq_date_invalid_datetime_value_mod_9.csv",
    "equipment_acq_type_invalid_column_header_name_mod_9.csv",
    "equipment_acq_type_invalid_data_type_int_as_a_boolean_mod_9.csv",
    "equipment_cost_federal__empty_value_mod_9.csv",
    # "equipment_cost_federal_invalid_boundary_max_length_mod_9.csv",
    "equipment_cost_federal_invalid_boundary_min_value_mod_9.csv",
    "equipment_cost_federal_invalid_boundary_precision_mod_9.csv",
    "equipment_cost_federal_invalid_column_header_name_mod_9.csv",
    "equipment_cost_federal_missing_column_header_name_mod_9.csv",
    "equipment_cost_federal_regex_blank_space_mod_9.csv",
    # "equipment_cost_total_invalid_boundary_max_length_mod_9.csv",
    "equipment_cost_total_invalid_boundary_min_value_mod_9.csv",
    "equipment_cost_total_invalid_boundary_precision_mod_9.csv",
    "equipment_cost_total_invalid_column_header_name_mod_9.csv",
    "equipment_cost_total_missing_column_header_name_mod_9.csv",
    "equipment_cost_total_regex_blank_space_mod_9.csv",
    "equipment_install_cost_const_invalid_boundary_max_length_mod_9.csv",
    "equipment_install_cost_const_invalid_boundary_min_value_mod_9.csv",
    "equipment_install_cost_const_invalid_boundary_precision_mod_9.csv",
    "equipment_install_cost_const_invalid_column_header_name_mod_9.csv",
    "equipment_install_cost_elec_invalid_boundary_max_length_mod_9.csv",
    "equipment_install_cost_elec_invalid_boundary_min_value_mod_9.csv",
    "equipment_install_cost_elec_invalid_boundary_precision_mod_9.csv",
    "equipment_install_cost_elec_invalid_column_header_name_mod_9.csv",
    "equipment_install_cost_federal_empty_value_mod_9.csv",
    "equipment_install_cost_federal_invalid_boundary_max_length_mod_9.csv",
    "equipment_install_cost_federal_invalid_boundary_min_value_mod_9.csv",
    "equipment_install_cost_federal_invalid_boundary_precision_mod_9.csv",
    "equipment_install_cost_federal_invalid_column_header_name_mod_9.csv",
    "equipment_install_cost_federal_missing_column_header_name_mod_9.csv",
    "equipment_install_cost_federal_regex_blank_space_mod_9.csv",
    "equipment_install_cost_labor_invalid_boundary_max_length_mod_9.csv",
    "equipment_install_cost_labor_invalid_boundary_min_value_mod_9.csv",
    "equipment_install_cost_labor_invalid_boundary_precision_mod_9.csv",
    "equipment_install_cost_labor_invalid_column_header_name_mod_9.csv",
    "equipment_install_cost_other_invalid_boundary_max_length_mod_9.csv",
    "equipment_install_cost_other_invalid_boundary_min_value_mod_9.csv",
    "equipment_install_cost_other_invalid_boundary_precision_mod_9.csv",
    "equipment_install_cost_other_invalid_column_header_name_mod_9.csv",
    "equipment_install_cost_total__invalid_column_header_name_mod_9.csv",
    # "equipment_install_cost_total_invalid_boundary_max_length_mod_9.csv",
    "equipment_install_cost_total_invalid_boundary_min_value_mod_9.csv",
    "equipment_install_cost_total_invalid_boundary_precision_mod_9.csv",
    "equipment_install_cost_total_missing_column_header_name_mod_9.csv",
    "equipment_install_cost_total_regex_blank_space_mod_9.csv",
    "equipment_install_date_invalid_column_header_name_mod_9.csv",
    "equipment_install_date_invalid_datetime_format_mod_9.csv",
    "equipment_install_date_invalid_datetime_value_mod_9.csv",
    "evchart_all_invalid_data_type_mod_9.csv",
    "evchart_data_m9_empty_value.csv",
    "evchart_data_m9_invalid_column_header.csv",
    "evchart_data_m9_invalid_data_type.csv",
    "evchart_data_m9_missing_column_header.csv",
    "evchart_empty_value_for_der_cost_federal_mod_9.csv",
    "evchart_empty_value_for_real_property_cost_federal_mod_9.csv",
    # "evchart_invalid_boundary_type_for_all_decimal_data_mod_9.csv",
    "evchart_invalid_data_type_String_as_all_decimal_data_mod_9.csv",
    "evchart_missing_column_header_for_der_install_cost_total_mod_9.csv",
    "evchart_missing_column_header_for_real_property_cost_total_mod_9.csv",
    "evchart_non_required_or_recommended_column_header_module_9.csv",
    # "extra_required_column_header_mod_9.csv",
    "non_required_or_recommended_column_header_module_9.csv",
    "project_id_invalid_column_header_name_mod_9.csv",
    "real_property_acq_date_invalid_column_header_name_mod_9.csv",
    "real_property_acq_date_invalid_datetime_format_mod_9.csv",
    "real_property_acq_date_invalid_datetime_vaule_mod_9.csv",
    "real_property_acq_type_invalid_column_header_name_mod_9.csv",
    "real_property_acq_type_invalid_data_type_int_as_a_boolean_mod_9.csv",
    "real_property_cost_federal_empty_value_mod_9.csv",
    # "real_property_cost_federal_invalid_boundary_max_length_mod_9.csv",
    "real_property_cost_federal_invalid_boundary_min_value_mod_9.csv",
    "real_property_cost_federal_invalid_boundary_precision_mod_9.csv",
    "real_property_cost_federal_invalid_column_header_name_mod_9.csv",
    "real_property_cost_federal_missing_column_header_mod_9.csv",
    "real_property_cost_federal_regex_blank_space_mod_9.csv",
    # "real_property_cost_total_invalid_boundary_max_length_mod_9.csv",
    "real_property_cost_total_invalid_boundary_min_value_mod_9.csv",
    "real_property_cost_total_invalid_boundary_precision_mod_9.csv",
    "real_property_cost_total_invalid_column_header_name_mod_9.csv",
    "real_property_cost_total_missing_column_header_mod_9.csv",
    "real_property_cost_total_regex_blank_space_mod_9.csv",
    "service_cost_federal__empty_value_mod_9.csv",
    "service_cost_federal__missing_column_header_mod_9.csv",
    "service_cost_federal_empty_value_mod_9.csv",
    "service_cost_federal_invalid_boundary_max_length_mod_9.csv",
    "service_cost_federal_invalid_boundary_min_value_mod_9.csv",
    "service_cost_federal_invalid_boundary_precision_mod_9.csv",
    "service_cost_federal_invalid_column_header_name_mod_9.csv",
    "service_cost_federal_missing_column_header_mod_9.csv",
    "service_cost_federal_regex_blank_space_mod_9.csv",
    "service_cost_total_invalid_boundary_max_length_mod_9.csv",
    "service_cost_total_invalid_boundary_min_value_mod_9.csv",
    "service_cost_total_invalid_boundary_precision_mod_9.csv",
    "service_cost_total_invalid_column_header_name_mod_9.csv",
    "service_cost_total_missing_column_header_mod_9.csv",
    "service_cost_total_regex_blank_space_mod_9.csv",
    "service_upgrade_invalid_data_type_int_as_a_boolean_mod_9.csv",
    # "station_id_empty_value_mod_9.csv",
    "station_id_invalid_column_header_name_mod_9.csv",
    # "station_id_missing_column_header_name_mod_9.csv",
    # "station_id_regex_blank_space_mod_9.csv",
    "station_upgrade_invalid_column_header_name_mod_9.csv",
    "invalid_module_9_null_equipment_acq_date.csv",
    "invalid_module_9_null_multiple.csv",
]


@pytest.mark.parametrize("filename", valid_files + valid_biz_magic_file)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_csv_module9_valid_bizmagic(mock_feature_toggle, filename):
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
                module_number=ModuleDefinitionEnum.MODULE_9,
                df=df,
                upload_id=upload_id,
                feature_toggle_set={Feature.ASYNC_BIZ_MAGIC_MODULE_9},
            )

    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)


@pytest.mark.parametrize("filename", invalid_files)
def test_csv_module9_invalid(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                module_number=ModuleDefinitionEnum.MODULE_9,
                df=df,
                upload_id=upload_id,
                feature_toggle_set={Feature.ASYNC_BIZ_MAGIC_MODULE_9, Feature.DATABASE_CENTRAL_CONFIG},
            )

    assert response.get("is_compliant") is False
    assert len(response.get("conditions")) > 0


@pytest.mark.parametrize("filename", valid_files)
def test_csv_module9_valid_biz_magic_and_central_config(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
    with patch("module_validation.execute_query") as mock_query:
        mock_query.return_value = []
        with patch("module_validation.aurora.get_connection") as mock_aurora:
            mock_aurora.return_value = MagicMock()
            df = get_dataframe_from_csv(body)
            upload_id = "123"
            response = validated_dataframe_by_module_id(
                ModuleDefinitionEnum.MODULE_9,
                df,
                upload_id,
                {Feature.ASYNC_BIZ_MAGIC_MODULE_9, Feature.DATABASE_CENTRAL_CONFIG},
            )
    assert response.get("is_compliant") is True
    assert response.get("conditions") == []
    assert isinstance(response.get("df"), pandas.DataFrame)
