from unittest.mock import patch, MagicMock
from decimal import Decimal
import datetime
import pandas
import pytest


from APIGetDashboardProgramPerformance.index import (  # type: ignore
    capital_costs,
    charging_sessions,
    count_section2_network,
    count_section3_reliability,
    count_section4_capital_cost,
    count_section4_maintenance_cost,
    count_section5_energy,
    execute_query_with_filters,
    get_outage_data,
    get_federally_funded_station_ports,
    get_station_registrations,
    federally_funded_ports,
    get_prior_quarter_window,
    normalized_monthly_cost,
    operational_days,
)
from evchart_helper.custom_exceptions import EvChartMissingOrMalformedHeadersError


def test_federally_funded_ports_cache():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = (("station1", "port1"),)
    assert ("station1", "port1") in federally_funded_ports(mock_cursor)
    assert federally_funded_ports.cache_info().hits == 0

    assert ("station1", "port1") in federally_funded_ports(mock_cursor)
    assert federally_funded_ports.cache_info().hits == 1


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


@patch("APIGetDashboardProgramPerformance.index.execute_query_with_filters")
def test_station_registrations(mock_execute_query_with_filters):
    mock_execute_query_with_filters.return_value = (("2024/04/18", "abc123"),)

    response = get_station_registrations(
        cursor=MagicMock(),
        filters={"dr_id": "All", "sr_id": "All", "year": "2024", "station": "All"},
    )
    assert len(response) == 1
    assert response[0]["operational_date"] == "2024/04/18"
    assert response[0]["station_uuid"] == "abc123"


@patch("APIGetDashboardProgramPerformance.index.execute_query_with_filters")
def test_outage_data(mock_execute_query_with_filters):
    mock_execute_query_with_filters.return_value = ((Decimal(12.341),),)
    assert get_outage_data(MagicMock(), "All") == 12.34


@patch("APIGetDashboardProgramPerformance.index.execute_query_with_filters")
def test_outage_data_nonetype(mock_execute_query_with_filters):
    mock_execute_query_with_filters.return_value = ((None,),)
    assert get_outage_data(MagicMock(), "All") is None


@patch("APIGetDashboardProgramPerformance.index.execute_query_with_filters")
def test_capital_costs(mock_execute_query_with_filters):
    capital_costs_one_row = tuple(["abc123"] + [float(x) for x in range(17)])
    mock_execute_query_with_filters.return_value = (capital_costs_one_row,)

    response = capital_costs(MagicMock(), "dr123")
    assert len(response) == 1
    assert response[0].get("dist_sys_cost_federal") == 8.0


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


@pytest.mark.skip("deprecated in JE-5771, remove in future")
@patch("APIGetDashboardProgramPerformance.index.get_prior_quarter_window")
def test_count_section3_reliability(mock_prior_quarter_window):
    mock_prior_quarter_window.return_value = {
        "start": datetime.date(year=2023, month=10, day=1),
        "end": datetime.date(year=2024, month=9, day=30),
    }
    port_data_sample = [
        {
            "station_uuid": "a1",
            "port_uuid": "p1",
            "port_type": "L2",
            "operational_date": datetime.date(year=2024, month=7, day=1),
            "uptime_reporting_end": datetime.date(year=2024, month=10, day=1),
            "uptime": Decimal(96),
        },
        {
            "station_uuid": "a1",
            "port_uuid": "b1",
            "port_type": "L2",
            "operational_date": datetime.date(year=2024, month=7, day=1),
            "uptime_reporting_end": datetime.date(year=2024, month=11, day=1),
            "uptime": Decimal(97),
        },
        {
            "station_uuid": "c3",
            "port_uuid": "p3",
            "port_type": "L2",
            "operational_date": datetime.date(year=2024, month=7, day=1),
            "uptime_reporting_end": datetime.date(year=2024, month=11, day=1),
            "uptime": Decimal(99),
        },
        {
            "station_uuid": "d4",
            "port_uuid": "p4",
            "port_type": "DCFC",
            "operational_date": datetime.date(year=2024, month=7, day=1),
            "uptime_reporting_end": datetime.date(year=2024, month=11, day=1),
            "uptime": Decimal(95),
        },
        {
            "station_uuid": "e5",
            "port_uuid": "p5",
            "port_type": "DCFC",
            "operational_date": datetime.date(year=2023, month=7, day=1),
            "uptime_reporting_end": datetime.date(year=2024, month=11, day=1),
            "uptime": Decimal(100),
        },
    ]

    response = count_section3_reliability(port_data_sample)
    assert response.get("total_ports_with_uptime_activity") == 5
    assert response.get("num_ports_meeting_uptime_req") == 3
    assert response.get("num_l2_chargers_not_meeting_req") == 1
    assert response.get("num_dcfc_chargers_not_meeting_req") == 1
    assert response.get("percentage_ports_meeting_uptime_req") == 0.6
    assert response.get("percentage_ports_not_meeting_uptime_req") == 0.4


