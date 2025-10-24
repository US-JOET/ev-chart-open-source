import json
from unittest.mock import MagicMock, patch

import pytest
from APIPostStation.index import handler as api_post_station
from APIPostStation.index import insert_station_registration
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartDatabaseAuroraQueryError,
)
from pymysql.err import IntegrityError

from feature_toggle import FeatureToggleService, Feature


@pytest.fixture(name="event")
def get_valid_event():
    return {
        "headers": {},
        "httpMethod": "PATCH",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "11111111-2222-3333-4444-555555555555",
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
               'address': '123 nice lane',
                'city': 'san diego ',
                'project_type': 'new_station',
                'station_id': 'station1',
                'latitude': '12.123456',
                'longitude': '12.123456',
                'nickname': 'station1',
                'federally_funded': True,
                'num_fed_funded_ports': '2',
                'num_non_fed_funded_ports': '2',
                'state': 'ca',
                'status': 'Active',
                'network_provider': 'abm',
                'operational_date': '2025-07-04',
                'NEVI': 1,
                'CFI': 1,
                'EVC_RAA': 0,
                'CMAQ': 0,
                'CRP': 0,
                'OTHER': 0,
                'AFC': 1,
                'authorized_subrecipients': [],
                'zip': '12345',
                'zip_extended': '1234',
                "fed_funded_ports": [
                    {"port_id": "123", "port_type": "L2"},
                    {"port_id": "345", "port_type": "L2"},
                ],
                "non_fed_funded_ports": [
                    {"port_id": "567", "port_type": "L2"},
                    {"port_id": "789", "port_type": "L2"},
                ],
                "dr_id": "11111111-2222-3333-4444-555555555555",
            }
        ),
    }

@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
def test_unauthorized_dr_adding_station(mock_validate_data_integrity, mock_config, event):
    mock_validate_data_integrity.return_value = mock_config
    invalid_event = event.copy()
    body = json.loads(invalid_event.get("body"))
    body["dr_id"] = "55555555-5555-5555-5555-555555555555"
    invalid_event["body"] = json.dumps(body)

    response = api_post_station(invalid_event, None)
    assert response.get("statusCode") == 403


# 201, station registered successfully as a DR
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
def test_valid_DR_adding_station_201(
    mock_validate_data_integrity, event, mock_config
):
    mock_validate_data_integrity.return_value = mock_config
    response = api_post_station(event, None)
    assert response.get("statusCode") == 201


# 201, station registered successfully as a DR
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPostStation.index.handle_port_data")
@patch("APIPostStation.index.insert_station_registration")
def test_register_station_called_without_ports_and_ports_called_with_them(
    mock_register_station,
    mock_handle_port_data,
    mock_validate_data_integrity,
    event,
    mock_config
):
    mock_validate_data_integrity.return_value = mock_config

    response = api_post_station(event, None)
    body = json.loads(event.get("body"))
    register_station_args, _ = mock_register_station.call_args
    handle_port_data_args, _ = mock_handle_port_data.call_args
    assert register_station_args[0].get("fed_funded_ports") is None
    assert register_station_args[0].get("non_fed_funded_ports") is None
    assert handle_port_data_args[0].get("fed_funded_ports") == body.get("fed_funded_ports")
    assert handle_port_data_args[0].get("non_fed_funded_ports") == body.get("non_fed_funded_ports")
    assert handle_port_data_args[0].get("station_uuid")
    assert response.get("statusCode") == 201


# 201, station registered successfully as an SR
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
def test_valid_SR_adding_station_201(
    mock_validate_data_integrity, event, mock_config
):
    mock_validate_data_integrity.return_value = mock_config
    event["requestContext"]["authorizer"]["claims"]["scope"] = "sub-recipient"

    response = api_post_station(event, None)
    assert response.get("statusCode") == 201


# 406, EvChartMissingOrMalformedBodyError
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
def test_invalid_406(mock_validate_data_integrity, event, mock_config):
    mock_validate_data_integrity.return_value = mock_config
    # removing a required field from the event
    invalid_station = json.loads(event["body"])
    invalid_station.pop("operational_date")
    event["body"] = json.dumps(invalid_station)

    response = api_post_station(event, None)
    assert response.get("statusCode") == 406


