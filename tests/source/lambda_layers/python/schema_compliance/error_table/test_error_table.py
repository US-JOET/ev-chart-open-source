import json
from unittest.mock import patch, MagicMock
from moto import mock_aws
import boto3
import pytest
import pandas
from schema_compliance.error_table import (
    error_table_insert,
    set_record,
    set_station_id,
    set_org_ids
)
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import EvChartDatabaseDynamoQueryError, EvChartJsonOutputError


# creating users table fixture
@pytest.fixture(name="_dynamodb_base")
def fixture_dynamodb_base():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[{"AttributeName": "org_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "org_id", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        yield dynamodb


@pytest.fixture(name="mock_boto3_manager")
def fixture_mock_boto3_manager(_dynamodb_base):
    with patch.object(
        Boto3Manager, 'resource', return_value=_dynamodb_base
    ) as mock_client:
        yield mock_client


# adding a DR and SR into the table
@pytest.fixture(name="_dynamodb_org_table")
def fixture_dynamodb_org_table(_dynamodb_base):
    table = _dynamodb_base.Table("ev-chart_org")
    table.put_item(
        Item={
            "org_id": "1212",
            "name": "New York DOT",
            "recipient_type": "direct-recipient",
            "org_friendly_id": "2"
        }
    )

    table.put_item(
        Item={
            "org_id": "123456",
            "name": "Sparkflow",
            "recipient_type": "sub-recipient",
            "org_friendly_id": "5"
        }
    )

    yield _dynamodb_base


df = pandas.DataFrame(data={
        'station_id': ['friendly station id 1', 'friendly station id 2'],
        'name': ['Sophia', 'Sarah']
    })

log = MagicMock()
cursor = MagicMock()


def test_set_record_valid():
    condition_obj = {"error_row": 0}
    expected_res = {
        "station_id": "friendly station id 1",
        "name": "Sophia"
    }
    response = set_record(
        query_data={}, condition_obj=condition_obj, df=df
    )
    assert json.loads(response.get('record')) == expected_res


def test_set_station_id():
    condition_obj = {"error_row": 1}
    expected_res = {
        "station_id": "friendly station id 2"
    }
    response = set_station_id(
        query_data={}, condition=condition_obj, df=df
    )
    assert response == expected_res


def test_set_org_ids_for_dr(
    mock_boto3_manager, _dynamodb_base, _dynamodb_org_table
):
    response = set_org_ids(query_data={}, org_id="1212")
    assert response["dr_org_friendly_id"] == "2"
    assert response["sr_org_friendly_id"] is None
    assert mock_boto3_manager.called


@patch('evchart_helper.api_helper.execute_query')
def test_valid_error_table_insert_row_level_dr(
    mock_insert_query, mock_boto3_manager, _dynamodb_base, _dynamodb_org_table
):
    # setting params
    condition_list = [{
        "error_row": 0,
        "error_description": "invalid datatype",
        "header_name": "charging time"
    }]

    # setting mocked return values
    mock_insert_query.return_value = None
    cursor.rowcount = 1

    response = error_table_insert(
        cursor=cursor,
        upload_id="123",
        module_id="6",
        org_id="1212",
        dr_id="1212",
        condition_list=condition_list,
        df=df
    )
    assert response is True


@patch('evchart_helper.api_helper.execute_query')
def test_valid_error_table_insert_row_level_sr(
    mock_insert_query, mock_boto3_manager, _dynamodb_base, _dynamodb_org_table
):
    # setting params
    condition_list = [{
        "error_row": 0,
        "error_description": "invalid datatype",
        "header_name": "charging time"
    }]

    # setting mocked return values
    mock_insert_query.return_value = None
    cursor.rowcount = 1

    response = error_table_insert(
        cursor=cursor,
        upload_id="123",
        module_id="6",
        org_id="123456",
        dr_id="1212",
        condition_list=condition_list, df=df
    )
    assert response is True


@patch('evchart_helper.api_helper.execute_query')
def test_valid_error_table_insert_col_level(
    mock_insert_query, mock_boto3_manager, _dynamodb_base, _dynamodb_org_table
):
    # setting params
    condition_list = [{
        "error_row": None,
        "error_description": "missing column",
        "header_name": "charging time"
    }]

    # setting mocked return values
    mock_insert_query.return_value = None
    cursor.rowcount = 1

    response = error_table_insert(
        cursor=cursor,
        upload_id="123",
        module_id="6",
        org_id="1212",
        dr_id="1212",
        condition_list=condition_list,
        df=df
    )
    assert response is True


@patch('evchart_helper.api_helper.execute_query')
@patch('schema_compliance.error_table.set_record')
def test_error_table_insert_error_400(mock_set_record, mock_insert_query):
    # setting params
    condition_list = [{
        "error_row": 0,
        "error_description": "missing column",
        "header_name": "charging time"
    }]
    # setting mocked return values
    cursor.rowcount = 1
    mock_set_record.side_effect = EvChartJsonOutputError(log)
    mock_insert_query.return_value = None

    # TODO: kenmacf's local testing raises EvChartDatabaseDynamoQueryError,
    #       but pipeline raises EvChartJsonOutputError.  catch either until
    #       discrepancy is found
    with pytest.raises(
        (EvChartJsonOutputError, EvChartDatabaseDynamoQueryError)
    ):
        error_table_insert(
            cursor=cursor,
            upload_id="123",
            module_id="6",
            org_id="123",
            dr_id="1212",
            condition_list=condition_list,
            df=df
        )
