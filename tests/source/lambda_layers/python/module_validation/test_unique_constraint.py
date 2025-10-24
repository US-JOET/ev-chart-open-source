import os
from unittest.mock import MagicMock, patch

from database_central_config import DatabaseCentralConfig
from feature_toggle.feature_enums import Feature
from AsyncDataValidation.index import get_dataframe_from_csv
from error_report_messages_enum import ErrorReportMessages

from module_validation.unique_constraint import (
    get_constraints_conditions,
    get_module_constraints_by_module_id,
    unique_constraint_violations,
    unique_constraint_violations_for_async,
    get_module_constraints_by_module_id,
    get_duplicate_within_db,
)

import pandas
import pytest


@pytest.fixture(name="config")
def fixture_config():
    return DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json",
        )
    )


# helper function used in all the tests to load the csv file from sample data folder
# and correctly set the station_uuid as the system would before entering data validation
def get_df_from_sample_data_csv(filename):
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
        async_df = get_dataframe_from_csv(body)
        async_df["station_uuid"] = "temp_uuid"
    return async_df


def test_constraint_already_exists():
    index = pandas.MultiIndex.from_tuples(
        [("1", "3", "5")], names=["station_uuid", "port_id", "session_id"]
    )
    constraint_series = pandas.Series(index=index, data=[{"123", "456"}])
    mock_log_event = MagicMock()
    response = get_constraints_conditions(mock_log_event, "789", constraint_series)
    assert response == []
    assert mock_log_event.log_custom_exception_called


@patch("module_validation.unique_constraint.execute_query_df")
@patch("module_validation.unique_constraint.get_module_id")
@patch("module_validation.unique_constraint.check_constraints_in_data")
def test_empty_constraints(
    mock_check_constraints_in_data, mock_get_module_id, mock_execute_query_df
):
    mock_check_constraints_in_data.return_value = pandas.DataFrame()
    mock_execute_query_df.return_value = pandas.DataFrame()
    mock_get_module_id.return_value = "2"

    response = unique_constraint_violations(
        cursor=MagicMock(),
        upload_id="upload01",
        dr_id="dr123",
        log_event=MagicMock(),
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
    )

    assert response.get("errors") == []
    assert response.get("df").empty


@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.execute_query_df")
def test_unique_constraint_violations_for_async_no_duplicates_in_db_and_file_happy_path(
    mock_execute_query_df, mock_database_central_config, mock_get_upload_metadata, config
):
    mock_database_central_config.return_value = config
    filename = "all_required_module_2.csv"
    async_df = get_df_from_sample_data_csv(filename)

    module_id = "2"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}
    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": [],
            "station_uuid": [],
            "port_id": [],
            "station_id_upload": [],
            "network_provider_upload": [],
            "session_id": [],
        }
    )

    response = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="upload01",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
    )

    assert response.get("errors") == []
    assert response.get("df").equals(async_df)


@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.get_duplicate_within_db")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
def test_unique_constraint_violations_for_async_no_null_duplicates_in_db_and_file_happy_path_m4(
    mock_database_central_config, mock_get_duplicate_within_db, mock_get_upload_metadata, config
):
    mock_database_central_config.return_value = config
    filename = "valid_module_4_nulls.csv"
    async_df = get_df_from_sample_data_csv(filename)

    module_id = "4"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "4"}
    get_duplicate_within_db.return_value = pandas.DataFrame()
    response = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="upload01",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_4},
    )

    assert response.get("errors") == []
    assert response.get("df").equals(async_df)


@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.execute_query_df")
@patch("module_validation.unique_constraint.check_constraints_in_data")
def test_unique_constraint_violations_for_async_given_empty_dataframe_returns_no_errors(
    mock_check_constraints_in_data, mock_execute_query_df, mock_get_upload_metadata
):
    async_df = pandas.DataFrame()
    module_id = "2"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}

    response = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="upload01",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
    )

    assert not mock_execute_query_df.called
    assert not mock_check_constraints_in_data.called
    assert response.get("errors") == []
    assert response.get("df") is None


