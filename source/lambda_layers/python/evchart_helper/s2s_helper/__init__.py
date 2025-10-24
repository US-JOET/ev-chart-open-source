"""
evhcart_helper.s2s_helper

Holds the helper functions that support the system to system upload feature,
so that module data can be submitted through an API
"""

from datetime import datetime, timedelta, UTC
import hashlib
import os

from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import NoCredentialsError
from evchart_helper import boto3_manager
from evchart_helper.custom_exceptions import EvChartDynamoConnectionError, EvChartInvalidAPIKey

API_KEY_EXPIRATION_DAYS = 90


def get_api_key_from_event(event):
    """
    Returns API key from event headers or errors.
    """
    api_key = None
    try:
        headers = event["headers"]
        api_key = headers["x-api-key"]
    except Exception as e:
        raise EvChartInvalidAPIKey(message="missing api key") from e

    return api_key


def get_hash_from_api_key(api_key):
    """
    Returns encoded hashed api key as string
    that only contains hexadecimal digits
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


def get_org_by_api_key(api_key):
    """
    Returns org_id given api_key, parent function
    for two methods of retrieving
    """
    hashed_api_key = get_hash_from_api_key(api_key)
    try:
        org_id = get_org_from_api_key_info(hashed_api_key)
    except EvChartInvalidAPIKey:
        # if not found in new table try old way of searching
        org_id = get_org_from_hash_handler(hashed_api_key)
    return org_id


def get_org_from_hash_handler(hashed_api_key):
    """
    Returns org_id or error based off scan,
    given hashed_api_key
    """
    response = scan_org_by_hashed_key(hashed_api_key)

    if response is not None:
        if "org_id" in response:
            org_id = response["org_id"]
            return org_id
        # return friendly name

    raise EvChartInvalidAPIKey(message="No organization associated with given api key")


def get_org_from_api_key_info(hashed_api_key):
    """
    Returns org_id based off Dynamo query,
    given hashed api key
    """
    response = get_hashed_api_key_info(hashed_api_key)

    if response is not None:
        if "org_id" in response:
            org_id = response["org_id"]
            return org_id
        # return friendly name

    raise EvChartInvalidAPIKey(message="No organization associated with given api key")


def get_hashed_api_key_info(hashed_api_key):
    """
    Returns all fields from Dynamo DB api key
    table given hashed api key
    """
    try:
        dynamodb = boto3_manager.resource("dynamodb")
        table = dynamodb.Table("ev-chart_api_key")
        environment_name = get_environment_name()
        response = table.query(
            KeyConditionExpression=Key("hashed_api_key").eq(hashed_api_key)
            & Key("environment").eq(environment_name)
        )

        items = response["Items"]
        result = None
        if len(items) > 0:
            result = items[0]
    except NoCredentialsError as e:
        raise EvChartDynamoConnectionError(message="issue verifying api key") from e
    return result


def check_valid_api_key(api_key):
    """
    Validates that the api key has not expired.
    """
    response = get_hashed_api_key_info(get_hash_from_api_key(api_key))
    generated_on = response and response.get("generated_on")

    if generated_on:
        generated_on = datetime.fromisoformat(generated_on)
        if datetime.now(UTC) - generated_on > timedelta(days=API_KEY_EXPIRATION_DAYS):
            raise EvChartInvalidAPIKey(message="Api key has expired.")


def scan_org_by_hashed_key(hashed_api_key):
    """
    Returns all fields from Dynamo DB org table
    based off given hashed api key
    """
    items = []
    try:
        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_name = f"_{sub_environment}" if sub_environment else ""
        column_name = "HashedApiKey" + sub_environment_name
        dynamodb = boto3_manager.resource("dynamodb")
        table = dynamodb.Table("ev-chart_org")
        response = table.scan(FilterExpression=Attr(column_name).eq(str(hashed_api_key)))
        items = response.get("Items")
        item = None
        if len(items) > 0:
            item = items[0]
    except NoCredentialsError as e:
        raise EvChartDynamoConnectionError(
            message=f"scan_org_by_hashed_key ran into an issue using hash {hashed_api_key}"
        ) from e

    return item


def get_environment_name():
    """
    Returns environment name
    """
    env_name = os.environ.get("ENVIRONMENT")
    sub_env_name = os.environ.get("SUBENVIRONMENT")
    return f"{sub_env_name}" if sub_env_name else env_name


# To find the day it expires add 1 to the API_KEY_EXPIRATION_DAYS
def get_expiring_api_keys(days_until_expired):
    date_key_expires = datetime.now(UTC) + timedelta(days=days_until_expired)
    # include extra day due to > instead of >=
    generated_on_target_date = (
        date_key_expires - timedelta(days=(API_KEY_EXPIRATION_DAYS + 1))
    ).date()

    try:
        dynamodb = boto3_manager.resource("dynamodb")
        table = dynamodb.Table("ev-chart_api_key")
        environment_name = get_environment_name()

        response = table.scan(
            FilterExpression=Attr("environment").eq(environment_name)
            & Attr("generated_on").begins_with(str(generated_on_target_date)),
        )

        items = response["Items"]
        result = None
        if len(items) > 0:
            result = items
    except NoCredentialsError as e:
        raise EvChartDynamoConnectionError(message="issue verifying api key") from e
    return result

# TODO: handle pagination in scan
def get_keys_by_org(org_id):
    try:
        dynamodb = boto3_manager.resource("dynamodb")
        table = dynamodb.Table("ev-chart_api_key")
        environment_name = get_environment_name()
        response = table.scan(
            FilterExpression=Attr("org_id").eq(org_id)
            & Attr("environment").eq(environment_name)
        )

        items = response["Items"]
        result = None
        if len(items) > 0:
            result = items
    except NoCredentialsError as e:
        raise EvChartDynamoConnectionError(message="issue verifying api key") from e
    return result

def get_newest_api_key(org_id):
    list_of_api_keys = get_keys_by_org(org_id)

    newest = None
    if list_of_api_keys:
        newest = list_of_api_keys[0]
        for key_object in list_of_api_keys:
            if newest["generated_on"] < key_object["generated_on"]:
                newest = key_object

    return newest
