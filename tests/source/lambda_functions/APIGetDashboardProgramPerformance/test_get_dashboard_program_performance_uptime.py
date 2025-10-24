from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from APIGetDashboardProgramPerformance.index import (
    count_section3_official_reliability, count_section3_uptime_most_recent)
from dateutil.relativedelta import relativedelta

operational_date_by_station_uuid_official = {
    "1": date(year=2022, month=1, day=1),
    "2": date(year=2024, month=2, day=1),
    "3": date(year=2022, month=12, day=31),
    "4": date(year=2022, month=5, day=12),
}

operational_date_by_station_uuid_unofficial = {
    "1": date(year=2023, month=3, day=1),
    "2": date(year=2024, month=2, day=1),
    "3": date(year=2022, month=12, day=1),
    "4": date(year=2022, month=5, day=1),
}

official_uptime_response = [
    {
        "station_uuid": "1",
        "port_id": "1",
        "port_uuid": "1",
        "uptime_reporting_start": datetime(year=2022, month=1, day=1),
        "uptime_reporting_end": datetime(year=2024, month=11, day=1),
        "uptime": Decimal(97),
        "port_type": "L2",
    },
    {
        "station_uuid": "1",
        "port_id": "1",
        "port_uuid": "1",
        "uptime_reporting_start": datetime(year=2022, month=1, day=1),
        "uptime_reporting_end": datetime(year=2023, month=10, day=1),
        "uptime": Decimal(95),
        "port_type": "L2",
    },
    {
        "station_uuid": "1",
        "port_id": "2",
        "port_uuid": "2",
        "uptime_reporting_start": datetime(year=2022, month=1, day=1),
        "uptime_reporting_end": datetime(year=2024, month=10, day=1),
        "uptime": Decimal(29),
        "port_type": "L2",
    },
    {
        "station_uuid": "2",
        "port_id": "1",
        "port_uuid": "3",
        "uptime_reporting_start": datetime(year=2022, month=1, day=1),
        "uptime_reporting_end": datetime(year=2025, month=2, day=1),
        "uptime": None,
        "port_type": "L2",
    },
    {
        "station_uuid": "2",
        "port_id": "1",
        "port_uuid": "3",
        "uptime_reporting_start": datetime(year=2022, month=1, day=1),
        "uptime_reporting_end": datetime(year=2024, month=10, day=1),
        "uptime": Decimal(88),
        "port_type": "L2",
    },
    {
        "station_uuid": "2",
        "port_id": "2",
        "port_uuid": "4",
        "uptime_reporting_start": datetime(year=2022, month=1, day=1),
        "uptime_reporting_end": datetime(year=2025, month=10, day=1),
        "uptime": None,
        "port_type": "L2",
    },
    {
        "station_uuid": "3",
        "port_id": "1",
        "port_uuid": "5",
        "uptime_reporting_start": datetime(year=2023, month=1, day=1),
        "uptime_reporting_end": datetime(year=2024, month=11, day=1),
        "uptime": Decimal(99),
        "port_type": "DCFC",
    },
]


def get_sql_output(uptime_data, operational_data):
    for item in uptime_data:
        item["operational_date"] = operational_data[item["station_uuid"]]
    return uptime_data


def test_official_uptime_2023():
    official_response = count_section3_uptime_most_recent(
        get_sql_output(official_uptime_response, operational_date_by_station_uuid_official), 2023
    )

    assert len(official_response) == 1
    assert official_response.get(("1", "1"))["uptime"] == Decimal(95)
    assert official_response.get(("1", "2")) is None
    assert official_response.get(("3", "1")) is None
    assert official_response.get(("4", "1")) is None

    uptime_response = count_section3_official_reliability(official_response)
    assert uptime_response.get("total_ports_with_uptime_activity") == 1
    assert uptime_response.get("num_l2_chargers_not_meeting_req") == 1


