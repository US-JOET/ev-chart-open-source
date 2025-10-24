"""
validate_data_integrity

Series of functions that validate station and port data for both post and patch APIs. Some functions have different validation
logic depending if the api is "post" or "patch", but ultimately checks for the same idea. These functions mainly focus on
datatypes, required or recommended fields, and port equality.
"""
import pandas as pd
from evchart_helper.database_tables import ModuleDataTables
from database_central_config import DatabaseCentralConfig

from module_validation import (
    validated_field
)

station_registrations = ModuleDataTables["RegisteredStations"].value
station_authorizations = ModuleDataTables["StationAuthorizations"].value
station_ports = ModuleDataTables["StationPorts"].value
network_providers = ModuleDataTables["NetworkProviders"].value



def validate_fields(validation_options):
    """
    Convenience function that verifies that all required fields are present for post requests or
    verifies that valid station fields are present for patch requests. Returns a dict with errors
    that the station data either has unknown fields, missing required fields, or both.
    """
    api = validation_options.get("api").lower()
    station = validation_options.get("station").copy()
    # these fields are required for the request but are not actual variables in the database
    additional_required_fields = ["fed_funded_ports", "non_fed_funded_ports", "authorized_subrecipients", "federally_funded"]
    # these fields are valid in patch requests, but are not actual variables in the database
    optional_fields = ["station_uuid", "srs_added", "srs_removed", "ports_removed", "nickname"]


    config = DatabaseCentralConfig()
    required_station_fields = config.required_fields("station_registrations")
    required_station_fields.update(additional_required_fields)
    all_valid_station_fields = required_station_fields.union(set(optional_fields))
    station_fields = set(list(key for key in station.keys()))
    message = ""

    # checks if there are any unkown fields while also verifying that fields are valid for patch requests
    if station_fields-all_valid_station_fields:
        unknown_fields = station_fields-all_valid_station_fields
        message += f"Unknown fields {unknown_fields} "

        # removing unknown fields from station_fields
        station_fields = station_fields - set(unknown_fields)

    # strictly checks that all required station data is present for post requests
    if api == "post":
        if not required_station_fields.issubset(station_fields):
            message += f"Missing required fields {required_station_fields-station_fields} "
    # strictly checks that station_uuid and federally funded is present in patch requests
    if api == "patch":
        if "station_uuid" not in station_fields:
            message  += "Field must be present for patch requests {'station_uuid'}. "

        if "federally_funded" not in station_fields:
            message  += "Field must be present for patch requests {'federally_funded'}. "

    if message:
        return {"validate_required_fields()": message}
    return True


def validate_station_datatypes(validation_options):
    """
    Convenience function that uses the central config file to verify that the station data and port data
    is of valid datatypes. If there are fields with invalid datatypes, an error is thrown and the dict
    that describes the errors is printed out in the error message. Returns True if all datatypes are valid.
    """
    station = validation_options.get("station").copy()
    feature_toggle_set = validation_options.get("feature_toggle_set")

    # removing ports arrays because it needs to be validated against port table (validated later in function)
    fed_funded_ports = station.pop("fed_funded_ports") if "fed_funded_ports" in station else []
    non_fed_funded_ports = station.pop("non_fed_funded_ports") if "non_fed_funded_ports" in station else []

    # removing other fields that have arrays
    station.pop("authorized_subrecipients", None)
    station.pop("srs_added", None)
    station.pop("srs_removed", None)
    station.pop("ports_removed", None)


    # get invalid station data
    station_df = pd.DataFrame(station, index=[0])
    station_df = station_df.astype(str)
    station_definitions = get_field_definitions("station_registrations")
    invalid_station_data = get_invalid_station_fields(station_df, station_definitions, feature_toggle_set)

    # get invalid port data
    port_data = fed_funded_ports + non_fed_funded_ports
    port_data_df = pd.DataFrame(port_data)
    port_data_df = port_data_df.astype(str)
    port_definitions = get_field_definitions("station_ports")
    invalid_port_data = get_invalid_station_fields(port_data_df, port_definitions, feature_toggle_set)

    if invalid_station_data or invalid_port_data:
        return {"validate_station_datatypes()": invalid_station_data + invalid_port_data}

    return True


def get_field_definitions(table_name):
    """
    Helper function for validate_station_datatypes. Get's the module definitions for the table
    specified. Returns a dict with the field being the key and it's definition dict as the value.
    """
    config = DatabaseCentralConfig()
    table_fields = config.module_validation(table_name)
    definition = table_fields.copy()
    for column_label in table_fields.keys():
            definition[column_label]["field_name"] = column_label
    return definition


def get_invalid_station_fields(df, definitions, feature_toggle_set):
    """
    Helper function for validate_station_datatypes.  Calls the same helper function use for validating module
    datatypes and returns the error object/dict that specifies the field name and type of error in the station data.
    """
    invalid_data = []
    for column_label, column_series in df.items():
        to_be_validated = column_series
        if column_label in definitions.keys():
            response = validated_field(
                definition=definitions[column_label],
                data=to_be_validated,
                module_number=1,
                feature_toggle_set=feature_toggle_set,
            )
            invalid_data.extend(response.get("conditions", []))
    return invalid_data