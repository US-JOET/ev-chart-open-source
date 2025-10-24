"""
APIGetStatus

Returns the status of the application. If application is under maintenance,
the maintenance variable is set to True
"""
import json
import logging
import os
# This is a random comment.
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.session import SessionManager

ssm_client = boto3_manager.client("ssm")

logger = logging.getLogger("APIStatus")
logger.setLevel(logging.DEBUG)


def get_application_status():
    sub_environment = os.environ.get("SUBENVIRONMENT")
    sub_environment_path = f"/{sub_environment}" if sub_environment else ""

    return {
        parameter["Name"].rsplit("/", maxsplit=1)[-1]: parameter["Value"]
        for parameter in ssm_client.get_parameters_by_path(
            Path=f"/ev-chart/status{sub_environment_path}"
        )["Parameters"]
    }


@SessionManager.check_session()
def handler(event, _context):
    log_data = {
        "headers": event.get("headers")
    }

    application_status = get_application_status()
    logger.debug(json.dumps(log_data | {
        "status": application_status
    }))

    return {
        "body": json.dumps({
            "maintenance": application_status["maintenance"] == "True"  # convert string to boolean
        }),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        },
        "statusCode": 200
    }
