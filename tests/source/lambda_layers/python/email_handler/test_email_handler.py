import datetime
from unittest.mock import patch, MagicMock

from email_handler import (
    trigger_email,
    format_email_templates,
    format_email_params,
    format_utc_to_est_datetimes,
)
from email_handler.email_enums import Email_Template
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import (
    EvChartMissingOrMalformedBodyError,
    EvChartJsonOutputError,
)
import known_good_emails

import boto3
from moto import mock_aws
import pytest

log_event = MagicMock()


@pytest.fixture(name="_ssm_base")
def fixture_ssm_base():
    with mock_aws():
        ssm = boto3.client("ssm")
        ssm.put_parameter(
            Name="/ev-chart/some_var", Value="true", Type="String"
        )
        yield ssm


@pytest.fixture(name="_ssm_add_true")
def fixture_ssm_add_true(_ssm_base):
    _ssm_base.put_parameter(
        Name="/ev-chart/features/send-email", Value="True", Type="String"
    )
    yield _ssm_base


@pytest.fixture(name="mock_boto3_manager")
def fixture_mock_boto3_manager(_ssm_add_true):
    with patch.object(
        Boto3Manager, "client", return_value=_ssm_add_true
    ) as mock_client:
        yield mock_client


def test_trigger_email_invalid_address(mock_boto3_manager):
    new_dict = {
        "email_type": Email_Template.NEW_USER,
        "email": "address@invalid",
        "first_name": "Test",
        "org_name": "Custom",
        "role": "Admin",
    }
    with pytest.raises(EvChartMissingOrMalformedBodyError):
        trigger_email(new_dict)

    assert mock_boto3_manager.called


@patch("email_handler.send_to_sqs")
def test_trigger_email_valid_address(mock_send_to_sqs, mock_boto3_manager):
    new_dict = {
        "email_type": Email_Template.NEW_USER,
        "email": "address@valid.com",
        "first_name": "Test",
        "org_name": "Custom",
        "role": "Admin",
    }
    mock_send_to_sqs.return_value = None
    trigger_email(new_dict)
    assert mock_send_to_sqs.call_count == 1
    assert mock_boto3_manager.called


def test_format_new_user_email():
    email_params = {
        "email_type": Email_Template.NEW_USER,
        "first_name": "Hayley",
        "org_name": "Pennsylvania DOT",
        "role": "Administrator",
    }
    formatted_email = format_email_templates(email_params)["html_text"]
    assert formatted_email == known_good_emails.new_user_html


def test_format_email_params_first_name_fail():
    email_params = {
        "email_type": Email_Template.NEW_USER,
        "first_name": "hayley",
        "org_name": "Pennsylvania DOT",
        "role": "Administrator",
    }
    formatted_email = format_email_templates(email_params)["html_text"]
    assert formatted_email != known_good_emails.new_user_html


def test_format_email_params_first_name_pass():
    email_params = {
        "email_type": Email_Template.NEW_USER,
        "first_name": "hayley",
        "org_name": "Pennsylvania DOT",
        "role": "Administrator",
    }
    email_params = format_email_params(email_params)
    formatted_email = format_email_templates(email_params)["html_text"]
    assert formatted_email == known_good_emails.new_user_html


def test_format_subrecip_approval_email():
    email_params = {
        "email_type": Email_Template.SR_APPROVED,
        "sr_first_name": "Jay",
        "reporting_year": "2024",
        "reporting_period": "One-Time",
        "module_number": "6",
        "module_name": "Station Operator Identity",
        "dr_org_name": "Pennsylvania DOT",
        "decision_date": "2024-06-04 8:18 PM EDT",
        "dr_name": "Ken MacFarlane",
        "feedback": "Looks great!",
        "sr_org_name": "Chargepoint USA",
        "module_last_updated_on": "2024-06-04 8:18 PM EDT",
        "module_last_updated_by": "hayley.gray@ee.doe.gov",
        "upload_id": "b61661e4-b60c-433a-9c77-95f78716f8af",
    }
    formatted_email = format_email_templates(email_params)["html_text"]
    assert formatted_email == known_good_emails.subrecip_submit_approve


def test_format_subrecip_deny_email():
    email_params = {
        "email_type": Email_Template.SR_REJECTED,
        "sr_first_name": "Jay",
        "reporting_year": "2024",
        "reporting_period": "One-Time",
        "module_number": "6",
        "module_name": "Station Operator Identity",
        "dr_org_name": "Pennsylvania DOT",
        "decision_date": "2024-06-04 8:18 PM EDT",
        "dr_name": "Ken MacFarlane",
        "feedback": "Please fix!",
        "sr_org_name": "Chargepoint USA",
        "module_last_updated_on": "2024-06-04 8:18 PM EDT",
        "module_last_updated_by": "hayley.gray@ee.doe.gov",
        "upload_id": "b61661e4-b60c-433a-9c77-95f78716f8af",
    }
    formatted_email = format_email_templates(email_params)["html_text"]
    assert formatted_email == known_good_emails.subrecip_submit_deny


def test_trigger_invalid_evchart_email_handler_error():
    with pytest.raises(Exception):
        trigger_email({})


def test_trigger_invalid_evchart_json_output_error():
    format_email_templates.side_effect = EvChartJsonOutputError

    with pytest.raises(Exception):
        trigger_email({})


def test_format_email_templates():
    email_params = {
        "email_type": Email_Template.NEW_USER,
        "email": " hayley.gray+space@ee.doe.gov ",
        "first_name": "hayley space",
        "org_name": "Pennsylvania DOT",
        "role": "Administrator",
    }

    formatted_email = format_email_templates(email_params)
    assert formatted_email


def test_format_utc_to_est_datetimes():
    email_params = {
        "email_type": Email_Template.SR_REJECTED,
        "module_last_updated_on": datetime.datetime(2024, 10, 15, 17, 6, 39),
    }

    res = format_utc_to_est_datetimes(email_params)
    assert res["module_last_updated_on"] == "10/15/24 01:06 PM EDT"