@pytest.mark.skip("deprecated in JE-5771, remove in future")
@patch("APIGetDashboardProgramPerformance.index.get_prior_quarter_window")
def test_count_section3_null_outage_duration(mock_prior_quarter_window):
    mock_prior_quarter_window.return_value = {
        "start": datetime.date(year=2023, month=10, day=1),
        "end": datetime.date(year=2024, month=9, day=30),
    }
    port_data_sample = [
        {
            "station_uuid": "a1",
            "port_uuid": "p1",
            "port_type": "L2",
            "operational_date": datetime.date(year=2024, month=7, day=1),
            "outage_id": datetime.datetime(year=2024, month=7, day=2),
            # skip if outage_duration is null
            "outage_duration": None,
        },
        {
            # skip because outage_id is later than EOQ
            "station_uuid": "b2",
            "port_uuid": "p2",
            "port_type": "L2",
            "operational_date": datetime.date(year=2024, month=7, day=1),
            "outage_id": datetime.datetime(year=2024, month=11, day=3),
            "outage_duration": Decimal(92.0),
        },
        {
            "station_uuid": "c3",
            "port_uuid": "p3",
            "port_type": "L2",
            "operational_date": datetime.date(year=2024, month=7, day=1),
            "outage_id": datetime.datetime(year=2024, month=7, day=2),
            # more minutes than any quarter
            "outage_duration": Decimal(1500 * 100),
        },
        {
            "station_uuid": "d4",
            "port_uuid": "p4",
            "port_type": "DCFC",
            "operational_date": datetime.date(year=2024, month=7, day=1),
            "outage_id": datetime.datetime(year=2024, month=7, day=2),
            # more minutes than any quarter
            "outage_duration": Decimal(1500 * 100),
        },
    ]
    response = count_section3_reliability(port_data_sample)
    assert response.get("total_ports_with_uptime_activity") == 2
    assert response.get("num_ports_meeting_uptime_req") == 0
    assert response.get("num_l2_chargers_not_meeting_req") == 1
    assert response.get("num_dcfc_chargers_not_meeting_req") == 1
    assert response.get("percentage_ports_meeting_uptime_req") == 0
    assert response.get("percentage_ports_not_meeting_uptime_req") == 1.0


def test_count_section3_reliability_no_records():
    response = count_section3_reliability([])
    assert response.get("total_ports_with_uptime_activity") == 0
    assert response.get("percentage_ports_meeting_uptime_req") is None
    assert response.get("percentage_ports_not_meeting_uptime_req") is None
    assert not response.get("reliability_metrics_available")


