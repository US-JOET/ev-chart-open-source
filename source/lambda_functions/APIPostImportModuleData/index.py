"""
APIPostImportModuleData

Generally, will provide a presigned URL so as to enable the user to upload their CSV module data to
S3 to be processed asynchronously.  Still contains deprecated code remnants (disabled via feature
toggle) that provides synchronous transfer to S3 directly.
"""
import datetime
import json
import logging
import os
import uuid
from dateutil import tz
from evchart_helper import aurora
from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.api_helper import execute_query, get_org_info_dynamo
from evchart_helper.custom_exceptions import (
    EvChartAuthorizationTokenInvalidError,
    EvChartDatabaseAuroraQueryError,
    EvChartDatabaseHandlerConnectionError,
    EvChartFeatureStoreConnectionError,
    EvChartInvalidCSVError,
    EvChartInvalidDataError,
    EvChartJsonOutputError,
    EvChartMissingOrMalformedBodyError,
    EvChartMissingOrMalformedHeadersError,
    EvChartModuleValidationError,
    EvChartUserNotAuthorizedError,
    EvChartAsynchronousS3Error
)
from evchart_helper.custom_logging import LogEvent
from evchart_helper.database_tables import ModuleDataTables
from evchart_helper.presigned_url import generate_presigned_url
from evchart_helper.session import SessionManager
from feature_toggle import FeatureToggleService
from feature_toggle.feature_enums import Feature

import_metadata = ModuleDataTables["Metadata"].value

logger = logging.getLogger("APIPostImportModuleData")
logger.setLevel(logging.DEBUG)


@SessionManager.check_session()
def handler(event, _context):
    log_event = LogEvent(
        event=event, api="APIPostImportModuleData", action_type="insert"
    )
    logging.debug(event)
    try:
        connection = aurora.get_connection()
    except Exception: # pylint: disable=W0718
        return EvChartDatabaseHandlerConnectionError().get_error_obj()

    try:
        # feature must be called in the handler in order to get the
        # current value every time, and not a value persisted by Lambda warm start
        # https://docs.aws.amazon.com/lambda/latest/operatorguide/global-scope.html
        # pylint: disable=duplicate-code
        feature_toggle_set = FeatureToggleService().get_active_feature_toggles(log_event=log_event)

        if log_event.is_auth_token_valid() is False:
            raise EvChartAuthorizationTokenInvalidError(
                message="Invalid authorization token"
            )
        token = log_event.get_auth_token()
        email = token.get("email")

        request_headers = event["headers"]
        logging.debug("Headers: %s", request_headers)
        recipient_type = token.get("recipient_type")
        response_body = {}


        metadata = build_metadata(request_headers, email, "Processing")
        upload_metadata(connection, metadata)

        if Feature.PRESIGNED_URL in feature_toggle_set:
            upload_id = metadata["upload_id"]
            org_name = token.get("org_name")
            parent_org = request_headers.get("parent_org")
            checksum = request_headers["checksum"]

            if recipient_type == 'direct-recipient':
                new_file_name = f"upload/{org_name}/{upload_id}.csv"
            elif recipient_type == 'sub-recipient':
                parent_name = get_org_info_dynamo(parent_org)["name"]
                new_file_name = f"upload/{parent_name}/{org_name}/{upload_id}.csv"
            else:
                new_file_name = f"testing/{org_name}/{upload_id}.csv"

            response_body = generate_presigned_url(
                file={
                    "name": new_file_name,
                    "metadata": {
                        "x-amz-meta-checksum": checksum,
                        "x-amz-meta-recipient_type": recipient_type
                    },
                },
                transfer_type="upload",
                url={
                    "expires": "900",
                    "url_type": "POST",
                }
            )

        else:
            upload_to_s3_from_raw(event["body"],metadata["upload_id"], request_headers, token)

    except (
        EvChartFeatureStoreConnectionError,
        EvChartDatabaseHandlerConnectionError,
        EvChartAuthorizationTokenInvalidError,
        EvChartMissingOrMalformedHeadersError,
        EvChartMissingOrMalformedBodyError,
        EvChartUserNotAuthorizedError,
        EvChartDatabaseAuroraQueryError,
        EvChartJsonOutputError,
        EvChartInvalidDataError,
        EvChartModuleValidationError,
        EvChartAsynchronousS3Error,
    ) as e:
        log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
        return_obj = e.get_error_obj()
        return_obj['body'] = json.dumps({
            'upload_success': False,
            'error_message': e.message
        })
    except (
        EvChartInvalidCSVError
    ) as e:
        log_event.log_custom_exception(
                message=e.message,
                status_code=e.status_code,
                log_level=e.log_level
            )
        return_obj = e.get_error_obj()
        return_obj['body'] = json.dumps({
            'upload_success': False,
            'upload_id': metadata['upload_id'],
            'error_count': 0
        })
    else:
        log_event.log_successful_request(
            message=(
                f"Successfully imported module data for upload "
                f"{metadata['upload_id']}"
            ),
            status_code=201
        )

        return_obj = {
            'statusCode': 201,
            'headers': {"Access-Control-Allow-Origin": "*"},
            'body': json.dumps(response_body | {
                'upload_success': True,
                'upload_id': metadata['upload_id'],
                'is_submitting_null': metadata.get('is_submitting_null'),
                'error_count': 0
            })
        }

    return return_obj

