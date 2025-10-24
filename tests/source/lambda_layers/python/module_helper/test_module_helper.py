from unittest.mock import patch, MagicMock
import os

from database_central_config import DatabaseCentralConfig
from evchart_helper.custom_exceptions import EvChartDatabaseDynamoQueryError
from evchart_helper.module_helper import (
    get_module_details,
    is_org_authorized_to_view_data,
    format_sub_recipient,
    format_direct_recipient,
    format_dataframe_bool,
    get_approval_chain,
    get_next_reviewer,
    format_module_frequency

)
from feature_toggle.feature_enums import Feature
import feature_toggle

import numpy
import pandas
import pytest

def mock_get_upload_info(recipient, status):
    # [module_org, module_parent_org, status]
    if recipient == "DR" and status == "Draft":
        return ["NY DOT", "NY DOT", "Draft"]
    if recipient == "DR" and status == "Submitted":
        return ["NY DOT", "NY DOT", "Submitted"]
    # SR views
    if recipient == "SR" and status == "Draft":
        return ["Sparkflow", "NY DOT", "Draft"]
    if recipient == "SR" and status == "Submitted":
        return ["Sparkflow", "NY DOT", "Submitted"]
    return []


def cursor():
    return MagicMock()


def log():
    return MagicMock()


@pytest.fixture(name="config")
def fixture_config():
    return DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json"
        )
    )


@patch('evchart_helper.module_helper.get_upload_info')
def test_is_org_authd_to_view_data_dr_views_own_draft_and_submitted_data_valid(
    mock_upload_info
):
    mock_upload_info.return_value = mock_get_upload_info("DR", "Draft")
    response_draft_data = is_org_authorized_to_view_data(
        "111", "NY DOT", "direct-recipient", cursor()
    )
    assert response_draft_data is True

    mock_upload_info.return_value = mock_get_upload_info("DR", "Submitted")
    response_submitted_data = is_org_authorized_to_view_data(
        "111", "NY DOT", "direct-recipient", cursor()
    )
    assert response_submitted_data is True


@patch('evchart_helper.module_helper.get_upload_info')
def test_is_org_authd_to_view_data_sr_views_own_draft_and_submitted_data_valid(
    mock_upload_info
):
    mock_upload_info.return_value = mock_get_upload_info("SR", "Draft")
    response_draft_data = is_org_authorized_to_view_data(
        "111", "Sparkflow", "sub-recipient", cursor()
    )
    assert response_draft_data is True

    mock_upload_info.return_value = mock_get_upload_info("SR", "Submitted")
    response_submitted_data = is_org_authorized_to_view_data(
        "111", "Sparkflow", "sub-recipient", cursor()
    )
    assert response_submitted_data is True


@patch('evchart_helper.module_helper.get_upload_info')
def test_is_org_authorized_to_view_data_dr_views_sr_draft_and_submitted_data(
    mock_upload_info
):
    mock_upload_info.return_value = mock_get_upload_info("SR", "Draft")
    response_invalid = is_org_authorized_to_view_data(
        "111", "NY DOT", "direct-recipient", cursor()
    )
    assert response_invalid is False

    mock_upload_info.return_value = mock_get_upload_info("SR", "Submitted")
    response_valid = is_org_authorized_to_view_data(
        "111", "NY DOT", "direct-recipient", cursor()
    )
    assert response_valid is True


@patch('evchart_helper.module_helper.get_upload_info')
def test_dr_view_dr_draft_invalid(mock_upload_info):
    """
        is_org_authorized_to_view_data_DR_views_other_DR_draft
        and_submitted_data_invalid
    """
    mock_upload_info.return_value = mock_get_upload_info("DR", "Draft")

    response_submitted_data = is_org_authorized_to_view_data(
        "111", "PA DOT", "direct-recipient", cursor()
    )
    assert response_submitted_data is False

    mock_upload_info.return_value = mock_get_upload_info("DR", "Submitted")
    response = is_org_authorized_to_view_data(
        "111", "PA DOT", "direct-recipient", cursor()
    )
    assert response is False


