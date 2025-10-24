import pandas

# module paths are set in conftest.py
from module_validation import (
    drop_sample_rows
)


def test_sample_rows_exist():
    sample_df = pandas.DataFrame({
        "is_string": ["String(36)", "Required", "data"],
        "is_categorical_string": ["Categorical String(36)", "Required", "dta"],
        "is_datetime": ["DateTime", "Required", "this_is_a_date"],
        "is_decimal": ["Decimal(7,2)", "Required", "123.54"],
        "is_boolean": ["Boolean", "Recommended", "FALSE"],
        "is_integer": ["Integer(6)", "Required", "789"],
    })
    sample_df.index += 2
    expected_df = sample_df.copy().loc[[4]]

    pandas.testing.assert_frame_equal(drop_sample_rows(sample_df), expected_df)


def test_sample_rows_datatype_only():
    sample_df = pandas.DataFrame({
        "is_string": ["String(36)", "data"],
        "is_categorical_string": ["Categorical String(36)", "dta"],
        "is_datetime": ["DateTime", "this_is_a_date"],
        "is_decimal": ["Decimal(7,2)", "123.54"],
        "is_boolean": ["Boolean", "FALSE"],
        "is_integer": ["Integer(6)", "789"],
    })
    sample_df.index += 2
    expected_df = sample_df.copy().loc[[3]]

    pandas.testing.assert_frame_equal(drop_sample_rows(sample_df), expected_df)


def test_sample_rows_out_of_order():
    sample_df = pandas.DataFrame({
        "is_string": ["Required", "String(36)", "data"],
        "is_categorical_string": ["Required", "Categorical String(36)", "dta"],
        "is_datetime": ["Required", "DateTime", "this_is_a_date"],
        "is_decimal": ["Required", "Decimal(7,2)", "123.54"],
        "is_boolean": ["Recommended", "Boolean", "FALSE"],
        "is_integer": ["Required", "Integer(6)", "789"],
    })
    sample_df.index += 2

    pandas.testing.assert_frame_equal(drop_sample_rows(sample_df), sample_df)


def test_bugfix_je5411():
    sample_df = pandas.DataFrame({
        "station_id": {
            2: "String(36)",
            3: "Required",
            4: "0036a9f4-b67e-43da-bbb5-3f78586316bf"
        },
        "port_id": {2: "String(36)", 3: "Required", 4: "seeewaaa"},
        "network_provider": {
            2: "CategoricalString(255)", 3: "Required", 4: "shell_recharge"
        },
        "charger_id": {2: "String(36)", 3: "Recommended", 4: "test"},
        "session_id": {2: "String(36)", 3: "Required", 4: "test"},
        "connector_id": {2: "String(36)", 3: "Recommended", 4: "test"},
        "session_start": {
            2: "DateTime", 3: "Required", 4: "2024-01-01T00:00:00Z"
        },
        "session_end": {
            2: "DateTime", 3: "Required", 4: "2024-01-20T00:00:00Z"
        },
        "session_error": {2: "String(255)", 3: "Required", 4: "ERROR1"},
        "error_other": {2: "String(255)", 3: "Recommended", 4: "test"},
        "energy_kwh": {2: "Decimal(7,2)", 3: "Required", 4: "20241.01"},
        "power_kw": {2: "Decimal(7,2)", 3: "Required", 4: "20241.02"},
        "payment_method": {2: "String(255)", 3: "Required", 4: "VISA"},
        "payment_other": {2: "String(255)", 3: "Recommended", 4: "test"}
    })
    expected_df = sample_df.copy().loc[[4]]

    pandas.testing.assert_frame_equal(drop_sample_rows(sample_df), expected_df)


