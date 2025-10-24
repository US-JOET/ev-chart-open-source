import os
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import feature_toggle
import pandas
import pytest

# module paths are set in conftest.py
from APIGetModuleData.index import (
    check_submitting_null,
    convert_empty_datetime,
    format_dataframe_bool,
    format_dataframe_date,
    get_dataframe,
    get_module_data_by_table_name,
    get_right_headers,
    get_UI_col_names_map,
)
from APIGetModuleData.index import handler as api_get_module_data
from APIGetModuleData.index import set_null_data
from dateutil import tz
from evchart_helper.custom_exceptions import (
    EvChartJsonOutputError,
    EvChartMissingOrMalformedHeadersError,
    EvChartUnknownException,
    EvChartUserNotAuthorizedError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.module_enums import ModulePrimary
from evchart_helper.module_helper import validate_headers
from feature_toggle.feature_enums import Feature


def cursor():
    return MagicMock()


def log():
    return MagicMock()


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetModuleData.index.aurora")
def test_handler_return(mock_aurora, mock_feature_toggle):
    mock_feature_toggle.get_feature_toggle_by_enum.side_effect = "True"
    response = api_get_module_data({"headers": {}}, None)
    assert response.get("statusCode") == 401
    assert mock_aurora.get_connection.called


@patch("evchart_helper.module_helper.is_valid_upload_id")
def test_validate_headers_invalid_upload_id(mock_upload_id_response):
    mock_upload_id_response.return_value = False

    with pytest.raises(EvChartMissingOrMalformedHeadersError):
        validate_headers("123", "111", "direct-recipient", cursor())
        # assert response.get('statusCode') == 400  this does nothing,
        # need handler test to view status code


@patch("evchart_helper.module_helper.is_org_authorized_to_view_data")
@patch("evchart_helper.module_helper.is_valid_upload_id")
def test_validate_headers_invalid_org(mock_upload_id_response, mock_org_response):
    mock_upload_id_response.return_value = True
    mock_org_response.return_value = False

    with pytest.raises(EvChartUserNotAuthorizedError):
        validate_headers("123", "111", "direct-recipient", cursor())
        # assert response.get('statusCode') == 403 this does nothing,
        # need handler test to view status code


@patch("evchart_helper.module_helper.is_org_authorized_to_view_data")
@patch("evchart_helper.module_helper.is_valid_upload_id")
def test_validate_headers_valid_org(mock_upload_id_response, mock_org_response):
    mock_upload_id_response.return_value = True
    mock_org_response.return_value = True

    response = validate_headers("123", "111", "direct-recipient", cursor())
    assert response is True


def test_get_right_headers_network_provider_ft_false():
    response = get_right_headers(3, "port_id", {})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "uptime_reporting_start",
        "uptime_reporting_end",
        "uptime",
        "total_outage",
        "total_outage_excl",
    ]
    assert response == expected


def test_get_right_headers_network_provider_ft_true():
    response = get_right_headers(3, "port_id", {})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "uptime_reporting_start",
        "uptime_reporting_end",
        "uptime",
        "total_outage",
        "total_outage_excl",
    ]
    assert response == expected


def test_get_right_headers_ft_biz_magic_m4_true():
    response = get_right_headers("4", "outage_id", {Feature.ASYNC_BIZ_MAGIC_MODULE_4})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "port_id",
        "outage_duration",
        "user_reports_no_data",
    ]
    assert response == expected


def test_get_right_headers_ft_biz_magic_m4_false():
    response = get_right_headers("4", "outage_id", {})
    expected = ["station_id_upload", "network_provider_upload", "port_id", "outage_duration"]
    assert response == expected


def test_get_right_headers_ft_biz_magic_m3_true():
    response = get_right_headers("3", "outage_id", {Feature.ASYNC_BIZ_MAGIC_MODULE_3})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "port_id",
        "uptime_reporting_start",
        "uptime_reporting_end",
        "uptime",
        "total_outage",
        "total_outage_excl",
        "user_reports_no_data",
    ]
    assert response == expected


def test_get_right_headers_ft_biz_magic_m3_false():
    response = get_right_headers("3", "outage_id", {})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "port_id",
        "uptime_reporting_start",
        "uptime_reporting_end",
        "uptime",
        "total_outage",
        "total_outage_excl",
    ]
    assert response == expected


def test_get_right_headers_ft_biz_magic_m2_true():
    response = get_right_headers("2", "outage_id", {Feature.ASYNC_BIZ_MAGIC_MODULE_2})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "port_id",
        "charger_id",
        "session_id",
        "connector_id",
        "session_start",
        "session_end",
        "session_error",
        "error_other",
        "energy_kwh",
        "power_kw",
        "payment_method",
        "payment_other",
        "user_reports_no_data",
    ]
    assert response == expected


