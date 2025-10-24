import importlib
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import boto3
import pandas as pd
import pytest
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import (
    EvChartFeatureStoreConnectionError, EvChartFeatureToggleNotFoundError)
from evchart_helper.custom_logging import LogEvent
from feature_toggle.feature_enums import Feature
from InfraDBMigrations.index import (
    ExecutionAction, FeatureToggledScript, check_if_files_in_list_exist,
    convert_legacy_files_to_feature_toggled_script, get_execution_action,
    get_feature_toggle_dict, get_feature_toggle_file_list,
    get_feature_toggle_value, get_feature_toggled_script_list,
    get_legacy_files, reverse_backouts, run_feature_toggle_scripts)
from moto import mock_aws


@pytest.fixture
def fixture_ssm_base():
    with mock_aws():
        ssm = boto3.client("ssm")
        yield ssm


@pytest.fixture
def mock_boto3_manager_return_empty(fixture_ssm_base):
    with patch.object(Boto3Manager, "client", return_value=fixture_ssm_base) as mock_client:
        yield mock_client


@pytest.fixture
def fixture_ssm_return_12_flags(fixture_ssm_base):
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/features/db-feature-toggle", Value="True", Type="String"
    )
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature2", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature3", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature4", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature5", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature6", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature7", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature8", Value="False", Type="String")
    fixture_ssm_base.put_parameter(Name="/ev-chart/features/feature9", Value="False", Type="String")
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/features/feature10", Value="False", Type="String"
    )
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/features/feature11", Value="False", Type="String"
    )
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/features/feature12", Value="False", Type="String"
    )
    yield fixture_ssm_base


@pytest.fixture
def mock_boto3_manager_return_12_flags(fixture_ssm_return_12_flags):
    with patch.object(
        Boto3Manager, "client", return_value=fixture_ssm_return_12_flags
    ) as mock_client:
        yield mock_client


@pytest.fixture
def fixture_ssm_return_db_migrations_example_true(fixture_ssm_base):
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/features/db-migrations-feature-toggle-example", Value="True", Type="String"
    )
    yield fixture_ssm_base


@pytest.fixture
def mock_boto3_manager_return_db_migrations_example(fixture_ssm_return_db_migrations_example):
    with patch.object(
        Boto3Manager, "client", return_value=fixture_ssm_return_db_migrations_example
    ) as mock_client:
        yield mock_client


def test_get_feature_toggle_dict_throws_error_no_ssm():
    with pytest.raises(EvChartFeatureStoreConnectionError) as e:
        log = LogEvent({}, api="", action_type="READ")
        get_feature_toggle_dict(log)


def test_get_feature_toggle_dict_returns_empty_if_no_features(mock_boto3_manager_return_empty):
    log = LogEvent({}, api="", action_type="READ")
    feature_toggle_list = get_feature_toggle_dict(log)

    assert len(feature_toggle_list) == 0


def test_get_feature_toggle_dict_returns_dict_of_12_features(mock_boto3_manager_return_12_flags):
    log = LogEvent({}, api="", action_type="READ")
    feature_toggle_dict = get_feature_toggle_dict(log)

    db_feature_toggle = feature_toggle_dict["db-feature-toggle"]

    assert len(feature_toggle_dict) == 12
    assert db_feature_toggle is True


def test_check_if_files_in_list_exist_throws_error_if_file_not_exist():
    path_obj = Path(__file__).parent
    directory = os.path.join(path_obj, "test_migrations")
    file_name_list = ["garbage.sql"]

    with pytest.raises(FileNotFoundError) as e:
        check_if_files_in_list_exist(directory, file_name_list)

    assert file_name_list[0] in e.value.filename


def test_check_if_files_in_list_exist_does_nothing_if_all_files_exist():
    path_obj = Path(__file__).parent
    directory = os.path.join(path_obj, "test_migrations")
    file_name_list = ["test_create_table.sql"]
    check_if_files_in_list_exist(directory, file_name_list)
    assert True