# 406, EvChartMissingOrMalformedBodyError
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
def test_invalid_field_datatype_406(mock_validate_data_integrity, event, mock_config):
    mock_validate_data_integrity.return_value = mock_config
    invalid_station = json.loads(event["body"])
    invalid_station["NEVI"] = "invalid_data"
    event["body"] = json.dumps(invalid_station)

    response = api_post_station(event, None)
    assert response.get("statusCode") == 406


# 500, EvChartDatabaseAuroraQueryError (error updating station)
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPostStation.index.insert_station_registration")
def test_invalid_500_updating_station(mock_update_station, mock_validate_data_integrity, event, mock_config):
    mock_validate_data_integrity.return_value = mock_config
    mock_update_station.side_effect = EvChartDatabaseAuroraQueryError()
    response = api_post_station(event, None)
    assert response.get("statusCode") == 500


# 500, EvChartDatabaseAuroraQueryError (error adding subrecipients)
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPostStation.index.insert_authorized_subrecipients")
def test_invalid_500_inserting_subrecipients(
    mock_insert_authorized_subrecipients, mock_validate_data_integrity, event, mock_config
):
    mock_validate_data_integrity.return_value = mock_config
    mock_insert_authorized_subrecipients.side_effect = EvChartDatabaseAuroraQueryError()
    response = api_post_station(event, None)
    assert response.get("statusCode") == 500


@patch.object(FeatureToggleService, "get_active_feature_toggles")
def test_registered_station_insert_v3_succeeds_uuid_exists_4(mock_toggle_set):
    mock_toggle_set.return_value = {Feature.NETWORK_PROVIDER_TABLE}
    cursor = MagicMock()
    cursor.execute.side_effect = IntegrityError(
        1062, "Duplicate entry 'new_station_id3' for key 'station_registrations.NP_Station_ID'"
    )

    edited_station = {
        "address": "111 N Ave",
        "station_id": "456",
        "city": " Portland",
        "latitude": "2.222222",
        "longitude": "2.222222",
        "network_provider": "amped_up",
        "nickname": "Sarah Station 5000",
        "number_of_ports": "1",
        "ports": "",
        "project_type": "existing_station",
        "state": "oregon",
        "stationID": "2000",
        "status": "Active",
        "zip": "22222",
        "zip_extended": "2222",
        "operational_date": "2025-05-01 17:55:16.230912+00:00",
        "NEVI": 1,
        "CFI": 0,
        "EVC_RAA": 0,
        "CMAQ": 0,
        "CRP": 1,
        "OTHER": 0,
        "AFC": 0,
        "num_fed_funded_ports": "2",
        "num_non_fed_funded_ports": "2",
        "dr_id": "1234",
        "station_uuid": "20b8168e-775d-486b-bc4c-c34839e93fd9",
        "updated_on": "2025-05-01 17:55:16.230912+00:00",
        "updated_by": "gcostanza@gmail.com",
    }
    with pytest.raises(EvChartDatabaseAuroraDuplicateItemError) as e:
        insert_station_registration(edited_station, cursor, mock_toggle_set)

    assert "EvChartDatabaseAuroraDuplicateItemError raised. Duplicate key" in e.value.message


@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("evchart_helper.station_helper.delete_port_data")
def test_remove_port_data_valid(
    mock_delete_port_data, mock_validate_data_integrity, event, mock_config
):
    mock_validate_data_integrity.return_value = mock_config

    api_post_station(event, None)
    assert not mock_delete_port_data.called


@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPostStation.index.insert_station_registration")
@patch("APIPostStation.index.handle_port_data")
@patch("APIPostStation.index.get_org_info_dynamo")
@patch("APIPostStation.index.trigger_station_authorizes_subrecipient_email")
@patch.object(FeatureToggleService, "get_active_feature_toggles")
def test_no_auth_email_sent_to_sr_when_sr_submits_station_for_approval(
    mock_toggle_set,
    mock_sr_auth_email,
    _mock_get_org_info,
    _mock_handle_port_data,
    _mock_register_station,
    mock_validate_data_integrity,
    event,
    mock_config
):
    mock_validate_data_integrity.return_value = mock_config
    mock_toggle_set.return_value = {
        Feature.STATION_AUTHORIZES_SR_EMAIL,
        Feature.NETWORK_PROVIDER_TABLE,
    }
    # updating the body to have the status = pending
    updated_api_body = json.loads(event["body"])
    updated_api_body["status"] = "Pending Approval"
    event["body"] = json.dumps(updated_api_body)

    res = api_post_station(event, None)
    assert res.get("statusCode") == 201
    mock_sr_auth_email.assert_not_called()
