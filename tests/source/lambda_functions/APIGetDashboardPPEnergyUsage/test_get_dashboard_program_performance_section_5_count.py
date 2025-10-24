from decimal import Decimal
from unittest.mock import patch, MagicMock

from APIGetDashboardPPEnergyUsage.index import (  # type: ignore
    charging_sessions,
    count_section5_energy
)


@patch("APIGetDashboardPPEnergyUsage.index.federally_funded_ports")
def test_count_section5_energy(mock_federally_funded_ports):
    mock_federally_funded_ports.return_value = set({("station1", "fed-funded-1")})
    charging_sessions_sample = [
        {
            "session_duration": Decimal(12.0),
            "energy_kwh": Decimal(5.0),
            "power_kw": Decimal(200.0),
            "port_id": "fed-funded-1",
            "station_uuid": "station1",
            "nevi": 1,
        },
        {
            "session_duration": Decimal(-12.0),
            "energy_kwh": Decimal(5.0),
            "power_kw": Decimal(200.0),
            "port_id": "fed-funded-1",
            "station_uuid": "station1",
            "nevi": 1,
        },
    ]

    response = count_section5_energy(MagicMock(), charging_sessions_sample)
    assert response.get("total_charging_sessions") == 1
    assert response.get("total_charging_power") == 200.0
    assert response.get("cumulative_energy_federal_ports") == 5.0
    assert response.get("dispensing_150kw_sessions") == 1
    assert response.get("energy_metrics_available")
    assert not response.get("stdev_charging_session")


@patch("APIGetDashboardPPEnergyUsage.index.federally_funded_ports")
def test_count_section5_energy_only_negative_duration(mock_federally_funded_ports):
    mock_federally_funded_ports.return_value = set({("station1", "fed-funded-1")})
    charging_sessions_sample = [
        {
            "session_duration": Decimal(-11.0),
            "energy_kwh": Decimal(5.0),
            "power_kw": Decimal(200.0),
            "port_id": "fed-funded-1",
            "station_uuid": "station1",
            "nevi": 1,
        },
        {
            "session_duration": Decimal(-12.0),
            "energy_kwh": Decimal(5.0),
            "power_kw": Decimal(200.0),
            "port_id": "fed-funded-1",
            "station_uuid": "station1",
            "nevi": 1,
        },
    ]

    response = count_section5_energy(MagicMock(), charging_sessions_sample)
    assert response.get("total_charging_sessions") == 0.0
    assert response.get("cumulative_energy_federal_ports") == 0.0
    assert response.get("dispensing_150kw_sessions") == 0.0
    assert response.get("average_charging_duration") is None
    assert response.get("average_charging_power") is None
    assert response.get("percentage_nevi_dispensing_150kw") is None
    assert response.get("median_charging_session") is None
    assert response.get("mode_charging_session") is None
    assert not response.get("energy_metrics_available")


def test_count_section5_standard_deviation():
    charging_sessions_sample = [
        {
            "session_duration": Decimal(12.0),
            "energy_kwh": Decimal(5.0),
            "power_kw": Decimal(200.0),
            "port_id": "fed-funded-1",
            "station_uuid": "station1",
            "nevi": 1,
        },
        {
            "session_duration": Decimal(14.0),
            "energy_kwh": Decimal(5.0),
            "power_kw": Decimal(200.0),
            "port_id": "fed-funded-1",
            "station_uuid": "station1",
            "nevi": 1,
        },
    ]

    response = count_section5_energy(MagicMock(), charging_sessions_sample)
    assert response.get("stdev_charging_session") == round(Decimal(1.41), 2)


def test_count_section5_with_null_session_duration_standard_deviation():
    charging_sessions_sample = [
        {
            "session_duration": Decimal(12.0),
            "energy_kwh": Decimal(5.0),
            "power_kw": Decimal(200.0),
            "port_id": "fed-funded-1",
            "station_uuid": "station1",
            "nevi": 1,
        },
        {
            "session_duration": Decimal(14.0),
            "energy_kwh": Decimal(5.0),
            "power_kw": Decimal(200.0),
            "port_id": "fed-funded-1",
            "station_uuid": "station1",
            "nevi": 1,
        },
        {
            "session_duration": None,
            "energy_kwh": Decimal(5.0),
            "power_kw": Decimal(200.0),
            "port_id": "fed-funded-1",
            "station_uuid": "station1",
            "nevi": 1,
        },
    ]

    response = count_section5_energy(MagicMock(), charging_sessions_sample)
    assert response.get("stdev_charging_session") == round(Decimal(1.41), 2)


def test_count_section5_energy_cost_zero_division_error():
    response = count_section5_energy(MagicMock(), [])
    assert response.get("total_charging_sessions") == 0.0
    assert response.get("cumulative_energy_federal_ports") == 0.0
    assert response.get("dispensing_150kw_sessions") == 0.0
    assert response.get("average_charging_duration") is None
    assert response.get("average_charging_power") is None
    assert response.get("percentage_nevi_dispensing_150kw") is None
    assert response.get("median_charging_session") is None
    assert response.get("mode_charging_session") is None
    assert not response.get("energy_metrics_available")

def test_charging_sessions():
    mock_cursor = MagicMock()

    charging_sessions(
        cursor=mock_cursor,
        filters={"dr_id": "dr123", "sr_id": "sr123", "year": "2024", "station": "All"},
    )
    execute_args, execute_kwargs = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_kwargs == {}

    charging_sessions(
        cursor=mock_cursor,
        filters={"dr_id": "dr123", "sr_id": "sr123", "year": "2024", "station": "All"},
    )
    execute_args, execute_kwargs = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_kwargs == {}

