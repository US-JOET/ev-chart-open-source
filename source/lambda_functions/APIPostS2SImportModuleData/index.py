"""
APIPostS2SImportModuleData

Import module data that has been submitted via S2S (API key).
"""
import datetime
import json
import re
import uuid
from typing import Any, Callable, List

import botocore
import botocore.client
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import NoCredentialsError
from dateutil import tz
from email_handler import get_email_regex
from evchart_helper import aurora, boto3_manager
from evchart_helper.api_helper import (
    execute_query,
    get_org_info_dynamo,
)
from evchart_helper.custom_exceptions import (
    EvChartDatabaseDynamoQueryError,
    EvChartDatabaseHandlerConnectionError,
    EvChartDynamoConnectionError,
    EvChartEmailError,
    EvChartInvalidAPIKey,
    EvChartJsonOutputError,
    EvChartLambdaConnectionError,
    EvChartMissingOrMalformedBodyError,
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.presigned_url import generate_presigned_url
from evchart_helper.s2s_helper import (
    check_valid_api_key, get_api_key_from_event, get_org_by_api_key
)
from evchart_helper.user_helper import get_authorized_drs
from feature_toggle import feature_enablement_check, FeatureToggleService
from feature_toggle.feature_enums import Feature

metadata_table = ModuleDataTables["Metadata"].value


@feature_enablement_check(Feature.S2S)
def handler(event, _context):
    log_event = LogEvent(
        event=event, api="APIPostS2SImportModuleData", action_type="insert"
    )
    log_event.log_info(event)

    features = FeatureToggleService().get_active_feature_toggles(
        log_event=log_event
    )

    try:
        connection = aurora.get_connection()
    except Exception:  # pylint: disable=W0718
        return EvChartDatabaseHandlerConnectionError().get_error_obj()

    try:
        api_key = get_api_key_from_event(event)
        check_valid_api_key(api_key)
        org_id = get_org_by_api_key(api_key)
        body = json.loads(event.get("body"))
        dr_friendly_id = body.get("direct_recipient_id")

        validation_errors = validate_body(body)
        if (
            body.get("email") and
            not validate_email_is_associated_with_active_user_in_org(
                body.get("email"), org_id
            )
        ):
            validation_errors.append(
                f"email {body.get('email')} not in org of given API Key"
            )

        dr_org_id = get_org_id_from_friendly_id(dr_friendly_id)
        if dr_org_id and not sr_can_submit_to_dr(
            connection, org_id, dr_org_id, features
        ):
            validation_errors.append(
                "You are not authorized to submit "
                f"for direct recipient {dr_friendly_id}"
            )

        if len(validation_errors) > 0:
            error_list_string = ", ".join(validation_errors)
            raise EvChartMissingOrMalformedBodyError(
                message=f"Errors found: {error_list_string}"
            )

        # as of right now only SRs will be using the S2S API
        s3_metadata_dict = {
            "checksum": body["checksum"],
            "recipient_type": "sub-recipient",
            "s2s_upload": "True",
        }

        # requires refactor
        import_metadata = build_import_metadata(body, org_id, dr_org_id)
        presigned_url = create_presigned_url(
            new_file_name=get_file_with_path(
                parent_org=import_metadata["parent_org"],
                org_id=org_id,
                upload_id=import_metadata.get("upload_id")
            ),
            metadata=s3_metadata_dict
        )

        upload_import_metadata(connection, import_metadata)

    except (
        EvChartInvalidAPIKey,
        EvChartDynamoConnectionError,
        EvChartMissingOrMalformedBodyError,
        EvChartJsonOutputError,
        EvChartLambdaConnectionError,
        EvChartDatabaseDynamoQueryError,
        EvChartEmailError,
    ) as e:
        log_event.log_custom_exception(
            message=e.message, status_code=e.status_code, log_level=e.log_level
        )
        return e.get_error_obj()

    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps(
            {
                "upload_id": import_metadata.get("upload_id"),
                "presigned_url": presigned_url,
                "presigned_url_headers": build_s3_metadata(s3_metadata_dict),
            }
        ),
    }


