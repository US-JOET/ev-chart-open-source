import datetime
from unittest.mock import patch, MagicMock
import os
import feature_toggle
import pytest
from evchart_helper.custom_exceptions import (
    EvChartMissingOrMalformedHeadersError
)


from APIGetSubmissionTracker.index import (
    handler as api_get_dashboard_submission_tracker,
    get_hover_status,
    get_reporting_details,
    get_response_payload,
    get_tracker_status,
    get_submission_status,
    get_station_registrations,
    get_table_names,
    validate_filters,
    get_authorized_stations,
)


@pytest.fixture(name="event")
def get_valid_event():
    return {
        "headers": {},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "JOET",
                    "email": "dev@ee.doe.gov",
                    "scope": "joet",
                    "role": "admin",
                }
            },
        },
        "queryStringParameters": {
            "dr_id": "All",
            'year': '2024',
            'station': ''
        },
    }


@pytest.fixture(name="filters")
def get_valid_filters():
    return {
            'dr_id': "c56c28b7-2c4f-4063-a6dd-0bbac8a76a2d",
            'sr_id': "All",
            'year': "2024",
            'station': "All"
        }


def test_get_submission_status_all_sr():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = \
        (("station1", "2", "2024", "1", "Draft"),)

    response = get_submission_status(
        True,
        cursor=mock_cursor,
        filters={'sr_id': 'All', 'station': 'All', 'dr_id': '123'}
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert execute_args[0].endswith(
        "GROUP BY station_uuid, module, year, quarter, submission_status "
    )
    assert response[0].get('station_uuid') == 'station1'


def test_get_submission_status_one_dr_all_sr_one_time_modules():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = \
        (("station1", "2", "2024", "1", "Draft"),)

    response = get_submission_status(
        True,
        cursor=mock_cursor,
        filters={'dr_id': 'dr123', 'sr_id': 'All', 'station': 'All'}
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert "WHERE parent_org = %(dr_id)s " in execute_args[0]
    assert " AND (year=%(year)s OR year IS NULL) " not in execute_args[0]
    assert response[0].get('module') == '2'


def test_get_submission_status_non_one_time_modules():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = \
        (("station1", "2", "2024", "1", "Draft"),)

    response = get_submission_status(
        False,
        cursor=mock_cursor,
        filters={'dr_id': 'dr123', 'sr_id': 'All', 'station': 'All'}
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert " AND (year=%(year)s OR year IS NULL) " in execute_args[0]
    assert response[0].get('module') == '2'


def test_get_submission_status_one_sr_all_stations():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = \
        (("station1", "2", "2024", "1", "Draft"),)

    response = get_submission_status(
        True,
        cursor=mock_cursor,
        filters={'dr_id': 'dr123', 'sr_id': 'sr456', 'station': 'All'}
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert "SELECT station_uuid from" in execute_args[0]
    assert response[0].get('quarter') == '1'


def test_get_submission_status_one_sr_one_stations():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = \
        (("station1", "2", "2024", "1", "Draft"),)

    response = get_submission_status(
        True,
        cursor=mock_cursor,
        filters={'dr_id': 'dr123', 'sr_id': 'sr456', 'station': 'station7'}
    )
    execute_args, _ = mock_cursor.execute.call_args
    assert "station_uuid = %(station)s" in execute_args[0]
    assert response[0].get('submission_status') == 'Draft'


def test_station_registrations():
    mock_cursor = MagicMock()
    mock_cursor.fetchall.return_value = (
        ("station1", "ev1", "1", "springfield", datetime.date(2022, 4, 18)),
    )

    response = get_station_registrations(
        cursor=mock_cursor,
        filters={"dr_id": 'All', 'sr_id': 'All', 'station': 'station1'}
    )
    assert 'station1' in response
    assert response['station1']['nickname'] == 'ev1'
    assert response['station1']['station_id'] == '1'
    assert response['station1']['city'] == 'springfield'
    assert response['station1']['operational_date'] == \
        datetime.date(year=2022, month=4, day=18)

    assert 'station1' in get_station_registrations(
        cursor=mock_cursor,
        filters={"dr_id": 'dr123', 'sr_id': 'All', 'station': 'station1'}
    )
    assert 'station1' in get_station_registrations(
        cursor=mock_cursor,
        filters={"dr_id": 'All', 'sr_id': 'All', 'station': 'All'}
    )
    assert 'station1' in get_station_registrations(
        cursor=mock_cursor,
        filters={"dr_id": 'dr123', 'sr_id': 'All', 'station': 'All'}
    )


@patch('APIGetSubmissionTracker.index.get_submission_status')
def test_get_tracker_status(mock_submission_status):
    mock_submission_status.return_value = [
        {
            "station_uuid": "station1",
            "module": "9",
            "year": "2024",
            "quarter": "",
            "submission_status": "Draft"
        },
        {
            "station_uuid": "station1",
            "module": "5",
            "year": "2024",
            "quarter": "",
            "submission_status": "Pending"
        },
        {
            "station_uuid": "station1",
            "module": "2",
            "year": "2024",
            "quarter": "1",
            "submission_status": "Approved"
        }
    ]

    response = get_tracker_status(MagicMock(), {})
    assert response.get(("station1", "9", "", "")) == 0
    assert response.get(("station1", "5", "2024", "")) == 1
    assert response.get(("station1", "2", "2024", "1")) == 2


def test_get_response_payload():
    filters = {'year': '2024'}
    tracker_status = {
        ("station1", "9", "", ""):  0,
        ("station1", "5", "2024", ""): 1,
        ("station1", "2", "2024", "1"): 2
    }
    station_registrations = {
        'station1': {
            'nickname': "ev1",
            'station_id': "1",
            'city': "springfield",
            'operational_date': datetime.date(2022, 4, 18)
        }
    }
    response = \
        get_response_payload(filters, tracker_status, station_registrations)

    assert len(response) == 1
    assert response[0]['quarter1']['module2_priority'] == 'submitted'
    assert response[0]['quarter1']['module3_priority'] == 'not_submitted'
    assert response[0]['quarter1']['module4_priority'] == 'not_submitted'
    assert response[0]['quarter2']['module2_priority'] == 'not_submitted'
    assert response[0]['quarter2']['module3_priority'] == 'not_submitted'
    assert response[0]['quarter2']['module4_priority'] == 'not_submitted'
    assert response[0]['quarter3']['module2_priority'] == 'not_submitted'
    assert response[0]['quarter3']['module3_priority'] == 'not_submitted'
    assert response[0]['quarter3']['module4_priority'] == 'not_submitted'
    assert response[0]['quarter4']['module2_priority'] == 'not_submitted'
    assert response[0]['quarter4']['module3_priority'] == 'not_submitted'
    assert response[0]['quarter4']['module4_priority'] == 'not_submitted'
    assert response[0]['annual']['module5_priority'] == 'pending'
    assert response[0]['annual']['module7_priority'] == 'not_submitted'
    assert response[0]['one_time']['module6_priority'] == 'not_submitted'
    assert response[0]['one_time']['module8_priority'] == 'not_submitted'
    assert response[0]['one_time']['module9_priority'] == 'not_submitted'
    assert 'hover_status' in response[0]['quarter1']
    assert 'hover_status' in response[0]['quarter2']
    assert 'hover_status' in response[0]['quarter3']
    assert 'hover_status' in response[0]['quarter4']
    assert 'hover_status' in response[0]['annual']
    assert 'hover_status' in response[0]['one_time']


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('evchart_helper.custom_logging.LogEvent.get_auth_token')
@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
@patch("APIGetSubmissionTracker.index.aurora")
def test_handler_403_joet(
    mock_aurora,
    mock_get_feature_by_enum,
    mock_get_auth_token,
    mock_feature_toggle,
    event
):
    mock_get_feature_by_enum.return_value = {
        "Name": "dr-st-dashboard",
        "Value": "True",
    }
    mock_get_auth_token.return_value = {
        "org_id": "1234",
        "recipient_type": "joet",
        "name": "JO",
        "org_friendly_id": "99",
    }

    response = api_get_dashboard_submission_tracker(event, None)
    assert response.get('statusCode') == 403
    assert mock_aurora.get_connection.called
    assert mock_feature_toggle.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('evchart_helper.custom_logging.LogEvent.get_auth_token')
@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
@patch("APIGetSubmissionTracker.index.aurora")
def test_handler_200_dr(
    mock_aurora,
    mock_get_feature_by_enum,
    mock_get_auth_token,
    mock_feature_toggle,
    event
):
    mock_get_feature_by_enum.return_value = {
        "Name": "dr-st-dashboard",
        "Value": "True",
    }
    mock_get_auth_token.return_value = {
        "org_id": "1234",
        "recipient_type": "direct-recipient",
        "name": "DR",
        "org_friendly_id": "99",
    }

    response = api_get_dashboard_submission_tracker(event, None)
    assert response.get('statusCode') == 200
    assert mock_aurora.get_connection.called
    assert mock_feature_toggle.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    target=feature_toggle.FeatureToggleService,
    attribute="get_feature_toggle_by_enum"
)
@patch("APIGetSubmissionTracker.index.aurora")
def test_handler_invalid_token(mock_aurora, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {
        "Name": "dr-st-dashboard",
        "Value": "True",
    }

    response = api_get_dashboard_submission_tracker({'headers': {}}, None)
    assert response.get('statusCode') == 401
    assert mock_aurora.get_connection.called


# JE-4716: (red flag) Module(s) require attention/review
# If any module Has a "pending approval" status
def test_hover_status_attention_pending():
    module_status = {
        'module6_priority': 'pending',
        'module8_priority': 'submitted',
        'module9_priority': 'submitted',
    }
    assert get_hover_status(
        module_status=module_status, period='one_time'
    ) == 'attention'


# JE-4716: (red flag) Module(s) require attention/review
# If any module in the reporting period is: Overdue
def test_hover_status_attention_overdue():
    module_status = {
        'module2_priority': 'not_submitted',
        'module3_priority': 'submitted',
        'module4_priority': 'submitted',
    }

    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2024, month=1, day=1),
        period='quarterly',
        year=2024,
        quarter=1,
        today=datetime.date(year=2024, month=5, day=1)
    ) == 'attention'


# JE-4716: (green circle) All modules approved/submitted
# If all modules have at least 1 submission with "approved/submitted"
# and there are no additional uploads with conflicting statuses
def test_hover_status_success():
    module_status = {
        'module2_priority': 'submitted',
        'module3_priority': 'submitted',
        'module4_priority': 'submitted',
        'irrelevant_key': 'ignore_this'
    }
    assert get_hover_status(
        module_status=module_status, period='one_time'
    ) == 'submitted'


# JE-4716: (N/A) - Station not operational, no submissions required
# If the station's operational date pre-dates the reporting period
def test_station_not_operational_not_submitted_1():
    module_status = {
        'module2_priority': 'not_submitted',
        'module3_priority': 'not_submitted',
        'module4_priority': 'not_submitted'
    }
    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2024, month=4, day=2),
        period='quarterly',
        year=2024,
        quarter=1,
        today=datetime.date(year=2024, month=4, day=18)
    ) == 'not_applicable'

    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2024, month=4, day=2),
        period='quarterly',
        year=2024,
        quarter=2,
        today=datetime.date(year=2024, month=4, day=18)
    ) == 'none_submitted'