def test_get_right_headers_ft_biz_magic_m2_false():
    response = get_right_headers("2", "outage_id", {})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "port_id",
        "charger_id",
        "session_id",
        "connector_id",
        "session_start",
        "session_end",
        "session_error",
        "error_other",
        "energy_kwh",
        "power_kw",
        "payment_method",
        "payment_other",
    ]
    assert response == expected


def test_get_right_headers_ft_biz_magic_m9_true():
    response = get_right_headers("9", "", {Feature.ASYNC_BIZ_MAGIC_MODULE_9})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "project_id",
        "station_upgrade",
        "real_property_acq_date",
        "real_property_acq_owned",
        "real_property_cost_total",
        "real_property_cost_federal",
        "equipment_acq_date",
        "equipment_acq_owned",
        "equipment_cost_total",
        "equipment_cost_federal",
        "equipment_install_date",
        "equipment_install_cost_total",
        "equipment_install_cost_federal",
        "equipment_install_cost_elec",
        "equipment_install_cost_const",
        "equipment_install_cost_labor",
        "equipment_install_cost_other",
        "der_acq_owned",
        "der_cost_federal",
        "der_cost_total",
        "der_install_cost_total",
        "der_install_cost_federal",
        "dist_sys_cost_total",
        "dist_sys_cost_federal",
        "service_cost_total",
        "service_cost_federal",
        "user_reports_no_data",
    ]
    assert response == expected


def test_get_right_headers_ft_biz_magic_m9_false():
    response = get_right_headers("9", "", {})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "project_id",
        "station_upgrade",
        "real_property_acq_date",
        "real_property_acq_owned",
        "real_property_cost_total",
        "real_property_cost_federal",
        "equipment_acq_date",
        "equipment_acq_owned",
        "equipment_cost_total",
        "equipment_cost_federal",
        "equipment_install_date",
        "equipment_install_cost_total",
        "equipment_install_cost_federal",
        "equipment_install_cost_elec",
        "equipment_install_cost_const",
        "equipment_install_cost_labor",
        "equipment_install_cost_other",
        "der_acq_owned",
        "der_cost_federal",
        "der_cost_total",
        "der_install_cost_total",
        "der_install_cost_federal",
        "dist_sys_cost_total",
        "dist_sys_cost_federal",
        "service_cost_total",
        "service_cost_federal",
    ]
    assert response == expected


def test_get_module_data_by_table_name_without_boolean_and_datetime_objs():
    mock_cursor = cursor()
    mock_cursor.fetchall.return_value = [
        ("TestStation1", "minority_owned, women_owned", None, 2023),
    ]
    mock_cursor.description = [
        ("station_id", 253, None, 144, 144, 0, False),
        ("opportunity_program", 253, None, 1020, 1020, 0, False),
        ("program_descript", 253, None, 1020, 1020, 0, True),
        ("program_report_year", 3, None, 11, 11, 0, False),
    ]

    upload_id = "3fcbda65-7007-492b-b8f2-8dc90b58c309"
    left_header = "station_id"
    db_table = "module7_data_v3"
    right_headers = [d[0] for d in mock_cursor.description]
    is_truncated = False

    result_df = get_module_data_by_table_name(
        upload_id, left_header, right_headers, db_table, mock_cursor, is_truncated
    )
    result = result_df["data"].to_dict(orient="records")
    expected = [
        {
            "station_id": "TestStation1",
            "opportunity_program": "minority_owned, women_owned",
            "program_descript": None,
            "program_report_year": 2023,
        }
    ]
    assert result == expected


