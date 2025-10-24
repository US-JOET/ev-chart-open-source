import os
import datetime
import json
from copy import deepcopy
from unittest.mock import patch, MagicMock

import feature_toggle
from feature_toggle.feature_enums import Feature
from evchart_helper.custom_exceptions import (
    EvChartFeatureStoreConnectionError
)
from APIPutSubmitModuleData.index import (
    handler as api_put_submit_module_data,
    check_unique_submission
)
from module_validation.unique_constraint import (
    check_constraints_in_data,
    get_constraints_conditions
)
from error_report_messages_enum import ErrorReportMessages

import pytest
import pandas
from botocore.exceptions import BotoCoreError

event = {
    "headers": {},
    "httpMethod": "PATCH",
    "requestContext": {
        "accountId": "414275662771",
        "authorizer": {
            "claims": {
                "org_id": "1234",
                "org_friendly_id": "1",
                "org_name": "New York DOT",
                "email": "test@gmail.com",
                "preferred_name": "Test test",
                "scope": "direct-recipient",
                "role": "admin"
            }
        }
    }
}

mocked_valid_db_return = {
    "module_id": "123",
    "updated_by": "abc",
    "updated_on": "datetine",
    "year": "2024",
    "parent_org": "123456789",
    "upload_id": "123"
}

@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('APIPutSubmitModuleData.index.get_module_id')
@patch('APIPutSubmitModuleData.index.execute_query')
@patch('APIPutSubmitModuleData.index.is_valid_upload_id')
@patch('APIPutSubmitModuleData.index.aurora')
def test_valid_upload_id_201(
    mock_aurora,
    mock_valid_upload,
    mock_execute_query,
    mock_get_module_id,
    mock_get_active_feature_toggles
):
    mock_get_module_id.return_value = 2
    event["body"] = json.dumps({"upload_id": "123"})
    mock_valid_upload.return_value = True
    mock_execute_query.return_value = [mocked_valid_db_return]
    response = api_put_submit_module_data(event, None)
    assert response.get('statusCode') == 201
    assert mock_aurora.get_connection.called
    assert mock_get_active_feature_toggles.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('APIPutSubmitModuleData.index.aurora')
def test_lambda_missing_upload_id_406(
    mock_aurora, mock_get_active_feature_toggles
):
    event["body"] = json.dumps({})
    response = api_put_submit_module_data(event, None)
    assert response.get('statusCode') == 406
    assert mock_aurora.get_connection.called
    assert mock_get_active_feature_toggles.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('APIPutSubmitModuleData.index.is_valid_upload_id')
@patch('APIPutSubmitModuleData.index.aurora')
def test_malformed_upload_id_406(
    mock_aurora, mock_valid_upload, mock_get_active_feature_toggles
):
    event["body"] = json.dumps({"upload_id": "123"})
    mock_valid_upload.return_value = False
    response = api_put_submit_module_data(event, None)
    assert response.get('statusCode') == 406
    assert mock_aurora.get_connection.called
    assert mock_get_active_feature_toggles.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('APIPutSubmitModuleData.index.aurora')
def test_lambda_response_body_invalid_token_401(
    mock_aurora, mock_get_active_feature_toggles
):
    response = api_put_submit_module_data({"headers": {}}, None)
    assert response.get('statusCode') == 401
    assert mock_aurora.get_connection.called
    assert mock_get_active_feature_toggles.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('APIPutSubmitModuleData.index.execute_query')
@patch('APIPutSubmitModuleData.index.is_valid_upload_id')
@patch('APIPutSubmitModuleData.index.aurora')
def test_user_not_auth_to_submit_403(
    mock_aurora,
    mock_valid_upload,
    mock_execute_query,
    mock_get_active_feature_toggles
):
    event["body"] = json.dumps({"upload_id": "123"})
    mock_valid_upload.return_value = True
    mock_execute_query.return_value = []
    response = api_put_submit_module_data(event, None)
    assert response.get('statusCode') == 403
    assert mock_aurora.get_connection.called
    assert mock_get_active_feature_toggles.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('APIPutSubmitModuleData.index.error_table_insert')
