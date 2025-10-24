"""
APIGetDraftOrSubmittedData

Retrieve a summary list of module data for a particular organization that has been submitted to the
system and is currently in a Draft or Submitted status.
"""
import json
import logging

from evchart_helper import aurora
from evchart_helper.api_helper import (
    execute_query, get_headers
)
from evchart_helper.custom_exceptions import (EvChartAuthorizationTokenInvalidError, EvChartDatabaseAuroraQueryError,
                                              EvChartMissingOrMalformedHeadersError, EvChartJsonOutputError)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.module_helper import (
    format_sub_recipient,
    format_direct_recipient,
    format_module_frequency,
    format_module_name,
    format_datetime_obj,
    format_fullname_from_email
)
from evchart_helper.session import SessionManager
from evchart_helper.database_tables import ModuleDataTables
from database_central_config import DatabaseCentralConfig
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

logger = logging.getLogger("APIGetDraftOrSubmittedData")
logger.setLevel(logging.INFO)

import_metadata = ModuleDataTables["Metadata"].value

@SessionManager.check_session()
def handler(event, _context):
    log_event = LogEvent(event= event, api= "APIGetDraftOrSubmitted", action_type= "Read")
    connection = aurora.get_connection()
    with connection.cursor() as cursor:
        try:
            #log setup
            if log_event.is_auth_token_valid() is False:
                raise EvChartAuthorizationTokenInvalidError()
            feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)
            #check if headers are valid and parse the event headers
            headers = get_headers(event=event, headers=["status"])
            status = headers.get("status")

            #get org info from auth token
            token = log_event.get_auth_token()
            org_id = token.get("org_id")
            recipient_type = token.get("recipient_type")

            #validating draft or submitted status
            validate_status(status)
            output = []
            logger.debug(f"Recipient_type: {recipient_type}, Status: {status}, Org id: {org_id}")

           #gets the module data with the corresponding status
            if status.lower() == 'draft':
                output = get_draft_data(cursor, org_id)

            elif status.lower() == 'submitted' or recipient_type == "joet":
                output = get_submitted_data(cursor, org_id, recipient_type)

            #format the data returned from database
            if len(output) > 0:
                format_metadata(recipient_type, output, feature_toggle_set)

            logger.debug(f"Formatted data: {output}")


        except (EvChartAuthorizationTokenInvalidError,
                EvChartMissingOrMalformedHeadersError,
                EvChartDatabaseAuroraQueryError,
                EvChartJsonOutputError
         ) as e:

            log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
            return_obj = e.get_error_obj()

        else:
            log_event.log_successful_request(
                message= "Successfully retrieved modules",
                status_code= 200
            )
            return_obj = {
                'statusCode' : 200,
                'headers': { "Access-Control-Allow-Origin": "*" },
                'body': json.dumps(output)
            }

        finally:
            connection.commit()
            aurora.close_connection()

        return return_obj


#helper function that throws an error if "status" request parameters is malformed
def validate_status(status):
    #checks if the status is valid
    if status.lower() == "draft" or status.lower() == "submitted":
        return True
    else:
        error_message = f"Error thrown in validate_status(). Malformed status type: {status}"
        raise EvChartMissingOrMalformedHeadersError(message= error_message)


#helper function that returns a list of dictionaries of the draft data for the given org_id
def get_draft_data(cursor, org_id):
    query = f"SELECT * FROM {import_metadata} WHERE (submission_status='Draft' AND org_id=%s) OR (submission_status='Processing' AND org_id=%s)" # nosec - SQL injection not possible
    #no need for try catch since execute_query will raise EvchartDatabaseAuroraQueryError if query is unsuccessful
    module_data = execute_query(query=query, data=(org_id, org_id), cursor=cursor, message="Helper method: get_draft_data()." )

    #checks if any rows were returned with correspoinding submission_status and org_id
    if module_data is None:
        logger.debug("Org id: %s does not have any draft data", org_id)

    return module_data


#helper function that returns a list of dictionaries of the modules with a status of "submitted", "rejected", and "pending approval"
def get_submitted_data(cursor, org_id, recipient_type):
    query = ""
    module_data = None

    if recipient_type.lower() == 'sub-recipient':
        query = f"SELECT * FROM {import_metadata} WHERE submission_status !='Draft' AND org_id=%s" # nosec - SQL injection not possible
        module_data = execute_query(query=query, data=(org_id,), cursor=cursor, message="Helper method: get_submitted_data().")

    elif recipient_type.lower() == 'direct-recipient':
        query = (
            f"SELECT * FROM {import_metadata} "
            "WHERE ( "
            "  submission_status in "
            "    ('Pending', 'Approved', 'Submitted', 'Rejected') AND "
            "  parent_org=%s "
            ") OR "
            "org_id = %s"
        )
        module_data = execute_query(query=query, data=(org_id,org_id,), cursor=cursor, message="Helper method: get_submitted_data().")

    elif recipient_type.lower() == "joet":
        query = f"SELECT * FROM {import_metadata} WHERE submission_status ='Submitted' or submission_status='Approved'" # nosec - SQL injection not possible
        module_data = execute_query(query=query, data=None, cursor=cursor, message="Helper method: get_submitted_data().")

    #checking if there is submitted data to be returned
    if module_data is None:
        logger.debug("Org id: %s does not have any draft data", org_id)

    return module_data


#helper function that returns a list of dictionaries of the formatted module data to be displayed on the table
def format_metadata(recipient_type, output, feature_toggle_set=frozenset()):
    config = DatabaseCentralConfig()

    for module_data_dict in output:


        #formatting uploaded_on and submitted_on datetime obj
        format_datetime_obj(module_data_dict)

        if Feature.DATABASE_CENTRAL_CONFIG in feature_toggle_set:
            module_id = str(module_data_dict["module_id"])

            #central config formatting module_name
            module_data_dict["module_name"] = config.module_display_name(module_id)

            #central config formatting module_frequency
            if config.module_frequency(module_id) != "quarterly":
                module_data_dict["module_frequency"] = config.module_frequency_proper(module_id)
            else:
                module_data_dict["module_frequency"] = config.module_frequency_quarter(module_data_dict.get("quarter"))
        else:
            #formatting module_name
            format_module_name(module_data_dict)

            #formatting module_frequency
            format_module_frequency(module_data_dict)

        format_fullname_from_email(module_data_dict)

        #formatting direct_recipient variable for output only if user is an SR or in Draft state
        if recipient_type.lower() == 'sub-recipient' or module_data_dict["submission_status"].lower() == "draft":
            format_direct_recipient(module_data_dict)

        #formatting sub_recipient variable for output only if user is a DR viewing submittals
        if recipient_type.lower() == "direct-recipient" and module_data_dict["submission_status"].lower() != "draft":
            format_sub_recipient(module_data_dict)

        #formatting data for JO view to see all submitted modules from all DRs and SRs
        if recipient_type.lower() == "joet":
            format_direct_recipient(module_data_dict)
            format_sub_recipient(module_data_dict)

    return output