def test_official_uptime_all():
    official_response = count_section3_uptime_most_recent(
        get_sql_output(official_uptime_response, operational_date_by_station_uuid_official)
    )
    assert len(official_response) == 5
    assert official_response.get(("1", "1"))["uptime"] == Decimal(97)
    assert official_response.get(("1", "2"))["uptime"] == Decimal(29)
    assert official_response.get(("2", "1"))["uptime"] is None
    assert official_response.get(("2", "2"))["uptime"] is None
    assert official_response.get(("3", "1"))["uptime"] == Decimal(99)
    assert official_response.get(("4", "1")) is None
    uptime_response = count_section3_official_reliability(official_response)
    assert uptime_response.get("total_ports_with_uptime_activity") == 3
    assert uptime_response.get("num_l2_chargers_not_meeting_req") == 1
    assert uptime_response.get("num_ports_meeting_uptime_req") == 2


# 1 - "Operational for at least one (1) year when Uptime was measured" condition (uptime_reporting_end - operational_date >= 1 year) + NULL data handling

# station_uuid	port_id	    operational_date	uptime_reporting_start	uptime_reporting_end	uptime	Incl. in calculation?	Notes
# 1	            1A	        8/1/2021	        1/1/2022	            12/31/2022	            99	    Yes	                    Uptime reported over > one (1) year period
# 2	            2A	        1/1/2022	        1/1/2022	            12/31/2022	            95	    Yes	                    Uptime reported over exactly one (1) year period
# 2	            2B	        1/1/2022	        1/1/2022	            12/31/2022	                    No	                    Empty string valid under "user reports no data" flow;
# 2	            3A	        3/1/2022	        3/1/2022	            12/31/2022	            29	    No	                    Station was not operational for at least one (1) during reporting period which doesn't follow 23 CFR 680.112(b) definition
# 3	            3B	        3/1/2022	        3/1/2022	            12/31/2022	            97	    No	                    replaces user submitting invalid uptime values for < 12 month reporting periods


def get_test_case_1_stations():
    return {
        "1": date(year=2021, month=8, day=1),
        "2": date(year=2022, month=1, day=1),
        "3": date(year=2022, month=3, day=1),
    }


def get_test_case_1_uptime():
    return [
        {
            "station_uuid": "1",
            "port_id": "1A",
            "port_uuid": "1A",
            "uptime_reporting_start": datetime(year=2022, month=1, day=1),
            "uptime_reporting_end": datetime(year=2022, month=12, day=31,),
            "uptime": Decimal(99),
            "port_type": "L2",
        },
        {
            "station_uuid": "2",
            "port_id": "2A",
            "port_uuid": "2A",
            "uptime_reporting_start": datetime(year=2022, month=1, day=1),
            "uptime_reporting_end": datetime(year=2022, month=12, day=31),
            "uptime": Decimal(95),
            "port_type": "L2",
        },
        {
            "station_uuid": "2",
            "port_id": "2B",
            "port_uuid": "2B",
            "uptime_reporting_start": datetime(year=2022, month=1, day=1),
            "uptime_reporting_end": datetime(year=2022, month=12, day=31),
            "uptime": None,
            "port_type": "L2",
        },
        {
            "station_uuid": "3",
            "port_id": "3A",
            "port_uuid": "3A",
            "uptime_reporting_start": datetime(year=2022, month=3, day=1),
            "uptime_reporting_end": datetime(year=2022, month=12, day=31),
            "uptime": Decimal(29),
            "port_type": "L2",
        },
        {
            "station_uuid": "3",
            "port_id": "3B",
            "port_uuid": "3B",
            "uptime_reporting_start": datetime(year=2022, month=3, day=1),
            "uptime_reporting_end": datetime(year=2023, month=12, day=31),
            "uptime": Decimal(97),
            "port_type": "L2",
        },
    ]


def test_official_uptime_all_test_case_1():
    reporting_year = 2022
    official_response = count_section3_uptime_most_recent(
        get_sql_output(get_test_case_1_uptime(), get_test_case_1_stations()), reporting_year
    )
    uptime_response = count_section3_official_reliability(official_response)
    assert uptime_response.get("total_ports_with_uptime_activity") == 2
    assert uptime_response.get("num_ports_meeting_uptime_req") == 1
    assert uptime_response.get("num_l2_chargers_not_meeting_req") == 1


