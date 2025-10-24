from pathlib import Path
import sys
import pytest

sys.path.extend(
    [".", "source/lambda_layers/python", "source/lambda_functions"]
)
import module_validation  # noqa: E402 # pylint: disable=wrong-import-position


@pytest.fixture(scope="module", autouse=True)
def load_module():
    module_path = Path(
        "./source/lambda_layers/python/module_validation/module_definitions"
    )

    module_validation.load_module_definitions(module_path)