@patch('evchart_helper.module_helper.get_upload_info')
def test_sr_view_sr_draft_invalid(mock_upload_info):
    """
        is_org_authorized_to_view_data_SR_views_other_SR_draft
        and_submitted_data_invalid
    """
    mock_upload_info.return_value = mock_get_upload_info("SR", "Draft")
    response_draft_data = is_org_authorized_to_view_data(
        "111", "Spark08", "sub-recipient", cursor()
    )
    assert response_draft_data is False

    mock_upload_info.return_value = mock_get_upload_info("SR", "Submitted")
    response_draft_data = is_org_authorized_to_view_data(
        "111", "Spark08", "sub-recipient", cursor()
    )
    assert response_draft_data is False


@patch('evchart_helper.module_helper.get_upload_info')
def test_sr_view_dr_draft_invalid(mock_upload_info):
    """
        is_org_authorized_to_view_data_SR_views_other_DR_draft
        and_submitted_data_invalid
    """
    mock_upload_info.return_value = mock_get_upload_info("DR", "Draft")

    response_draft_data = is_org_authorized_to_view_data(
        "111", "Spark08", "sub-recipient", cursor()
    )
    assert response_draft_data is False

    mock_upload_info.return_value = mock_get_upload_info("DR", "Draft")
    response_submitted_data = is_org_authorized_to_view_data(
        "111", "Spark08", "sub-recipient", cursor()
    )
    assert response_submitted_data is False


@patch('evchart_helper.module_helper.get_upload_info')
def test_joet_viewing_dr_submitted_module(mock_upload_info):
    mock_upload_info.return_value = \
        ["New York DOT", "New York DOT", "Submitted"]
    response = is_org_authorized_to_view_data(
        "111", "Joint Office", "joet", cursor()
    )
    assert response is True


@patch('evchart_helper.module_helper.get_upload_info')
def test_joet_viewing_sr_approved_module(mock_upload_info):
    mock_upload_info.return_value = \
        ["Sparkflow", "Sparkflow", "Approved"]
    response = is_org_authorized_to_view_data(
        "111", "Joint Office", "joet", cursor()
    )
    assert response is True


@patch('evchart_helper.module_helper.get_upload_info')
def test_is_org_authorized_to_view_data_invalid_joet(mock_upload_info):
    mock_upload_info.return_value = ["New York DOT", "New York DOT", "Draft"]
    response = is_org_authorized_to_view_data(
        "111", "Joint Office", "joet", cursor()
    )
    assert response is False


@patch('evchart_helper.module_helper.get_org_info_dynamo')
def test_format_sub_recipient_dr_view(mock_get_org_info):
    module_data = {
        "org_id": "111"
    }

    mock_get_org_info.return_value = \
        {"recipient_type": "direct-recipient", "name": "New York DOT"}
    response = format_sub_recipient(module_data)
    assert response.get("sub_recipient") == "N/A"


@patch('evchart_helper.module_helper.get_org_info_dynamo')
def test_format_sub_recipient_sr_view(mock_get_org_info):
    module_data = {
        "org_id": "222"
    }

    mock_get_org_info.return_value = \
        {"recipient_type": "sub-recipient", "name": "Sparkflow"}
    response = format_sub_recipient(module_data)
    assert response.get("sub_recipient") == "Sparkflow"


@patch('evchart_helper.module_helper.get_org_info_dynamo')
def test_format_direct_recipient_dr_present(mock_get_org_info):
    module_data = {
        "parent_org": "111"
    }

    mock_get_org_info.return_value = \
        {"recipient_type": "direct-recipient", "name": "New York DOT"}
    response = format_direct_recipient(module_data)
    assert response.get("direct_recipient") == "New York DOT"


def test_format_dataframe_bool_station_variables():
    df = pandas.DataFrame({
        "NEVI": [0, 1, None],
        "AFC": [0.0, 1.0, numpy.nan]
    })
    expected_df = pandas.DataFrame({
        "NEVI": ["FALSE", "TRUE", ""],
        "AFC": ["FALSE", "TRUE", ""]
    })

    format_dataframe_bool(df)
    pandas.testing.assert_frame_equal(df, expected_df)


@patch("evchart_helper.module_helper.DatabaseCentralConfig")
def test_format_dataframe_bool__central_config_ft_true(
    mock_database_central_config, config
):
    mock_database_central_config.return_value = config
    df = pandas.DataFrame({
        "NEVI": [0, 1, None],
        "AFC": [0.0, 1.0, numpy.nan],
        "excluded_outage": [0, 1, None]
    })
    expected_df = pandas.DataFrame({
        "NEVI": ["FALSE", "TRUE", ""],
        "AFC": ["FALSE", "TRUE", ""],
        "excluded_outage": ["FALSE", "TRUE", ""]
    })

    format_dataframe_bool(df, {Feature.DATABASE_CENTRAL_CONFIG})
    pandas.testing.assert_frame_equal(df, expected_df)


