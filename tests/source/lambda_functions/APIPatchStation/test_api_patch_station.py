from datetime import datetime
import json
from unittest.mock import MagicMock, patch
import pandas as pd

import pytest
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseDynamoQueryError,
    EvChartUnableToDeleteItemError,
)
from evchart_helper.station_helper import handle_port_data


@pytest.fixture(name="event")
def get_event():
    event = {
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
        "body": json.dumps({"station_id": "123", "operational_date": "06/11/2024"}),
    }
    return event


@pytest.fixture(name="station_data")
def get_station_data():
    return [
        {
            "address": "sdasdf",
            "city": "sdfasdfaf",
            "dr_id": "11111111-2222-3333-4444-555555555555",
            "station_uuid": "71f6da10-7de0-4926-8a72-8cf2fcb444ab",
            "latitude": 0.000000,
            "longitude": 0.000000,
            "network_provider": "ampup",
            "nickname": "sdfasfa",
            "project_type": "existing_station",
            "station_id": "ssdfasdfaf",
            "state": "VA",
            "status": "Active",
            "updated_by": "ebenes@ee.doe.gov",
            "updated_on": "2024-12-31 00:00:00",
            "zip": "12345",
            "zip_extended": "1234",
            "operational_date": "2024-12-31",
            "NEVI": 1,
            "CFI": 0,
            "EVC_RAA": 0,
            "CMAQ": 0,
            "CRP": 0,
            "OTHER": 0,
            "AFC": 1,
            "num_fed_funded_ports": 1,
            "num_non_fed_funded_ports": None,
        }
    ]


from APIPatchStation.index import handler as api_patch_station
from APIPatchStation.index import update_station_sql_builder, send_station_approval_email


# 201, station updated successfully
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.get_network_provider_uuid_by_network_provider_value")
@patch("APIPatchStation.index.is_valid_station")
def test_valid_201(mock_is_valid_station, mock_get_np, mock_validate_data_integrity, event, mock_config, mock_validate_authorizations, station_data):
    mock_validate_data_integrity.return_value = mock_config
    mock_is_valid_station.return_value = station_data
    mock_get_np.return_value = "12345"
    event["body"] = json.dumps(
        {
            "federally_funded": True,
            "address": "100 State St E",
            "station_uuid": "017bdcba-aab5-44b8-82a0-f58ce386a321",
            "operational_date": "2024-06-11",
            "srs_added": [],
            "srs_removed": [],
        }
    )

    response = api_patch_station(event, None)
    assert response.get("statusCode") == 201
    assert not mock_get_np.called


# 201, station updated successfully
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.get_network_provider_uuid_by_network_provider_value")
@patch("APIPatchStation.index.is_valid_station")
@patch("APIPatchStation.index.aurora")
def test_valid_201_network_provider_changed(
    mock_aurora, mock_is_valid_station, mock_get_np, mock_validate_data_integrity, event, station_data, mock_config, mock_validate_authorizations
):
    mock_validate_data_integrity.return_value = mock_config
    execute_query = (
        mock_aurora.get_connection.return_value.cursor.return_value.__enter__.return_value.execute
    )
    # mock_aurora.get_connection.return_value.cursor.return_value.__enter__.return_value.execute.return_value = {}
    mock_is_valid_station.return_value = station_data
    network_provider_uuid = "12345"
    mock_get_np.return_value = network_provider_uuid
    event["body"] = json.dumps(
        {
            "address": "100 State St E",
            "station_uuid": "017bdcba-aab5-44b8-82a0-f58ce386a321",
            "federally_funded": True,
            "operational_date": "2024-06-11",
            "network_provider": "new one",
            "srs_added": [],
            "srs_removed": [],
        }
    )

    response = api_patch_station(event, None)
    assert response.get("statusCode") == 201
    assert mock_get_np.called
    args, _ = execute_query.call_args
    assert execute_query.called
    assert "network_provider_uuid = %(network_provider_uuid)" in args[0]
    assert args[1].get("network_provider_uuid") == network_provider_uuid



