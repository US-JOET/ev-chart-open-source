from datetime import date
from ScheduledSubmissionDeadlineEmail.index import (
    should_send_email,
    format_email_template,
    get_search_modules,
    get_quarter_string,
    get_quarter,
    get_past_due_modules_by_station
)
from unittest.mock import patch
import pytest
import pandas as pd

def get_upload_data_frame():
    data = {
        "upload_id": ["111", "222", "333", "444", "555"],
        "org_id": ["1","2","1", "1", "1"],
        "parent_org": ["3","3","4", "3", "3"],
        "quarter": ["1", "1", "2", "3", ""],
        "updated_on": ["now", "then", "sometime", "wow", "nope"],
        "year": ["2024", "2023", "2024", "2025", "2024"],
        "module_id": ['3', '4', '5', '3', '8']
    }
    return pd.DataFrame(data)

def get_station_data_frame():
    data = {
        "nickname": ["station1", "station2", "station3"],
        "station_uuid": ["1","2","3"],
        "dr_id": ["3","3","4"],
        "station_id": ["station1", "station22", "station32"],
        "operational_date": [date(2024, 1, 1), date(2023, 1, 1), date(2024, 1, 1)]
    }
    return pd.DataFrame(data)

def get_past_due_stations_dict():
    data = {
        "1": [1, 2, 3],
        "2": [4],
        "3": [5,6]
    }
    return data

def get_sr_data_frame():
    data = {
        "sr_id": ["station1", "station2", "station3"]
    }
    return pd.DataFrame(data)

def get_expected_template(sr_present):
    if sr_present:
        return '\n<li>Station Nickname: Station ID - station1: station1</li>\n\n<ul>\n   <li>Authorized subrecipient(s)/contractor(s):</li>\n    <ul>\n        \n<li>SR name</li>\n\n<li>SR name</li>\n\n<li>SR name</li>\n\n    </ul>\n</ul>\n\n<ul>\n    <li>Module(s) overdue:</li>\n    <ul>\n        \n<li>Module 1: Station Location</li>\n\n<li>Module 2: Charging Sessions</li>\n\n<li>Module 3: Uptime</li>\n\n    </ul>\n</ul>\n\n<li>Station Nickname: Station ID - station2: station22</li>\n\n<ul>\n   <li>Authorized subrecipient(s)/contractor(s):</li>\n    <ul>\n        \n<li>SR name</li>\n\n<li>SR name</li>\n\n<li>SR name</li>\n\n    </ul>\n</ul>\n\n<ul>\n    <li>Module(s) overdue:</li>\n    <ul>\n        \n<li>Module 4: Outages</li>\n\n    </ul>\n</ul>\n\n<li>Station Nickname: Station ID - station3: station32</li>\n\n<ul>\n   <li>Authorized subrecipient(s)/contractor(s):</li>\n    <ul>\n        \n<li>SR name</li>\n\n<li>SR name</li>\n\n<li>SR name</li>\n\n    </ul>\n</ul>\n\n<ul>\n    <li>Module(s) overdue:</li>\n    <ul>\n        \n<li>Module 5: Maintenance Costs</li>\n\n<li>Module 6: Station Operator Identity</li>\n\n    </ul>\n</ul>\n'
    return '\n<li>Station Nickname: Station ID - station1: station1</li>\n\n<ul>\n    <li>Module(s) overdue:</li>\n    <ul>\n        \n<li>Module 1: Station Location</li>\n\n<li>Module 2: Charging Sessions</li>\n\n<li>Module 3: Uptime</li>\n\n    </ul>\n</ul>\n\n<li>Station Nickname: Station ID - station2: station22</li>\n\n<ul>\n    <li>Module(s) overdue:</li>\n    <ul>\n        \n<li>Module 4: Outages</li>\n\n    </ul>\n</ul>\n\n<li>Station Nickname: Station ID - station3: station32</li>\n\n<ul>\n    <li>Module(s) overdue:</li>\n    <ul>\n        \n<li>Module 5: Maintenance Costs</li>\n\n<li>Module 6: Station Operator Identity</li>\n\n    </ul>\n</ul>\n'


@patch('ScheduledSubmissionDeadlineEmail.index.get_org_info_dynamo')
@patch('ScheduledSubmissionDeadlineEmail.index.get_station_authorized')
def test_format_email_template_authorized_srs_present(mock_station_authorized, mock_org_info):
    cursor = ""
    features = []
    mock_org_info.return_value = {"name": "SR name"}
    mock_station_authorized.return_value = get_sr_data_frame()
    formatted_template = format_email_template(get_station_data_frame(), get_past_due_stations_dict(), cursor, features)
    assert formatted_template == get_expected_template(sr_present=True)

