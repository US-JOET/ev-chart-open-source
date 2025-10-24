from datetime import datetime, timedelta
from dateutil import tz
import pandas
from numpy import nan as NaN
from feature_toggle.feature_enums import Feature


def allow_null_charging_sessions(feature_toggle_set, df):
    transform_df = df.copy()
    
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