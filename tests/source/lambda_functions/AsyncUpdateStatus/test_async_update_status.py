import json
from pathlib import Path
from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest

from AsyncUpdateStatus.index import (
    data_uploaded,
    insert_into_error_table,
    send_awaiting_review_email,
    send_email,
    handler,
    biz_magic_validation
)
from email_handler.email_enums import Email_Template
from feature_toggle.feature_enums import Feature


# pylint: disable=invalid-name
upload_key = "upload/Joint Office/852ade96-4075-4766-9b97-5e9379b31ab0.csv"
body = {
        "key": upload_key,
        "bucket": "ev-chart-artifact-data-unit-test",
        "recipient_type": "test"
    }


def get_org_name_from_path(key):
    return Path(key).parent.name


def get_parent_org_name_from_path(key):
    parent_org = Path(key).parent.parent.name
    if parent_org.lower() == "uploads":
        return None
    return parent_org


def generate_tuple(s2s):
    message_attributes = {
        "data-uploaded": {
            "stringValue": "passed",
            "stringListValues": [],
            "binaryListValues": [],
            "dataType": "String",
        },
        "is-s2s": {
            "stringValue": f"{s2s}",
            "stringListValues": [],
            "binaryListValues": [],
            "dataType": "String",
        }
    }
    message = body
    key = message["key"]
    return_obj = namedtuple(
        typename="Desc",
        field_names=[
            "message",
            "message_attribute",
            "bucket",
            "key",
            "upload_id",
            "org_name",
            "parent_org",
            "recipient_type"
        ]
    )
    return return_obj(
            message,
            message_attributes,
            message["bucket"],
            key,
            Path(key).stem,
            get_org_name_from_path(key),
            get_parent_org_name_from_path(key),
            message["recipient_type"]
        )


@patch("AsyncUpdateStatus.index.update_upload_status")
def test_handler_update_status_data_uploaded_s2s(
    mock_update_upload_status
):
    sns_message = generate_tuple(True)
    data_uploaded(sns_message, "wow", "much test")
    args, _ = mock_update_upload_status.call_args

    assert args[0] == "Pending"
    assert args[1] == "S2SSuccess"
    assert mock_update_upload_status.called


@patch("AsyncUpdateStatus.index.update_upload_status")
def test_handler_update_status_data_uploaded(
    mock_update_upload_status
):
    sns_message = generate_tuple(False)
    data_uploaded(sns_message, "wow", "much test")
    args, _ = mock_update_upload_status.call_args

    assert args[0] == "Draft"
    assert args[1] == "Success"
    assert mock_update_upload_status.called


@patch("AsyncUpdateStatus.index.trigger_email")
@patch("AsyncUpdateStatus.index.format_users")
@patch("AsyncUpdateStatus.index.get_org_users")
def test_awaiting_review_email_success(
    mock_get_org_users, mock_format_users, mock_trigger_email
):
    mock_get_org_users.return_value = {
        "Items": [
            {
                "first_name": "Jerry",
                "last_name": "Seinfeld",
                "identifier": "jseinfeld@gmail.com"
            }, {
                "first_name": "George",
                "last_name": "Costanza",
                "identifier": "gcostanza@gmail.com"
            }
        ]
    }
    mock_format_users.return_value = [{
        "first_name": "Jerry",
        "last_name": "Seinfeld",
        "role": "Administrator",
        "email": "jseinfeld@gmail.com",
        "status": "Active"
    }]
    import_metadata = {"module_id": "1", "updated_by": "George",
                       "year": 2024, "parent_org_id": 2134}
    message = generate_tuple(True)

    send_awaiting_review_email(import_metadata, message)
    assert mock_get_org_users.called
    assert mock_format_users.called
    assert mock_trigger_email.called

    execute_args, _ = mock_trigger_email.call_args
    assert execute_args[0]["email_type"] == Email_Template.DR_APPROVAL


@patch("AsyncUpdateStatus.index.trigger_email")
@patch("AsyncUpdateStatus.index.get_user_info_dynamo")
def test_s2s_send_upload_success_email(
    mock_get_user_info_dynamo, mock_trigger_email
):
    import_metadata = {"module_id": "1", "updated_by": "George",
                       "year": 2024, "parent_org_id": 2134}
    message = generate_tuple(True)

    send_email(import_metadata, "S2SSuccess", message)
    assert mock_get_user_info_dynamo.called
    assert mock_trigger_email.called

    execute_args, _ = mock_trigger_email.call_args
    assert execute_args[0]["email_type"] == \
        Email_Template.S2S_PROCESSING_SUCCESS

def get_event_object():
    event_object = {
        "Records": [
            {
                "body": json.dumps(body),
                "messageAttributes": {
                    "file-type": {
                        "stringValue": "json"
                    },
                    "biz-magic": {
                        "stringValue": "failed",
                    }
                },
            }
        ]
    }
    return event_object

@patch("AsyncUpdateStatus.index.error_row_exists", return_value = True)
@patch("AsyncUpdateStatus.index.aurora")
@patch("AsyncUpdateStatus.index.biz_magic_validation")
def test_handler_biz_magic_fail(
    mock_biz_magic_validation,
    mock_aurora,
    _mock_error_row_exists
):
    event_object = get_event_object()
    handler(event_object, "context")
    assert mock_biz_magic_validation.called
    assert mock_aurora.get_connection.called