# 2 - "Reporting period should be exactly 12 months" condition (uptime_reporting_end - uptime_reporting_start = 12 months)

# station_uuid	port_id	operational_date	uptime_reporting_start	uptime_reporting_end	uptime	Incl. in calculation?	Notes
# 1	            1A	        8/1/2021	        1/1/2022	            12/31/2022	         99	        Yes	                Reporting period = 12 months
# 2	            2A	        1/1/2022	        1/1/2022	            1/25/2023	         95	        Yes	                Reporting period > 12 months, resulting in invalid uptime value – user reported data for reporting period > 12 months which doesn't follow 23 CFR 680.112(b) definition
# 2	            2B	        1/1/2022	        3/1/2022	            12/31/2022	         97	        No	                Reporting period < 12 months, resulting in invalid uptime value – user reported data for reporting period < 12 months which doesn't follow 23 CFR 680.112(b) definition


def get_test_case_2_stations():
    return {
        "1": date(year=2021, month=8, day=1),
        "2": date(year=2022, month=1, day=1),
    }


def get_test_case_2_uptime():
    return [
        {
            "station_uuid": "1",
            "port_id": "1A",
            "port_uuid": "1A",
            "uptime_reporting_start": datetime(year=2022, month=1, day=1),
            "uptime_reporting_end": datetime(year=2022, month=12, day=31),
            "uptime": Decimal(99),
            "port_type": "L2",
        },
        {
            "station_uuid": "2",
            "port_id": "2A",
            "port_uuid": "2A",
            "uptime_reporting_start": datetime(year=2022, month=1, day=1),
            "uptime_reporting_end": datetime(year=2023, month=1, day=25),
            "uptime": Decimal(95),
            "port_type": "L2",
        },
        {
            "station_uuid": "2",
            "port_id": "2B",
            "port_uuid": "2B",
            "uptime_reporting_start": datetime(year=2022, month=3, day=1),
            "uptime_reporting_end": datetime(year=2022, month=12, day=31),
            "uptime": Decimal(97),
            "port_type": "L2",
        },
    ]


# @patch("APIGetDashboardProgramPerformance.index.datetime")
def test_official_uptime_all_test_case_2():
    reporting_year = 2023
    official_response = count_section3_uptime_most_recent(
        get_sql_output(get_test_case_2_uptime(), get_test_case_2_stations()), reporting_year
    )
    uptime_response = count_section3_official_reliability(official_response)
    assert uptime_response.get("total_ports_with_uptime_activity") == 2
    assert uptime_response.get("num_ports_meeting_uptime_req") == 1
    assert uptime_response.get("num_l2_chargers_not_meeting_req") == 1


# 3 - "Only the most recent Uptime should be included" condition (max(uptime_reporting_end))


# station_uuid	port_id	operational_date	uptime_reporting_start	uptime_reporting_end	uptime	Incl. in calculation?	Notes
# 1	             1A	        8/1/2021	        1/1/2022	            12/31/2022	         99	        Yes	                This row includes the most recent reporting period (denoted by the latest uptime_reporting_end value) for port_id = 1A at station_uuid = 1
# 1	             1A	        8/1/2021	        12/1/2021	            11/30/2022	         96	        No	                While a valid value in the 2022Q4 quarterly reporting for station_uuid = 1, this row is not the most recent reporting period for port_id = 1A.
# 1	             1A	        8/1/2021	        11/1/2021	            10/31/2022	         98	        No	                While a valid value in the 2022Q4 quarterly reporting for station_uuid = 1, this row is not the most recent reporting period for port_id = 1A.
def get_test_case_3_stations():
    return {
        "1": date(year=2021, month=8, day=1),
    }


