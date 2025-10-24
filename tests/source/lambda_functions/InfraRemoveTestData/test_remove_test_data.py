# # import pytest
from InfraRemoveTestData.index import (
    get_remove_from_data_tables_commands,
    get_remove_from_station_tables_commands,
    get_remove_from_auth_tables_commands,
)

def test_get_remove_import_id_commands():
    good_delete_commands = [
        """DELETE FROM evchart_data_v3.import_metadata WHERE import_id = "123-456" """,
        """DELETE FROM evchart_data_v3.import_metadata_history WHERE import_id = "123-456" """,
        """DELETE FROM evchart_data_v3.module2_data_v3 WHERE import_id = "123-456" """,
        """DELETE FROM evchart_data_v3.module3_data_v3 WHERE import_id = "123-456" """,
        """DELETE FROM evchart_data_v3.module4_data_v3 WHERE import_id = "123-456" """,
        """DELETE FROM evchart_data_v3.module5_data_v3 WHERE import_id = "123-456" """,
        """DELETE FROM evchart_data_v3.module6_data_v3 WHERE import_id = "123-456" """,
        """DELETE FROM evchart_data_v3.module7_data_v3 WHERE import_id = "123-456" """,
        """DELETE FROM evchart_data_v3.module8_data_v3 WHERE import_id = "123-456" """,
        """DELETE FROM evchart_data_v3.module9_data_v3 WHERE import_id = "123-456" """,
    ]

    uploads_results = ["123-456"]
    delete_commands = []
    # Get commands to remove data from module data, import metadata, and import metadata history
    command_list = get_remove_from_data_tables_commands(uploads_results)
    delete_commands.extend(command_list)

    assert delete_commands.sort() == good_delete_commands.sort()

def test_get_remove_auth_uuid_commands():
    good_delete_commands = [
        """DELETE FROM evchart_data_v3.station_authorizations WHERE authorization_uuid = "321-987" """,
        """DELETE FROM evchart_data_v3.station_authorizations_history WHERE authorization_uuid = "321-987" """
    ]

    auth_results = ["321-987"]
    delete_commands = []
    #Get commands to remove station auth history
    command_list = get_remove_from_auth_tables_commands(auth_results)
    delete_commands.extend(command_list)

    assert delete_commands.sort() == good_delete_commands.sort()

def test_get_remove_station_registrations_commands():
    good_delete_commands = [
        """DELETE FROM evchart_data_v3.station_registrations WHERE station_uuid = "456-789" """,
        """DELETE FROM evchart_data_v3.station_registrations_history WHERE station_uuid = "456-789" """
    ]

    stations_results = ["456-789"]
    delete_commands = []
    #Get commands to remove stations from station tables
    command_list = get_remove_from_station_tables_commands(stations_results)
    delete_commands.extend(command_list)

    assert delete_commands.sort() == good_delete_commands.sort()
