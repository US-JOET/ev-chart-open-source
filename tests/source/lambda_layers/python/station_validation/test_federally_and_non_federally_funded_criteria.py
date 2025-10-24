from unittest.mock import patch
import pytest
import pandas as pd

from station_validation.validate_federally_and_non_federally_funded_criteria import (
    validate_funding_type,
    validate_port_equality,
    validate_port_logic_against_fed_funded_criteria,
    validate_federally_and_non_federally_funded_station
)

from feature_toggle.feature_enums import Feature

def get_port_info():
    return {
        "num_fed_funded_ports": 1,
        "num_non_fed_funded_ports": 1,
        "fed_funded_ports": [{"port_id": "1", "type": "DCFC"}],
        "non_fed_funded_ports": [{"port_id": "3", "type": "DCFC"}],
        "station_uuid": "123",
        "federally_funded": True
    }



@pytest.mark.parametrize("feature_toggle_set", [{}, {Feature.REGISTER_NON_FED_FUNDED_STATION}])
def test_creating_fed_funded_station_with_no_funding_type_invalid(feature_toggle_set, validation_options_for_federally_funded_station):
    station = validation_options_for_federally_funded_station.get("station")
    validation_options_for_federally_funded_station["feature_toggle_set"] = feature_toggle_set
    station["NEVI"]= 0
    station["CFI"]= 0
    station["EVC_RAA"]= 0
    station["CMAQ"]= 0
    station["CRP"]= 0
    station["OTHER"]= 0
    response = validate_funding_type(validation_options_for_federally_funded_station)
    assert response is not True


def test_creating_non_fed_funded_station_with_no_funding_type_valid(validation_options_for_non_federally_funded_station):
    station = validation_options_for_non_federally_funded_station.get("station")
    validation_options_for_non_federally_funded_station["feature_toggle_set"] = {Feature.REGISTER_NON_FED_FUNDED_STATION}
    station["num_fed_funded_ports"] = 0
    station["fed_funded_ports"] = []
    station["NEVI"]= 0
    station["CFI"]= 0
    station["EVC_RAA"]= 0
    station["CMAQ"]= 0
    station["CRP"]= 0
    station["OTHER"]= 0
    assert validate_funding_type(validation_options_for_non_federally_funded_station) == ''


