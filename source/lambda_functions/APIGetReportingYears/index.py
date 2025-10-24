"""
APIGetReportingYears

Return a list of valid years that have had data being reported for a particular organization to the
frontend for display purposes.
"""

import json
from datetime import datetime, timezone

from evchart_helper.api_helper import get_available_years
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError, EvChartDatabaseAuroraQueryError)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.session import SessionManager

import_metadata = ModuleDataTables["Metadata"].value


@SessionManager.check_session()
def handler(event, _context):
    todays_date = datetime.now(timezone.utc).date()
    try:
        log_event = LogEvent(event, api="APIGetReportingYears", action_type="Read")
        if log_event.is_auth_token_valid() is False:
            raise EvChartAuthorizationTokenInvalidError()
        output = {}

        output = get_years(todays_date)

    except (EvChartAuthorizationTokenInvalidError, EvChartDatabaseAuroraQueryError) as err:
        log_event.log_custom_exception(
            message=err.message, status_code=err.status_code, log_level=err.log_level
        )
        return_obj = err.get_error_obj()

    else:
        log_event.log_successful_request(
            message="Successfully retrieved Reporting Years", status_code=200
        )
        return_obj = {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps(output),
        }

    return return_obj


def get_years(todays_date):
    years = get_available_years(todays_date)

    result = []
    for year in years:
        result.append({"year": year})

    return result