@pytest.mark.skipif(os.name == "nt", reason="format_datetime_obj does not work on windows")
def test_get_module_data_by_table_name_with_boolean_and_datetime_objs():
    mock_cursor = cursor()
    utc_tz = tz.gettz("UTC")
    mock_cursor.fetchall.return_value = [
        (
            None,
            "707b7bb3-4fb8-41f5-9c23-79e835e67331",
            Decimal("1394011.23"),
            Decimal("1394011.23"),
            datetime(2023, 12, 31, 23, 59, 59, tzinfo=utc_tz),
            datetime(2023, 1, 1, 0, 0, tzinfo=utc_tz),
            None,
        ),
    ]
    mock_cursor.description = [
        ("caas", 1, None, 1, 1, 0, True),
        ("station_id", 253, None, 144, 144, 0, False),
        ("maintenance_cost_federal", 246, None, 11, 11, 2, False),
        ("maintenance_cost_total", 246, None, 11, 11, 2, False),
        ("maintenance_report_end", 12, None, 19, 19, 0, False),
        ("maintenance_report_start", 12, None, 19, 19, 0, False),
        ("project_id", 253, None, 144, 144, 0, True),
    ]

    upload_id = "3fcbda65-7007-492b-b8f2-8dc90b58c309"
    left_header = "station_id"
    db_table = "module5_data_v3"
    right_headers = [d[0] for d in mock_cursor.description]
    is_truncated = False

    result_df = get_module_data_by_table_name(
        upload_id, left_header, right_headers, db_table, mock_cursor, is_truncated
    )
    result = result_df["data"].to_dict(orient="records")
    # added zeros up front for testing right now as I can't get %-I working
    expected = [
        {
            "station_id": "707b7bb3-4fb8-41f5-9c23-79e835e67331",
            "caas": "",
            "maintenance_cost_federal": Decimal("1394011.23"),
            "maintenance_cost_total": Decimal("1394011.23"),
            "maintenance_report_end": "12/31/23 11:59 PM UTC",
            "maintenance_report_start": "01/01/23 12:00 AM UTC",
            "project_id": None,
        }
    ]
    assert result[0]["station_id"] == expected[0]["station_id"]
    assert result[0]["caas"] == expected[0]["caas"]
    assert result[0]["maintenance_cost_federal"] == expected[0]["maintenance_cost_federal"]
    assert result[0]["maintenance_cost_total"] == expected[0]["maintenance_cost_total"]
    assert result[0]["maintenance_report_end"] == expected[0]["maintenance_report_end"]
    assert result[0]["maintenance_report_start"] == expected[0]["maintenance_report_start"]
    assert result[0]["project_id"] == expected[0]["project_id"]
    assert result == expected  # check order


def test_unchanged_bool_in_df():
    # test_format_dataframe_bool_given_column_not_
    # in_bool_list_value_is_unchanged
    test_data = [0, 1]
    column_name = "upload_id"
    df = pandas.DataFrame({column_name: test_data})
    format_dataframe_bool(df)
    assert df[column_name][0] == 0
    assert df[column_name][1] == 1


@pytest.mark.parametrize(
    "column_name",
    [
        ("caas"),
        ("der_upgrade"),
        ("der_onsite"),
        ("station_upgrade"),
        ("real_property_acq_type"),
        ("real_property_acq_owned"),
        ("equipment_acq_type"),
        ("equipment_acq_owned"),
        ("der_acq_type"),
        ("der_acq_owned"),
        ("station_upgrade"),
    ],
)
def test_format_dataframe_bool_given_bool_column_name_converts_to_string_bool(column_name):
    test_data = [0, 1]
    df = pandas.DataFrame({column_name: test_data})
    format_dataframe_bool(df)
    assert df[column_name][0] == "FALSE"
    assert df[column_name][1] == "TRUE"


def test_format_dataframe_date_with_non_datetime_field_does_nothing():
    test_data = [0]
    column_name = "upload_id"
    df = pandas.DataFrame({column_name: test_data})
    format_dataframe_date(df)
    assert df[column_name][0] == 0


@pytest.mark.skipif(os.name == "nt", reason="format_datetime_obj does not work on windows")
def test_format_dataframe_date_with_datetime_changes_timezone_and_formats():
    utc_tz = tz.gettz("UTC")
    test_data = [datetime(2023, 12, 31, 23, 59, 59, tzinfo=utc_tz)]
    column_name = "does_not_matter"
    df = pandas.DataFrame({column_name: test_data})
    format_dataframe_date(df)
    assert df[column_name][0] == "12/31/23 11:59 PM UTC"


@pytest.mark.skip("this is no longer expected behavior, remove in future")
def test_get_dataframe_drops_upload_id():
    mock_cursor = cursor()
    utc_tz = tz.gettz("UTC")
    mock_cursor.fetchall.return_value = [
        (
            None,
            "707b7bb3-4fb8-41f5-9c23-79e835e67331",
            Decimal("1394011.23"),
            Decimal("1394011.23"),
            datetime(2023, 12, 31, 23, 59, 59, tzinfo=utc_tz),
            datetime(2023, 1, 1, 0, 0, tzinfo=utc_tz),
            None,
            "68abc887-c8e4-45f7-bec8-fe9f80b2998e",
        ),
    ]
    mock_cursor.description = [
        ("caas", 1, None, 1, 1, 0, True),
        ("station_id", 253, None, 144, 144, 0, False),
        ("maintenance_cost_federal", 246, None, 11, 11, 2, False),
        ("maintenance_cost_total", 246, None, 11, 11, 2, False),
        ("maintenance_report_end", 12, None, 19, 19, 0, False),
        ("maintenance_report_start", 12, None, 19, 19, 0, False),
        ("project_id", 253, None, 144, 144, 0, True),
        ("upload_id", 253, None, 144, 144, 0, True),
    ]
    right_headers = [d[0] for d in mock_cursor.description]

    upload_id = 1
    db_table = "module5"
    df = get_dataframe(upload_id, db_table, right_headers, mock_cursor)
    assert "upload_id" not in df.columns


