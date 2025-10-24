from unittest.mock import call, patch

from ScheduledAPIKeyExpirationEmail.index import (
    FIRST_EMAIL_DAYS_UNTIL_EXPIRED,
    SECOND_EMAIL_DAYS_UNTIL_EXPIRED,
    handler,
)


@patch("ScheduledAPIKeyExpirationEmail.index.get_expiring_api_keys")
def test_handler_checks_keys_for_first_and_second_emails(mock_get_api_keys):
    mock_get_api_keys.return_value = None
    handler(None, None)
    assert mock_get_api_keys.call_count == 2
    expected_calls = [call(FIRST_EMAIL_DAYS_UNTIL_EXPIRED), call(SECOND_EMAIL_DAYS_UNTIL_EXPIRED)]
    mock_get_api_keys.has_calls(expected_calls)
