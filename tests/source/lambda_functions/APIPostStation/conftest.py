import sys
import pytest
from unittest.mock import patch, MagicMock
import os

sys.path.extend(
    [".", "source/lambda_layers/python", "source/lambda_functions"]
)

from database_central_config import DatabaseCentralConfig
from feature_toggle import FeatureToggleService, Feature


@pytest.fixture(scope="module", autouse=True)
def mock_aurora():
    mock_aurora = MagicMock()
    with patch("APIPostStation.index.aurora", return_value= mock_aurora):
        yield mock_aurora


@pytest.fixture(scope="module", autouse=True)
def mock_environment_variables():
    with patch.dict(os.environ, {"ENVIRONMENT": "dev", "AWS_REGION": "us-east-1"}):
        yield


@pytest.fixture(scope="module", autouse=True)
def mock_get_feature_toggles():
    with patch.object(FeatureToggleService, "get_active_feature_toggles") as mock_get_feature_toggles:
        mock_get_feature_toggles.return_value = {Feature.NETWORK_PROVIDER_TABLE, Feature.DATABASE_CENTRAL_CONFIG}
        yield mock_get_feature_toggles


@pytest.fixture(scope="module")
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