@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.execute_query_df")
def test_unique_constraints_violations_for_async_multiple(
    mock_execute_query_df, mock_database_central_config, mock_get_upload_metadata, config
):
    """
    test unique constraints violations for async given ran multiple times
    does not change constraints
    """
    filename = "all_required_module_2.csv"
    async_df = get_df_from_sample_data_csv(filename)

    mock_database_central_config.return_value = config
    module_id = "2"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}

    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": ["b2_submitted"],
            "network_provider_upload": ["bob"],
            "station_uuid": ["789"],
            "station_id_upload": ["789"],
            "session_id": ["7"],
            "port_id": ["3"],
        }
    )
    constraints_before = get_module_constraints_by_module_id(module_id)
    _ = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="a1_draft",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={
            Feature.UNIQUE_CONSTRAINT_MODULE_2,
        },
    )

    constraints_after = get_module_constraints_by_module_id(module_id)

    assert constraints_before == constraints_after


@patch("module_validation.unique_constraint.get_module_constraints_by_module_id")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.execute_query_df")
@patch("module_validation.unique_constraint.get_module_id")
@patch("module_validation.unique_constraint.check_constraints_in_data")
def test_ft_central_config_false(
    mock_check_constraints_in_data,
    mock_get_module_id,
    mock_execute_query_df,
    mock_database_central_config,
    mock_get_module_constraints_by_module_id,
):
    mock_check_constraints_in_data.return_value = pandas.DataFrame()
    mock_execute_query_df.return_value = pandas.DataFrame()
    mock_get_module_id.return_value = "2"

    response = unique_constraint_violations(
        cursor=MagicMock(),
        upload_id="upload01",
        dr_id="dr123",
        log_event=MagicMock(),
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
    )

    assert response.get("errors") == []
    assert response.get("df").empty
    assert not mock_database_central_config.called
    assert mock_get_module_constraints_by_module_id.called


@patch("module_validation.unique_constraint.get_module_constraints_by_module_id")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.execute_query_df")
@patch("module_validation.unique_constraint.get_module_id")
@patch("module_validation.unique_constraint.check_constraints_in_data")
def test_ft_central_config_true(
    mock_check_constraints_in_data,
    mock_get_module_id,
    mock_execute_query_df,
    mock_database_central_config,
    mock_get_module_constraints_by_module_id,
):
    mock_check_constraints_in_data.return_value = pandas.DataFrame()
    mock_execute_query_df.return_value = pandas.DataFrame()
    mock_get_module_id.return_value = "2"

    response = unique_constraint_violations(
        cursor=MagicMock(),
        upload_id="upload01",
        dr_id="dr123",
        log_event=MagicMock(),
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2, Feature.DATABASE_CENTRAL_CONFIG},
    )

    assert response.get("errors") == []
    assert response.get("df").empty
    assert mock_database_central_config.called
    assert not mock_get_module_constraints_by_module_id.called


@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.execute_query_df")
def test_unique_constraint_violations_for_async_duplicate_non_null_data_in_db_found(
    mock_execute_query_df, mock_database_central_config, mock_get_upload_metadata, config
):
    """
    test_unique_constraint_violations_for_s2s_given_dataframe_with_
    constraint_violation_return_list
    """
    filename = "all_required_module_2.csv"
    async_df = get_df_from_sample_data_csv(filename)

    module_id = "2"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}
    mock_database_central_config.return_value = config
    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": ["b2_submitted"],
            "station_uuid": ["789"],
            "station_id_upload": ["789"],
            "network_provider_upload": ["np1"],
            "session_id": ["7"],
            "port_id": ["3"],
        }
    )

    response = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="a1_draft",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
    )

    assert len(response.get("errors")) == 1
    assert response.get("df") is None


@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.execute_query_df")
def test_unique_constraint_violation_duplicate_rows_in_file(
    mock_execute_query_df, mock_database_central_config, mock_get_upload_metadata, config
):
    """
    testing scenario for duplicate rows in file
    """
    filename = "invalid_module_2_duplicate_columns_in_file.csv"
    async_df = get_df_from_sample_data_csv(filename)

    module_id = "2"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}
    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": [],
            "network_provider_upload": [],
            "station_uuid": [],
            "station_id_upload": [],
            "session_id": [],
            "port_id": [],
        }
    )
    mock_database_central_config.return_value = config
    constraint_unique_violation_async = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="a1_draft",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
    )
    assert len(constraint_unique_violation_async.get("errors")) > 0


