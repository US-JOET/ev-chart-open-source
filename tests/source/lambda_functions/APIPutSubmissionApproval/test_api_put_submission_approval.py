import datetime
import json
import os
from unittest.mock import patch, MagicMock
from copy import deepcopy

from email_handler.email_enums import Email_Template
from evchart_helper.custom_exceptions import (
    EvChartDatabaseAuroraQueryError,
    EvChartUserNotAuthorizedError,
)
import feature_toggle
from feature_toggle.feature_enums import Feature
from APIPutSubmissionApproval.index import (
    handler as api_put_submission_approval,
    send_submission_status_email,
    set_submission_status,
    validate_upload_id,
)

import pytest

event = {
    "headers": {},
    "httpMethod": "MODIFY",
    "requestContext": {
        "accountId": "414275662771",
        "authorizer": {
            "claims": {
                "org_id": "123",
                "org_friendly_id": "1",
                "org_name": "New York DOT",
                "email": "dev@ee.doe.gov",
                "scope": "direct-recipient",
                "preferred_name": "",
                "role": "admin",
            }
        },
    },
    "body": json.dumps(
        {
            "upload_id": "0987",
            "submission_status": "Rejected",
            "updated_by": "DR1",
            "comments": "No comment",
        }
    ),
}


# 201, valid response
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutSubmissionApproval.index.validate_upload_id")
@patch("APIPutSubmissionApproval.index.aurora")
def test_rejected_module_valid_201(mock_aurora, mock_validate_upload_id, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {"Name": "new-user-email", "Value": "True"}
    mock_validate_upload_id.return_value = True

    response = api_put_submission_approval(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 201


# 422, EvChartInvalidDataError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutSubmissionApproval.index.validate_upload_id")
@patch("APIPutSubmissionApproval.index.aurora")
def test_approved_module_valid_201(mock_aurora, mock_validate_upload_id, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {"Name": "new-user-email", "Value": "True"}
    mock_validate_upload_id.return_value = True
    event_invalid_status = deepcopy(event)
    event_invalid_status["body"] = json.dumps(
        {
            "upload_id": "0987",
            "submission_status": "Approved",
            "updated_by": "DR1",
            "comments": "No comment",
        }
    )

    response = api_put_submission_approval(event_invalid_status, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 201


# 400, EvChartMissingOrMalformedBodyError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutSubmissionApproval.index.aurora")
def test_invalid_headers_406(mock_aurora_connection, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {"Name": "new-user-email", "Value": "True"}
    invalid_event = deepcopy(event)
    invalid_event["body"] = json.dumps({})
    response = api_put_submission_approval(invalid_event, None)
    assert response.get("statusCode") == 406
    assert mock_aurora_connection.get_connection.called


# 401, EvChartAuthorizationTokenInvalidError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutSubmissionApproval.index.aurora")
def test_invalid_token_401(mock_aurora_connection, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {"Name": "new-user-email", "Value": "True"}

    response = api_put_submission_approval({"headers": {}}, None)
    assert response.get("statusCode") == 401
    assert mock_aurora_connection.get_connection.called


# 403, EvChartUserNotAuthorizedError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutSubmissionApproval.index.execute_query")
@patch("APIPutSubmissionApproval.index.aurora")
def test_user_not_authorized_407(mock_aurora_connection, mock_query, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {"Name": "new-user-email", "Value": "True"}
    mock_query.return_value = [{"parent_org": "invalid-parent-org"}]
    validate_upload_id.side_effect = EvChartUserNotAuthorizedError
    response = api_put_submission_approval(event, None)
    assert response.get("statusCode") == 403
    assert mock_aurora_connection.get_connection.called


# 422, EvChartInvalidDataError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutSubmissionApproval.index.validate_upload_id")
@patch("APIPutSubmissionApproval.index.aurora")
def test_invalid_status_407(mock_aurora, mock_validate_upload_id, mock_get_feature_by_enum):
    mock_get_feature_by_enum.return_value = {"Name": "new-user-email", "Value": "True"}
    mock_validate_upload_id.return_value = True
    event_invalid_status = deepcopy(event)
    event_invalid_status["body"] = json.dumps(
        {
            "upload_id": "0987",
            "submission_status": "Submitted",
            "updated_by": "DR1",
            "comments": "No comment",
        }
    )

    response = api_put_submission_approval(event_invalid_status, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 422


# 422, EvChartInvalidDataError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutSubmissionApproval.index.execute_query")
@patch("APIPutSubmissionApproval.index.aurora")
def test_invalid_upload_id_407(
    mock_aurora_connection, mock_execute_query, mock_get_feature_by_enum
):
    mock_get_feature_by_enum.return_value = {"Name": "new-user-email", "Value": "True"}
    mock_execute_query.return_value = []
    response = api_put_submission_approval(event, None)
    assert response.get("statusCode") == 422
    assert mock_aurora_connection.get_connection.called


# 500, EvChartDatabaseAuroraQueryError
@patch("APIPutSubmissionApproval.index.validate_upload_id")
@patch("APIPutSubmissionApproval.index.aurora")
def test_invalid_aurora_query_500(mock_aurora_connection, mock_validate):
    mock_validate.return_value = None
    set_submission_status.side_effect = EvChartDatabaseAuroraQueryError
    with pytest.raises(EvChartDatabaseAuroraQueryError):
        set_submission_status(None, MagicMock(), None)
        assert mock_aurora_connection.get_connection.called


@patch("APIPutSubmissionApproval.index.get_org_info_dynamo")
@patch("APIPutSubmissionApproval.index.get_user_info")
@patch("APIPutSubmissionApproval.index.trigger_email")
@pytest.mark.skipif(os.name == "nt", reason="format_datetime_obj does not work on windows")
def test_send_submission_status(mock_trigger_email, mock_get_user_info, mock_get_org_info_dynamo):
    token = {}
    upload_info = {
        "module_id": "2",
        "updated_by": "oscar@grouch.gov",
        "updated_on": datetime.datetime.utcnow(),
    }
    request_body = {"comments": "scram!", "upload_id": "upload123", "submission_status": "Rejected"}

    send_submission_status_email(token, request_body, upload_info)
    assert mock_get_user_info.called
    assert mock_get_org_info_dynamo.called

    execute_args, _ = mock_trigger_email.call_args
    assert execute_args[0]["email_type"] == Email_Template.SR_REJECTED

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum"
)
@patch("APIPutSubmissionApproval.index.get_org_info_dynamo")
@patch("APIPutSubmissionApproval.index.get_user_info")
@patch("APIPutSubmissionApproval.index.DatabaseCentralConfig")
@patch("APIPutSubmissionApproval.index.validate_upload_id")
@patch("APIPutSubmissionApproval.index.aurora")
@pytest.mark.skipif(os.name == "nt", reason="format_datetime_obj does not work on windows")
def test_ft_central_config_false(
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    mock_aurora,
    mock_validate_upload_id,
    mock_database_central_config,
    mock_get_user_info,
    mock_get_org_info_dynamo,
    mock_get_feature_toggle_by_enum
):
    mock_get_feature_toggle_by_enum.side_effect = lambda f, _: (
        "True"
        if f in {Feature.DATA_APPROVAL_REJECTION_EMAIL}
        else "False"
    )

    mock_validate_upload_id.return_value = {
        "updated_by": "system",
        "org_id": "dr123",
        "module_id": "4",
        "updated_on": datetime.datetime.now(),
        "year": 2024
    }

    response = api_put_submission_approval(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 201
    assert mock_get_user_info.called
    assert mock_get_org_info_dynamo.called
    assert not mock_database_central_config.called

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum"
)
@patch("APIPutSubmissionApproval.index.get_org_info_dynamo")
@patch("APIPutSubmissionApproval.index.get_user_info")
@patch("APIPutSubmissionApproval.index.DatabaseCentralConfig")
@patch("APIPutSubmissionApproval.index.validate_upload_id")
@patch("APIPutSubmissionApproval.index.aurora")
@pytest.mark.skipif(os.name == "nt", reason="format_datetime_obj does not work on windows")
def test_ft_central_config_true(
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    mock_aurora,
    mock_validate_upload_id,
    mock_database_central_config,
    mock_get_user_info,
    mock_get_org_info_dynamo,
    mock_get_feature_toggle_by_enum
):
    mock_get_feature_toggle_by_enum.side_effect = lambda f, _: (
        "True"
        if f in {
            Feature.DATA_APPROVAL_REJECTION_EMAIL,
            Feature.DATABASE_CENTRAL_CONFIG
        }
        else "False"
    )

    mock_validate_upload_id.return_value = {
        "updated_by": "system",
        "org_id": "dr123",
        "module_id": "4",
        "updated_on": datetime.datetime.now(),
        "year": 2024
    }

    response = api_put_submission_approval(event, None)
    assert mock_aurora.get_connection.called
    assert response.get("statusCode") == 201
    assert mock_get_user_info.called
    assert mock_get_org_info_dynamo.called
    assert mock_database_central_config.called