def test_get_column_table_names_network_provider_ft_false():
    left_header = [ModulePrimary["Module7"].value]
    right_header = get_right_headers(7, left_header[0], {})
    response = get_UI_col_names_map(7, left_header + right_header)

    expected = {
        "station_id_upload": "Station ID",
        "program_report_year": "Opportunity Program Reporting Year",
        "opportunity_program": "Opportunity Program Participation",
        "program_descript": "Opportunity Program Description",
        "network_provider_upload": "Network Provider",
    }
    assert response == expected, f"{response=}"


def test_get_column_table_names_network_provider_ft_true():
    left_header = [ModulePrimary["Module7"].value]
    right_header = get_right_headers(7, left_header[0], {})
    response = get_UI_col_names_map(7, left_header + right_header)

    expected = {
        "station_id_upload": "Station ID",
        "network_provider_upload": "Network Provider",
        "program_report_year": "Opportunity Program Reporting Year",
        "opportunity_program": "Opportunity Program Participation",
        "program_descript": "Opportunity Program Description",
    }
    assert response == expected, f"{response=}"


def test_missing_column_field():
    left_header = [ModulePrimary["Module7"].value]
    right_header = get_right_headers(7, left_header[0], {})
    with pytest.raises(EvChartJsonOutputError):
        get_UI_col_names_map(7, left_header + right_header + ["unkown_variable"])


