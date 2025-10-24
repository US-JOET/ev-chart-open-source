import pandas
from pandas.testing import assert_frame_equal

from feature_toggle.feature_enums import Feature
from module_transform.transform_m4 import allow_null_outages


def test_allow_allow_null_outages_with_biz():
    source_record = {
        'station_id': ["APIM4"],
        'port_id': ["354321"],
        'outage_id': [""],
        'outage_duration': [""],
        'network_provider': ["abm"]
    }
    unchanged_fields = ['station_id', 'port_id']
    df = pandas.DataFrame(source_record)
    response = allow_null_outages({Feature.ASYNC_BIZ_MAGIC_MODULE_4}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])
    assert "user_reports_no_data" in response.columns
    assert response.loc[0, 'user_reports_no_data'] == 1
    assert response['outage_id'].dtype == 'datetime64[ns]'
    assert isinstance(response.loc[0, 'outage_id'], pandas.Timestamp)

# JE-6997 prod issue where valid outage_ids get overwritten after an empty row of data
def test_mod_4_bug_overwritten_outage_ids():
    source_record = {
        'station_id': ["7.21","diff","7.17","7.11",],
        'port_id': ["111", "222", "333", "444"],
        'outage_id': ["2024-05-29T21:13:00", "", "2025-04-25T21:13:00", "2025-03-15T21:13:00"],
        'outage_duration': ["44","", "78", "75"],
        'network_provider': ["abm", "autel", "7charge", "ampup"]
    }
    df = pandas.DataFrame(source_record)
    response = allow_null_outages({Feature.ASYNC_BIZ_MAGIC_MODULE_4}, df)
    assert response['outage_id'].dtype == 'datetime64[ns]'
    assert isinstance(response.loc[0, 'outage_id'], pandas.Timestamp)

