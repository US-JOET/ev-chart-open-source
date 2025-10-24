"""
Row-level transformation for Module 6 uploads performed during AsyncBizMagic.
Transforming the dataframe to acceptable datatypes to prepare for database insertion
"""

from database_central_config import DatabaseCentralConfig
from feature_toggle.feature_enums import Feature
from numpy import nan as NaN
import pandas


def allow_null_capital_install_costs(feature_toggle_set, df):
    """
    Convenience function that converts all module 9 decimal fields
    to None or decimals and sets the user_reports_no_data field using
    a binary boolean value. Also sets the der_acq_owned field to a
    boolean binary value
    """
    transform_df = df.copy()
    if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
        config = DatabaseCentralConfig()
        bizmagic_decimal_fields = config.required_empty_allowed_fields(9).union(config.recommended_fields(9))
        bizmagic_decimal_fields.remove("der_acq_owned")
    else:
        bizmagic_decimal_fields = [
            "real_property_cost_total",
            "equipment_cost_total",
            "equipment_install_cost_total",
            "equipment_install_cost_elec",
            "equipment_install_cost_const",
            "equipment_install_cost_labor",
            "equipment_install_cost_other",
            "der_cost_total",
            "der_install_cost_total",
            "dist_sys_cost_total",
            "service_cost_total",
        ]

    # sets the recommended fields that were not included in the original upload to None
    for field in bizmagic_decimal_fields:
        if field not in transform_df:
            transform_df[field] = None

    if Feature.ASYNC_BIZ_MAGIC_MODULE_9 in feature_toggle_set:
        correct_nulls = (transform_df[list(bizmagic_decimal_fields)] == "").all(axis=1)
        for bizmagic_decimal in bizmagic_decimal_fields:
            transform_df.loc[correct_nulls, [bizmagic_decimal]] = None
        transform_df.loc[~correct_nulls, ['user_reports_no_data']] = 0
        transform_df.loc[correct_nulls, ['user_reports_no_data']] = 1
        transform_df['user_reports_no_data'] = \
            pandas.to_numeric(transform_df['user_reports_no_data']).convert_dtypes()

    # converts non-empty decimal fields to decimals
    for bizmagic_decimal in bizmagic_decimal_fields:
        if bizmagic_decimal in transform_df:
            transform_df[bizmagic_decimal] = pandas.to_numeric(
                transform_df[bizmagic_decimal]
            ).convert_dtypes()

    # converts der_acq_owned field to a boolean binary value
    if "der_acq_owned" in transform_df:
        transform_df["der_acq_owned"] = (
            transform_df["der_acq_owned"]
            .str.upper()
            .map({"TRUE": 1, "FALSE": 0})
            .convert_dtypes()
        )
    return transform_df
