"""
evchart_helper.user_helper

A set of helper functions for managing user data.
"""
from evchart_helper.api_helper import execute_query, get_org_info_dynamo
from evchart_helper.database_tables import ModuleDataTables


def get_authorized_drs(org_id, cursor, n_tier_enabled=False):
    """
        Return a list of authorizers for a particular organization ID.
    """
    table = ModuleDataTables.StationAuthorizations.value
    authorizer_column = "dr_id"
    authorizee_column = "sr_id"

    if n_tier_enabled:
        authorizer_column = "authorizer"
        authorizee_column = "authorizee"

    query = f"SELECT {authorizer_column} FROM {table} WHERE {authorizee_column} = %s" # nosec - no SQL injection possible
    output = execute_query(
        query=query,
        data=(org_id,),
        cursor=cursor,
        message=f"Error retrieving authorized DRs for Org {org_id}",
    )

    dr_id_list = [dr[authorizer_column] for dr in output]
    return {dr_id: get_org_info_dynamo(dr_id).get("name") for dr_id in dr_id_list}
