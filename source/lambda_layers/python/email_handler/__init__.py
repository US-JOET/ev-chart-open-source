"""
email_handler

A helper module that will handle defining and processing email templates and ultimately send to the
relevant SQS queue.
"""

import datetime
import re  # Regular expressions for email validation
import os
from dateutil import tz
import pandas as pd
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

# import sqs_extended_client # For sending larger payload (formatted emails)
from email_handler.email_enums import Email_Template
from email_handler.html_templates import (
    api_key_expiring,
    data_processing_fail,
    data_processing_success,
    new_user_html,
    new_org_html,
    station_authorizes_subrecipient,
    direct_recip_approval,
    subrecip_submit_approve,
    subrecip_submit_deny,
    file_upload_fail,
    insert_rds_fail,
    upload_cleanup,
    dr_rejects_sr_station,
    dr_review_sr_station,
    dr_approve_sr_station,
    dr_past_due_submission,
    api_key_expiring
)
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_logging import LogEvent
from evchart_helper.custom_exceptions import (
    EvChartEmailError,
    EvChartMissingOrMalformedBodyError,
    EvChartJsonOutputError,
)

sqs = boto3_manager.client("sqs")
sts = boto3_manager.client("sts")


def trigger_email(email_params):
    """
    Sends message to SQS queue after validating email address,
    formatting email params, and formatting email templates.
    No returned object. Parameter email_params expects dictionary
    with following fields: email, first_name, last_name.
    """
    try:
        feature_toggle_service = FeatureToggleService()
        log = LogEvent({}, api="email_handler", action_type="READ")
        if feature_toggle_service.get_feature_toggle_by_enum(Feature.SEND_EMAIL, log) == "True":
            email_addr = email_params.get("email")
            if not email_addr:
                raise EvChartMissingOrMalformedBodyError(log_obj=log, message="Missing Email Addr")
            # Remove whitespace and set to lower.
            email_addr = email_addr.strip().lower()
            # Basic email validation
            validate_email_address_format(email_addr, log)

            # Prepare message for SQS queue
            receiver_email = email_params["email"]
            plain_text = "HTML Only for now"
            formatted_params = format_email_params(email_params)
            email_templates = format_email_templates(formatted_params)

            emailPayload = {}
            emailPayload["receiver_email"] = receiver_email
            emailPayload["email_subject"] = email_templates["email_subject"]
            emailPayload["html_body"] = email_templates["html_text"]
            emailPayload["plain_body"] = plain_text

            # Send message to SQS queue
            send_to_sqs(emailPayload)
    except EvChartMissingOrMalformedBodyError as exc:
        raise EvChartMissingOrMalformedBodyError() from exc
    except Exception as e:
        raise EvChartEmailError(
            log_obj=None, message=f"Error thrown in email_handler, trigger_email(): {repr(e)}"
        ) from e


def validate_email_address_format(email_address, log):
    """
    Convenience function to verify given email passes regex formatting,
    throws error if regex is not a full match.
    """
    email_regex = get_email_regex()
    if not email_address or not re.fullmatch(email_regex, email_address):
        raise EvChartMissingOrMalformedBodyError(
            log_obj=log, message=f"Invalid Email Addr: {email_address}"
        )


def get_email_regex():
    return r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"


def format_email_params(email_params):
    """
    Convenience function to set first and last names, as well
    as formatting any datetimes. Returns updated dictionary with values.
    """
    try:
        for key in list(email_params.keys()):
            if "first_name" in key.lower() or "last_name" in key.lower():
                email_params[key] = email_params[key].title()

        format_utc_to_est_datetimes(email_params)
        return email_params
    except Exception as e:
        raise EvChartJsonOutputError(
            log_obj=None, message=f"Error formatting email params: {repr(e)}"
        )


def format_utc_to_est_datetimes(email_params):
    """
    Convenience function that formats all datetime objecst
    in parameter email_params to EST timezone. Returns updated
    dictionary with formatted values.
    """
    # formatted_email_params = {}
    for key, value in email_params.items():
        if isinstance(value, datetime.datetime):
            try:
                eastern = tz.gettz("US/Eastern")
                date_format = "%m/%d/%y %I:%M %p %Z"

                correct_format = pd.to_datetime(value, utc=True).tz_convert(eastern)
                added_zone = correct_format.strftime(date_format).replace(
                    r"\b0(\d:\d{2} [AP]M)", r"\1"
                )

                email_params[key] = added_zone
            except Exception as e:
                raise EvChartJsonOutputError(
                    log_obj=None, message=f"Error formatting timezone for: {e}"
                ) from e
    return email_params