# 201, station updated successfully and ports called successfully
@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query_df")
@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query")
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.get_network_provider_uuid_by_network_provider_value")
@patch("APIPatchStation.index.is_valid_station")
@patch("APIPatchStation.index.handle_port_data")
@patch("APIPatchStation.index.update_station")
def test_valid_201_and_update_station_called_without_ports_and_ports_called_with_them(
    mock_update_station,
    mock_handle_port_data,
    mock_is_valid_station,
    mock_get_np,
    mock_validate_data_integrity,
    mock_validate_port_equality_execute_query,
    mock_validate_funding_type_execute_query_df,
    event,
    station_data,
    mock_config,
    mock_validate_authorizations
):
    mock_validate_data_integrity.return_value = mock_config
    mock_validate_port_equality_execute_query.return_value = [
        {
            "num_non_fed_funded_ports": 2,
            "non_fed_funded_ports": 2,
            "num_fed_funded_ports": 1,
            "fed_funded_ports": 1,
        }
    ]
    mock_validate_funding_type_execute_query_df.return_value = pd.DataFrame({
        "NEVI": [1],
        "CFI": [0],
        "EVC_RAA": [0],
        "CMAQ": [0],
        "CRP": [0],
        "OTHER": [1],
    })
    mock_is_valid_station.return_value = station_data
    mock_get_np.return_value = "12345"
    event["body"] = json.dumps(
        {
            "station_uuid": "4e3981f8-9113-43ac-8f86-dffb9dbc66b3",
            "operational_date": "2024-03-01",
            "federally_funded": True,
            "num_fed_funded_ports": "1",
            "num_non_fed_funded_ports": "1",
            "fed_funded_ports": [{"port_id": "1234", "port_type": "L2"}],
            "non_fed_funded_ports": [{"port_id": "5678", "port_type": "DCFC"}],
        }
    )

    response = api_patch_station(event, None)
    body = json.loads(event.get("body"))
    update_station_args, _ = mock_update_station.call_args
    handle_port_data_args, _ = mock_handle_port_data.call_args
    assert update_station_args[0].get("fed_funded_ports") is None
    assert update_station_args[0].get("non_fed_funded_ports") is None
    assert handle_port_data_args[0].get("fed_funded_ports") == body.get("fed_funded_ports")
    assert handle_port_data_args[0].get("non_fed_funded_ports") == body.get("non_fed_funded_ports")
    assert handle_port_data_args[0].get("station_uuid")
    assert response.get("statusCode") == 201


# 201, station updated successfully operational date not added
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.get_network_provider_uuid_by_network_provider_value")
@patch("APIPatchStation.index.is_valid_station")
def test_no_operational_date_valid_201(
    mock_is_valid_station, mock_get_np, mock_validate_data_integrity, event, station_data, mock_config, mock_validate_authorizations
):
    mock_validate_data_integrity.return_value = mock_config
    mock_is_valid_station.return_value = station_data
    mock_get_np.return_value = "12345"
    event["body"] = json.dumps(
        {
            "address": "100 State St E",
            "station_uuid": "017bdcba-aab5-44b8-82a0-f58ce386a321",
            "federally_funded": True,
            "srs_added": [],
            "srs_removed": [],
        }
    )

    response = api_patch_station(event, None)
    assert response.get("statusCode") == 201


# 406, EvChartInvalidBodyError
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
def test_unknown_field_in_station_data_406(mock_validate_data_integrity, mock_get_feature_toggles, mock_validate_authorizations, mock_config, event):
    mock_validate_data_integrity.return_value = mock_config
    malformed_event = event
    malformed_event["body"] = json.dumps({"invalid_data": "13"})

    response = api_patch_station(malformed_event, None)
    assert response.get("statusCode") == 406


# 403, EvChartUserNotAuthorized
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
def test_invalid_sr_updating_station_403(mock_validate_data_integrity, mock_get_feature_toggles, mock_validate_authorizations, mock_config, event):
    mock_validate_data_integrity.return_value = mock_config
    event["requestContext"]["authorizer"]["claims"]["scope"] = "sub-recipient"
    event["requestContext"]["authorizer"]["claims"]["org_id"] = "11111111-1111-3333-4444-555555555555"

    response = api_patch_station(event, None)
    assert response.get("statusCode") == 403


# 500, EvChartDatabaseQueryError (error updating station)
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.update_station")
def test_invalid_500_updating_station(mock_update_station, mock_validate_data_integrity, event, mock_config, mock_validate_authorizations):
    mock_validate_data_integrity.return_value = mock_config
    mock_update_station.side_effect = EvChartDatabaseAuroraQueryError()

    response = api_patch_station(event, None)
    assert response.get("statusCode") == 406


