"""
evchart_helper.station_helper

A set of helper functions for managing station data.
"""
import datetime
import uuid
from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from evchart_helper.api_helper import (
    execute_query,
    execute_query_fetchone,
    format_users,
    get_org_info_dynamo,
    get_org_users,
    execute_query_df,
)
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraDuplicateItemError,
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseDynamoQueryError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedBodyError,
    EvChartUnableToDeleteItemError,
    EvChartUserNotAuthorizedError,
    EvChartEmailError,
    EvChartUnknownException
)
from evchart_helper.database_tables import ModuleDataTables
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature

station_registrations = ModuleDataTables["RegisteredStations"].value
station_authorizations = ModuleDataTables["StationAuthorizations"].value
station_ports = ModuleDataTables["StationPorts"].value
network_providers = ModuleDataTables["NetworkProviders"].value



def insert_authorized_subrecipients(
    srs_added, station_uuid, updated_on, updated_by,
    dr_id, cursor, log_event=None, n_tier_enabled=False
):
    """
        Convenience function to authorize a list subrecipient for a given direct
        recipient. Each subrecipient in the list is added with the direct recipient
        into the station_authorizations table. If n_tier is enabled, additional
        columns for n_tier values are added.
    """
    n_tier_columns = ""
    n_tier_values = ""

    if n_tier_enabled:
        n_tier_columns = ", authorizer, authorizee"
        n_tier_values = ", %s, %s"

    for sr in srs_added:
        try:
            query = f"""
                INSERT INTO {station_authorizations}
                (authorization_uuid, dr_id, sr_id, station_uuid, updated_on, updated_by{n_tier_columns})
                VALUES (%s, %s, %s, %s, %s, %s{n_tier_values})
            """
            auth_uuid = str(uuid.uuid4())
            parameters = [auth_uuid, dr_id, sr, station_uuid, updated_on, updated_by]
            if n_tier_enabled:
                parameters.extend([dr_id, sr])
            cursor.execute(query, parameters)

        except Exception as e:
            raise EvChartDatabaseAuroraQueryError(
                message=f"Error thrown in add_authorized_subrecipients(). Error adding to {station_authorizations}: {e}"
            )


def get_authorized_subrecipients(station_uuid, features, cursor):
    """
        Convenience function to retrieve the authorized subrecipients for a given station_uuid
        from the station_authorizations table.
    """
    authorizee_column = "sr_id"

    if Feature.N_TIER_ORGANIZATIONS in features:
        authorizee_column = "authorizee"

    cursor.execute(
        f"SELECT DISTINCT {authorizee_column} FROM {ModuleDataTables.StationAuthorizations.value} WHERE station_uuid=%s", # nosec - no SQL injection possible
        (station_uuid,)
    )
    output = [row[0] for row in cursor.fetchall()]

    return output


@feature_enablement_check(Feature.STATION_AUTHORIZES_SR_EMAIL)
def trigger_station_authorizes_subrecipient_email(
    srs_added, station_id, station_nickname, dr_org_name
):
    """
        Convenience function to send email to every admin in a given subrecipient
        org when that org is newly authorized to a station (by a direct recipient). Can
        be used for multiple subrecipients at a time.
    """
    try:
        email_values = {}
        email_values["email_type"] = Email_Template.DR_APPROVE_SR_STATION
        email_values["station_id"] = station_id
        email_values["dr_org_name"] = dr_org_name
        if station_nickname:
            email_values["station_nickname"] = station_nickname
        else:
            email_values["station_nickname"] = ""

        for sr in srs_added:
            email_values["sr_org_name"] = get_org_info_dynamo(sr, None)["name"]
            all_org_users = get_org_users(sr, None)
            formatted_users = format_users(all_org_users)
            for user in formatted_users:
                if user.get("status") == "Active" and user.get("role") == "Administrator":
                    email_values["first_name"] = user.get("first_name")
                    email_values["email"] = user.get("email")
                    trigger_email(email_values)

    except (
        EvChartDatabaseDynamoQueryError,
        EvChartJsonOutputError,
        EvChartMissingOrMalformedBodyError,
        EvChartEmailError
    )as e:
        e.message += "Error thrown in trigger_station_authorizes_subrecipient_email()."
        raise e
    except Exception as e:
        raise EvChartUnknownException(
            message=f"Error thrown in trigger_station_authorizes_subrecipient_email(). Error formatting fields for email handler: {e}"
        )