def test_count_section4_capital_cost():
    capital_costs_sample = [
        {
            "nevi": 1,
            "station_uuid": "nevi1",
            "der_cost_total": Decimal(12.0),
            "der_cost_federal": Decimal(9.0),
            "der_install_cost_total": Decimal(12.0),
            "der_install_cost_federal": Decimal(9.0),
            "distribution_cost_total": Decimal(12.0),
            "distribution_cost_federal": Decimal(9.0),
            "equipment_cost_total": Decimal(12.0),
            "equipment_cost_federal": Decimal(9.0),
            "equipment_install_cost_total": Decimal(12.0),
            "equipment_install_cost_federal": Decimal(9.0),
            "real_property_cost_total": Decimal(12.0),
            "real_property_cost_federal": Decimal(9.0),
            "service_cost_total": Decimal(12.0),
            "service_cost_federal": Decimal(9.0),
            "dist_sys_cost_total": Decimal(12.0),
            "dist_sys_cost_federal": Decimal(9.0),
        },
        {
            "nevi": 0,
            "station_uuid": "antinevi",
            "der_cost_total": None,
            "der_cost_federal": None,
            "der_install_cost_total": None,
            "der_install_cost_federal": None,
            "distribution_cost_total": None,
            "distribution_cost_federal": None,
            "equipment_cost_total": None,
            "equipment_cost_federal": None,
            "equipment_install_cost_total": None,
            "equipment_install_cost_federal": None,
            "real_property_cost_total": None,
            "real_property_cost_federal": None,
            "service_cost_total": None,
            "service_cost_federal": None,
            "dist_sys_cost_total": None,
            "dist_sys_cost_federal": None,
        },
    ]

    response = count_section4_capital_cost(capital_costs_sample)
    assert response["federal_funding"] == 36.0
    assert response["nonfederal_funding"] == 12.0
    assert response["capital_costs_total_nevi"] == 48.0
    assert response["average_nevi_capital_cost"] == 48.0
    assert response["capital_cost_metrics_available"]


def test_count_section4_capital_cost_zero_division_error():
    response = count_section4_capital_cost([])
    assert response["federal_funding"] == 0.0
    assert response["nonfederal_funding"] == 0.0
    assert response["capital_costs_total_nevi"] == 0.0
    assert response["average_nevi_capital_cost"] is None
    assert not response["capital_cost_metrics_available"]


def test_count_section4_maintenance_cost():
    maintenance_costs_sample = [
        {
            "station_uuid": "a1",
            "year": 2024,
            "operational_date": datetime.date(year=2024, month=1, day=1),
            "maintenance_cost_total": Decimal(360.0),
            # normalized monthly cost is 30.0
        },
        {
            "station_uuid": "b2",
            "year": 2024,
            "operational_date": datetime.date(year=2024, month=1, day=1),
            "maintenance_cost_total": Decimal(720.0),
            # normalized monthly cost is 60.0
        },
        {
            "station_uuid": "c3",
            "year": 2024,
            "operational_date": datetime.date(year=2026, month=5, day=14),
            "maintenance_cost_total": Decimal(24.0),
            # record will be skipped because operational_date is
            # later than reporting year
        },
    ]

    response = count_section4_maintenance_cost(maintenance_costs_sample)
    # average of 30.0 and 60.0 is 45.0
    assert response.get("monthly_avg_maintenance_repair_cost") == 45.0
    assert response.get("maintenance_cost_metrics_available")


def test_count_section4_maintenance_cost_zero_division_error():
    response = count_section4_maintenance_cost([])
    assert response.get("monthly_avg_maintenance_repair_cost") is None
    assert not response.get("maintenance_cost_metrics_available")


@patch("APIGetDashboardProgramPerformance.index.federally_funded_ports")
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


@patch("APIGetDashboardProgramPerformance.index.federally_funded_ports")
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


