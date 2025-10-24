import pytest

from station_validation.validate_data_integrity import (
    validate_fields,
    validate_station_datatypes,
)


def test_validate_fields_all_fields_are_valid_for_post_request(validation_options_for_federally_funded_station, validation_options_for_non_federally_funded_station, mock_config):
    response = validate_fields(validation_options_for_federally_funded_station)
    assert response is True
    response = validate_fields(validation_options_for_non_federally_funded_station)
    assert response is True


def test_validate_fields_all_fields_are_valid_for_patch_request(validation_options_for_federally_funded_station, validation_options_for_non_federally_funded_station, mock_config):
    validation_options_for_federally_funded_station["api"] = "patch"
    validation_options_for_federally_funded_station["station"]["station_uuid"] = '11111111-2222-3333-4444-555555555555'
    response = validate_fields(validation_options_for_federally_funded_station)
    assert response is True
    validation_options_for_non_federally_funded_station["api"] = "patch"
    validation_options_for_non_federally_funded_station["station"]["station_uuid"] = '11111111-2222-3333-4444-555555555555'
    response = validate_fields(validation_options_for_non_federally_funded_station)
    assert response is True


@pytest.mark.parametrize("api", ("post", "patch"))
def test_validate_requried_fields_patch_unknown_field_in_data_returns_an_error_object(api,validation_options_for_federally_funded_station, mock_config):
    validation_options_for_federally_funded_station["api"] = api
    validation_options_for_federally_funded_station["station"]["unknown_field"] = "invalid_data"
    response = validate_fields(validation_options_for_federally_funded_station)
    assert response is not True


@pytest.mark.parametrize("api, expected",
    [
        ("patch", {'validate_required_fields()': "Field must be present for patch requests {'station_uuid'}. "}),
        ("post", {'validate_required_fields()': "Missing required fields {'fed_funded_ports'} "})
    ]
)
def test_validate_fields_missing_fields_for_post_and_patch(api, expected, validation_options_for_federally_funded_station, mock_config):
    validation_options_for_federally_funded_station["api"] = api
    station = validation_options_for_federally_funded_station.get("station")
    station.pop("fed_funded_ports", None)
    response = validate_fields(validation_options_for_federally_funded_station)
    assert response == expected


@pytest.mark.parametrize("api,expected",
    [
        ("post", {"validate_required_fields()": "Unknown fields {'unknown_field'} Missing required fields {'fed_funded_ports'} "}),
        ("patch", {"validate_required_fields()": "Unknown fields {'unknown_field'} Field must be present for patch requests {'station_uuid'}. "})
    ]
)
def test_unknown_and_missing_fields(api, expected, validation_options_for_federally_funded_station, mock_config):
    validation_options_for_federally_funded_station["api"] = api
    station = validation_options_for_federally_funded_station.get("station")
    station["unknown_field"] = "invalid_data"
    station.pop("fed_funded_ports", None)
    response = validate_fields(validation_options_for_federally_funded_station)
    assert response == expected


def test_validate_datatypes_all_valid(validation_options_for_federally_funded_station, validation_options_for_non_federally_funded_station, mock_config):

    fed_funded_response = validate_station_datatypes(validation_options_for_federally_funded_station)
    assert fed_funded_response is True

    non_fed_funded_response = validate_station_datatypes(validation_options_for_non_federally_funded_station)
    assert non_fed_funded_response is True


