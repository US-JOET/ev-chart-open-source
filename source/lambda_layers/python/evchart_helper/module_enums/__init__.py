"""
evchart_helper.module_enums

Multi-class enum file that establishes relationships between module related data,
accompanied by helper functions related to the mapping of these classes
"""
from enum import Enum
from evchart_helper.custom_exceptions import EvChartJsonOutputError

# pylint: disable=invalid-name

class ModuleFrequencyProper(Enum):
    """
        Outlining the relationship between module and submission frequency
    """
    Module1 = "One-Time"
    Module2 = "Quarterly"
    Module3 = "Quarterly"
    Module4 = "Quarterly"
    Module5 = "Annual"
    Module6 = "One-Time"
    Module7 = "Annual"
    Module8 = "One-Time"
    Module9 = "One-Time"

class ModulePrimary(Enum):
    """
        Outlining the relationship between module number and the pinned left-most column when viewing
        module data in the application
    """
    Module1 = "station_id_upload"
    Module2 = "session_id"
    Module3 = "port_id"
    Module4 = "outage_id"
    Module5 = "station_id_upload"
    Module6 = "station_id_upload"
    Module7 = "station_id_upload"
    Module8 = "station_id_upload"
    Module9 = "station_id_upload"


class ModuleNames(Enum):
    """
        Outlining the relationship between module number and its official module name
    """
    Module1 = "Station Location"
    Module2 = "Charging Sessions"
    Module3 = "Uptime"
    Module4 = "Outages"
    Module5 = "Maintenance Costs"
    Module6 = "Station Operator Identity"
    Module7 = "Station Operator Program"
    Module8 = "DER Information"
    Module9 = "Capital and Installation Costs"

# broke up each module into its own enum class, AllAttributeNames class may soon be deprecated
class AllAttributeNames(Enum):
    """
        Outlining the relationship between all module database variables in the database and the actual column
        name presented in the application when viewing individual module data
    """
    station_uuid = "Station UUID" # should never be front end visible
    # station_id = "Station ID"
    port_id = "Port ID" #found in mod 2,3,4
    project_id = "Project ID" #found in mod  5,9
    submission_id = "Submission ID" #not found in any
    network_provider = "Network Provider" # 2,3,4,5,6,7,8,9, station_registration
    station_id_upload = "Station ID" # 2,3,4,5,6,7,8,9
    time_at_upload = "Time at Upload" #2,
    # Mod 1
    station_address = "Station Address"
    station_city = "Station City"
    station_state = "Station State"
    station_zip = "Station Zip"
    station_zip_extended = "Station ZIP Extended"
    station_longitude = "Station Longitude"
    station_latitude = "Station Latitude"
    # Mod 2
    charger_id = "Charger ID"
    session_id = "Session ID"
    connector_id = "Connector ID"
    # provider_id = "Network Provider ID"
    session_start = "Session Start"
    session_end = "Session End"
    session_error = "Session Error"
    error_other = "Session Error Description"
    energy_kwh = "Energy Charged"
    power_kw = "Peak Power"
    payment_method = "Payment Method"
    payment_other = "Payment Method Description"
    # Mod 3
    uptime_reporting_start = "Uptime Reporting Start Date"
    uptime_reporting_end = "Uptime Reporting End Date"
    uptime = "Uptime"
    total_outage = "Total Outage"
    total_outage_excl = "Total Excluded Outage"
    # Mod 4
    outage_id = "Outage ID"
    outage_duration = "Outage Duration"
    # Mod 5
    maintenance_report_start = \
        "Maintenance and Repair Cost Reporting Start Date"
    maintenance_report_end = "Maintenance and Repair Cost Reporting End Date"
    caas = "Charging as a Service"
    maintenance_cost_total = "Total Maintenance and Repair Cost"
    maintenance_cost_federal = "Federal Maintenance and Repair Cost"
    maintenance_notes = "Maintenance Notes"
    # Mod 6
    operator_name = "Station Operator Name"
    operator_address = "Station Operator Address"
    operator_city = "Station Operator City"
    operator_state = "Station Operator State"
    operator_zip = "Station Operator ZIP"
    operator_zip_extended = "Station Operator ZIP Extended"
    operator_type = "Operator Type"
    operator_notes = "Operator Notes"
    # Mod 7
    program_report_year = "Opportunity Program Reporting Year"
    opportunity_program = "Opportunity Program Participation"
    program_descript = "Opportunity Program Description"
    # Mod 8
    der_upgrade = "DER Upgrade"
    der_onsite = "Distributed Energy Resource On-Site"
    der_type = "DER Asset Type"
    der_type_other = "DER Asset Type Description"
    der_kw = "Power Output Capacity"
    der_kwh = "Energy Storage Capacity"
    # Mod 9
    station_upgrade = "Station Upgrade"
    real_property_acq_date = "Real Property Acquisition Date"
    real_property_acq_owned = "Real Property Acquisition Owned"
    real_property_cost_total = "Total Real Property Acquisition Cost"
    real_property_cost_federal = "Federal Real Property Acquisition Cost"
    equipment_acq_date = "Charging Equipment Acquisition Date"
    equipment_acq_owned = "Charging Equipment Acquisition Owned"
    equipment_cost_total = "Total Charging Equipment Acquisition Cost"
    equipment_cost_federal = "Federal Charging Equipment Acquisition Cost"
    equipment_install_date = "Charging Equipment Installation Date"
    equipment_install_cost_total = "Total Charging Equipment Installation Cost"
    equipment_install_cost_federal = \
        "Federal Charging Equipment Installation Cost"
    equipment_install_cost_elec = \
        "Charging Equipment Installation Cost - Electric Material"
    equipment_install_cost_const = \
        "Charging Equipment Installation Cost - Construction Material"
    equipment_install_cost_labor = \
        "Charging Equipment Installation Cost - Labor"
    equipment_install_cost_other = \
        "Charging Equipment Installation Cost - Other"
    der_acq_owned = "Distributed Energy Acquisition Owned"
    der_cost_federal = "Federal Distributed Energy Acquisition Cost"
    der_cost_total = "Total Distributed Energy Acquisition Cost "
    der_install_cost_total = "Total Distributed Energy Installation Cost"
    der_install_cost_federal = "Federal Distributed Energy Installation Cost"
    dist_sys_cost_total = "Total Distribution and System Costs"
    dist_sys_cost_federal = "Federal Distribution and System Costs"
    service_cost_total = "Total Service Costs"
    service_cost_federal = "Federal Service Costs"

