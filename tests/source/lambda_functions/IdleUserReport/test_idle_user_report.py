from datetime import datetime, timedelta, UTC
from unittest.mock import patch
from moto import mock_aws
import pytest
import boto3

# module paths are set in conftest.py
from IdleUserReport.index import handler

# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name


def get_ssm_param(ssm_parameter_name):
    session = boto3.Session()
    ssm_client = session.client("ssm")
    param = ssm_client.get_parameter(
        Name=ssm_parameter_name, WithDecryption=True
    )
    return param["Parameter"]["Value"]


@pytest.fixture
def fixture_ssm_base():
    with mock_aws():
        ssm = boto3.client('ssm')
        ssm.put_parameter(
            Name="/ev-chart/dynamodb/table",
            Value="ev-chart_users",
            Type="String"
        )
        yield ssm


@pytest.fixture
def fixture_ssm_idle_60_pending_14(fixture_ssm_base):
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/lambda/idle-user-report/max-idle",
        Value="60",
        Type="String"
    )
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/lambda/idle-user-report/max-pending",
        Value="14",
        Type="String"
    )
    yield fixture_ssm_base


@pytest.fixture
def fixture_ssm_idle_120_pending_14(fixture_ssm_base):
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/lambda/idle-user-report/max-idle",
        Value="120",
        Type="String"
    )
    fixture_ssm_base.put_parameter(
        Name="/ev-chart/lambda/idle-user-report/max-pending",
        Value="14",
        Type="String"
    )
    yield fixture_ssm_base


@pytest.fixture
def fixture_dynamodb_base():
    with mock_aws():
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.create_table(
            TableName='ev-chart_users',
            KeySchema=[{
                'AttributeName': 'identifier',
                'KeyType': 'HASH'
            }],
            AttributeDefinitions=[{
                'AttributeName': 'identifier',
                'AttributeType': 'S'
            }],
            BillingMode="PAY_PER_REQUEST"
        )
        table.wait_until_exists()
        yield dynamodb


@pytest.fixture
def fixture_dynamodb_valid_user(fixture_dynamodb_base):
    table = fixture_dynamodb_base.Table("ev-chart_users")
    table.put_item(
        Item={
            "identifier": "valid_user@driveelectric.gov",
            "last_generated": str(datetime.now(UTC) - timedelta(days=2)),
            "account_status": "Active"
        }
    )
    yield fixture_dynamodb_base


@pytest.fixture
def fixture_dynamodb_idle_user(fixture_dynamodb_base):
    table = fixture_dynamodb_base.Table("ev-chart_users")
    table.put_item(
        Item={
            "identifier": "idle_user@driveelectric.gov",
            "last_generated": str(datetime.now(UTC) - timedelta(days=75)),
            "account_status": "Active"
        }
    )
    yield fixture_dynamodb_base


@pytest.fixture
def fixture_dynamodb_never_logged_user(fixture_dynamodb_base):
    table = fixture_dynamodb_base.Table("ev-chart_users")
    table.put_item(
        Item={
            "identifier": "never_logged_in@driveelectric.gov",
            "account_status": "Pending",
            "last_generated":
                str(datetime.now(UTC) - timedelta(days=20))
        }
    )
    yield fixture_dynamodb_base


@pytest.fixture
def fixture_dynamodb_mixed_users(fixture_dynamodb_valid_user):
    table = fixture_dynamodb_valid_user.Table("ev-chart_users")
    table.put_item(
        Item={
            "identifier": "idle_user@driveelectric.gov",
            "last_generated": str(datetime.now(UTC) - timedelta(days=75)),
            "account_status": "Active"
        }
    )
    yield fixture_dynamodb_valid_user

@patch('IdleUserReport.index.LogEvent')
def test_valid_user_60_days(
    mock_log_event,
    fixture_ssm_base,
    fixture_dynamodb_base,
    fixture_ssm_idle_60_pending_14,
    fixture_dynamodb_valid_user
):
    with (
        patch("IdleUserReport.index.boto3_manager.resource", return_value=fixture_dynamodb_base),
        patch("IdleUserReport.index.boto3_manager.client", return_value=fixture_ssm_base)
    ):
        summary = handler(None, None)
        assert 'expirations' in summary
        assert summary.get('expirations') == []


@patch('IdleUserReport.index.LogEvent')
def test_idle_user_over_60_days(
    mock_log_event,
    fixture_ssm_base,
    fixture_dynamodb_base,
    fixture_ssm_idle_60_pending_14,
    fixture_dynamodb_idle_user
):
    with (
        patch("IdleUserReport.index.boto3_manager.resource", return_value=fixture_dynamodb_base),
        patch("IdleUserReport.index.boto3_manager.client", return_value=fixture_ssm_base)
    ):
        summary = handler(None, None)
        assert 'deactivations' in summary
        assert summary.get('deactivations') == \
            ['idle_user@driveelectric.gov']
        table = fixture_dynamodb_idle_user.Table("ev-chart_users")
        response = table.get_item(
            Key={'identifier': "idle_user@driveelectric.gov"}
        )
        assert response.get('Item', {}).get('account_status') == 'Deactivated'


@patch('IdleUserReport.index.LogEvent')
def test_never_logged_user_over_14_days(
    mock_log_event,
    fixture_ssm_base,
    fixture_dynamodb_base,
    fixture_ssm_idle_60_pending_14,
    fixture_dynamodb_never_logged_user
):
    with (
        patch("IdleUserReport.index.boto3_manager.resource", return_value=fixture_dynamodb_base),
        patch("IdleUserReport.index.boto3_manager.client", return_value=fixture_ssm_base)
    ):
        summary = handler(None, None)
        assert 'expirations' in summary
        assert summary.get('expirations') == \
            ['never_logged_in@driveelectric.gov']
        table =  fixture_dynamodb_never_logged_user.Table("ev-chart_users")
        response = table.get_item(
            Key={'identifier': "never_logged_in@driveelectric.gov"}
        )
        assert response.get('Item', {}).get('account_status') == 'Expired'


@patch('IdleUserReport.index.LogEvent')
def test_user_mix_60_days(
    mock_log_event,
    fixture_ssm_base,
    fixture_dynamodb_base,
    fixture_ssm_idle_60_pending_14,
    fixture_dynamodb_mixed_users
):
    with (
        patch("IdleUserReport.index.boto3_manager.resource", return_value=fixture_dynamodb_base),
        patch("IdleUserReport.index.boto3_manager.client", return_value=fixture_ssm_base)
    ):
        summary = handler(None, None)
        assert 'deactivations' in summary
        assert summary.get('deactivations') == \
            ['idle_user@driveelectric.gov']
        table = fixture_dynamodb_mixed_users.Table("ev-chart_users")
        response = table.get_item(
            Key={'identifier': "idle_user@driveelectric.gov"}
        )
        assert response.get('Item', {}).get('account_status') == 'Deactivated'


@patch('IdleUserReport.index.LogEvent')
def test_user_mix_120_days(
    mock_log_event,
    fixture_ssm_base,
    fixture_dynamodb_base,
    fixture_ssm_idle_120_pending_14,
    fixture_dynamodb_mixed_users
):
    with (
        patch("IdleUserReport.index.boto3_manager.resource", return_value=fixture_dynamodb_base),
        patch("IdleUserReport.index.boto3_manager.client", return_value=fixture_ssm_base)
    ):
        summary = handler(None, None)
        assert 'expirations' in summary
        assert summary.get('expirations') == []
