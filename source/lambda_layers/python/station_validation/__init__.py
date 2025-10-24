"""
station_validation

This file lists the station validation functions that need to be ran against station data for both post and patch APIs.
All functions are defined in these other files:
validate_authorization_and_recipient_types.py, validate_data_integrity.py, validate_federally_and_non_federally_funded_criteria.py
All functions will take in "validation_options' as a parameter, which is a dictionary that consists of variables that will be
referenced in the function. These variables include station data, api type, authorization token, feature toggle set, and a cursor object.
"""

from station_validation.validate_authorizations_and_recipient_types import (
    validate_dr_is_authorized,
    validate_recipient_type,
    validate_authorized_subrecipients
)

from station_validation.validate_data_integrity import (
    validate_fields,
    validate_station_datatypes,
)

from station_validation.validate_federally_and_non_federally_funded_criteria import (
    validate_federally_and_non_federally_funded_station
)

"""
List of station validation functions used in post and patch station api
"""

# TODO if you are ready to implement validation function to post api, just uncomment the function
common_station_validations = [
    validate_dr_is_authorized,
    validate_recipient_type,
    validate_authorized_subrecipients,
    validate_fields,
    validate_station_datatypes,
    validate_federally_and_non_federally_funded_station,
    # TODO: create validate_module_data_exists_for_ports - only used in patch
    # TODO: create validate_existing_srs_not_repeated - only used in patch
]