def test_group_by_clause():
    mock_cursor = MagicMock()

    execute_query_with_filters(
        cursor=mock_cursor,
        query="NOT A QUERY ",
        filters={"dr_id": "All", "sr_id": "All", "year": "2024", "station": "All"},
        group_by=["dr_id"],
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_args[0] == (
        "NOT A QUERY "
        " AND dr_id <> '154ecdd3-d864-4110-916b-9c1287bb31e8' "
        " AND year = %(year)s "
        " GROUP BY dr_id "
    )


def test_group_by_clause_year():
    mock_cursor = MagicMock()

    execute_query_with_filters(
        cursor=mock_cursor,
        query="NOT A QUERY ",
        filters={"dr_id": "All", "sr_id": "All", "year": "NA", "station": "All"},
        group_by=["dr_id"],
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_args[0] == (
        "NOT A QUERY "
        " AND dr_id <> '154ecdd3-d864-4110-916b-9c1287bb31e8' "
        " AND year = %(year)s "
        " GROUP BY dr_id "
    )


def test_group_by_clause_station():
    mock_cursor = MagicMock()

    execute_query_with_filters(
        cursor=mock_cursor,
        query="NOT A QUERY ",
        filters={"dr_id": "dr456", "sr_id": "sr789", "year": "NA", "station": "123"},
        group_by=["dr_id"],
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert len(execute_args) == 2
    assert execute_args[0] == (
        "NOT A QUERY "
        " AND dr_id = %(dr_id)s "
        " AND evchart_data_v3.station_registrations.station_uuid IN ( "
        "   SELECT station_uuid from evchart_data_v3.station_authorizations "
        "    WHERE dr_id = %(dr_id)s and sr_id = %(sr_id)s "
        ")  "
        "AND evchart_data_v3.station_registrations.station_uuid = %(station)s "
        " AND year = %(year)s "
        " GROUP BY dr_id "
    )


def test_group_by_clause_invalid_type():
    mock_cursor = MagicMock()

    with pytest.raises(EvChartMissingOrMalformedHeadersError):
        execute_query_with_filters(
            cursor=mock_cursor,
            query="NOT A QUERY ",
            filters={"dr_id": "All", "sr_id": "All", "year": "2024", "station": "All"},
            group_by="dr_id",
        )


def test_operational_days():
    # year in import_metadata is a varchar(4)
    assert operational_days(datetime.date(year=2023, month=12, day=1), reporting_year="2023") == 31
    assert (
        operational_days(
            operational_date=datetime.date(year=2023, month=1, day=2), reporting_year="2023"
        )
        == 364
    )
    assert (
        operational_days(
            operational_date=datetime.date(year=2023, month=1, day=1), reporting_year="2023"
        )
        == 365
    )
    assert (
        operational_days(
            operational_date=datetime.date(year=2023, month=12, day=31), reporting_year="2024"
        )
        == 365
    )
    assert (
        operational_days(
            operational_date=datetime.date(year=2025, month=4, day=18), reporting_year="2024"
        )
        == 0
    )

    # disregard leap years for now
    assert (
        operational_days(
            operational_date=datetime.date(year=2024, month=1, day=2), reporting_year="2024"
        )
        == 365
    )
    assert (
        operational_days(
            operational_date=datetime.date(year=2024, month=1, day=1), reporting_year="2024"
        )
        == 365
    )


def test_normalized_monthly_cost():
    assert normalized_monthly_cost(Decimal(360.0), 365) == pytest.approx(30.0)
    assert normalized_monthly_cost(Decimal(360.0), 182.5) == pytest.approx(60.0)
    assert normalized_monthly_cost(Decimal(360.0), 30) == pytest.approx(365.0)
    assert normalized_monthly_cost(Decimal(12.0), 1) == pytest.approx(365.0)


@pytest.mark.parametrize(
    "today,start,end",
    [
        (
            datetime.date(year=2023, month=12, day=31),
            datetime.date(year=2022, month=10, day=1),
            datetime.date(year=2023, month=9, day=30),
        ),
        (
            datetime.date(year=2024, month=1, day=1),
            datetime.date(year=2023, month=1, day=1),
            datetime.date(year=2023, month=12, day=31),
        ),
        (
            datetime.date(year=2024, month=3, day=31),
            datetime.date(year=2023, month=1, day=1),
            datetime.date(year=2023, month=12, day=31),
        ),
        (
            datetime.date(year=2024, month=4, day=1),
            datetime.date(year=2023, month=4, day=1),
            datetime.date(year=2024, month=3, day=31),
        ),
        (
            datetime.date(year=2024, month=6, day=30),
            datetime.date(year=2023, month=4, day=1),
            datetime.date(year=2024, month=3, day=31),
        ),
        (
            datetime.date(year=2024, month=7, day=1),
            datetime.date(year=2023, month=7, day=1),
            datetime.date(year=2024, month=6, day=30),
        ),
        (
            datetime.date(year=2024, month=9, day=30),
            datetime.date(year=2023, month=7, day=1),
            datetime.date(year=2024, month=6, day=30),
        ),
        (
            datetime.date(year=2024, month=10, day=1),
            datetime.date(year=2023, month=10, day=1),
            datetime.date(year=2024, month=9, day=30),
        ),
    ],
)
def test_prior_quarter(today, start, end):
    assert get_prior_quarter_window(today)["start"] == start
    assert get_prior_quarter_window(today)["end"] == end


def test_prior_quarter_cache():
    get_prior_quarter_window(datetime.date(2025, 2, 3))
    cache_hits = get_prior_quarter_window.cache_info().hits

    get_prior_quarter_window(datetime.date(2025, 2, 3))
    assert get_prior_quarter_window.cache_info().hits == cache_hits + 1


# JE-5445
def test_capital_costs_per_station():
    capital_costs_sample = [
        {
            "nevi": 1,
            "station_uuid": "1",
            "equipment_cost_total": Decimal(1.0),
            "equipment_cost_federal": Decimal(0.0),
            "equipment_install_cost_total": Decimal(1.0),
            "equipment_install_cost_federal": Decimal(0.0),
            "service_cost_total": Decimal(1.0),
            "service_cost_federal": Decimal(0.0),
            "dist_sys_cost_total": Decimal(1.0),
            "dist_sys_cost_federal": Decimal(0.0),
        },
        {
            "nevi": 1,
            "station_uuid": "2",
            "equipment_cost_total": Decimal(2.0),
            "equipment_cost_federal": Decimal(2.0),
            "equipment_install_cost_total": Decimal(2.0),
            "equipment_install_cost_federal": Decimal(2.0),
            "service_cost_total": Decimal(2.0),
            "service_cost_federal": Decimal(2.0),
            "dist_sys_cost_total": Decimal(2.0),
            "dist_sys_cost_federal": Decimal(2.0),
        },
        {
            "nevi": 0,
            "station_uuid": "3",
            "equipment_cost_total": Decimal(3.0),
            "equipment_cost_federal": Decimal(3.0),
            "equipment_install_cost_total": Decimal(3.0),
            "equipment_install_cost_federal": Decimal(3.0),
            "service_cost_total": Decimal(3.0),
            "service_cost_federal": Decimal(3.0),
            "dist_sys_cost_total": Decimal(3.0),
            "dist_sys_cost_federal": Decimal(0.0),
        },
        {
            "nevi": 1,
            "station_uuid": "4",
            "equipment_cost_total": None,
            "equipment_cost_federal": Decimal(0.0),
            "equipment_install_cost_total": None,
            "equipment_install_cost_federal": Decimal(0.0),
            "service_cost_total": None,
            "service_cost_federal": Decimal(0.0),
            "dist_sys_cost_total": None,
            "dist_sys_cost_federal": Decimal(0.0),
        },
        {
            "nevi": 1,
            "station_uuid": "5",
            "equipment_cost_total": None,
            "equipment_cost_federal": Decimal(0.0),
            "equipment_install_cost_total": Decimal(5.0),
            "equipment_install_cost_federal": Decimal(5.0),
            "service_cost_total": Decimal(5.0),
            "service_cost_federal": Decimal(5.0),
            "dist_sys_cost_total": Decimal(5.0),
            "dist_sys_cost_federal": Decimal(5.0),
        },
    ]

    df = pandas.DataFrame(capital_costs_sample)
    df = df[
        ~df[
            [
                "equipment_cost_total",
                "equipment_install_cost_total",
                "dist_sys_cost_total",
                "service_cost_total",
            ]
        ]
        .isnull()
        .any(axis=1)
    ]

    df["cost_station_capital_total"] = (
        df["equipment_cost_total"]
        + df["equipment_install_cost_total"]
        + df["dist_sys_cost_total"]
        + df["service_cost_total"]
    )

    df["cost_station_capital_federal"] = (
        df["equipment_cost_federal"]
        + df["equipment_install_cost_federal"]
        + df["dist_sys_cost_federal"]
        + df["service_cost_federal"]
    )

    nevi_df = df.copy()[df["nevi"] == 1]

    # calculation A
    assert sum(nevi_df["cost_station_capital_total"]) / len(nevi_df) == 6.0
    # calculation B
    assert sum(df["cost_station_capital_total"]) == 24.0
    # calculation E
    assert sum(df["cost_station_capital_federal"]) == 17.0

    assert len(df) == 3
    assert (sum(df["cost_station_capital_total"]) - sum(df["cost_station_capital_federal"])) == 7.0

    response = count_section4_capital_cost(capital_costs_sample)
    assert response["capital_cost_metrics_available"]
    assert response["average_nevi_capital_cost"] == 6.0
    assert response["deployment_cost"] == 24.0
    assert response["capital_costs_total_nevi"] == 12.0
    assert response["federal_funding"] == 17.0
    assert response["nonfederal_funding"] == 7.0


# JE-6385
@patch("APIGetDashboardProgramPerformance.index.date")
def test_unofficial_uptime_window(mock_date):
    # for mocking datetime.date, see:
    # https://docs.python.org/3/library/unittest.mock-examples.html#partial-mocking
    # test window is 2023/10/01 to 2024/09/30
    mock_date.today.return_value = datetime.date(year=2024, month=10, day=2)
    mock_date.side_effect = lambda *args, **kwargs: datetime.date(*args, **kwargs)

    port_data_sample = [
        {
            "station_uuid": "s1",
            "port_uuid": "p1",
            "port_type": "L2",
            # exclude, outage_id before start of window
            "operational_date": datetime.date(year=2023, month=9, day=30),
            "outage_id": datetime.datetime(year=2023, month=9, day=30),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s2",
            "port_uuid": "p2",
            "port_type": "L2",
            # include, outage_id in window
            "operational_date": datetime.date(year=2023, month=9, day=30),
            "outage_id": datetime.datetime(year=2023, month=10, day=1),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s3",
            "port_uuid": "p3",
            "port_type": "L2",
            # exclude, outage_id before start of window
            "operational_date": datetime.date(year=2023, month=10, day=1),
            "outage_id": datetime.datetime(year=202, month=9, day=30),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s4",
            "port_uuid": "p4",
            "port_type": "DCFC",
            # include, first day of window
            "operational_date": datetime.date(year=2023, month=10, day=1),
            "outage_id": datetime.datetime(year=2023, month=10, day=1),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s5",
            "port_uuid": "p5",
            "port_type": "DCFC",
            # include, station operational first day of window,
            #          outage occurs on last day of window
            "operational_date": datetime.date(year=2023, month=10, day=1),
            "outage_id": datetime.datetime(year=2024, month=9, day=30),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s6",
            "port_uuid": "p6",
            "port_type": "L2",
            # exclude, outage_id after end of window
            "operational_date": datetime.date(year=2023, month=10, day=1),
            "outage_id": datetime.datetime(year=2024, month=10, day=2),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s7",
            "port_uuid": "p7",
            "port_type": "DCFC",
            # exclude, operational_date in window but before operational_date
            "operational_date": datetime.date(year=2024, month=9, day=30),
            "outage_id": datetime.datetime(year=2023, month=10, day=1),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s8",
            "port_uuid": "p8",
            "port_type": "L2",
            # exclude, last day of window, divide by zero
            "operational_date": datetime.date(year=2024, month=10, day=1),
            "outage_id": datetime.datetime(year=2023, month=9, day=30),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s9",
            "port_uuid": "p9",
            "port_type": "DCFC",
            # exclude, operational_date after end of window
            "operational_date": datetime.date(year=2024, month=10, day=1),
            "outage_id": datetime.datetime(year=2023, month=10, day=1),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s10",
            "port_uuid": "p10",
            "port_type": "L2",
            # exclude, operational_date after end of window
            "operational_date": datetime.date(year=2024, month=10, day=2),
            "outage_id": datetime.datetime(year=2023, month=10, day=1),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s11",
            "port_uuid": "p11",
            "port_type": "DCFC",
            # exclude, outage_id after end of window
            "operational_date": datetime.date(year=2023, month=9, day=30),
            "outage_id": datetime.datetime(year=2024, month=10, day=1),
            "outage_duration": Decimal(1),
        },
        {
            "station_uuid": "s12",
            "port_uuid": "p12",
            "port_type": "DCFC",
            # include, outage_id in window and after operational_date
            "operational_date": datetime.date(year=2023, month=11, day=1),
            "outage_id": datetime.datetime(year=2023, month=11, day=3),
            "outage_duration": Decimal(1),
        },
    ]
    response = count_section3_reliability(port_data_sample)
    assert response.get("total_ports_with_uptime_activity") == 4
    assert response.get("num_ports_meeting_uptime_req") == 4
