"""
Row-level transformation for Module 5 uploads performed during AsyncBizMagic.
Transforming the dataframe to acceptable datatypes to prepare for database insertion
"""

from feature_toggle.feature_enums import Feature
import pandas


def allow_null_federal_maintenance(feature_toggle_set, df):
    """
    Convenience function that converts empty maintenance_cost_total value
    to None and sets the user_reports_no_data field using a binary boolean value.
    """
    transform_df = df.copy()
    if Feature.ASYNC_BIZ_MAGIC_MODULE_5 in feature_toggle_set:
        correct_nulls = (
            transform_df['maintenance_cost_total']
            .astype(str)
            .str.lower()
        ) == ""
        transform_df.loc[correct_nulls, ['maintenance_cost_total']] = None
        transform_df.loc[~correct_nulls, ['user_reports_no_data']] = 0
        transform_df.loc[correct_nulls, ['user_reports_no_data']] = 1
        transform_df['user_reports_no_data'] = (
        pandas.to_numeric(transform_df['user_reports_no_data'])
        .convert_dtypes()
    )
    elif Feature.MODULE_5_NULLS in feature_toggle_set:
        correct_nulls = (
            transform_df['maintenance_cost_total']
            .astype(str)
            .str.lower()
        ) == "null"
        transform_df.loc[correct_nulls, ['maintenance_cost_total']] = None

    transform_df['maintenance_cost_total'] = (
        pandas.to_numeric(transform_df['maintenance_cost_total'])
        .convert_dtypes()
    )
    return transform_df