def module_data_exists_for_port_uuid(port_uuid, cursor):
    """
        Convenience function that checks if there is any module data
        that exists (in any module table) for a given port. Returns
        True or False.
    """
    try:
        for i in range(2, 5):
            query = f"SELECT upload_id FROM evchart_data_v3.module{i}_data_v3 WHERE port_uuid=%s"
            output = execute_query(query, (port_uuid,), cursor)

            if output:
                return True
        return False
    except EvChartDatabaseAuroraQueryError as e:
        e.message += "Function called in module_data_exists_for_port_uuid()."
        raise e
    except Exception as e:
        raise EvChartUnknownException(
            message=f"Error thrown in module_data_exists_for_port_uuid(). Error querying Aurora for module data: {repr(e)}"
        )

def get_ports_from_list(port_uuid_list, cursor):

    query = f"""
        SELECT *
        FROM {station_ports}
        WHERE port_uuid IN ({", ".join(["%s"] * len(port_uuid_list))})
        """
    data = port_uuid_list

    output = execute_query_df(query=query, data=data, cursor=cursor)

    return output

def remove_station(station_uuid, cursor,  log_event=None):
    """
        Convenience function that deletes a station from station_registrations.
        Also checks station validity and any existing module data before
        deleting.
    """
    try:
        #verify station exists
        if is_valid_station(station_uuid, cursor, log_event):
            #check for uploaded data
            if module_data_exists_for_station_uuid(station_uuid, cursor) is False:
                #if no data, delete station data
                delete_station_data(station_uuid, cursor)
            else:
                raise EvChartMissingOrMalformedBodyError(
                    message=f"Module data present for station: {station_uuid}."
                )
        else:
            raise EvChartMissingOrMalformedBodyError(
                message=f"No station found for station uuid {station_uuid}."
            )
    except EvChartMissingOrMalformedBodyError as e:
        e.message += "Function called in remove_station()"
        raise e
    except EvChartDatabaseAuroraQueryError as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Error thrown in remove_station(). Error querying Aurora for module data: {repr(e)}"
        )
    except Exception as e:
        raise EvChartUnknownException(message="Error thrown in remove_station(): {e}")


def delete_station_data(station_uuid, cursor):
    """
        Convenience function to delete a station from
        station_authorizations based off a station_uuid.
    """
    try:
        tables = [station_ports, station_authorizations, station_registrations]
        for station_table in tables:
            query = f"DELETE FROM {station_table} WHERE station_uuid=%s"
            execute_query(query, (station_uuid,), cursor)
    except EvChartDatabaseAuroraQueryError as e:
        e.message += "Function called in delete_station_data()."
        raise e
    except Exception as e:
        raise EvChartUnknownException(
            message=f"Error thrown in delete_station_data(): {repr(e)}"
        )


def module_data_exists_for_station_uuid(station_uuid, cursor):
    """
        Convenience function that checks if there is any module data
        that exists (in any module table) for a given station. Returns
        True or False.
    """
    try:
        for i in range(2, 10):
            query = f"SELECT upload_id FROM evchart_data_v3.module{i}_data_v3 WHERE station_uuid=%s"
            output = execute_query(query, (station_uuid,), cursor)
            if output:
                return True
        return False
    except EvChartDatabaseAuroraQueryError as e:
        e.message += "Function called in module_data_exists_for_station_uuid()."
        raise e
    except Exception as e:
        raise EvChartUnknownException(
            message=f"Error thrown in module_data_exists_for_station_uuid(). Error querying Aurora for module data: {repr(e)}"
        )


def check_for_existing_srs(srs_added, station_uuid, dr_id, features, cursor, log_event=None):
    """
        Convenience function to check if there are any subrecipients authorized for a
        given station. If no sub-recipients exist, error is thrown.
    """
    authorizer_column = "dr_id"
    authorizee_column = "sr_id"

    if Feature.N_TIER_ORGANIZATIONS in features:
        authorizer_column = "authorizer"
        authorizee_column = "authorizee"

    for sr in srs_added:
        query = f"""
            SELECT * FROM {station_authorizations}
            WHERE {authorizee_column}=%s AND {authorizer_column}=%s AND station_uuid=%s
        """
        result_arr = execute_query_fetchone(
            query=query,
            data= (sr, dr_id, station_uuid),
            cursor=cursor,
            message=(
                "Error thrown in station_helper: check_for_existing_srs()"
            )
        )

        if result_arr or result_arr is not None:
            raise EvChartDatabaseAuroraDuplicateItemError(
                message=f"Error thrown in check_for_existing_srs(). SR {sr} already exists in Station {station_uuid}"
            )


