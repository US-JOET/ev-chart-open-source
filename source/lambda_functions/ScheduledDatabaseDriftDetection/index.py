"""
ScheduledDatabaseDriftDetection

A function that runs on a schedule that will determine if the MySQL database schema has drifted from
what has been defined in the DatabaseCentralConfig.
"""
import json
import logging
from collections import defaultdict

from database_central_config import DatabaseCentralConfig
from evchart_helper import aurora
from evchart_helper.api_helper import execute_query
from evchart_helper.custom_exceptions import (
    EvChartDatabaseHandlerConnectionError,
    EvChartDatabaseIntegrityError
)
from evchart_helper.custom_logging import LogEvent

from pymysql.err import Error
from botocore.exceptions import BotoCoreError


logger = logging.getLogger("ScheduledDatabaseDriftDetection")
logger.setLevel(logging.DEBUG)


def compare_schema(
    table_name: str,
    column_name: str,
    aurora_schema: dict,
    config_schema: dict
) -> list:
    return [
        {
            'table_name': table_name,
            'column_name': column_name,
            'error_description': (
                f"Value from aurora [{aurora_schema.get(column)}] does not "
                "match value from central config"
                f" [{config_schema.get(column)}]"
            )
        }
        for column in [
            'rds_column_default',
            'rds_is_nullable',
            'rds_column_type',
            'rds_column_key',
            'reference'
        ]
        if aurora_schema.get(column) != config_schema.get(column)
    ]


def compare_columns(
    table_name: str, aurora_table: dict, config_table: dict
) -> list:
    conditions = []

    aurora_column_names = set(aurora_table.keys())
    config_column_names = set(config_table.keys())

    aurora_column_names_only = aurora_column_names - config_column_names
    config_column_names_only = config_column_names - aurora_column_names
    joint_column_names = aurora_column_names & config_column_names

    conditions.extend([
        {
            'table_name': table_name,
            'column_name': column_name,
            'error_description': "Column does not exist in database"
        }
        for column_name in config_column_names_only
    ])
    conditions.extend([
        {
            'table_name': table_name,
            'column_name': column_name,
            'error_description': "Column does not exist in config"
        }
        for column_name in aurora_column_names_only
    ])
    for column_name in joint_column_names:
        conditions.extend(
            compare_schema(
                table_name=table_name,
                column_name=column_name,
                aurora_schema=aurora_table[column_name],
                config_schema=config_table[column_name]
            )
        )

    return conditions


def compare_tables(aurora_response: list, foreign_keys: list, config_data: dict) -> list:
    conditions = []
    aurora_data = defaultdict(dict)

    for row in aurora_response:
        aurora_data[row['TABLE_NAME']][row['COLUMN_NAME']] = {
            'rds_column_default': row.get('COLUMN_DEFAULT'),
            'rds_is_nullable': row.get('IS_NULLABLE'),
            'rds_column_type': row.get('COLUMN_TYPE'),
            'rds_column_key': row.get('COLUMN_KEY')
        }

        for constraint in foreign_keys:
            if (
                row['TABLE_NAME'] == constraint['TABLE_NAME']
                and row['COLUMN_NAME'] == constraint['COLUMN_NAME']
            ):
                aurora_data[row['TABLE_NAME']][row['COLUMN_NAME']] |= {
                    "reference": {
                        constraint['REFERENCED_TABLE_NAME']: constraint['REFERENCED_COLUMN_NAME']
                    }
                }

    aurora_table_names = set(aurora_data.keys())
    config_table_names = set(config_data.keys())

    aurora_table_names_only = aurora_table_names - config_table_names
    config_table_names_only = config_table_names - aurora_table_names
    joint_table_names = aurora_table_names & config_table_names

    conditions.extend([
        {
            'table_name': table_name,
            'error_description': "Table does not exist in database"
        }
        for table_name in config_table_names_only
    ])
    conditions.extend([
        {
            'table_name': table_name,
            'error_description': "Table does not exist in config"
        }
        for table_name in aurora_table_names_only
    ])
    for table_name in joint_table_names:
        conditions.extend(
            compare_columns(
                table_name=table_name,
                aurora_table=aurora_data[table_name],
                config_table=config_data[table_name]['schema']
            )
        )

    return conditions


def get_evchart_config_from_aurora(cursor):
    return execute_query(
        query=(
            "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_DEFAULT, IS_NULLABLE, "
            "       COLUMN_TYPE, COLUMN_KEY "
            "  FROM information_schema.columns "
            " WHERE table_schema=%s"
        ),
        data=("evchart_data_v3",),
        cursor=cursor
    )


def get_evchart_foreign_keys_from_aurora(cursor):
    return execute_query(
        query=("""
            SELECT kcu.TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                FROM information_schema.KEY_COLUMN_USAGE AS kcu
                JOIN information_schema.TABLE_CONSTRAINTS AS tc USING (CONSTRAINT_NAME)
                WHERE kcu.TABLE_SCHEMA = %s
                AND tc.CONSTRAINT_TYPE = 'FOREIGN KEY';
        """),
        data=("evchart_data_v3",),
        cursor=cursor
    )


def handler(event, _context):
    log_event = LogEvent(
        event=event, api="ScheduledDatabaseDriftDetection", action_type="read"
    )

    try:
        connection = aurora.get_connection()
    except (Error, BotoCoreError):
        return EvChartDatabaseHandlerConnectionError().get_error_obj()
    except Exception as e:
        logger.debug("non-database error encountered: %s", repr(e))
        raise

    with connection.cursor() as cursor:
        try:
            aurora_config = get_evchart_config_from_aurora(cursor)
            foreign_keys = get_evchart_foreign_keys_from_aurora(cursor)
        except Exception as e:  # pylint: disable=broad-exception-caught
            try:
                # pylint: disable=no-member
                # (asking for forgiveness not permission)
                log_event.log_custom_exception(
                    message=e.message,
                    status_code=e.status_code,
                    log_level=e.log_level
                )
                return e.get_error_obj()
            except Exception as ex:
                logger.debug(
                    "error encountered outside of Ev-ChART: %s",
                    repr(ex)
                )
                raise

    conditions = compare_tables(aurora_config, foreign_keys, DatabaseCentralConfig())
    if len(conditions) == 0:
        log_event.log_successful_request(
            message="No drift detected",
            status_code=200
        )
        return {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"message": "No drift detected"})
        }

    log_conditions = [
        EvChartDatabaseIntegrityError(log_event, json.dumps(condition))
        for condition in conditions
    ]

    response_payload = log_conditions[0].get_error_obj()
    response_payload['body'] = json.dumps({"message": "Drift detected"})
    return response_payload
