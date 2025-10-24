"""
TestUserData

Generate a set of users specified in the ./config that will be used to log into the application
via URL query string.  This login method is only applicable to the Dev and Test AWS accounts and
will not function in the Prod account (Prod and Preprod environments).
"""
from datetime import datetime, UTC
import logging
import os
import random
import string
import urllib3

from config import user_data
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.cognito import cognito

cognito_client = boto3_manager.client("cognito-idp")
dynamodb_resource = boto3_manager.resource("dynamodb")
ssm_client = boto3_manager.client("ssm")
sts_client = boto3_manager.client("sts")

http = urllib3.PoolManager()

logger = logging.getLogger("TestUserData")
logger.setLevel(logging.DEBUG)


def create_users(user_pool_id):
    for user_identity, user_details in user_data.items():
        validate_user_details(user_identity, user_details)
        validate_org_id(user_identity, user_details["org_id"])

        try:
            logger.debug("Creating Cognito user \"%s\"...", user_identity)
            cognito_client.admin_create_user(
                MessageAction="SUPPRESS",
                Username=user_identity,
                UserPoolId=user_pool_id
            )

        except cognito_client.exceptions.UsernameExistsException:
            logger.debug("Cognito user \"%s\" exists; skipping creation.", user_identity)

        logger.debug("Adding user \"%s\" information to DynamoDB.", user_identity)

        user_table = dynamodb_resource.Table("ev-chart_users")
        user_table.put_item(
            Item={
                "account_status": user_details["account_status"],
                "first_name": user_details["first_name"],
                "identifier": user_identity.lower(),
                "last_generated": str(datetime.now(UTC)),
                "last_name": user_details["last_name"],
                "org_id": user_details["org_id"],
                "role": user_details["role"],
            },
        )


def generate_password(length = 12):
    length = max(length, 8)

    symbols = "$-_.!*(),"
    password_chars = string.ascii_letters + string.digits + symbols

    password_data = random.choice(string.digits)
    password_data += random.choice(symbols)
    password_data += random.choice(string.ascii_lowercase)
    password_data += random.choice(string.ascii_uppercase)

    if len(password_data) <= length:
        password_data += "".join(
            random.choice(password_chars) for i in range(length - len(password_data))
        )

    password_list = list(password_data)
    random.shuffle(password_list)

    return "".join(password_list)


def valid_env_for_query_string_login():
    return sts_client.get_caller_identity()["Account"] in [
        "414275662771", #Dev
        "030628784534"  #Test
    ]


def validate_org_id(user_identity, org_id):
    logger.debug("Checking validity of org ID for user \"%s\"...", user_identity)

    org_table = dynamodb_resource.Table("ev-chart_org")
    org_id_valid = bool(org_table.get_item(
        Key={
            "org_id": org_id,
        },
    ).get("Item"))

    if org_id_valid:
        logger.debug("\"%s\" org ID validated.", user_identity)

    else:
        raise RuntimeError(
            f"Failed to validate org ID for user \"{user_identity}\"; org ID not found."
        )


def validate_user_details(user_identity, user_details):
    logger.debug("Checking validity of details for user \"%s\"...", user_identity)

    missing_details = [
        attribute for attribute in [
            attribute if attribute not in user_details else None
            for attribute in ["account_status", "first_name", "last_name", "org_id", "role"]
        ] if attribute is not None
    ]
    if missing_details:
        logger.debug(
            "Failed validating details for user \"%s\".  Missing: %s",
            user_identity,
            missing_details
        )
        raise RuntimeError(
            f"Missing required details for user \"{user_identity}\"; see logs."
        )


def validate_users(user_pool_id):
    sub_environment = os.environ.get("SUBENVIRONMENT")
    sub_environment_path = f"/{sub_environment}" if sub_environment else ""
    environment = sub_environment or os.environ["ENVIRONMENT"]

    api_gateway_id = ssm_client.get_parameter(
        Name=f"/ev-chart/api-gateway{sub_environment_path}/gateway-id"
    )["Parameter"]["Value"]

    for user_identity, user_details in user_data.items():
        new_password = generate_password()

        logger.debug("Setting new password for Cognito user \"%s\".", user_identity)
        cognito_client.admin_set_user_password(
            Password=new_password,
            Permanent=True,
            Username=user_identity,
            UserPoolId=user_pool_id
        )

        logger.debug("Validating user login for \"%s\"...", user_identity)
        response = http.request(
            "GET",
            (
                f"https://{api_gateway_id}.execute-api.{os.environ['AWS_REGION']}.amazonaws.com/"
                f"{environment}/token?username={user_identity}&password={new_password}"
            )
        )

        if response.status != 200:
            logger.debug("Failed user validation.  Response output: %s", response.data)
            raise RuntimeError(f"Failed to validate login for user \"{user_identity}\"; see logs.")

        logger.debug("\"%s\" login validated.", user_identity)
        user_details["password"] = new_password


def handler(_event, _context):
    if not valid_env_for_query_string_login():
        return None

    create_users(cognito.id)
    validate_users(cognito.id)

    return {
        "Users": [
            {
                "Username": user_identity,
                "Password": user_details["password"]
            } for user_identity, user_details in user_data.items()
        ]
    }