def get_fed_funded_filter(station_registration_representations, station_port_representation):
    sr_rep = station_registration_representations
    sp_rep = station_port_representation
    is_fed_funded_filter = f"""
        AND(
            {sr_rep}.num_fed_funded_ports > 0
            OR {sp_rep}.federally_funded = 1
            OR (
                {sr_rep}.NEVI = 1
                OR {sr_rep}.CFI = 1
                OR {sr_rep}.EVC_RAA = 1
                OR {sr_rep}.CMAQ = 1
                OR {sr_rep}.CRP = 1
                OR {sr_rep}.OTHER = 1
            )
        )
    """
    return is_fed_funded_filter

def get_non_fed_funded_filter(station_registration_representations, station_port_representation):
    sr_rep = station_registration_representations
    sp_rep = station_port_representation
    non_fed_funded_filter = f"""
        AND(
            {sr_rep}.num_fed_funded_ports = 0
            OR (
                {sr_rep}.NEVI = 0
                AND {sr_rep}.CFI = 0
                AND {sr_rep}.EVC_RAA = 0
                AND {sr_rep}.CMAQ = 0
                AND {sr_rep}.CRP = 0
                AND {sr_rep}.OTHER = 0
            )
            AND {sp_rep}.federally_funded = 0
        )
    """
    return non_fed_funded_filter

def is_valid_station(station_uuid, cursor, log_event=None):
    """
        Convenience function that returns station details if a
        station exists in the table. Otherwise, an error is thrown.
        Note: must return station details because they are used in APIPatchStation.
    """
    query = f"SELECT * FROM {station_registrations} WHERE station_uuid=%s" # nosec - SQL injection not possible
    data = (station_uuid,)
    output = execute_query(query, data, cursor)
    if output:
        return output
    raise EvChartMissingOrMalformedBodyError(
        message=f"Error thrown in is_valid_station(). No station found for station uuid {station_uuid}."
    )


def is_valid_org(org_id, recipient_type, station_uuid, cursor, features, log_event=None):
    """
        Convenience function that verifies if an org is allowed to view
        a given station based on its station_uuid. Error is thrown if
        org is not allowed to view, otherwise True is returned.
    """
    authorizer_column = "dr_id"
    authorizee_column = "sr_id"

    if Feature.N_TIER_ORGANIZATIONS in features:
        authorizer_column = "authorizer"
        authorizee_column = "authorizee"

    get_org_query = (
        f"SELECT dr_id FROM {station_registrations} WHERE station_uuid=%s" # nosec - SQL injection not possible
    )
    result = execute_query_fetchone(
        get_org_query,
        (station_uuid,),
        cursor,
        message="Error thrown in is_valid_org().",
    )
    if not result or result is None:
        raise EvChartMissingOrMalformedBodyError(
            message=f"Error thrown in is_valid_org(). Station {station_uuid} does not exist"
        )
    #TODO: Need to account for multiple returns for n-tier.
    dr_station_owner = result[0]

    # checks if user is a valid DR viewing their own data
    if recipient_type == "direct-recipient":
        if dr_station_owner != org_id:
            raise EvChartUserNotAuthorizedError(
                message="Error thrown in is_valid_org(). Direct recipients can only view their own data"
            )

    # checks if the user is a valid SR that has been authorized by the station owner to view the data
    elif recipient_type == "sub-recipient":
        query = f"""SELECT * FROM {station_authorizations}
                    WHERE station_uuid =%s AND {authorizer_column}=%s AND {authorizee_column}=%s
                """
        output = execute_query(
            query,
            (
                station_uuid,
                dr_station_owner,
                org_id,
            ),
            cursor,
            message=f"Error thrown in is_valid_org(). For org_id {org_id}",
        )

        # if there are no rows returned from the database, that means the current SR is not authorized to view data
        if not output:
            raise EvChartUserNotAuthorizedError(
                message=f"Error thrown in is_valid_org(). Recipient type is not authorized to view station data: {recipient_type}"
            )

    elif recipient_type != "joet":
        raise EvChartUserNotAuthorizedError(
            message=f"Error thrown in is_valid_org(). Recipient type is not authorized to view station data: {recipient_type}"
        )
    return True


def format_operational_date(operational_date):
    """
        Convenience function that formats and returns
        operational date as database-compatible format.
    """
    try:
        if operational_date:
            operational_date = datetime.datetime.strptime(
                operational_date, "%Y-%m-%d"
            ).date()
        else:
            operational_date = None

        return operational_date
    except Exception as e:
        raise EvChartJsonOutputError(
            message=f"Error thrown in format_operational_date(). Error converting date string into date obj {e}"
        )