class AllCommonModuleAttributes(Enum):
    """
        Outlining the relationship between database variable name and frontend column labels for
        the columns that must be present for all module uploads
    """
    station_id_upload = "Station ID"
    network_provider_upload = "Network Provider"

class Module1Attributes(Enum):
    """
        Outlining the relationship between module 1 database variable names and frontend column
        labels when viewing module data
    """
    station_address = "Station Address"
    station_city = "Station City"
    station_state = "Station State"
    station_zip = "Station Zip"
    station_zip_extended = "Station ZIP Extended"
    station_longitude = "Station Longitude"
    station_latitude = "Station Latitude"

class Module2Attributes(Enum):
    """
        Outlining the relationship between module 2 database variable names and frontend column
        labels when viewing module data
    """
    port_id = "Port ID"
    charger_id = "Charger ID"
    session_id = "Session ID"
    connector_id = "Connector ID"
    # provider_id = "Network Provider ID"
    session_start = "Session Start"
    session_end = "Session End"
    session_error = "Session Error"
    error_other = "Session Error Description"
    energy_kwh = "Energy Charged"
    power_kw = "Peak Power"
    payment_method = "Payment Method"
    payment_other = "Payment Method Description"
    # TODO: uncomment this line out when we have moved to reference module2_data_with_constraint table
    # time_at_upload = "Time at Upload"

class Module3Attributes(Enum):
    """
        Outlining the relationship between module 3 database variable names and frontend column
        labels when viewing module data
    """
    port_id = "Port ID"
    uptime_reporting_start = "Uptime Reporting Start Date"
    uptime_reporting_end = "Uptime Reporting End Date"
    uptime = "Uptime"
    total_outage = "Total Outage"
    total_outage_excl = "Total Excluded Outage"

class Module4Attributes(Enum):
    """
        Outlining the relationship between module 4 database variable names and frontend column
        labels when viewing module data
    """
    port_id = "Port ID"
    outage_id = "Outage ID"
    outage_duration = "Outage Duration"

class Module5Attributes(Enum):
    """
        Outlining the relationship between module 5 database variable names and frontend column
        labels when viewing module data
    """
    project_id = "Project ID"
    maintenance_report_start = \
        "Maintenance and Repair Cost Reporting Start Date"
    maintenance_report_end = "Maintenance and Repair Cost Reporting End Date"
    caas = "Charging as a Service"
    maintenance_cost_total = "Total Maintenance and Repair Cost"
    maintenance_cost_federal = "Federal Maintenance and Repair Cost"
    maintenance_notes = "Maintenance Notes"

class Module6Attributes(Enum):
    """
        Outlining the relationship between module 6 database variable names and frontend column
        labels when viewing module data
    """
    operator_name = "Station Operator Name"
    operator_address = "Station Operator Address"
    operator_city = "Station Operator City"
    operator_state = "Station Operator State"
    operator_zip = "Station Operator ZIP"
    operator_zip_extended = "Station Operator ZIP Extended"
    operator_type = "Operator Type"
    operator_notes = "Operator Notes"

class Module7Attributes(Enum):
    """
        Outlining the relationship between module 7 database variable names and frontend column
        labels when viewing module data
    """
    program_report_year = "Opportunity Program Reporting Year"
    opportunity_program = "Opportunity Program Participation"
    program_descript = "Opportunity Program Description"