@pytest.mark.parametrize(
    "invalid_data, invalid_field",
    [
        ({"state": "California"}, "state"),
        ({"AFC": "12"}, "AFC"),
        ({"CFI": "true"}, "CFI"),
        ({"city": "x" * 101}, "city"),
        ({"CMAQ": "false"}, "CMAQ"),
        ({"CRP": -1}, "CRP"),
        ({"dr_id": "x"  * 37}, "dr_id"),
        ({"EVC_RAA": 2}, "EVC_RAA"),
        ({"latitude": "-90.01"}, "latitude"),
        ({"latitude": "-1.1234567891011"}, "latitude"),
        ({"longitude": "-180.000003"}, "longitude"),
        ({"network_provider": "x"  * 37}, "network_provider"),
        ({"network_provider_uuid": "x"  * 37}, "network_provider_uuid"),
        ({"NEVI": "0.1"}, "NEVI"),
        ({"nickname": "x"  * 51}, "nickname"),
        ({"num_fed_funded_ports": "-1"}, "num_fed_funded_ports"),
        ({"num_non_fed_funded_ports": "-1"}, "num_non_fed_funded_ports"),
        ({"operational_date": "1-1-250:00"}, "operational_date"),
        ({"OTHER": "0.1"}, "OTHER"),
        ({"project_type": "x"  * 31}, "project_type"),
        ({"station_id": "x"  * 37}, "station_id"),
        ({"station_uuid": "x"  * 37}, "station_uuid"),
        ({"zip": "0.1"}, "zip"),
        ({"zip_extended": "12345"}, "zip_extended"),
    ]

)
def test_validate_all_station_datatypes_invalid(invalid_data, invalid_field, validation_options_for_federally_funded_station, mock_config):
    validation_options_for_federally_funded_station["station"]=invalid_data
    response = validate_station_datatypes(validation_options_for_federally_funded_station)
    assert response["validate_station_datatypes()"][0].get("header_name") == invalid_field


def test_get_invalid_station_fields_for_port_data_invalid_port_id(validation_options_for_federally_funded_station, mock_config):
    port_info = {
        "fed_funded_ports": [{"port_id": "", "port_type": "DCFC"}, {"port_id": "2", "port_type": ""}, ],
        "non_fed_funded_ports": [{"port_id": "123456789-123456789-123456789-123456789-123", "port_type": "DCFC"}]
    }
    validation_options_for_federally_funded_station["station"].update(port_info)
    response = validate_station_datatypes(validation_options_for_federally_funded_station)
    error_list = response["validate_station_datatypes()"]
    assert len(error_list) == 2
    for error_obj in error_list:
        assert error_obj["header_name"] == "port_id"


def test_patch_station_adding_port_while_having_an_exsting_port_already(validation_options_for_federally_funded_station, mock_config):
    validation_options_for_federally_funded_station["api"] = "patch"
    validation_options_for_federally_funded_station["station"] = {
        'station_uuid': '001148d2-711d-451b-9cf3-521ed18936ab',
        'fed_funded_ports': [
            {'port_uuid': 'a4cd085c-c02e-4f0c-b196-6ae3f164e7f2', 'port_id': 'port-id-m86188391', 'port_type': 'DCFC'},
            {'port_id': 'port-id-m123456', 'port_type': ''}
        ],
        'operational_date': '2023-04-20',
        'num_fed_funded_ports': '2'
    }
    response = validate_station_datatypes(validation_options_for_federally_funded_station)
    assert response is True


def test_valid_port_fields_for_patch(validation_options_for_federally_funded_station, mock_config):
    validation_options_for_federally_funded_station["api"] = "patch"
    validation_options_for_federally_funded_station["station"] = {
        'station_uuid': '22222222-2222-2222-2222-222222222222',
        'fed_funded_ports': [{'port_uuid': '33333333-3333-3333-3333-333333333333', 'port_id': '123', 'port_type': ''}],
        'operational_date': '2025-07-04',
        'address': 'asdf lane'
    }
    response = validate_station_datatypes(validation_options_for_federally_funded_station)
    assert response is True


def test_invalid_station_and_port_fields(validation_options_for_federally_funded_station, mock_config):
    invalid_station_data = {
        'state': 'california',
        'NEVI': "invalid_string",
        'fed_funded_ports': [{'port_id': '', 'port_type': 'DCFC'}],
        'non_fed_funded_ports': [{'port_id': '', 'port_type': ''}],
    }

    validation_options_for_federally_funded_station["station"].update(invalid_station_data)
    response = validate_station_datatypes(validation_options_for_federally_funded_station)
    error_list = response["validate_station_datatypes()"]
    assert len(error_list) == 4
    for error_obj in error_list:
        assert error_obj.get("header_name") in ["state", "NEVI", "port_id"]


# JE-7047 nickname field is allowed to be empty for post patch stations since it is a recommended field
def test_valid_nickname_field_for_patch_stations(validation_options_for_federally_funded_station, mock_config):
    valid_nickname = { "nickname": ""}
    validation_options_for_federally_funded_station['station'].update(valid_nickname)
    response = validate_station_datatypes(validation_options_for_federally_funded_station)
    assert response is True