@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.get_duplicate_within_db")
def test_unique_constraint_violation_duplicate_data_in_file_and_db(
    mock_get_duplicate_within_db, mock_database_central_config, mock_get_upload_metadata, config
):
    """
    testing scenario where there are duplicate rows in csv and duplicate rows present in
    the database
    """
    filename = "invalid_module_2_duplicate_columns_in_file.csv"
    with open(f"./tests/sample_data/{filename}", "r", encoding="utf-8") as fh:
        body = fh.read()
        input_df = get_dataframe_from_csv(body)
        input_df["station_uuid"] = "temp_uuid"

        mock_database_central_config.return_value = config
        mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}
        mock_get_duplicate_within_db.return_value = pandas.DataFrame(
            data={
                "upload_id": [
                    "65805308-0958-4912-a1a7-aa227f9306f6",
                    "65805308-0958-4912-a1a7-aa227f9306f6",
                ],
                "network_provider_upload": ["blink", "blink"],
                "station_uuid": [
                    "b375a95a-454b-4d05-a000-3cfe3f6d81e3",
                    "b375a95a-454b-4d05-a000-3cfe3f6d81e3",
                ],
                "station_id_upload": ["subway-station-updated3", "subway-station-updated3"],
                "session_id": ["10008", "10009"],
                "port_id": ["1111", "12"],
            }
        )

        response = unique_constraint_violations_for_async(
            cursor=MagicMock(),
            upload_id="curr_upload_id_123",
            dr_id="dr_id",
            log_event=MagicMock(),
            df=input_df,
            module_id="2",
            feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
        )
        assert len(response["errors"]) == 3


@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.execute_query_df")
def test_unique_constraints_violations_for_async_database_constraint(
    mock_execute_query_df, mock_database_central_config, mock_get_upload_metadata, config
):
    """
    test duplicate data against unique_constraint and
    validate if duplicate data error correctly concatenate with the
    database constraint and works as expected. If there is error returned
    then we can assume that
    """
    filename = "all_required_module_2.csv"
    async_df = get_df_from_sample_data_csv(filename)

    module_id = "2"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}
    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": ["a1_draft", "a2_draft", "a3_draft", "a4_draft"],
            "network_provider_upload": ["bob", "bob", "bob", "bob"],
            "station_uuid": ["APIM", "APIM", "APID", "APID"],
            "station_id_upload": ["APIM", "APIM", "APID", "APID"],
            "session_id": ["None", "None", "None", "None"],
            "port_id": ["None", "None", "None", "None"],
        }
    )
    mock_database_central_config.return_value = config
    constraint_unique_violation_async = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="a1_draft",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
    )

    assert len(constraint_unique_violation_async.get("errors")) > 0


@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.execute_query_df")
def test_unique_constraints_violations_for_async_duplicate_rows_in_csv_no_database_constraint(
    mock_execute_query_df, mock_database_central_config, mock_get_upload_metadata, config
):
    """
    test duplicate data against unique_constraint and
    validate if duplicate data error correctly concatenate with the
    database constraint and works as expected. If there is error returned
    then we can assume that
    """
    filename = "invalid_module_2_duplicate_columns_in_file.csv"
    async_df = get_df_from_sample_data_csv(filename)
    module_id = "2"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}
    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": [],
            "network_provider_upload": [],
            "station_uuid": [],
            "station_id_upload": [],
            "session_id": [],
            "port_id": [],
        }
    )
    mock_database_central_config.return_value = config
    constraint_unique_violation_async = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="a1_draft",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
    )
    assert len(constraint_unique_violation_async.get("errors")) > 0


# JE-6650 adding duplicate checks for null modules, specifically for module 2
@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.execute_query_df")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
def test_unique_constraint_violations_for_M2_null_duplicate_in_system(
    mock_database_central_config,
    mock_execute_query_df,
    mock_get_upload_metadata,
    config,
):
    filename = "valid_module_2_nulls_empty.csv"
    async_df = get_df_from_sample_data_csv(filename)

    module_id = "2"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}
    mock_database_central_config.return_value = config
    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": ["b2_submitted"],
            "station_uuid": ["789"],
            "station_id_upload": ["789"],
            "network_provider_upload": ["np1"],
            "port_id": ["12"],
            "session_id": ["1223"],
        }
    )
    result = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="upload_id",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2},
    )
    # _, kwargs = mock_get_duplicate_within_db.call_args
    # assert kwargs.get('is_null_data') is False
    expected_fields = ["port_id=12", "network_provider=np1", "session_id=", "station_id=789"]
    assert result.get("errors")[0].get(
        "error_description"
    ) == ErrorReportMessages.DUPLICATE_RECORD_IN_SYSTEM.format(
        fields=expected_fields, upload_id="{'b2_submitted'}"
    )
    assert len(result.get("errors")) == 1