def test_check_if_files_in_list_exist_does_nothing_if_given_empty_list():
    path_obj = Path(__file__).parent
    directory = os.path.join(path_obj, "test_migrations")
    file_name_list = []
    check_if_files_in_list_exist(directory, file_name_list)

    assert True


def test_listed_files_exist():
    file_name_list = get_legacy_files()
    feature_toggle_file_list = get_feature_toggle_file_list()
    for feature_toggle_file in feature_toggle_file_list:
        file_name_list.append(feature_toggle_file.file_name)
        if feature_toggle_file.backout_file_name:
            file_name_list.append(feature_toggle_file.backout_file_name)

    # Get files in migration directory
    module_name = "InfraDBMigrations.index"
    spec = importlib.util.find_spec(module_name)
    module_dir = os.path.dirname(spec.origin)
    migrations_dir = os.path.join(module_dir, "migrations")

    # Run check on list throws error if a file does not exist
    check_if_files_in_list_exist(migrations_dir, file_name_list)
    assert True


def test_convert_legacy_files_to_feature_toggled_script_given_empty_list_return_empty_list():
    legacy_list = []
    result = convert_legacy_files_to_feature_toggled_script(legacy_list)
    assert result == []


def test_convert_legacy_files_to_feature_toggled_script_given_none_return_empty_list():
    legacy_list = None
    result = convert_legacy_files_to_feature_toggled_script(legacy_list)
    assert result == []


def test_convert_legacy_files_to_feature_toggled_script_given_one_file_return_converted_file():
    legacy_list = ["a_file_name.sql"]
    result = convert_legacy_files_to_feature_toggled_script(legacy_list)
    assert len(result) == 1
    first_result = result[0]
    assert first_result.file_name == legacy_list[0]
    assert first_result.backout_file_name is None
    assert first_result.requires_backout is False


def test_convert_legacy_files_to_feature_toggled_script_given_multiple_file_return_same_number_of_files():
    legacy_list = ["file_1.sql", "file_2.sql", "file_3.sql"]
    result = convert_legacy_files_to_feature_toggled_script(legacy_list)
    assert len(result) == 3


@patch("InfraDBMigrations.index.get_legacy_files")
@patch("InfraDBMigrations.index.get_feature_toggle_file_list")
def test_get_feature_toggled_script_list_returns_converted_list_of_legacy_files(
    mock_get_feature_toggle_file_list, mock_legacy_file_list
):
    mock_legacy_file_list.return_value = ["test_create_table.sql"]
    mock_get_feature_toggle_file_list.return_value = [FeatureToggledScript("test_edit_column.sql")]

    result = get_feature_toggled_script_list()
    assert len(result) == 2
    result_files = []
    for toggle in result:
        result_files.append(toggle.file_name)
    assert "test_create_table.sql" in result_files
    assert "test_edit_column.sql" in result_files


def test_get_feature_toggle_value_given_no_toggle_return_true():
    file_name = "1234_db_feature_toggle_test.sql"
    feature_toggled_dict = {"db-migrations-feature-toggle-example": True}

    feature_toggled_script = FeatureToggledScript(file_name=file_name, feature_toggle=None)
    result = get_feature_toggle_value(feature_toggled_script, feature_toggled_dict)

    assert result is True


def test_get_feature_toggle_value_given_true_return_true():
    file_name = "1234_db_feature_toggle_test.sql"
    toggle = Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE
    feature_toggled_dict = {"db-migrations-feature-toggle-example": True}

    feature_toggled_script = FeatureToggledScript(file_name=file_name, feature_toggle=toggle)
    result = get_feature_toggle_value(feature_toggled_script, feature_toggled_dict)

    assert result is True


def test_get_feature_toggle_value_given_false_return_true():
    file_name = "1234_db_feature_toggle_test.sql"
    toggle = Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE
    feature_toggled_dict = {"db-migrations-feature-toggle-example": False}

    feature_toggled_script = FeatureToggledScript(file_name=file_name, feature_toggle=toggle)
    result = get_feature_toggle_value(feature_toggled_script, feature_toggled_dict)

    assert result is False