# 500, EvChartDatabaseQueryError (error adding subrecipients)
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.insert_authorized_subrecipients")
@patch("APIPatchStation.index.check_for_existing_srs")
@patch("APIPatchStation.index.is_valid_station")
def test_invalid_500_inserting_subrecipients(
    mock_is_valid_station,
    mock_insert_authorized_subrecipients,
    _mock_existing_srs,
    mock_validate_data_integrity,
    event,
    station_data,
    mock_config,
    mock_validate_authorizations
):
    mock_validate_data_integrity.return_value = mock_config
    mock_is_valid_station.return_value = station_data
    event["body"] = json.dumps(
        {"station_uuid": "017bdcba-aab5-44b8-82a0-f58ce386a321", "srs_added": {"123": "Sparkflow"}, "operational_date": "2025-07-04"}
    )
    mock_insert_authorized_subrecipients.side_effect = EvChartDatabaseAuroraQueryError()
    response = api_patch_station(event, None)
    assert response.get("statusCode") == 500


# 500, EvChartDatabaseQueryError (error removing subrecipients)
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.remove_authorized_subrecipients")
def test_invalid_500_removing_subrecipients(
    mock_remove_authorized_subrecipients,
    mock_validate_data_integrity,
    event,
    mock_config,
    mock_validate_authorizations,
    # following mocks are used for validate_authorized_subrecipients()
    _dynamodb_org,
    _mock_boto3_manager
):
    mock_validate_data_integrity.return_value = mock_config
    event["body"] = json.dumps(
        {"srs_removed": {"123": "Sparkflow"}, "operational_date": "06/11/2024"}
    )
    mock_remove_authorized_subrecipients.side_effect = EvChartDatabaseAuroraQueryError()
    response = api_patch_station(event, None)
    assert response.get("statusCode") == 500


# 409, EvChartDatabaseAuroraDuplicateItemError (sr already exists for station)
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.check_for_existing_srs")
@patch("APIPatchStation.index.is_valid_station")
def test_invalid_409_existing_srs(
    mock_is_valid_station,
    mock_check_for_existing_srs,
    mock_validate_data_integrity,
    event,
    station_data,
    mock_config,
    mock_validate_authorizations,
    # following mocks are used for validate_authorized_subrecipients()
    _dynamodb_org,
    _mock_boto3_manager
):
    mock_validate_data_integrity.return_value = mock_config
    mock_is_valid_station.return_value = station_data
    event["body"] = json.dumps(
        {
            "station_uuid": "017bdcba-aab5-44b8-82a0-f58ce386a321",
            "federally_funded": True,
            "srs_added": {"3": "Sparkflow"},
            "operational_date": "2024-06-11"
        }
    )
    mock_check_for_existing_srs.side_effect = EvChartDatabaseAuroraDuplicateItemError()

    response = api_patch_station(event, None)
    assert response.get("statusCode") == 409


# 500, EvChartDatabaseDynamoQueryError (sr incorrect type)
@patch("station_validation.validate_authorizations_and_recipient_types.validate_authorized_subrecipients")
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.check_for_existing_srs")
@patch("APIPatchStation.index.is_valid_station")
def test_invalid_500_sr_type(
    mock_is_valid_station,
    _mock_check_for_existing_srs,
    mock_validate_data_integrity,
    mock_validate_authorized_subrecipients,
    event,
    station_data,
    mock_config,
    mock_validate_authorizations
):
    mock_validate_data_integrity.return_value = mock_config
    mock_is_valid_station.return_value = station_data
    mock_validate_authorized_subrecipients.side_effect = EvChartDatabaseDynamoQueryError()

    event["body"] = json.dumps({"station_uuid": "017bdcba-aab5-44b8-82a0-f58ce386a321", "srs_added": {"123": "Sparkflow"}})
    response = api_patch_station(event, None)
    assert response.get("statusCode") == 500


# 409, EvChartDatabaseAuroraDuplicateItemError
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.update_station")
@patch("APIPatchStation.index.is_valid_station")
def test_duplicate_item_error_409(
    mock_is_valid_station,
    mock_update_station,
    mock_validate_data_integrity,
    event,
    station_data,
    mock_config,
    mock_validate_authorizations
):
    mock_validate_data_integrity.return_value = mock_config
    mock_is_valid_station.return_value = station_data

    event["body"] = json.dumps(
        {
            "station_uuid": "017bdcba-aab5-44b8-82a0-f58ce386a321",
            "federally_funded": True,
            "operational_date": "2024-06-11"
        }
    )
    mock_update_station.side_effect = EvChartDatabaseAuroraDuplicateItemError()
    response = api_patch_station(event, None)
    assert response.get("statusCode") == 409


@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("evchart_helper.station_helper.delete_port_data")
def test_remove_ports(mock_delete_port_data, mock_validate_data_integrity, mock_config, mock_validate_authorizations):
    mock_validate_data_integrity.return_value = mock_config
    station = {"station_uuid": "123", "ports_removed": ["111", "222"]}

    response = handle_port_data(station, MagicMock(), "User", datetime.now())

    assert mock_delete_port_data.called
    assert response == True