# JE-6837 handling non constraint nulls to not trigger null path
@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.get_duplicate_within_db")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
def test_unique_constraint_violations_for_M2_partial_null_duplicate_in_system(
    mock_database_central_config,
    mock_get_duplicate_within_db,
    mock_get_upload_metadata,
    config,
):
    async_df = pandas.DataFrame(
        data={
            "station_id": ["Josh_Test"],
            "port_id": ["1234"],
            "network_provider": ["7Charge"],
            "charger_id": ["87888"],
            "session_id": ["a99f8799"],
            "connector_id": [""],
            "session_start": [pandas.Timestamp("2024-07-03 12:59:48+0000", tz="UTC")],
            "session_end": [pandas.NaT],
            "session_error": ["error"],
            "error_other": [""],
            "energy_kwh": [322.99],
            "power_kw": [34.88],
            "payment_method": ["mastercard"],
            "payment_other": [""],
            "station_uuid": ["4e3981f8-9113-43ac-8f86-dffb9dbc66b3"],
        }
    )

    module_id = "2"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "2"}
    mock_database_central_config.return_value = config
    mock_get_duplicate_within_db.return_value = pandas.DataFrame(
        data={
            "upload_id": ["b2_submitted"],
            "station_uuid": ["789"],
            "station_id_upload": ["789"],
            "network_provider_upload": ["np1"],
            "port_id": ["12"],
            "session_id": ["1223"],
        }
    )
    result = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="upload_id",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_2, Feature.DATABASE_CENTRAL_CONFIG},
    )
    _, kwargs = mock_get_duplicate_within_db.call_args
    assert kwargs.get("is_null_data") is False
    expected_fields = ["port_id=12", "session_id=1223", "network_provider=np1", "station_id=789"]
    # "Duplicate rows found with these Primary Keys ['port_id=12', 'session_id=1223', 'network_provider=np1', 'station_id=789'] found in previous upload id {'b2_submitted'}. Delete duplicate rows."
    assert result.get("errors")[0].get(
        "error_description"
    ) == ErrorReportMessages.DUPLICATE_RECORD_IN_SYSTEM.format(
        fields=expected_fields, upload_id="{'b2_submitted'}"
    )
    assert len(result.get("errors")) == 1


# JE-6650 adding duplicate checks for null modules, specifically for module 9
@patch("module_validation.unique_constraint.execute_query_df")
@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
def test_unique_constraint_violations_for_M9_null_annual_duplicate_in_system(
    mock_database_central_config,
    mock_get_upload_metadata,
    mock_execute_query_df,
    config,
):
    filename = "valid_module_9_biz_magic.csv"
    async_df = get_df_from_sample_data_csv(filename)

    module_id = "9"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "5"}
    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": ["b2_submitted"],
            "station_uuid": ["789"],
            "station_id_upload": ["789"],
            "network_provider_upload": ["np1"],
        }
    )
    mock_database_central_config.return_value = config
    result = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="upload_id",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_9},
    )
    expected_fields = ["network_provider=np1", "station_id=789"]
    expected_conditions = [
        {
            "error_description": ErrorReportMessages.DUPLICATE_RECORD_IN_SYSTEM.format(
                fields=expected_fields, upload_id="{'b2_submitted'}"
            ),
            "header_name": "N/A",
            "error_row": None,
        }
    ]
    assert result.get("errors") == expected_conditions


# JE-6640 ensuring that invalid module data does not go through duplicate check process, no need to check
# there are duplicates in system if we are already working with bad data
@patch("module_validation.unique_constraint.get_duplicate_within_db")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
def test_unique_constraint_violations_for_M4_outage_id_missing_no_duplicate_errors(
    mock_database_central_config, mock_get_duplicate_within_db, config
):
    filename = "outage_id_empty_value_mod_4.csv"
    async_df = get_df_from_sample_data_csv(filename)

    module_id = "4"
    mock_database_central_config.return_value = config
    result = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="upload_id",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_4},
    )
    assert len(result.get("errors")) == 0


# JE-6650 adding duplicate checks for null modules, specifically for module 4
@patch("module_validation.unique_constraint.execute_query_df")
@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
def test_unique_constraint_violations_for_M4_null_duplicate_in_system(
    mock_database_central_config,
    mock_get_upload_metadata,
    mock_execute_query_df,
    config,
):
    filename = "valid_mod_4_null_with_empty_fields.csv"
    async_df = get_df_from_sample_data_csv(filename)

    module_id = "4"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "5"}
    mock_database_central_config.return_value = config

    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": ["upload_id_from_db"],
            "network_provider_upload": ["np"],
            "station_uuid": ["station_uuid"],
            "station_id_upload": ["station_id_upload"],
            "ouatge_duration": ["outage_duration"],
            "port_id": ["port_id"],
        }
    )
    result = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="upload_id",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_4},
    )
    expected_fields = [
        "port_id=port_id",
        "network_provider=np",
        "outage_id=",
        "station_id=station_id_upload",
    ]
    expected_errors = [
        {
            "error_description": ErrorReportMessages.DUPLICATE_RECORD_IN_SYSTEM.format(
                fields=expected_fields, upload_id="{'upload_id_from_db'}"
            ),
            "header_name": "N/A",
            "error_row": None,
        }
    ]
    assert result.get("errors") == expected_errors


