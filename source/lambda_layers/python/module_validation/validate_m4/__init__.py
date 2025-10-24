"""
Row-level validation checks for Module 4 uploads performed during AsyncBizMagic.
Module-specific business logic is applied and verified

This file verifies
that for non-empty rows of data, both the outage_id and outage_duration fields must be left
blank in order for the data to be considered valid.
"""

from feature_toggle.feature_enums import Feature
from error_report_messages_enum import ErrorReportMessages


def validate_empty_outage(validation_options):
    """
    Convenience function that verifies that for non-empty rows of data, both the outage_id
    and outage_duration fields must be left blank in order for the data to be considered valid.
    If these fields are both not empty, this is flagged as an error. For each row of invalid
    data present within the csv, its details regarding the name and location of the invalid
    data, are stored in a list of dicts and is returned as a whole conditions object.
    """
    feature_toggle_set = validation_options.get('feature_toggle_set')
    df = validation_options.get('df')

    if Feature.BIZ_MAGIC not in feature_toggle_set:
        return {'conditions': []}

    # adding a new boolean column that is set to true if the outage_id field is empty but the outage_duration is not
    validated_df = df.copy()
    validated_df['duration_empty__id_not'] = (
        (validated_df['outage_duration'] == '') &
        (validated_df['outage_id'] != '')
    )

    # adding a new boolean column that is set to true if the outage_duration field is empty but the outage_id is not
    validated_df['id_empty__duration_not'] = (
        (validated_df['outage_id'] == '') &
        (validated_df['outage_duration'] != '')
    )

    # constructs conditions object based on validated dataframe
    return {'conditions': [
        {
            'error_row': row,
            'error_description': (
                ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(column_name= column)
            ),
            'header_name': column
        }
        for row in validated_df[
            validated_df[['id_empty__duration_not', 'duration_empty__id_not']]
            .any(axis=1)
        ].index
        for column in validated_df.loc[[row], (validated_df.loc[[row]] == "").any()].columns.tolist()
    ]}
