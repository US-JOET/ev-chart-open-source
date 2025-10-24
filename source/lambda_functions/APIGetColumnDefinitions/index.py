"""
APIGetColumnDefinitions

This is a "helper" API that will return the definitions for the columns in the relevant module data
for presentation purposes on the frontend.
"""
import json

from evchart_helper.custom_logging import LogEvent
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartMissingOrMalformedHeadersError
)
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature


@SessionManager.check_session()
def handler(event, _context):
    try:
        log_event = LogEvent(event, api="APIGetColumnDefinitions", action_type="Read")
        feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)
        if log_event.is_auth_token_valid() is False:
            raise EvChartAuthorizationTokenInvalidError()

        request_headers = event["headers"]
        table_name = request_headers["table_name"]

        # adding in federally funded tooltip if feature toggle is turned on
        station_tables = ["station_direct_recipient", "station_sub_recipient", "station_joet"]
        if Feature.REGISTER_NON_FED_FUNDED_STATION in feature_toggle_set and table_name in station_tables:
            feature_toggle_enabled = "_fed_funded_FT_ON"
            table_name += feature_toggle_enabled
            output = column_definitions.get(table_name)
        else:
            output = column_definitions.get(table_name)

        if not output:
            raise EvChartMissingOrMalformedHeadersError(
                message=f"Table name does not exist: {table_name}"
            )

    except (EvChartAuthorizationTokenInvalidError,
            EvChartMissingOrMalformedHeadersError
    ) as e:
        log_event.log_custom_exception(
            message=e.message,
            status_code=e.status_code,
            log_level=e.log_level
        )
        return_obj = e.get_error_obj()

    else:
        log_event.log_successful_request(
            message="Successfully retrieved Column Definitions",
            status_code=200
        )
        return_obj = {
            'statusCode' : 200,
            'headers': { "Access-Control-Allow-Origin": "*" },
            'body': json.dumps(output)
        }

    return return_obj