@patch('evchart_helper.module_helper.execute_query')
def test_get_module_details_joet_view(mock_module_details):
    mock_module_details.return_value = {"org_id": "NY DOT"}
    response = get_module_details("111", "Joint Office", "joet", cursor)
    assert len(response) > 0


# JE-5947 ensuring nested error messages are separated and the correct error is returned
@patch('evchart_helper.module_helper.get_org_info_dynamo')
def test_nested_error_message_format_sub_recipient_500(mock_get_org_info):
    mock_get_org_info.side_effect = EvChartDatabaseDynamoQueryError(message="nested message")
    with pytest.raises(EvChartDatabaseDynamoQueryError) as e:
        format_sub_recipient({"org_id": "test value"})
    assert e.value.message == (
        "EvChartDatabaseDynamoQueryError raised. "
        "nested message Error thrown in format_sub_recipient()"
    )


@patch('evchart_helper.module_helper.get_next_reviewer')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_get_approval_chain_3_tier_multiple_contractors_authorized_to_one_station(
    mock_feature_enablement_check,
    mock_get_next_reviewer,
):
    ny_dot, sparkflow, evgo = '2','3','5'
    mock_get_next_reviewer.side_effect = [sparkflow, ny_dot]
    expected_result = [sparkflow, ny_dot]
    result = get_approval_chain(MagicMock(), evgo, "station_uuid")
    assert result == expected_result


@patch('evchart_helper.module_helper.get_next_reviewer')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_get_approval_chain_3_tier_subcontractor_authorized(
    mock_feature_enablement_check,
    mock_get_next_reviewer
):
    ny_dot, spark09, shell_recharge = '2', '4', '7'
    mock_get_next_reviewer.side_effect = [spark09, ny_dot]
    expected_result = [spark09, ny_dot]
    result = get_approval_chain(MagicMock(), shell_recharge, "station_uuid")
    assert result == expected_result


@patch('evchart_helper.module_helper.get_next_reviewer')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_get_approval_chain_2_tier_subrecipient_authorized(
    mock_feature_enablement_check,
    mock_get_next_reviewer,
):
    sparkflow, ny_dot = '3','2'
    mock_get_next_reviewer.side_effect = [ny_dot, []]
    expected_result = [ny_dot]
    result = get_approval_chain(MagicMock(), sparkflow, "station_uuid")
    assert result == expected_result


@patch('evchart_helper.module_helper.get_next_reviewer')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_approval_chain_1_tier_no_subrecipients_authorized(
    mock_feature_enablement_check,
    mock_get_next_reviewer,
):
    mock_get_next_reviewer.side_effect = [[]]
    expected_result = []
    result = get_approval_chain(MagicMock(), "sparkflow", "station_uuid")
    assert result == expected_result


@patch('evchart_helper.module_helper.execute_query_fetchone')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_get_next_reviewer_valid(
    mock_feature_enablement_check,
    mock_execute
):
    mock_execute.return_value = ['2']
    response = get_next_reviewer(MagicMock(), "curr_org", "station_uuid")
    assert response == '2'

@patch('evchart_helper.module_helper.execute_query_fetchone')
@patch.object(feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum")
def test_get_next_reviewer_no_next_reviewer(
    mock_feature_enablement_check,
    mock_execute
):
    mock_execute.return_value = []
    response = get_next_reviewer(MagicMock(), "curr_org", "station_uuid")
    assert response == []


def test_format_module_frequency_one_time():
    test_dict = {
        "module_id": 9
    }
    response_dict = format_module_frequency(test_dict)
    assert response_dict.get("module_frequency") == "One-Time"

def test_format_module_frequency_annual():
    test_dict = {
        "module_id": 5
    }
    response_dict = format_module_frequency(test_dict)
    assert response_dict.get("module_frequency") == "Annual"

def test_format_module_frequency_quarter():
    test_dict = {
        "module_id": 2,
        "quarter": "2"
    }
    response_dict = format_module_frequency(test_dict)
    assert response_dict.get("module_frequency") == "Quarter 2 (Apr-Jun)"