@patch('module_validation.unique_constraint.check_constraints_in_data')
@patch('module_validation.unique_constraint.get_module_id')
@patch('APIPutSubmitModuleData.index.execute_query')
@patch('APIPutSubmitModuleData.index.is_valid_upload_id')
@patch('APIPutSubmitModuleData.index.aurora')
def test_duplicate_module_409(
    # pylint: disable=too-many-positional-arguments
    mock_aurora,
    mock_valid_upload,
    mock_execute_query,
    mock_get_module_id,
    mock_check_constraints_in_data,
    mock_error_table_insert,
    mock_get_active_feature_toggles
):
    # pylint: disable=too-many-arguments
    mock_get_module_id.return_value = "2"
    mock_get_active_feature_toggles.return_value = {
        Feature.UNIQUE_CONSTRAINT_MODULE_2
    }
    index = pandas.MultiIndex.from_tuples(
        [('1', '3', '5')],
        names=['station_uuid', 'port_id', 'session_id']
    )
    mock_check_constraints_in_data.return_value = pandas.Series(
        index=index,
        data=[{"123", "456"}]
    )
    event["body"] = json.dumps({"upload_id": "123"})
    mock_valid_upload.return_value = True
    mock_execute_query.return_value = [mocked_valid_db_return]
    response = api_put_submit_module_data(event, None)
    assert response.get('statusCode') == 409
    assert mock_error_table_insert.called
    assert mock_aurora.get_connection.called
    assert mock_get_active_feature_toggles.called


@patch('APIPutSubmitModuleData.index.get_module_id')
@patch.object(
    feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum"
)
def test_unique_constraint_ft_false(
    mock_get_feature_by_enum,
    mock_get_module_id
):
    mock_get_feature_by_enum.get_feature_toggle_by_enum.return_value = "False"
    mock_get_module_id.return_value = 2
    assert check_unique_submission(
        cursor=MagicMock(),
        log_event=MagicMock(),
        upload_id=None,
        org_id=None,
        dr_id=None,
        feature_toggle_set={}
    )


@patch('APIPutSubmitModuleData.index.get_module_id')
@patch.object(
    feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum"
)
def test_unique_constraint_ft_not_defined(
    mock_get_feature_by_enum,
    mock_get_module_id
):
    mock_get_feature_by_enum.get_feature_toggle_by_enum.side_effect = \
        EvChartFeatureStoreConnectionError
    mock_get_module_id.return_value = 2
    assert check_unique_submission(
        cursor=MagicMock(),
        log_event=MagicMock(),
        upload_id=None,
        org_id=None,
        dr_id=None,
        feature_toggle_set={}
    )


def test_check_constraints_fail():
    df = pandas.DataFrame(data={
        "upload_id": [
            'a1_draft', 'a1_draft', 'a1_draft',
            'a1_draft', 'b2_submitted', 'c3_approved'
        ],
        "network_provider": ["1234","1234", "4564", "789", "789", "1001"],
        "network_provider_upload": ["123","123", "456", "789", "789", "1001"],
        "station_uuid": ["123", "123", "456", "789", "789", "1001"],
        "station_id_upload": ["1", "1", "4", "7", "7", "11"],
        "favorite_color": [
            "red", "orange", "yellow", "green", "blue", "purple"
        ]
    })

    response = check_constraints_in_data(
        df=df, unique_constraint=['station_uuid'], feature_toggle_set={}
    )
    assert response.get(('123','1')).item() == {'a1_draft'}
    assert response.get(('789', '7')).item() == {'a1_draft', 'b2_submitted'}


