import pandas
import pytest

# module paths are set in conftest.py
from module_validation import (
    validated_field
)

from error_report_messages_enum import ErrorReportMessages

required_fields = [
    {
        "field_name": "required_string",
        "required": True,
        "datatype": "string",
        "max_length": 255
    },
    {
        "field_name": "required_decimal",
        "required": True,
        "datatype": "decimal",
        "max_precision": 7,
        "max_scale": 2
    },
    {
        "field_name": "required_datetime",
        "required": True,
        "datatype": "datetime"
    }
]


# JE-2854 All required field values are non-null:
#    Each cell of a required field is NonNull. If condition not met,
#    'error_description' value is found in ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN
@pytest.mark.parametrize("required_field", required_fields)
def test_required_not_null(required_field):
    null_series = pandas.Series([""])

    response = validated_field(required_field, null_series, 2)
    assert response.get('conditions') == [{
        'error_description': ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name=required_field['field_name']),
        'header_name': required_field['field_name'],
        'error_row': 0
    }]


# JE-2854 All provided values are in the correct data type:
#   Each cell (of both required and recommended fields) are in the correct
#   data type. If condition not met,  'error_description' value is:
#     ErrorReportMessages.INVALID_DECIMAL_INPUT
def test_decimal_incorrect_data_type():
    definition = {
        "field_name": "required_decimal",
        "required": True,
        "datatype": "decimal",
        "max_precision": 7,
        "max_scale": 2
    }
    data = pandas.Series(["abc", "123.45"])
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {0} == error_row_set
    assert 1 not in error_row_set

    assert response.get('conditions') == [{
        'error_description':
            ErrorReportMessages.INVALID_DECIMAL_INPUT.format(),
        'header_name': definition['field_name'],
        'error_row': 0
    }]

    definition['required'] = False
    response = validated_field(definition, data, 2)
    assert response.get('conditions') == [{
        'error_description':
            ErrorReportMessages.INVALID_DECIMAL_INPUT.format(),
        'header_name': definition['field_name'],
        'error_row': 0
    }]


# JE-2854 All provided values meet UTC format requirement (if applicable):
#   Each cell in the data import meets its UTC format requirement if specified
#   This holds true for both required and recommended fields.
#   If condition not met, 'error_description' value is:
#     ErrorReportMessages.INVALID_TIMESTAMP_FORMAT
def test_timestamp_incorrect_data_type():
    definition = {
        "field_name": "required_timestamp",
        "required": True,
        "datatype": "datetime"
    }
    data = pandas.Series([
        "abc123",
        "09/32/24",
        "TRUE",
        # below values come directly from OCPI 2.2.1 as valid
        "2015-06-29T20:39:09Z",
        "2015-06-29T20:39:09",
        "2016-12-29T17:45:09.2Z",
        "2016-12-29T17:45:09.2",
        "2018-01-01T01:08:01.123Z",
        "2018-01-01T01:08:01.123",
        # match OCPI format but invalid data
        "2018-13-01T01:08:01.123Z",
        "2018-01-32T01:08:01.123Z",
        "2018-01-01T25:08:01.123Z",
        "2018-01-01T01:98:01.123Z",
        "2018-01-01T01:08:67.123Z",
        # ISO 8601 compliant but not OCPI compliant
        "2011-W01-2T00:05:23.283",
        "2011-11-04 00:05:23.283",
        "2011-11-04 00:05:23.283+00:00",
        "2011-11-04T00:05:23+04:00"
    ])
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {0, 1, 2, 9, 10, 11, 12, 13, 14, 15, 16, 17} == error_row_set
    assert 3 not in error_row_set
    assert 4 not in error_row_set
    assert 5 not in error_row_set
    assert 6 not in error_row_set
    assert 7 not in error_row_set
    assert 8 not in error_row_set

    assert len(response.get('conditions', [])) == 12
    assert all(
        r['error_description'] == ErrorReportMessages.INVALID_TIMESTAMP_FORMAT.format()
        for r in response.get('conditions', [])
    )

    definition['required'] = False
    response = validated_field(definition, data, 2)
    assert len(response.get('conditions', [])) == 12
    assert all(
        r['error_description'] == ErrorReportMessages.INVALID_TIMESTAMP_FORMAT.format()
        for r in response.get('conditions', [])
    )


