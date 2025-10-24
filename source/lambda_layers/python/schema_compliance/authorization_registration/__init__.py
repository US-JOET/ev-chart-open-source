"""
schema_compliance.authorization_registration

A list of helper functions to verify schema compliance.
"""

from evchart_helper.api_helper import execute_query_fetchone, execute_query_df
from evchart_helper.database_tables import ModuleDataTables
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature
from error_report_messages_enum import ErrorReportMessages


def stations_not_registered(df):
    """
    Returns a list of condition objects where
    each object catches: missing station_uuid column, missing
    station_uuid cells, and unregistered stations.
    """
    conditions = []
    for index, data in df[df["station_uuid"].isna()].iterrows():
        if df["network_provider"][index] == "":
            conditions.append(
                {
                    "error_row": index,
                    "header_name": "network_provider",
                    "error_description": (
                        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                            column_name="network_provider"
                        )
                    ),
                }
            )
        elif df["station_id"][index] == "":
            conditions.append(
                {
                    "error_row": index,
                    "header_name": "station_id",
                    "error_description": (
                        ErrorReportMessages.MISSING_VALUE_FOR_REQUIRED_COLUMN.format(
                            column_name="station_id"
                        )
                    ),
                }
            )
        else:
            conditions.append(
                {
                    "error_row": index,
                    "header_name": "station_id",
                    "error_description": ErrorReportMessages.STATION_NOT_REGISTERED.format(
                        station_id=data["station_id"], network_provider=data["network_provider"]
                    ),
                }
            )
    return conditions


def unauthorized_stations_for_dr(cursor, dr_id, df):
    conditions = []
    in_clause = ", ".join(["%s"] * len(df))
    if not df.empty:
        query = f"""
            SELECT station_uuid
            FROM {ModuleDataTables["RegisteredStations"].value}
            WHERE station_uuid in ({in_clause})
            AND dr_id != %s"""

        # The trailing comma is important.  this is a 1 element tuple
        query_data = tuple(df["station_uuid"]) + (dr_id,)

        result = execute_query_df(cursor=cursor, query=query, data=query_data)

        if not result.empty:
            for _, row in result.iterrows():
                station_uuid = row["station_uuid"]
                index = df.index[df["station_uuid"] == station_uuid].item()
                data = df.loc[index]
                conditions.append(
                    {
                        "error_row": index,
                        "header_name": "station_id",
                        "error_description": ErrorReportMessages.DR_NOT_AUTHORIZED_TO_SUBMIT.format(
                            station_id=data["station_id"], network_provider=data["network_provider"]
                        ),
                    }
                )
    return conditions


def stations_not_authorized(
    cursor,
    dr_id,
    sr_id,
    df,
):
    """
    Returns a list of conditions if s station is
    not authorized to the given direct or sub-recipient
    in station_authorizations table.
    """
    conditions = []

    df_copy = df.copy()
    df_copy["authorization_uuid"] = get_auth_and_unauth_stations(cursor, dr_id, sr_id, df)

    # go through list and add conditions to where stations are not auth
    # (in the list as None)
    for index, data in df_copy[df_copy["authorization_uuid"].isna()].iterrows():
        if data.get("station_uuid"):
            conditions.append(
                {
                    "error_row": index,
                    "header_name": "station_id",
                    "error_description": ErrorReportMessages.SR_NOT_AUTHORIZED_TO_SUBMIT.format(
                        station_id=data["station_id"], network_provider=data["network_provider"]
                    ),
                }
            )

    return conditions


