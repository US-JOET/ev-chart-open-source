"""
Row-level transformation for Module 2 uploads performed during AsyncBizMagic.
Transforming the dataframe to acceptable datatypes to prepare for database insertion
"""

from datetime import datetime, timedelta
from dateutil import tz

import pandas
from numpy import nan as NaN
from feature_toggle.feature_enums import Feature


def allow_null_charging_sessions(feature_toggle_set, df):
    """
    For rows that have session_id as empty, this function will auto-generate a
    session_id since this field cannot be a null in the databse. The
    user_reports_no_data field is then updated with a binary boolean value and
    datetime and decimal fields are also converted to their data types.
    """
    transform_df = df.copy()
    if Feature.ASYNC_BIZ_MAGIC_MODULE_2 in feature_toggle_set:
        start_time = datetime.now(tz.gettz("UTC"))
        no_session = (
            transform_df['session_id'].astype(str) == ""
        )

        transform_df.loc[no_session, 'session_id'] = (
            transform_df
            .groupby('session_id')
            .cumcount()
            .apply(lambda x: start_time + timedelta(milliseconds=x))
        )
        transform_df['session_id'] = \
            transform_df['session_id'].astype("string")
        transform_df.loc[no_session, 'session_id'] = \
            transform_df['session_id'].apply(lambda x: 'NoSession' + x)
        transform_df.loc[~no_session, ['user_reports_no_data']] = 0
        transform_df.loc[no_session, ['user_reports_no_data']] = 1


        transform_df.replace('', None, regex=True, inplace=True)
        transform_df.replace({NaN: None}, inplace=True)
    
    for bizmagic_datetime in ['session_start', 'session_end']:
        transform_df[bizmagic_datetime] = pandas.to_datetime(
            transform_df[bizmagic_datetime],
            format='ISO8601',
            errors='coerce'
        ).convert_dtypes()

    for bizmagic_decimal in ['energy_kwh', 'power_kw']:
        transform_df[bizmagic_decimal] = \
            pandas.to_numeric(transform_df[bizmagic_decimal]).convert_dtypes()

    return transform_df
