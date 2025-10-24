import json
import logging
import os
from unittest.mock import patch
from evchart_helper.custom_exceptions import (
    EvChartDatabaseDynamoQueryError,
    EvChartUserNotAuthorizedError,
    EvChartAuthorizationTokenInvalidError,
    EvChartMissingOrMalformedHeadersError,
)
from evchart_helper.custom_logging import LogEvent


def get_valid_event():
    return {
        "httpMethod": "POST",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
                    "org_friendly_id": "5",
                    "org_name": "Pennsylvania DOT",
                    "email": "direct.recipient@local.env",
                    "scope": "direct-recipient",
                    "name": "John Doe",
                    "role": "admin",
                }
            },
        },
    }


def get_invalid_event():
    return {
        "httpMethod": "Post",
        "requestContext": {
            "authorizer": {
                "claims": {
                    "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
                    "org_friendly_id": "5",
                    "scope": "direct-recipient",
                    "org_name": "Pennsylvania DOT",
                    "preferred_name": " ",
                    "email": "direct.recipient@local.env",
                    "role": "admin",
                }
            }
        },
    }


def get_async_event():
    return {
        "Records": [
            {
                "eventVersion": "2.0",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-1",
                "eventTime": "1970-01-01T00:00:00.000Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {"principalId": "EXAMPLE"},
                "requestParameters": {"sourceIPAddress": "127.0.0.1"},
                "responseElements": {
                    "x-amz-request-id": "EXAMPLE123456789",
                    "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH",
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "testConfigRule",
                    "bucket": {
                        "name": f"evchart_bucket",
                        "ownerIdentity": {"principalId": "EXAMPLE"},
                        "arn": "arn:aws:s3:::DOC-EXAMPLE-BUCKET",
                    },
                    "object": {
                        "key": f"upload/Joint+Office/123.csv",
                        "size": 1024,
                        "eTag": "0123456789abcdef0123456789abcdef",
                        "sequencer": "0A1B2C3D4E5F678901",
                    },
                },
            }
        ]
    }


@patch.dict(os.environ, {"ENVIRONMENT": "dev"})
def test_creating_log_object():
    # log setup
    event = get_valid_event()
    log = LogEvent(event, api="APIPostUser", action_type="Create")

    # expected_log is what will be logged when obj is first created
    log_event = log.get_log_obj()
    expected_log = {
        "application": "EV-ChART",
        "log_level": 6,
        "api": "APIPostUser",
        "action_type": "CREATE",
        "message": "API Invocation",
        "operation": "APIPostUser",
        "status_code": None,
        "module_info": None,
        "method": "POST",
        "user_name": "direct.recipient@local.env",
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "org_friendly_id": "5",
        "org_name": "Pennsylvania DOT",
        "recipient_type": "direct-recipient",
        "role": "admin",
        # 'environment': 'development',
        "environment": "dev",
        "valid_auth_token": True,
        "name": "John Doe",
        "result": "SUCCESS",
    }

    assert log_event == expected_log


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_log_successful_request():
    # log setup
    event = get_valid_event()
    log = LogEvent(event, api="APIPostUser", action_type="Create")

    # call when request is successful
    log.log_successful_request("Logging Success Message", 200, "Module3, quarter2")
    log_event = log.get_log_obj()

    # fields changed: message, status_code, module_info
    expected_log = {
        "application": "EV-ChART",
        "log_level": 6,
        "api": "APIPostUser",
        "action_type": "CREATE",
        "message": "Logging Success Message",
        "operation": "APIPostUser",
        "status_code": 200,
        "module_info": "Module3, quarter2",
        "method": "POST",
        "user_name": "direct.recipient@local.env",
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "org_friendly_id": "5",
        "org_name": "Pennsylvania DOT",
        "recipient_type": "direct-recipient",
        "role": "admin",
        "environment": "qa",
        "valid_auth_token": True,
        "name": "John Doe",
        "result": "SUCCESS",
    }

    assert log_event == expected_log