# checks if "outage_id" constraint was removed from the query, and is properly set to "" before df is returned,
# and the key is added back to constraints
@patch("module_validation.unique_constraint.execute_query_df")
@patch("module_validation.unique_constraint.get_upload_metadata")
def test_get_duplicate_within_db_M4(mock_get_upload_metadata, mock_execute_query):
    filename = "valid_mod_4_null_with_empty_fields.csv"
    async_df = get_df_from_sample_data_csv(filename)
    module_id = "4"

    mock_get_upload_metadata.return_value = {"quarter": "1", "module_id": "4", "year": "2023"}
    # only returning 1 duplicate value from the system
    mock_execute_query.return_value = pandas.DataFrame(
        data={
            "upload_id": ["duplicate_non_null_upload_id"],
            "network_provider_upload": ["np"],
            "station_uuid": ["station_uuid"],
            "station_id_upload": ["station_id_upload"],
            "ouatge_duration": ["outage_duration"],
            "port_id": ["port_id"],
        }
    )
    expected_df = pandas.DataFrame(
        data={
            "upload_id": ["duplicate_non_null_upload_id"],
            "network_provider_upload": ["np"],
            "station_uuid": ["station_uuid"],
            "station_id_upload": ["station_id_upload"],
            "ouatge_duration": ["outage_duration"],
            "port_id": ["port_id"],
            "outage_id": [""],
        }
    )
    response = get_duplicate_within_db(
        async_df=async_df,
        cursor=MagicMock(),
        upload_id="upload_id",
        dr_id="dr_id",
        module_id=module_id,
        is_null_data=True,
        constraints=get_module_constraints_by_module_id(module_id),
    )
    assert response.equals(expected_df)


# makes sure constraints are not updated and what is returned from the db, is what is returned by the function
@patch("module_validation.unique_constraint.execute_query_df")
@patch("module_validation.unique_constraint.get_upload_metadata")
def test_get_duplicate_within_db_M9(mock_get_upload_metadata, mock_execute_query):
    filename = "all_required_module_9.csv"
    async_df = get_df_from_sample_data_csv(filename)
    module_id = "9"

    mock_get_upload_metadata.return_value = {"quarter": "1", "module_id": "9", "year": "2023"}
    # only returning 1 duplicate value from the system
    mock_execute_query.return_value = pandas.DataFrame(
        data={
            "upload_id": ["duplicate_non_null_upload_id"],
            "network_provider_upload": ["np"],
            "station_uuid": ["station_uuid"],
            "station_id_upload": ["station_id_upload"],
        }
    )
    expected_df = pandas.DataFrame(
        data={
            "upload_id": ["duplicate_non_null_upload_id"],
            "network_provider_upload": ["np"],
            "station_uuid": ["station_uuid"],
            "station_id_upload": ["station_id_upload"],
        }
    )
    response = get_duplicate_within_db(
        async_df=async_df,
        cursor=MagicMock(),
        upload_id="upload_id",
        dr_id="dr_id",
        module_id=module_id,
        is_null_data=True,
        constraints=get_module_constraints_by_module_id(module_id),
    )
    assert response.equals(expected_df)


