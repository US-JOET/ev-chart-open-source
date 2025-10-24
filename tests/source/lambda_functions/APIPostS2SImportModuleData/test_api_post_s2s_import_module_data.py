# pylint: disable=C0301
import datetime
import json
from unittest.mock import patch

import boto3
import pytest
import feature_toggle
from APIPostS2SImportModuleData.index import (
    build_s3_metadata,
    get_api_key_from_event,
    get_file_with_path,
    get_org_id_from_friendly_id,
    handler,
    is_valid_direct_recipient_id,
    is_valid_module_id,
    is_valid_module_year,
    is_valid_quarter,
    module_requires_quarter,
    sr_can_submit_to_dr,
    validate_body,
    validate_email_is_associated_with_active_user_in_org,
)

from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import (
    EvChartDynamoConnectionError,
    EvChartInvalidAPIKey,
)
from moto import mock_aws


@pytest.fixture(name="dynamodb_tables")
def fixture_dynamodb_tables():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        org_table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[{"AttributeName": "org_id", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "org_id", "AttributeType": "S"},
                {"AttributeName": "recipient_type", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi_recipient_type",
                    "KeySchema": [{"AttributeName": "recipient_type", "KeyType": "HASH"}],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        org_table.wait_until_exists()

        # inserting Maine DR
        org_table.put_item(
            Item={
                "org_id": "123-456",
                "name": "Maine DOT",
                "org_friendly_id": "123",
                "recipient_type": "direct-recipient",
            }
        )

        org_table.put_item(
            Item={
                "org_id": "111-222",
                "name": "API Client",
                "org_friendly_id": "111",
                "recipient_type": "sub-recipient",
                "HashedApiKey": "123",
            }
        )

        user_table = dynamodb.create_table(
            TableName="ev-chart_users",
            KeySchema=[{"AttributeName": "identifier", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "identifier", "AttributeType": "S"},
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "org_id", "AttributeType": "S"},
            ],
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "gsi_org_id",
                    "KeySchema": [
                        {"AttributeName": "org_id", "KeyType": "HASH"},
                        {"AttributeName": "identifier", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                },
                {
                    "IndexName": "gsi_session_id",
                    "KeySchema": [{"AttributeName": "session_id", "KeyType": "HASH"}],
                    "Projection": {
                        "ProjectionType": "INCLUDE",
                        "NonKeyAttributes": ["refresh_token"],
                    },
                },
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        user_table.wait_until_exists()

        user_table.put_item(
            Item={
                "identifier": "ev-chart-user@ee.doe.gov",
                "account_status": "Active",
                "first_name": "Jane",
                "last_generated": str(datetime.datetime.now()),
                "last_name": "Doe",
                "org_id": "111-222",
            }
        )

        user_table.put_item(
            Item={
                "identifier": "expired@gmail.com",
                "account_status": "Deactivated",
                "first_name": "John",
                "last_generated": str(datetime.datetime.now()),
                "last_name": "Doe",
                "org_id": "111-222",
            }
        )

        user_table.put_item(
            Item={
                "identifier": "MaineDot@gmail.com",
                "account_status": "Active",
                "first_name": "DR",
                "last_generated": str(datetime.datetime.now()),
                "last_name": "Org",
                "org_id": "123-456",
            }
        )

        yield dynamodb


@pytest.fixture(name="_mock_boto3_manager")
def mock_boto3_manager(dynamodb_tables):
    with patch.object(Boto3Manager, "resource", return_value=dynamodb_tables) as mock_resource:
        yield mock_resource


@pytest.fixture(name="ssm_client")
def ssm_client_fixture():
    with mock_aws():
        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(Name="/ev-chart/features/s2s", Value="True", Type="String")
        yield ssm_client


@pytest.fixture(name="_mock_boto3_client_manager")
def mock_boto3_client_manager(ssm_client):
    with patch.object(Boto3Manager, "client", return_value=ssm_client) as mock_client:
        yield mock_client


@pytest.fixture(name="ssm_client_no_feature")
def ssm_client_fixture_no_feature():
    with mock_aws():
        ssm_client = boto3.client("ssm")
        yield ssm_client


@pytest.fixture(name="_mock_boto3_client_manager_no_feature")
def mock_boto3_client_manager_no_feature(ssm_client_no_feature):
    with patch.object(Boto3Manager, "client", return_value=ssm_client_no_feature) as mock_client:
        yield mock_client


@pytest.fixture(name="ssm_client_false_feature")
def ssm_client_fixture_false_feature():
    with mock_aws():
        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(Name="/ev-chart/features/s2s", Value="False", Type="String")
        yield ssm_client


@pytest.fixture(name="_mock_boto3_client_manager_false_feature")
def mock_boto3_client_manager_false_feature(ssm_client_false_feature):
    with patch.object(Boto3Manager, "client", return_value=ssm_client_false_feature) as mock_client:
        yield mock_client


VALID_CHECKSUM = "0d810e7fbf2f435b93a7b51d26e7df28e3b8747a322a33dcf2a4db8dbae63ce0"


def test_get_api_key_from_event_returns_key():
    api_key = 123
    event = {"headers": {"x-api-key": api_key}}
    result = get_api_key_from_event(event)
    assert result == api_key


def test_get_api_key_from_event_throws_auth_error_if_key_not_found():
    event = {"headers": {"Token": "something"}}
    with pytest.raises(EvChartInvalidAPIKey) as raised_error:
        get_api_key_from_event(event)
    assert "missing api key" in raised_error.value.message


def test_validate_body_given_valid_body_return_true(_mock_boto3_manager):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert len(result) is 0


def test_validate_body_given_no_checksum_return_false(_mock_boto3_manager):
    body = {
        "module_id": "5",
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert "missing required field: checksum" in result


def test_validate_body_given_no_module_id_return_false(_mock_boto3_manager):
    body = {
        "checksum": VALID_CHECKSUM,
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert "missing required field: module_id" in result


def test_validate_body_given_no_year_return_false(_mock_boto3_manager):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert "missing required field: year" in result


def test_validate_body_given_no_direct_recipient_id_return_false():
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "year": "2024",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert "missing required field: direct_recipient_id" in result


def test_validate_body_given_no_email_return_false(_mock_boto3_manager):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "year": "2024",
        "direct_recipient_id": "123",
    }
    result = validate_body(body)

    assert "missing required field: email" in result


def test_validate_body_given_no_quarter_in_module_that_does_not_require_a_quarter_return_no_error(
    _mock_boto3_manager,
):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert len(result) is 0


def test_validate_body_given_quarter_for_module_that_does_not_require_a_quarter_return_error_string(
    _mock_boto3_manager,
):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
        "quarter": "1",
    }
    result = validate_body(body)

    assert len(result) is 1


def test_validate_body_given_blank_quarter_in_module_that_does_not_require_a_quarter_return_no_error(
    _mock_boto3_manager,
):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
        "quarter": "",
    }
    result = validate_body(body)

    assert len(result) == 0


def test_validate_body_given_no_quarter_in_module_that_does_require_a_quarter_return_error_string(
    _mock_boto3_manager,
):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "2",
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert "missing required field: quarter" in result


def test_validate_body_given_invalid_quarter_in_module_that_does_require_a_quarter_return_error_string(
    _mock_boto3_manager,
):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "2",
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
        "quarter": "r",
    }
    result = validate_body(body)

    assert len(result) > 0


def test_validate_body_given_invalid_checksum_return_false(_mock_boto3_manager):
    body = {
        "checksum": "1",
        "module_id": "5",
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    # assert "checksum must be a SHA256 hash" in result
    assert "invalid checksum" in result[0]


def test_validate_body_given_invalid_year_return_false(_mock_boto3_manager):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "year": "abcd",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert "invalid year of" in result[0]


def test_validate_body_given_invalid_module_id_return_false(_mock_boto3_manager):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "12",
        "year": "2024",
        "direct_recipient_id": "123",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert "invalid module_id" in result[0]


def test_validate_body_given_invalid_direct_recipient_id_return_false(_mock_boto3_manager):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "year": "2024",
        "direct_recipient_id": "-12",
        "email": "ev-chart-user@ee.doe.gov",
    }
    result = validate_body(body)

    assert "invalid direct_recipient_id" in result[0]


def test_validate_body_given_invalid_email_return_false(_mock_boto3_manager):
    body = {
        "checksum": VALID_CHECKSUM,
        "module_id": "5",
        "year": "2024",
        "direct_recipient_id": "2",
        "email": "123 gmail com",
    }
    result = validate_body(body)

    assert "invalid email" in result[0]


@pytest.mark.parametrize(
    "module_id,expected_result",
    [
        ("2", True),
        ("3", True),
        ("4", True),
        ("5", False),
        ("6", False),
        ("7", False),
        ("8", False),
        ("9", False),
    ],
)
def test_module_requires_quarter_given_id_returns_bool(module_id, expected_result):
    result = module_requires_quarter(module_id)
    assert expected_result is result


@pytest.mark.parametrize(
    "year, expected_result",
    [
        ("2023", True),
        ("2024", True),
        ("abcd", False),
        ("2a23", False),
        # ("2020", False)
    ],
)
def test_is_valid_module_year(year, expected_result):
    result = is_valid_module_year(year)
    assert result == expected_result


@pytest.mark.parametrize(
    "quarter, expected_result",
    [("1", True), ("2", True), ("3", True), ("4", True), ("2023", False), ("a", False)],
)
def test_is_valid_quarter(quarter, expected_result):
    result = is_valid_quarter(quarter)
    assert result == expected_result


@pytest.mark.parametrize(
    "module_id, expected_result",
    [
        ("1", False),
        ("2", True),
        ("3", True),
        ("4", True),
        ("5", True),
        ("6", True),
        ("7", True),
        ("8", True),
        ("9", True),
        ("2", True),
        ("2023", False),
        ("a", False),
    ],
)
def test_is_valid_module_id(module_id, expected_result):
    result = is_valid_module_id(module_id)
    assert result == expected_result


def test_build_s3_metadata():
    checksum = "1"
    recipient_type = "sub-recipient"
    s2s_upload = True
    metadata_args = {
        "checksum": checksum,
        "recipient_type": recipient_type,
        "s2s_upload": s2s_upload,
    }
    result = build_s3_metadata(metadata_args)

    assert "x-amz-meta-checksum" in result
    assert "x-amz-meta-recipient_type" in result
    assert "x-amz-meta-s2s_upload" in result

    assert result["x-amz-meta-checksum"] == checksum
    assert result["x-amz-meta-recipient_type"] == recipient_type
    assert result["x-amz-meta-s2s_upload"] == s2s_upload


def test_validate_email_is_associated_with_active_user_in_org_given_exists_return_true(
    _mock_boto3_manager,
):
    email = "ev-chart-user@ee.doe.gov"
    org_id = "111-222"
    result = validate_email_is_associated_with_active_user_in_org(email, org_id)
    assert True is result


def test_validate_email_is_associated_with_active_user_in_org_given_does_not_exists_return_false(
    _mock_boto3_manager,
):
    email = "not-real-email@gmail.com"
    org_id = "111"
    result = validate_email_is_associated_with_active_user_in_org(email, org_id)
    assert False is result


def test_validate_email_is_associated_with_active_user_in_org_given_exists_but_expired_return_false(
    _mock_boto3_manager,
):
    email = "expired@gmail.com"
    org_id = "111"
    result = validate_email_is_associated_with_active_user_in_org(email, org_id)
    assert False is result


def test_validate_email_is_associated_with_active_user_in_org_given_exists_but_not_in_org_false(
    _mock_boto3_manager,
):
    email = "MaineDot@gmail.com"
    org_id = "111"
    result = validate_email_is_associated_with_active_user_in_org(email, org_id)
    assert False is result


def test_validate_email_is_associated_with_active_user_in_org_raises_error_when_dynamo_connection_fails():
    email = "not-real-email@gmail.com"
    org_id = "111"
    with pytest.raises(EvChartDynamoConnectionError) as raised_error:
        validate_email_is_associated_with_active_user_in_org(email, org_id)
    assert email in raised_error.value.message


def test_is_valid_direct_recipient_id_given_existing_dr_id_true(_mock_boto3_manager):
    friendly_dr_id = "123"
    result = is_valid_direct_recipient_id(friendly_dr_id)
    assert True is result


def test_is_valid_direct_recipient_id_given_sub_recipient_id_falses(_mock_boto3_manager):
    dr_id = "111"
    result = is_valid_direct_recipient_id(dr_id)
    assert False is result


def test_is_valid_direct_recipient_id_raises_error_when_dynamo_connection_fails():
    dr_id = "111"
    with pytest.raises(EvChartDynamoConnectionError) as raised_error:
        is_valid_direct_recipient_id(dr_id)
    assert dr_id in raised_error.value.message


def get_event():
    return {
        "headers": {"x-api-key": "111"},
        "body": json.dumps(
            {
                "checksum": VALID_CHECKSUM,
                "module_id": "5",
                "year": "2024",
                "direct_recipient_id": "123",
                "email": "ev-chart-user@ee.doe.gov",
            }
        ),
    }


def test_handler_return_error_with_no_feature(_mock_boto3_client_manager_no_feature):
    response = handler(get_event(), None)

    body = response["body"]
    assert response["statusCode"] == 500
    assert "No feature found with the name s2s" in body


def test_handler_return_error_with_feature_toggle_off(_mock_boto3_client_manager_false_feature):
    response = handler(get_event(), None)

    body = response["body"]
    assert response["statusCode"] == 403
    assert "Error feature is disabled: Feature s2s is currently disabled" in body


def test_handler_return_error_with_no_aurora(_mock_boto3_client_manager):
    response = handler(get_event(), None)

    body = response["body"]
    assert response["statusCode"] == 500
    assert "EvChartDatabaseHandlerConnectionError" in body


@patch("APIPostS2SImportModuleData.index.aurora")
def test_handler_return_error_with_no_not_authorized(_mock_aurora, _mock_boto3_client_manager):
    event = get_event()
    event["headers"] = {}
    response = handler(event, None)

    body = response["body"]
    assert response["statusCode"] == 403
    assert "EvChartUserNotAuthorizedError" in body


@pytest.mark.skip("fails when ran individually")
@patch("APIPostS2SImportModuleData.index.get_org_by_api_key")
@patch("APIPostS2SImportModuleData.index.aurora")
def test_handler_return_error_with_no_boto3(
    _mock_aurora, mock_get_org_by_api_key, _mock_boto3_client_manager
):

    mock_get_org_by_api_key.return_value = "111"
    response = handler(get_event(), None)

    body = response["body"]
    assert response["statusCode"] == 500
    assert "EvChartDynamoConnectionError" in body


@patch("APIPostS2SImportModuleData.index.check_valid_api_key")
@patch("APIPostS2SImportModuleData.index.get_authorized_drs")
@patch("APIPostS2SImportModuleData.index.upload_import_metadata")
@patch("APIPostS2SImportModuleData.index.get_org_by_api_key")
@patch("APIPostS2SImportModuleData.index.aurora")
def test_handler_return_error_with_no_lambda_client_connection(
    _mock_aurora,
    mock_get_org_by_api_key,
    _mock_import_metadata,
    mock_get_authorized_drs,
    _mock_check_valid_api_key,
    _mock_boto3_manager,
    _mock_boto3_client_manager,
):

    mock_get_org_by_api_key.return_value = "111-222"
    mock_get_authorized_drs.return_value = {"123-456": "Maine DOT", "dcae286d": "New York DOT"}

    response = handler(get_event(), None)

    body = response["body"]
    assert response["statusCode"] == 500
    assert "EvChartLambdaConnectionError" in body


@patch("APIPostS2SImportModuleData.index.check_valid_api_key")
@patch("APIPostS2SImportModuleData.index.get_authorized_drs")
@patch("APIPostS2SImportModuleData.index.create_presigned_url")
@patch("APIPostS2SImportModuleData.index.upload_import_metadata")
@patch("APIPostS2SImportModuleData.index.get_org_by_api_key")
@patch("APIPostS2SImportModuleData.index.aurora")
def test_handler_return_success_with_presigned_url_and_upload_id(
    _mock_aurora,
    mock_get_org_by_api_key,
    _mock_import_metadata,
    mock_create_presigned_url,
    mock_get_authorized_drs,
    _mock_check_valid_api_key,
    _mock_boto3_manager,
    _mock_boto3_client_manager,
):

    mock_get_org_by_api_key.return_value = "111-222"
    url = "https://aurl.com"
    mock_create_presigned_url.return_value = url
    mock_get_authorized_drs.return_value = {"123-456": "Maine DOT", "dcae286d": "New York DOT"}

    event = get_event()
    response = handler(event, None)

    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert body.get("presigned_url") == url
    assert body.get("upload_id") is not None
    assert "x-amz-meta-checksum" in body.get("presigned_url_headers")
    assert "x-amz-meta-recipient_type" in body.get("presigned_url_headers")
    assert "x-amz-meta-s2s_upload" in body.get("presigned_url_headers")


@patch("APIPostS2SImportModuleData.index.check_valid_api_key")
@patch("APIPostS2SImportModuleData.index.create_presigned_url")
@patch("APIPostS2SImportModuleData.index.upload_import_metadata")
@patch("APIPostS2SImportModuleData.index.get_org_by_api_key")
@patch("APIPostS2SImportModuleData.index.aurora")
def test_handler_return_error_with_empty_body(
    _mock_aurora,
    mock_get_org_by_api_key,
    _mock_import_metadata,
    mock_create_presigned_url,
    _mock_check_valid_api_key,
    _mock_boto3_manager,
    _mock_boto3_client_manager,
):

    mock_get_org_by_api_key.return_value = "111"
    url = "https://aurl.com"
    mock_create_presigned_url.return_value = url
    event = get_event()
    event["body"] = "{}"
    response = handler(event, None)

    body = json.loads(response["body"])
    assert response["statusCode"] == 406
    assert "EvChartMissingOrMalformedBodyError" in body


# @pytest.mark.skip("issue with boto3 auth will come back to")
def test_get_file_with_path_given_existing_ids_returns_path(_mock_boto3_manager):
    upload_id = "567"
    sr_id = "111-222"
    dr_id = "123-456"
    expected = "upload/Maine DOT/API Client/567.csv"
    result = get_file_with_path(dr_id, sr_id, upload_id)
    assert result == expected


def test_get_org_id_from_friendly_id_when_no_connection_to_dynamo_error():
    friendly_id = "000"
    with pytest.raises(EvChartDynamoConnectionError) as raised_error:
        get_org_id_from_friendly_id(friendly_id)
    assert friendly_id in raised_error.value.message


def test_get_org_id_from_friendly_id_when_given_valid_id_return_value(_mock_boto3_manager):
    friendly_id = "123"
    org_id = get_org_id_from_friendly_id(friendly_id)
    assert "123-456" == org_id


def test_get_org_id_from_friendly_id_when_given_invalid_id_return_error(_mock_boto3_manager):
    friendly_id = "000"
    org_id = get_org_id_from_friendly_id(friendly_id)
    assert org_id is None


@patch("APIPostS2SImportModuleData.index.check_valid_api_key")
@patch("APIPostS2SImportModuleData.index.get_authorized_drs")
@patch("APIPostS2SImportModuleData.index.create_presigned_url")
@patch("APIPostS2SImportModuleData.index.upload_import_metadata")
@patch("APIPostS2SImportModuleData.index.get_org_by_api_key")
@patch("APIPostS2SImportModuleData.index.aurora")
def test_handler_given_dr_that_is_not_authorized_return_error(
    _mock_aurora,
    mock_get_org_by_api_key,
    _mock_import_metadata,
    mock_create_presigned_url,
    mock_get_authorized_drs,
    _mock_check_valid_api_key,
    _mock_boto3_manager,
    _mock_boto3_client_manager,
):
    mock_get_org_by_api_key.return_value = "111-222"
    url = "https://aurl.com"
    mock_create_presigned_url.return_value = url
    mock_get_authorized_drs.return_value = {
        "3824c24b": "Pennsylvania DOT",
        "dcae286d": "New York DOT",
    }

    event = get_event()
    response = handler(event, None)

    body = json.loads(response["body"])
    assert response["statusCode"] == 406
    assert "EvChartMissingOrMalformedBodyError" in body


@patch("APIPostS2SImportModuleData.index.check_valid_api_key")
@patch("APIPostS2SImportModuleData.index.get_authorized_drs")
@patch("APIPostS2SImportModuleData.index.create_presigned_url")
@patch("APIPostS2SImportModuleData.index.upload_import_metadata")
@patch("APIPostS2SImportModuleData.index.get_org_by_api_key")
@patch("APIPostS2SImportModuleData.index.aurora")
def test_handler_given_dr_that_is_does_not_exist_return_error(
    _mock_aurora,
    mock_get_org_by_api_key,
    _mock_import_metadata,
    mock_create_presigned_url,
    mock_get_authorized_drs,
    _mock_check_valid_api_key,
    _mock_boto3_manager,
    _mock_boto3_client_manager,
):
    mock_get_org_by_api_key.return_value = "111-222"
    url = "https://aurl.com"
    mock_create_presigned_url.return_value = url
    mock_get_authorized_drs.return_value = {"123-456": "Maine DOT", "dcae286d": "New York DOT"}

    dr_id = "00"
    event = get_event()
    event["body"] = json.dumps(
        {
            "checksum": VALID_CHECKSUM,
            "module_id": "5",
            "year": "2024",
            "direct_recipient_id": dr_id,
            "email": "ev-chart-user@ee.doe.gov",
        }
    )
    response = handler(event, None)

    body = json.loads(response["body"])
    assert response["statusCode"] == 406
    assert "EvChartMissingOrMalformedBodyError" in body


@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIPostS2SImportModuleData.index.get_authorized_drs")
@patch("APIPostS2SImportModuleData.index.aurora")
def test_sr_can_submit_to_dr_given_unauthorized_sr_return_false(
    mock_aurora, mock_get_authorized_drs, mock_feature_toggle
):
    mock_get_authorized_drs.return_value = {
        "3824c24b": "Pennsylvania DOT",
        "dcae286d": "New York DOT",
    }
    sr_id = "5"
    dr_id = "2"
    result = sr_can_submit_to_dr(mock_aurora.connection, sr_id, dr_id, mock_feature_toggle)

    assert result is False


@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIPostS2SImportModuleData.index.get_authorized_drs")
@patch("APIPostS2SImportModuleData.index.aurora")
def test_sr_can_submit_to_dr_given_an_authorized_sr_return_true(
    mock_aurora, mock_get_authorized_drs, mock_feature_toggle
):
    mock_get_authorized_drs.return_value = {"2": "Authorized Example", "dcae286d": "New York DOT"}
    sr_id = "5"
    dr_id = "2"
    result = sr_can_submit_to_dr(mock_aurora.connection, sr_id, dr_id, mock_feature_toggle)

    assert result is True
