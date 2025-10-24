"""
APIPostOrg

Takes the provided organization information from the frontend, validates it, and then creates a new
organization and new administrator user for said organization.
"""
from datetime import datetime, UTC
from functools import reduce
import json
import logging
import re
from uuid import uuid4

from boto3.dynamodb.conditions import Attr, Key

from email_handler import trigger_email
from email_handler.email_enums import Email_Template
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseDynamoDuplicateItemError,
    EvChartDatabaseDynamoQueryError,
    EvChartInvalidEmailError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedBodyError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.session import SessionManager
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature

dynamodb_resource = boto3_manager.resource("dynamodb")

logger = logging.getLogger("APIPostOrg")
logger.setLevel(logging.INFO)


def add_org(org_name: str, org_friendly_id: str, org_type: str) -> str:
    org_id = str(uuid4())
    try:
        dynamodb_resource.Table("ev-chart_org").put_item(
            Item={
                "org_id": org_id,
                "name": org_name,
                "org_friendly_id": org_friendly_id,
                "recipient_type": org_type,
            }
        )

    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(message="Error adding organization.") from e

    return org_id


def add_user(first_name: str, last_name: str, email: str, org_id: str) -> None:
    try:
        dynamodb_resource.Table("ev-chart_users").put_item(
            Item={
                "identifier": email.lower(),
                "account_status": "Pending",
                "first_name": first_name,
                "last_generated": str(datetime.now(UTC)),
                "last_name": last_name,
                "org_id": org_id,
                "role": "admin",
            }
        )

    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(message="Error adding user.") from e


def check_organization(org_name: str) -> None:
    response = dynamodb_resource.Table("ev-chart_org").scan(
        FilterExpression=Attr("name").eq(org_name)
    )

    if response["Count"]:
        raise EvChartDatabaseDynamoDuplicateItemError(message="Organization name already exists.")


def check_user(email: str) -> None:
    response = dynamodb_resource.Table("ev-chart_users").query(
        KeyConditionExpression=Key("identifier").eq(email.lower())
    )

    if response["Count"]:
        raise EvChartDatabaseDynamoDuplicateItemError(message="User email already exists.")


def get_next_org_friendly_id() -> str:
    try:
        org_friendly_ids = [
            int(item["org_friendly_id"])
            for item in dynamodb_resource.Table("ev-chart_org").scan(
                ProjectionExpression="org_friendly_id"
            )["Items"] if item.get("org_friendly_id") is not None
        ]

    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(message="Error generating organization ID.") from e

    org_friendly_ids.sort()

    return str(org_friendly_ids[-1] + 1)


def validate_body(request_body: dict, requesting_org_type: str) -> None:
    required_keys = {"email", "first_name", "last_name", "org_name"}

    if requesting_org_type == "joet":
        required_keys.add("org_type")
    else:
        request_body["org_type"] = "sub-recipient"

    # Check that required keys exist in the request body and are not falsy.
    if not reduce(lambda a, b: a and bool(request_body.get(b)), required_keys, True):
        raise EvChartMissingOrMalformedBodyError(message="Missing or malformed parameters.")

    if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", request_body["email"]):
        raise EvChartInvalidEmailError(message="Invalid email format.")


@SessionManager.check_session()
@feature_enablement_check(Feature.ADD_SR_ORG)
def handler(
    event: dict["body": dict],
    _context: dict
) -> dict["body": str, "headers": dict, "statusCode": int]:
    try:
        log_event = LogEvent(event=event, api="APIPostOrg", action_type="write")
        if not log_event.is_auth_token_valid():
            raise EvChartAuthorizationTokenInvalidError()

        if log_event.recipient_type not in ["direct-recipient", "joet"]:
            raise EvChartAuthorizationTokenInvalidError(message="Invalid user organization.")

        request_body = json.loads(event["body"])
        validate_body(request_body, log_event.recipient_type)
        check_organization(request_body["org_name"])
        check_user(request_body["email"])

        org_id = add_org(
            org_name=request_body["org_name"],
            org_friendly_id=get_next_org_friendly_id(),
            org_type=request_body["org_type"],
        )
        add_user(
            first_name=request_body["first_name"],
            last_name=request_body["last_name"],
            email=request_body["email"],
            org_id=org_id,
        )

        trigger_email({
            "email_type": Email_Template.NEW_ORG,
            "email": request_body["email"],
            "creator_org_name": log_event.get_auth_token().get("org_name"),
            "first_name": request_body["first_name"],
            "is_joet": log_event.recipient_type == "joet",
            "last_name": request_body["last_name"],
            "new_org_name": request_body["org_name"],
            "new_org_type": request_body["org_type"],
        })

    except (
        EvChartAuthorizationTokenInvalidError,
        EvChartDatabaseDynamoDuplicateItemError,
        EvChartDatabaseDynamoQueryError,
        EvChartInvalidEmailError,
        EvChartJsonOutputError,
        EvChartMissingOrMalformedBodyError,
    ) as e:
        log_event.log_custom_exception(
            message=e.message,
            status_code=e.status_code,
            log_level=e.log_level
        )
        return_obj = e.get_error_obj()

    else:
        return_obj = {
            "body": json.dumps({"message": "Success."}),
            "headers": {"Access-Control-Allow-Origin": "*"},
            "statusCode" : 200,
        }

    return return_obj
