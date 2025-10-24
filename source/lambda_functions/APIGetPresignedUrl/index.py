"""
APIGetPresignedUrl

Returns a presigned url that contains a downloadable s3 file.
"""

# TODO: Move the bulk of this to a shared module to remove need for inter-Lambda function
# invokation.
import json
import logging
import os
from pathlib import PurePosixPath
import re
from urllib.parse import urlparse, urlunparse

from endpoints import Endpoints
from exceptions import (
    APIGetPresignedUrlGenerationError,
    APIGetPresignedUrlInvalidQuery
)

from evchart_helper.boto3_manager import boto3_manager
from feature_toggle import feature_enablement_check
from feature_toggle.feature_enums import Feature

logger = logging.getLogger("APIGetPresignedUrl")
logger.setLevel(logging.DEBUG)


def generate_presigned_url(
    url_type: str, expires: int, path: PurePosixPath, metadata: dict
) -> dict:
    s3_client = boto3_manager.client(
        "s3", endpoint_url=f"https://bucket.{Endpoints[os.environ['ENVIRONMENT'].upper()].value}"
    )

    environment_part = os.environ.get("SUBENVIRONMENT") or os.environ["ENVIRONMENT"]
    bucket = f"ev-chart-artifact-data-{environment_part}-{os.environ['AWS_REGION']}"
    object_key = str(path) if not path.is_absolute() else str(path)[1:]
    expires = min(expires, 900)

    try:
        presigned_url = None
        if url_type == "GET":
            presigned_url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": object_key},
                ExpiresIn=expires
            )

        elif url_type == "POST":
            presigned_url = s3_client.generate_presigned_post(
                Bucket=bucket,
                Key=object_key,
                ExpiresIn=expires,
                Fields=metadata,
                Conditions=[
                    ["starts-with", "$x-amz-meta-recipient_type", ""],
                    ["starts-with", "$x-amz-meta-checksum", ""]
                ]
            )

        elif url_type == "PUT":
            presigned_url = s3_client.generate_presigned_url(
                "put_object",
                Params={"Bucket": bucket, "Key": object_key, "Metadata": metadata},
                ExpiresIn=expires
            )

    except Exception as e:
        raise APIGetPresignedUrlGenerationError() from e

    if not isinstance(presigned_url, dict):
        presigned_url = {"url": presigned_url}

    environment_part = "" if environment_part == "prod" else f"-{environment_part}"
    _url = urlparse(presigned_url["url"])
    _url = _url._replace(
        netloc=f"evchart{environment_part}.driveelectric.gov",
        path=re.sub(f"/{bucket}", "/files", _url.path)
    )
    presigned_url["url"] = urlunparse(_url)

    return presigned_url


@feature_enablement_check(Feature.PRESIGNED_URL)
def handler(event: dict, _context: dict) -> dict:
    response = {
        "body": json.dumps([]),
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
        },
        "statusCode": 200
    }

    parameters = event.get("queryStringParameters")

    try:
        if not parameters:
            raise APIGetPresignedUrlInvalidQuery()

        expires = parameters.get("expires")
        metadata = parameters.get("metadata")
        path = parameters.get("path")
        url_type = parameters.get("type", "").upper()

        if (
            url_type not in ["GET", "POST", "PUT"]
            or not expires or not expires.isdigit()
            or not path
        ):
            raise APIGetPresignedUrlInvalidQuery()

        presigned_url = generate_presigned_url(
            url_type, int(expires), PurePosixPath(path), metadata
        )
        response["body"] = presigned_url

    except (
        APIGetPresignedUrlGenerationError,
        APIGetPresignedUrlInvalidQuery
    ) as e:
        message = {"message": str(e)}
        logger.debug(json.dumps(message | {"base_exception": str(e.__cause__)}))

        response |= {
            "body": json.dumps(message),
            "statusCode": e.status_code
        }

    return response
