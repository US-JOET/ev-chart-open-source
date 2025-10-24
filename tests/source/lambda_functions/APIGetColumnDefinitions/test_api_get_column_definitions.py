import json
from unittest.mock import patch
import os
import feature_toggle
import pytest
from feature_toggle.feature_enums import Feature


from APIGetColumnDefinitions.index import handler as api_get_column_definitions


@pytest.fixture(name="event")
def get_valid_event():
    return {
        "headers": {"table_name": "station_direct_recipient"},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "JOET",
                    "email": "dev@ee.doe.gov",
                    "scope": "joet",
                    "role": "admin",
                }
            },
        },
    }

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_getting_column_definitions_for_dr_station_with_register_non_fed_FT_OFF(
    mock_get_feature_by_enum, event
):
    mock_get_feature_by_enum.return_value = {}
    expected_output = {
        "headers": ["Station Nickname", "Station ID", "Status", "Subrecipient/Contractor", "Actions", "Please Note"],
        "values" :["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
            "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
            'Stations can have two statuses: "Pending Approval" and "Active". Stations with a “Pending Approval” status are waiting for your review. Stations with an "Active" status signifies the station has been approved/added and data for this station can now be uploaded successfully. Stations can be "Active" before their operational start date.',
            "The Subrecipient(s) that is (are) assigned and authorized to your station.",
            'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.',
            'The "Remove Station" action is only available to stations that do not have any data associated with the station. If you are looking to adjust station details, select "Edit Station" from the "Actions" dropdown.'] # type: ignore
    }
    response = api_get_column_definitions(event, None)
    assert response.get("body") == json.dumps(expected_output)


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_getting_column_definitions_for_station_sub_recipient_with_register_non_fed_FT_OFF(
    mock_get_feature_by_enum, event
):
    event["headers"]["table_name"] = "station_sub_recipient"
    mock_get_feature_by_enum.return_value = {}
    expected_output = {
        "headers": ["Station Nickname", "Station ID", "Status", "Direct Recipient", "Actions"],
        "values" : ["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
            "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
            'Stations can have two statuses: "Pending Approval" and "Active". Stations with a “Pending Approval” status are waiting for review by the direct recipient and no action is required. Stations with an "Active" status signifies the station has been added/approved by the direct recipient and data for this station can now be uploaded successfully. Stations can be "Active" before their operational start date.',
            "The Direct Recipient that authorized your organization to submit data on behalf of this station.",
            'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']
        }
    response = api_get_column_definitions(event, None)
    assert response.get("body") == json.dumps(expected_output)

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_getting_column_definitions_for_station_joet_with_register_non_fed_FT_OFF(
    mock_get_feature_by_enum, event
):
    event["headers"]["table_name"] = "station_joet"
    mock_get_feature_by_enum.return_value = {}
    expected_output = {
        "headers":  ["Station Nickname", "Station ID", "Direct Recipient"],
        "values" :["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
            "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
            "The Direct Recipient of federal funding for which the station has been registered under."]
        }
    response = api_get_column_definitions(event, None)
    assert response.get("body") == json.dumps(expected_output)


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_getting_column_definitions_for_dr_station_with_register_non_fed_FT_ON(
    mock_get_feature_by_enum, event
):
    mock_get_feature_by_enum.return_value = {Feature.REGISTER_NON_FED_FUNDED_STATION}
    expected_output = {
        "headers": ["Station Nickname", "Station ID", "Status", "Subrecipient/Contractor", "Federally Funded", "Actions", "Please Note"],
        "values" :["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
            "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
            'Stations can have two statuses: "Pending Approval" and "Active". Stations with a “Pending Approval” status are waiting for your review. Stations with an "Active" status signifies the station has been approved/added and data for this station can now be uploaded successfully. Stations can be "Active" before their operational start date.',
            "The Subrecipient(s) that is (are) assigned and authorized to your station.",
            "The acquisition, installation, network connection, operation, or maintenance of this charging station, uses funds made available under Title 23, U.S.C. for projects for the construction of publicly accessible EV chargers or any EV charging infrastructure project funded with Federal funds that is treated as a project on a Federal-aid highway. Note that this is a frontend-only field used to determine which subsequent fields and subsections are displayed.",
            'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.',
            'The "Remove Station" action is only available to stations that do not have any data associated with the station. If you are looking to adjust station details, select "Edit Station" from the "Actions" dropdown.'] # type: ignore
    }
    response = api_get_column_definitions(event, None)
    assert response.get("body") == json.dumps(expected_output)


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_getting_column_definitions_for_station_sub_recipient_with_register_non_fed_FT_ON(
    mock_get_feature_by_enum, event
):
    event["headers"]["table_name"] = "station_sub_recipient"
    mock_get_feature_by_enum.return_value = {Feature.REGISTER_NON_FED_FUNDED_STATION}
    expected_output = {
        "headers":  ["Station Nickname", "Station ID", "Status", "Direct Recipient", "Federally Funded", "Actions"],
        "values" :["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
            "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
            'Stations can have two statuses: "Pending Approval" and "Active". Stations with a “Pending Approval” status are waiting for review by the direct recipient and no action is required. Stations with an "Active" status signifies the station has been added/approved by the direct recipient and data for this station can now be uploaded successfully. Stations can be "Active" before their operational start date.',
            "The Direct Recipient that authorized your organization to submit data on behalf of this station.",
            "The acquisition, installation, network connection, operation, or maintenance of this charging station, uses funds made available under Title 23, U.S.C. for projects for the construction of publicly accessible EV chargers or any EV charging infrastructure project funded with Federal funds that is treated as a project on a Federal-aid highway. Note that this is a frontend-only field used to determine which subsequent fields and subsections are displayed.",
            'This is the list of actions that are available to you. Select the "Actions" button to see a dropdown of available actions.']
        }
    response = api_get_column_definitions(event, None)
    assert response.get("body") == json.dumps(expected_output)


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_getting_column_definitions_for_station_joet_with_register_non_fed_FT_ON(
    mock_get_feature_by_enum, event
):
    event["headers"]["table_name"] = "station_joet"
    mock_get_feature_by_enum.return_value = {Feature.REGISTER_NON_FED_FUNDED_STATION}
    expected_output = {
        "headers":  ["Station Nickname", "Station ID", "Direct Recipient", "Federally Funded"],
        "values" :["The nickname that was given to the station by the Direct Recipient organization upon station registration.",
            "This uniquely identifies a charging station. The Station ID should have been created by the Network Provider and per 23 CFR 680.112, and must be the same charging station identifier used to identify the charging station in data made available to third-parties in 23 CFR 680.116(c)(1).",
            "The Direct Recipient of federal funding for which the station has been registered under.",
            "The acquisition, installation, network connection, operation, or maintenance of this charging station, uses funds made available under Title 23, U.S.C. for projects for the construction of publicly accessible EV chargers or any EV charging infrastructure project funded with Federal funds that is treated as a project on a Federal-aid highway. Note that this is a frontend-only field used to determine which subsequent fields and subsections are displayed."]
        }
    response = api_get_column_definitions(event, None)
    assert response.get("body") == json.dumps(expected_output)


