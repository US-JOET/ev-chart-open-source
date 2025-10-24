from unittest.mock import patch, MagicMock
import datetime

from APIGetDashboardPPFederallyFundedNetworkSize.index import (  # type: ignore
    count_section2_network,
    get_federally_funded_station_ports,
    get_station_registrations,
)


def test_get_federally_funded_station_ports():
    mock_cursor = MagicMock()

    get_federally_funded_station_ports(
        mock_cursor, {"dr_id": "All", "sr_id": "All", "station": "All", "year": "2024"}
    )
    execute_args, execute_kwargs = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_kwargs == {}

    get_federally_funded_station_ports(
        mock_cursor, {"dr_id": "dr123", "sr_id": "All", "station": "All", "year": "2024"}
    )
    execute_args, execute_kwargs = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_kwargs == {}

    get_federally_funded_station_ports(
        mock_cursor, {"dr_id": "All", "sr_id": "sr123", "station": "All", "year": "2024"}
    )
    execute_args, execute_kwargs = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_kwargs == {}

    get_federally_funded_station_ports(
        mock_cursor, {"dr_id": "dr123", "sr_id": "sr123", "station": "All", "year": "2024"}
    )
    execute_args, execute_kwargs = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_kwargs == {}


@patch("APIGetDashboardPPFederallyFundedNetworkSize.index.execute_query_with_filters")
def test_station_registrations(mock_execute_query_with_filters):
    mock_execute_query_with_filters.return_value = (("2024/04/18", "abc123"),)

    response = get_station_registrations(
        cursor=MagicMock(),
        filters={"dr_id": "All", "sr_id": "All", "year": "2024", "station": "All"},
    )
    assert len(response) == 1
    assert response[0]["operational_date"] == "2024/04/18"
    assert response[0]["station_uuid"] == "abc123"


def test_count_section2_network():
    operational_date = datetime.date(year=2022, month=4, day=18)
    station_registrations_sample = [
        {"operational_date": operational_date, "station_uuid": "online1"},
        {"operational_date": None, "station_uuid": "offline0"},
    ]
    station_ports_sample = [
        {"operational_date": operational_date, "port_type": "L2"},
        {"operational_date": operational_date, "port_type": "L2"},
        {"operational_date": operational_date, "port_type": "L2"},
        {"operational_date": operational_date, "port_type": "DCFC"},
        {"operational_date": operational_date, "port_type": "DCFC"},
        {"operational_date": operational_date, "port_type": ""},
    ]

    response = count_section2_network(station_registrations_sample, station_ports_sample)
    assert response.get("total_stations") == 2
    assert response.get("total_ports") == 6
    assert response.get("l2_ports") == 3
    assert response.get("dcfc_ports") == 2
    assert response.get("undefined_ports") == 1


# JE-6324 bug fix for year filtering
def test_count_section2_network_year_filter():
    old_operational_date = datetime.date(year=2022, month=4, day=18)
    current_operational_date = datetime.date(year=2024, month=4, day=18)
    station_registrations_sample = [
        {"operational_date": old_operational_date, "station_uuid": "online1"},
        {"operational_date": current_operational_date, "station_uuid": "online1"},
        {"operational_date": None, "station_uuid": "offline0"},
    ]
    station_ports_sample = [
        {"operational_date": current_operational_date, "port_type": "L2"},
        {"operational_date": current_operational_date, "port_type": "L2"},
        {"operational_date": current_operational_date, "port_type": "L2"},
        {"operational_date": old_operational_date, "port_type": "DCFC"},
        {"operational_date": old_operational_date, "port_type": "DCFC"},
        {"operational_date": old_operational_date, "port_type": ""},
    ]

    response = count_section2_network(station_registrations_sample, station_ports_sample)
    assert response.get("total_stations") == 3
    assert response.get("total_ports") == 6
    assert response.get("l2_ports") == 3
    assert response.get("dcfc_ports") == 2
    assert response.get("undefined_ports") == 1

    full_response = count_section2_network(station_registrations_sample, station_ports_sample)
    assert full_response.get("total_stations") == 3
    assert full_response.get("total_ports") == 6
    assert full_response.get("l2_ports") == 3
    assert full_response.get("dcfc_ports") == 2
    assert full_response.get("undefined_ports") == 1
