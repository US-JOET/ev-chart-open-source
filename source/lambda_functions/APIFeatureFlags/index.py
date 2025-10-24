"""
APIFeatureFlags

Returns a list of dictionaries that hold the feature toggle name and if that toggle is set
to either True or False.
"""

import json

from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartFeatureStoreConnectionError
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService


@SessionManager.check_session()
def handler(event, _context):
    feature_toggle = FeatureToggleService()
    features = []
    log = LogEvent(event, api="APIFeatureFlags", action_type="READ")
    try:
        features = feature_toggle.get_all_feature_toggles(log)

    except (EvChartFeatureStoreConnectionError,
            EvChartAuthorizationTokenInvalidError
    )as e:
        log.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
        return_obj = e.get_error_obj()
    else:
        log.log_successful_request(
            message="Logging Success Message",
            status_code=200
        )
        return_obj = {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(features),
        }

    return return_obj
