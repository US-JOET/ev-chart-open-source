from datetime import date
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from pymysql.err import IntegrityError, ProgrammingError
from pymysql.constants.ER import DUP_ENTRY, BAD_NULL_ERROR, PARSE_ERROR
from evchart_helper.custom_exceptions import (
    EvChartMissingOrMalformedHeadersError,
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartDatabaseAuroraQueryError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.api_helper import (
    get_available_years,
    get_headers,
    get_station_and_port_uuid,
    get_station_uuid,
    execute_query,
    query_builder_station_uuid,
    get_orgs_by_recipient_type_dynamo
)

from moto import mock_aws
import boto3
from evchart_helper.boto3_manager import Boto3Manager



# creating org table fixture
@pytest.fixture(name="dynamodb_org")
def fixture_dynamodb_org():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[
                {"AttributeName": "org_id", "KeyType": "HASH"},
                {"AttributeName": "recipient_type", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "org_id", "AttributeType": "S"},
                {"AttributeName": "recipient_type", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi_recipient_type",
                    "KeySchema": [
                        {"AttributeName": "recipient_type", "KeyType": "HASH"}
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()

        # inserting Maine DR
        table.put_item(
            Item={
                "org_id": "1",
                "name": "Maine DOT",
                "recipient_type": "direct-recipient",
                "org_friendly_id": "1",
            }
        )

        # inserting NY DR
        table.put_item(
            Item={
                "org_id": "2",
                "name": "NY DOT",
                "recipient_type": "direct-recipient",
                "org_friendly_id": "2",
            }
        )

        # inserting Sparkflow SR
        table.put_item(
            Item={
                "org_id": "3",
                "name": "Sparkflow",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "3",
            }
        )

        # inserting Spark08 SR
        table.put_item(
            Item={
                "org_id": "4",
                "name": "Spark08",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "4",
            }
        )

        yield dynamodb


@pytest.fixture(name="mock_boto3_manager")
def fixture_mock_boto3_manager(dynamodb_org):
    with patch.object(
        Boto3Manager, "resource", return_value=dynamodb_org
    ) as mock_client:
        yield mock_client


def cursor():
    return MagicMock()


def log():
    return MagicMock()


def get_valid_event():
    return {
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
                    "org_name": "Pennsylvania DOT",
                    "email": "sarah.biely@ee.doe.gov",
                    "scope": "direct-recipient",
                    "preferred_name": "Sarah Biely",
                }
            },
        },
        "headers": {"upload_id": "123", "status": "draft"},
    }


def get_event_incomplete_headers():
    return {
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {"email": "sarah.biely@ee.doe.gov", "preferred_name": "Sarah Biely"}
            },
        },
        "headers": {"upload_id": "123"},
    }


def test_get_headers_valid():
    test_log = LogEvent(get_valid_event(), "Test", "test")
    target_headers = ["upload_id", "status"]
    expected = {"upload_id": "123", "status": "draft"}
    headers = get_headers(test_log, get_valid_event(), target_headers)
    assert headers == expected


def test_get_headers_incomplete_headers():
    test_log = LogEvent(get_valid_event(), "Test", "test")
    target_headers = ["upload_id", "status"]
    with pytest.raises(EvChartMissingOrMalformedHeadersError):
        get_headers(test_log, get_event_incomplete_headers(), target_headers)


def test_get_station_uuid_valid():
    # set params
    station_id = "friendly id"
    expected_uuid = "1010"

    # create mock cursor oject and set return value of cursor
    mock_cursor = cursor()
    mock_cursor.fetchone.return_value = [expected_uuid]

    response = get_station_uuid(mock_cursor, station_id, None)
    assert response == expected_uuid


def test_get_station_uuid_invalid_no_station():
    # set params
    station_id = "friendly id"
    expected_uuid = None

    # create mock cursor oject and set return value of cursor
    mock_cursor = cursor()
    mock_cursor.fetchone.return_value = []

    response = get_station_uuid(mock_cursor, station_id, None)
    assert response == expected_uuid


