import os
from unittest.mock import MagicMock, patch

import pytest
from APIGetModuleDetails.index import handler as api_get_module_details
from evchart_helper.custom_exceptions import EvChartJsonOutputError


@pytest.fixture(name="event")
def get_event():
    return {
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "Pennsylania DOT",
                    "email": "ebenes@ee.doe.gov",
                    "scope": "direct-recipient",
                    "preferred_name": "Elaine Benes",
                    "role": "admin",
                }
            },
        },
        "headers": {"upload_id": "71f6da10-7de0-4926-8a72-8cf2fcb444ab"},
    }


# pylint: disable=too-many-arguments
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("evchart_helper.module_helper.is_org_authorized_to_view_data")
@patch("evchart_helper.module_helper.is_valid_upload_id")
@patch("APIGetModuleDetails.index.format_metadata")
@patch("APIGetModuleDetails.index.get_module_details")
@patch("evchart_helper.module_helper.validate_headers")
@patch("APIGetModuleDetails.index.aurora")
def test_lambda_response_body_valid_200(
    mock_aurora,
    mock_validate_headers,
    mock_get_details,
    mock_format,
    mock_valid_upload_id,
    mock_org_authorized,
    event
):
    mock_aurora.return_value = MagicMock()
    mock_validate_headers.return_value = True
    mock_get_details.return_value = [{"submission_status": "Draft"}]
    mock_format.return_value = {}
    mock_valid_upload_id.return_value = True
    mock_org_authorized.return_value = True
    api_import_response = api_get_module_details(event, None)
    assert api_import_response.get("statusCode") == 200


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetModuleDetails.index.aurora')
def test_lambda_response_body_invalid_400_missing_headers(
    mock_aurora_get_connection,
    event
):
    mock_aurora_get_connection.return_value = MagicMock()
    body = {
        'upload_ids': '71f6da10-7de0-4926-8a72-8cf2fcb444ab'
    }
    event['headers'] = body
    api_import_response = api_get_module_details(event, None)
    assert api_import_response.get("statusCode") == 400


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetModuleDetails.index.get_module_details")
@patch("evchart_helper.module_helper.is_org_authorized_to_view_data")
@patch("evchart_helper.module_helper.is_valid_upload_id")
@patch("evchart_helper.module_helper.validate_headers")
@patch("APIGetModuleDetails.index.aurora")
def test_lambda_response_body_invalid_formatting(
    mock_aurora_get_connection,
    mock_validate_headers,
    mock_valid_upload_id,
    mock_org_authorized,
    mock_get_details,
    event
):
    mock_aurora_get_connection.return_value = MagicMock()
    mock_validate_headers.return_value = True
    mock_valid_upload_id.return_value = True
    mock_org_authorized.return_value = True
    mock_get_details.side_effect = EvChartJsonOutputError()

    api_import_response = api_get_module_details(event, None)
    assert api_import_response.get("statusCode") == 500


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("evchart_helper.module_helper.is_org_authorized_to_view_data")
@patch("evchart_helper.module_helper.is_valid_upload_id")
@patch("APIGetModuleDetails.index.format_metadata")
@patch("APIGetModuleDetails.index.get_module_details")
@patch("evchart_helper.module_helper.validate_headers")
@patch("APIGetModuleDetails.index.aurora")
def test_valid_status_invalid_response_407(
    mock_aurora,
    mock_validate_headers,
    mock_get_details,
    mock_format,
    mock_valid_upload_id,
    mock_org_authorized,
    event
):
    mock_aurora.return_value = MagicMock()
    mock_validate_headers.return_value = True
    mock_get_details.return_value = [{"submission_status": "Processing"}]
    mock_format.return_value = {}
    mock_valid_upload_id.return_value = True
    mock_org_authorized.return_value = True
    api_import_response = api_get_module_details(event, None)
    assert api_import_response.get('statusCode') == 422


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIGetModuleDetails.index.format_metadata')
@patch('APIGetModuleDetails.index.get_module_details')
@patch('APIGetModuleDetails.index.validate_headers')
@patch('APIGetModuleDetails.index.aurora')
def test_invalid_role_type_viewing_pending_data_403(
    mock_aurora,
    mock_validate_headers,
    mock_get_details,
    mock_format,
    event
):
    mock_aurora.return_value = MagicMock()
    mock_validate_headers.return_value = True
    mock_get_details.return_value = [{"submission_status": "Pending Approval"}]
    mock_format.return_value = {}
    event["requestContext"]["authorizer"]["claims"]["role"] = "Viewer"
    api_import_response = api_get_module_details(event, None)
    assert api_import_response.get('statusCode') == 403

    mock_get_details.return_value = [{"submission_status": "Draft"}]
    api_import_response = api_get_module_details(event, None)
    assert api_import_response.get('statusCode') == 403