@patch("AsyncUpdateStatus.index.get_upload_metadata")
@patch("AsyncUpdateStatus.index.insert_into_error_table")
@patch("AsyncUpdateStatus.index.error_row_exists", return_value = False)
@patch("AsyncUpdateStatus.index.aurora")
@patch("AsyncUpdateStatus.index.biz_magic_validation")
def test_handler_biz_magic_fail_with_no_error_row(
    mock_biz_magic_validation,
    mock_aurora,
    _mock_error_row_exists,
    mock_insert_into_error_table,
    _mock_get_upload_metadata
):
    event_object = get_event_object()
    handler(event_object, "context")
    assert mock_biz_magic_validation.called
    assert mock_aurora.get_connection.called
    assert mock_insert_into_error_table.called


@patch("AsyncUpdateStatus.index.aurora")
@patch("AsyncUpdateStatus.index.get_attribute_value")
@patch("AsyncUpdateStatus.index.update_upload_status")
def test_handler_biz_magic_passed(
    mock_update_upload_status,
    mock_get_attribute_value,
    mock_aurora
):
    message = namedtuple("Desc", ["message_attribute"])
    message({
        "biz-magic": {
            "stringValue": "failed",
        },
    })
    biz_magic_validation(message, "wow", "much test")
    args, _ = mock_update_upload_status.call_args

    assert args[0] == "Error"
    assert mock_update_upload_status.called


@patch("AsyncUpdateStatus.index.DatabaseCentralConfig")
@patch("AsyncUpdateStatus.index.trigger_email")
@patch("AsyncUpdateStatus.index.get_user_info_dynamo")
def test_ft_central_config_true(
    mock_get_user_info_dynamo, mock_trigger_email, mock_database_central_config
):
    import_metadata = {"module_id": "1", "updated_by": "George",
                       "year": 2024, "parent_org_id": 2134}
    message = generate_tuple(True)

    send_email(
        metadata=import_metadata,
        status_type="S2SSuccess",
        message=message,
        feature_toggle_set={Feature.DATABASE_CENTRAL_CONFIG}
    )
    assert mock_get_user_info_dynamo.called
    assert mock_trigger_email.called
    assert mock_database_central_config.called


@patch("AsyncUpdateStatus.index.DatabaseCentralConfig")
@patch("AsyncUpdateStatus.index.trigger_email")
@patch("AsyncUpdateStatus.index.get_user_info_dynamo")
def test_ft_central_config_false(
    mock_get_user_info_dynamo, mock_trigger_email, mock_database_central_config
):
    import_metadata = {"module_id": "1", "updated_by": "George",
                       "year": 2024, "parent_org_id": 2134}
    message = generate_tuple(True)

    send_email(
        metadata=import_metadata,
        status_type="S2SSuccess",
        message=message,
        feature_toggle_set={}
    )
    assert mock_get_user_info_dynamo.called
    assert mock_trigger_email.called
    assert not mock_database_central_config.called


@patch("AsyncUpdateStatus.index.error_table_insert")
def test_insert_into_error_table_given_checksum_failed(mock_error_table_insert):
    cursor = MagicMock()
    metadata = {"upload_id": "123", "module_id": "2", "org_id": "1", "parent_org": "1"}
    message = "An internal error occurred, please try your upload again, if the issue persists, contact EV-ChART help."
    insert_into_error_table(cursor, metadata, message)
    conditions = [{"error_row": None, "error_description": message, "header_name": ""}]

    # use kwargs instead of args since I used named(key word) args
    _, kwargs = mock_error_table_insert.call_args
    assert mock_error_table_insert.called
    assert kwargs["cursor"] == cursor
    assert kwargs["upload_id"] == metadata["upload_id"]
    assert kwargs["module_id"] == metadata["module_id"]
    assert kwargs["org_id"] == metadata["org_id"]
    assert kwargs["dr_id"] == metadata["parent_org"]
    assert kwargs["condition_list"] == conditions
    assert kwargs["df"] is None


@patch("AsyncUpdateStatus.index.error_table_insert")
def test_insert_into_error_table_given_none(mock_error_table_insert):
    cursor = MagicMock()
    upload_id = "123"
    metadata = None
    message = "an error occured"
    conditions = [{"error_row": None, "error_description": message, "header_name": ""}]

    insert_into_error_table(cursor, metadata, message, upload_id)
    _, kwargs = mock_error_table_insert.call_args

    assert mock_error_table_insert.called
    assert kwargs["cursor"] == cursor
    assert kwargs["upload_id"] == upload_id
    assert kwargs["module_id"] == ""
    assert kwargs["org_id"] == ""
    assert kwargs["dr_id"] == ""
    assert kwargs["condition_list"] == conditions
    assert kwargs["df"] is None


def test_insert_into_error_table_given_none_and_no_upload_id_raise_error():
    cursor = MagicMock()
    metadata = None
    message = "an error occured"
    with pytest.raises(TypeError) as e:
        insert_into_error_table(cursor, metadata, message)
    assert e