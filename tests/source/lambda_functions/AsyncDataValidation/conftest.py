import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.extend(
    [".", "source/lambda_layers/python", "source/lambda_functions"]
)

import module_validation  # noqa: E402 # pylint: disable=wrong-import-position
from database_central_config import DatabaseCentralConfig


@pytest.fixture(scope="module", autouse=True)
def load_module():
    module_path = Path(
        "./source/lambda_layers/python/module_validation/module_definitions"
    )

    module_validation.load_module_definitions(module_path)



@pytest.fixture(scope="module", autouse=True, name="config")
def config():
    print('using conftests')
    mock_config = DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json"
        )
    )

    # # using patch to mock the call to DatabaseCentralConfig
    with patch("module_validation.DatabaseCentralConfig", return_value=mock_config) as mock_dbcc:
        yield mock_dbcc
