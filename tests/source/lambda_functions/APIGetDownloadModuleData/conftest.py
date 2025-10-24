import sys
import pytest
from unittest.mock import patch, MagicMock
import os

sys.path.extend(
    [".", "source/lambda_layers/python", "source/lambda_functions"]
)

@pytest.fixture(scope="module", autouse=True)
def mock_aurora():
    mock_aurora = MagicMock()
    with patch("APIGetDownloadModuleData.index.aurora", return_value= mock_aurora):
        yield mock_aurora

@pytest.fixture(scope="module", autouse=True)
def mock_environment_variables():
    with patch.dict(os.environ, {"ENVIRONMENT": "dev", "AWS_REGION": "us-east-1"}):
        yield