@patch('ScheduledSubmissionDeadlineEmail.index.get_org_info_dynamo')
@patch('ScheduledSubmissionDeadlineEmail.index.get_station_authorized')
def test_format_email_template_no_authorized_srs(mock_station_authorized, mock_org_info):
    cursor = ""
    features = []
    mock_org_info.return_value = {"name": "SR name"}
    mock_station_authorized.return_value = pd.DataFrame({})
    formatted_template = format_email_template(get_station_data_frame(), get_past_due_stations_dict(), cursor, features)
    assert formatted_template == get_expected_template(sr_present=False)

@pytest.mark.parametrize(
    "month, expected_result",
    [
        (1, []),
        (2, [2, 3, 4]),
        (3, [5,6,7,9]),
        (4, []),
        (5, [2, 3, 4]),
        (6, []),
        (7, []),
        (8, [2, 3, 4]),
        (9, []),
        (10, []),
        (11, [2, 4]),
        (12, []),
    ],
)
@patch('ScheduledSubmissionDeadlineEmail.index.get_module_data')
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_year")
def test_past_due_modules_by_station(mock_get_year, mock_get_month,
                                     mock_get_module_data,
                                     month,expected_result
):
    cursor = ""
    mock_get_year.return_value = 2025
    mock_get_month.return_value = month
    station_df = get_station_data_frame()
    uploads_df = get_upload_data_frame()
    filter_station_df = station_df[station_df['station_id'] == 'station1']
    filter_uploads_df = uploads_df[uploads_df['quarter'] == str(get_quarter())]
    for _,row in filter_station_df.iterrows():
        station_row = row
    past_due_modules = get_past_due_modules_by_station(station_row, filter_uploads_df, cursor)
    assert set(past_due_modules) == set(expected_result)

# JE-6504 Debugging use case for a submitted module still getting flagged as an overdue module
@patch('ScheduledSubmissionDeadlineEmail.index.get_module_data')
@patch("ScheduledSubmissionDeadlineEmail.index.get_day_of_week")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_day")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_year")
def test_past_due_modules_annual_only_module_6_submitted(
    mock_get_year,
    mock_get_day,
    mock_get_month,
    mock_get_day_of_week,
    mock_get_module_data,
):
    station_data_df = pd.DataFrame({
        "nickname": ["cherry"],
        "station_uuid": ["1"],
        "dr_id": ["3"],
        "station_id": ["cherry"],
        "operational_date": [date(2023, 1, 1)]
    })

    upload_data = pd.DataFrame({
        "upload_id": ["111"],
        "org_id": ["3"],
        "parent_org": ["3"],
        "quarter": [""],
        "updated_on": ["now"],
        "year": ["2024"],
        "module_id": ['6']
    })

    cursor = ""
    mock_get_year.return_value = 2024
    mock_get_month.return_value = 3
    mock_get_day.return_value = 4
    mock_get_day_of_week.return_value = 3
    mock_get_module_data.return_value = (1,)
    for _,row in station_data_df.iterrows():
        station_row = row
    past_due_modules = get_past_due_modules_by_station(station_row, upload_data, cursor)
    # since module 6 was submitted, it is not counted as a past due module
    expected_result = [8,9,5,7]
    assert set(past_due_modules) == set(expected_result)


@pytest.mark.parametrize(
    "month, expected_result",
    [
        (1, "N/A"),
        (2, "Quarter 4 (Oct-Dec)"),
        (3, "One-Time/Annual"),
        (4, "N/A"),
        (5, "Quarter 1 (Jan-Mar)"),
        (6, "N/A"),
        (7, "N/A"),
        (8, "Quarter 2 (Apr-Jun)"),
        (9, "N/A"),
        (10, "N/A"),
        (11, "Quarter 3 (Jul-Sep)"),
        (12, "N/A"),
    ],
)
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
def test_get_quarter_string(
    mock_get_current_month,
    month, expected_result
):
    mock_get_current_month.return_value = month
    result = get_quarter_string()
    assert expected_result == result


@pytest.mark.parametrize(
    "month, expected_result",
    [
        (1, ()),
        (2, (2,3,4)),
        (3, (5,6,7,8,9)),
        (4, ()),
        (5, (2,3,4)),
        (6, ()),
        (7, ()),
        (8, (2,3,4)),
        (9, ()),
        (10, ()),
        (11, (2,3,4)),
        (12, ()),
    ],
)
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
def test_get_search_modules(
    mock_get_current_month,
    month, expected_result
):
    mock_get_current_month.return_value = month
    result = get_search_modules()
    assert set(expected_result) == set(result)


@pytest.mark.parametrize(
    "day, expected_result",
    [
        (1, False),
        (2, False),
        (3, True),
        (4, True),
        (5, True),
        (6, False),
        (7, False),
        (8, False),
        (9, False),
        (10, False),
        (20, False),
        (21, True),
        (22, True),
        (23, True),
        (24, False),
    ],
)
@patch("ScheduledSubmissionDeadlineEmail.index.get_day_of_week")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_day")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
def test_should_trigger_email_monday(
    mock_get_current_month,
    mock_get_current_day,
    mock_get_day_of_week,
    day, expected_result
):
    mock_get_day_of_week.return_value = 0
    mock_get_current_month.return_value = 5
    mock_get_current_day.return_value = day
    result = should_send_email()
    assert expected_result is result


