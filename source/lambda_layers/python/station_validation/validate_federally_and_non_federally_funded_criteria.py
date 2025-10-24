"""
validate_federally_and_non_federally_funded_criteria

Series of functions that validate individual station data for both post and patch APIs. This specific file tests
validity and logic for federal and non federally funded stations. All functions will take in "validation_options'
as a parameter, which is a dictionary that consists of variables that will be referenced in the function.
These variables include station data, api type, authorization token, feature toggle set, and a cursor object.
"""

import pandas as pd
from evchart_helper.api_helper import execute_query, execute_query_df
from feature_toggle.feature_enums import Feature


from evchart_helper.database_tables import ModuleDataTables
station_registrations = ModuleDataTables["RegisteredStations"].value
station_ports = ModuleDataTables["StationPorts"].value

def validate_funding_type(validation_options):
    """
    Convenience function to verify that inputs are valid funding types, given API type.
    For federally funded stations, at least 1 funding type must be selected, for non-federally
    funded stations, no funding type should be selected. Returns an error message if invalid,
    or an empty string if valid.
    """
    api = validation_options.get("api")
    station = validation_options.get("station")
    cursor = validation_options.get("cursor")
    funding_types = ["NEVI", "CFI", "EVC_RAA", "CMAQ", "CRP", "OTHER"]
    federally_funded = station.get("federally_funded")
    error_message = ""

    if api.lower() == "post":
        # checks funding type against federally funded stations
        if (
            federally_funded and all(station.get(key, None) == 0 for key in funding_types)
        ):
            error_message = (
                "Funding Type is a required field for federally funded stations and 1 option must be selected. "
            )

        # checks funding type against non federally funded stations
        if (
            not federally_funded and any(station.get(key, None) == 1 for key in funding_types)
        ):
            error_message = (
                "Funding Type should not be selected for non-federally funded stations. "
            )

    if api.lower() == "patch":
        query = (
            f"SELECT NEVI, CFI, EVC_RAA, CMAQ, CRP, OTHER "
            f"FROM {station_registrations} WHERE station_uuid = %s "
            # nosec
            # SQL injection not possible
        )
        df = execute_query_df(query, (station["station_uuid"],), cursor)

        # updates df with the updated funding types and num_fed_funded values
        df.update(pd.DataFrame([station]))
        df = df.astype(int)

        #  sets error message if funding type was not set for fed funded stations
        if federally_funded and (df == 0).all().all():
            error_message = (
                "Funding Type is a required field for federally funded stations and 1 option must be selected. "
            )

        # sets error message if funding type was set for non-fed funded stations
        if not federally_funded and not (df == 0).all().all():
            error_message = (
                "Funding Type should not be selected for non-federally funded stations. "
            )
    return error_message