def test_station_not_operational_not_submitted_2():
    module_status = {
        'module2_priority': 'not_submitted',
        'module3_priority': 'not_submitted',
        'module4_priority': 'not_submitted'
    }
    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2024, month=4, day=24),
        period='quarterly',
        year=2024,
        quarter=2,
        today=datetime.date(year=2024, month=10, day=11)
    ) == 'attention'


# JE-4716: If someone submits data for a period with an "N/A" or  "––" status,
# the icon remains the same - no change.
# So if the icon was "N/A" it would stay "N/A"
def test_station_not_operational_one_submitted():
    module_status = {
        'module2_priority': 'not_submitted',
        'module3_priority': 'submitted',
        'module4_priority': 'not_submitted'
    }
    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2024, month=4, day=2),
        period='quarterly',
        year=2024,
        quarter=1,
        today=datetime.date(year=2024, month=4, day=18)
    ) == 'not_applicable'


# JE-4716: (–) No Modules due yet, Upcoming reporting period
def test_upcoming_reporting_period():
    module_status = {
        'module2_priority': 'not_submitted',
        'module3_priority': 'not_submitted',
        'module4_priority': 'not_submitted'
    }
    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2024, month=1, day=2),
        period='quarterly',
        year=2024,
        quarter=2,
        today=datetime.date(year=2024, month=2, day=1)
    ) == 'not_required'