def stations_not_active(cursor, dr_id, df, feature_toggle_set=frozenset()):
    """
    Returns a list of condition objects, each of which is a
    station with status of 'Pending Approval'
    """
    conditions = []
    if Feature.SR_ADDS_STATION in feature_toggle_set:
        station_registrations_table = ModuleDataTables["RegisteredStations"].value
        pending_stations_query = f"""
            SELECT station_uuid from {station_registrations_table}
            WHERE status='Pending Approval'
            AND dr_id=%s
        """

        # get list of pending stations
        pending_stations_df = execute_query_df(
            query=pending_stations_query, data=(dr_id,), cursor=cursor
        )
        pending_stations_set = set(pending_stations_df["station_uuid"])

        # if station found in list of pending stations, then create and add a new error
        for index, data in df.iterrows():
            if data["station_uuid"] in pending_stations_set:
                conditions.append(
                    {
                        "error_row": index,
                        "header_name": "station_id",
                        "error_description": (
                            ErrorReportMessages.INVALID_STATION_STATUS_PENDING_APPROVAL.format()
                        ),
                    }
                )

    return conditions


def _get_station_auth_uuid(lookup_table, cursor, dr_id, sr_id, station_uuid, network_provider=None):
    # Quick lookup table implementation to reduce repeated unnecessary DB calls.
    key_tuple = (dr_id, sr_id, station_uuid)
    if key_tuple not in lookup_table:
        print(f"lookup miss for {key_tuple}; hitting db")
        lookup_table[key_tuple] = get_station_auth_uuid(
            cursor, dr_id, sr_id, station_uuid, network_provider
        )

    return lookup_table[key_tuple]


def get_auth_and_unauth_stations(
    cursor,
    dr_id,
    sr_id,
    df,
):
    """
    List builder function that parses through a dataframe
    and returns a list of authorization_uuid's or None
    """
    lookup_table = {}
    return [
        _get_station_auth_uuid(lookup_table, cursor, dr_id, sr_id, s, np)
        for s, np in df[["station_uuid", "network_provider"]].to_records(index=False)
    ]


def query_builder_authorization_uuid(dr_id, sr_id, station_uuid):
    """
    Returns a query based on the given inputs for selecting
    authorization_uuid from station_authorization table.
    """
    station_authorizations_table = ModuleDataTables["StationAuthorizations"].value
    authorizer_column = "dr_id"
    authorizee_column = "sr_id"

    features = FeatureToggleService().get_active_feature_toggles(log_event=None)
    if Feature.N_TIER_ORGANIZATIONS in features:
        authorizer_column = "authorizer"
        authorizee_column = "authorizee"

    auth_query = (
        f"SELECT authorization_uuid FROM {station_authorizations_table} "
        f"WHERE {authorizer_column}=%s AND {authorizee_column}=%s AND station_uuid=%s"
    )
    query_data = (dr_id, sr_id, station_uuid)
    return auth_query, query_data


def get_station_auth_uuid(cursor, dr_id, sr_id, station_uuid, network_provider=None):
    """
    Lookup function that returns authorization_uuid if a sub-recipient
    is authorized to submit for that station that direct recipient. Otherwise,
    returns None.
    """
    auth_query, query_data = query_builder_authorization_uuid(dr_id, sr_id, station_uuid)

    result_arr = execute_query_fetchone(
        query=auth_query,
        data=query_data,
        cursor=cursor,
        message=(
            "Error thrown in authroization_registration helper file: " "get_station_auth_uuid()"
        ),
    )

    if result_arr is None or len(result_arr) == 0:
        return None
    return result_arr[0]


def get_station_registration_uuid(cursor, org_id, station_id):
    """
    Returns station_uuid if a station exists in station_registrations
    for the given station_id, otherwise returns None.
    """
    registration_query = f"""
        SELECT station_uuid FROM {ModuleDataTables["RegisteredStations"].value}
        WHERE org_id=%s AND station_id=%s
    """
    result_arr = execute_query_fetchone(
        query=registration_query,
        data=(org_id, station_id),
        cursor=cursor,
        message="Error thrown in authorization_registration helper file: is_station_registered()",
    )

    # returns station_uuid or None if not found in station_registrations table
    if result_arr is None or len(result_arr) == 0:
        return None
    return result_arr[0]
