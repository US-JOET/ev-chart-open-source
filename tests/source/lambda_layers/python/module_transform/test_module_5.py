import pandas
from pandas.testing import assert_frame_equal, assert_series_equal

from feature_toggle.feature_enums import Feature
from module_transform.transform_m5 import allow_null_federal_maintenance


def test_allow_null_federal_maintenance():
    source_record = {
        'station_id': ["APIM4"],
        'caas': ["FALSE"],
        'maintenance_cost_federal': ["123.45"],
        'maintenance_cost_total': [""],
        'maintenance_report_start': ["2023-07-02T12:51:48Z"],
        'maintenance_report_end': ["2023-07-03T12:51:4Z"],
        'maintenance_notes': ["No notes"],
        'project_id': ["project_1"]
    }
    unchanged_fields = [
        'station_id',
        'caas',
        'maintenance_cost_federal',
        'maintenance_report_start',
        'maintenance_report_end',
        'maintenance_notes',
        'project_id'
    ]
    df = pandas.DataFrame(source_record)
    response = allow_null_federal_maintenance({Feature.MODULE_5_NULLS}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])
    assert_series_equal(
        response['maintenance_cost_total'],
        pandas.Series(
            [None],
            dtype=pandas.Int64Dtype,
            name='maintenance_cost_total'
        )
    )

def test_allow_null_federal_maintenance_bizmagic():
    source_record = {
        'station_id': ["APIM4"],
        'caas': ["FALSE"],
        'maintenance_cost_federal': ["123.45"],
        'maintenance_cost_total': [""],
        'maintenance_report_start': ["2023-07-02T12:51:48Z"],
        'maintenance_report_end': ["2023-07-03T12:51:4Z"],
        'maintenance_notes': ["No notes"],
        'project_id': ["project_1"]
    }
    unchanged_fields = [
        'station_id',
        'caas',
        'maintenance_cost_federal',
        'maintenance_report_start',
        'maintenance_report_end',
        'maintenance_notes',
        'project_id'
    ]
    df = pandas.DataFrame(source_record)
    response = allow_null_federal_maintenance({Feature.ASYNC_BIZ_MAGIC_MODULE_5}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])
    assert_series_equal(
        response['maintenance_cost_total'],
        pandas.Series(
            [None],
            dtype=pandas.Int64Dtype,
            name='maintenance_cost_total'
        )
    )

def test_allow_non_null_workflow_bizmagic():
    source_record = {
        'station_id': ["APIM4"],
        'caas': ["FALSE"],
        'maintenance_cost_federal': ["123.45"],
        'maintenance_cost_total': ["1394011.23"],
        'maintenance_report_start': ["2023-07-02T12:51:48Z"],
        'maintenance_report_end': ["2023-07-03T12:51:4Z"],
        'maintenance_notes': ["No notes"],
        'project_id': ["project_1"]
    }
    unchanged_fields = [
        'station_id',
        'caas',
        'maintenance_cost_federal',
        'maintenance_report_start',
        'maintenance_report_end',
        'maintenance_notes',
        'project_id'
    ]
    df = pandas.DataFrame(source_record)
    response = allow_null_federal_maintenance({Feature.ASYNC_BIZ_MAGIC_MODULE_5}, df)
    assert_frame_equal(df[unchanged_fields], response[unchanged_fields])
    assert_series_equal(
        response['maintenance_cost_total'],
        pandas.Series(
            data=response['maintenance_cost_total'][0],
            dtype=pandas.Float64Dtype,
            name='maintenance_cost_total'
        )
    )
