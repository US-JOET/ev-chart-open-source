from unittest.mock import MagicMock, patch
import datetime
import json
import pytest
import pandas as pd

from evchart_helper.station_helper import (
    format_operational_date,
    handle_port_data,
    remove_station,
    is_valid_station,
    check_for_existing_srs,
    trigger_station_authorizes_subrecipient_email
    )
from evchart_helper.custom_exceptions import (
    EvChartMissingOrMalformedBodyError,
    EvChartJsonOutputError,
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartDatabaseDynamoQueryError
)

import feature_toggle
from feature_toggle.feature_enums import Feature


@pytest.fixture(name="event")
def get_valid_event():
    return {
        "httpMethod": "PATCH",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "1234",
                    "org_friendly_id": "1",
                    "org_name": "New York DOT",
                    "email": "gcostanza@gmail.com",
                    "preferred_name": "George Costanza",
                    "scope": "direct-recipient",
                    "role": "admin",
                }
            },
        },
        "body": json.dumps(
            {
                "address": "111 N Ave",
                "city": "San Diego",
                "project_type": "existing_station",
                "station_id": "456",
                "latitude": "2.123456",
                "longitude": "3.123456",
                "nickname": "Superstation",
                "num_fed_funded_ports": "3",
                "num_non_fed_funded_ports": "4",
                "state": "CA",
                "status": "Active",
                "authorized_subrecipients": [],
                "zip": "92139",
                "zip_extended": "1234",
                "station_uuid": "13-13",
                "fed_funded_ports": [
                    {"port_id": "abc", "port_uuid": "abc-abc", "port_type": "DCFC"},
                    {"port_id": "123", "port_type": "L2"},
                    {"port_id": "345", "port_type": "L2"},
                ],
                "non_fed_funded_ports": [
                    {"port_id": "lmn", "port_uuid": "lmn-lmn", "port_type": "DCFC"},
                    {"port_id": "hij", "port_uuid": "hij-hij", "port_type": "DCFC"},
                    {"port_id": "567", "port_type": "L2"},
                    {"port_id": "789", "port_type": "L2"},
                ],
                # list of port_uuids
                "ports_removed": ["123-123", "456-456"],
            }
        ),
    }


@pytest.fixture(name="event_funding_types")
def get_event_funding_types():
    event = {}
    event["NEVI"] = 0
    event["CFI"] = 0
    event["EVC_RAA"] = 0
    event["CMAQ"] = 0
    event["CRP"] = 0
    event["OTHER"] = 0
    event["station_uuid"] = "123"
    return event


def test_format_operational_date_empty():
    empty_date = ""
    response = format_operational_date(empty_date)
    assert response is None


def test_format_operational_date():
    date = "2024-06-11"
    expected = datetime.datetime.strptime("2024-06-11", "%Y-%m-%d").date()
    response = format_operational_date(date)
    assert response == expected

@patch("evchart_helper.station_helper.execute_query")
def test_handle_port_data_correct_fields_passed_in(mock_query, event):
    response = handle_port_data(
        json.loads(event["body"]),
        cursor=MagicMock(),
        updated_by="Sophia",
        updated_on=datetime.datetime.now(),
    )
    assert response is True


@patch("evchart_helper.station_helper.delete_station_data")
@patch("evchart_helper.station_helper.module_data_exists_for_station_uuid")
@patch("evchart_helper.station_helper.is_valid_station")
def test_remove_station_valid(mock_valid_station, mock_data_exists, mock_delete):
    mock_valid_station.return_value = True
    mock_data_exists.return_value = False
    cursor = MagicMock()
    remove_station(station_uuid="1213", cursor=cursor)
    mock_delete.assert_called_once_with("1213", cursor)