def test_truncation():
    mock_cursor = cursor()
    mock_cursor.fetchall.return_value = []
    for _x in range(1100):
        mock_cursor.fetchall.return_value.append(
            ("TestStation1", "minority_owned, women_owned", None, 2023)
        )
    mock_cursor.description = [
        ("station_id", 253, None, 144, 144, 0, False),
        ("opportunity_program", 253, None, 1020, 1020, 0, False),
        ("program_descript", 253, None, 1020, 1020, 0, True),
        ("program_report_year", 3, None, 11, 11, 0, False),
    ]

    upload_id = "3fcbda65-7007-492b-b8f2-8dc90b58c309"
    left_header = "station_id"
    db_table = "module7_data_v3"
    right_headers = [d[0] for d in mock_cursor.description]
    is_truncated = False

    result_df = get_module_data_by_table_name(
        upload_id, left_header, right_headers, db_table, mock_cursor, is_truncated
    )
    result = result_df["data"].to_dict(orient="records")
    assert len(result) == 1000


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_is_submitting_null_4_true(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"

    raw = [
        ["APIM4", 354321, "2023-07-03T12:51:48Z", 123248.92],
        ["APIM5", 354321, "", ""],
        ["APIM9", 354321, "2023-07-03T12:51:48Z", 123248.92],
        ["APIM10", 354321, "2023-07-03T12:51:48Z", 123248.92],
        ["APIM11", 354321, "2023-07-03T12:51:48Z", 123248.92],
    ]

    df = pandas.DataFrame(raw, columns=["station_id", "port_id", "outage_id", "outage_duration"])

    response = check_submitting_null(df, False, "4")
    assert response


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_is_submitting_null_4_false(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"

    raw = [
        ["APIM4", 354321, "2023-07-03T12:51:48Z", 123248.92],
        ["APIM5", 354321, "2023-07-03T12:51:48Z", 123248.92],
        ["APIM9", 354321, "2023-07-03T12:51:48Z", 123248.92],
        ["APIM10", 354321, "2023-07-03T12:51:48Z", 123248.92],
        ["APIM11", 354321, "2023-07-03T12:51:48Z", 123248.92],
    ]

    df = pandas.DataFrame(raw, columns=["station_id", "port_id", "outage_id", "outage_duration"])

    response = check_submitting_null(df, False, "4")
    assert not response


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_is_submitting_null_9_true(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"

    raw = [
        [
            "QA155561",
            "NULL",
            2800.89,
            "NULL",
            4800.89,
            "NULL",
            6800.89,
            "NULL",
            8800.89,
            "NULL",
            10800.89,
            "NULL",
            12345,
            "NULL",
            14800.89,
        ]
    ]

    df = pandas.DataFrame(
        raw,
        columns=[
            "station_id",
            "real_property_cost_total",
            "real_property_cost_federal",
            "equipment_cost_total",
            "equipment_cost_federal",
            "equipment_install_cost_total",
            "equipment_install_cost_federal",
            "der_cost_total",
            "der_cost_federal",
            "der_install_cost_total",
            "der_install_cost_federal",
            "dist_sys_cost_total",
            "dist_sys_cost_federal",
            "service_cost_total",
            "service_cost_federal",
        ],
    )

    response = check_submitting_null(df, False, "9")
    assert response


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_is_submitting_null_9_false(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"

    raw = [
        [
            "QA155561",
            2800,
            2800.89,
            "100",
            4800.89,
            "100",
            6800.89,
            "100",
            8800.89,
            "100",
            10800.89,
            "100",
            12345,
            "100",
            14800.89,
        ]
    ]

    df = pandas.DataFrame(
        raw,
        columns=[
            "station_id",
            "real_property_cost_total",
            "real_property_cost_federal",
            "equipment_cost_total",
            "equipment_cost_federal",
            "equipment_install_cost_total",
            "equipment_install_cost_federal",
            "der_cost_total",
            "der_cost_federal",
            "der_install_cost_total",
            "der_install_cost_federal",
            "dist_sys_cost_total",
            "dist_sys_cost_federal",
            "service_cost_total",
            "service_cost_federal",
        ],
    )

    response = check_submitting_null(df, False, "9")
    assert not response


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_is_submitting_null_9_onlyrequired(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"
    raw = ["23434", "QA155561", "NULL"]

    df = pandas.DataFrame(
        [raw], columns=["der_install_cost_federal", "station_id", "der_install_cost_total"]
    )

    response = check_submitting_null(df, False, "9")
    assert response


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_is_submitting_null_9_notonlyrequired(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"

    raw = [["NULL", "QA155561"]]

    df = pandas.DataFrame(raw, columns=["der_install_cost_federal", "station_id"])

    response = check_submitting_null(df, False, "9")
    assert not response


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_is_submitting_null_2_false(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"

    raw = [
        [
            "APIM4",
            "123",
            "123",
            "123435",
            "144234",
            "2023-07-03T12:51:48Z",
            "2023-07-03T12:51:48Z",
            "error",
            "other",
            1.23,
            5.67,
            "visa",
            "desc",
        ]
    ]

    df = pandas.DataFrame(
        raw,
        columns=[
            "station_id",
            "port_id",
            "charger_id",
            "session_id",
            "connector_id",
            "session_start",
            "session_end",
            "session_error",
            "error_other",
            "energy_kwh",
            "power_kw",
            "payment_method",
            "payment_other",
        ],
    )

    response = check_submitting_null(df, False, "2")
    assert not response


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_is_submitting_null_2_true(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"

    raw = [
        [
            "APIM4",
            "123",
            "",
            "123435",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ]
    ]

    df = pandas.DataFrame(
        raw,
        columns=[
            "station_id",
            "port_id",
            "charger_id",
            "session_id",
            "connector_id",
            "session_start",
            "session_end",
            "session_error",
            "error_other",
            "energy_kwh",
            "power_kw",
            "payment_method",
            "payment_other",
        ],
    )
    response = check_submitting_null(df, True, "2")
    assert response


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_is_submitting_null_2_not_required_false(mock_feature_toggle):
    mock_feature_toggle.return_value = "True"

    raw = [
        [
            "APIM4",
            "123",
            "123",
            "123435",
            "144234",
            "2023-07-03T12:51:48Z",
            "2023-07-03T12:51:48Z",
            "error",
            "other",
            5.67,
            5.67,
            "visa",
            "",
        ]
    ]

    df = pandas.DataFrame(
        raw,
        columns=[
            "station_id",
            "port_id",
            "charger_id",
            "session_id",
            "connector_id",
            "session_start",
            "session_end",
            "session_error",
            "error_other",
            "energy_kwh",
            "power_kw",
            "payment_method",
            "payment_other",
        ],
    )

    response = check_submitting_null(df, False, "2")
    assert not response


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_set_null_data_9(_mock_feature_toggle):

    raw = [["TRUE", "QA155561", None, None, None, None, None, None, None, None, None, None, None, None,]]
    df = pandas.DataFrame(
        raw,
        columns=[
            "user_reports_no_data",
            "station_id",
            "real_property_cost_total",
            "equipment_cost_total",
            "equipment_install_cost_total",
            "equipment_install_cost_elec",
            "equipment_install_cost_const",
            "equipment_install_cost_labor",
            "equipment_install_cost_other",
            "der_acq_owned",
            "der_cost_total",
            "der_install_cost_total",
            "dist_sys_cost_total",
            "service_cost_total",
        ],
    )

    expected_raw = [["TRUE", "QA155561", "",  "", "", "", "", "", "", "",  "", "", "", ""]]
    expected_df = pandas.DataFrame(
        expected_raw,
        columns=[
            "user_reports_no_data",
            "station_id",
            "real_property_cost_total",
            "equipment_cost_total",
            "equipment_install_cost_total",
            "equipment_install_cost_elec",
            "equipment_install_cost_const",
            "equipment_install_cost_labor",
            "equipment_install_cost_other",
            "der_acq_owned",
            "der_cost_total",
            "der_install_cost_total",
            "dist_sys_cost_total",
            "service_cost_total",
        ],
    )

    response = set_null_data({Feature.ASYNC_BIZ_MAGIC_MODULE_9}, 9, df)
    assert response.to_string() == expected_df.to_string()


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_empty_datetimes_9(_mock_feature_toggle):
    raw = [
        [
            None,
            "QA155561",
            "NULL",
            100.7,
            "NULL",
            "NULL",
            "NULL",
            "NULL",
            467.4,
            "0000-00-00 00:00:00",
            "0000-00-00 00:00:00",
            "0000-00-00 00:00:00",
        ]
    ]
    df = pandas.DataFrame(
        raw,
        columns=[
            "der_install_cost_federal",
            "station_id",
            "real_property_cost_total",
            "equipment_cost_total",
            "equipment_install_cost_total",
            "der_cost_total",
            "der_install_cost_total",
            "dist_sys_cost_total",
            "service_cost_total",
            "real_property_acq_date",
            "equipment_acq_date",
            "equipment_install_date",
        ],
    )

    expected_raw = [
        [None, "QA155561", "NULL", 100.7, "NULL", "NULL", "NULL", "NULL", 467.4, "", "", ""]
    ]
    expected_df = pandas.DataFrame(
        expected_raw,
        columns=[
            "der_install_cost_federal",
            "station_id",
            "real_property_cost_total",
            "equipment_cost_total",
            "equipment_install_cost_total",
            "der_cost_total",
            "der_install_cost_total",
            "dist_sys_cost_total",
            "service_cost_total",
            "real_property_acq_date",
            "equipment_acq_date",
            "equipment_install_date",
        ],
    )

    response = convert_empty_datetime(df)
    assert response.to_string() == expected_df.to_string()


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_set_null_data_5(_mock_feature_toggle):
    raw = [
        [
            123,
            True,
            123.4,
            None,
            "2023-07-03T12:51:48Z",
            "2023-07-02T12:51:48Z",
            "No notes",
            "123",
            "456",
        ]
    ]
    df = pandas.DataFrame(
        raw,
        columns=[
            "station_id",
            "caas",
            "maintenance_cost_federal",
            "maintenance_cost_total",
            "maintenance_report_end",
            "maintenance_report_start",
            "maintenance_notes",
            "project_id",
            "upload_id",
        ],
    )

    expected_raw = [
        [
            123,
            True,
            123.4,
            "NULL",
            "2023-07-03T12:51:48Z",
            "2023-07-02T12:51:48Z",
            "No notes",
            "123",
            "456",
        ]
    ]
    expected_df = pandas.DataFrame(
        expected_raw,
        columns=[
            "station_id",
            "caas",
            "maintenance_cost_federal",
            "maintenance_cost_total",
            "maintenance_report_end",
            "maintenance_report_start",
            "maintenance_notes",
            "project_id",
            "upload_id",
        ],
    )

    response = set_null_data({Feature.MODULE_5_NULLS}, 5, df)
    assert response.to_string() == expected_df.to_string()


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_set_null_data_4_biz_magic(mock_feature_toggle):
    raw = [
        ["APIM4", 354321, "2023-07-03T12:51:48Z", None,None,None,None,"TRUE"],
        ["APIM5", 354321, "2023-07-03T12:51:48Z", 123248.92,1,2,None,"FALSE"],
        ["APIM5", 354321, "2023-07-03T12:51:48Z", 123248.92,0,None,None,"FALSE"],
        ["APIM5", 354321, "2023-07-03T12:51:48Z", 123248.92,None,None,None,"FALSE"],
        ["APIM9", 354321, "2023-07-03T12:51:48Z", None,None,None,None,"TRUE"],
    ]
    df = pandas.DataFrame(
        raw,
        columns=[
            "station_id",
            "port_id",
            "outage_id",
            "outage_duration",
            "excluded_outage",
            "excluded_outage_reason",
            "excluded_outage_notes",
            "user_reports_no_data",
        ],
    )

    expected_raw = [
        ["APIM4", 354321, "", "","","","","TRUE"],
        ["APIM5", 354321, "2023-07-03T12:51:48Z", 123248.92,1.0,2.0,"","FALSE"],
        ["APIM5", 354321, "2023-07-03T12:51:48Z", 123248.92,0.0,"","","FALSE"],
        ["APIM5", 354321, "2023-07-03T12:51:48Z", 123248.92,"","","","FALSE"],
        ["APIM9", 354321, "", "","","","","TRUE"],
    ]

    expected_df = pandas.DataFrame(
        expected_raw,
        columns=[
            "station_id",
            "port_id",
            "outage_id",
            "outage_duration",
            "excluded_outage",
            "excluded_outage_reason",
            "excluded_outage_notes",
            "user_reports_no_data",
        ],
    )

    response = set_null_data({Feature.ASYNC_BIZ_MAGIC_MODULE_4}, 4, df)
    assert response.to_string() == expected_df.to_string()


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_set_null_data_3_biz_magic(mock_feature_toggle):
    raw = [[123, 456, "", 4565.5, "TRUE"], [123, 456, None, 4565.5, "FALSE"]]
    df = pandas.DataFrame(
        raw, columns=["port_id", "station_id", "uptime", "total_outage", "user_reports_no_data"]
    )

    expected_raw = [[123, 456, "", 4565.5, "TRUE"], [123, 456, None, 4565.5, "FALSE"]]
    expected_df = pandas.DataFrame(
        expected_raw,
        columns=["port_id", "station_id", "uptime", "total_outage", "user_reports_no_data"],
    )

    response = set_null_data({Feature.ASYNC_BIZ_MAGIC_MODULE_3}, 3, df)
    assert response.to_string() == expected_df.to_string()


@patch("APIGetModuleData.index.FeatureToggleService.get_feature_toggle_by_enum")
def test_set_null_data_2_biz_magic(mock_feature_toggle):
    raw = [
        ["APIM4", "123", None, "12345", None, None, None, None, None, None, None, None, None, "TRUE"],
        [
            "APIM4",
            "123",
            None,
            "12345",
            "2024",
            "2024",
            "ERROR1",
            None,
            "20241.01",
            "20241.02",
            "VISA",
            None,
            None,
            "FALSE",
        ],
    ]
    df = pandas.DataFrame(
        raw,
        columns=[
            "station_id",
            "port_id",
            "charger_id",
            "session_id",
            "connector_id",
            "session_start",
            "session_end",
            "session_error",
            "error_other",
            "energy_kwh",
            "power_kw",
            "payment_method",
            "payment_other",
            "user_reports_no_data",
        ],
    )

    expected_raw = [
        ["APIM4", "123", "", "", "", "", "", "", "", "", "", "", "", "TRUE"],
        [
            "APIM4",
            "123",
            "",
            "12345",
            "2024",
            "2024",
            "ERROR1",
            "",
            "20241.01",
            "20241.02",
            "VISA",
            "",
            "",
            "FALSE",
        ],
    ]

    expected_df = pandas.DataFrame(
        expected_raw,
        columns=[
            "station_id",
            "port_id",
            "charger_id",
            "session_id",
            "connector_id",
            "session_start",
            "session_end",
            "session_error",
            "error_other",
            "energy_kwh",
            "power_kw",
            "payment_method",
            "payment_other",
            "user_reports_no_data",
        ],
    )

    response = set_null_data({Feature.ASYNC_BIZ_MAGIC_MODULE_2}, 2, df)
    assert response.to_string() == expected_df.to_string()


# JE-5739 Verifying that nested error messages get returned correctly to aid debugging efforts
@patch("APIGetModuleData.index.get_dataframe")
@patch("APIGetModuleData.index.format_dataframe_bool")
@patch("APIGetModuleData.index.format_dataframe_date")
def test_get_module_data_by_table_name_nested_error_message(
    mock_format_date, mock_format_bool, mock_get_df
):
    mock_format_date.side_effect = EvChartJsonOutputError(message="error message ")
    with pytest.raises(EvChartJsonOutputError) as e:
        get_module_data_by_table_name(
            "upload-id", "left-header", ["right-headers"], "db-table", MagicMock(), "download"
        )
    assert (
        e.value.message
        == "EvChartJsonOutputError raised. error message Error thrown in get_module_data_by_table_name()"
    )


@patch("APIGetModuleData.index.get_dataframe")
@patch("APIGetModuleData.index.format_dataframe_bool")
@patch("APIGetModuleData.index.format_dataframe_date")
def test_get_module_data_by_table_name_unknown_exception_500(
    mock_format_date, mock_format_bool, mock_get_df
):
    mock_format_date.side_effect = ValueError()
    with pytest.raises(EvChartUnknownException) as e:
        get_module_data_by_table_name(
            "upload-id", "left-header", ["right-headers"], "db-table", MagicMock(), "download"
        )
    assert e.value.message.startswith(
        "EvChartUnknownException raised. Error thrown in " "get_module_data_by_table_name():"
    )


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetModuleData.index.DatabaseCentralConfig")
@patch("APIGetModuleData.index.get_module_data_by_table_name")
@patch("APIGetModuleData.index.get_module_id")
@patch("APIGetModuleData.index.validate_headers")
@patch("APIGetModuleData.index.aurora")
@patch.object(LogEvent, "is_auth_token_valid")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_config_ft_true(
    mock_feature_toggle_set,
    mock_log_auth_token,
    mock_aurora,
    mock_validate_headers,
    mock_get_module_id,
    mock_get_module_data_by_table_name,
    mock_database_central_config,
):
    mock_log_auth_token.return_value = True
    mock_validate_headers.return_value = True
    mock_get_module_id.return_value = "4"
    mock_get_module_data_by_table_name.return_value = {
        "data": pandas.DataFrame(columns=["station_id", "port_id", "outage_id", "outage_duration"]),
        "is_truncated": False,
    }
    mock_feature_toggle_set.return_value = {Feature.DATABASE_CENTRAL_CONFIG}
    response = api_get_module_data({"headers": {"upload_id": "123", "download": "false"}}, None)
    assert response.get("statusCode") == 200
    assert mock_database_central_config().module_grid_display_headers.called
    assert mock_database_central_config().module_field_display_names.called
    assert mock_aurora.get_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetModuleData.index.DatabaseCentralConfig")
@patch("APIGetModuleData.index.get_module_data_by_table_name")
@patch("APIGetModuleData.index.get_module_id")
@patch("APIGetModuleData.index.validate_headers")
@patch("APIGetModuleData.index.aurora")
@patch.object(LogEvent, "is_auth_token_valid")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_config_ft_false(
    mock_feature_toggle_set,
    mock_log_auth_token,
    mock_aurora,
    mock_validate_headers,
    mock_get_module_id,
    mock_get_module_data_by_table_name,
    mock_database_central_config,
):
    mock_log_auth_token.return_value = True
    mock_validate_headers.return_value = True
    mock_get_module_id.return_value = "4"
    mock_get_module_data_by_table_name.return_value = {
        "data": pandas.DataFrame(columns=["station_id", "port_id", "outage_id", "outage_duration"]),
        "is_truncated": False,
    }
    mock_feature_toggle_set.return_value = frozenset()
    response = api_get_module_data({"headers": {"upload_id": "123", "download": "false"}}, None)
    assert response.get("statusCode") == 200
    assert not mock_database_central_config().module_grid_display_headers.called
    assert not mock_database_central_config().module_field_display_names.called
    assert mock_aurora.get_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetModuleData.index.get_dataframe")
@patch("APIGetModuleData.index.get_module_id")
@patch("APIGetModuleData.index.validate_headers")
@patch("APIGetModuleData.index.aurora")
@patch.object(LogEvent, "is_auth_token_valid")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_valid_config_ft_true_and_bizmagic(
    mock_feature_toggle_set,
    mock_log_auth_token,
    mock_aurora,
    mock_validate_headers,
    mock_get_module_id,
    mock_get_dataframe,
):
    mock_log_auth_token.return_value = True
    mock_validate_headers.return_value = True
    mock_get_module_id.return_value = "4"

    raw = [
        ["APIM4", 354321, "2023-07-03T12:51:48Z", None, 1, None, None, None],
        ["APIM5", 354321, "2023-07-03T12:51:48Z", 123248.92, 0, None, None, None],
        ["APIM9", 354321, "2023-07-03T12:51:48Z", None, 1, None, None, None],
    ]
    df = pandas.DataFrame(
        raw,
        columns=[
            "station_id_upload",
            "port_id",
            "outage_id",
            "outage_duration",
            "user_reports_no_data",
            "excluded_outage",
            "excluded_outage_reason",
            "excluded_outage_notes",
        ],
    )

    mock_get_dataframe.return_value = df
    mock_feature_toggle_set.return_value = {
        Feature.DATABASE_CENTRAL_CONFIG,
        Feature.ASYNC_BIZ_MAGIC_MODULE_4,
    }
    response = api_get_module_data({"headers": {"upload_id": "123", "download": "false"}}, None)
    print(response)
    assert response.get("statusCode") == 200
    assert "user_reports_no_data" in mock_get_dataframe.call_args_list[0][1]["headers"]


def test_headers_for_bizmagic_m5_true():
    response = get_right_headers("5", "maintenance_cost_total", {Feature.ASYNC_BIZ_MAGIC_MODULE_5})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "project_id",
        "maintenance_report_start",
        "maintenance_report_end",
        "caas",
        "maintenance_cost_federal",
        "maintenance_notes",
        "user_reports_no_data",
    ]
    assert response == expected


def test_headers_for_bizmagic_m5_false():
    response = get_right_headers("5", "maintenance_cost_total", {})
    expected = [
        "station_id_upload",
        "network_provider_upload",
        "project_id",
        "maintenance_report_start",
        "maintenance_report_end",
        "caas",
        "maintenance_cost_federal",
        "maintenance_notes",
    ]
    assert response == expected