# PORT LEVEL HELPER METHODS
def handle_port_data(station, cursor, updated_on, updated_by):
    """
        Convenience function to either insert, update, or delete
        port data based on station['port'] input parameter. Returns
        True once successfully completed.
    """
    station_uuid = station["station_uuid"]

    if "fed_funded_ports" in station:
        for port in station["fed_funded_ports"]:
            if "port_uuid" not in port:
                insert_port_data(port, station_uuid, cursor, updated_on, updated_by, 1)
            elif "port_uuid" in port:
                update_port_data(port, cursor, updated_on, updated_by)

    if "non_fed_funded_ports" in station:
        for port in station["non_fed_funded_ports"]:
            if "port_uuid" not in port:
                insert_port_data(port, station_uuid, cursor, updated_on, updated_by, 0)
            elif "port_uuid" in port:
                update_port_data(port, cursor, updated_on, updated_by)

    # deleting ports
    if "ports_removed" in station:
        delete_port_data(station["ports_removed"], cursor)

    return True


def insert_port_data(
    # pylint: disable=too-many-arguments
    port_dict, station_uuid, cursor, updated_on, updated_by, is_fed_funded
):
    """
        Convenience function to insert port data into
        station_ports table given station_uuid.
    """
    try:
        query = (
            f"INSERT INTO {station_ports} ("
            "  station_uuid, port_uuid, port_id, port_type, federally_funded, "
            "  updated_on, updated_by"
            ") VALUES (%s, %s, %s, %s, %s, %s, %s)"
        )
        port_uuid = str(uuid.uuid4())
        cursor.execute(
            query,
            (
                station_uuid,
                port_uuid,
                port_dict.get("port_id"),
                port_dict.get("port_type"),
                is_fed_funded,
                updated_on,
                updated_by,
            ),
        )
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message=(
                "Error thrown in station_helper insert_port_data(). "
                f"Error adding to {station_ports}: {repr(e)}"
            )
        ) from e


def update_port_data(port, cursor, updated_on, updated_by):
    """
        Convenience function to update 1 row of port data in
        station_ports table.
    """

    update_row_query = f"""
        UPDATE {station_ports} SET port_id=%s, port_type=%s, updated_by=%s, updated_on=%s WHERE port_uuid=%s
    """
    query_data = (port.get("port_id"), port.get("port_type"), updated_by, updated_on, port.get("port_uuid"))
    execute_query(update_row_query, query_data, cursor=cursor, message="update_port_data()")


def delete_port_data(ports_list, cursor):
    """
        Convenience function to delete port data from
        station_ports table given port_uuid.
    """

    # SQL injection not possible
    query = f"DELETE FROM {station_ports} WHERE port_uuid=%s" # nosec
    for port_uuid in ports_list:
        try:
            cursor.execute(query, (port_uuid,))

        except Exception as e:
            raise EvChartDatabaseAuroraQueryError(
                message=(
                    "Error thrown in delete_port_data(). "
                    f"Error removing from {station_ports}: {repr(e)}"
                )
            ) from e

def module_data_exists_for_ports(ports_list, cursor):
    # check data in ports first
    ports_with_data = []
    for port_uuid in ports_list:
        if module_data_exists_for_port_uuid(port_uuid, cursor):
            ports_with_data.append(port_uuid)

    if len(ports_with_data) > 0:
        # get ports data from ports table
        ports = get_ports_from_list(ports_with_data, cursor)
        port_ids = ports["port_id"].str.cat(sep=', ')

        raise EvChartUnableToDeleteItemError(
            message=f"Module data present for ports: {port_ids}"
        )

def get_formatted_station_ports(station_uuid, cursor, fed_funded_only = True):
    """
        Convenience function to grab and return all ports from
        station_ports table and format, given a station_uuid.
    """
    cursor.execute(
        # no SQL injection possible
        f"SELECT * FROM {ModuleDataTables.StationPorts.value} "
        "WHERE station_uuid=%s", # nosec
        (station_uuid,)
    )
    output = [
        dict((cursor.description[i][0], value) for i, value in enumerate(row))
        for row in cursor.fetchall()
    ]

    formatted_ports = []
    for port in output:
        if fed_funded_only and not port["federally_funded"]:
            continue

        formatted_ports.append({
            "id": port["port_id"],
            "type": port["port_type"] or "Not Provided",
        })

    return formatted_ports