# JE-4716: (yellow half circle) Some modules approved/submitted
# If at least 1 module in the reporting period (but not all) have
# at least 1 submission with "approved/submitted"
# AND there is no module with a "pending approval" status
# AND the reporting period has not elapsed
def test_hover_status_some_submitted():
    module_status = {
        'module2_priority': 'not_submitted',
        'module3_priority': 'submitted',
        'module4_priority': 'submitted',
    }

    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2024, month=1, day=1),
        period='quarterly',
        year=2024,
        quarter=1,
        today=datetime.date(year=2024, month=3, day=1)
    ) == 'some_submitted'


# JE-4716: (o) No Modules Submitted
def test_hover_status_none_submitted():
    module_status = {
        'module2_priority': 'not_submitted',
        'module3_priority': 'not_submitted',
        'module4_priority': 'not_submitted',
    }

    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2023, month=1, day=1),
        period='quarterly',
        year=2024,
        quarter=1,
        today=datetime.date(year=2024, month=3, day=1)
    ) == 'none_submitted'


def test_hover_status_none_submitted_one_time():
    module_status = {
        'module6_priority': 'not_submitted',
        'module8_priority': 'not_submitted',
        'module9_priority': 'not_submitted',
    }

    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2023, month=6, day=9),
        period='one_time',
        year=2024,
        today=datetime.date(year=2024, month=2, day=11)
    ) == 'none_submitted'


