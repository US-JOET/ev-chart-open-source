"""
error_report_messages_enum

A helper module that contains the definitions for all the error report error messages so that they
are managed all in one place.
"""
from enum import Enum

class ErrorReportMessages(Enum):
    # unique constraints
    DUPLICATE_RECORD_IN_SAME_UPLOAD = 'Duplicate rows found within this submission for these Primary Keys {fields}. Delete duplicate rows.'
    DUPLICATE_RECORD_IN_SYSTEM = 'Duplicate rows found with these Primary Keys {fields} found in previous upload id {upload_id}. Delete duplicate rows.'
    DUPLICATE_COLUMN = '"{column_name}" column has duplicates. Delete duplicate column.'
    UNKNOWN_DATATYPE  = 'Incorrect datatype in definition for column "{column_name}". Refer to Data Dictionary tab in Data Input Template for guidance.'
    UNKNOWN_COLUMN = 'Unknown column "{column_name}" identified. Update or remove unknown column.'
    CSV_EMPTY = 'Uploaded file does not contain any data.'

    # station registration & authorization & status
    STATION_NOT_REGISTERED = 'No station exists in EV-ChART with the combination of Station ID {station_id} and Network Provider {network_provider} for which you are authorized to upload data.'
    SR_NOT_AUTHORIZED_TO_SUBMIT = 'You are not authorized by the Direct Recipient to submit data for Station ID {station_id} and network provider {network_provider}'
    DR_NOT_AUTHORIZED_TO_SUBMIT = 'You are not authorized to submit data for Station ID {station_id} and network provider {network_provider}'
    INVALID_STATION_STATUS_PENDING_APPROVAL = 'Data cannot be submitted for a station that has a pending status.'

    # Missing fields
    MISSING_NETWORK_PROVIDER_COLUMN = '"Network Provider" column is missing. Refer to Resources > Network Provider Names to find network provider values.'
    MISSING_REQUIRED_COLUMN = 'Required column "{column_name}" is missing. Add required column.'
    MISSING_VALUE_FOR_REQUIRED_COLUMN = 'Required value for "{column_name}" is missing at this row and column.'

    # boolean data validation
    INVALID_BOOLEAN_INPUT = 'Value provided is not in the required format. Value must be the word "TRUE" or "FALSE".'

    # string data validation
    INVALID_TIMESTAMP_FORMAT = 'Value for reporting time must be in RFC 3339, the OCPI standard for timestamps.'
    INVALID_WHITESPACE_VALUE = 'Required strings must contain alphanumerical values and must not consist of only spaces.'
    MAX_STRING_LENGTH_EXCEEDED = 'The value provided exceeds maximum length requirement.'
    MIN_STRING_LENGTH_NOT_MET = 'The value provided does not meet the minimum length requirement.'
    EXACT_STRING_LENGTH_NOT_MATCHED = 'Value does not meet exact length requirement'

    # integer data validation
    INVALID_INTEGER_INPUT = 'Value provided is not in the required Integer format. Value must be a whole number.'
    MIN_INTEGER_LENGTH_NOT_MET = 'The integer provided does not meet the minimum value requirement. Refer to Data Dictionary tab in Data Input Template for guidance.'
    MAX_INTEGER_LENGTH_NOT_MET = 'The integer provided does not meet the maximum value requirement. Refer to Data Dictionary tab in Data Input Template for guidance.'
    EXACT_INTEGER_LENGTH_NOT_MATCHED = 'The integer provided does not meet the exact length requirement. Refer to Data Dictionary tab in Data Input Template for guidance.'

    # decimal data validation
    INVALID_DECIMAL_INPUT = 'The value provided must be a decimal.'
    MAX_DECIMAL_LENGTH_EXCEEDED = 'The value provided must not exceed 8 digits and must include 2 decimal places.'
    MAX_DECIMAL_PLACES_EXCEEDED = 'The value provided must not exceed more than 2 decimal places.'
    MIN_DECIMAL_LENGTH_NOT_MET = 'The number of decimals provided does not meet the minimum value requirement. Refer to Data Dictionary tab in Data Input Template for guidance.'
    MAX_DECIMAL_LENGTH_NOT_MET = 'The number of decimals provided does not meet the maximum value requirement. Refer to Data Dictionary tab in Data Input Template for guidance.'

    # bizmagic errors
    # TODO: remove these deprecated errors, not used anywhere
    MODULE_2_INVALID_NULL_VALUES = 'If reporting no sessions, the station_id, network_provider, and port_id must contain values, but all other fields must be blank. Otherwise complete all required fields.'

    MODULE_3_UPTIME_REQUIRED = "Stations operational for at least 1 year must report uptime."

    MODULE_4_INVALID_NULL_VALUES = 'If there are no outages to report, outage_id and outage_duration should be blank. Otherwise, these fields are required.'

    MODULE_9_INVALID_NULL_VALUES = 'If reporting no federal cost information, all required fields must contain values, but all total cost fields must be blanked. Otherwise complete all required fields.'

    # function that formats the parameterized variables into the error description
    def format(self, **kwargs) -> str:
        return self.value.format(**kwargs)
