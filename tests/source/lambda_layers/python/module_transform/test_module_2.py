import pandas
from pandas.testing import assert_frame_equal, assert_series_equal

from feature_toggle.feature_enums import Feature
from module_transform.transform_m2 import allow_null_charging_sessions


def test_allow_null_charging_sessions():
    source_record = {
        'session_id': [""],
        'payment_method': ["visa"],
        'payment_other': ["other"],
        'session_start': ['2023-07-03T12:51:48Z'],
        'session_end': ['2023-07-07T12:51:48Z'],
        'session_error': ['error'],
        'energy_kwh': [''],
        'power_kw': ['']
    }
    unchanged_fields = ['payment_method', 'payment_other', 'session_error']
    df = pandas.DataFrame(source_record)
    response = allow_null_charging_sessions({Feature.ASYNC_BIZ_MAGIC_MODULE_2}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])
    assert_series_equal(
        response['energy_kwh'],
        pandas.Series([None], dtype=pandas.Int64Dtype(), name='energy_kwh')
    )
    assert_series_equal(
        response['power_kw'],
        pandas.Series([None], dtype=pandas.Int64Dtype(), name='power_kw')
    )
    assert response.loc[0, 'session_id'].startswith('NoSession')


def test_allow_empty_charging_sessions():
    source_record = {
        'session_id': ["", "123"],
        'payment_method': ["visa", "visa"],
        'payment_other': ["other", "other"],
        'session_start': ['2023-07-03T12:51:48Z', '2023-07-03T12:51:48Z'],
        'session_end': ['2023-07-07T12:51:48Z', '2023-07-03T12:51:48Z'],
        'session_error': ['error', 'error'],
        'energy_kwh': ['', '12'],
        'power_kw': ['', '12']
    }
    unchanged_fields = ['payment_method', 'payment_other', 'session_error']
    df = pandas.DataFrame(source_record)
    response = allow_null_charging_sessions(
        {Feature.ASYNC_BIZ_MAGIC_MODULE_2}, df
    )
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])
    assert_series_equal(
        response['energy_kwh'],
        pandas.Series([None, '12'], dtype=pandas.Int64Dtype, name='energy_kwh')
    )
    assert_series_equal(
        response['power_kw'],
        pandas.Series([None, '12'], dtype=pandas.Int64Dtype, name='power_kw')
    )
    assert response.loc[0, 'session_id'].startswith('NoSession')
    assert not response.loc[1, 'session_id'].startswith('NoSession')
    assert response.loc[0, 'user_reports_no_data'] == 1
    assert response.loc[1, 'user_reports_no_data'] == 0
