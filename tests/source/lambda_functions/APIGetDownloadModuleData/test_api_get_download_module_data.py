import json
import os
from io import StringIO
from unittest.mock import MagicMock, patch

import boto3
import feature_toggle
import pandas as pd
import pytest
from APIGetDownloadModuleData.index import (
    format_dataframe_module,
    format_dataframe_uuid,
    get_formatted_fields_from_event,
    get_query_and_data,
    get_query_filters,
    get_stored_proc_data,
)
from APIGetDownloadModuleData.index import handler as api_download_module_data
from APIGetDownloadModuleData.index import validate_fields
from botocore.response import StreamingBody
from database_central_config import DatabaseCentralConfig
from evchart_helper.boto3_manager import Boto3Manager
from evchart_helper.custom_exceptions import EvChartMissingOrMalformedHeadersError
from feature_toggle.feature_enums import Feature
from moto import mock_aws


@pytest.fixture(name="config")
def fixture_config():
    return DatabaseCentralConfig(
        path=os.path.join(
            ".",
            "source",
            "lambda_layers",
            "python",
            "database_central_config",
            "database_central_config.json",
        )
    )


@pytest.fixture
def fixture_s3():
    with mock_aws():
        s3_resource = boto3.resource("s3")
        s3_resource.Bucket("ev-chart-artifact-data-dev-us-east-1").create()

        yield s3_resource


@pytest.fixture
def mock_boto3_manager_s3(fixture_s3):
    with patch.object(Boto3Manager, "resource", return_value=fixture_s3) as mock_resource:
        yield mock_resource


@pytest.fixture
def fixture_lambda():
    with mock_aws():
        lambda_client = boto3.client("lambda")
        lambda_client.invoke = MagicMock()
        mock_payload = json.dumps({"body": ""})
        lambda_client.invoke.return_value = {
            "Payload": StreamingBody(StringIO(mock_payload), len(mock_payload))
        }

        yield lambda_client


@pytest.fixture
def mock_boto3_manager_lambda(fixture_lambda):
    with patch.object(Boto3Manager, "client", return_value=fixture_lambda) as mock_client:
        yield mock_client