@pytest.mark.parametrize(
    "day, expected_result",
    [
        (1, False),
        (2, False),
        (3, True),
        (4, False),
        (5, False),
        (6, False),
        (7, False),
        (8, False),
        (9, False),
        (10, False),
        (20, False),
        (21, True),
        (22, False),
        (23, False),
        (24, False),
    ],
)
@patch("ScheduledSubmissionDeadlineEmail.index.get_day_of_week")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_day")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
def test_should_trigger_email_tuesday(
    mock_get_current_month,
    mock_get_current_day,
    mock_get_day_of_week,
    day, expected_result
):
    mock_get_day_of_week.return_value = 1
    mock_get_current_month.return_value = 5
    mock_get_current_day.return_value = day
    result = should_send_email()
    assert expected_result is result


@pytest.mark.parametrize(
    "day, expected_result",
    [
        (1, False),
        (2, False),
        (3, True),
        (4, False),
        (5, False),
        (6, False),
        (7, False),
        (8, False),
        (9, False),
        (10, False),
        (20, False),
        (21, True),
        (22, False),
        (23, False),
        (24, False),
    ],
)
@patch("ScheduledSubmissionDeadlineEmail.index.get_day_of_week")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_day")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
def test_should_trigger_email_wednesday(
    mock_get_current_month,
    mock_get_current_day,
    mock_get_day_of_week,
    day, expected_result
):
    mock_get_day_of_week.return_value = 2
    mock_get_current_month.return_value = 5
    mock_get_current_day.return_value = day
    result = should_send_email()
    assert expected_result is result

@pytest.mark.parametrize(
    "day, expected_result",
    [
        (1, False),
        (2, False),
        (3, True),
        (4, False),
        (5, False),
        (6, False),
        (7, False),
        (8, False),
        (9, False),
        (10, False),
        (20, False),
        (21, True),
        (22, False),
        (23, False),
        (24, False),
    ],
)
@patch("ScheduledSubmissionDeadlineEmail.index.get_day_of_week")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_day")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
def test_should_trigger_email_thursday(
    mock_get_current_month,
    mock_get_current_day,
    mock_get_day_of_week,
    day, expected_result
):
    mock_get_day_of_week.return_value = 3
    mock_get_current_month.return_value = 5
    mock_get_current_day.return_value = day
    result = should_send_email()
    assert expected_result is result

@pytest.mark.parametrize(
    "day, expected_result",
    [
        (1, False),
        (2, False),
        (3, True),
        (4, False),
        (5, False),
        (6, False),
        (7, False),
        (8, False),
        (9, False),
        (10, False),
        (20, False),
        (21, True),
        (22, False),
        (23, False),
        (24, False),
    ],
)
@patch("ScheduledSubmissionDeadlineEmail.index.get_day_of_week")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_day")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
def test_should_trigger_email_friday(
    mock_get_current_month,
    mock_get_current_day,
    mock_get_day_of_week,
    day, expected_result
):
    mock_get_day_of_week.return_value = 4
    mock_get_current_month.return_value = 5
    mock_get_current_day.return_value = day
    result = should_send_email()
    assert expected_result is result

@pytest.mark.parametrize(
    "day, expected_result",
    [
        (1, False),
        (2, False),
        (3, False),
        (4, False),
        (5, False),
        (6, False),
        (7, False),
        (8, False),
        (9, False),
        (10, False),
        (20, False),
        (21, False),
        (22, False),
        (23, False),
        (24, False),
    ],
)
@patch("ScheduledSubmissionDeadlineEmail.index.get_day_of_week")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_day")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
def test_should_trigger_email_saturday(
    mock_get_current_month,
    mock_get_current_day,
    mock_get_day_of_week,
    day, expected_result
):
    mock_get_day_of_week.return_value = 5
    mock_get_current_month.return_value = 5
    mock_get_current_day.return_value = day
    result = should_send_email()
    assert expected_result is result

@pytest.mark.parametrize(
    "day, expected_result",
    [
        (1, False),
        (2, False),
        (3, False),
        (4, False),
        (5, False),
        (6, False),
        (7, False),
        (8, False),
        (9, False),
        (10, False),
        (20, False),
        (21, False),
        (22, False),
        (23, False),
        (24, False),
    ],
)
@patch("ScheduledSubmissionDeadlineEmail.index.get_day_of_week")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_day")
@patch("ScheduledSubmissionDeadlineEmail.index.get_current_month")
def test_should_trigger_email_sunday(
    mock_get_current_month,
    mock_get_current_day,
    mock_get_day_of_week,
    day, expected_result
):
    mock_get_day_of_week.return_value = 6
    mock_get_current_month.return_value = 5
    mock_get_current_day.return_value = day
    result = should_send_email()
    assert expected_result is result
