from unittest.mock import patch
import boto3
from moto import mock_aws
import pytest

from station_validation.validate_authorizations_and_recipient_types import (
    validate_dr_is_authorized,
    validate_recipient_type,
    validate_authorized_subrecipients
)

from evchart_helper.custom_exceptions import (
    EvChartUserNotAuthorizedError,
)

from evchart_helper.boto3_manager import Boto3Manager

# creating org table fixture
@pytest.fixture(name="_dynamodb_org")
def fixture_dynamodb_org():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[
                {"AttributeName": "org_id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "org_id", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()

        # inserting Maine DR
        table.put_item(
            Item={
                "org_id": "1",
                "name": "Maine DOT",
                "recipient_type": "direct-recipient",
                "org_friendly_id": "1",
            }
        )

        # inserting Spark09 SR
        table.put_item(
            Item={
                "org_id": "2",
                "name": "Spark09",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "2",
            }
        )

        # inserting Sparkflow SR
        table.put_item(
            Item={
                "org_id": "3",
                "name": "Sparkflow",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "3",
            }
        )

        # inserting Evgo SR
        table.put_item(
            Item={
                "org_id": "4",
                "name": "Evgo",
                "recipient_type": "sub-recipient",
                "org_friendly_id": "4",
            }
        )

        # inserting NY DR
        table.put_item(
            Item={
                "org_id": "5",
                "name": "NY DOT",
                "recipient_type": "direct-recipient",
                "org_friendly_id": "5",
            }
        )

        yield dynamodb


@pytest.fixture(name="_mock_boto3_manager")
def fixture_mock_boto3_manager(_dynamodb_org):
    with patch.object(Boto3Manager, "resource", return_value=_dynamodb_org) as mock_client:
        yield mock_client

def test_dr_is_authorized_to_create_station_for_their_own_org_valid_200(
    validation_options_for_federally_funded_station,
    validation_options_for_non_federally_funded_station
    ):
    validation_options_for_non_federally_funded_station["api"] = "post"
    validation_options_for_non_federally_funded_station["api"] = "post"
    assert validate_dr_is_authorized(validation_options_for_federally_funded_station) is True
    assert validate_dr_is_authorized(validation_options_for_non_federally_funded_station) is True


def test_dr_is_not_authorized_to_create_station_for_another_dr_invlaid_401(
    validation_options_for_federally_funded_station,
    validation_options_for_non_federally_funded_station
):
    validation_options_for_federally_funded_station["auth_values"]["org_id"] = "111"
    validation_options_for_non_federally_funded_station["auth_values"]["org_id"] = "111"
    with pytest.raises(EvChartUserNotAuthorizedError) as e:
        validate_dr_is_authorized(validation_options_for_federally_funded_station)
        validate_dr_is_authorized(validation_options_for_non_federally_funded_station)
    assert e.value.message == "EvChartUserNotAuthorizedError raised. The direct recipient requester cannot be a different org than the dr_id associated with station"


@pytest.mark.parametrize("api", ["patch", "post"])
def test_dr_is_authorized_to_create_and_edit_station_valid_200(
    api,
    validation_options_for_federally_funded_station,
    validation_options_for_non_federally_funded_station
):
    validation_options_for_federally_funded_station["api"] = api
    validation_options_for_non_federally_funded_station["api"] = api

    assert validate_recipient_type(validation_options_for_federally_funded_station) is True
    assert validate_recipient_type(validation_options_for_non_federally_funded_station) is True


def test_sr_is_only_authorized_to_create_station_for_dr_valid_200(
    validation_options_for_federally_funded_station,
    validation_options_for_non_federally_funded_station
):
    validation_options_for_federally_funded_station["auth_values"]["recipient_type"] = "sub-recipient"
    validation_options_for_non_federally_funded_station["auth_values"]["recipient_type"] = "sub-recipient"

    assert validate_recipient_type(validation_options_for_federally_funded_station) is True
    assert validate_recipient_type(validation_options_for_non_federally_funded_station) is True


def test_sr_is_not_authorized_to_edit_station_invalid_401(
    validation_options_for_federally_funded_station,
    validation_options_for_non_federally_funded_station
):
    validation_options_for_federally_funded_station["auth_values"]["recipient_type"] = "sub-recipient"
    validation_options_for_federally_funded_station["api"] = "patch"

    validation_options_for_non_federally_funded_station["auth_values"]["recipient_type"] = "sub-recipient"
    validation_options_for_non_federally_funded_station["api"] = "patch"

    with pytest.raises(EvChartUserNotAuthorizedError) as e:
        validate_recipient_type(validation_options_for_federally_funded_station)
    assert e.value.message == "EvChartUserNotAuthorizedError raised. User must be direct recipient to edit station"

    with pytest.raises(EvChartUserNotAuthorizedError) as e:
        validate_recipient_type(validation_options_for_non_federally_funded_station)
    assert e.value.message == "EvChartUserNotAuthorizedError raised. User must be direct recipient to edit station"


def test_all_authorized_subrecipients_valid(validation_options_for_federally_funded_station, _mock_boto3_manager,  _dynamodb_org,):
    station = validation_options_for_federally_funded_station.get("station")
    srs_updated = {
        'station_uuid': "123-123-123",
        'srs_added': ['2'],
        'srs_removed': ['3'],
        'authorized_subrecipients': ['4']
    }
    station.update(srs_updated)
    assert validate_authorized_subrecipients(validation_options_for_federally_funded_station)


def test_dr_present_in_authorized_subrecipients_invalid(validation_options_for_federally_funded_station, _mock_boto3_manager,  _dynamodb_org,):
    station = validation_options_for_federally_funded_station.get("station")
    srs_updated = {
        'authorized_subrecipients': ['1'],
        'srs_removed': ['5']
    }
    station.update(srs_updated)
    response = validate_authorized_subrecipients(validation_options_for_federally_funded_station)
    assert response == {"validate_authorized_subrecipients()": "['Maine DOT', 'NY DOT'] added in request body is not a sub-recipient"}


def test_no_sr_list_present_valid(validation_options_for_federally_funded_station, _mock_boto3_manager,  _dynamodb_org,):
    station = validation_options_for_federally_funded_station.get("station")
    srs_updated = {
        'station_uuid': "123-123-123",
        'zip': "12345",
    }
    station.update(srs_updated)
    assert validate_authorized_subrecipients(validation_options_for_federally_funded_station)
