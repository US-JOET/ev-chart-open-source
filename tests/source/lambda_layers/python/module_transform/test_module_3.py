import pandas
from pandas.testing import assert_frame_equal, assert_series_equal
import pytest

from feature_toggle.feature_enums import Feature
from module_transform.transform_m3 import allow_null_uptime


def test_allow_null_uptime_nulls_no_toggle_error():
    source_record = {
        'station_id': ["APIM4"],
        'port_id': ["354321"],
        'uptime': ["null_less_than_a_year"],
        'total_outage': [0.1]
    }

    df = pandas.DataFrame(source_record)
    # null_less_than_a_year is no longer a valid value
    with pytest.raises(ValueError):
        allow_null_uptime({}, df)


def test_allow_null_uptime_biz_magic():
    source_record = {
        'station_id': ["APIM4", "APIM4"],
        'port_id': ["354321", "354321"],
        'uptime': ["", 1],
        'total_outage': [0.1, 0.1]
    }
    unchanged_fields = ['station_id', 'port_id', 'total_outage']
    df = pandas.DataFrame(source_record)
    response = allow_null_uptime({Feature.ASYNC_BIZ_MAGIC_MODULE_3}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])
    assert_series_equal(
        response['uptime'],
        pandas.Series([None, 1], dtype=pandas.Int64Dtype, name='uptime')
    )
    assert_series_equal(
        response['user_reports_no_data'],
        pandas.Series([1, 0], dtype=pandas.Int64Dtype, name='user_reports_no_data')
    )