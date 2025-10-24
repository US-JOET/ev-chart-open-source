from datetime import datetime
import json
from unittest.mock import patch
import os

from APIGetReportingYears.index import handler as api_get_reporting_years
from evchart_helper.custom_exceptions import EvChartDatabaseAuroraQueryError

event = {
    "headers": {},
    "httpMethod": "MODIFY",
    "requestContext": {
        "accountId": "414275662771",
        "authorizer": {
            "claims": {
                "org_id": "123",
                "org_friendly_id": "1",
                "org_name": "New York DOT",
                "email": "dev@ee.doe.gov",
                "scope": "direct-recipient",
                "preferred_name": "",
                "role": "admin",
            }
        },
    },
}


# 200, valid response
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetReportingYears.index.datetime")
def test_valid_200(mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 4, 14, 12, 0, 0)
    expected_results = [{"year": "2025"}, {"year": "2024"}, {"year": "2023"}]
    users_response = api_get_reporting_years(event, None)
    assert users_response.get("statusCode") == 200
    body = json.loads(users_response.get("body"))
    assert body == expected_results


# 500, EvChartDatabaseAuroraQueryError
@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
@patch("APIGetReportingYears.index.get_years")
def test_lambda_invalid_aurora_500(mock_get_years):
    mock_get_years.side_effect = EvChartDatabaseAuroraQueryError

    response = api_get_reporting_years(event, None)
    assert response.get("statusCode") == 500