@pytest.mark.parametrize("feature_toggle_set", [{}, {Feature.REGISTER_NON_FED_FUNDED_STATION}])
@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query_df")
def test_updating_fed_funded_station_setting_all_funding_types_to_0_invalid_400(mock_df, feature_toggle_set, validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["feature_toggle_set"] = feature_toggle_set
    validation_options_for_federally_funded_station["api"] = "patch"
    # simulating changing the funding types to 0 for that station
    validation_options_for_federally_funded_station["station"] ={
        "station_uuid": "123-123",
        "NEVI": 0,
        "CFI": 0,
        "EVC_RAA": 0,
        "CMAQ": 0,
        "CRP": 0,
        "OTHER": 0,
    }

    data_in_table = {
        "NEVI": [1],
        "CFI": [1],
        "EVC_RAA": [1],
        "CMAQ": [1],
        "CRP": [1],
        "OTHER": [1]
    }

    mock_df.return_value = pd.DataFrame(data_in_table)
    response = validate_funding_type(validation_options_for_federally_funded_station)
    assert response is not True


@pytest.mark.parametrize("feature_toggle_set", [{}, {Feature.REGISTER_NON_FED_FUNDED_STATION}])
@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query_df")
def test_setting_all_funding_types_to_0_for_non_fed_station_valid_200(mock_df, feature_toggle_set, validation_options_for_non_federally_funded_station):
    validation_options_for_non_federally_funded_station["feature_toggle_set"] = feature_toggle_set
    validation_options_for_non_federally_funded_station["api"] = "patch"
    # simulating changing the funding types to 0 for that station
    validation_options_for_non_federally_funded_station["station"] ={
        "station_uuid": "123-123",
        "NEVI": "0",
        "CFI": "0",
        "EVC_RAA": "0",
        "CMAQ": "0",
        "CRP": "0",
        "OTHER": "0",
        "num_fed_funded_ports": "0",
        "fed_funded_ports": []
    }

    data_in_table = {
        "NEVI": [1],
        "CFI": [1],
        "EVC_RAA": [1],
        "CMAQ": [1],
        "CRP": [1],
        "OTHER": [1]
    }

    mock_df.return_value = pd.DataFrame(data_in_table)
    assert validate_funding_type(validation_options_for_non_federally_funded_station) == ''


@pytest.mark.parametrize("feature_toggle_set", [{}, {Feature.REGISTER_NON_FED_FUNDED_STATION}])
@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query_df")
def test_deselecting_funding_type_but_other_option_still_picked_valid_200(
    mock_df, feature_toggle_set, validation_options_for_federally_funded_station
):
    validation_options_for_federally_funded_station["feature_toggle_set"] = feature_toggle_set
    validation_options_for_federally_funded_station["api"] = "patch"
    # simulating changing the funding types to 0 for that station
    validation_options_for_federally_funded_station["station"] ={
        "station_uuid": "123-123",
        "federally_funded": True,
        "NEVI": 0
    }

    data_in_table = {
        "NEVI": [1],
        "CFI": [0],
        "EVC_RAA": [0],
        "CMAQ": [0],
        "CRP": [0],
        "OTHER": [1]
    }

    mock_df.return_value = pd.DataFrame(data_in_table)
    assert validate_funding_type(validation_options_for_federally_funded_station) == ''


@pytest.mark.parametrize("api", ("post","patch"))
@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query_df")
def test_invalid_fed_funded_station_funding_type_selected(mock_df, api, validation_options_for_federally_funded_station):
    station_updates = {
        'station_uuid': '132456',
        'federally_funded': True,
        'NEVI': 0,
        'CFI': 0,
        'EVC_RAA': 0,
        'CMAQ': 0,
        'CRP': 0,
        'OTHER': 0
    }
    validation_options_for_federally_funded_station["api"] = api
    validation_options_for_federally_funded_station.get("station").update(station_updates)
    data_in_table = {
        "NEVI": [1],
        "CFI": [1],
        "EVC_RAA": [1],
        "CMAQ": [1],
        "CRP": [1],
        "OTHER": [1]
    }

    mock_df.return_value = pd.DataFrame(data_in_table)
    response = validate_funding_type(validation_options_for_federally_funded_station)
    assert response == "Funding Type is a required field for federally funded stations and 1 option must be selected. "


@pytest.mark.parametrize("api", ("post","patch"))
@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query_df")
def test_invalid_non_fed_funded_station_funding_type_selected(mock_df, api, validation_options_for_non_federally_funded_station):
    station_updates = {
        'station_uuid': '132456',
        'federally_funded': False,
        'NEVI': 1,
        'CFI': 0,
        'EVC_RAA': 0,
        'CMAQ': 0,
        'CRP': 0,
        'OTHER': 0
    }
    validation_options_for_non_federally_funded_station["api"] = api
    validation_options_for_non_federally_funded_station.get("station").update(station_updates)
    data_in_table = {
        "NEVI": [0],
        "CFI": [0],
        "EVC_RAA": [0],
        "CMAQ": [0],
        "CRP": [0],
        "OTHER": [0]
    }

    mock_df.return_value = pd.DataFrame(data_in_table)
    response = validate_funding_type(validation_options_for_non_federally_funded_station)
    assert response == "Funding Type should not be selected for non-federally funded stations. "


def test_updating_federal_funded_ports_and_num_but_values_provided_are_not_equal(validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "post"
    station_values = get_port_info()
    station_values["num_fed_funded_ports"] = 0
    validation_options_for_federally_funded_station["station"] = station_values
    response = validate_port_equality(validation_options_for_federally_funded_station)
    assert response == "Number of federal funded ports must match the federal ports provided.Must have at least 1 federally funded port on record in order to be considered a federally funded station. "


def test_updating_non_federal_funded_ports_and_num_but_values_provided_are_not_equal(validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "post"
    station_values = get_port_info()
    station_values["num_non_fed_funded_ports"] = 4
    validation_options_for_federally_funded_station["station"] = station_values
    response = validate_port_equality(validation_options_for_federally_funded_station)
    assert response == "Number of non-federal funded ports must match the non-federal ports provided."

def test_updating_all_port_information_valid(validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "post"
    station_values = get_port_info()
    validation_options_for_federally_funded_station["station"] = station_values
    validate_port_equality(validation_options_for_federally_funded_station) is True


@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query")
def test_updating_federal_funded_ports_only_but_num_ports_in_db_are_not_equal(mock_query, validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "patch"
    station_values= {
        "station_uuid": "123",
        "federally_funded": True,
        "fed_funded_ports": [
            {"port_id": "1", "type": "DCFC"},
            {"port_id": "2", "type": "DCFC"}
        ]
    }
    mock_query.return_value = [
        {
            "num_non_fed_funded_ports": 2,
            "non_fed_funded_ports": 2,
            "num_fed_funded_ports": 1,
            "fed_funded_ports": 1,
        }
    ]
    validation_options_for_federally_funded_station["station"] = station_values
    response = validate_port_equality(validation_options_for_federally_funded_station)
    assert response == "Number of federal funded ports must match the federal ports provided."


@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query")
def test_updating_num_federal_funded_ports_only_but_acutal_ports_in_db_are_not_equal(mock_query, validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "patch"
    station_values = {
        "station_uuid": "123",
        "num_fed_funded_ports": 3,
        "federally_funded": True
    }
    validation_options_for_federally_funded_station["station"] = station_values
    mock_query.return_value = [
        {
            "num_non_fed_funded_ports": 2,
            "non_fed_funded_ports": 2,
            "num_fed_funded_ports": 2,
            "fed_funded_ports": 2,
        }
    ]
    response = validate_port_equality(validation_options_for_federally_funded_station)
    assert response == "Number of federal funded ports must match the federal ports provided."


@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query")
def test_patching_both_num_and_ports_array_valid(mock_query, validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "patch"
    station_values = {
        "num_fed_funded_ports": 1,
        "fed_funded_ports": [{"port_id": "1", "type": "DCFC"}],
        "num_non_fed_funded_ports": 1,
        "non_fed_funded_ports": [{"port_id": "2", "type": "DCFC"}],
        "station_uuid": "123",
        "federally_funded": True
    }
    validation_options_for_federally_funded_station["station"] = station_values
    mock_query.return_value = [
        {
            "num_non_fed_funded_ports": 2,
            "non_fed_funded_ports": 2,
            "num_fed_funded_ports": 2,
            "fed_funded_ports": 2,
        }
    ]
    assert validate_port_equality(validation_options_for_federally_funded_station) == ''


@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query")
def test_valid_replacement_of_one_port(mock_query, validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "patch"
    station_values = {
        "fed_funded_ports": [{"port_id": "1", "type": "DCFC"}] ,
        "station_uuid": "123",
        "federally_funded": True
    }
    station_values["fed_funded_ports"] = "1"
    mock_query.return_value = [
        {
            "num_non_fed_funded_ports": None,
            "non_fed_funded_ports": 0,
            "num_fed_funded_ports": 1,
            "fed_funded_ports": 1,
        }
    ]
    validation_options_for_federally_funded_station["station"] = station_values
    assert validate_port_equality(validation_options_for_federally_funded_station) == ''


@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query")
def test_patching_both_ports_array_do_not_match_db_values(mock_query, validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "patch"
    station_values = {
        "fed_funded_ports": [{"port_id": "1", "type": "DCFC"}],
        "non_fed_funded_ports": [{"port_id": "2", "type": "DCFC"}],
        "station_uuid": "123",
        "federally_funded": True
    }
    validation_options_for_federally_funded_station["station"] = station_values
    mock_query.return_value = [
        {
            "num_non_fed_funded_ports": 3,
            "non_fed_funded_ports": 3,
            "num_fed_funded_ports": 2,
            "fed_funded_ports": 2,
        }
    ]
    response = validate_port_equality(validation_options_for_federally_funded_station)
    assert response == "Number of federal funded ports must match the federal ports provided.Number of non-federal funded ports must match the non-federal ports provided."


@pytest.mark.parametrize(
    "api, num_fed, fed_list, num_non_fed, non_fed_list, fed_type_error",
    [
        # num federal stations not equal to ports provided
        ("post", "2", [{"port_id": "2", "type": "DCFC"}], "1", [{"port_id": "1", "type": "DCFC"}], "federal"),
        ("patch", "2", [{"port_id": "2", "type": "DCFC"}], "1", [{"port_id": "1", "type": "DCFC"}], "federal"),
        # num non-federal stations not equal to ports provided
        ("post", "1", [{"port_id": "2", "type": "DCFC"}], "3", [{"port_id": "1", "type": "DCFC"}], "non-federal"),
        ("patch", "1", [{"port_id": "2", "type": "DCFC"}], "3", [{"port_id": "1", "type": "DCFC"}], "non-federal")
    ]
)
@patch("station_validation.validate_federally_and_non_federally_funded_criteria.execute_query")
def test_number_of_ports_does_not_match_ports_provided_in_new_data(mock_query, api, num_fed, fed_list, num_non_fed, non_fed_list, fed_type_error, validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = api
    station_values = {
        "num_fed_funded_ports": num_fed,
        "fed_funded_ports": fed_list,
        "num_non_fed_funded_ports": num_non_fed,
        "non_fed_funded_ports": non_fed_list,
        "station_uuid": "123",
        "federally_funded": True
    }
    validation_options_for_federally_funded_station["station"] = station_values
    mock_query.return_value = [
        {
            "num_non_fed_funded_ports": 3,
            "non_fed_funded_ports": 3,
            "num_fed_funded_ports": 1,
            "fed_funded_ports": 1,
        }
    ]
    response = validate_port_equality(validation_options_for_federally_funded_station)
    assert response == f"Number of {fed_type_error} funded ports must match the {fed_type_error} ports provided."


def test_verify_fed_non_fed_port_validity(validation_options_for_federally_funded_station, validation_options_for_non_federally_funded_station):
    assert validate_port_equality(validation_options_for_federally_funded_station) == ''
    assert validate_port_equality(validation_options_for_non_federally_funded_station) == ''


def test_federally_funded_station_submits_no_non_federal_ports_valid(validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "post"
    station_values = get_port_info()
    station_values["num_non_fed_funded_ports"] = None
    station_values["non_fed_funded_ports"] = []
    validation_options_for_federally_funded_station["station"] = station_values
    assert validate_port_equality(validation_options_for_federally_funded_station) == ''


def test_non_federally_funded_station_submits_no_federal_ports_valid(validation_options_for_non_federally_funded_station):
    validation_options_for_non_federally_funded_station["api"] = "post"
    station_values = get_port_info()
    station_values["num_fed_funded_ports"] = None
    station_values["fed_funded_ports"] = []
    validation_options_for_non_federally_funded_station["station"] = station_values
    assert validate_port_equality(validation_options_for_non_federally_funded_station)


@pytest.mark.parametrize(
    "num_fed, fed, num_non_fed, non_fed, federally_funded",
    [
        (1,1,0,0,True),
        (1,1,1,1,True),
        (0,0,1,1,False)
    ]
)
def test_valid_ports_for_fed_and_non_fed_funded_station(num_fed, fed, num_non_fed, non_fed, federally_funded):
    port_logic = {
        "num_fed_funded_ports": num_fed,
        "fed_funded_ports": fed,
        "num_non_fed_funded_ports": num_non_fed,
        "non_fed_funded_ports": non_fed
    }
    assert validate_port_logic_against_fed_funded_criteria(federally_funded=federally_funded, cross_check=port_logic) == ""


@pytest.mark.parametrize(
    "num_fed, fed, num_non_fed, non_fed, federally_funded, error_message",
    [
        (0,0,1,1,True, "Must have at least 1 federally funded port on record in order to be considered a federally funded station. "),
        (1,1,1,1,False, "Cannot have any federally funded ports on record in order to be considered a non-federally funded station. "),
        (0,0,0,0,False, "Must have at least 1 non-federally funded port on record in order to be considered a non-federally funded station. "),
        (1,1,0,0, False, "Cannot have any federally funded ports on record in order to be considered a non-federally funded station. Must have at least 1 non-federally funded port on record in order to be considered a non-federally funded station. ")
    ]
)
def test_invalid_ports_for_fed_and_non_fed_funded_station(num_fed, fed, num_non_fed, non_fed, federally_funded, error_message):
    port_logic = {
        "num_fed_funded_ports": num_fed,
        "fed_funded_ports": fed,
        "num_non_fed_funded_ports": num_non_fed,
        "non_fed_funded_ports": non_fed
    }
    assert validate_port_logic_against_fed_funded_criteria(federally_funded=federally_funded, cross_check=port_logic) == error_message


def test_validate_federally_and_non_federally_funded_no_change_to_station_type(validation_options_for_federally_funded_station):
    validation_options_for_federally_funded_station["api"] = "patch"
    station_values = {
        "station_uuid": "123",
        "city": "San Diego",
        "federally_funded": True
    }
    validation_options_for_federally_funded_station["station"] = station_values
    assert validate_federally_and_non_federally_funded_station(validation_options_for_federally_funded_station) is True


def test_validate_federally_and_non_federally_funded_station_no_errors(validation_options_for_federally_funded_station, validation_options_for_non_federally_funded_station):
    assert validate_federally_and_non_federally_funded_station(validation_options_for_federally_funded_station) is True
    assert validate_federally_and_non_federally_funded_station(validation_options_for_non_federally_funded_station) is True


def test_invalid_port_equality_and_funding_type_for_station(validation_options_for_federally_funded_station):
    station_updates = {
        'NEVI': 0,
        'CFI': 0,
        'EVC_RAA': 0,
        'CMAQ': 0,
        'CRP': 0,
        'OTHER': 0,
        'num_fed_funded_ports': "0",
        'fed_funded_ports': []
    }
    validation_options_for_federally_funded_station.get("station").update(station_updates)
    response = validate_federally_and_non_federally_funded_station(validation_options_for_federally_funded_station)
    assert response == {
                "validate_federally_and_non_federally_funded_station()": (
                    "Invalid attributes for federally funded station. Funding Type is a required field for federally funded stations and 1 option must be selected. Must have at least 1 federally funded port on record in order to be considered a federally funded station. "
                )
            }

def test_invalid_non_fed_funded_station_no_non_fed_ports_listed(validation_options_for_non_federally_funded_station):
    station_updates = {
        'num_non_fed_funded_ports': 0,
        'non_fed_funded_ports': [],
        'num_fed_funded_ports': 1,
        'fed_funded_ports': [{"port_id": "1", "type": "DCFC"}]
    }
    validation_options_for_non_federally_funded_station.get("station").update(station_updates)
    response = validate_federally_and_non_federally_funded_station(validation_options_for_non_federally_funded_station)
    assert response == {
        "validate_federally_and_non_federally_funded_station()": (
            "Invalid attributes for non-federally funded station. Cannot have any federally funded ports on record in order to be considered a non-federally funded station. Must have at least 1 non-federally funded port on record in order to be considered a non-federally funded station. "
        )
    }