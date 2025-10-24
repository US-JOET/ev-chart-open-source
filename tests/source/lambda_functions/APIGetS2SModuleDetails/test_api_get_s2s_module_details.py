from unittest.mock import patch, MagicMock

import pytest
from APIGetS2SModuleDetails.index import (
    format_response_body,
    format_submission_status,
    validate_body,
)
from evchart_helper.custom_exceptions import EvChartAPIS2SError


def get_cursor():
    return MagicMock()


@patch("APIGetS2SModuleDetails.index.is_valid_upload_id", return_value=True)
@patch("APIGetS2SModuleDetails.index.is_org_authorized_to_view_data", return_value=True)
def test_validate_body_given_valid_body_return_empty_string(
    _mock_is_valid_upload_id, _mock_is_org_authorized_to_view_data
):
    body = {"upload_id": "12123141234-213421354-12345321-5341252"}
    org_id = "12344235342-243242234-234234234"
    recipient_type = "sub-recipient"
    cursor = get_cursor()
    errors = validate_body(body, org_id, recipient_type, cursor)

    assert len(errors) == 0


def test_validate_body_given_invalid_body_return_error_list():
    body = {"uploadid": "12123141234-213421354-12345321-5341252"}
    org_id = "12344235342-243242234-234234234"
    recipient_type = "sub-recipient"
    cursor = get_cursor()
    errors = validate_body(body, org_id, recipient_type, cursor)

    assert len(errors) == 1


def test_validate_body_given_empty_body_return_error_list():
    body = {}
    org_id = "12344235342-243242234-234234234"
    recipient_type = "sub-recipient"
    cursor = get_cursor()
    errors = validate_body(body, org_id, recipient_type, cursor)

    assert len(errors) == 1


@patch("APIGetS2SModuleDetails.index.is_valid_upload_id", return_value=False)
@patch("APIGetS2SModuleDetails.index.is_org_authorized_to_view_data", side_effect=TypeError)
def test_validate_body_given_invalid_upload_id_return_error_list(
    _mock_is_valid_upload_id, _mock_is_org_authorized_to_view_data
):
    body = {"upload_id": "invalid"}
    org_id = "12344235342-243242234-234234234"
    recipient_type = "sub-recipient"
    cursor = get_cursor()
    errors = validate_body(body, org_id, recipient_type, cursor)

    assert len(errors) == 1


@patch("APIGetS2SModuleDetails.index.is_valid_upload_id", return_value=True)
@patch("APIGetS2SModuleDetails.index.is_org_authorized_to_view_data", return_value=False)
def test_validate_body_given_org_not_authorized_return_error_list(
    _mock_is_valid_upload_id, _mock_is_org_authorized_to_view_data
):
    body = {"upload_id": "12123141234-213421354-12345321-5341252"}
    org_id = "unauthorized"
    recipient_type = "sub-recipient"
    cursor = get_cursor()
    errors = validate_body(body, org_id, recipient_type, cursor)

    assert len(errors) == 1


def get_formated_module_details():
    return [
        {
            "comments": "",
            "module_id": "2",
            "org_id": "a3375aeb-6686-4c5a-82a6-0ecbf378a5d7",
            "parent_org": "7af4eee9-0e1f-4f27-90b6-89ddee67658c",
            "quarter": "1",
            "submission_status": "Pending",
            "upload_id": "b48e7357-12f6-41e3-80f2-8d08167b8f2d",
            "upload_friendly_id": 1141,
            "updated_by": "Subrecipient Account",
            "updated_on": "12/09/24 7:08 PM EST",
            "year": "2024",
            "uploaded_on": "12/09/24 7:08 PM EST",
            "direct_recipient": "Sarah DOT",
            "module_name": "Module 2: Charging Sessions",
            "module_frequency": "Quarter 1 (Jan-Mar)",
        }
    ]


expected_keys = [
    "direct_recipient",
    "upload_id",
    "module_id",
    "module_name",
    "module_frequency",
    "year",
    "quarter",
    "submission_status",
    "uploaded_on",
]
expected_removed_keys = [
    "updated_on",
    "updated_by",
    "upload_friendly_id",
    "parent_org",
    "org_id",
]


def test_format_response_body_given_valid_input():
    module_details = get_formated_module_details()
    result = format_response_body(module_details)

    keys = result.keys()
    assert isinstance(result, dict)
    for key in expected_keys:
        assert key in keys
    for key in expected_removed_keys:
        assert not key in keys
    assert "comments" not in keys


def test_format_response_body_given_valid_input_with_comments():
    module_details = get_formated_module_details()
    module_details[0]["comments"] = "test"
    result = format_response_body(module_details)

    keys = result.keys()
    assert isinstance(result, dict)
    for key in expected_keys:
        assert key in keys
    for key in expected_removed_keys:
        assert not key in keys
    assert "comments" in keys


def test_format_response_body_given_missing_key_raise_error():
    module_details = get_formated_module_details()
    removed_key = "upload_id"
    del module_details[0][removed_key]
    with pytest.raises(EvChartAPIS2SError) as e:
        format_response_body(module_details)
        assert removed_key in e.message


@pytest.mark.parametrize(
    "input_status, expected_status",
    [
        ("Processing", "Upload Draft"),
        ("Draft", "Draft"),
        ("Submitted", "Submitted"),
        ("Pending", "Pending Approval"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Error", "Error"),
        ("Duplicate", "Duplicate"),
        ("Archived", "Archived"),
        ("processing", "Upload Draft"),
        ("draft", "Draft"),
        ("submitted", "Submitted"),
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("error", "Error"),
        ("duplicate", "Duplicate"),
        ("archived", "Archived"),
    ],
)
def test_format_submission_status_given_status_return_user_version(input_status, expected_status):
    result = format_submission_status(input_status)

    assert expected_status == result
