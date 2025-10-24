import json
import os
from unittest.mock import MagicMock, patch

import email_handler
import feature_toggle
import pytest
from APIPutRemoveStationId.index import handler as api_put_remove_station_id
from evchart_helper.custom_exceptions import (EvChartDatabaseAuroraQueryError,
                                              EvChartUserNotAuthorizedError)
from feature_toggle.feature_enums import Feature


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
        "body": json.dumps({"station_uuid": "71f6da10-7de0-4926-8a72-8cf2fcb444ab"}),
        "headers": {"upload_id": "71f6da10-7de0-4926-8a72-8cf2fcb444ab"},
    }


@pytest.fixture(name="station_data")
def get_station_data():
    return [
        {
            "address": "sdasdf",
            "city": "sdfasdfaf",
            "dr_id": "some UUID",
            "station_uuid": "71f6da10-7de0-4926-8a72-8cf2fcb444ab",
            "latitude": 0.000000,
            "longitude": 0.000000,
            "network_provider": "ampup",
            "nickname": "sdfasfa",
            "project_type": "existing_station",
            "station_id": "ssdfasdfaf",
            "state": "VA",
            "status": "Active",
            "updated_by": "ebenes@ee.doe.gov",
            "updated_on": "2024-12-31 00:00:00",
            "zip": "12345",
            "zip_extended": "1234",
            "operational_date": "2024-12-31",
            "NEVI": 1,
            "CFI": 0,
            "EVC_RAA": 0,
            "CMAQ": 0,
            "CRP": 0,
            "OTHER": 0,
            "AFC": 1,
            "num_fed_funded_ports": 1,
            "num_non_fed_funded_ports": None,
            "is_federally_funded": 1,
        }
    ]

@pytest.fixture(name="email_station_data")
def get_email_station_data():
    return [
        {
            "address": "sdasdf",
            "city": "sdfasdfaf",
            "dr_id": "some UUID",
            "station_uuid": "71f6da10-7de0-4926-8a72-8cf2fcb444ab",
            "latitude": 0.000000,
            "longitude": 0.000000,
            "network_provider": "ampup",
            "nickname": "sdfasfa",
            "project_type": "existing_station",
            "station_id": "ssdfasdfaf",
            "state": "VA",
            "status": "Pending Approval",
            "updated_by": "ebenes@ee.doe.gov",
            "updated_on": "2024-12-31 00:00:00",
            "zip": "12345",
            "zip_extended": "1234",
            "operational_date": "2024-12-31",
            "NEVI": 1,
            "CFI": 0,
            "EVC_RAA": 0,
            "CMAQ": 0,
            "CRP": 0,
            "OTHER": 0,
            "AFC": 1,
            "num_fed_funded_ports": 1,
            "num_non_fed_funded_ports": None,
            "is_federally_funded": 0,
        }
    ]

