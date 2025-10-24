"""
InfraAPIKeys

Function run from a GitHub Action to generate an API Gateway API key for an organization.
"""
import datetime
import hashlib
import os
from dateutil import tz
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_exceptions import (
    EvChartAPIKeyGenerationError,
    EvChartDatabaseDynamoQueryError,
)
from evchart_helper.api_helper import get_org_info_dynamo
from evchart_helper.s2s_helper import get_environment_name


def handler(event, _context):
    try:
        operation = event.get("operation")
        org_id = event.get("org_id")
        response = {}

        # Get Key value and ID
        if operation in {"Create New Key", "Recreate Key"}:
            org_info = get_org_info_dynamo(org_id)
            # if api key already exists and you aren't recreating the key, raise exception
            if operation != "Recreate Key" and org_info.get("HashedApiKey"):
                raise EvChartAPIKeyGenerationError(message=f"Key already exists for org {org_id}")
            key_id, key_value = create_api_key(org_info)
            response = {"key_id": key_id, "key_value": key_value}
        else:
            key_id = event.get("key_id")
            key_value = get_key_from_secret_manager(org_id)
            response = {"key_id": key_id, "key_value": key_value}

        # add key to usage plan and org
        add_key_to_usage_plan(key_id)
        add_key_to_api_key_table(org_id, key_value)
        return response

    except Exception as e:
        print(f"Exception: {repr(e)}")
        raise EvChartAPIKeyGenerationError(message=f"Error with api key: {e}") from e


def get_usage_plan_id():
    ssm = boto3_manager.client("ssm")

    sub_environment = os.environ.get("SUBENVIRONMENT")
    sub_environment = f"{sub_environment}/" if sub_environment else ""
    usage_plan_id = ssm.get_parameter(Name=f"/ev-chart/{sub_environment}usage-plan-id")[
        "Parameter"
    ]["Value"]

    return usage_plan_id


def create_api_key(org_info):
    apigateway_client = boto3_manager.client("apigateway")
    try:

        response = apigateway_client.create_api_key(
            name=f'Api-Key-{org_info["name"]}',
            description=f'API key for {org_info["name"]}',
            enabled=True,
            generateDistinctId=True,
        )

        key_value = response.get("value")
        key_id = response.get("id")

        # add_key_to_secret_manager(org_info, key_value)
        return key_id, key_value

    except Exception as e:
        raise EvChartAPIKeyGenerationError(f"Error creating API key: {repr(e)}") from e


def add_key_to_secret_manager(org_info, key):
    secret_manager_client = boto3_manager.client("secretsmanager")
    try:
        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_path = f"/{sub_environment}" if sub_environment else ""
        response = secret_manager_client.create_secret(
            Name=f"evchart/api_key{sub_environment_path}/{org_info['org_id']}",
            Description=f'API key for {org_info["name"]}',
            SecretString=key,
        )
        if not response:
            raise EvChartAPIKeyGenerationError(message="Secret unable to be created")
    except Exception as e:
        raise EvChartAPIKeyGenerationError(f"Error adding key to secret manager: {repr(e)}") from e


def get_key_from_secret_manager(org_id):
    secret_manager_client = boto3_manager.client("secretsmanager")
    try:
        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_path = f"/{sub_environment}" if sub_environment else ""
        response = secret_manager_client.get_secret_value(
            SecretId=f"evchart/api_key{sub_environment_path}/{org_id}"
        )
        return response.get("SecretString")
    except Exception as e:
        raise EvChartAPIKeyGenerationError(message="Error retreveing key secret") from e


def add_key_to_usage_plan(key):
    apigateway_client = boto3_manager.client("apigateway")
    try:
        usage_plan_id = get_usage_plan_id()
        usage_response = apigateway_client.create_usage_plan_key(
            usagePlanId=f"{usage_plan_id}", keyId=key, keyType="API_KEY"
        )
        if not usage_response:
            raise EvChartAPIKeyGenerationError(message="Usage plan unable to be assigned")
    except Exception as e:
        raise EvChartAPIKeyGenerationError(message=f"Error creating API key: {repr(e)}") from e

# DELETE after confirmation new way works
def assign_key_to_org(org_id, key_value):
    dynamodb = boto3_manager.resource("dynamodb")
    try:
        hashed_key = hashlib.sha256(key_value.encode()).hexdigest()
        evchart_users_table = dynamodb.Table("ev-chart_org")

        if not evchart_users_table.update_item(
            Key={"org_id": org_id},
            UpdateExpression="set HashedApiKey=:o",
            ExpressionAttributeValues={":o": hashed_key},
            ReturnValues="UPDATED_NEW",
        ):
            raise EvChartDatabaseDynamoQueryError(message="Error querying Dynamo.")
    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(message=f"Err assigning key to {org_id}") from e


def add_key_to_api_key_table(org_id, key_value):
    dynamodb = boto3_manager.resource("dynamodb")
    result = None
    try:
        hashed_key = hashlib.sha256(key_value.encode()).hexdigest()
        evchart_api_key_table = dynamodb.Table("ev-chart_api_key")
        # put_item
        result = evchart_api_key_table.put_item(
            Item={
                "hashed_api_key": hashed_key,
                "environment": get_environment_name(),
                "org_id": org_id,
                "generated_on": str(datetime.datetime.now(tz.gettz("UTC"))),
            }
        )
    except Exception as e:
        raise EvChartDatabaseDynamoQueryError(message="Error adding key to dynamo") from e

    return result