def upload_metadata(connection, metadata):
    upload_query = f"""
            INSERT INTO {import_metadata} (
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
                    message="Error thrown in ImportModuleData"
                )
    connection.commit()


def build_metadata(request_headers, email, status="Draft"):
    metadata = {}
    try:
        metadata["module_id"] = request_headers["module_id"]
        metadata["year"] = request_headers["year"]
        metadata["updated_on"] = str(datetime.datetime.now(tz.gettz("UTC")))
        metadata["updated_by"] = email
        metadata["upload_id"] = str(uuid.uuid4())
        metadata["org_id"] = request_headers["org_id"]
        metadata["submission_status"] = status
        metadata["quarter"] = check_quarter(metadata["module_id"], request_headers["quarter"])

        if request_headers["parent_org"]:
            metadata["parent_org"] = request_headers["parent_org"]
        else:
            metadata["parent_org"] = request_headers["org_id"]

        return metadata
    except Exception as e:
        raise EvChartJsonOutputError(
            message=f"Error building metadata: {e}"
        ) from e


def check_quarter(module_id, quarter):
    if module_id in ["2", "3", "4"]:
        return quarter
    return ""

def upload_to_s3_from_raw(raw_data, upload_id, request_headers, token):
    if "checksum" in request_headers:
        checksum = request_headers["checksum"]
    else:
        raise EvChartMissingOrMalformedHeadersError("missing checksum in headers")
    try:
        # account for sub environment
        bucket_name = get_async_bucket()
        org_name = token.get("org_name")
        parent_org = request_headers.get("parent_org")
        recipient_type = token.get("recipient_type")
        new_file_name = ""

        if recipient_type == 'direct-recipient':
            new_file_name = f"upload/{org_name}/{upload_id}.csv"
        elif recipient_type == 'sub-recipient':
            parent_name = get_org_info_dynamo(parent_org)["name"]
            new_file_name = f"upload/{parent_name}/{org_name}/{upload_id}.csv"
        else:
            new_file_name = f"testing/{org_name}/{upload_id}.csv"

        s3 = boto3_manager.resource('s3')
        custom_metadata = {
            'checksum': checksum,
            'recipient_type': recipient_type
        }

        s3.Bucket(bucket_name).put_object(
            Key= new_file_name,
            Body= raw_data,
            Metadata = custom_metadata
        )

        return True
    except Exception as e:
        raise EvChartAsynchronousS3Error(
            message=f"Error uploading {upload_id} to S3 bucket: {e}"
        ) from e

def get_async_bucket():
    sub_environment = os.environ.get("SUBENVIRONMENT")
    sub_environment_path = f"/{sub_environment}" if sub_environment else ""
    ssm_client = boto3_manager.client("ssm")

    # return 'ev-chart-artifact-data-dev-us-east-1'
    return ssm_client.get_parameter(
        Name=f"/ev-chart/s3{sub_environment_path}/async-artifact-bucket-name"
    )["Parameter"]["Value"]