def get_org_id_from_friendly_id(friendly_id):
    response = scan_org_by_org_friendly_id(friendly_id)

    try:
        return response.get("org_id")
    except AttributeError:
        return None


def scan_org_by_org_friendly_id(friendly_id):
    items = []
    try:
        dynamodb = boto3_manager.resource("dynamodb")
        table = dynamodb.Table("ev-chart_org")
        response = table.scan(
            FilterExpression=Attr("org_friendly_id").eq(str(friendly_id))
        )
        items = response.get("Items")
        item = None
        if len(items) > 0:
            item = items[0]
    except NoCredentialsError as e:
        raise EvChartDynamoConnectionError(
            message=(
                "an issue occured when searching for org "
                f"from given id {friendly_id}"
            )
        ) from e

    return item


def validate_body(body):
    error_list = []

    error_list.extend(
        validate_body_item(body, "module_id", is_valid_module_id)
    )
    error_list.extend(validate_body_item(body, "checksum", is_valid_checksum))
    error_list.extend(validate_body_item(body, "year", is_valid_module_year))
    error_list.extend(validate_body_item(body, "email", is_valid_email))
    error_list.extend(
        validate_body_item(
            body, "direct_recipient_id", is_valid_direct_recipient_id
        )
    )

    module_id = body.get("module_id")

    quarter = body.get("quarter")
    if not quarter:
        if module_requires_quarter(module_id):
            error_list.append("missing required field: quarter")
    else:
        if module_requires_quarter(module_id):
            if not is_valid_quarter(quarter):
                error_list.append(f"invalid quarter {quarter}")
        else:
            error_list.append(f"quarter not valid for module {module_id}")

    return error_list


def validate_body_item(
    body: dict, arg_name: str, validation_func: Callable[[Any], bool]
) -> List:
    error_list = []
    if body.get(arg_name) is None:
        error_list.append(f"missing required field: {arg_name}")
    else:
        arg_value = body.get(arg_name)
        if not validation_func(arg_value):
            error_list.append(f"invalid {arg_name} of {arg_value}")
    return error_list


def is_valid_checksum(checksum):
    checksum_regex = r"^[A-Fa-f0-9]{64}$"
    return re.fullmatch(checksum_regex, checksum) is not None


def is_valid_module_year(year):
    regex = r"^\d{4}$"
    return re.fullmatch(regex, year) is not None


def is_valid_quarter(quarter):
    quarters = ["1", "2", "3", "4"]
    return quarter in quarters


def is_valid_module_id(module_id):
    modules = ["2", "3", "4", "5", "6", "7", "8", "9"]
    return module_id in modules


def is_valid_email(email):
    email_regex = get_email_regex()
    return re.fullmatch(email_regex, email) is not None


def validate_email_is_associated_with_active_user_in_org(email, org_id):
    key_condition = Key("identifier").eq(email.lower())
    query = Attr("account_status").eq("Active") & Attr("org_id").eq(org_id)
    table_name = "ev-chart_users"
    result = do_items_exist_in_table(
        key_condition,
        query,
        table_name,
        "validate_email_is_associated_with_active_user_in_org",
        email,
    )
    return result


def is_valid_direct_recipient_id(dr_friendly_id):
    dr_id = get_org_id_from_friendly_id(dr_friendly_id)
    key_condition = Key("org_id").eq(dr_id)
    query = Attr("recipient_type").eq("direct-recipient")
    table_name = "ev-chart_org"

    result = do_items_exist_in_table(
        key_condition=key_condition,
        query=query,
        table_name=table_name,
        source_name="validate_direct_recipient_id",
        item_searched=dr_friendly_id
    )
    return result


