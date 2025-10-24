from datetime import datetime
from unittest.mock import patch

import pytest
import os
#module paths are set in conftest.py
from APIGetDraftOrSubmittedData.index import (format_metadata,
                                              format_module_frequency,
                                              format_module_name,
                                              validate_status)
import feature_toggle
from feature_toggle.feature_enums import Feature

valid_event = {
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
        "preferred_name": "Elaine Benes"
      }
    }
  }
}

def mock_get_draft_modules():
    module6 = {
        "comments": None, 
        "module_id" : 6, 
        "org_id" : 123, 
        "parent_org": 123,
        "quarter": None, 
        "submission_status": "Draft",
        "upload_id": 111,
        "upload_friendly_id": 1,
        "updated_by" : "Sophia Canja",
        "updated_on" : datetime(2024, 2, 7, 22, 39, 38)
    }
    
    module2 = {
        "comments": None, 
        "module_id" : 2, 
        "org_id" : 123, 
        "parent_org": 123,
        "quarter": 4, 
        "submission_status": "Draft",
        "upload_id": 111,
        "upload_friendly_id": 2,
        "updated_by" : "Sophia Canja",
        "updated_on" : datetime(2024, 2, 7, 22, 39, 38)
    }
    
    module_data = []
    module_data.append(module6)
    module_data.append(module2)
    return module_data
    
     
def test_validate_status_valid():
    draft = "Draft"
    submitted = "Submitted"
    
    status_draft = validate_status(draft)
    status_submitted = validate_status(submitted)
    
    assert status_draft is True
    assert status_submitted is True
    
    
def test_validate_status_invalid():
    pending = "Pending Approval"
    rejected = "Rejected"
    random = "asdf"
    
    with pytest.raises(Exception):
        response1 = validate_status(pending)
        assert response1.get('statusCode') == 406
        
    with pytest.raises(Exception):
        response2 = validate_status(rejected)
        assert response2.get('statusCode') == 406
        
    with pytest.raises(Exception):
        response3 = validate_status(random)
        assert response3.get('statusCode') == 406
        
    

def test_format_module_name():
    module_data_arr = mock_get_draft_modules() 
    module_data = module_data_arr[0]
    
    response = format_module_name(module_data)
    assert response.get("module_name") == "Module 6: Station Operator Identity"
    assert response.get("module_id") == 6
    
    
def test_format_module_frequency_annual_onetime():
    module1 = {"module_id" : "1"}
    module5 = {"module_id" : "5"}
    module6 = {"module_id": "6"}
    module7  = {"module_id" : "7"}
    module8 = {"module_id" : "8"}
    module9  = {"module_id" : "9"}
    
    module1_response = format_module_frequency(module1)
    module5_response = format_module_frequency(module5)
    module6_response = format_module_frequency(module6)
    module7_response = format_module_frequency(module7)
    module8_response = format_module_frequency(module8)
    module9_response = format_module_frequency(module9)
    
    assert module1_response.get("module_frequency") == "One-Time"
    assert module5_response.get("module_frequency") == "Annual"
    assert module6_response.get("module_frequency") == "One-Time"
    assert module7_response.get("module_frequency") == "Annual"
    assert module8_response.get("module_frequency") == "One-Time"
    assert module9_response.get("module_frequency") == "One-Time"

 
def module_data_quarter_1():
    return {"module_id": "2", "quarter": "1"}


def module_data_quarter_2():
    return {"module_id": "2", "quarter": "2"}


def module_data_quarter_3():
    return {"module_id": "2", "quarter": "3"}


def module_data_quarter_4():
    return {"module_id": "2", "quarter": "4"}


def test_format_module_frequency_module2_quarterly():
    # quarter 1
    response1 = format_module_frequency(module_data_quarter_1())
    assert response1.get("module_frequency") == "Quarter 1 (Jan-Mar)"
    assert response1.get("module_id") == "2"

    # quarter 2
    response2 = format_module_frequency(module_data_quarter_2())
    assert response2.get("module_frequency") == "Quarter 2 (Apr-Jun)"
    assert response2.get("module_id") == "2"

    # quarter 3
    response3 = format_module_frequency(module_data_quarter_3())
    assert response3.get("module_frequency") == "Quarter 3 (Jul-Sep)"
    assert response3.get("module_id") == "2"

    # quarter 4
    response4 = format_module_frequency(module_data_quarter_4())
    assert response4.get("module_frequency") == "Quarter 4 (Oct-Dec)"
    assert response4.get("module_id") == "2"


# this tests fails and throws a format string error because some environments do not support the .strftime %-I which takes out the leading zeros in the time ex: 09:23 = 9:23
# def test_format_datetime_obj_uploaded_and_submitted():
#     date = datetime(2024, 2, 7, 22, 39, 38)
#     module_data_dict = {
#         "uploaded_on" : date,
#         "submitted_on" : date
#     }
    
#     expected_response = {
#         "uploaded_on" : "02/07/24 5:39 AM EST",
#         "submitted_on" : "02/07/24 5:39 AM EST"
#     }
    