@patch("evchart_helper.api_helper.execute_query_df")
def test_get_station_and_port_uuid_given_no_matching_station(mock_query):
    station_id = "friendly id"
    port_id = "port 1"
    network_provider = "my network"
    expected_result = pd.DataFrame(
        columns=["station_uuid", "network_provider_uuid", "port_uuid", "port_id"]
    )

    mock_query.return_value = expected_result

    with pytest.raises(EvChartDatabaseAuroraQueryError) as e:
        get_station_and_port_uuid(cursor, station_id, network_provider, port_id)

    assert e


@patch("evchart_helper.api_helper.execute_query_df")
def test_get_station_and_port_uuid_given_matching_port_found(mock_query):
    station_id = "friendly id"
    port_id = "port 1"
    network_provider = "my network"
    expected_station_uuid = "0"
    expected_network_uuid = "1"
    expected_port_uuid = "3"
    expected_data = {
        "station_uuid": [expected_station_uuid],
        "network_provider_uuid": [expected_network_uuid],
        "port_uuid": [expected_port_uuid],
        "port_id": [port_id],
    }
    expected_result = pd.DataFrame(expected_data)

    mock_query.return_value = expected_result

    response = get_station_and_port_uuid(cursor, station_id, network_provider, port_id)

    assert response["station_uuid"] == expected_station_uuid
    assert response["network_provider_uuid"] == expected_network_uuid
    assert response["port_uuid"] == expected_port_uuid
    assert response["port_id"] == port_id

@patch("evchart_helper.api_helper.execute_query_df")
def test_get_station_and_port_uuid_given_multiple_ports_found_with_matching(mock_query):
    station_id = "friendly id"
    port_id = "port 1"
    network_provider = "my network"
    expected_station_uuid = "0"
    expected_network_uuid = "1"
    expected_port_uuid = "3"
    expected_data = {
        "station_uuid": [expected_station_uuid, expected_station_uuid],
        "network_provider_uuid": [expected_network_uuid, expected_network_uuid],
        "port_uuid": ['other_uuid', expected_port_uuid],
        "port_id": ['other_id',port_id],
    }
    expected_result = pd.DataFrame(expected_data)

    mock_query.return_value = expected_result

    response = get_station_and_port_uuid(cursor, station_id, network_provider, port_id)

    assert response["station_uuid"] == expected_station_uuid
    assert response["network_provider_uuid"] == expected_network_uuid
    assert response["port_uuid"] == expected_port_uuid
    assert response["port_id"] == port_id

@patch("evchart_helper.api_helper.execute_query_df")
def test_get_station_and_port_uuid_given_multiple_ports_found_without_matching(mock_query):
    station_id = "friendly id"
    port_id = "port 1"
    network_provider = "my network"
    expected_station_uuid = "0"
    expected_network_uuid = "1"
    expected_port_uuid = None
    expected_data = {
        "station_uuid": [expected_station_uuid, expected_station_uuid],
        "network_provider_uuid": [expected_network_uuid, expected_network_uuid],
        "port_uuid": ['other_uuid', 'second_port_uuid'],
        "port_id": ['other_id','second_port_id'],
    }
    expected_result = pd.DataFrame(expected_data)

    mock_query.return_value = expected_result

    response = get_station_and_port_uuid(cursor, station_id, network_provider, port_id)

    assert response["station_uuid"] == expected_station_uuid
    assert response["network_provider_uuid"] == expected_network_uuid
    assert response["port_uuid"] == expected_port_uuid
    assert response["port_id"] is None