# JE-6765 Used for debugging M5 when a recommended field is not present in df
@patch("module_validation.unique_constraint.get_upload_metadata")
@patch("module_validation.unique_constraint.DatabaseCentralConfig")
@patch("module_validation.unique_constraint.execute_query_df")
def test_unique_constraint_violations_for_async_bug(
    mock_execute_query_df, mock_database_central_config, mock_get_upload_metadata, config
):
    """
    test_unique_constraint_violations_for_s2s_given_dataframe_with_
    constraint_violation_return_list
    """
    filename = "all_mod_5_1001_rows.csv"
    # async_df = get_df_from_sample_data_csv(filename)
    async_df = pandas.DataFrame(
        data={
            "station_id": [
                "blueberry",
                "blueberry",
                "blueberry",
                "blueberry",
                "blueberry",
                "blueberry",
                "blueberry",
                "blueberry",
                "blueberry",
                "blueberry",
            ],
            "project_id": [
                "2eb02cd0-b182-4a0e-aa26-51e26b1605f1",
                "a13e46e1-b993-46c2-ba25-8f12c7d2f996",
                "b7713a0c-bd72-46eb-b462-c830b110ebc3",
                "f6e11230-3415-4a66-92b3-0118bd0311f7",
                "6e1107af-c75d-43ee-bae3-a6d01255d681",
                "35a38dc8-1892-4803-bd1a-30a14dd47e6e",
                "cf37594c-6a0a-4d9f-ac3d-a9b26634abf1",
                "00d40708-2ade-49c9-8f56-afac5f686fd3",
                "aa168a12-5e39-4c8f-8ba5-49227812c62d",
                "e0134efa-94d3-4453-8ef2-cc724649dc01",
            ],
            "maintenance_report_start": [
                None,
                pandas.Timestamp("2020-09-23 12:42:56+0000", tz="UTC"),
                pandas.Timestamp("2023-08-30 17:16:42+0000", tz="UTC"),
                pandas.Timestamp("2024-04-14 14:58:42+0000", tz="UTC"),
                pandas.Timestamp("2021-05-19 07:23:20+0000", tz="UTC"),
                pandas.Timestamp("2020-12-19 12:55:32+0000", tz="UTC"),
                pandas.Timestamp("2021-01-08 10:06:06+0000", tz="UTC"),
                pandas.Timestamp("2024-05-01 00:44:34+0000", tz="UTC"),
                pandas.Timestamp("2021-01-06 21:07:51+0000", tz="UTC"),
                pandas.Timestamp("2023-02-27 10:19:40+0000", tz="UTC"),
            ],
            "maintenance_report_end": [
                pandas.Timestamp("2024-03-04 04:13:29+0000", tz="UTC"),
                pandas.Timestamp("2020-10-16 12:42:56+0000", tz="UTC"),
                pandas.Timestamp("2023-09-27 17:16:42+0000", tz="UTC"),
                pandas.Timestamp("2024-04-30 14:58:42+0000", tz="UTC"),
                pandas.Timestamp("2021-06-07 07:23:20+0000", tz="UTC"),
                pandas.Timestamp("2021-01-13 12:55:32+0000", tz="UTC"),
                pandas.Timestamp("2021-01-18 10:06:06+0000", tz="UTC"),
                pandas.Timestamp("2024-05-15 00:44:34+0000", tz="UTC"),
                pandas.Timestamp("2021-02-04 21:07:51+0000", tz="UTC"),
                pandas.Timestamp("2023-03-16 10:19:40+0000", tz="UTC"),
            ],
            "caas": [None, None, True, None, None, False, False, None, True, False],
            "maintenance_cost_federal": [
                4302.01,
                372.61,
                3815.46,
                912.48,
                2774.39,
                874.56,
                4828.89,
                4261.7,
                4451.74,
                1663.81,
            ],
            "maintenance_cost_total": [
                4302.01,
                372.61,
                3815.46,
                912.48,
                2774.39,
                874.56,
                4828.89,
                4261.7,
                4451.74,
                1663.81,
            ],
            "network_provider_upload": [None, None, None, None, None, None, None, None, None, None],
            "station_uuid": [None, None, None, None, None, None, None, None, None, None],
        }
    )

    module_id = "5"
    mock_get_upload_metadata.return_value = {"year": "2024", "quarter": "", "module_id": "5"}
    mock_database_central_config.return_value = config
    # mocking out pretending there is already an existing duplicate in db
    mock_execute_query_df.return_value = pandas.DataFrame(
        data={
            "upload_id": ["b2_submitted"],
            "station_uuid": ["789"],
            "station_id_upload": ["789"],
            "network_provider_upload": ["np1"],
            "maintenance_report_start": [pandas.Timestamp("2020-09-23 12:42:56+0000")],
            "port_id": ["3"],
        }
    )

    response = unique_constraint_violations_for_async(
        cursor=MagicMock(),
        upload_id="a1_draft",
        dr_id="dr123",
        log_event=MagicMock(),
        df=async_df,
        module_id=module_id,
        feature_toggle_set={Feature.UNIQUE_CONSTRAINT_MODULE_5},
    )

    assert len(response.get("errors")) == 1
    assert response.get("df") is None