def validate_port_equality(validation_options):
    """
    Convenience function to verify that the federally funded ports in the database match the number of ports provided
    in station input. Returns empty string if all input are matched, else an error message is returned stating if federal or
    non-federal ports are not equal or if port data does not meet criteria for fed or nonfed funded station.
    """
    api = validation_options.get("api")
    feature_toggle_set = validation_options.get("feature_toggle_set")
    station = validation_options.get("station").copy()
    cursor = validation_options.get("cursor")
    federally_funded = station.get("federally_funded")
    error_message = ""
    # cross_check will be used to store current and updated values of port data, in order to verify equality at the end
    cross_check = {}

    port_fields =["num_fed_funded_ports", "num_non_fed_funded_ports", "fed_funded_ports", "non_fed_funded_ports"]

    # returning true if no port fields are changed and port equality does not need to be checked
    if all(port_field not in station for port_field in port_fields):
        return True

    # grabbing db values for number of ports field and ports provided field for patch station
    if api == "patch":
        get_station_info_query = f"""
            Select
            sr.num_non_fed_funded_ports,
            sr.num_fed_funded_ports,
            COUNT(CASE WHEN sp.federally_funded = 1 THEN 1 END)
             AS fed_funded_ports,
            COUNT(CASE WHEN sp.federally_funded = 0 THEN 1 END)
             AS non_fed_funded_ports
            from {station_registrations} sr
            inner join {station_ports} sp on sr.station_uuid = sp.station_uuid
            where sr.station_uuid=%s
        """
        db_results = execute_query(
            query=get_station_info_query,
            data=station["station_uuid"],
            cursor=cursor
        )
        cross_check = db_results[0]

    # checks station data to see if port values need to be updated with new data before doing comparison
    # FED FUNDED PORTS
    if "num_fed_funded_ports" in station:
        if (
            Feature.REGISTER_NON_FED_FUNDED_STATION not in feature_toggle_set and
            (station["num_fed_funded_ports"] == 0 or station["num_fed_funded_ports"] is None)
        ):
            error_message = "Number of federal funded ports cannot be 0 or null."
        try:
            cross_check["num_fed_funded_ports"] = \
                int(station["num_fed_funded_ports"])
        except (TypeError, ValueError):
            cross_check["num_fed_funded_ports"] = 0

    if "fed_funded_ports" in station:
        cross_check["fed_funded_ports"] = len(station["fed_funded_ports"])

    # checks if number of federally funded ports and ports provided are equal after the station updates
    if cross_check["fed_funded_ports"] != cross_check["num_fed_funded_ports"]:
        error_message += "Number of federal funded ports must match the federal ports provided."

    # NON FED FUNDED PORTS
    # check db for equality where port list is updated
    if "num_non_fed_funded_ports" in station:
        if (
            station["num_non_fed_funded_ports"] is None
            or station["num_non_fed_funded_ports"] == ""
        ):
            cross_check["num_non_fed_funded_ports"] = 0
        else:
            cross_check["num_non_fed_funded_ports"] = int(
                station["num_non_fed_funded_ports"]
            )
    # check db for equality where port list is updated
    if "non_fed_funded_ports" in station:
        cross_check["non_fed_funded_ports"] = \
            len(station["non_fed_funded_ports"])

    # set values for num non fed when it is left blank
    if (
        "num_non_fed_funded_ports" not in station and
        cross_check["num_non_fed_funded_ports"] is None
    ):
        cross_check["num_non_fed_funded_ports"] = 0

    # checks if number of non-federally funded ports and ports provided are equal after the station updates
    if cross_check["non_fed_funded_ports"] != \
        cross_check["num_non_fed_funded_ports"]:
        error_message += "Number of non-federal funded ports must match the non-federal ports provided."

    # apply set of checks dependent on federally funded
    error_message += validate_port_logic_against_fed_funded_criteria(federally_funded, cross_check)
    return error_message


def validate_port_logic_against_fed_funded_criteria(federally_funded, cross_check):
    error_message = ""
    if federally_funded:
        # checks if fed funded ports do not have defined fed funded ports
        if int(cross_check["num_fed_funded_ports"]) < 1 or int(cross_check["fed_funded_ports"] < 1):
            error_message += "Must have at least 1 federally funded port on record in order to be considered a federally funded station. "
    else:
        # checks if fed funded ports are provided
        if int(cross_check["num_fed_funded_ports"]) > 0 or int(cross_check["fed_funded_ports"] < 0):
            error_message += "Cannot have any federally funded ports on record in order to be considered a non-federally funded station. "

        # checks if non fed funded ports are missing
        if cross_check["num_non_fed_funded_ports"] < 1 or int(cross_check["non_fed_funded_ports"] < 1):
            error_message += "Must have at least 1 non-federally funded port on record in order to be considered a non-federally funded station. "
    return error_message


def validate_federally_and_non_federally_funded_station(validation_options):
    """
    Convenience function that verifies if a station follows the criteria for fed or non fed funded station.
    For fed funded stations, a station must have num_fed_funded > 0, must list at least 1 port,
    and must have 1 funding type selected. For non fed funded stations, a station must have num_fed_funded = 0,
    only lists non-fed funded ports, and has no funding type selected. These 3 conditions are checked and
    if any are invalid, this function returns an error object, else returns True.
    """
    station = validation_options.get("station")
    # verify criteria based on if this station is defined to be federally_funded or not
    federally_funded = station.get("federally_funded")

    funding_types = ["NEVI", "CFI", "EVC_RAA", "CMAQ", "CRP", "OTHER"]
    federally_funded_criteria = ["fed_funded_ports", "non_fed_funded_ports", "num_fed_funded", "num_non_fed_funded"] + funding_types
    fed_funded_fields_updated = [field for field in federally_funded_criteria if field in station]
    if fed_funded_fields_updated:
        validate_funding_type_result = validate_funding_type(validation_options)
        validate_ports_provided_against_fed_funded_criteria_result = validate_port_equality(validation_options)

        if validate_funding_type_result or validate_ports_provided_against_fed_funded_criteria_result:
            station_type = "federally" if federally_funded else "non-federally"
            return {
                "validate_federally_and_non_federally_funded_station()": (
                    f"Invalid attributes for {station_type} funded station. {validate_funding_type_result + validate_ports_provided_against_fed_funded_criteria_result}"
                )
            }
    return True