sr_draft_data = {}
sr_draft_data["headers"] = ["Module", "Reporting Year", "Type", "Direct Recipient", "Uploaded On", "Uploaded By", "Upload ID", "Actions"]
sr_draft_data["values"] = ["The module associated with the Draft Module Data. Additional details about each module can be found in the EV-ChART Data Input Guidance documentation.",
    "The reporting year associated with the Draft Module Data.",
    "The submission cadence (Annual, One-time, or Quarter 1-4) associated with the Draft Module Data.",
    "The Direct Recipient of federal funding for which the Draft Module Data was uploaded.",
    "The date on which the Draft Module Data was uploaded.",
    "The user that uploaded the Draft Module Data.",
    "An EV-ChART identifier that uniquely identifies the Draft Module Data.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']

dr_draft_data = {}
dr_draft_data["headers"] = ["Module", "Reporting Year", "Type", "Uploaded On", "Uploaded By", "Upload ID", "Actions"]
dr_draft_data["values"] = ["The module associated with the Draft Module Data. Additional details about each module can be found in the EV-ChART Data Input Guidance documentation.",
    "The reporting year associated with the Draft Module Data.",
    "The submission cadence (Annual, One-time, or Quarter 1-4) associated with the Draft Module Data.",
    "The date on which the Draft Module Data was uploaded.",
    "The user that uploaded the Draft Module Data.",
    "An EV-ChART identifier that uniquely identifies the Draft Module Data.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']

sr_admin_submitted_data = {}
sr_admin_submitted_data["headers"] = ["Module", "Reporting Year", "Type", "Direct Recipient", "Status", "Updated On", "Updated By", "Upload ID", "Actions"]
sr_admin_submitted_data["values"] = ["The module associated with the Submitted Module Data. Additional details about each module can be found in the EV-ChART Data Input Guidance documentation.",
    "The reporting year associated with the Submitted Module Data.",
    "The submission cadence (Annual, One-time, or Quarter 1-4) associated with the Submitted Module Data.",
    "The Direct Recipient of federal funding for which the Submitted Module Data was uploaded on behalf of.",
    "The Module Data's current status (pending approval, submitted, rejected) within the submission process. Modules that have the status of 'Pending approval' need to be approved by the Direct Recipient. Modules that have the status of 'Rejected' need to be resubmitted. Modules that are 'Submitted' have been approved by the Direct Recipient and are considered complete.",
    "The date on which the Module Data was last updated.",
    "The user who last updated the Module Data.",
    "An EV-ChART identifier that uniquely identifies the Submitted Module Data.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']

sr_viewer_submitted_data = {}
sr_viewer_submitted_data["headers"] = ["Module", "Reporting Year", "Type", "Direct Recipient", "Updated On", "Updated By", "Upload ID", "Actions"]
sr_viewer_submitted_data["values"] = ["The module associated with the Submitted Module Data. Additional details about each module can be found in the EV-ChART Data Input Guidance documentation.",
    "The reporting year associated with the Submitted Module Data.",
    "The submission cadence (Annual, One-time, or Quarter 1-4) associated with the Submitted Module Data.",
    "The Direct Recipient of federal funding for which the Submitted Module Data was uploaded on behalf of.",
    "The date on which the Module Data was last updated.",
    "The user who last updated the Module Data.",
    "An EV-ChART identifier that uniquely identifies the Submitted Module Data.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']

dr_admin_submitted_data = {}
dr_admin_submitted_data["headers"] = ["Module", "Reporting Year", "Type", "Subrecipient/Contractor", "Status", "Updated On", "Updated By", "Upload ID", "Actions"]
dr_admin_submitted_data["values"] = ["The module associated with the Submitted Module Data. Additional details about each module can be found in the EV-ChART Data Input Guidance documentation.",
    "The reporting year associated with the Submitted Module Data.",
    "The submission cadence (Annual, One-time, or Quarter 1-4) associated with the Submitted Module Data.",
    'The Subrecipient or Contractor for your organization that uploaded the Module Data. "N/A" is displayed if someone within your oganization Submitted this Module Data.',
    "The Module Data's current status (pending approval, submitted, rejected) within the submission process. Modules that have the status of 'Pending approval' need to be approved by the Direct Recipient. Modules that have the status of 'Rejected' need to be resubmitted. Modules that are 'Submitted' have been approved by the Direct Recipient and are considered complete.",
    "The date on which the Module Data was last updated.",
    "The user who last updated the Module Data.",
    "An EV-ChART identifier that uniquely identifies the Submitted Module Data.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']

dr_viewer_submitted_data = {}
dr_viewer_submitted_data["headers"] = ["Module", "Reporting Year", "Type", "Subrecipient/Contractor", "Updated On", "Updated By", "Upload ID", "Actions"]
dr_viewer_submitted_data["values"] = ["The module associated with the Submitted Module Data. Additional details about each module can be found in the EV-ChART Data Input Guidance documentation.",
    "The reporting year associated with the Submitted Module Data.",
    "The submission cadence (Annual, One-time, or Quarter 1-4) associated with the Submitted Module Data.",
    'The Subrecipient or Contractor for your organization that uploaded the Module Data. "N/A" is displayed if someone within your oganization Submitted this Module Data.',
    "The date on which the Module Data was last updated.",
    "The user who last updated the Module Data.",
    "An EV-ChART identifier that uniquely identifies the Submitted Module Data.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']

jo_submitted_data = {}
jo_submitted_data["headers"] = ["Module", "Reporting Year", "Type", "Direct Recipient", "Subrecipient/Contractor", "Updated On", "Upload ID", "Actions"]
jo_submitted_data["values"] = ["The module associated with the Submitted Module Data. Additional details about each module can be found in the EV-ChART Data Input Guidance documentation.",
    "The reporting year associated with the Submitted Module Data.",
    "The submission cadence (Annual, One-time, or Quarter 1-4) associated with the Submitted Module Data.",
    "The Direct Recipient of federal funding for which the Submitted Module Data was uploaded by or on behalf of.",
    'The Subrecipient or Contractor of the Direct Recipient that uploaded the Module Data. "N/A" is displayed if the Direct Recipient uploaded the Module Data.',
    "The date on which the Module Data was last updated.",
    "An EV-ChART identifier that uniquely identifies the Submitted Module Data.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']

station_direct_recipient = {}
station_direct_recipient["headers"] = ["Station Nickname", "Station ID", "Status", "Subrecipient/Contractor", "Actions", "Please Note"]
station_direct_recipient["values"] = ["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
    "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
    'Stations can have two statuses: "Pending Approval" and "Active". Stations with a “Pending Approval” status are waiting for your review. Stations with an "Active" status signifies the station has been approved/added and data for this station can now be uploaded successfully. Stations can be "Active" before their operational start date.',
    "The Subrecipient(s) that is (are) assigned and authorized to your station.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.',
    'The "Remove Station" action is only available to stations that do not have any data associated with the station. If you are looking to adjust station details, select "Edit Station" from the "Actions" dropdown.']

station_sub_recipient = {}
station_sub_recipient["headers"] = ["Station Nickname", "Station ID", "Status", "Direct Recipient", "Actions"]
station_sub_recipient["values"] = ["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
    "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
    'Stations can have two statuses: "Pending Approval" and "Active". Stations with a “Pending Approval” status are waiting for review by the direct recipient and no action is required. Stations with an "Active" status signifies the station has been added/approved by the direct recipient and data for this station can now be uploaded successfully. Stations can be "Active" before their operational start date.',
    "The Direct Recipient that authorized your organization to submit data on behalf of this station.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']

station_joet = {}
station_joet["headers"] = ["Station Nickname", "Station ID", "Direct Recipient"]
station_joet["values"] = ["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
    "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
    "The Direct Recipient of federal funding for which the station has been registered under."]

station_direct_recipient_fed_funded_FT_ON = {}
station_direct_recipient_fed_funded_FT_ON["headers"] = ["Station Nickname", "Station ID", "Status", "Subrecipient/Contractor", "Federally Funded", "Actions", "Please Note"]
station_direct_recipient_fed_funded_FT_ON["values"] = ["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
    "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
    'Stations can have two statuses: "Pending Approval" and "Active". Stations with a “Pending Approval” status are waiting for your review. Stations with an "Active" status signifies the station has been approved/added and data for this station can now be uploaded successfully. Stations can be "Active" before their operational start date.',
    "The Subrecipient(s) that is (are) assigned and authorized to your station.",
    "The acquisition, installation, network connection, operation, or maintenance of this charging station, uses funds made available under Title 23, U.S.C. for projects for the construction of publicly accessible EV chargers or any EV charging infrastructure project funded with Federal funds that is treated as a project on a Federal-aid highway. Note that this is a frontend-only field used to determine which subsequent fields and subsections are displayed.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.',
    'The "Remove Station" action is only available to stations that do not have any data associated with the station. If you are looking to adjust station details, select "Edit Station" from the "Actions" dropdown.']

station_sub_recipient_fed_funded_FT_ON = {}
station_sub_recipient_fed_funded_FT_ON["headers"] = ["Station Nickname", "Station ID", "Status", "Direct Recipient", "Federally Funded", "Actions"]
station_sub_recipient_fed_funded_FT_ON["values"] = ["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
    "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
    'Stations can have two statuses: "Pending Approval" and "Active". Stations with a “Pending Approval” status are waiting for review by the direct recipient and no action is required. Stations with an "Active" status signifies the station has been added/approved by the direct recipient and data for this station can now be uploaded successfully. Stations can be "Active" before their operational start date.',
    "The Direct Recipient that authorized your organization to submit data on behalf of this station.",
    "The acquisition, installation, network connection, operation, or maintenance of this charging station, uses funds made available under Title 23, U.S.C. for projects for the construction of publicly accessible EV chargers or any EV charging infrastructure project funded with Federal funds that is treated as a project on a Federal-aid highway. Note that this is a frontend-only field used to determine which subsequent fields and subsections are displayed.",
    'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']

station_joet_fed_funded_FT_ON = {}
station_joet_fed_funded_FT_ON["headers"] = ["Station Nickname", "Station ID", "Direct Recipient", "Federally Funded"]
station_joet_fed_funded_FT_ON["values"] = ["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
    "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
    "The Direct Recipient of federal funding for which the station has been registered under.",
    "The acquisition, installation, network connection, operation, or maintenance of this charging station, uses funds made available under Title 23, U.S.C. for projects for the construction of publicly accessible EV chargers or any EV charging infrastructure project funded with Federal funds that is treated as a project on a Federal-aid highway. Note that this is a frontend-only field used to determine which subsequent fields and subsections are displayed."]

submission_tracker = {}
submission_tracker["headers"] = ["Module(s) require attention/review", "Approved/submitted data for all modules", "Some modules approved/submitted", "No Modules approved/submitted", "No modules due yet", "Station not operational, no submissions required"]
submission_tracker["values"] = ["At least one module submission within the reporting period is either pending approval or is overdue.",
    "All required modules have data that has been approved/submitted for this reporting period.",
    "At least one - but not all - modules have data that has been approved/submitted for this reporting period.",
    "No modules have data that has been approved/submitted for this reporting period.",
    "This is an upcoming reporting period and there are no modules currently required to be approved/submitted at this time.",
    "No module submissions required - station was not operational during this reporting period"]

submission_status_sr = {}
submission_status_sr["headers"] = ["Uploading Draft", "Draft", "Pending Approval", "Approved", "Rejected", "Error"]
submission_status_sr["values"] = ['"Uploading Draft" is a temporary status to indicate that a draft is being uploaded to the system. No action is required.',
    '"Draft" module data has not yet been submitted. Users should review draft data, ensure data quality, and then submit the data for approval by the Direct Recipient.',
    'Modules labeled "Pending Approval" are waiting for review by the Direct Recipient. No action is required.',
    '"Approved" module data has been reviewed and submitted by the Direct Recipient. "Approved" is considered the desired final status of each module data.',
    '"Rejected" module data has been reviewed and rejected by the Direct Recipient. Review the Direct Recipient feedback, address issues raised, and ipload a new module data file.',
    'There are a number of reasons that modules could be labeled "Error". Review the Error Report to understand the root cause of the error. To view the Error Report, naviagte to the module data file with the "Error" status, select "Actions", and then select "Download Error Report".']

submission_status_dr = {}
submission_status_dr["headers"] = ["Uploading Draft", "Draft", "Pending Approval", "Submitted", "Approved", "Rejected", "Error"]
submission_status_dr["values"] = ['"Uploading Draft" is a temporary status to indicate that a draft is being uploaded to the system. No action is required.',
    '"Draft" module data has not yet been submitted. Users should review draft data, ensure data quality, and then submit the data for approval by the Direct Recipient.',
    'Modules labeled "Pending Approval" have been submitted by the Subrecipient/Contractor and require review by the Direct Recipient.',
    '"Submitted" module data has been submitted by the Direct Recipient. Both "Submitted" and "Approved" are considered the desired final status of each module data.',
    '"Approved" module data has been submitted by a Subrecipient/Contractor and reviewed by a Direct Recipient. Both "Submitted" and "Approved" are considered the desired final status of each module data.',
    '"Rejected" module data has been reviewed and rejected by the Direct Recipient. The Subrecipient/Contractor will be notified and must upload a new module data file.',
    'There are a number of reasons that modules could be labeled "Error". Review the Error Report to understand the root cause of the error. To view the Error Report, naviagte to the module data file with the "Error" status, select "Actions", and then select "Download Error Report".']

submission_status_jo = {}
submission_status_jo["headers"] = ["Submitted", "Approved"]
submission_status_jo["values"] = ['"Submitted" module data has been submitted by the Direct Recipient. Both "Submitted" and "Approved" are considered the desired final status of each module data.',
    '"Approved" module data has been submitted by a Subrecipient/Contractor and reviewed by a Direct Recipient. Both "Submitted" and "Approved" are considered the desired final status of each module data.']

dr_station_submission_details = {}
dr_station_submission_details["headers"] = ["Module", "Subrecipient/Contractor", "Status", "Updated On", "Upload ID" ]
dr_station_submission_details["values"] = ["The module associated with the Submitted Module Data. Additional details about each module can be found in the EV-ChART Data Input Guidance documentation.",
    'The Subrecipient or Contractor for your organization that uploaded the Module Data. "N/A" is displayed if someone within your oganization Submitted this Module Data.',
    "The Module Data's current status (pending approval, submitted, rejected) within the submission process. Modules that have the status of 'Pending approval' need to be approved by the Direct Recipient. Modules that have the status of 'Rejected' need to be resubmitted. Modules that are 'Submitted' have been approved by the Direct Recipient and are considered complete.",
    "The date on which the Module Data was last updated.",
    "An EV-ChART identifier that uniquely identifies the Submitted Module Data."]


column_definitions = {}
column_definitions["sr_draft_data"] = sr_draft_data
column_definitions["dr_draft_data"] = dr_draft_data
column_definitions["sr_admin_submitted_data"] = sr_admin_submitted_data
column_definitions["sr_viewer_submitted_data"] = sr_viewer_submitted_data
column_definitions["dr_admin_submitted_data"] = dr_admin_submitted_data
column_definitions["dr_viewer_submitted_data"] = dr_viewer_submitted_data
column_definitions["jo_submitted_data"] = jo_submitted_data
column_definitions["station_direct_recipient"] = station_direct_recipient
column_definitions["station_sub_recipient"] = station_sub_recipient
column_definitions["station_joet"] = station_joet
column_definitions["submission_tracker"] = submission_tracker
column_definitions["submission_status_sr"] = submission_status_sr
column_definitions["submission_status_dr"] = submission_status_dr
column_definitions["submission_status_jo"] = submission_status_jo
column_definitions["dr_station_submission_details"] = dr_station_submission_details
# after adding ft check for federally funded stations
column_definitions["station_direct_recipient_fed_funded_FT_ON"] = station_direct_recipient_fed_funded_FT_ON
column_definitions["station_sub_recipient_fed_funded_FT_ON"] = station_sub_recipient_fed_funded_FT_ON
column_definitions["station_joet_fed_funded_FT_ON"] = station_joet_fed_funded_FT_ON