def get_removable_stations_by_dr_id(cursor, dr_id):
    """
        Convenience function that returns a
        list of station_uuids that can be deleted due
        to not having any station data within the module tables.
    """
    removable_stations = []
    get_stations_query = f"""
        SELECT sr.station_uuid
        FROM {ModuleDataTables["RegisteredStations"].value} sr
        WHERE sr.dr_id = %s
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module2"].value} m2
            WHERE sr.station_uuid = m2.station_uuid)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module3"].value} m3
            WHERE sr.station_uuid = m3.station_uuid)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module4"].value} m4
            WHERE sr.station_uuid = m4.station_uuid)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module5"].value} m5
            WHERE sr.station_uuid = m5.station_uuid)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module6"].value} m6
            WHERE sr.station_uuid = m6.station_uuid)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module7"].value} m7
            WHERE sr.station_uuid = m7.station_uuid)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module8"].value} m8
            WHERE sr.station_uuid = m8.station_uuid)
        AND NOT EXISTS (SELECT 1 FROM {ModuleDataTables["Module9"].value} m9
            WHERE sr.station_uuid = m9.station_uuid)
    """
    try:
        cursor.execute(get_stations_query, (dr_id,))
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Error in get_removable_stations_by_dr_id(): {repr(e)}"
        ) from e

    removable_stations = [row[0] for row in cursor.fetchall()]
    return removable_stations


def get_all_federally_funded_stations(cursor):
    """
    Convenience function that returns a list of federally funded station uuids
    """
    get_fed_funded_stations_query = f"""
        SELECT DISTINCT sr.station_uuid FROM {station_registrations} sr
        INNER JOIN {station_ports} sp ON sr.station_uuid = sp.station_uuid
        WHERE sr.dr_id IS NOT NULL
    """ + get_fed_funded_filter("sr", "sp")
    try:
        cursor.execute(get_fed_funded_stations_query, None)
    except Exception as e:
        raise EvChartDatabaseAuroraQueryError(
            message=f"Error in get_all_federally_funded_stations(): {repr(e)}"
        ) from e

    fed_funded_stations = [row[0] for row in cursor.fetchall()]
    return fed_funded_stations


def get_network_provider_uuid(station_uuid, cursor):
    """
        Convenience function to retrieve network_provider_uuid
        from network_provider table for a given station.
    """
    sql = f"""SELECT np.network_provider_uuid
              FROM {network_providers} np
              INNER JOIN {station_registrations} sr
              ON sr.network_provider = np.network_provider_value
              WHERE sr.station_uuid = %s
          """
    np_uuid = execute_query_fetchone(
        query=sql,
        data=station_uuid,
        cursor=cursor,
        message="Error thrown retrieving network_provider_uuid"
    )

    if np_uuid is None or len(np_uuid) == 0:
        raise EvChartDatabaseAuroraQueryError(
            message=(
                f"""Error thrown in get_network_provider_uuid(),
                network_provider_uuid for station {station_uuid}
                does not exist."""
            )
        )
    else:
        return np_uuid[0]


def update_network_provider_uuid(station_uuid, network_provider_uuid, cursor):
    """
        Convenience function that sets/updates network_provider_uuid in
        station_registrations based on what is the existing network_provider
        field passed in during creation/update.
    """
    sql = f"""
        UPDATE {station_registrations}
        SET network_provider_uuid = %s
        WHERE station_uuid = %s
    """

    execute_query(
        query=sql,
        data=(network_provider_uuid, station_uuid),
        cursor=cursor,
        message="Error thrown updating network_provider_uuid in station_registration"
    )


def get_network_provider_uuid_by_network_provider_value(network_provider, cursor):
    """
        Convenience function to retrieve network_provider_uuid
        from network_provider table for a given station.
    """
    sql = f"""SELECT network_provider_uuid
              FROM {network_providers}
              WHERE network_provider_value = %s
          """
    np_uuid = execute_query_fetchone(
        query=sql,
        data=network_provider,
        cursor=cursor,
        message="Error thrown retrieving network_provider_uuid"
    )

    if np_uuid is None or len(np_uuid) == 0:
        raise EvChartDatabaseAuroraQueryError(
            message=(
                f"""Error thrown in get_network_provider_uuid_by_network_provider_value(),
                network_provider_uuid for network_provider_value {network_provider}
                does not exist."""
            )
        )
    else:
        return np_uuid[0]