@patch.dict(os.environ, {"ENVIRONMENT": "prod"})
def test_get_auth_token():
    # log setup
    event = get_valid_event()
    log = LogEvent(event, api="APIPostUser", action_type="Create")
    auth_token = log.get_auth_token()

    expected_auth_token = {
        "email": "direct.recipient@local.env",
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "org_friendly_id": "5",
        "org_name": "Pennsylvania DOT",
        "recipient_type": "direct-recipient",
        "name": "John Doe",
        "role": "admin",
    }

    assert auth_token == expected_auth_token


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
def test_EvChartDatabaseDynamoQueryError():
    # log setup
    event = get_valid_event()
    log = LogEvent(event, api="APIPostUser", action_type="Create")

    # throwing an error
    try:
        # dummy code so that it enters the except block
        _ = event["scope"]

    except KeyError:
        err = EvChartDatabaseDynamoQueryError(message="Could not insert into dynamo table")

        # VERIFYING OUTCOME OF ERROR OBJ (used to return to FE)
        err_obj = err.get_error_obj()
        expected_err_obj = {
            "statusCode": 500,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": (
                '"EvChartDatabaseDynamoQueryError raised. ' 'Could not insert into dynamo table"'
            ),
        }

        assert err_obj == expected_err_obj

    # VERIFYING OUTCOME OF LOG OBJ
    log.log_custom_exception(
        message=err.message,
        status_code=err.status_code,
        log_level=err.log_level,
    )

    log_event = log.get_log_obj()
    expected_log = {
        "application": "EV-ChART",
        "log_level": 3,
        "api": "APIPostUser",
        "action_type": "CREATE",
        "message": (
            "EvChartDatabaseDynamoQueryError raised. " "Could not insert into dynamo table"
        ),
        "operation": "APIPostUser",
        "status_code": 500,
        "module_info": None,
        "method": "POST",
        "user_name": "direct.recipient@local.env",
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "org_friendly_id": "5",
        "org_name": "Pennsylvania DOT",
        "recipient_type": "direct-recipient",
        "role": "admin",
        "environment": "test",
        "valid_auth_token": True,
        "name": "John Doe",
        "result": "FAILURE",
    }

    assert log_event == expected_log


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "preprod"})
def test_EvChartUserNotAuthorizedError():
    # log setup
    event = get_valid_event()
    log = LogEvent(event, api="APIPostUser", action_type="Create")

    # throwing an error
    scope = "SR"
    if scope == "DR":
        # return True
        err = None
        assert True
    else:
        err = EvChartUserNotAuthorizedError()
        log.log_custom_exception(
            message=err.message, status_code=err.status_code, log_level=err.log_level
        )

    # VERIFY ERROR OBJ
    err_obj = err.get_error_obj()
    expected_err_obj = {
        "statusCode": 403,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": '"EvChartUserNotAuthorizedError raised. "',
    }

    assert err_obj == expected_err_obj

    # VERIFYING LOG OBJ
    # fields changed in log obj: log_level, message, status_code,
    log_event = log.get_log_obj()
    expected_log = {
        "application": "EV-ChART",
        "log_level": 4,
        "api": "APIPostUser",
        "action_type": "CREATE",
        "message": "EvChartUserNotAuthorizedError raised. ",
        "operation": "APIPostUser",
        "status_code": 403,
        "module_info": None,
        "method": "POST",
        "user_name": "direct.recipient@local.env",
        "org_id": "3824c24b-f4fa-44bb-b030-09e99c3e4b6c",
        "org_friendly_id": "5",
        "org_name": "Pennsylvania DOT",
        "recipient_type": "direct-recipient",
        "role": "admin",
        "environment": "preprod",
        "valid_auth_token": True,
        "name": "John Doe",
        "result": "FAILURE",
    }

    assert log_event == expected_log


def test_EvChartAuthorizationTokenInvalidError():
    # log setup
    invalid_event = get_invalid_event()
    try:
        log = LogEvent(invalid_event, api="APIPostUser", action_type="Create")

        if log.is_auth_token_valid() is False:
            raise EvChartAuthorizationTokenInvalidError()

    except EvChartAuthorizationTokenInvalidError as e:
        log.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
        )

    log_obj = log.get_log_obj()
    assert log_obj.get("log_level") == 4
    assert log_obj.get("status_code") == 401
    assert log_obj.get("message") == "EvChartAuthorizationTokenInvalidError raised. "


def test_EvChartMissingOrMalformedHeadersError():
    # log setup
    event = get_valid_event()
    try:
        log = LogEvent(event, api="Test", action_type="Create")
        raise EvChartMissingOrMalformedHeadersError()

    except EvChartMissingOrMalformedHeadersError as e:
        log.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
        )

    log_obj = log.get_log_obj()
    assert log_obj.get("log_level") == 4
    assert log_obj.get("status_code") == 400
    assert log_obj.get("message") == "EvChartMissingOrMalformedHeadersError raised. "


@patch.dict(os.environ, {"ENVIRONMENT": "test"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "qa"})
def test_log_info_with_async_event(caplog):
    # log setup
    event = get_async_event()
    log = LogEvent(event, api="APIPostUser", action_type="Create")

    # fields changed: message, status_code, module_info
    expected_log = {
        "application": "EV-ChART",
        "log_level": 20,
        "api": "APIPostUser",
        "action_type": "CREATE",
        "message": "This is just info",
        "operation": "APIPostUser",
        "status_code": None,
        "module_info": None,
        "environment": "qa",
        "valid_auth_token": False,
    }

    # call when request is successful
    with caplog.at_level(logging.INFO):
        log.log_info("This is just info")
        called_message = caplog.messages[0]
        called_json = json.loads(called_message)
        assert expected_log == called_json

@patch.dict(os.environ, {"ENVIRONMENT": "prod"})
@patch.dict(os.environ, {"SUBENVIRONMENT": "preprod"})
def test_log_debug_with_async_event(caplog):
    # log setup
    event = get_async_event()
    log = LogEvent(event, api="APIPostUser", action_type="Create")

    # fields changed: message, status_code, module_info
    expected_log = {
        "application": "EV-ChART",
        "log_level": 10,
        "api": "APIPostUser",
        "action_type": "CREATE",
        "message": "This is just info",
        "operation": "APIPostUser",
        "status_code": None,
        "module_info": None,
        "environment": "preprod",
        "valid_auth_token": False,
    }

    logger = log.get_logger()
    logger.setLevel(logging.DEBUG)
    # call when request is successful
    with caplog.at_level(logging.DEBUG):
        log.log_debug("This is just info")
        called_message = caplog.messages[0]
        called_json = json.loads(called_message)
        assert expected_log == called_json