# Tests the bug JE-6911, to return column definitions  for the station submission details table
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_getting_column_definitions_for_station_submission_details(
    mock_get_feature_by_enum, event
):
    event["headers"]["table_name"] = "dr_station_submission_details"
    mock_get_feature_by_enum.return_value = {Feature.REGISTER_NON_FED_FUNDED_STATION}
    expected_output = {
        "headers":  ["Module", "Subrecipient/Contractor", "Status", "Updated On", "Upload ID" ],
        "values" :["The module associated with the Submitted Module Data. Additional details about each module can be found in the EV-ChART Data Input Guidance documentation.",
            'The Subrecipient or Contractor for your organization that uploaded the Module Data. "N/A" is displayed if someone within your oganization Submitted this Module Data.',
            "The Module Data's current status (pending approval, submitted, rejected) within the submission process. Modules that have the status of 'Pending approval' need to be approved by the Direct Recipient. Modules that have the status of 'Rejected' need to be resubmitted. Modules that are 'Submitted' have been approved by the Direct Recipient and are considered complete.",
            "The date on which the Module Data was last updated.",
            "An EV-ChART identifier that uniquely identifies the Submitted Module Data."]
        }
    response = api_get_column_definitions(event, None)
    assert response.get("body") == json.dumps(expected_output)