@patch("evchart_helper.station_helper.delete_station_data")
@patch("evchart_helper.station_helper.module_data_exists_for_station_uuid")
@patch("evchart_helper.station_helper.is_valid_station")
def test_remove_station_invalid(mock_valid_station, mock_data_exists, mock_delete):
    mock_valid_station.return_value = True
    mock_data_exists.return_value = True
    with pytest.raises(EvChartMissingOrMalformedBodyError):
        remove_station(station_uuid="1213", cursor=MagicMock())
    mock_delete.assert_not_called()

#  JE-6118 bug ticket that is preventing authorizing srs for edit station due to "bool not subscriptable" error for api patch station
# this test ensures that is_valid_station will always return station details if the station exists
@patch("evchart_helper.station_helper.execute_query")
def test_adding_srs(mock_execute_query):
    station = {
        'station_uuid': '111',
        'fed_funded_ports': [
            {'port_uuid': '888', 'port_id': 'port-id', 'port_type': 'L2'},
        ],
        'operational_date': '2025-12-18',
        'srs_added': ['333'],
        'dr_id': '222'
    }

    mock_execute_query.return_value = [{"station_id": "test-station", "mock_station_details": "temp_data"}]
    response = is_valid_station(station_uuid=station.get("station_uuid"), cursor=MagicMock())[0]
    assert response

# JE-5739 ensuring correct error messages are returned, especially nested error messages
@patch("evchart_helper.station_helper.execute_query_fetchone")
def test_check_for_existing_srs_aurora_db_error(mock_execute_query):
    mock_execute_query.side_effect = EvChartDatabaseAuroraQueryError(message="test error message")
    with pytest.raises(EvChartDatabaseAuroraQueryError) as e:
        check_for_existing_srs(["sr-id"],"station-uuid","dr-id",{},MagicMock())

    assert e.value.message == "EvChartDatabaseAuroraQueryError raised. test error message"

# JE-5739 ensuring correct error messages are returned, especially nested error messages
@patch("evchart_helper.station_helper.execute_query_fetchone")
def test_check_for_existing_srs_duplicate_item_error(mock_execute_query):
    mock_execute_query.return_value = [{"test": "invalid-result"}]
    with pytest.raises(EvChartDatabaseAuroraDuplicateItemError) as e:
        check_for_existing_srs(["sr-id"],"station-uuid","dr-id",{},MagicMock())
    assert e.value.message == (
        "EvChartDatabaseAuroraDuplicateItemError raised. "
        "Error thrown in check_for_existing_srs(). SR sr-id already exists in Station station-uuid"
    )

# JE-5739 ensuring correct error messages are returned, especially nested error messages
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("evchart_helper.station_helper.trigger_email")
@patch("evchart_helper.station_helper.format_users")
@patch("evchart_helper.station_helper.get_org_users")
@patch("evchart_helper.station_helper.get_org_info_dynamo")
def test_trigger_station_authorizes_subrecipient_error(
    mock_get_org,
    mock_get_users,
    mock_format_users,
    mock_trigger_email,
    mock_feature_enablement_check
):
    mock_feature_enablement_check.return_value = {
        "Name": "STATION_AUTHORIZES_SR_EMAIL",
        "Value": "True"
    }
    mock_get_org.side_effect = EvChartDatabaseDynamoQueryError(message="test error message. ")
    with pytest.raises(EvChartDatabaseDynamoQueryError) as e:
        trigger_station_authorizes_subrecipient_email(["sr-id"],"station-id","nickname","dr org name")
    assert e.value.message == (
        "EvChartDatabaseDynamoQueryError raised. test error message. Error thrown in trigger_station_authorizes_subrecipient_email()."
    )

# JE-5739 ensuring correct error messages are returned, especially nested error messages
@patch("evchart_helper.station_helper.is_valid_station")
def test_nested_error_messages(mock_is_valid_station):
    mock_is_valid_station.return_value = False
    with pytest.raises(EvChartMissingOrMalformedBodyError) as e:
        remove_station("123", MagicMock())

    assert e.value.message == (
        "EvChartMissingOrMalformedBodyError raised. No station found for station uuid 123.Function called in remove_station()"
    )
