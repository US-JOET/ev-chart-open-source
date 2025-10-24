"""
InfraInitOrganization

[Deprecated, UI-capable] Create a new organzation as part of a GitHub Action.
"""
from uuid import uuid4

from boto3.dynamodb.conditions import Attr, Key
from exceptions import (
    InfraInitOrganizationGenericError
)
from evchart_helper.boto3_manager import boto3_manager

dynamodb_resource = boto3_manager.resource("dynamodb")


def create_organizations(payload: list[dict[str, str]]) -> None:
    table = dynamodb_resource.Table("ev-chart_org")
    org_friendly_id = int(sorted(
        table.scan(
            AttributesToGet=["org_friendly_id"]
        )["Items"] or [{"org_friendly_id": "-1"}],
        key=lambda k: int(k.get("org_friendly_id", "-1"))
    )[-1].get("org_friendly_id", "-1")) + 1

    with table.batch_writer() as batch:
        for org in payload:
            if validate_idempotency(org):
                continue

            org["org_friendly_id"] = str(org_friendly_id)
            org["org_id"] = get_no_collision_uuid()

            batch.put_item(Item=org)

            org_friendly_id += 1


def get_no_collision_uuid() -> str:
    uuid = str(uuid4())
    table = dynamodb_resource.Table("ev-chart_org")

    return get_no_collision_uuid() if table.query(
        KeyConditionExpression=Key("org_id").eq(uuid)
    )["Items"] else uuid


def validate_idempotency(org: dict[str, str]) -> bool:
    # Really just checking if the organization name and recipient type tuple already exists.
    table = dynamodb_resource.Table("ev-chart_org")

    return bool(table.scan(
        FilterExpression=Attr("name").eq(org["name"])
                            & Attr("recipient_type").eq(org["recipient_type"])
    )["Items"])


def validate_payload(payload: list[dict[str, str]]) -> None:
    if not payload:
        raise AttributeError("Invoke event missing required attribute: \"payload\".")

    if not isinstance(payload, list):
        raise TypeError("Payload is not formatted properly; attribute must be a list of dicts.")

    for i, org in enumerate(payload):
        if not isinstance(org, dict):
            raise TypeError(f"Payload is not formatted properly; list item {i} is not a dict.")

        for attribute in ["name", "recipient_type"]:
            if not org.get(attribute):
                raise AttributeError(
                    f"Payload item {i} missing required attribute: \"{attribute}\"."
                )

            if not isinstance(org[attribute], str):
                raise TypeError((
                    f"Payload item {i} \"{attribute}\" invalid; "
                    "attribute must be instance of string."
                ))

        if org["recipient_type"] not in ["direct-recipient", "sub-recipient"]:
            raise ValueError((
                f"Payload item {i} \"recipient_type\" invalid; attribute must be one of: "
                "\"direct-recipient\", \"sub-recipient\"."
            ))


def handler(event: dict, _context: dict) -> None:
    try:
        payload = event.get("payload")
        validate_payload(payload)

        create_organizations(payload)

    except Exception as e:
        raise InfraInitOrganizationGenericError(f"{type(e).__name__}: {str(e)}") from e