def get_org_user():
    return {
        "Items":[
            {
                "first_name": "John",
                "last_name": "Doe",
                "role": "admin",
                "identifier": "john.doe@evchart.gov",
                "account_status": "Active"
            },
        ],
    }

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutRemoveStationId.index.aurora")
def test_invalid_recipient_401(
    mock_aurora, mock_feature_enablement_check, mock_feature_toggle, event
):
    mock_aurora.return_value = MagicMock()
    mock_feature_toggle.return_value = {Feature.REMOVE_STATION, Feature.SR_ADDS_STATION}
    event["requestContext"]["authorizer"]["claims"]["scope"] = "sub-recipient"
    res = api_put_remove_station_id(event, None)
    assert res.get("statusCode") == 401


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIPutRemoveStationId.index.remove_station")
@patch("APIPutRemoveStationId.index.verify_station_ownership")
@patch("APIPutRemoveStationId.index.get_station_details")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutRemoveStationId.index.aurora")
def test_valid_deletion_201(
    mock_aurora,
    mock_feature_enablement_check,
    mock_feature_toggle,
    mock_get_station_details,
    mock_station_ownership,
    mock_remove_station,
    event,
    station_data,
):
    mock_get_station_details.return_value = station_data
    mock_aurora.return_value = MagicMock()
    mock_station_ownership.return_value = True
    mock_feature_toggle.return_value = {Feature.SR_ADDS_STATION}
    mock_remove_station.return_value = True
    res = api_put_remove_station_id(event, None)
    assert res.get("statusCode") == 201


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIPutRemoveStationId.index.remove_station")
@patch("APIPutRemoveStationId.index.verify_station_ownership")
@patch("APIPutRemoveStationId.index.get_station_details")
@patch("APIPutRemoveStationId.index.get_user_org_id")
@patch("APIPutRemoveStationId.index.get_org_info_dynamo")
@patch("APIPutRemoveStationId.index.get_org_users")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch.object(email_handler, "send_to_sqs")
@patch("APIPutRemoveStationId.index.aurora")
def test_valid_deletion_201_and_email(
    mock_aurora,
    mock_send_to_sqs,
    mock_get_feature_toggle_by_enum,
    mock_feature_toggle,
    mock_get_org_users,
    mock_get_org_info_dynamo,
    _mock_get_user_org_id,
    mock_get_station_details,
    mock_station_ownership,
    mock_remove_station,
    event,
    email_station_data,
):
    # I used this test to get the HTML output for the email
    mock_get_org_users.return_value = get_org_user()
    mock_get_org_info_dynamo.return_value = {"name": "My Org"}
    mock_get_station_details.return_value = email_station_data
    mock_aurora.return_value = MagicMock()
    mock_station_ownership.return_value = True
    mock_feature_toggle.return_value = {Feature.SR_ADDS_STATION, Feature.SEND_EMAIL}
    mock_get_feature_toggle_by_enum.return_value = "True"
    mock_remove_station.return_value = True
    res = api_put_remove_station_id(event, None)
    args, _ = mock_send_to_sqs.call_args
    html_body = args[0].get("html_body")
    assert "Funding Type" not in html_body
    assert res.get("statusCode") == 201


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIPutRemoveStationId.index.remove_station")
@patch("APIPutRemoveStationId.index.verify_station_ownership")
@patch("APIPutRemoveStationId.index.get_station_details")
@patch("APIPutRemoveStationId.index.get_user_org_id")
@patch("APIPutRemoveStationId.index.get_org_info_dynamo")
@patch("APIPutRemoveStationId.index.get_org_users")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch.object(email_handler, "send_to_sqs")
@patch("APIPutRemoveStationId.index.aurora")
def test_valid_deletion_201_and_email_is_fed_funded(
    mock_aurora,
    mock_send_to_sqs,
    mock_get_feature_toggle_by_enum,
    mock_feature_toggle,
    mock_get_org_users,
    mock_get_org_info_dynamo,
    _mock_get_user_org_id,
    mock_get_station_details,
    mock_station_ownership,
    mock_remove_station,
    event,
    email_station_data,
):
    # I used this test to get the HTML output for the email
    mock_get_org_users.return_value = get_org_user()
    mock_get_org_info_dynamo.return_value = {"name": "My Org"}
    email_station_data[0]["is_federally_funded"] = 1
    mock_get_station_details.return_value = email_station_data
    mock_aurora.return_value = MagicMock()
    mock_station_ownership.return_value = True
    mock_feature_toggle.return_value = {Feature.SR_ADDS_STATION, Feature.SEND_EMAIL}
    mock_get_feature_toggle_by_enum.return_value = "True"
    mock_remove_station.return_value = True
    res = api_put_remove_station_id(event, None)
    args, _ = mock_send_to_sqs.call_args
    html_body = args[0].get("html_body")
    assert "Funding Type" in html_body
    assert res.get("statusCode") == 201


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIPutRemoveStationId.index.remove_station")
@patch("APIPutRemoveStationId.index.verify_station_ownership")
@patch("APIPutRemoveStationId.index.get_station_details")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutRemoveStationId.index.aurora")
def test_invalid_query_error_500(
    mock_aurora,
    _mock_feature_enablement_check,
    mock_feature_toggle,
    mock_get_station_details,
    mock_station_ownership,
    mock_remove_station,
    event,
    station_data,
):
    mock_get_station_details.return_value = station_data
    mock_aurora.return_value = MagicMock()
    mock_station_ownership.return_value = True
    mock_feature_toggle.return_value = {Feature.SR_ADDS_STATION}
    mock_remove_station.side_effect = EvChartDatabaseAuroraQueryError()
    res = api_put_remove_station_id(event, None)
    assert res.get("statusCode") == 500


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIPutRemoveStationId.index.verify_station_ownership")
@patch("APIPutRemoveStationId.index.get_station_details")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
@patch("APIPutRemoveStationId.index.aurora")
def test_invalid_DR_401(
    mock_aurora,
    mock_feature_enablement_check,
    mock_feature_toggle,
    mock_get_station_details,
    mock_station_ownership,
    event,
    station_data,
):
    mock_get_station_details.return_value = station_data
    mock_feature_toggle.return_value = {Feature.SR_ADDS_STATION}
    mock_station_ownership.side_effect = EvChartUserNotAuthorizedError()
    res = api_put_remove_station_id(event, None)
    assert res.get("statusCode") == 403