def format_email_templates(email_params):
    """
    Convenience function that takes email parameters and replaces their corresponding
    values in HTML templates, based on the email type. Returns dictionary with
    html_text (formatted email) and email_subject as keys.
    """
    try:
        email_templates = {}
        html_text = ""
        email_subject = ""
        email_type = email_params["email_type"]

        match email_type:
            case Email_Template.NEW_USER:
                html_text = str(new_user_html.new_user_html)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    org_name=email_params["org_name"],
                    role=email_params["role"],
                )
                email_subject = email_type.value["email_subject"]
            case Email_Template.NEW_ORG:
                org_type_description = "<strong>Subrecipient/contractor</strong> &ndash; An entity, usually but not limited to non-federal entities, that receives a subaward from a pass-through entity to carry out part of a federal award; but does not include an individual that is a beneficiary of such award. A subrecipient may also be a recipient of other federal awards directly from a federal awarding agency. See definition for Subaward in <a href='https://www.ecfr.gov/on/2023-03-23/title-2/subtitle-A/chapter-II/part-200/subpart-A/subject-group-ECFR2a6a0087862fd2c/section-200.1'>2 CFR 200.1</a>."
                dr_admin_blurb = ""
                if email_params["new_org_type"] == "direct-recipient":
                    org_type_description = "<strong>Direct recipient</strong> &ndash; An entity, usually but not limited to non-federal entities, that receives a federal award directly from a federal awarding agency. The term direct recipient does not include subrecipients or individuals that are beneficiaries of the award."
                    dr_admin_blurb = (
                        ", approve or reject data uploaded by subrecipients/contractors,"
                    )

                html_text = str(new_org_html.new_org_html)
                html_text = html_text.format(
                    creator_org_name=(
                        "The Joint Office of Energy & Transportation"
                        if email_params["is_joet"]
                        else email_params["creator_org_name"]
                    ),
                    dr_admin_blurb=f"{dr_admin_blurb} ",
                    email=email_params["email"],
                    first_name=email_params["first_name"],
                    last_name=email_params["last_name"],
                    new_org_name=email_params["new_org_name"],
                    org_type_description=org_type_description,
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    new_org_name=email_params["new_org_name"],
                )
            case Email_Template.DR_APPROVAL:
                html_text = str(direct_recip_approval.direct_recip_approval)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                    reporting_year=email_params["reporting_year"],
                    sr_org_name=email_params["sr_org_name"],
                    dr_org_name=email_params["dr_org_name"],
                    reporting_period=email_params["reporting_period"],
                    last_updated_on=email_params["last_updated_on"],
                    last_updated_by=email_params["last_updated_by"],
                    upload_id=email_params["upload_id"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    module_number=email_params["module_number"],
                    sr_org_name=email_params["sr_org_name"],
                )
            case Email_Template.SR_APPROVED:
                html_text = str(subrecip_submit_approve.subrecip_submit_approve)
                html_text = html_text.format(
                    sr_first_name=email_params["sr_first_name"],
                    dr_name=email_params["dr_name"],
                    sr_org_name=email_params["sr_org_name"],
                    dr_org_name=email_params["dr_org_name"],
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                    module_last_updated_by=email_params["module_last_updated_by"],
                    module_last_updated_on=email_params["module_last_updated_on"],
                    reporting_year=email_params["reporting_year"],
                    reporting_period=email_params["reporting_period"],
                    decision_date=email_params["decision_date"],
                    feedback=email_params["feedback"],
                    upload_id=email_params["upload_id"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    module_number=email_params["module_number"],
                    dr_org_name=email_params["dr_org_name"],
                )
            case Email_Template.SR_REJECTED:
                html_text = str(subrecip_submit_deny.subrecip_submit_deny)
                html_text = html_text.format(
                    sr_first_name=email_params["sr_first_name"],
                    dr_name=email_params["dr_name"],
                    sr_org_name=email_params["sr_org_name"],
                    dr_org_name=email_params["dr_org_name"],
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                    module_last_updated_by=email_params["module_last_updated_by"],
                    module_last_updated_on=email_params["module_last_updated_on"],
                    reporting_year=email_params["reporting_year"],
                    reporting_period=email_params["reporting_period"],
                    decision_date=email_params["decision_date"],
                    feedback=email_params["feedback"],
                    upload_id=email_params["upload_id"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    module_number=email_params["module_number"],
                    dr_org_name=email_params["dr_org_name"],
                )
            case Email_Template.STATION_AUTHORIZES_SR:
                html_text = str(station_authorizes_subrecipient.station_authorizes_subrecipient)
                html_text = html_text.format(
                    sr_first_name=email_params["sr_first_name"],
                    sr_org_name=email_params["sr_org_name"],
                    dr_org_name=email_params["dr_org_name"],
                    station_id=email_params["station_id"],
                    station_nickname=email_params["station_nickname"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    sr_org_name=email_params["sr_org_name"],
                    station_id=email_params["station_id"],
                    station_nickname=email_params["station_nickname"],
                    dr_org_name=email_params["dr_org_name"],
                )
            case Email_Template.DATA_PROCESSING_FAIL:
                html_text = str(data_processing_fail.data_processing_fail)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                    reporting_year=email_params["reporting_year"],
                    dr_name=email_params["dr_name"],
                    sr_name=email_params["sr_name"],
                    updated_on=email_params["updated_on"],
                    updated_by=email_params["updated_by"],
                    upload_id=email_params["upload_id"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                    first_name=email_params["first_name"],
                )
            case Email_Template.DATA_PROCESSING_SUCCESS:
                html_text = str(data_processing_success.data_processing_success)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                    reporting_year=email_params["reporting_year"],
                    dr_name=email_params["dr_name"],
                    sr_name=email_params["sr_name"],
                    updated_on=email_params["updated_on"],
                    updated_by=email_params["updated_by"],
                    upload_id=email_params["upload_id"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                )
            case Email_Template.S2S_PROCESSING_SUCCESS:
                html_text = str(data_processing_success.s2s_processing_success)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                    reporting_year=email_params["reporting_year"],
                    dr_name=email_params["dr_name"],
                    sr_name=email_params["sr_name"],
                    updated_on=email_params["updated_on"],
                    updated_by=email_params["updated_by"],
                    upload_id=email_params["upload_id"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                )
            case Email_Template.FILE_UPLOAD_FAIL:
                html_text = str(file_upload_fail.file_upload_fail)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                    reporting_year=email_params["reporting_year"],
                    dr_name=email_params["dr_name"],
                    sr_name=email_params["sr_name"],
                    updated_on=email_params["updated_on"],
                    updated_by=email_params["updated_by"],
                    upload_id=email_params["upload_id"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                )
            case Email_Template.INSERT_RDS_FAIL:
                html_text = str(insert_rds_fail.insert_rds_fail)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                    reporting_year=email_params["reporting_year"],
                    dr_name=email_params["dr_name"],
                    sr_name=email_params["sr_name"],
                    updated_on=email_params["updated_on"],
                    updated_by=email_params["updated_by"],
                    upload_id=email_params["upload_id"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    module_number=email_params["module_number"],
                    module_name=email_params["module_name"],
                )
            case Email_Template.UPLOAD_FAILED:
                html_text = str(upload_cleanup.upload_cleanup)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    combined_table=email_params["table"],
                )
                email_subject = email_type.value["email_subject"]
            case Email_Template.DR_REJECTS_SR_STATION:
                # Send SR who submitted?
                fed_port_table = ""
                for port in email_params["ports_fed"]:
                    fed_port_table = f"""{fed_port_table}
                        <tr>
                            <td>Federally Funded Port ID (Port Type)</td>
                            <td><strong>{port["id"]} ({port["type"]})</strong></td>
                        </tr>
                    """

                html_text = str(dr_rejects_sr_station.dr_rejects_sr_station)
                html_text = html_text.format(
                    sr_org_name=email_params["sr_org_name"],
                    dr_org_name=email_params["dr_org_name"],
                    first_name=email_params["first_name"],
                    station_nickname=email_params["station_nickname"],
                    station_id=email_params["station_id"],
                    updated_on=email_params["updated_on"],
                    updated_by=email_params["updated_by"],
                    feedback=email_params["feedback"],
                    station_address=email_params["station_address"],
                    station_city=email_params["station_city"],
                    station_state=email_params["station_state"],
                    station_zip=email_params["station_zip"],
                    station_zip_extended=email_params["station_zip_extended"],
                    station_lat=email_params["station_lat"],
                    station_long=email_params["station_long"],
                    station_np=email_params["station_np"],
                    station_project_type=email_params["station_project_type"],
                    station_operational_date=email_params["station_operational_date"],
                    station_funding_type=email_params["station_funding_type"],
                    station_afc="Yes" if email_params["station_afc"] else "No",
                    ports_num_fed=email_params["ports_num_fed"],
                    ports_num_non_fed=email_params["ports_num_non_fed"],
                    is_federally_funded=email_params["station_is_federally_funded"],
                    fed_port_table=fed_port_table,
                    funding_status_section=dr_rejects_sr_station.get_funding_status_section(
                        email_params["station_is_federally_funded"],
                        email_params["station_funding_type"],
                        email_params["station_project_type"],
                    ),
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    dr_org_name=email_params["dr_org_name"],
                )
            case Email_Template.DR_REVIEW_SR_STATION:
                html_text = str(dr_review_sr_station.dr_review_sr_station)
                html_text = html_text.format(
                    sr_org_name=email_params["sr_org_name"],
                    dr_org_name=email_params["dr_org_name"],
                    first_name=email_params["first_name"],
                    station_nickname=email_params["station_nickname"],
                    station_id=email_params["station_id"],
                    station_address=email_params["station_address"],
                    station_city=email_params["station_city"],
                    station_state=email_params["station_state"],
                    station_zip=email_params["station_zip"],
                    station_zip_extended=email_params["station_zip_extended"],
                    station_np=email_params["station_np"],
                    station_funding_type=email_params["station_funding_type"],
                    station_afc="Yes" if email_params["station_afc"] else "No",
                    ports_num_fed=email_params["ports_num_fed"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    dr_org_name=email_params["dr_org_name"],
                    sr_org_name=email_params["sr_org_name"],
                )
            case Email_Template.DR_APPROVE_SR_STATION:
                subject_station_nickname = (
                    email_params.get("subject_station_nickname") or email_params["station_nickname"]
                )

                html_text = str(dr_approve_sr_station.dr_approve_sr_station)
                html_text = html_text.format(
                    sr_org_name=email_params["sr_org_name"],
                    dr_org_name=email_params["dr_org_name"],
                    first_name=email_params["first_name"],
                    station_nickname=email_params["station_nickname"],
                    station_id=email_params["station_id"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    dr_org_name=email_params["dr_org_name"],
                    sr_org_name=email_params["sr_org_name"],
                    subject_station_nickname=subject_station_nickname,
                )
            case Email_Template.DR_PAST_DUE_SUBMISSION:
                html_text = str(dr_past_due_submission.dr_past_due_submission)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    dr_org_name=email_params["dr_org_name"],
                    reporting_period=email_params["reporting_period"],
                    year=email_params["year"],
                    station_list=email_params["station_list"],
                )
                email_subject = email_type.value["email_subject"]
                email_subject = email_subject.format(
                    reporting_period=email_params["reporting_period"]
                )
            case Email_Template.API_KEY_EXPIRING:
                html_text = str(api_key_expiring.api_key_expiring)
                html_text = html_text.format(
                    first_name=email_params["first_name"],
                    dr_org_name=email_params["dr_org_name"],
                    days_until_expired=email_params["days_until_expired"]
                )
                email_subject = email_subject.format(
                    dr_org_name=email_params["dr_org_name"]
                )
            case _:
                email_subject = ""

        email_templates["html_text"] = html_text
        email_templates["email_subject"] = email_subject

        return email_templates
    except Exception as e:
        raise EvChartJsonOutputError(
            log_obj=None, message=f"Error formatting email templates: {repr(e)}"
        )


def send_to_sqs(email):
    """
    Convenience function to send email templates to SQS queue, based on environment.
    Sends email or errors out.
    """
    try:
        account_id = sts.get_caller_identity()["Account"]
        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment = f"_{sub_environment}" if sub_environment else ""
        queue_url = "https://sqs.us-east-1.amazonaws.com/{account_id}/ev-chart-outbound{subenv}"
        queue_url = queue_url.format(account_id=account_id, subenv=sub_environment)
        sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=email["html_body"],
            MessageAttributes={
                "receiver_email": {
                    "StringValue": email["receiver_email"],
                    "DataType": "String",
                },
                "email_subject": {
                    "StringValue": email["email_subject"],
                    "DataType": "String",
                },
            },
        )
    except Exception as e:
        raise EvChartEmailError(log_obj=None, message=f"Error thrown in send_to_sqs: {repr(e)}")
