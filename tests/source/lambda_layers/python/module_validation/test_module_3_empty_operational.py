from unittest.mock import MagicMock, patch
from datetime import date

from error_report_messages_enum import ErrorReportMessages
from module_validation import validate_m3
from feature_toggle.feature_enums import Feature

import pandas


# JE-5779
# A module 3 upload containing uptime as empty string will be not be
# accepted if the uptime_reporting_start is at least 1 year after the
# operational date for the associated station
@patch("module_validation.validate_m3.get_operational_date")
def test_records_with_empty_values(mock_get_operational_date):
    mock_get_operational_date.return_value = date(year=2024, month=7, day=4)

    df = pandas.DataFrame({
        'station_id': ["s1", "s2", "s3", "s4", "s5", "s6"],
        'network_provider': ["np1", "np1", "np2", "np2", "np3", "np3"],
        'port_id': ["port1", "port1", "port2", "port2", "port3", "port3"],
        'uptime_reporting_start': [
            '2024-07-04T00:00:01Z',
            '2024-12-01T01:00:00Z',
            '2025-12-01T10:00:00Z',
            '2025-12-01T10:00:00Z',
            '2025-07-04T14:00:00Z',
            '2025-07-03T14:00:00Z',
        ],
        'uptime_reporting_end': [
            '2024-12-01T02:00:00Z',
            '2024-12-01T02:00:00Z',
            '2025-12-01T11:00:00Z',
            '2025-12-01T11:00:00Z',
            '2025-12-01T15:00:00Z',
            '2025-12-01T15:00:00Z',
        ],
        'uptime': ["", "7", "", "7", "7", "7"],
        'total_outage': ["3", "8", "12", "17", "21", "26"],
        'total_outage_excl': ["4", "9", "13", "18", "23", "13"],
    })

    validation_options = {
        "feature_toggle_set": {},
        "df": df,
        "cursor": MagicMock()
    }
    response = validate_m3.validate_operational_one_year(validation_options)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {2} == error_row_set
    assert {0, 1, 3, 4, 5} & error_row_set == set()

    assert len(response.get('conditions', [])) == 1
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MODULE_3_UPTIME_REQUIRED.value
    assert response['conditions'][0]['header_name'] == 'uptime'


@patch("module_validation.validate_m3.get_operational_date")
def test_qa_feedback_1(mock_get_operational_date):
    mock_get_operational_date.return_value = date(year=2024, month=7, day=4)

    df = pandas.DataFrame({
        'station_id': ["StationW1", "StationW1", "StationW1"],
        'network_provider': ["ampup", "ampup", "ampup"],
        'port_id': ["port-id-qa3", "port-id-qa3", "port-id-qa6"],
        'uptime_reporting_start': [
            '2025-12-01T10:52:53Z',
            '2025-12-01T10:52:53Z',
            '2024-07-03T10:52:53Z'
        ],
        'uptime_reporting_end': [
            '2025-12-01T11:53:50Z',
            '2025-12-01T11:53:50Z',
            '2024-12-01T11:53:50Z'
        ],
        'uptime': [None, "", "345.23"],
        'total_outage': ["800000.12", "800000.12", "800000.12"],
        'total_outage_excl': ["800000.12", "800000.12", "800000.12"]
    })

    validation_options = {
        "feature_toggle_set": {},
        "df": df,
        "cursor": MagicMock()
    }
    response = validate_m3.validate_operational_one_year(validation_options)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {0, 1} == error_row_set
    assert {2} & error_row_set == set()

    assert len(response.get('conditions', [])) == 2
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MODULE_3_UPTIME_REQUIRED.value
    assert response['conditions'][0]['header_name'] == 'uptime'


@patch("module_validation.validate_m3.get_operational_date")
def test_qa_feedback_2(mock_get_operational_date):
    mock_get_operational_date.return_value = date(year=2024, month=7, day=4)

    df = pandas.DataFrame({
        'station_id': ["ModJE5779", "ModJE5779"],
        'network_provider': ["ampup", "ampup"],
        'port_id': ["port-id-qa3", "port-id-qa3"],
        'uptime_reporting_start': [
            '2025-12-01T10:52:23Z',
            '2025-12-01T10:52:23Z'
        ],
        'uptime_reporting_end': [
            '2025-12-01T11:53:50Z',
            '2025-12-01T11:53:50Z'
        ],
        'uptime': ["", None],
        'total_outage': ["800000.12", "800000.12"],
        'total_outage_excl': ["800000.12", "800000.12"]
    })

    validation_options = {
        "feature_toggle_set": {},
        "df": df,
        "cursor": MagicMock()
    }
    response = validate_m3.validate_operational_one_year(validation_options)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {0, 1} == error_row_set

    assert len(response.get('conditions', [])) == 2
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MODULE_3_UPTIME_REQUIRED.value
    assert response['conditions'][0]['header_name'] == 'uptime'

