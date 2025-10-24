"""
InfraRemoveTestData

Generally run in the Prod account to remove test data generated when testing a new release
deployment.
"""
import logging

from evchart_helper import aurora
from evchart_helper.database_tables import ModuleDataTables
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

logger = logging.getLogger("InfraRemoveTestData")
logger.setLevel(logging.DEBUG)


def handler(event, _context):
    connection = aurora.get_connection()
    cursor = connection.cursor()

    features = FeatureToggleService().get_active_feature_toggles(log_event=logger)

    remove_org = event.get('org_id')
    operation_delete = event.get('delete')

    run_data = {
        "org_id" : remove_org,
        "delete" : operation_delete
    }

    stations_results, uploads_results, auth_results = collect_all_keys(cursor, remove_org, features)

    commands = []
    #get all sql commands to execute
    if operation_delete:
        #Get commands to remove data from module data, import metadata, and import metadata history
        commands.extend(get_remove_from_data_tables_commands(uploads_results))
        #Get commands to remove station auth history
        commands.extend(get_remove_from_auth_tables_commands(auth_results))
        #Finally, get commands to remove stations from station tables
        commands.extend(get_remove_from_station_tables_commands(stations_results))
    else:
        commands.extend(get_data_changes_commands(uploads_results, stations_results, auth_results))

    results = []
    results.append(run_data)
    results.append(execute_all_commands(cursor, commands))
    results.append(commands)

    connection.commit()
    aurora.close_connection()
    return results

def collect_all_keys(cursor, org_id, features):
    table_station_registrations = ModuleDataTables.RegisteredStations.value
    table_import_metadata = ModuleDataTables.Metadata.value
    table_station_authorizations = ModuleDataTables.StationAuthorizations.value

    authorizer_column = "authorizer" if Feature.N_TIER_ORGANIZATIONS in features else "dr_id"

    cursor.execute(
        f"SELECT station_uuid FROM {table_station_registrations} WHERE dr_id = %s", # nosec - no SQL injection possible
        (org_id,)
    )
    station_uuids = [row[0] for row in cursor.fetchall()]
    cursor.execute(
        f"SELECT upload_id FROM {table_import_metadata} WHERE parent_org = %s", # nosec - no SQL injection possible
        (org_id,)
    )
    upload_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute(
        f"SELECT authorization_uuid FROM {table_station_authorizations} WHERE {authorizer_column} = %s", # nosec - no SQL injection possible
        (org_id,)
    )
    auth_uuids = [row[0] for row in cursor.fetchall()]

    return station_uuids, upload_ids, auth_uuids

def execute_all_commands(cursor, commands):
    results = []
    for command in commands:
        cursor.execute(command)
        returned = cursor.fetchall()
        if returned:
            results.append([str(item) for item in list(returned[0])])
    return results

def format_select_command(table, column_name, column_value):
    return f"""SELECT * FROM evchart_data_v3.{table} WHERE {column_name} = '{column_value}' """

def format_delete_command(table, column_name, column_value):
    return f"""DELETE FROM evchart_data_v3.{table} WHERE {column_name} = '{column_value}' """

def format_mod_table(module_id):
    return f"module{module_id}_data_v3"

def get_data_changes_commands(uploads_result, stations_results, auth_results):
    commands = []
    upload_id_tables = ["import_metadata", "import_metadata_history"]
    for i in range(2, 10):
        for upload in uploads_result:
            commands.append(format_select_command(format_mod_table(i), "upload_id", upload))
    for db_table in upload_id_tables:
        for upload_id in uploads_result:
            commands.append(format_select_command(db_table, "upload_id", upload_id))

    station_tables = ["station_ports", "station_registrations", "station_registrations_history"]
    for db_table in station_tables:
        for station_id in stations_results:
            commands.append(format_select_command(db_table, "station_uuid", station_id))

    auth_tables = ["station_authorizations", "station_authorizations_history"]
    for auth_table in auth_tables:
        for auth_uuid in auth_results:
            commands.append(format_select_command(auth_table, "authorization_uuid", auth_uuid))

    return commands #Return multiple sets to create one csv table

def get_remove_from_data_tables_commands(uploads_result):
    commands = []
    upload_id_tables = ["import_metadata", "import_metadata_history"]
    for i in range(2, 10):
        for upload in uploads_result:
            commands.append(format_delete_command(format_mod_table(i), "upload_id", upload))
    for db_table in upload_id_tables:
        for upload_id in uploads_result:
            commands.append(format_delete_command(db_table, "upload_id", upload_id))
    return commands

def get_remove_from_station_tables_commands(stations_results):
    commands = []
    station_tables = ["station_ports", "station_registrations", "station_registrations_history"]
    for db_table in station_tables:
        for station_id in stations_results:
            commands.append(format_delete_command(db_table, "station_uuid", station_id))
    return commands

def get_remove_from_auth_tables_commands(auth_results):
    commands = []
    auth_tables = ["station_authorizations", "station_authorizations_history"]
    for auth_table in auth_tables:
        for auth_uuid in auth_results:
            commands.append(format_delete_command(auth_table, "authorization_uuid", auth_uuid))
    return commands