class Module8Attributes(Enum):
    """
        Outlining the relationship between module 8 database variable names and frontend column
        labels when viewing module data
    """
    der_upgrade = "DER Upgrade"
    der_onsite = "Distributed Energy Resource On-Site"
    der_type = "DER Asset Type"
    der_type_other = "DER Asset Type Description"
    der_kw = "Power Output Capacity"
    der_kwh = "Energy Storage Capacity"

class Module9Attributes(Enum):
    """
        Outlining the relationship between module 9 database variable names and frontend column
        labels when viewing module data
    """
    project_id = "Project ID"
    station_upgrade = "Station Upgrade"
    real_property_acq_date = "Real Property Acquisition Date"
    real_property_acq_owned = "Real Property Acquisition Owned"
    real_property_cost_total = "Total Real Property Acquisition Cost"
    real_property_cost_federal = "Federal Real Property Acquisition Cost"
    equipment_acq_date = "Charging Equipment Acquisition Date"
    equipment_acq_owned = "Charging Equipment Acquisition Owned"
    equipment_cost_total = "Total Charging Equipment Acquisition Cost"
    equipment_cost_federal = "Federal Charging Equipment Acquisition Cost"
    equipment_install_date = "Charging Equipment Installation Date"
    equipment_install_cost_total = "Total Charging Equipment Installation Cost"
    equipment_install_cost_federal = \
        "Federal Charging Equipment Installation Cost"
    equipment_install_cost_elec = \
        "Charging Equipment Installation Cost - Electric Material"
    equipment_install_cost_const = \
        "Charging Equipment Installation Cost - Construction Material"
    equipment_install_cost_labor = \
        "Charging Equipment Installation Cost - Labor"
    equipment_install_cost_other = \
        "Charging Equipment Installation Cost - Other"
    der_acq_owned = "Distributed Energy Acquisition Owned"
    der_cost_federal = "Federal Distributed Energy Acquisition Cost"
    der_cost_total = "Total Distributed Energy Acquisition Cost "
    der_install_cost_total = "Total Distributed Energy Installation Cost"
    der_install_cost_federal = "Federal Distributed Energy Installation Cost"
    dist_sys_cost_total = "Total Distribution and System Costs"
    dist_sys_cost_federal = "Federal Distribution and System Costs"
    service_cost_total = "Total Service Costs"
    service_cost_federal = "Federal Service Costs"

#use dict to map the module number to corresponding class name
def get_module_class_name(mod_num):
    """
        Returns the module enum class specified by the integer that was passed in
    """
    module_class_map = {
        1 : Module1Attributes,
        2 : Module2Attributes,
        3 : Module3Attributes,
        4 : Module4Attributes,
        5 : Module5Attributes,
        6 : Module6Attributes,
        7 : Module7Attributes,
        8 : Module8Attributes,
        9 : Module9Attributes
    }
    if mod_num in module_class_map:
        return module_class_map[mod_num]
    else:
        raise EvChartJsonOutputError(message=f"Error thrown in get_module_class_name, module number passed in is not within the range 1-9.")


def get_UI_col_names_map(mod_num, fields):
    """
        Helper function that takes in a module number and a list of module fields and
        returns a dictionary with the corresponding field and official column name
    """
    mod_class = get_module_class_name(mod_num)
    all_attribute_keys = [
        common_field.name for common_field in AllCommonModuleAttributes
    ]
    all_mod_keys = [common_field.name for common_field in mod_class]
    column_names_map = {}
    for item in fields:
        if item in all_attribute_keys:
            column_names_map[item] = AllCommonModuleAttributes[item].value
        elif item in all_mod_keys:
            column_names_map[item] = mod_class[item].value
        else:
            raise EvChartJsonOutputError(
                message=(
                    f"Error in get_UI_col_table_names in module_enums file. "
                    f"Error mapping out column variable to column title, "
                    f"column {item} is not mapped to a column title."
                )
            )
    return column_names_map


def get_db_col_names_arr(mod_num):
    """
        Helper function that takes in a module number and returns a list of the
        column names that are used for the database table
    """
    mod_class = get_module_class_name(mod_num)

    try:
        common_fields = [field.name for field in AllCommonModuleAttributes]
        module_fields = [field.name for field in mod_class]
        return common_fields + module_fields
    except Exception as e:
        raise EvChartJsonOutputError(message=f"Error getting column names from mod enum file {e}")


def get_list_of_boolean_columns():
    """
        Returns a list of boolean variable names from the module, station, and ports tables
    """
    boolean_columns = [
        #boolean variables in module tables
        "caas",
        "der_upgrade",
        "der_onsite",
        "station_upgrade",
        "real_property_acq_type",
        "real_property_acq_owned",
        "equipment_acq_type",
        "equipment_acq_owned",
        "der_acq_type",
        "der_acq_owned",

        #boolean variables in station table
        "NEVI",
        "CFI",
        "EVC_RAA",
        "CMAQ",
        "CRP",
        "OTHER",
        "AFC",

        #boolean variables in ports table
        "federally_funded"
    ]
    return boolean_columns