def test_sql_builder_for_funding_type_and_AFC():
    station = {
        "AFC": 0,
        "NEVI": 1,
        "CFI": 0,
        "EVC_RAA": 1,
        "CMAQ": 1,
        "CRP": 1,
        "OTHER": 1,
    }
    query_result = update_station_sql_builder(station=station, updated_on="test", updated_by="test")
    assert (
        "AFC = %(AFC)s" in query_result
    ), f"AFC expected in sql builder but was not returned, instead got {query_result}"
    assert (
        "NEVI = %(NEVI)s" in query_result
    ), f"NEVI funding type expected in sql builder but was not returned, instead got {query_result}"
    assert (
        "CFI = %(CFI)s" in query_result
    ), f"CFI funding type expected in sql builder but was not returned, instead got {query_result}"
    assert (
        "EVC_RAA = %(EVC_RAA)s" in query_result
    ), f"EVC_RAA funding type expected in sql builder but was not returned, instead got {query_result}"
    assert (
        "CMAQ = %(CMAQ)s" in query_result
    ), f"CMAQ funding type expected in sql builder but was not returned, instead got {query_result}"
    assert (
        "CRP = %(CRP)s" in query_result
    ), f"CRP funding type expected in sql builder but was not returned, instead got {query_result}"
    assert (
        "OTHER = %(OTHER)s" in query_result
    ), f"OTHER funding type expected in sql builder but was not returned, instead got {query_result}"


# JE-5739 ensuring correct error messages are returned, especially nested error messages
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.trigger_email")
@patch("APIPatchStation.index.format_users")
@patch("APIPatchStation.index.get_org_users")
@patch("APIPatchStation.index.get_org_info_dynamo")
def test_unknown_exception_500(
    mock_get_org, _mock_get_users, _mock_format_users, _mock_trigger_email, mock_validate_data_integrity, mock_config
):
    mock_validate_data_integrity.return_value = mock_config
    mock_get_org.side_effect = EvChartDatabaseDynamoQueryError(message="test error message. ")
    with pytest.raises(EvChartDatabaseDynamoQueryError) as e:
        send_station_approval_email(
            {"nickname": "", "station_id": ""}, {}, "dr org name", ["sr-id"]
        )
    assert e.value.message == (
        "EvChartDatabaseDynamoQueryError raised. test error message. Error thrown in send_station_approval_email()."
    )


@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query_df")
@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query")
@patch("station_validation.validate_data_integrity.DatabaseCentralConfig")
@patch("APIPatchStation.index.module_data_exists_for_ports")
@patch("APIPatchStation.index.is_valid_station")
@patch("APIPatchStation.index.handle_port_data")
@patch("APIPatchStation.index.update_station")
def test_given_change_fed_funded_to_non_fed_funded_all_fed_funded_ports_removed(
    _mock_update_station,
    _mock_handle_port_data,
    mock_is_valid_station,
    mock_module_data_exists_for_ports,
    mock_validate_data_integrity_central_config,
    mock_validate_port_equality_execute_query,
    mock_validate_funding_type_execute_query_df,
    event,
    station_data,
    mock_config,
    mock_validate_authorizations
):
    mock_validate_data_integrity_central_config.return_value = mock_config
    stations_to_delete = ["123", "345"]
    mock_validate_funding_type_execute_query_df.return_value = pd.DataFrame({
        "NEVI": [0],
        "CFI": [0],
        "EVC_RAA": [0],
        "CMAQ": [0],
        "CRP": [0],
        "OTHER": [0],
    })

    mock_validate_port_equality_execute_query.return_value = [
        {
            "num_non_fed_funded_ports": 2,
            "non_fed_funded_ports": 2,
            "num_fed_funded_ports": 1,
            "fed_funded_ports": 1,
        }
    ]
    mock_module_data_exists_for_ports.side_effect = EvChartUnableToDeleteItemError(
        message=f"Module data present for ports: {stations_to_delete}."
    )
    mock_is_valid_station.return_value = station_data

    event["body"] = json.dumps(
        {
            "federally_funded": False,
            "station_uuid": "4e3981f8-9113-43ac-8f86-dffb9dbc66b3",
            "operational_date": "2024-03-01",
            "num_fed_funded_ports": "0",
            "num_non_fed_funded_ports": "1",
            "fed_funded_ports": [],
            "non_fed_funded_ports": [{"port_id": "5678", "port_type": "DCFC"}],
            # list of port_uuids
            "ports_removed": ["123-123", "456-456"],
        }
    )

    response = api_patch_station(event, None)

    assert response.get("statusCode") == 409