def test_get_feature_toggle_value_given_invalid_toggle_raise_error():
    file_name = "1234_db_feature_toggle_test.sql"
    toggle = Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE
    feature_toggle_name = toggle.value
    feature_toggled_dict = {"test": True}

    feature_toggled_script = FeatureToggledScript(file_name=file_name, feature_toggle=toggle)
    with pytest.raises(EvChartFeatureToggleNotFoundError) as raised_error:
        get_feature_toggle_value(feature_toggled_script, feature_toggled_dict)

    assert f"{feature_toggle_name}" in raised_error.value.message


@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
def test_run_feature_toggle_scripts_given_none_toggle_and_file_not_ran_run_script(
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    migrations = pd.DataFrame({"script_name": ["test1"], "executed_on": [datetime.now()]})
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        feature_toggle=None,
    )
    feature_toggle_scripts = [feature_toggle_script]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": True}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )
    executed_file_path = os.path.join(migration_directory, feature_toggle_script.file_name)
    mock_run_sql_file.assert_called_once_with(cursor, executed_file_path)
    assert mock_insert_into_migrations_table.called


@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
def test_run_feature_toggle_scripts_given_true_toggle_and_file_not_ran_run_script(
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    migrations = pd.DataFrame({"script_name": ["test1"], "executed_on": [datetime.now()]})
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
    )
    feature_toggle_scripts = [feature_toggle_script]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": True}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )
    executed_file_path = os.path.join(migration_directory, feature_toggle_script.file_name)
    mock_run_sql_file.assert_called_once_with(cursor, executed_file_path)
    assert mock_insert_into_migrations_table.called


@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
def test_run_feature_toggle_scripts_given_none_toggle_and_file_ran_dont_run_script(
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    migrations = pd.DataFrame(
        {
            "script_name": ["5014_DB_Migration_Feature_Toggle_Example.sql"],
            "executed_on": [datetime.now()],
        }
    )
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        feature_toggle=None,
    )
    feature_toggle_scripts = [feature_toggle_script]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": True}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )
    assert not mock_run_sql_file.called
    assert not mock_insert_into_migrations_table.called


@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
def test_run_feature_toggle_scripts_given_true_toggle_and_file_ran_dont_run_script(
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    migrations = pd.DataFrame(
        {
            "script_name": ["5014_DB_Migration_Feature_Toggle_Example.sql"],
            "executed_on": [datetime.now()],
        }
    )
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
    )
    feature_toggle_scripts = [feature_toggle_script]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": True}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )

    assert not mock_run_sql_file.called
    assert not mock_insert_into_migrations_table.called


@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
def test_run_feature_toggle_scripts_given_false_and_requires_backout_false_toggle_do_not_execute_script(
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    migrations = pd.DataFrame({"script_name": ["test.sql"], "executed_on": [datetime.now()]})
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
    )
    feature_toggle_scripts = [feature_toggle_script]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": False}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )

    assert not mock_run_sql_file.called
    assert not mock_insert_into_migrations_table.called


@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
def test_run_feature_toggle_scripts_given_false_and_requires_backout_true_and_file_not_ran_toggle_do_not_execute_script(
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    migrations = pd.DataFrame({"script_name": ["test.sql"], "executed_on": [datetime.now()]})
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
        backout_file_name="backout_test.sql",
        requires_backout=True,
    )
    feature_toggle_scripts = [feature_toggle_script]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": False}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )

    assert not mock_run_sql_file.called
    assert not mock_insert_into_migrations_table.called


@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
@patch("InfraDBMigrations.index.remove_from_migrations_table")
def test_run_feature_toggle_scripts_given_false_and_requires_backout_true_and_file_has_ran_toggle_execute_backout(
    mock_remove_from_migrations_table,
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    migrations = pd.DataFrame(
        {
            "script_name": ["5014_DB_Migration_Feature_Toggle_Example.sql"],
            "executed_on": [datetime.now()],
        }
    )
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
        backout_file_name="backout_test.sql",
        requires_backout=True,
    )
    feature_toggle_scripts = [feature_toggle_script]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": False}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )

    executed_file_path = os.path.join(migration_directory, feature_toggle_script.backout_file_name)
    mock_run_sql_file.assert_called_once_with(cursor, executed_file_path)
    mock_insert_into_migrations_table.assert_called_once_with(
        cursor, feature_toggle_script.backout_file_name
    )
    mock_remove_from_migrations_table.assert_called_once_with(
        cursor, feature_toggle_script.file_name
    )


