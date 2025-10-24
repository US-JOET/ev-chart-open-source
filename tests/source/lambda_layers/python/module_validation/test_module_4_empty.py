from module_validation import validate_m4
from feature_toggle.feature_enums import Feature
from error_report_messages_enum import ErrorReportMessages

import pandas


def test_records_with_empty_values():
    df = pandas.DataFrame({
        "station_id": ["s1", "s2", "s3", "s4"],
        "network_provider": ["np1", "np2", "np3", "np4"],
        "port_id": ["p1", "p2", "p3", "p4"],
        "outage_id": ["2015-06-29T20:39:09Z", "", "", "2015-06-29T20:39:09"],
        "outage_duration": ["123.45", "", "67.89", ""]
    })

    validation_options = {
        "feature_toggle_set": set([Feature.BIZ_MAGIC]),
        "df": df
    }
    response = validate_m4.validate_empty_outage(validation_options)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {2, 3} == error_row_set
    assert {0, 1}.intersection(error_row_set) == set()

    assert len(response.get('conditions', [])) == 2
    assert response['conditions'][0]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='outage_id')
    assert response['conditions'][0]['header_name'] == 'outage_id'
    assert response['conditions'][1]['error_description'] == \
        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name='outage_duration')
    assert response['conditions'][1]['header_name'] == 'outage_duration'


def test_biz_magic_ft_off():
    validation_options = {
        "feature_toggle_set": set(),
        "df": pandas.DataFrame()
    }
    response = validate_m4.validate_empty_outage(validation_options)
    assert response.get('conditions') == []