#     response = format_datetime_obj(module_data_dict)
#     assert response == expected_response
# assert response.get("uploaded_on") == "02/07/24 5:39 PM EST"

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetDraftOrSubmittedData.index.DatabaseCentralConfig")
@patch('evchart_helper.module_helper.format_fullname_from_email')
@patch('evchart_helper.module_helper.format_sub_recipient')
@patch('APIGetDraftOrSubmittedData.index.format_datetime_obj')
@patch('evchart_helper.module_helper.get_user_info_dynamo')
@patch('evchart_helper.module_helper.get_org_info_dynamo')
def test_format_metadata_DR_views_draft_Mod234(
    mock_org_info,
    mock_user_info,
    mock_date_obj,
    mock_sub_recipient,
    mock_full_name,
    mock_database_central_config
):
    recipient_type = "direct-recipient"
    module_data = [
        {
            "module_id": "2",
            "upload_id": "d2fb7dd6-11a4-4e21-831f-2e8731b70482",
            "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "submission_status": "Draft",
            "updated_on": "2024-02-07 22:39:43",
            "updated_by": "Sophia Canja",
            "year": "2024",
            "quarter": "1"
        },
        {
            "module_id": "3",
            "upload_id": "b955e32e-8ae7-4130-bd85-5e3a4ad04812",
            "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "submission_status": "Draft",
            "updated_on": "2024-02-07 22:49:17",
            "updated_by": "Direct.recipient@local.env",
            "year": "2023",
            "quarter": "1"
        },
        {
            "module_id": "4",
            "upload_id": "b955e32e-8ae7-4130-bd85-5e3a4ad04812",
            "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "submission_status": "Draft",
            "updated_on": "2024-02-07 22:49:17",
            "updated_by": "Direct.recipient@local.env",
            "year": "2023",
            "quarter": "1"
        }
    ]
    mock_date_obj.return_value = None
    mock_org_info.return_value = \
        {"recipient_type": "direct-recipient", "name": "New York DOT"}

    response = format_metadata(recipient_type, module_data)
    mod2_response = response[0]
    mod3_response = response[1]
    mod4_response = response[2]

    # checking valid format for module 2
    assert mod2_response.get("module_id") == "2"
    assert mod2_response.get("module_name") == "Module 2: Charging Sessions"
    assert mod2_response.get("module_frequency") == "Quarter 1 (Jan-Mar)"
    assert mod2_response.get("direct_recipient") == "New York DOT"
    assert "sub_recipient" not in mod2_response

    # checking valid format for module 3
    assert mod3_response.get("module_id") == "3"
    assert mod3_response.get("module_name") == "Module 3: Uptime"
    assert mod3_response.get("module_frequency") == "Quarter 1 (Jan-Mar)"
    assert mod3_response.get("direct_recipient") == "New York DOT"
    assert "sub_recipient" not in mod3_response

    # checking valid format for module 4
    assert mod4_response.get("module_id") == "4"
    assert mod4_response.get("module_name") == "Module 4: Outages"
    assert mod4_response.get("module_frequency") == "Quarter 1 (Jan-Mar)"
    assert mod4_response.get("direct_recipient") == "New York DOT"
    assert "sub_recipient" not in mod4_response
    assert not mock_sub_recipient.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetDraftOrSubmittedData.index.DatabaseCentralConfig")
@patch('evchart_helper.module_helper.format_fullname_from_email')
@patch('evchart_helper.module_helper.format_sub_recipient')
@patch('APIGetDraftOrSubmittedData.index.format_datetime_obj')
@patch('evchart_helper.module_helper.get_user_info_dynamo')
@patch('evchart_helper.module_helper.get_org_info_dynamo')
def test_format_metadata_SR_views_draft_Mod5(
    mock_org_info,
    mock_user_info,
    mock_date_obj,
    mock_sub_recipient,
    mock_full_name,
    mock_database_central_config
):
    recipient_type = "sub-recipient"
    module_data = [
        {
            "module_id": "5",
            "upload_id": "d2fb7dd6-11a4-4e21-831f-2e8731b70482",
            "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "submission_status": "Draft",
            "updated_on": "2024-02-07 22:39:43",
            "updated_by": "Sophia Canja",
            "year": "2024"
        }
    ]

    mock_date_obj.return_value = None
    mock_org_info.return_value = \
        {"recipient_type": "New York DOT", "name": "New York DOT"}
    response = format_metadata(recipient_type, module_data)
    mod5_response = response[0]
    
    assert mod5_response.get("module_id") == "5"
    assert mod5_response.get("module_frequency") == "Annual"
    assert mod5_response.get("direct_recipient") == "New York DOT"
    assert not mock_sub_recipient.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetDraftOrSubmittedData.index.DatabaseCentralConfig")
