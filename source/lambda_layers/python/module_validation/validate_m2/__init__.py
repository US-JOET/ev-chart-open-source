"""
Row-level validation checks for Module 2 uploads performed during AsyncBizMagic.
Module-specific business logic is applied and verified
"""
import pandas

from database_central_config import DatabaseCentralConfig
from feature_toggle.feature_enums import Feature
from error_report_messages_enum import ErrorReportMessages


def validate_empty_session(validation_options):
    """
    Convenience function that verifies all non-empty rows within csv contain the required fields.
    Valid empty rows are verified in the unique constraint check by ensuring that unique rows
    exist for those with the session_id field left blank. If invalid data is present, the details
    regarding the name and location of the invalid data, are stored in a list of dicts and is
    returned as a whole conditions object.
    """
    feature_toggle_set = validation_options.get('feature_toggle_set')
    df = validation_options.get('df')

    if Feature.BIZ_MAGIC not in feature_toggle_set:
        return {'conditions': []}

    if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        config = DatabaseCentralConfig()
        required_fields = config.required_empty_allowed_fields(2)
    else:
        required_fields = [
            "session_id",
            "session_start",
            "session_end",
            "session_error",
            "energy_kwh",
            "power_kw",
            "payment_method"
        ]

    validated_df = df.copy()
    validated_df = validated_df.drop(columns=["station_id", "port_id", "network_provider", "station_uuid", "upload_id"], axis=1, errors='ignore')
    valid_empty_rows = []

    # adding a new column to hold boolean values to denote whether each row is a valid empty row
    # or if the row is a valid non-empty row where all requried fields are filled out
    for index, row in validated_df.iterrows():
        if is_valid_empty_row(row):
            valid_empty_rows.append(True)
        else:
            valid_empty_rows.append(False)
    validated_df['valid_empty_row'] = valid_empty_rows

    # checks for valid non-empty rows
    validated_df['valid_all_required'] = validated_df.apply(
        lambda x: all(x[rf] for rf in required_fields),
        axis=1
    )

    # constructs conditions object based on rows with missing required fields
    return {'conditions': [
        {
            'error_row': row,
            'error_description':(
                ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name= column)
            ),
            'header_name': column
        }
        # evaluates rows that have partially filled out requried fields ie:entire row is not empty or completely filled out
        for row in validated_df[
            ~validated_df[['valid_empty_row', 'valid_all_required']]
            .any(axis=1)
        ].index
        # evaluates the row and creates a list of col that have empty values and is in required_fields list
        for column in validated_df.loc[[row], (validated_df.loc[[row]] == "").any()].columns.tolist() if column in required_fields
    ]}


def is_valid_empty_row(row):
    """
    A valid empty row of data must have an empty session_id and must be a unique row. This is
    because session_id is part of the unique constraints for module 2, so this check is to verify
    there are no duplicate null data present within the csv
    """
    return len(pandas.unique(row)) == 1 and row["session_id"] == ''