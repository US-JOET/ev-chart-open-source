from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from evchart_helper.api_helper import format_users, get_org_info_dynamo, get_org_users
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseDynamoQueryError,
    EvChartJsonOutputError,
    EvChartUnknownException,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.s2s_helper import get_expiring_api_keys

station_ports = ModuleDataTables["StationPorts"].value
station_registrations = ModuleDataTables["RegisteredStations"].value
import_metadata = ModuleDataTables["Metadata"].value
station_authorizations = ModuleDataTables["StationAuthorizations"].value

FIRST_EMAIL_DAYS_UNTIL_EXPIRED = 7
SECOND_EMAIL_DAYS_UNTIL_EXPIRED = 1

def handler(event, _context):
    log = LogEvent(event, api="ScheduledSubmissionDeadlineEmail", action_type="Read")
    # TODO prevent sending on weekend and adjust on fridays to send friday, sat, and sun emails.
    # TODO dont send email if newer key exists
    # If it's not a valid day, stop execution
    # if not should_send_email():
    try:
        # get api_key info for first emails
        first_api_key_list = get_expiring_api_keys(FIRST_EMAIL_DAYS_UNTIL_EXPIRED)
        # get api_key info for second emails
        second_api_key_list = get_expiring_api_keys(SECOND_EMAIL_DAYS_UNTIL_EXPIRED)

        # build first email
        if first_api_key_list:
            for api_key_info in first_api_key_list:
                org_id = api_key_info["org_id"]
                send_email_to_org(org_id, FIRST_EMAIL_DAYS_UNTIL_EXPIRED)

        # build second email
        if second_api_key_list:
            for api_key_info in second_api_key_list:
                org_id = api_key_info["org_id"]
                send_email_to_org(org_id, SECOND_EMAIL_DAYS_UNTIL_EXPIRED)

    except (
        EvChartDatabaseAuroraQueryError,
        EvChartDatabaseDynamoQueryError,
    ) as e:
        log.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
        )
    except Exception as e:
        raise EvChartUnknownException(
            message=("Unknown Exception in ScheduleSubmissionDeadlineEmail: " f"{repr(e)}")
        ) from e

    return None

def send_email_to_org(org_id, days_until_expired):
    try:
        email_values = {}
        email_values["email_type"] = Email_Template.API_KEY_EXPIRING
        dr_org_name = get_org_info_dynamo(org_id).get("name")
        email_values["dr_org_name"] = dr_org_name
        email_values["days_until_expired"] = days_until_expired

        org_users = get_org_users(org_id)
        formatted_users = format_users(org_users)
        for user in formatted_users:
            if user.get("status") == "Active" and user.get("role") == "Administrator":
                email_values["first_name"] = user.get("first_name").strip()
                email_values["email"] = user.get("email").strip()
                trigger_email(email_values)
    except EvChartJsonOutputError as e:
        raise EvChartJsonOutputError(
            message=f"Error formatting fields for email handler: {repr(e)}"
        ) from e
    except EvChartDatabaseDynamoQueryError as e:
        raise EvChartJsonOutputError(
            message=f"Error with dynamo query in send_org_emails():  {e}"
        ) from e
