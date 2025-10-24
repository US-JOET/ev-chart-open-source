import sys
import boto3
import pytest
from unittest.mock import patch, MagicMock
import os
from moto import mock_aws

sys.path.extend(
    [".", "source/lambda_layers/python", "source/lambda_functions"]
)

from database_central_config import DatabaseCentralConfig
from feature_toggle import FeatureToggleService, Feature
from evchart_helper.boto3_manager import Boto3Manager


@pytest.fixture(scope="module", autouse=True)
def mock_aurora():
    mock_aurora = MagicMock()
    with patch("APIPatchStation.index.aurora", return_value= mock_aurora):
        yield mock_aurora


@pytest.fixture(scope="module", autouse=True)
def mock_environment_variables():
    with patch.dict(os.environ, {"ENVIRONMENT": "dev", "AWS_REGION": "us-east-1"}):
        yield


@pytest.fixture(scope="module", autouse=True)
def mock_get_feature_toggles():
    with patch.object(FeatureToggleService, "get_active_feature_toggles") as mock_get_feature_toggles:
        mock_get_feature_toggles.return_value = {
            Feature.NETWORK_PROVIDER_TABLE,
            Feature.DATABASE_CENTRAL_CONFIG
        }
        yield mock_get_feature_toggles


@pytest.fixture(scope="module", autouse=True)
def mock_config():
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


@pytest.fixture(scope="module", autouse=True)
def mock_validate_authorizations():
    with patch("station_validation.validate_authorizations_and_recipient_types.execute_query_fetchone") as mock_validate_authorizations:
        mock_validate_authorizations.return_value = ["11111111-2222-3333-4444-555555555555"]
        yield mock_validate_authorizations


# creating org table fixture
@pytest.fixture(name="_dynamodb_org", autouse=True)
def fixture_dynamodb_org():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[
                {"AttributeName": "org_id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "org_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()

        # inserting Maine DR
        table.put_item(
            Item={
                "org_id": "1",
                "name": "Maine DOT",
                "recipient_type": "direct-recipient",
                "org_friendly_id": "1",
            }
        )

        # inserting Spark09 SR
        table.put_item(
            Item={
                "org_id": "2",
                "name": "Spark09",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "2",
            }
        )

        # inserting Sparkflow SR
        table.put_item(
            Item={
                "org_id": "3",
                "name": "Sparkflow",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "3",
            }
        )

        # inserting Evgo SR
        table.put_item(
            Item={
                "org_id": "4",
                "name": "Evgo",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "4",
            }
        )

        yield dynamodb


@pytest.fixture(name="_mock_boto3_manager")
def fixture_mock_boto3_manager(_dynamodb_org):
    with patch.object(Boto3Manager, "resource", return_value=_dynamodb_org) as mock_client:
        yield mock_client