# catch invalid status
def test_hover_status_invalid():
    module_status = {
        'module6_priority': 'error',
        'module8_priority': 'draft',
        'module9_priority': 'not_submitted',
    }

    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2023, month=1, day=1),
        period='quarterly',
        year=2024,
        quarter=1,
        today=datetime.date(year=2024, month=3, day=1)
    ) == 'unknown'


def test_invalid_reporting_periods():
    with pytest.raises(IndexError):
        get_reporting_details(period='quarterly', quarter=7)
    with pytest.raises(IndexError):
        get_reporting_details(period='daily')


# https://driveelectric.gov/files/ev-chart-data-requirement-memo.pdf
# Quarterly data (Modules 2, 3, and 4):
# For example, a station that became operational on Jan. 16 would need to
# report quarterly data on that station from Jan. 16 to March 31,
# and the report should be submitted no later than April 30.
@pytest.mark.parametrize(
    "reporting_year,is_open,is_applicable",
    [
        (2023, True, False),
        (2024, True, True),
        (2025, False, True)
    ]
)
def test_guidance_quarterly_details(reporting_year, is_open, is_applicable):
    reporting_details = get_reporting_details(
        operational_date=datetime.date(year=2024, month=1, day=16),
        period='quarterly',
        year=reporting_year,
        quarter=1,
        today=datetime.date(year=2024, month=10, day=24)
    )
    assert reporting_details.get('is_open') is is_open
    assert reporting_details.get('is_applicable') is is_applicable
    assert reporting_details.get('deadline') == \
        datetime.date(year=reporting_year, month=4, day=30)