# creating org table fixture
@pytest.fixture(name="dynamodb_org")
def fixture_dynamodb_org():
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        table = dynamodb.create_table(
            TableName="ev-chart_org",
            KeySchema=[
                {"AttributeName": "org_id", "KeyType": "HASH"},
                {"AttributeName": "recipient_type", "KeyType": "RANGE"},
            ],
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
        table.wait_until_exists()

        # inserting Maine DR
        table.put_item(
            Item={
                "org_id": "111",
                "name": "Maine DOT",
                "org_friendly_id": "1",
                "recipient_type": "direct-recipient",
            }
        )

        # inserting NY DR
        table.put_item(
            Item={
                "org_id": "222",
                "name": "NY DOT",
                "org_friendly_id": "2",
                "recipient_type": "direct-recipient",
            }
        )

        # inserting Sparkflow SR
        table.put_item(
            Item={
                "org_id": "333",
                "name": "Sparkflow",
                "org_friendly_id": "3",
                "recipient_type": "sub-recipient",
            }
        )

        yield dynamodb


@pytest.fixture
def mock_boto3_manager(dynamodb_org):
    with patch.object(Boto3Manager, "resource", return_value=dynamodb_org) as mock_client:
        yield mock_client


@pytest.fixture(name="event")
def get_event():
    return {
        "headers": {},
        "httpMethod": "GET",
        "requestContext": {
            "accountId": "414275662771",
            "authorizer": {
                "claims": {
                    "org_id": "123",
                    "org_friendly_id": "1",
                    "org_name": "New York DOT",
                    "email": "dev@ee.doe.gov",
                    "scope": "joet",
                    "role": "admin",
                }
            },
        },
        "queryStringParameters": {
            "modules": '["6"]',
            "years": '["2023"]',
            "quarters": '["1"]',
            "network_providers": '["ampup"]',
            "federal_funding_status": '["1","0"]',
            "drs": '["3824c24b-f4fa-44bb-b030-09e99c3e4b6c"]',
            "srs": '["a3375aeb-6686-4c5a-82a6-0ecbf378a5d7"]',
            "stations": '["d89afa33-f2b9-46da-900b-8483c66255b5"]',
        },
    }


valid_data = {"upload_id": ["abc"], "station_uuid": ["abc"], "other_columns": ["efg"]}


@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDownloadModuleData.index.get_network_providers_from_db")
def test_invalid_user_401(mock_get_network_providers, mock_feature_toggle, event):
    mock_get_network_providers.return_value = ["ampup"]
    mock_feature_toggle.return_value = {
        
        Feature.REGISTER_NON_FED_FUNDED_STATION,
    }
    event["requestContext"]["authorizer"]["claims"]["scope"] = "sub-recipient"
    response = api_download_module_data(event, None)
    assert response.get("statusCode") == 403


@patch("APIGetDownloadModuleData.index.format_dataframe_module")
@patch("APIGetDownloadModuleData.index.format_dataframe_uuid")
@patch("APIGetDownloadModuleData.index.format_dataframe_date")
@patch("APIGetDownloadModuleData.index.format_dataframe_bool")
@patch("APIGetDownloadModuleData.index.validate_fields")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDownloadModuleData.index.execute_query_df")
def test_valid_200(
    mock_query,
    mock_feature_toggle,
    mock_validate_fields,
    _mock_bool,
    _mock_date,
    _mock_uuid,
    _mock_module,
    event,
):
    mock_feature_toggle.return_value = {}
    mock_validate_fields.return_value = True
    mock_query.return_value = pd.DataFrame(valid_data)
    response = api_download_module_data(event, None)
    assert response.get("statusCode") == 200
    payload = json.loads(response.get("body"))
    assert payload["is_data_present"] == True


@patch("APIGetDownloadModuleData.index.validate_fields")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDownloadModuleData.index.execute_query_df")
def test_no_data_returned_from_stored_procedure_200(
    mock_query, mock_feature_toggle, mock_validate_fields, event
):
    mock_feature_toggle.return_value = {}
    mock_validate_fields.return_value = True
    mock_query.return_value = pd.DataFrame([])
    response = api_download_module_data(event, None)
    assert response.get("statusCode") == 200
    payload = json.loads(response.get("body"))
    assert payload["is_data_present"] == False


@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
def test_invalid_data_for_module_id_400(mock_feature_toggle, event):
    mock_feature_toggle.return_value = {}
    event["queryStringParameters"]["modules"] = "[-1]"
    response = api_download_module_data(event, None)
    assert response.get("statusCode") == 400


def test_format_fields_from_event_select_all():
    body = {"modules": '["2"]', "quarters": '["-1"]'}
    expected = {
        "modules": ["2"],
        "years": ["-1"],
        "quarters": ["-1"],
        "network_providers": ["-1"],
        "drs": ["-1"],
        "srs": ["-1"],
        "stations": ["-1"],
    }
    response = get_formatted_fields_from_event(body, {})
    assert expected == response, f"this is whats passed in {response}"


@pytest.mark.parametrize(
    "federal_funding_status, expected",
    [('["1"]', "1"), ('["0"]', "0"), ('["-1"]', "-1"), ('["0", "1"]', "-1"), ('["1", "0"]', "-1")],
)
def test_format_fields_from_event_register_non_fed_stations_ft_true(
    federal_funding_status, expected
):
    body = {"modules": '["2"]', "federal_funding_status": federal_funding_status}

    response = get_formatted_fields_from_event(body, {Feature.REGISTER_NON_FED_FUNDED_STATION})
    assert response["federal_funding_status"] == [expected]


def test_validate_fields_non_quarterly():
    body = {"modules": '["8"]'}
    expected = {
        "modules": ["8"],
        "years": ["-1"],
        "network_providers": ["-1"],
        "drs": ["-1"],
        "srs": ["-1"],
        "stations": ["-1"],
        "quarters": ["-1"],
    }
    response = get_formatted_fields_from_event(body, {})
    assert expected == response


def test_get_stored_proc_data_with_default_values_selected():
    request_fields = {
        "modules": ["2"],
        "quarters": ["-1"],
        "network_providers": ["-1"],
        "drs": ["-1"],
        "srs": ["-1"],
        "stations": ["-1"],
        "years": ["-1"],
    }
    expected = (
        "module2_data_v3",
        "-1",
        "-1",
        "-1",
        "-1",
        "-1",
        "-1",
    )
    statement = get_stored_proc_data(request_fields)
    assert expected == statement


def test_get_stored_proc_data_with_multiple_values_selected():
    request_fields = {
        "modules": ["1"],
        "quarters": ["1", "2", "3"],
        "network_providers": ["np1", "np2", "np3"],
        "drs": ["dr1", "dr2", "dr3"],
        "srs": ["sr1", "sr2", "sr3"],
        "stations": ["111", "222", "333"],
        "years": ["2023", "2024", "2025"],
    }
    expected = (
        "station_registrations",
        "'2023', '2024', '2025'",
        "'1', '2', '3'",
        "'np1', 'np2', 'np3'",
        "'111', '222', '333'",
        "'dr1', 'dr2', 'dr3'",
        "'sr1', 'sr2', 'sr3'",
    )
    statement = get_stored_proc_data(request_fields)
    assert expected == statement


def test_format_dr_uuid_in_df(mock_boto3_manager):
    df = {"dr_id": ["111", "222"]}
    output_df = pd.DataFrame(df)
    response = format_dataframe_uuid(output_df, "dr_id", "direct-recipient")

    expected = {"dr_id": ["1", "2"]}
    expected = pd.DataFrame(expected)

    assert response.equals(expected)


def test_format_sr_uuid_in_df(mock_boto3_manager):
    df = {"sr_id": ["333"]}
    output_df = pd.DataFrame(df)
    response = format_dataframe_uuid(output_df, "sr_id", "sub-recipient")

    expected = {"sr_id": ["3"]}
    expected = pd.DataFrame(expected)

    assert response.equals(expected)


def test_validate_fields_with_network_provider_table_ft_valid():
    body = {
        "modules": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "quarters": ["1", "2", "3", "4"],
        "network_providers": ["-1"],
        "drs": ["-1"],
        "srs": ["-1"],
        "stations": ["-1"],
        "years": ["2023", "2024"],
    }
    assert (
        validate_fields(
            body, cursor=MagicMock(), feature_toggle_set={}
        )
        is True
    )


@pytest.mark.parametrize(
    "federal_funding_status", [(["1", "0"]), (["0", "1"]), (["1"]), (["0"]), (["-1"])]
)
def test_validate_fields_with_register_non_fed_funded_station_ft_on(federal_funding_status):
    body = {
        "modules": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "quarters": ["1", "2", "3", "4"],
        "network_providers": ["-1"],
        "drs": ["-1"],
        "srs": ["-1"],
        "stations": ["-1"],
        "years": ["2023", "2024"],
        "federal_funding_status": federal_funding_status,
    }
    assert (
        validate_fields(
            body,
            cursor=MagicMock(),
            feature_toggle_set={
                
                Feature.REGISTER_NON_FED_FUNDED_STATION,
            },
        )
        is True
    )


def test_validate_fields_with_register_non_fed_funded_station_ft_off():
    body = {
        "modules": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "quarters": ["1", "2", "3", "4"],
        "network_providers": ["-1"],
        "drs": ["-1"],
        "srs": ["-1"],
        "stations": ["-1"],
        "years": ["2023", "2024"],
        "federal_funding_status": ["1", "0"],
    }
    with pytest.raises(EvChartMissingOrMalformedHeadersError) as e:
        validate_fields(
            body, cursor=MagicMock(), feature_toggle_set={}
        )


def test_validate_fields_with_invalid_federal_funding_status_value():
    body = {
        "modules": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "quarters": ["1", "2", "3", "4"],
        "network_providers": ["-1"],
        "drs": ["-1"],
        "srs": ["-1"],
        "stations": ["-1"],
        "years": ["2023", "2024"],
        "federal_funding_status": ["1'", "0"],
    }
    with pytest.raises(EvChartMissingOrMalformedHeadersError) as e:
        validate_fields(
            body, cursor=MagicMock(), feature_toggle_set={}
        )


def test_validate_fields_with_invalid_field_400():
    body = {
        "modules": ["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        "quarters": ["1", "2", "3", "4"],
        "network_providers": ["-1"],
        "drs": ["-1"],
        "srs": ["-1"],
        "stations": ["-1"],
        "years": ["2023", "2024"],
        "unknown_field": ["0"],
    }
    with pytest.raises(EvChartMissingOrMalformedHeadersError) as e:
        validate_fields(
            body, cursor=MagicMock(), feature_toggle_set={}
        )


def test_format_module_id_in_df(mock_boto3_manager):
    df = {
        "module": [
            "station_registrations",
            "module2_data_v3",
            "module3_data_v3",
            "module4_data_v3",
            "module5_data_v3",
            "module6_data_v3",
            "module7_data_v3",
            "module8_data_v3",
            "module9_data_v3",
        ]
    }
    output_df = pd.DataFrame(df)
    response = format_dataframe_module(output_df)

    expected = {"module": ["1", "2", "3", "4", "5", "6", "7", "8", "9"]}
    expected = pd.DataFrame(expected)

    assert response.equals(expected)


# JE-5739 verifying that nested errors will still be returned by the api to enhance debugging
@patch("APIGetDownloadModuleData.index.generate_presigned_url")
@patch("APIGetDownloadModuleData.index.format_dataframe_module")
@patch("APIGetDownloadModuleData.index.format_dataframe_uuid")
@patch("APIGetDownloadModuleData.index.format_dataframe_date")
@patch("APIGetDownloadModuleData.index.format_dataframe_bool")
@patch("APIGetDownloadModuleData.index.validate_fields")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDownloadModuleData.index.execute_query_df")
def test_nested_error_message(
    mock_query,
    mock_feature_toggle_set,
    mock_validate_fields,
    mock_bool,
    mock_date,
    mock_uuid,
    mock_module,
    mock_presigned_url,
    event,
):
    mock_feature_toggle_set.return_value = {Feature.PRESIGNED_URL}
    mock_validate_fields.return_value = True
    mock_query.return_value = pd.DataFrame(valid_data)
    mock_presigned_url.return_value = {"error": "presigned url error message"}
    response = api_download_module_data(event, None)
    assert response.get("statusCode") == 200
    mock_presigned_url.assert_called()
    payload = json.loads(response.get("body"))
    assert payload["error"] == "presigned url error message"


# JE-6668 ensuring M4 returns null outage_id for null modules and that user_reports_no_data column is not a column in the df
@patch("APIGetDownloadModuleData.index.format_dataframe_uuid")
@patch("APIGetDownloadModuleData.index.format_dataframe_date")
@patch("APIGetDownloadModuleData.index.format_dataframe_bool")
@patch("APIGetDownloadModuleData.index.validate_fields")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDownloadModuleData.index.execute_query_df")
def test_correctly_outputted_fields_for_m4(
    mock_query, mock_feature_toggle, mock_validate_fields, mock_bool, mock_date, mock_uuid, event
):
    db_response = pd.DataFrame(
        data={
            "module": ["module4_data_v3", "module4_data_v3"],
            "dr_id": ["dr_id", "dr_id"],
            "sr_id": ["sr_id", "sr_id"],
            "year": ["2024", "2023"],
            "quarter": ["4", "1"],
            "network_provider_value": ["blink", "blink"],
            "network_provider_upload": ["blink", "blink"],
            "network_provider_uuid": ["np_uuid", "np_uuid"],
            "outage_duration": [None, "123248.95"],
            # note: outage_id is not null yet, because this represents the system generated value returned from db call
            "outage_id": ["2025-04-17 22:46:44", "2025-04-17 22:46:44"],
            "port_id": ["port_id", "port_id"],
            "port_id_upload": ["port_id", "port_id"],
            "port_uuid": ["port_uuid", "port_uuid"],
            "station_id_upload": ["cherry", "mango"],
            "station_uuid": ["station_uuid", "station_uuid"],
            "time_at_upload": ["2025-04-17 22:46:45", "2025-04-17 22:46:45"],
            "upload_id": ["upload_id", "upload_id"],
            "user_reports_no_data": [1, 0],
        }
    )
    mock_feature_toggle.return_value = {}
    mock_validate_fields.return_value = True
    mock_uuid.side_effect = (db_response, db_response)
    mock_query.return_value = db_response

    expected = pd.DataFrame(
        data={
            "module": ["4", "4"],
            "dr_id": ["dr_id", "dr_id"],
            "sr_id": ["sr_id", "sr_id"],
            "year": ["2024", "2023"],
            "quarter": ["4", "1"],
            "current_network_provider": ["blink", "blink"],
            "network_provider_at_upload": ["blink", "blink"],
            "outage_duration": [None, "123248.95"],
            "outage_id": [None, "2025-04-17 22:46:44"],
            "port_id": ["port_id", "port_id"],
            "station_id": ["cherry", "mango"],
        }
    )

    response = api_download_module_data(event, None)
    payload = json.loads(response.get("body"))
    assert payload["data"] == expected.to_dict(orient="records")


# JE-6717 ensuring M2 returns null session_id for null modules and that user_reports_no_data column is not a column in the df
@patch("APIGetDownloadModuleData.index.format_dataframe_uuid")
@patch("APIGetDownloadModuleData.index.format_dataframe_date")
@patch("APIGetDownloadModuleData.index.format_dataframe_bool")
@patch("APIGetDownloadModuleData.index.validate_fields")
@patch.object(feature_toggle.FeatureToggleService, "get_active_feature_toggles")
@patch("APIGetDownloadModuleData.index.execute_query_df")
def test_correctly_outputted_fields_for_m2(
    mock_query, mock_feature_toggle, mock_validate_fields, mock_bool, mock_date, mock_uuid, event
):
    db_response = pd.DataFrame(
        data={
            "module": ["module4_data_v3", "module4_data_v3"],
            "dr_id": ["dr_id", "dr_id"],
            "sr_id": ["sr_id", "sr_id"],
            "year": ["2024", "2023"],
            "quarter": ["4", "1"],
            "network_provider_value": ["blink", "blink"],
            "network_provider_upload": ["blink", "blink"],
            "network_provider_uuid": ["np_uuid", "np_uuid"],
            # note: session_id is not null yet, because this represents the system generated value returned from db call
            "session_id": ["NoSession2025-04-09 23:11:10.451133+", "1003"],
            "port_id": ["port_id", "port_id"],
            "port_id_upload": ["port_id", "port_id"],
            "port_uuid": ["port_uuid", "port_uuid"],
            "station_id_upload": ["cherry", "mango"],
            "station_uuid": ["station_uuid", "station_uuid"],
            "time_at_upload": ["2025-04-17 22:46:45", "2025-04-17 22:46:45"],
            "upload_id": ["upload_id", "upload_id"],
            "user_reports_no_data": [1, 0],
        }
    )
    mock_feature_toggle.return_value = {}
    mock_validate_fields.return_value = True
    mock_uuid.side_effect = (db_response, db_response)
    mock_query.return_value = db_response

    expected = pd.DataFrame(
        data={
            "module": ["4", "4"],
            "dr_id": ["dr_id", "dr_id"],
            "sr_id": ["sr_id", "sr_id"],
            "year": ["2024", "2023"],
            "quarter": ["4", "1"],
            "current_network_provider": ["blink", "blink"],
            "network_provider_at_upload": ["blink", "blink"],
            "session_id": [None, "1003"],
            "port_id": ["port_id", "port_id"],
            "station_id": ["cherry", "mango"],
        }
    )

    response = api_download_module_data(event, None)
    payload = json.loads(response.get("body"))
    assert payload["data"] == expected.to_dict(orient="records")


# JE-6758 Synack found an sql injection issue when passing in the network_provider field.
# This test ensures that the network providers passed in are valid network providers in the database
@patch("APIGetDownloadModuleData.index.get_network_providers_from_db")
def test_pen_test_bug_on_network_provider_field(mock_get_network_providers):
    mock_get_network_providers.return_value = ["7charge", "abm"]
    request_fields = {
        "modules": ["1"],
        "years": ["-1"],
        "quarters": ["-1"],
        "network_providers": ["7charge'"],
        "stations": ["-1"],
        "drs": ["3824c24b-f4fa-44bb-b030-09e99c3e4b6c"],
        "srs": ["-1"],
    }
    with pytest.raises(EvChartMissingOrMalformedHeadersError) as e:
        validate_fields(
            request_fields, cursor=MagicMock(), feature_toggle_set={}
        )
        assert e.value.message == (
            "EvChartMissingOrMalformedHeadersError raised. Improper data in network providers: 7charge'"
        )


@patch("APIGetDownloadModuleData.index.get_all_station_uuids")
@patch("APIGetDownloadModuleData.index.get_orgs_by_recipient_type_dynamo")
@patch("APIGetDownloadModuleData.index.get_all_network_provider_uuids")
@patch("APIGetDownloadModuleData.index.get_column_names")
def test_get_query_filters_default_values_register_nonfed_station_ft_off(
    mock_get_column_names,
    mock_get_all_network_providers,
    mock_get_orgs_by_recipient_type,
    mock_get_all_station_uuids,
):
    mock_get_column_names.return_value = ["col1", "md.col2", "md.col3"]
    mock_get_all_network_providers.return_value = ["111-blink", "222-ampup"]
    mock_get_orgs_by_recipient_type.side_effect = [
        [{"org_id": "dr1", "recipient_type": "direct-recipient"}],
        [{"org_id": "sr1", "recipient_type": "sub-recipient"}],
    ]
    mock_get_all_station_uuids.return_value = ["station1", "station2"]
    token = {"org_id": "123", "recipient_type": "direct-recipient"}
    request_fields = {
        "modules": ["1"],
        "years": ["-1"],
        "quarters": ["-1"],
        "network_providers": ["-1"],
        "stations": ["-1"],
        "drs": ["-1"],
        "srs": ["-1"],
    }

    expected = {
        "table_name": "station_registrations",
        "modules": "1",
        "column_names": ["col1", "md.col2", "md.col3"],
        "years": ["2025", "2024", "2023"],
        "quarters": ["1", "2", "3", "4"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
    }

    response = get_query_filters(token, MagicMock(), request_fields, {})
    assert response == expected


@patch("APIGetDownloadModuleData.index.get_column_names")
def test_get_query_filters_specified_values_register_nonfed_station_ft_off(mock_get_column_names):
    mock_get_column_names.return_value = ["col1", "md.col2", "md.col3"]
    token = {"org_id": "123", "recipient_type": "direct-recipient"}
    request_fields = {
        "modules": ["1"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
    }

    expected = {
        "table_name": "station_registrations",
        "modules": "1",
        "column_names": ["col1", "md.col2", "md.col3"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
    }
    response = get_query_filters(token, MagicMock(), request_fields, {})
    assert response == expected
    assert response.get("federal_funding_status") is None


@patch("APIGetDownloadModuleData.index.get_column_names")
def test_get_query_filters_specified_values_register_nonfed_station_ft_on(mock_get_column_names):
    mock_get_column_names.return_value = ["col1", "md.col2", "md.col3"]
    token = {"org_id": "123", "recipient_type": "direct-recipient"}
    request_fields = {
        "modules": ["1"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
        "federal_funding_status": ["1"],
    }

    response = get_query_filters(
        token, MagicMock(), request_fields, {Feature.REGISTER_NON_FED_FUNDED_STATION}
    )
    assert response.get("federal_funding_status") == ["1"]


@patch("APIGetDownloadModuleData.index.DatabaseCentralConfig")
def test_get_query_and_data_mod_1_sr_specified(mock_database_central_config, config):
    mock_database_central_config.return_value = config
    request_fields = {
        "modules": ["1"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
    }

    filters = {
        "table_name": "station_registrations",
        "modules": "1",
        "column_names": ["col1", "md.col2", "md.col3"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
    }
    expected_data = (
        filters["network_providers"] + filters["stations"] + filters["drs"] + filters["srs"]
    )
    response = get_query_and_data(filters, request_fields, {Feature.DATABASE_CENTRAL_CONFIG})
    assert response.get("data") == expected_data


@patch("APIGetDownloadModuleData.index.DatabaseCentralConfig")
def test_get_query_and_data_mod_1_dr_or_default_selected(mock_database_central_config, config):
    mock_database_central_config.return_value = config
    request_fields = {
        "modules": ["1"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["-1"],
    }

    filters = {
        "table_name": "station_registrations",
        "modules": "1",
        "column_names": ["col1", "md.col2", "md.col3"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["-1"],
    }
    expected_data = filters["network_providers"] + filters["stations"] + filters["drs"]
    response = get_query_and_data(filters, request_fields, {Feature.DATABASE_CENTRAL_CONFIG})
    assert response.get("data") == expected_data


@patch("APIGetDownloadModuleData.index.DatabaseCentralConfig")
def test_get_query_and_data_mod_3_quarterly_module_with_sr_specified(
    mock_database_central_config, config
):
    mock_database_central_config.return_value = config
    request_fields = {
        "modules": ["3"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
    }

    filters = {
        "table_name": "module3_data_v3",
        "modules": "3",
        "column_names": ["col1", "md.col2", "md.col3"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
    }
    expected_data = (
        filters["network_providers"]
        + filters["stations"]
        + filters["drs"]
        + filters["srs"]
        + filters["years"]
        + filters["quarters"]
    )
    response = get_query_and_data(filters, request_fields, {Feature.DATABASE_CENTRAL_CONFIG})
    assert response.get("data") == expected_data


@patch("APIGetDownloadModuleData.index.DatabaseCentralConfig")
def test_get_query_and_data_mod_3_quarterly_module_dr_or_default_selected(
    mock_database_central_config, config
):
    mock_database_central_config.return_value = config
    request_fields = {
        "modules": ["3"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["-1"],
    }

    filters = {
        "table_name": "module3_data_v3",
        "modules": "3",
        "column_names": ["col1", "md.col2", "md.col3"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["-1"],
    }
    expected_data = (
        filters["network_providers"]
        + filters["stations"]
        + filters["drs"]
        + filters["years"]
        + filters["quarters"]
    )
    response = get_query_and_data(filters, request_fields, {Feature.DATABASE_CENTRAL_CONFIG})
    assert response.get("data") == expected_data


@patch("APIGetDownloadModuleData.index.DatabaseCentralConfig")
def test_get_query_and_data_mod_9_one_time_module_with_sr_specified(
    mock_database_central_config, config
):
    mock_database_central_config.return_value = config
    request_fields = {
        "modules": ["9"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
    }

    filters = {
        "table_name": "module9_data_v3",
        "modules": "9",
        "column_names": ["col1", "md.col2", "md.col3"],
        "years": ["2023"],
        "quarters": ["1", "2"],
        "network_providers": ["111-blink", "222-ampup"],
        "stations": ["station1", "station2"],
        "drs": ["dr1"],
        "srs": ["sr1"],
    }
    expected_data = (
        filters["network_providers"] + filters["stations"] + filters["drs"] + filters["srs"]
    )
    response = get_query_and_data(filters, request_fields, {Feature.DATABASE_CENTRAL_CONFIG})
    assert response.get("data") == expected_data


# @patch("APIGetDownloadModuleData.index.DatabaseCentralConfig")
# def test_get_query_and_data_mod_3_quarterly_module_dr_or_default_selected(
#     mock_database_central_config, config
# ):
#     mock_database_central_config.return_value = config
#     request_fields = {
#         "modules": ["9"],
#         "years": ["2023"],
#         "quarters": ["1", "2"],
#         "network_providers": ["111-blink", "222-ampup"],
#         "stations": ["station1", "station2"],
#         "drs": ["dr1"],
#         "srs": ["-1"],
#     }

#     filters = {
#         "table_name": "module9_data_v3",
#         "modules": "9",
#         "column_names": ["col1", "md.col2", "md.col3"],
#         "years": ["2023"],
#         "quarters": ["1", "2"],
#         "network_providers": ["111-blink", "222-ampup"],
#         "stations": ["station1", "station2"],
#         "drs": ["dr1"],
#         "srs": ["-1"],
#     }
#     expected_data = filters["network_providers"] + filters["stations"] + filters["drs"]
#     response = get_query_and_data(filters, request_fields, {Feature.DATABASE_CENTRAL_CONFIG})
#     assert response.get("data") == expected_data


# @patch("APIGetDownloadModuleData.index.DatabaseCentralConfig")
# def test_get_query_and_data_mod_5_annual_module_with_sr_specified(mock_database_central_config, config):
#     mock_database_central_config.return_value = config
#     request_fields = {
#         "modules" : ["5"],
#         "years" : ["2023"],
#         "quarters" : ["1", "2"],
#         "network_providers": ["111-blink", "222-ampup"],
#         "stations" : ["station1", "station2"],
#         "drs" : ["dr1"],
#         "srs" : ["sr1"],
#     }

#     filters = {
#         "table_name": "module5_data_v3",
#         "modules" : "5",
#         "column_names": ["col1", "md.col2", "md.col3"],
#         "years" : ["2023"],
#         "quarters" : ["1", "2"],
#         "network_providers": ["111-blink", "222-ampup"],
#         "stations" : ["station1", "station2"],
#         "drs" : ["dr1"],
#         "srs" : ["sr1"],
#     }
#     expected_data = filters["network_providers"] + filters["stations"] + filters["drs"]  + filters["srs"] + filters["years"]
#     response = get_query_and_data(filters, request_fields, {Feature.DATABASE_CENTRAL_CONFIG})
#     assert response.get("data") == expected_data


# @patch("APIGetDownloadModuleData.index.DatabaseCentralConfig")
# def test_get_query_and_data_mod_5_annual_module_dr_or_default_selected(mock_database_central_config, config):
#     mock_database_central_config.return_value = config
#     request_fields = {
#         "modules" : ["5"],
#         "years" : ["2023"],
#         "quarters" : ["1", "2"],
#         "network_providers": ["111-blink", "222-ampup"],
#         "stations" : ["station1", "station2"],
#         "drs" : ["dr1"],
#         "srs" : ["-1"],
#     }

#     filters = {
#         "table_name": "module5_data_v3",
#         "modules" : "5",
#         "column_names": ["col1", "md.col2", "md.col3"],
#         "years" : ["2023"],
#         "quarters" : ["1", "2"],
#         "network_providers": ["111-blink", "222-ampup"],
#         "stations" : ["station1", "station2"],
#         "drs" : ["dr1"],
#         "srs" : ["-1"],
#     }
#     expected_data = filters["network_providers"] + filters["stations"] + filters["drs"] + filters["years"]
#     response = get_query_and_data(filters, request_fields, {Feature.DATABASE_CENTRAL_CONFIG})
#     assert response.get("data") == expected_data