@patch("evchart_helper.api_helper.execute_query_df")
def test_get_station_and_port_uuid_given_no_port_found(mock_query):
    station_id = "friendly id"
    port_id = "port 1"
    network_provider = "my network"
    expected_station_uuid = "0"
    expected_network_uuid = "1"
    expected_data = {
        "station_uuid": [expected_station_uuid],
        "network_provider_uuid": [expected_network_uuid],
        "port_uuid": ['other_uuid'],
        "port_id": ['other_id'],
    }
    expected_result = pd.DataFrame(expected_data)

    mock_query.return_value = expected_result

    response = get_station_and_port_uuid(cursor, station_id, network_provider, port_id)

    assert response["station_uuid"] == expected_station_uuid
    assert response["network_provider_uuid"] == expected_network_uuid
    assert response["port_uuid"] is None
    assert response["port_id"] is None

@patch("evchart_helper.api_helper.execute_query_df")
def test_get_station_and_port_uuid_given_no_port_id_in_parameter_return_station_info(mock_query):
    station_id = "friendly id"
    network_provider = "my network"
    expected_station_uuid = "0"
    expected_network_uuid = "1"
    expected_data = {
        "station_uuid": [expected_station_uuid],
        "network_provider_uuid": [expected_network_uuid],
        "port_uuid": [None],
        "port_id": [None],
    }
    expected_result = pd.DataFrame(expected_data)

    mock_query.return_value = expected_result

    # called without port_id
    response = get_station_and_port_uuid(cursor, station_id, network_provider)

    assert response["station_uuid"] == expected_station_uuid
    assert response["network_provider_uuid"] == expected_network_uuid
    assert response["port_uuid"] is None
    assert response["port_id"] is None

def test_execute_query_duplicate():
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = IntegrityError(DUP_ENTRY, "duplicate entry")
    with pytest.raises(EvChartDatabaseAuroraDuplicateItemError):
        _ = execute_query(None, (), mock_cursor)


def test_execute_query_integrity_error_not_duplicate():
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = IntegrityError(BAD_NULL_ERROR, "bad null")
    with pytest.raises(EvChartDatabaseAuroraQueryError):
        _ = execute_query(None, (), mock_cursor)


def test_execute_query_programming_error():
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = ProgrammingError(PARSE_ERROR, "parse error")
    with pytest.raises(EvChartDatabaseAuroraQueryError):
        _ = execute_query(None, (), mock_cursor)


def test_ft_network_provider_in_query_true():
    response_query, response_data = query_builder_station_uuid(
        station_id="1", network_provider="nptest"
    )
    assert "network_provider_uuid" in response_query
    assert len(response_data) == 2


def test_get_available_years_does_not_return_anything_before_2023():
    todays_date = date(2022, 3, 14)
    result = get_available_years(todays_date)
    assert len(result) == 0


@pytest.mark.parametrize(
    "todays_date, expected_years",
    [
        (date(2022, 12, 31), []),
        (date(2024, 1, 1), ["2023"]),
        (date(2024, 4, 1), ["2024", "2023"]),
        (date(2025, 1, 1), ["2024", "2023"]),
        (date(2025, 4, 1), ["2025", "2024", "2023"]),
    ],
)
def test_get_available_years_by_date(todays_date, expected_years):
    result = get_available_years(todays_date)
    assert expected_years == result


def test_get_orgs_by_recipient_type_dr(mock_boto3_manager, dynamodb_org):
    response = get_orgs_by_recipient_type_dynamo("direct-recipient")
    expected = [
        {'org_id': '1', 'name': 'Maine DOT', 'recipient_type': 'direct-recipient', 'org_friendly_id': '1'},
        {'org_id': '2', 'name': 'NY DOT', 'recipient_type': 'direct-recipient', 'org_friendly_id': '2'}
    ]
    assert response == expected


def test_get_orgs_by_recipient_type_sr(mock_boto3_manager, dynamodb_org):
    response = get_orgs_by_recipient_type_dynamo("sub-recipient")
    expected = [
        {'org_id': '3', 'name': 'Sparkflow', 'recipient_type': 'sub-recipient', 'org_friendly_id': '3'},
        {'org_id': '4', 'name': 'Spark08', 'recipient_type': 'sub-recipient', 'org_friendly_id': '4'}
    ]
    assert response == expected