@pytest.mark.parametrize(
    "year,month,day,status",
    [
        (2024, 4, 30, 'none_submitted'),
        (2024, 5, 1, 'attention'),
    ]
)
def test_guidance_quarterly_not_submitted(year, month, day, status):
    module_status = {
        'module2_priority': 'not_submitted',
        'module3_priority': 'not_submitted',
        'module4_priority': 'not_submitted'
    }
    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2024, month=1, day=16),
        period='quarterly',
        year=2024,
        quarter=1,
        today=datetime.date(year=year, month=month, day=day)
    ) == status


# https://driveelectric.gov/files/ev-chart-data-requirement-memo.pdf
# Annual data (Modules 5 and 7):
# States or other direct recipients must submit annual data—
#   or approve data pre-submitted by their subrecipients and contractors—
# by March 1 of the current year for stations that became operational in the
# preceding year.
# For stations that became operational any time during the 2023 calendar year,
# all annual modules must be submitted no later than March 1, 2024.
@pytest.mark.parametrize(
    "reporting_year,is_open,is_applicable",
    [
        (2023, True, False),
        (2024, True, True),
        (2025, False, True)
    ]
)
def test_guidance_annual_details(reporting_year, is_open, is_applicable):
    reporting_details = get_reporting_details(
        operational_date=datetime.date(year=2024, month=1, day=16),
        period='annual',
        year=reporting_year,
        today=datetime.date(year=2024, month=10, day=24)
    )
    assert reporting_details.get('is_open') is is_open
    assert reporting_details.get('is_applicable') is is_applicable
    assert reporting_details.get('deadline') == \
        datetime.date(year=reporting_year+1, month=3, day=1)


@pytest.mark.parametrize(
    "year,month,day,status",
    [
        (2024, 3, 1, 'none_submitted'),
        (2024, 3, 2, 'attention'),
    ]
)
def test_guidance_annual_not_submitted(year, month, day, status):
    module_status = {
        'module5_priority': 'not_submitted',
        'module7_priority': 'not_submitted'
    }
    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2023, month=1, day=16),
        period='annual',
        year=2023,
        today=datetime.date(year=year, month=month, day=day)
    ) == status


# https://driveelectric.gov/files/ev-chart-data-requirement-memo.pdf
# One-time data (Modules 6, 8, and 9):
# States or other direct recipients must submit onetime data—
#   or approve data pre-submitted by their subrecipients and contractors—
# by March 1 of the current year for stations that became operational in the
# preceding year.
# For example, a station that became operational any time during the
# 2023 calendar year may submit one-time data any time in 2023, but all
# one-time modules must be submitted no later than March 1, 2024.
def test_guidance_one_time_details():
    reporting_details = get_reporting_details(
        operational_date=datetime.date(year=2024, month=1, day=16),
        period='one_time',
        today=datetime.date(year=2024, month=10, day=24)
    )
    assert reporting_details.get('is_open') is True
    assert reporting_details.get('is_applicable') is True
    assert reporting_details.get('deadline') == \
        datetime.date(year=2025, month=3, day=1)


@pytest.mark.parametrize(
    "year,month,day,status",
    [
        (2024, 3, 1, 'none_submitted'),
        (2024, 3, 2, 'attention'),
    ]
)
def test_guidance_one_time_not_submitted(year, month, day, status):
    module_status = {
        'module6_priority': 'not_submitted',
        'module8_priority': 'not_submitted',
        'module9_priority': 'not_submitted',
    }
    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(year=2023, month=1, day=16),
        period='one_time',
        year=2023,
        today=datetime.date(year=year, month=month, day=day)
    ) == status


