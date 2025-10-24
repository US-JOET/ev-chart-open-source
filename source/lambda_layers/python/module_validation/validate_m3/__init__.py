"""
Row-level validation checks for Module 3 uploads performed during AsyncBizMagic.
Module-specific business logic is applied and verified
"""
import pandas
from dateutil.relativedelta import relativedelta

from error_report_messages_enum import ErrorReportMessages
from evchart_helper.api_helper import execute_query_fetchone
from evchart_helper.database_tables import ModuleDataTables
from feature_toggle.feature_enums import Feature

station_registrations = ModuleDataTables["RegisteredStations"].value
network_providers = ModuleDataTables["NetworkProviders"].value


def get_operational_date(cursor, station_id, network_provider, feature_toggle_set):
    """
    Convenience function that returns the operational date for a given station id and network provider
    """
    sql = (
        f"""
        SELECT operational_date from {station_registrations} sr
        INNER JOIN {network_providers} np ON sr.network_provider_uuid = np.network_provider_uuid
        WHERE sr.station_id=%s AND np.network_provider_value=%s
        """
    )
    return execute_query_fetchone(
        query=sql, data=(station_id, network_provider), cursor=cursor
    )[0]


def validate_operational_one_year(validation_options):
    """
    If a station has been operational for more than 1 year, all rows for that station cannot have
    a null or missing value for the 'uptime' field. For each row of invalid data present within the
    csv, its details regarding the name and location of the invalid data, are stored in a list of
    dicts and is returned as a whole conditions object.
    """
    feature_toggle_set = validation_options.get('feature_toggle_set')
    cursor = validation_options.get('cursor')
    df = validation_options.get('df').copy().fillna("")

    df['operational_date'] = df.apply(
        lambda x: get_operational_date(
            cursor, x['station_id'], x['network_provider'], feature_toggle_set
        ),
        axis=1
    )

    df['one_year_before_uptime_start'] = (
        pandas.to_datetime(df['uptime_reporting_start']).dt.date -
        relativedelta(years=1)
    )

    # constructs conditions object based on operational date requirements
    return {'conditions': [
        {
            'error_row': row,
            'error_description':
                ErrorReportMessages.MODULE_3_UPTIME_REQUIRED.value,
            'header_name': 'uptime'
        }
        for row in df[
            (df['uptime'] == "") &
            (df['operational_date'] < df['one_year_before_uptime_start'])
        ].index
    ]}
