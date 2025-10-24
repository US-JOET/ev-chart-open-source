from enum import Enum

class Email_Template(Enum):
    NEW_USER = {
        "email_subject": "Welcome - You have been added as a user in EV-ChART",
    }
    NEW_ORG = {
        "email_subject": "Welcome - {new_org_name} has been added as an organization in EV-ChART",
    }
    DR_APPROVAL = {
        "email_subject": "Action Required - EV-ChART Module {module_number} Submission from {sr_org_name} is Pending Review"
    }
    SR_APPROVED = {
        "email_subject": "EV-ChART Module {module_number} Submission Has Been Approved by {dr_org_name}"
    }
    SR_REJECTED = {
        "email_subject": "Action Required - EV-ChART Module {module_number} Submission Has Been Rejected by {dr_org_name} "
    }
    STATION_AUTHORIZES_SR = {
        "email_subject": "{sr_org_name} Has Been Authorized to Submit Data in EV-ChART on Behalf of {dr_org_name} - Station {station_id} "
    }
    DATA_PROCESSING_FAIL = {
        "email_subject": "Action Required - Module {module_number} {module_name} Failed Data Processing"
    }
    DATA_PROCESSING_SUCCESS = {
        "email_subject": "Module {module_number} ({module_name}) Successfully Uploaded to EV-ChART - Login to Complete Submission"
    }
    S2S_PROCESSING_SUCCESS = {
        "email_subject": "Module {module_number} ({module_name}) Successfully Uploaded to EV-ChART"
    }
    FILE_UPLOAD_FAIL = {
        "email_subject": "Action Required - Module {module_number} ({module_name}) Failed To Upload"
    }
    INSERT_RDS_FAIL = {
        "email_subject": "Action Required - Module {module_number} ({module_name}) Failed Inserting into Database"
    }
    UPLOAD_FAILED = {
        "email_subject": "EV-ChART Upload Contains No Data and Will Be Deleted"
    }
    DR_REJECTS_SR_STATION = {
        "email_subject": "Action Required – A Station You Added in EV-ChART was Rejected by {dr_org_name}"
    }
    DR_REVIEW_SR_STATION = {
        "email_subject": "Action Required - EV-ChART Station Added by {sr_org_name} for {dr_org_name} is Pending"
    }
    DR_APPROVE_SR_STATION = {
        "email_subject": "{dr_org_name} Authorized {sr_org_name} to Submit Data in EV-ChART on their Behalf for Station {subject_station_nickname}"
    }
    DR_PAST_DUE_SUBMISSION = {
        "email_subject": "EV-ChART Overdue Data for {reporting_period}"
    }
    API_KEY_EXPIRING = {
        "email_subject": "{dr_org_name} API Key is about to expire"
    }