def do_items_exist_in_table(
    key_condition, query, table_name, source_name, item_searched
):
    items_exists = False
    items = []
    try:
        dynamodb = boto3_manager.resource("dynamodb")
        table = dynamodb.Table(table_name)
        response = table.query(
            KeyConditionExpression=key_condition, FilterExpression=query
        )
        items = response.get("Items")

    except NoCredentialsError as e:
        raise EvChartDynamoConnectionError(
            message=(
                f"issue occured when trying to {source_name} "
                f"for {item_searched}: {repr(e)}"
            )
        ) from e
    # could not find key
    except botocore.exceptions.ClientError:
        pass

    if len(items) > 0:
        items_exists = True
    return items_exists


def build_s3_metadata(metadata_dict):
    metadata = {}
    for key, value in metadata_dict.items():
        metadata[f"x-amz-meta-{key}"] = value

    return metadata


# https://github.doe.gov/Joet/EV-ChART-Application/blob/develop/source/lambda_functions/APIPostImportModuleData/index.py#L97-L116
def create_presigned_url(new_file_name, metadata):
    try:
        response_body = generate_presigned_url(
            file={
                "name": new_file_name,
                "metadata": metadata,
            },
            transfer_type="upload",
            url={
                "expires": "900",
                "url_type": "PUT",
            },
        )

    except botocore.exceptions.ClientError as e:
        raise EvChartLambdaConnectionError(
            f"an issued occured when requesting a presigned URL: {repr(e)}"
        ) from e
    except Exception as e:
        raise EvChartLambdaConnectionError(
            f"an issued occured when requesting a presigned URL: {repr(e)}"
        ) from e
    return response_body


def build_import_metadata(args, org_id, parent_org_id):
    metadata = {}
    status = "Processing"
    try:
        metadata["module_id"] = args.get("module_id")
        metadata["year"] = args.get("year")
        metadata["updated_on"] = str(datetime.datetime.now(tz.gettz("UTC")))
        metadata["updated_by"] = args.get("email")
        metadata["upload_id"] = str(uuid.uuid4())
        metadata["org_id"] = org_id
        metadata["submission_status"] = status
        quarter = get_quarter_for_module(
            metadata["module_id"], args.get("quarter")
        )
        metadata["quarter"] = quarter

        metadata["parent_org"] = parent_org_id

        return metadata
    except Exception as e:
        raise EvChartJsonOutputError(
            message=f"Error building metadata: {repr(e)}"
        ) from e


def get_quarter_for_module(module_id, quarter):
    if module_id in ["2", "3", "4"]:
        return quarter
    return ""


def module_requires_quarter(module_id):
    modules_that_require_quarters = ["2", "3", "4"]
    return module_id in modules_that_require_quarters


# refactor to a common layer
def upload_import_metadata(connection, metadata):
    upload_query = f"""
            INSERT INTO {metadata_table} (
                module_id, year, quarter, org_id,
                parent_org, updated_on,
                updated_by, upload_id, submission_status
            )
            VALUES (
                %(module_id)s, %(year)s, %(quarter)s, %(org_id)s,
                %(parent_org)s, %(updated_on)s,
                %(updated_by)s, %(upload_id)s, %(submission_status)s
            )
            """
    with connection.cursor() as cursor:
        execute_query(
            query=upload_query,
            data=metadata,
            cursor=cursor,
            message="Error thrown in ImportModuleData",
        )
    connection.commit()


# Assumed s2s is only used by sub-recipients
def get_file_with_path(parent_org, org_id, upload_id):
    parent_name = get_org_info_dynamo(parent_org).get("name")
    org_name = get_org_info_dynamo(org_id).get("name")
    new_file_name = f"upload/{parent_name}/{org_name}/{upload_id}.csv"
    return new_file_name


def sr_can_submit_to_dr(connection, sr_id, dr_id, features):
    is_authorized = False
    with connection.cursor() as cursor:
        authorized_drs = get_authorized_drs(
            sr_id,
            cursor,
            n_tier_enabled=Feature.N_TIER_ORGANIZATIONS in features
        )
        if dr_id in authorized_drs:
            is_authorized = True
    return is_authorized
