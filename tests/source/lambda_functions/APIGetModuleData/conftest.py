# noqa: E402 # pylint: disable=wrong-import-position
import os
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.extend([".", "source/lambda_layers/python", "source/lambda_functions"])

import module_validation
import pytest
from database_central_config import DatabaseCentralConfig



@pytest.fixture(scope="module", autouse=True)
def load_module():
    module_path = Path("./source/lambda_layers/python/module_validation/module_definitions")

    module_validation.load_module_definitions(module_path)


@pytest.fixture(scope="module", autouse=True, name="config")
def config():
    mock_config = DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json",
        )
    )

    # # using patch to mock the call to DatabaseCentralConfig
    with patch(
        "evchart_helper.module_helper.DatabaseCentralConfig", return_value=mock_config
    ) as helper_mock_dbcc, patch(
        "APIGetModuleData.index.DatabaseCentralConfig", return_value=mock_config
    ) as index_mock_dbbc:
        yield (helper_mock_dbcc, index_mock_dbbc)
