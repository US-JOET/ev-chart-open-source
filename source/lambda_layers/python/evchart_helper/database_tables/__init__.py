"""
evchart_helper.database_tables

Holds the references to the current database tables in the application.
Referencing the enum keys within sql calls in APIs will allow for seamless table
updates
"""
from enum import Enum

# pylint: disable=invalid-name

class ModuleDataTables(Enum):
    """
    Key, Value pairs that hold the updated references to the aurora database tables
    Import the class and use the keys when referencing database tables in APIs
    Example: ModuleDataTables.StationAuthorizations.value
    """
    Metadata = "evchart_data_v3.import_metadata"
    Module1 = "evchart_data_v3.module1_data_v3"
    Module2 = "evchart_data_v3.module2_data_v3"
    Module3 = "evchart_data_v3.module3_data_v3"
    Module4 = "evchart_data_v3.module4_data_v3"
    Module5 = "evchart_data_v3.module5_data_v3"
    Module6 = "evchart_data_v3.module6_data_v3"
    Module7 = "evchart_data_v3.module7_data_v3"
    Module8 = "evchart_data_v3.module8_data_v3"
    Module9 = "evchart_data_v3.module9_data_v3"
    RegisteredStations = "evchart_data_v3.station_registrations"
    StationAuthorizations = "evchart_data_v3.station_authorizations"
    EvErrorData = "evchart_data_v3.ev_error_data"
    StationPorts = "evchart_data_v3.station_ports"
    NetworkProviders = "evchart_data_v3.network_providers"
    MetadataHistory = "evchart_data_v3.import_metadata_history"