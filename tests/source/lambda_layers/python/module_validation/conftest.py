import os
from pathlib import Path
import sys
import pytest
from unittest.mock import patch

sys.path.extend(
    [".", "source/lambda_layers/python", "source/lambda_functions"]
)
from database_central_config import DatabaseCentralConfig
import module_validation  # noqa: E402 # pylint: disable=wrong-import-position


@pytest.fixture(scope="module", autouse=True)
def load_module():
    module_path = Path(
        "./source/lambda_layers/python/module_validation/module_definitions"
    )

    module_validation.load_module_definitions(module_path)


@pytest.fixture(scope="module")
def mock_config():
    print('using conftests')
    config = DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json"
        )
    )

    # using patch to mock the call to DatabaseCentralConfig
    with patch("module_validation.DatabaseCentralConfig", return_value=config):
        yield config