# JE-5507, edge case for last day of reporting window
@pytest.mark.parametrize(
    "period,year,quarter,operational_day,status",
    [
        ('one_time', 2023, None, 30, 'attention'),
        ('annual', 2023, None, 30, 'attention'),
        ('quarterly', 2023, 1, 30, 'not_applicable'),
        ('quarterly', 2023, 2, 30, 'not_applicable'),
        ('quarterly', 2023, 3, 30, 'not_applicable'),
        ('quarterly', 2023, 4, 30, 'attention'),
        ('one_time', 2023, None, 31, 'attention'),
        ('annual', 2023, None, 31, 'attention'),
        ('quarterly', 2023, 1, 31, 'not_applicable'),
        ('quarterly', 2023, 2, 31, 'not_applicable'),
        ('quarterly', 2023, 3, 31, 'not_applicable'),
        ('quarterly', 2023, 4, 31, 'attention'),
    ]
)
def test_operation_date_dec_31(
    period: str,
    year: int,
    quarter: None | int,
    operational_day: int,
    status: str
):
    module_status = {
        'module2_priority': 'not_submitted',
        'module3_priority': 'not_submitted',
        'module4_priority': 'not_submitted',
        'module5_priority': 'not_submitted',
        'module6_priority': 'not_submitted',
        'module7_priority': 'not_submitted',
        'module8_priority': 'not_submitted',
        'module9_priority': 'not_submitted'
    }
    assert get_hover_status(
        module_status=module_status,
        operational_date=datetime.date(
            year=2023, month=12, day=operational_day
        ),
        period=period,
        year=year,
        quarter=quarter,
        today=datetime.date(year=2024, month=10, day=30)
    ) == status


def test_get_table_names():
    one_time_tables = get_table_names(True)

    assert "module2_data_v3" not in one_time_tables
    assert "module3_data_v3" not in one_time_tables
    assert "module4_data_v3" not in one_time_tables
    assert "module5_data_v3" not in one_time_tables
    assert "module7_data_v3" not in one_time_tables

    assert "module6_data_v3" in one_time_tables
    assert "module8_data_v3" in one_time_tables
    assert "module9_data_v3" in one_time_tables

    non_one_time_tables = get_table_names(False)

    assert "module2_data_v3" in non_one_time_tables
    assert "module3_data_v3" in non_one_time_tables
    assert "module4_data_v3" in non_one_time_tables
    assert "module5_data_v3" in non_one_time_tables
    assert "module7_data_v3" in non_one_time_tables

    assert "module6_data_v3" not in non_one_time_tables
    assert "module8_data_v3" not in non_one_time_tables
    assert "module9_data_v3" not in non_one_time_tables

def test_get_table_names_one_time_sql():
    one_time_sql = get_table_names(True)
    expected = """
        SELECT station_uuid, upload_id, '6' AS module FROM evchart_data_v3.module6_data_v3
        UNION SELECT station_uuid, upload_id, '8' AS module FROM evchart_data_v3.module8_data_v3
        UNION SELECT station_uuid, upload_id, '9' AS module FROM evchart_data_v3.module9_data_v3
    """
    # normalizes whitespace
    expected = " ".join(expected.split())
    assert one_time_sql == expected


def test_get_table_names_annual_sql():
    annual_sql = get_table_names(False)
    expected = """
        SELECT station_uuid, upload_id, '2' AS module
        FROM evchart_data_v3.module2_data_v3
        UNION SELECT station_uuid, upload_id, '3' AS module FROM evchart_data_v3.module3_data_v3
        UNION SELECT station_uuid, upload_id, '4' AS module FROM evchart_data_v3.module4_data_v3
        UNION SELECT station_uuid, upload_id, '5' AS module FROM evchart_data_v3.module5_data_v3
        UNION SELECT station_uuid, upload_id, '7' AS module FROM evchart_data_v3.module7_data_v3
    """
    # normalizes whitespace
    expected = " ".join(expected.split())
    assert annual_sql == expected


@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch("APIGetSubmissionTracker.index.is_valid_station")
def test_valid_filters(mock_valid_station, mock_feature_toggle, filters):
    mock_cursor = MagicMock()
    mock_valid_station.return_value = []
    new_filter = validate_filters(mock_cursor, filters, mock_feature_toggle)
    assert new_filter["sr_id"] == "All"
    assert new_filter["year"] == "2024"
    assert new_filter["station"] == "All"


@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch("evchart_helper.api_helper.execute_query")
def test_valid_filters_transform(
    mock_execute_query, mock_feature_toggle, filters
):
    mock_cursor = MagicMock()
    mock_execute_query.return_value = ["exists"]
    filters["station"] = ""
    filters["sr_id"] = "None"
    new_filter = validate_filters(mock_cursor, filters, mock_feature_toggle)
    assert new_filter["sr_id"] == "c56c28b7-2c4f-4063-a6dd-0bbac8a76a2d"
    assert new_filter["year"] == "2024"
    assert new_filter["station"] == "All"


