# module paths are set in conftest.py
import pytest
from APIGetDraftOrSubmittedData.index import (  # pylint: disable=import-error
    handler as api_get_draft_or_submitted_data,
)

def test_api_get_draft_or_submitted_data_placeholder():
    with pytest.raises(Exception):
        api_get_draft_or_submitted_data(None, None)
