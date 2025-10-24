"""
Row-level transformation for Module 4 uploads performed during AsyncBizMagic.
Transforming the dataframe to acceptable datatypes to prepare for database insertion
"""

from datetime import datetime, timedelta
from dateutil import tz

import pandas
from feature_toggle.feature_enums import Feature


def allow_null_outages(feature_toggle_set, df):
    """
    Convenience function that converts empty outage_id and outage_duration values
    to None and sets the user_reports_no_data field using a binary boolean value.
    """
    transform_df = df.copy()
    if Feature.ASYNC_BIZ_MAGIC_MODULE_4 in feature_toggle_set:
        start_time = datetime.now(tz.gettz("UTC"))
        correct_nulls = (
            (transform_df['outage_id'] == "") &
            (transform_df['outage_duration'] == "")
        )
        transform_df.loc[transform_df["station_id"] != "", ['user_reports_no_data']] = 0
        transform_df.loc[correct_nulls, ['user_reports_no_data']] = 1
        transform_df.loc[correct_nulls, ['outage_duration']] = None
        # creating system generated outage_id for null
        transform_df.loc[correct_nulls, 'outage_id'] = (
            transform_df.groupby('outage_id')
            .cumcount()
            .apply(lambda x: (start_time + timedelta(milliseconds=x)).strftime("%Y-%m-%d %H:%M:%S"))
        )

    transform_df['outage_id'] = pandas.to_datetime(
        transform_df['outage_id'],
        format='ISO8601',
        errors='coerce'
    ).convert_dtypes()

    transform_df['outage_duration'] = \
        pandas.to_numeric(transform_df['outage_duration']).convert_dtypes()

    return transform_df
