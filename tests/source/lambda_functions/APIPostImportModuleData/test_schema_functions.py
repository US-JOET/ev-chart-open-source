import os
from unittest.mock import MagicMock, patch

import pandas
import pytest
# module paths are set in conftest.py
from APIPostImportModuleData.index import \
    handler as api_post_import_module_data  # pylint: disable=import-error
from error_report_messages_enum import ErrorReportMessages
from evchart_helper.custom_exceptions import EvChartFeatureStoreConnectionError
from module_validation import (drop_blank_rows, load_module_definitions,
                               validated_dataframe)


@pytest.fixture(name="sample_module_fields")
def fixture_sample_module_fields():
    return [
        {
            "field_name": "required_string",
            "required": True,
            "datatype": "string",
            "length": None
        },
        {
            "field_name": "required_decimal",
            "required": True,
            "datatype": "decimal",
            "max_precision": 11,
            "max_scale": 2
        },
        {
            "field_name": "recommended_decimal",
            "required": False,
            "datatype": "decimal",
            "max_precision": 11,
            "max_scale": 2
        }
    ]


# JE-2854: Required fields present: Each required field columns are present.
# If condition not met,
#   'error_description' value is:  ErrorReportMessages.MISSING_REQUIRED_COLUMN
#   'header_name' value is: the name of the missing column
# The 'error_row' value for all column-level schema compliance checks is: NA
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_missing_1_2_invalid_3(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "True"
    df = pandas.DataFrame(data={
            "recommended_decimal": ["abc", "def"]
        }
    )
    with patch('module_validation.metadata_update_validation_status') as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(module_fields=sample_module_fields, df=df, upload_id="123", module_number="3")
    assert response.get('is_compliant') is False
    assert len(response.get('conditions', [])) == 4

    assert {
        'error_description': ErrorReportMessages.MISSING_REQUIRED_COLUMN.format(column_name="required_string"),
        'header_name': 'required_string',
        'error_row': None
    } in response.get('conditions', [])

    assert {
        'error_description': ErrorReportMessages.MISSING_REQUIRED_COLUMN.format(column_name="required_decimal"),
        'header_name': 'required_decimal',
        'error_row': None
    } in response.get('conditions', [])


# JE-2854: An import missing one or more recommended fields does not
# constitute an error.
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_valid_df_all_required_fields(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "True"
    df = pandas.DataFrame(data={
            "required_string": ["hello", "world"],
            "required_decimal": ["987.60", "54.32"]
        }
    )
    with patch('module_validation.metadata_update_validation_status') as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(module_fields=sample_module_fields, df=df, upload_id="123", module_number="2")
    assert response.get('is_compliant') is True
    assert len(response.get('conditions', [])) == 0

@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_missing_1_2_valid_3(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "True"
    df = pandas.DataFrame(data={
            "recommended_decimal": ["12.34", "57.68"]
        }
    )
    with patch('module_validation.metadata_update_validation_status') as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(module_fields=sample_module_fields, df=df, upload_id="123", module_number="2")
    assert response.get('is_compliant') is False
    assert len(response.get('conditions', [])) == 2
    assert len(response.get('warnings', [])) == 0

@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_valid_df_all_fields(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "True"
    df = pandas.DataFrame(data={
            "required_string": ["hello", "world"],
            "required_decimal": ["987.60", "54.32"],
            "recommended_decimal": ["12.34", "57.68"]
        }
    )
    with patch('module_validation.metadata_update_validation_status') as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(module_fields=sample_module_fields, df=df, upload_id="123", module_number="2")
    assert response.get('is_compliant') is True
    assert len(response.get('conditions', [])) == 0
    assert isinstance(response.get('df'), pandas.DataFrame)
    assert len(response.get('warnings', [])) == 0


# JE-2854 Only schema-specified columns present: Only columns specified in
#   the module schema are present (required or recommended).
#   If condition not met, the 'error_description' value is:
#     "Unknown field {x} identified"
#     where {x} is the string of theunknown column name
#   Additionally:  The 'error_row' value for all column-level schema
#   compliance checks is: NA
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_valid_df_with_extra_fields_invalid(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "True"
    df = pandas.DataFrame(data={
            "required_string": ["hello", "world"],
            "required_decimal": ["987.60", "54.32"],
            "something_extra": ["something", "extra"]
        }
    )
    with patch('module_validation.metadata_update_validation_status') as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(module_fields=sample_module_fields, df=df, upload_id="123", module_number="2")
    assert response.get('is_compliant') is False
    assert len(response.get('conditions', [])) == 1
    assert response.get('conditions') == [{
        'error_description':
            ErrorReportMessages.UNKNOWN_COLUMN.format(column_name="something_extra"),
        'header_name': "something_extra",
        'error_row': None
    }]

@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_valid_df_drop_blank_lines(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "True"
    df_without_blank = pandas.DataFrame(data={
            "required_string": ["hello", "world"],
            "required_decimal": ["987.60", "54.32"],
            "recommended_decimal": ["12.34", "57.68"]
        }
    )
    df = pandas.DataFrame(data={
            "required_string": ["hello", "world", ""],
            "required_decimal": ["987.60", "54.32", ""],
            "recommended_decimal": ["12.34", "57.68", ""]
        }
    )

    pandas.testing.assert_frame_equal(
        df_without_blank,
        drop_blank_rows(df)
    )
    with patch('module_validation.metadata_update_validation_status') as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(module_fields=sample_module_fields, df=drop_blank_rows(df), upload_id="123", module_number="2")
    assert response.get('is_compliant') is True
    assert len(response.get('conditions', [])) == 0
    assert isinstance(response.get('df'), pandas.DataFrame)

@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_empty_df_invalid(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "True"
    df = pandas.DataFrame(data={
            "required_string": [],
            "required_decimal": [],
            "recommended_decimal": []
        },
        dtype='object'
    )
    with patch('module_validation.metadata_update_validation_status') as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(module_fields=sample_module_fields, df=df, upload_id="123", module_number="2")
    assert response.get('is_compliant') is False
    assert len(response.get('conditions', [])) == 1

@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_station_id_uuid_passthrough(mock_feature_toggle, sample_module_fields):
    mock_feature_toggle.return_value = "True"
    df = pandas.DataFrame(data={
            "required_string": ["hello", "world"],
            "required_decimal": ["987.60", "54.32"],
            "station_id": ["station1", "station2"],
            "station_uuid": ["abc123", "def456"],
        }
    )
    with patch('module_validation.metadata_update_validation_status') as mock_update:
        mock_update.return_value = True
        response = validated_dataframe(module_fields=sample_module_fields, df=df, upload_id="123", module_number="2")
    assert response.get('is_compliant') is True
    assert len(response.get('conditions', [])) == 0
    pandas.testing.assert_series_equal(
        df['station_id'], response['df']['station_id']
    )
    pandas.testing.assert_series_equal(
        df['station_uuid'], response['df']['station_uuid']
    )


@pytest.mark.skip('reactivate after schema validation updates')
@patch('awswrangler.mysql.to_sql')
@patch('APIPostImportModuleData.index.aurora')
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions", )
)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_lambda_response_body_valid_200(mock_feature_toggle, mock_aurora, mock_awswrangler):
    mock_feature_toggle.return_value = "True"
    headers = {
        'module_id': '2',
        'quarter': '4',
        'year': '2023',
        'uploaded_by': 'pytest',
        'org_id': '123',
        'parent_org': '456',
        'sr_id': '789',
        'dr_id': '1020'
    }
    with open(
        "./tests/sample_data/evchart_valid_all_required_module_2.csv", "r",
        encoding="utf-8"
    ) as fh:
        body = fh.read()
    event = {"headers": headers, "body": body}
    api_import_response = api_post_import_module_data(event, None)
    assert api_import_response.get('statusCode') == 200
    assert mock_awswrangler.called
    assert mock_aurora.get_connection.called
    assert mock_aurora.get_connection().commit.called
    assert mock_aurora.close_connection.called


@pytest.mark.skip('rewrite with a proper request context instead of headers')
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions", )
)
@patch("APIPostImportModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_lambda_response_body_invalid_406():
    headers = {
        'module_id': '2',
        'quarter': '4',
        'year': '2023',
        'uploaded_by': 'pytest',
        'org_id': '123',
        'parent_org': '456',
        'sr_id': '789',
        'dr_id': '1020'
    }
    with open(
        "./tests/sample_data/all_invalid_data_type_mod_2.csv", "r",
        encoding="utf-8"
    ) as fh:
        body = fh.read()
    event = {"headers": headers, "body": body}
    api_import_response = api_post_import_module_data(event, None)
    assert api_import_response.get('statusCode') == 406


@pytest.mark.skip('reactivate after schema validation updates')
@patch('awswrangler.mysql.to_sql')
@patch('APIPostImportModuleData.index.aurora')
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions", )
)
def test_lambda_response_body_sql_failed(mock_aurora, mock_awswrangler):
    mock_awswrangler.side_effect = ValueError
    headers = {
        'module_id': '2',
        'quarter': '4',
        'year': '2023',
        'uploaded_by': 'pytest',
        'org_id': '123',
        'parent_org': '456',
        'sr_id': '789',
        'dr_id': '1020'
    }
    with open(
        "./tests/sample_data/evchart_valid_all_required_module_2.csv", "r",
        encoding="utf-8"
    ) as fh:
        body = fh.read()
    event = {"headers": headers, "body": body}
    api_import_response = api_post_import_module_data(event, None)
    assert api_import_response.get('statusCode') == 500
    assert mock_awswrangler.called
    assert mock_aurora.get_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIPostImportModuleData.index.aurora')
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions", )
)
def test_lambda_response_body_aurora_connect_failed(mock_aurora):
    mock_aurora.get_connection = MagicMock(side_effect=ZeroDivisionError)
    headers = {
        'module_id': '2',
        'quarter': '4',
        'year': '2023',
        'uploaded_by': 'pytest',
        'org_id': '123',
        'parent_org': '456',
        'sr_id': '789',
        'dr_id': '1020'
    }
    with open(
        "./tests/sample_data/evchart_valid_all_required_module_2.csv", "r",
        encoding="utf-8"
    ) as fh:
        body = fh.read()
    event = {"headers": headers, "body": body}
    api_import_response = api_post_import_module_data(event, None)
    assert api_import_response.get('statusCode') == 500
    assert mock_aurora.get_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch(
    "APIPostImportModuleData.index.FeatureToggleService"
    ".get_active_feature_toggles"
)
@patch('APIPostImportModuleData.index.aurora')
@patch.object(
    load_module_definitions,
    "__defaults__",
    ("./source/lambda_layers/python/module_validation/module_definitions", )
)
def test_feature_toggle_set_with_true_and_exception(
    mock_aurora,
    mock_get_feature_toggle_by_enum
):
    mock_get_feature_toggle_by_enum.side_effect = \
        ["True", EvChartFeatureStoreConnectionError, "True", "True", "True"]
    headers = {
        'module_id': '2',
        'quarter': '4',
        'year': '2023',
        'uploaded_by': 'pytest',
        'org_id': '123',
        'parent_org': '456',
        'sr_id': '789',
        'dr_id': '1020'
    }
    with open(
        "./tests/sample_data/evchart_valid_all_required_module_2.csv", "r",
        encoding="utf-8"
    ) as fh:
        body = fh.read()
    event = {"headers": headers, "body": body}
    api_import_response = api_post_import_module_data(event, None)
    assert api_import_response.get('statusCode') == 401
    assert mock_aurora.get_connection.called