# JE-2854 All provided values meet MaxLength requirement (if applicable):
#   Each cell in the data import meets its MaxLength requirement if specified.
#   This holds true for both required and recommended fields.
#   If condition not met, 'error_description' value is:
#     ErrorReportMessages.MAX_STRING_LENGTH_EXCEEDED
def test_string_maxlength():
    definition = {
        "field_name": "required_string",
        "required": True,
        "datatype": "string",
        "max_length": 4
    }
    data = pandas.Series(["abc123", "defg"])
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {0} == error_row_set
    assert 1 not in error_row_set

    assert response.get('conditions') == [{
        'error_description': ErrorReportMessages.MAX_STRING_LENGTH_EXCEEDED.format(),
        'header_name': definition['field_name'],
        'error_row': 0
    }]

    definition['required'] = False
    response = validated_field(definition, data, 2)
    assert response.get('conditions') == [{
        'error_description': ErrorReportMessages.MAX_STRING_LENGTH_EXCEEDED.format(),
        'header_name': definition['field_name'],
        'error_row': 0
    }]


# JE-3667 As a user, I want the system to assume that when I submit values
# that are of type decimal, and don't provide any decimals, the digits to the
# right of the decimal place are zero. This will streamline the data
# submission process so I don't receive an error
def test_decimal_max_precision():
    definition = {
        "field_name": "required_decimal",
        "required": True,
        "datatype": "decimal",
        "max_precision": 7,
        "max_scale": 2
    }
    valid_data = \
        ["12345.67", "123.45", "12345", "-12345", "12345.6", "-12345.6"]
    invalid_data = ["123456.78", "123456", "-123456", "123456.7"]
    data = pandas.Series(valid_data + invalid_data)
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert error_row_set.intersection({0, 1, 2, 3, 4, 5}) == set()
    assert {6, 7, 8, 9} == error_row_set
    assert error_row_set.intersection({0, 1, 2, 3, 4, 5}) == set()
    assert {6, 7, 8, 9} == error_row_set

    assert all(
        r['error_description'] ==
        ErrorReportMessages.MAX_DECIMAL_LENGTH_EXCEEDED.format()
        for r in response.get('conditions', [])
    )
    assert all(
        r['error_description'] ==
        ErrorReportMessages.MAX_DECIMAL_LENGTH_EXCEEDED.format()
        for r in response.get('conditions', [])
    )

    definition['required'] = False
    response = validated_field(definition, data, 2)
    assert all(
        r['error_description'] ==
        ErrorReportMessages.MAX_DECIMAL_LENGTH_EXCEEDED.format()
        for r in response.get('conditions', [])
    )


# JE-2854 (paraphrased): All provided values meet exact decimal scale
# requirement (if applicable): Each cell in the data import meets its
# scale (Decimal) requirement if specified. This holds true for both required
# and recommended fields. If condition not met, 'error_description' value is:
#   ErrorReportMessages.MAX_DECIMAL_PLACES_EXCEEDED
#
# JE-3667 As a user, I want the system to assume that when I submit values
# that are of type decimal, and don't provide any decimals, the digits to the
# right of the decimal place are zero. This will streamline the data
# submission process so I don't receive an error
def test_decimal_scale():
    definition = {
        "field_name": "required_decimal",
        "required": True,
        "datatype": "decimal",
        "max_precision": 7,
        "max_scale": 2
    }
    data = pandas.Series(["1", "2.3", "4.56", "7.809"])
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {3} == error_row_set
    assert 0 not in error_row_set
    assert 1 not in error_row_set
    assert 2 not in error_row_set

    assert len(response.get('conditions', [])) == 1
    assert all(
        r['error_description'] ==
        ErrorReportMessages.MAX_DECIMAL_PLACES_EXCEEDED.format()
        for r in response.get('conditions', [])
    )

    definition['required'] = False
    response = validated_field(definition, data, 2)
    assert len(response.get('conditions', [])) == 1
    assert all(
        r['error_description'] ==
        ErrorReportMessages.MAX_DECIMAL_PLACES_EXCEEDED.format()
        for r in response.get('conditions', [])
    )