def test_constraints_conditions_ft_network_provider_false():
    df = pandas.DataFrame(data={
        "upload_id": [
            'a1_draft', 'a1_draft', 'a1_draft',
            'a1_draft', 'b2_submitted', 'c3_approved'
        ],
        "station_uuid": ["123", "123", "456", "789", "789", "1001"],
        "station_id_upload": ["1", "1", "4", "7", "7", "11"],
        "network_provider_upload": ["123","123", "456", "789", "789", "1001"],
        "favorite_color": [
            "red", "orange", "yellow", "green", "blue", "purple"
        ]
    })

    response = check_constraints_in_data(
        df=df, unique_constraint=['station_uuid'], feature_toggle_set={}
    )
    conditions = get_constraints_conditions(
        log_event=MagicMock(),
        submission_upload_id='a1_draft',
        constraints=response
    )
    assert len(conditions) == 2

    assert conditions[0]['error_description'] == ErrorReportMessages.DUPLICATE_RECORD_IN_SAME_UPLOAD.format(fields=['station_id=1', 'network_provider=123'])
    assert conditions[1]['error_description'] == ErrorReportMessages.DUPLICATE_RECORD_IN_SYSTEM.format(upload_id={'b2_submitted'}, fields=['station_id=7', 'network_provider=789'])

def test_constraints_conditions_ft_network_provider_true():
    df = pandas.DataFrame(data={
        "upload_id": [
            'a1_draft', 'a1_draft', 'a1_draft',
            'a1_draft', 'b2_submitted', 'c3_approved'
        ],
        "station_uuid": ["123", "123", "456", "789", "789", "1001"],
        "station_id_upload": ["1", "1", "4", "7", "7", "11"],
        "network_provider_upload": ["np1", "np1", "np2", "np3", "np3", "np4"],
        "favorite_color": [
            "red", "orange", "yellow", "green", "blue", "purple"
        ]
    })

    response = check_constraints_in_data(
        df=df,
        unique_constraint=['station_uuid'],
        feature_toggle_set={}
    )
    conditions = get_constraints_conditions(
        log_event=MagicMock(),
        submission_upload_id='a1_draft',
        constraints=response
    )
    assert len(conditions) == 2
    assert conditions[0]['error_description'] == \
        ErrorReportMessages.DUPLICATE_RECORD_IN_SAME_UPLOAD.format(
            fields=['station_id=1', 'network_provider=np1']
        )
    assert conditions[1]['error_description'] == \
        ErrorReportMessages.DUPLICATE_RECORD_IN_SYSTEM.format(
            upload_id={'b2_submitted'},
            fields=['station_id=7', 'network_provider=np3']
        )


def test_check_constraints_pass():
    df = pandas.DataFrame(data={
        "upload_id": [
            'a1_draft', 'a1_draft', 'a1_draft',
            'a1_draft', 'b2_submitted', 'c3_approved'
        ],
        "station_uuid": ["123", "234", "456", "789", "888", "1001"],
        "station_id_upload": ["1", "1", "4", "7", "7", "11"],
        "network_provider_upload": ["np1", "np1", "np2", "np3", "np3", "np4"],
        "favorite_color": [
            "red", "orange", "yellow", "green", "blue", "purple"
        ]
    })

    response = check_constraints_in_data(
        df=df, unique_constraint=['station_uuid'], feature_toggle_set={}
    )

    assert response.empty


@patch.object(
    feature_toggle.FeatureToggleService, "get_feature_toggle_by_enum"
)
@patch('APIPutSubmitModuleData.index.get_module_id')
@patch('module_validation.unique_constraint.execute_query_df')
def test_check_unique_pass(
    mock_execute_query_df,
    mock_get_module_id,
    mock_get_feature_by_enum
):
    mock_get_feature_by_enum.return_value = "True"
    mock_get_module_id.return_value = "9"
    mock_execute_query_df.return_value = pandas.DataFrame(data={
        "upload_id": [
            'a1_draft', 'a1_draft', 'a1_draft',
            'a1_draft', 'b2_submitted', 'c3_approved'
        ],
        "station_uuid": ["123", "234", "456", "789", "888", "1001"],
        "station_id_upload": ["1", "1", "4", "7", "7", "11"],
        "favorite_color": [
            "red", "orange", "yellow", "green", "blue", "purple"
        ]
    })

    assert check_unique_submission(
        cursor=MagicMock(),
        log_event=MagicMock(),
        upload_id="abc123",
        org_id="org456",
        dr_id="dr789",
        feature_toggle_set={}
    )


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIPutSubmitModuleData.index.aurora')
def test_lambda_aurora_exception_500(mock_aurora):
    mock_aurora.get_connection.side_effect = BotoCoreError
    response = api_put_submit_module_data(event, None)
    assert response.get('statusCode') == 500
    assert mock_aurora.get_connection.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch('APIPutSubmitModuleData.index.aurora')