def get_test_case_3_uptime():
    return [
        {
            "station_uuid": "1",
            "port_id": "1A",
            "port_uuid": "1A",
            "uptime_reporting_start": datetime(year=2022, month=1, day=1),
            "uptime_reporting_end": datetime(year=2022, month=12, day=31),
            "uptime": Decimal(99),
            "port_type": "L2",
        },
        {
            "station_uuid": "1",
            "port_id": "1A",
            "port_uuid": "1A",
            "uptime_reporting_start": datetime(year=2021, month=12, day=1),
            "uptime_reporting_end": datetime(year=2022, month=11, day=30),
            "uptime": Decimal(96),
            "port_type": "L2",
        },
        {
            "station_uuid": "1",
            "port_id": "1A",
            "port_uuid": "1A",
            "uptime_reporting_start": datetime(year=2021, month=11, day=1),
            "uptime_reporting_end": datetime(year=2022, month=10, day=31),
            "uptime": Decimal(98),
            "port_type": "L2",
        },
    ]


def test_official_uptime_all_test_case_3():
    reporting_year = 2022
    official_response = count_section3_uptime_most_recent(
        get_sql_output(get_test_case_3_uptime(), get_test_case_3_stations()), reporting_year
    )
    assert len(official_response) == 1
    uptime_response = count_section3_official_reliability(official_response)
    assert uptime_response.get("reliability_metrics_available") is True
    assert uptime_response.get("num_ports_meeting_uptime_req") == 1
    assert uptime_response.get("num_l2_chargers_not_meeting_req") == 0
    assert uptime_response.get("num_dcfc_chargers_not_meeting_req") == 0
    assert uptime_response.get("total_ports_with_uptime_activity") == 1
    assert uptime_response.get("percentage_ports_meeting_uptime_req") == Decimal(1)
    assert uptime_response.get("percentage_ports_not_meeting_uptime_req") == Decimal(0)


# 4 write tests for leap year
# station_uuid	port_id	operational_date	uptime_reporting_start	uptime_reporting_end	uptime	Incl. in calculation?	Notes
# 1	             1A	        1/1/2024	        1/1/2024	            12/31/2024	         99	        Yes	                Checking 366 days on a leap year
# 1	             1B	        1/1/2024	        1/2/2024	            12/31/2024	         99	        No	                Checking 365 days start to end on a leap year
# 2	             2A	        1/2/2024	        1/1/2024	            12/31/2024	         96	        No	                Checking 365 days operational on a leap year
def get_test_case_4_stations():
    return {
        "1": date(year=2024, month=1, day=1),
        "2": date(year=2024, month=1, day=2),
    }


def get_test_case_4_uptime():
    return [
        {
            "station_uuid": "1",
            "port_id": "1A",
            "port_uuid": "1A",
            "uptime_reporting_start": datetime(year=2024, month=1, day=1),
            "uptime_reporting_end": datetime(year=2024, month=12, day=31),
            "uptime": Decimal(99),
            "port_type": "L2",
        },
        {
            "station_uuid": "1",
            "port_id": "1B",
            "port_uuid": "1B",
            "uptime_reporting_start": datetime(year=2024, month=1, day=2),
            "uptime_reporting_end": datetime(year=2024, month=12, day=31),
            "uptime": Decimal(99),
            "port_type": "L2",
        },
        {
            "station_uuid": "2",
            "port_id": "2A",
            "port_uuid": "2A",
            "uptime_reporting_start": datetime(year=2024, month=1, day=1),
            "uptime_reporting_end": datetime(year=2024, month=12, day=31),
            "uptime": Decimal(95),
            "port_type": "L2",
        },
    ]


@patch("APIGetDashboardProgramPerformance.index.date")
def test_official_uptime_all_test_case_4(mock_datetime):
    reporting_year = 2025
    official_response = count_section3_uptime_most_recent(
        get_sql_output(get_test_case_4_uptime(), get_test_case_4_stations()), reporting_year
    )
    uptime_response = count_section3_official_reliability(official_response)
    assert uptime_response.get("total_ports_with_uptime_activity") == 1
    assert uptime_response.get("num_ports_meeting_uptime_req") == 1
    assert uptime_response.get("num_l2_chargers_not_meeting_req") == 0


def test_feb_29_plus_1_year():
    leap_year = date(2024, 2, 29)
    next_year = leap_year + relativedelta(years=1)
    assert next_year.day == 28