# JE-2854 All provided values meet MinValue requirement (if applicable):
#   Each cell in the data import meets its MinValue requirement if specified.
#   This holds true for both required and recommended fields.
#   If condition not met, 'error_description' value is:
#     ErrorReportMessages.MIN_DECIMAL_LENGTH_NOT_MET
def test_decimal_min_value():
    definition = {
        "field_name": "required_decimal",
        "required": True,
        "datatype": "decimal",
        "max_precision": 7,
        "max_scale": 2,
        "min_value": 0
    }
    data = pandas.Series(["-1.01", "0.00", "2.03"])
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {0} == error_row_set
    assert 1 not in error_row_set
    assert 2 not in error_row_set

    assert len(response.get('conditions', [])) == 1
    assert {
        'error_description': ErrorReportMessages.MIN_DECIMAL_LENGTH_NOT_MET.format(),
        'header_name': definition['field_name'],
        'error_row': 0
    } in response.get('conditions')

    definition['required'] = False
    response = validated_field(definition, data, 2)
    assert len(response.get('conditions', [])) == 1
    assert {
        'error_description': ErrorReportMessages.MIN_DECIMAL_LENGTH_NOT_MET.format(),
        'header_name': definition['field_name'],
        'error_row': 0
    } in response.get('conditions')


def test_datatype_boolean_valid():
    definition = {
        "field_name": "caas",
        "required": True,
        "datatype": "boolean",
    }
    data = pandas.Series(["True", "false", "TRUE", "FALSE", "", "abc123"])
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {4, 5} == error_row_set
    assert 0 not in error_row_set
    assert 1 not in error_row_set
    assert 2 not in error_row_set
    assert 3 not in error_row_set

    assert len(response.get('conditions', [])) == 2
    assert {
        'error_description':
            ErrorReportMessages.INVALID_BOOLEAN_INPUT.format(),
        'header_name': definition['field_name'],
        'error_row': 5
    } in response.get('conditions')

    assert {
        'error_description': ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name=definition['field_name']),
        'header_name': definition['field_name'],
        'error_row': 4
    } in response.get('conditions')

    definition['required'] = False
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {5} == error_row_set
    assert 0 not in error_row_set
    assert 1 not in error_row_set
    assert 2 not in error_row_set
    assert 3 not in error_row_set
    assert 4 not in error_row_set

    assert len(response.get('conditions', [])) == 1
    assert {
        'error_description':
            ErrorReportMessages.INVALID_BOOLEAN_INPUT.format(),
        'header_name': definition['field_name'],
        'error_row': 5
    } in response.get('conditions')

    assert {
        'error_description': ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name=definition['field_name']),
        'header_name': definition['field_name'],
        'error_row': 4
    } not in response.get('conditions')


def test_datatype_integer_valid():
    definition = {
        "field_name": "required_integer",
        "required": True,
        "datatype": "integer",
        "min_value": 0
    }
    data = pandas.Series(["1234", "18.1", "abc", "", "-1"])
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {1, 2, 3, 4} == error_row_set
    assert 0 not in error_row_set

    assert len(response.get('conditions', [])) == 4
    assert {
        'error_description':
            ErrorReportMessages.INVALID_INTEGER_INPUT.format(),
        'header_name': definition['field_name'],
        'error_row': 1
    } in response.get('conditions')

    assert {
        'error_description': ErrorReportMessages.MIN_INTEGER_LENGTH_NOT_MET.format(),
        'header_name': definition['field_name'],
        'error_row': 4
    } in response.get('conditions')

    definition['required'] = False
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {1, 2, 4} == error_row_set
    assert 0 not in error_row_set
    assert 3 not in error_row_set

    assert len(response.get('conditions', [])) == 3


def test_datatype_integer_length():
    definition = {
        "field_name": "required_integer",
        "required": True,
        "datatype": "integer",
        "length": 4
    }
    data = pandas.Series(["1234", "-5678", "+9876", "-101", "333", "90210"])
    response = validated_field(definition, data, 2)
    error_row_set = {r['error_row'] for r in response.get('conditions', [])}
    assert {3, 4, 5} == error_row_set
    assert 0 not in error_row_set
    assert 1 not in error_row_set
    assert 2 not in error_row_set

    assert len(response.get('conditions', [])) == 3
    assert all(
        r['error_description'] ==
        ErrorReportMessages.EXACT_INTEGER_LENGTH_NOT_MATCHED.format()
        for r in response.get('conditions', [])
    )