def test_lambda_aurora_exception_raised(mock_aurora):
    mock_aurora.get_connection.side_effect = ZeroDivisionError
    with pytest.raises(ZeroDivisionError):
        api_put_submit_module_data(event, None)


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('APIPutSubmitModuleData.index.get_org_users')
@patch('APIPutSubmitModuleData.index.get_org_info_dynamo')
@patch('APIPutSubmitModuleData.index.execute_query')
@patch('APIPutSubmitModuleData.index.is_user_authorized_to_submit')
@patch('APIPutSubmitModuleData.index.is_valid_upload_id')
@patch("APIPutSubmitModuleData.index.DatabaseCentralConfig")
@patch("APIPutSubmitModuleData.index.aurora")
def test_ft_central_config_true(
    mock_aurora,
    mock_database_central_config,
    mock_valid_upload,
    mock_user_authorized_to_submit,
    mock_execute_query,
    mock_get_org_info_dynamo,
    mock_get_org_users,
    mock_get_active_feature_toggles
):
    # pylint: disable=too-many-positional-arguments
    sr_event = deepcopy(event)
    sr_event['requestContext']['authorizer']['claims']['scope'] = \
        'sub-recipient'
    sr_event["body"] = json.dumps({"upload_id": "123"})

    mock_valid_upload.return_value = True
    mock_user_authorized_to_submit.return_value = {
        "parent_org": "dr123",
        "module_id": "2",
        "updated_by": "System",
        "updated_on": datetime.datetime.now(),
        "year": 2024
    }
    mock_execute_query.return_value = []
    mock_get_active_feature_toggles.return_value = {
        Feature.DATABASE_CENTRAL_CONFIG,
        Feature.DATA_AWAITING_REVIEW_EMAIL
    }
    _ = api_put_submit_module_data(sr_event, None)
    assert mock_database_central_config.called
    assert mock_aurora.get_connection.called
    assert mock_get_org_info_dynamo.called
    assert mock_get_org_users.called


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch.object(
    feature_toggle.FeatureToggleService, "get_active_feature_toggles"
)
@patch('APIPutSubmitModuleData.index.get_org_users')
@patch('APIPutSubmitModuleData.index.get_org_info_dynamo')
@patch('APIPutSubmitModuleData.index.execute_query')
@patch('APIPutSubmitModuleData.index.is_user_authorized_to_submit')
@patch('APIPutSubmitModuleData.index.is_valid_upload_id')
@patch("APIPutSubmitModuleData.index.DatabaseCentralConfig")
@patch("APIPutSubmitModuleData.index.aurora")
def test_ft_central_config_false(
    mock_aurora,
    mock_database_central_config,
    mock_valid_upload,
    mock_user_authorized_to_submit,
    mock_execute_query,
    mock_get_org_info_dynamo,
    mock_get_org_users,
    mock_get_active_feature_toggles
):
    # pylint: disable=too-many-positional-arguments
    sr_event = deepcopy(event)
    sr_event['requestContext']['authorizer']['claims']['scope'] = \
        'sub-recipient'
    sr_event["body"] = json.dumps({"upload_id": "123"})
    mock_valid_upload.return_value = True
    mock_user_authorized_to_submit.return_value = {
        "parent_org": "dr123",
        "module_id": "2",
        "updated_by": "System",
        "updated_on": datetime.datetime.now(),
        "year": 2024
    }
    mock_execute_query.return_value = []
    mock_get_active_feature_toggles.return_value = {
        Feature.DATA_AWAITING_REVIEW_EMAIL
    }
    _ = api_put_submit_module_data(sr_event, None)
    assert not mock_database_central_config.called
    assert mock_aurora.get_connection.called
    assert mock_get_org_info_dynamo.called
    assert mock_get_org_users.called