from unittest.mock import patch, MagicMock
from decimal import Decimal
import datetime

from APIGetDashboardPPReliability.index import (  # type: ignore
    count_section3_reliability,
    get_outage_data,
)


@patch("APIGetDashboardPPReliability.index.execute_query_with_filters")
def test_outage_data(mock_execute_query_with_filters):
    mock_execute_query_with_filters.return_value = ((Decimal(12.341),),)
    assert get_outage_data(MagicMock(), "All") == 12.34


@patch("APIGetDashboardPPReliability.index.execute_query_with_filters")
def test_outage_data_nonetype(mock_execute_query_with_filters):
    mock_execute_query_with_filters.return_value = ((None,),)
    assert get_outage_data(MagicMock(), "All") is None

def test_count_section3_reliability_no_records():
    response = count_section3_reliability([])
    assert response.get("total_ports_with_uptime_activity") == 0
    assert response.get("percentage_ports_meeting_uptime_req") is None
    assert response.get("percentage_ports_not_meeting_uptime_req") is None
    assert not response.get("reliability_metrics_available")

# JE-6385
@patch("APIGetDashboardPPReliability.index.date")
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