@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch("APIGetSubmissionTracker.index.is_valid_station")
def test_validate_sr(mock_valid_station, mock_feature_toggle, filters):
    mock_cursor = MagicMock()
    mock_valid_station.return_value = []
    filters["sr_id"] = "c56c28b7-2c4f-4063-a6dd-0bbac8a76a2d"
    new_filter = validate_filters(mock_cursor, filters, mock_feature_toggle)
    assert new_filter["sr_id"] == "c56c28b7-2c4f-4063-a6dd-0bbac8a76a2d"


@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch("APIGetSubmissionTracker.index.is_valid_station")
@patch("APIGetSubmissionTracker.index.get_authorized_stations")
def test_valid_station(
    mock_authorized_stations,
    mock_valid_station,
    mock_feature_toggle,
    filters
):
    mock_cursor = MagicMock()
    mock_valid_station.return_value = True
    mock_authorized_stations.return_value = ["123"]
    filters["sr_id"] = "c56c28b7-2c4f-4063-a6dd-0bbac8a76a2d"
    filters["station"] = "123"
    new_filter = validate_filters(mock_cursor, filters, mock_feature_toggle)
    assert new_filter["sr_id"] == "c56c28b7-2c4f-4063-a6dd-0bbac8a76a2d"


@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch("APIGetSubmissionTracker.index.is_valid_station")
@patch("APIGetSubmissionTracker.index.get_authorized_stations")
def test_invalid_station(
    mock_authorized_stations, mock_valid_station, mock_feature_toggle, filters
):
    mock_cursor = MagicMock()
    mock_valid_station.return_value = True
    mock_authorized_stations.return_value = False
    with pytest.raises(EvChartMissingOrMalformedHeadersError):
        validate_filters(mock_cursor, filters, mock_feature_toggle)


@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
def test_invalid_sr(mock_feature_toggle, filters):
    mock_cursor = MagicMock()
    filters["sr_id"] = "123abc"
    with pytest.raises(EvChartMissingOrMalformedHeadersError):
        validate_filters(mock_cursor, filters, mock_feature_toggle)


@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
def test_invalid_year(mock_feature_toggle, filters):
    mock_cursor = MagicMock()
    filters["year"] = "123abc"
    with pytest.raises(EvChartMissingOrMalformedHeadersError):
        validate_filters(mock_cursor, filters, mock_feature_toggle)


@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch("APIGetSubmissionTracker.index.execute_query")
def test_get_authorized_stations(mock_execute_query, mock_feature_toggle):
    mock_cursor = MagicMock()
    mock_execute_query.return_value = [{"station_uuid": "123"}]
    response = get_authorized_stations(
        cursor=mock_cursor,
        filters={"dr_id": "dr", "sr_id": "All", "station": "123"},
        features=mock_feature_toggle
    )
    assert response


# JE-6617 one-time submissions not showing correct status in tracker
@patch('APIGetSubmissionTracker.index.get_submission_status')
def test_get_tracker_status_null_quarter(mock_submission_status):
    mock_submission_status.side_effect = [
        [],
        [
            {
                "station_uuid": "maui",
                "module": "6",
                "year": "2024",
                "quarter": None,
                "submission_status": "Approved"
            },
            {
                "station_uuid": "maui",
                "module": "8",
                "year": "2024",
                "quarter": "",
                "submission_status": "Approved"
            },
            {
                "station_uuid": "maui",
                "module": "9",
                "year": "2024",
                "quarter": "",
                "submission_status": "Approved"
            }
        ]
    ]

    response = get_tracker_status(MagicMock(), {})
    assert response.get(("maui", "6", "", "")) == 2
    assert response.get(("maui", "8", "", "")) == 2
    assert response.get(("maui", "9", "", "")) == 2
