import os
from unittest.mock import patch

from database_central_config import DatabaseCentralConfig
from ScheduledDatabaseDriftDetection.index import (
    handler as scheduled_database_drift_detection,
    compare_tables
)

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
            "database_central_config.json"
        )
    )


# JE-5965
# 1. Report any tables that are defined in central config
#    but do not exist in database
def test_no_tables(config):
    response = compare_tables([], [], config)
    not_in_database = [
        r for r in response
        if r.get('error_description') == "Table does not exist in database"
    ]
    assert len(not_in_database) > 0


# JE-5965
# 2. Report any tables that exist in database
#    but are not defined in central config
def test_extra_tables(config):
    bogus_aurora_response = [{
        'TABLE_NAME': 'some_bogus_table',
        'COLUMN_NAME': 'some_bogus_column'
    }]
    response = compare_tables(bogus_aurora_response, [], config)
    not_in_config = [
        r for r in response
        if r.get('error_description') == "Table does not exist in config"
    ]
    assert len(not_in_config) == 1
    assert not_in_config[0]['table_name'] == 'some_bogus_table'


# JE-5965
# 3. For each table defined in central config, report any fields that are
#    defined in central config but do not exist in table
def test_missing_in_database(config):
    bogus_aurora_response = [{
        'TABLE_NAME': 'migration',
        'COLUMN_NAME': 'executed_on'
    }]
    response = compare_tables(bogus_aurora_response, [], config)
    not_in_aurora = [
        r for r in response
        if r.get('error_description') == "Column does not exist in database"
    ]
    assert len(not_in_aurora) == 1
    assert not_in_aurora[0]['table_name'] == 'migration'
    assert not_in_aurora[0]['column_name'] == 'script_name'


# JE-5965
# 4. For each table defined in central config, report any fields that exist
#    in table but are not defined in central config
def test_missing_in_config(config):
    bogus_aurora_response = [{
        'TABLE_NAME': 'import_metadata',
        'COLUMN_NAME': 'some_bogus_column'
    }]
    response = compare_tables(bogus_aurora_response, [], config)
    not_in_aurora = [
        r for r in response
        if r.get('error_description') == "Column does not exist in config"
    ]
    assert len(not_in_aurora) == 1
    assert not_in_aurora[0]['table_name'] == 'import_metadata'
    assert not_in_aurora[0]['column_name'] == 'some_bogus_column'


# JE-5965
# 5. For each table defined in central config, report any differences
#    between defined vs. actual field attributes:
#    COLUMN_DEFAULT, IS_NULLABLE, COLUMN_TYPE, COLUMN_KEY
def test_table_definition_match(config):
    bogus_aurora_response = [
        {
            'TABLE_NAME': 'migration',
            'COLUMN_NAME': 'executed_on',
            'COLUMN_DEFAULT': 'CURRENT_TIMESTAMP',
            'IS_NULLABLE': 'YES',
            'COLUMN_TYPE': 'datetime',
            'COLUMN_KEY': ""
        },
        {
            'TABLE_NAME': 'migration',
            'COLUMN_NAME': 'script_name',
            'COLUMN_DEFAULT': None,
            'IS_NULLABLE': 'NO',
            'COLUMN_TYPE': 'varchar(100)',
            'COLUMN_KEY': "PRI"
        }
    ]

    response = compare_tables(bogus_aurora_response, [], config)
    migration_table_errors = [
        r for r in response
        if r.get('table_name') == "migration"
    ]
    assert migration_table_errors == []


def test_table_definition_mismatch(config):
    bogus_aurora_response = [
        {
            'TABLE_NAME': 'migration',
            'COLUMN_NAME': 'executed_on',
            'COLUMN_DEFAULT': 'CURRENT_TIMESTAMP',
            'IS_NULLABLE': 'YES',
            'COLUMN_TYPE': 'datetime',
            'COLUMN_KEY': ""
        },
        {
            'TABLE_NAME': 'migration',
            'COLUMN_NAME': 'script_name',
            'COLUMN_DEFAULT': None,
            'IS_NULLABLE': 'NO',
            'COLUMN_TYPE': 'varchar(72)',
            'COLUMN_KEY': "PRI"
        }
    ]

    response = compare_tables(bogus_aurora_response, [], config)
    migration_table_errors = [
        r for r in response
        if r.get('table_name') == "migration"
    ]
    assert len(migration_table_errors) == 1
    assert migration_table_errors[0]['table_name'] == 'migration'
    assert migration_table_errors[0]['column_name'] == 'script_name'


# code coverage
def test_response_500():
    response = scheduled_database_drift_detection({}, None)
    assert response.get('statusCode') == 500


@patch("ScheduledDatabaseDriftDetection.index.DatabaseCentralConfig")
@patch("ScheduledDatabaseDriftDetection.index.get_evchart_foreign_keys_from_aurora")
@patch("ScheduledDatabaseDriftDetection.index.get_evchart_config_from_aurora")
@patch("ScheduledDatabaseDriftDetection.index.compare_tables")
@patch("ScheduledDatabaseDriftDetection.index.aurora")
def test_response_200(
    mock_aurora,
    mock_compare_tables,
    mock_get_evchart_config_from_aurora,
    mock_get_evchart_foreign_keys_from_aurora,
    mock_database_central_config
):
    mock_compare_tables.return_value = []
    response = scheduled_database_drift_detection({}, None)
    assert response.get('statusCode') == 200
    assert mock_aurora.get_connection.called
    assert mock_get_evchart_config_from_aurora.called
    assert mock_get_evchart_foreign_keys_from_aurora.called
    assert mock_database_central_config.called


@patch("ScheduledDatabaseDriftDetection.index.DatabaseCentralConfig")
@patch("ScheduledDatabaseDriftDetection.index.get_evchart_foreign_keys_from_aurora")
@patch("ScheduledDatabaseDriftDetection.index.get_evchart_config_from_aurora")
@patch("ScheduledDatabaseDriftDetection.index.compare_tables")
@patch("ScheduledDatabaseDriftDetection.index.aurora")
def test_response_500_drift_detected(
    mock_aurora,
    mock_compare_tables,
    mock_get_evchart_config_from_aurora,
    mock_get_evchart_foreign_keys_from_aurora,
    mock_database_central_config
):
    mock_compare_tables.return_value = [
        {
            "error_description": "Column does not exist in config",
            "table_name": "some_bogus_table",
            "column_name": "some_bogus_column"
        }
    ]
    response = scheduled_database_drift_detection({}, None)
    assert response.get('statusCode') == 500
    assert response.get('body') == '{"message": "Drift detected"}'
    assert mock_aurora.get_connection.called
    assert mock_get_evchart_config_from_aurora.called
    assert mock_get_evchart_foreign_keys_from_aurora.called
    assert mock_database_central_config.called


@patch("ScheduledDatabaseDriftDetection.index.get_evchart_config_from_aurora")
@patch("ScheduledDatabaseDriftDetection.index.aurora")
def test_exception_outside_evchart(
    mock_aurora,
    mock_get_evchart_config_from_aurora
):
    mock_get_evchart_config_from_aurora.side_effect = ZeroDivisionError
    with pytest.raises(AttributeError):
        scheduled_database_drift_detection({}, None)
    assert mock_aurora.get_connection.called