@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
@patch("InfraDBMigrations.index.remove_from_migrations_table")
def test_run_feature_toggle_scripts_given_multiple_files_to_backout_execute_backout_reverse_of_original(
    mock_remove_from_migrations_table,
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    migrations = pd.DataFrame(
        {
            "script_name": [
                "5014_DB_Migration_Feature_Toggle_Example_1.sql",
                "5014_DB_Migration_Feature_Toggle_Example_2.sql",
            ],
            "executed_on": [
                datetime.now(),
                datetime.now()
            ],
        }
    )
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example_1.sql",
        feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
        backout_file_name="backout_test_1.sql",
        requires_backout=True,
    )
    feature_toggle_script_2 = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example_2.sql",
        feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
        backout_file_name="backout_test_2.sql",
        requires_backout=True,
    )
    feature_toggle_scripts = [feature_toggle_script, feature_toggle_script_2]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": False}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )

    executed_file_path_1 = os.path.join(
        migration_directory, feature_toggle_script.backout_file_name
    )
    executed_file_path_2 = os.path.join(
        migration_directory, feature_toggle_script_2.backout_file_name
    )
    expected_calls = [call(cursor, executed_file_path_2), call(cursor, executed_file_path_1)]

    mock_run_sql_file.assert_has_calls(expected_calls)


# Should we always run backouts first?
# realistically the backout files could be mixed in with toggles that are just getting turned on.
# the smaller the team the lower the risk and hopefully the toggles do not touch the same columns or keys


def test_reverse_backouts_given_mix_of_backouts_and_normal():
    script_data_collection = [
        {
            "file_name": "1",
            "execution_action": ExecutionAction.BACKOUT,
            "file_to_remove": None
        },
        {
            "file_name": "2",
            "execution_action": ExecutionAction.EXECUTE,
            "file_to_remove": None
        },
        {
            "file_name": "3",
            "execution_action": ExecutionAction.BACKOUT,
            "file_to_remove": None
        },
        {
            "file_name": "4",
            "execution_action": ExecutionAction.EXECUTE,
            "file_to_remove": None
        },
    ]
    reversed_collection = reverse_backouts(script_data_collection)
    assert reversed_collection[0].get("file_name") == "3"
    assert reversed_collection[1].get("file_name") == "1"
    assert reversed_collection[2].get("file_name") == "2"
    assert reversed_collection[3].get("file_name") == "4"

def test_reverse_backouts_given_only_backouts():
    script_data_collection = [
        {
            "file_name": "1",
            "execution_action": ExecutionAction.BACKOUT,
            "file_to_remove": None
        },
        {
            "file_name": "2",
            "execution_action": ExecutionAction.BACKOUT,
            "file_to_remove": None
        },
        {
            "file_name": "3",
            "execution_action": ExecutionAction.BACKOUT,
            "file_to_remove": None
        },
        {
            "file_name": "4",
            "execution_action": ExecutionAction.BACKOUT,
            "file_to_remove": None
        },
    ]
    reversed_collection = reverse_backouts(script_data_collection)
    assert reversed_collection[0].get("file_name") == "4"
    assert reversed_collection[1].get("file_name") == "3"
    assert reversed_collection[2].get("file_name") == "2"
    assert reversed_collection[3].get("file_name") == "1"

def test_reverse_backouts_given_only_normal():
    script_data_collection = [
        {
            "file_name": "1",
            "execution_action": ExecutionAction.EXECUTE,
            "file_to_remove": None
        },
        {
            "file_name": "2",
            "execution_action": ExecutionAction.EXECUTE,
            "file_to_remove": None
        },
        {
            "file_name": "3",
            "execution_action": ExecutionAction.EXECUTE,
            "file_to_remove": None
        },
        {
            "file_name": "4",
            "execution_action": ExecutionAction.EXECUTE,
            "file_to_remove": None
        },
    ]
    reversed_collection = reverse_backouts(script_data_collection)
    assert reversed_collection[0].get("file_name") == "1"
    assert reversed_collection[1].get("file_name") == "2"
    assert reversed_collection[2].get("file_name") == "3"
    assert reversed_collection[3].get("file_name") == "4"

