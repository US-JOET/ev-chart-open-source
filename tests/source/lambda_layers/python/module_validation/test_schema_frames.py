from unittest.mock import patch
import pandas
import pytest
from error_report_messages_enum import ErrorReportMessages


# module paths are set in conftest.py
from module_validation import (
    adjust_for_booleans,
    load_module_definitions,
    validated_dataframe
)


@pytest.fixture(name="sample_module_fields")
def fixture_sample_module_fields():
    return  [
       {
            "field_name": "required_decimal_11_2",
            "required": True,
            "datatype": "decimal",
            "max_precision": 11,
            "max_scale": 2
        },
        {
            "field_name": "recommended_decimal_7_2",
            "required": True,
            "datatype": "decimal",
            "max_precision": 7,
            "max_scale": 2
        }
    ]


@patch(
    "APIPostImportModuleData.index.FeatureToggleService"
    ".get_feature_toggle_by_enum"
)
def test_validation_summary(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "True"
    df = pandas.DataFrame(data={
        "required_decimal_11_2": ["abc", "123.45", "567.89"],
        "recommended_decimal_7_2": ["123.45", "234.56", "123456.78"]
    })
    df.index = df.index + 1

    with patch(
        'module_validation.metadata_update_validation_status'
    ) as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(
            module_fields=sample_module_fields,
            df=df,
            upload_id="123",
            module_number=2
        )
    assert response.get('total_records') == 3
    assert response.get('valid_records') == 1
    assert response.get('rejected_records') == 2

    assert len(response.get('conditions', [])) == 2
    assert {
        'error_description':
            ErrorReportMessages.INVALID_DECIMAL_INPUT.format(),
        'header_name': 'required_decimal_11_2',
        'error_row': 1
    } in response.get('conditions', [])
    assert {
        'error_description':
            ErrorReportMessages.MAX_DECIMAL_LENGTH_EXCEEDED.format(),
        'header_name': 'recommended_decimal_7_2',
        'error_row': 3
    } in response.get('conditions', [])


@patch(
    "APIPostImportModuleData.index.FeatureToggleService"
    ".get_feature_toggle_by_enum"
)
def test_mix_schema_compliant(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "False"
    df = pandas.DataFrame(data={
        "required_decimal_11_2": ["abc", "123.45", "567.89"],
        "recommended_decimal_7_2": ["123.45", "234.56", "123456.78"]
    })
    df.index = df.index + 1

    with patch(
        'module_validation.metadata_update_validation_status'
    ) as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(
            module_fields=sample_module_fields,
            df=df,
            upload_id="123",
            module_number=2
        )
    assert response.get('is_compliant') is False
    assert response.get('total_records') == 3
    assert response.get('valid_records') == 1
    assert response.get('rejected_records') == 2
    assert len(response.get('conditions', [])) == 2

    assert {
        'error_description':
            ErrorReportMessages.INVALID_DECIMAL_INPUT.format(),
        'header_name': 'required_decimal_11_2',
        'error_row': 1
    } in response.get('conditions', [])
    assert {
        'error_description':
            ErrorReportMessages.MAX_DECIMAL_LENGTH_EXCEEDED.format(),
        'header_name': 'recommended_decimal_7_2',
        'error_row': 3
    } in response.get('conditions', [])


# JE-4672 Unable to download / view error log when a module is imported
# with multiple columns with the same header
def test_duplicate_column_headers(sample_module_fields):
    df = pandas.DataFrame(data={
        "required_decimal_11_2": ["888.88", "123.45", "567.89"],
        "recommended_decimal_7_2": ["123.45", "234.56", "1234.78"],
        "col3": ["123.45", "234.56", "1234.78"]
    })
    df.index = df.index + 1
    df.columns = [
        "required_decimal_11_2",
        "recommended_decimal_7_2",
        "required_decimal_11_2"
        ]

    with patch(
        'module_validation.metadata_update_validation_status'
    ) as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(
            module_fields=sample_module_fields,
            df=df,
            upload_id="123",
            module_number=2
        )

    assert response.get('is_compliant') is False
    assert response.get('total_records') == 3
    assert len(response.get('conditions', [])) == 1
    assert {
        'error_description':
            ErrorReportMessages.DUPLICATE_COLUMN.format(column_name="required_decimal_11_2"),
        'header_name': 'required_decimal_11_2',
        'error_row': None
    } in response.get('conditions', [])


# JE-5324 Properly Store TRUE=1, FALSE=0, null=null in DB for any Boolean Value
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions",),
)
def test_boolean_conversion():
    m8_df = pandas.DataFrame({
        "station_id": {
            "2": "0006ffce-7c48-4ec0-85bc-afdc51054b85",
            "3": "0006ffce-7c48-4ec0-85bc-afdc51054b85",
            "4": "0006ffce-7c48-4ec0-85bc-afdc51054b85"
        },
        "network_provider": {
            "2": "bc_hydro", "3": "bc_hydro", "4": "bc_hydro"
        },
        "der_upgrade": {"2": "TRUE", "3": "FALSE", "4": ""},
        "der_onsite": {"2": "TRUE", "3": "FALSE", "4": "FALSE"},
        "der_type": {"2": "type1", "3": "type2", "4": "type3"},
        "der_type_other": {
            "2": "ombined_heat_and_power_units-utilize",
            "3": "ombined_heat_and_power_units-utilize",
            "4": "ombined_heat_and_power_units-utilize"
        },
        "der_kw": {"2": "123.15", "3": "123.15", "4": "123.15"},
        "der_kwh": {"2": "45.12", "3": "45.12", "4": "45.12"},
        "upload_id": {
            "2": "0046b6e0-372a-4e38-b6d1-3183de5839c7",
            "3": "0046b6e0-372a-4e38-b6d1-3183de5839c7",
            "4": "0046b6e0-372a-4e38-b6d1-3183de5839c7"
        },
        "station_uuid": {
            "2": "e1403c56-c333-4967-8434-8b69acc90b14",
            "3": "e1403c56-c333-4967-8434-8b69acc90b14",
            "4": "e1403c56-c333-4967-8434-8b69acc90b14"
        }
    })
    response_df = adjust_for_booleans(m8_df, "8")
    pandas.testing.assert_series_equal(
        response_df['der_upgrade'],
        pandas.Series(
            data=[True, False, None],
            name='der_upgrade',
            index=['2', '3', '4']
        )
    )

    m8_df.drop(['der_upgrade', 'der_onsite'], inplace=True, axis=1)
    pandas.testing.assert_frame_equal(m8_df, adjust_for_booleans(m8_df, "8"))