@patch('evchart_helper.module_helper.format_fullname_from_email')
@patch('evchart_helper.module_helper.format_sub_recipient')
@patch('APIGetDraftOrSubmittedData.index.format_datetime_obj')
@patch('evchart_helper.module_helper.get_user_info_dynamo')
@patch('evchart_helper.module_helper.get_org_info_dynamo')
@patch.object(
    feature_toggle.FeatureToggleService,
    "get_active_feature_toggles"
)
def test_format_metadata_DR_views_draft_Mod234_central_config_on(
    mock_feature_toggle_set,
    mock_org_info,
    mock_user_info,
    mock_date_obj,
    mock_sub_recipient,
    mock_full_name,
    mock_database_central_config
):
    recipient_type = "direct-recipient"
    module_data = [
        {
            "module_id": "2",
            "upload_id": "d2fb7dd6-11a4-4e21-831f-2e8731b70482",
            "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "submission_status": "Draft",
            "updated_on": "2024-02-07 22:39:43",
            "updated_by": "Sophia Canja",
            "year": "2024",
            "quarter": "1"
        },
        {
            "module_id": "3",
            "upload_id": "b955e32e-8ae7-4130-bd85-5e3a4ad04812",
            "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "submission_status": "Draft",
            "updated_on": "2024-02-07 22:49:17",
            "updated_by": "Direct.recipient@local.env",
            "year": "2023",
            "quarter": "1"
        },
        {
            "module_id": "4",
            "upload_id": "b955e32e-8ae7-4130-bd85-5e3a4ad04812",
            "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "submission_status": "Draft",
            "updated_on": "2024-02-07 22:49:17",
            "updated_by": "Direct.recipient@local.env",
            "year": "2023",
            "quarter": "1"
        }
    ]
    mock_date_obj.return_value = None
    mock_org_info.return_value = \
        {"recipient_type": "direct-recipient", "name": "New York DOT"}
    mock_database_central_config().module_display_name.side_effect = [
        "Module 2: Charging Sessions","Module 3: Uptime","Module 4: Outages"]
    mock_database_central_config().module_frequency.return_value = "quarterly"
    mock_database_central_config().module_frequency_quarter.return_value = "Quarter 1 (Jan-Mar)"

    response = format_metadata(recipient_type, module_data, {Feature.DATABASE_CENTRAL_CONFIG})
    mod2_response = response[0]
    mod3_response = response[1]
    mod4_response = response[2]

    # checking valid format for module 2
    assert mod2_response.get("module_id") == "2"
    assert mod2_response.get("module_name") == "Module 2: Charging Sessions"
    assert mod2_response.get("module_frequency") == "Quarter 1 (Jan-Mar)"
    assert mod2_response.get("direct_recipient") == "New York DOT"
    assert "sub_recipient" not in mod2_response

    # checking valid format for module 3
    assert mod3_response.get("module_id") == "3"
    assert mod3_response.get("module_name") == "Module 3: Uptime"
    assert mod3_response.get("module_frequency") == "Quarter 1 (Jan-Mar)"
    assert mod3_response.get("direct_recipient") == "New York DOT"
    assert "sub_recipient" not in mod3_response

    # checking valid format for module 4
    assert mod4_response.get("module_id") == "4"
    assert mod4_response.get("module_name") == "Module 4: Outages"
    assert mod4_response.get("module_frequency") == "Quarter 1 (Jan-Mar)"
    assert mod4_response.get("direct_recipient") == "New York DOT"
    assert "sub_recipient" not in mod4_response
    assert not mock_sub_recipient.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetDraftOrSubmittedData.index.DatabaseCentralConfig")
@patch('evchart_helper.module_helper.format_fullname_from_email')
@patch('evchart_helper.module_helper.format_sub_recipient')
@patch('APIGetDraftOrSubmittedData.index.format_datetime_obj')
@patch('evchart_helper.module_helper.get_user_info_dynamo')
@patch('evchart_helper.module_helper.get_org_info_dynamo')
def test_format_metadata_SR_views_draft_Mod5_central_config_on(
    mock_org_info,
    mock_user_info,
    mock_date_obj,
    mock_sub_recipient,
    mock_full_name,
    mock_database_central_config
):
    recipient_type = "sub-recipient"
    module_data = [
        {
            "module_id": "5",
            "upload_id": "d2fb7dd6-11a4-4e21-831f-2e8731b70482",
            "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "parent_org": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
            "submission_status": "Draft",
            "updated_on": "2024-02-07 22:39:43",
            "updated_by": "Sophia Canja",
            "year": "2024"
        }
    ]
    mock_date_obj.return_value = None
    mock_org_info.return_value = \
        {"recipient_type": "New York DOT", "name": "New York DOT"}
    mock_database_central_config().module_frequency_proper.return_value = "Annual"
    response = format_metadata(recipient_type, module_data, {Feature.DATABASE_CENTRAL_CONFIG})
    mod5_response = response[0]
    
    assert mod5_response.get("module_id") == "5"
    assert mod5_response.get("module_frequency") == "Annual"
    assert mod5_response.get("direct_recipient") == "New York DOT"
    assert not mock_sub_recipient.called