def test_reverse_backouts_given_empty_list():
    reversed_collection = reverse_backouts([])
    assert not reversed_collection

@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
@patch("InfraDBMigrations.index.remove_from_migrations_table")
def test_run_feature_toggle_scripts_given_backout_has_ran_and_would_otherwise_run_backout_do_not_execute(
    mock_remove_from_migrations_table,
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    backout_file = "backout_test.sql"
    migrations = pd.DataFrame({"script_name": [backout_file], "executed_on": [datetime.now()]})
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
        backout_file_name=backout_file,
        requires_backout=True,
    )
    feature_toggle_scripts = [feature_toggle_script]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": False}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )

    assert not mock_run_sql_file.called
    assert not mock_insert_into_migrations_table.called
    assert not mock_remove_from_migrations_table.called


@patch("InfraDBMigrations.index.run_sql_file")
@patch("InfraDBMigrations.index.insert_into_migrations_table")
@patch("InfraDBMigrations.index.remove_from_migrations_table")
def test_run_feature_toggle_scripts_given_backout_has_ran_and_toggle_flipped_true_execute_file_remove_backout(
    mock_remove_from_migrations_table,
    mock_insert_into_migrations_table,
    mock_run_sql_file,
):
    path_obj = Path(__file__).parent
    migration_directory = os.path.join(path_obj, "test_migrations")
    connection = MagicMock()
    cursor = MagicMock()
    connection.cursor.return_value.__enter__.return_value = cursor
    backout_file = "backout_test.sql"
    migrations = pd.DataFrame({"script_name": [backout_file], "executed_on": [datetime.now()]})
    feature_toggle_script = FeatureToggledScript(
        file_name="5014_DB_Migration_Feature_Toggle_Example.sql",
        feature_toggle=Feature.DB_MIGRATIONS_FEATURE_TOGGLE_EXAMPLE,
        backout_file_name=backout_file,
        requires_backout=True,
    )
    feature_toggle_scripts = [feature_toggle_script]
    feature_toggled_dict = {"db-migrations-feature-toggle-example": True}

    run_feature_toggle_scripts(
        migration_directory, connection, migrations, feature_toggle_scripts, feature_toggled_dict
    )

    executed_file_path = os.path.join(migration_directory, feature_toggle_script.file_name)
    mock_run_sql_file.assert_called_once_with(cursor, executed_file_path)
    mock_insert_into_migrations_table.assert_called_once_with(
        cursor, feature_toggle_script.file_name
    )
    mock_remove_from_migrations_table.assert_called_once_with(
        cursor, feature_toggle_script.backout_file_name
    )


@pytest.mark.parametrize(
    "toggle_value,backout_enabled,original_executed,backout_executed,expected_result",
    [
        (True, False, False, False, ExecutionAction.EXECUTE),
        (True, True, False, False, ExecutionAction.EXECUTE),
        (True, True, True, False, ExecutionAction.SKIP),
        (True, True, True, True, ExecutionAction.SKIP),  # unlikely to happen
        (True, True, False, True, ExecutionAction.EXECUTE),
        (True, False, True, False, ExecutionAction.SKIP),
        (False, False, False, False, ExecutionAction.SKIP),
        (False, False, True, False, ExecutionAction.SKIP),
        (False, False, False, True, ExecutionAction.SKIP),
        (False, True, False, False, ExecutionAction.SKIP),
        (False, True, True, False, ExecutionAction.BACKOUT),
        (False, True, False, True, ExecutionAction.SKIP),
        (False, True, True, True, ExecutionAction.SKIP),  # unlikely to happen
    ],
)
def test_get_execution_action_given_inputs_gets_action(
    toggle_value, backout_enabled, original_executed, backout_executed, expected_result
):
    result = get_execution_action(
        toggle_value, backout_enabled, original_executed, backout_executed
    )
    assert result == expected_result
