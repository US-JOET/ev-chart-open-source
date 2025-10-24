"""
evchart_helper.presigned_url

Helper module that handles requests for a presigned URL and invoking the relevant Lambda function to
generate it.
"""
import json
import logging
import os
from uuid import uuid4

from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.presigned_url.exceptions import (
    EVChARTHelperPresignedURLParametersError,
    EVChARTHelperPresignedURLLambdaError,
    EVChARTHelperPresignedURLS3Error,
)

lambda_client = boto3_manager.client("lambda")
s3_resource = boto3_manager.resource("s3")

logger = logging.getLogger("PresignedURLHelper")
logger.setLevel(logging.DEBUG)


def generate_presigned_url(
    file: dict["data": str, "name": str, "metadata": dict],
    transfer_type: str,
    url: dict["expires": str, "url_type": str] = None,
) -> dict:
    if not url:
        url = {
            "expires": "900",
            "url_type": "GET",
        }

    environment = os.environ.get("SUBENVIRONMENT") or os.environ["ENVIRONMENT"]

    try:
        if (
            not file.get("name")
            or transfer_type not in ["download", "upload"]
            or transfer_type == "download" and not file.get("data")
            or url["url_type"] not in ["GET", "POST", "PUT"]
        ):
            raise EVChARTHelperPresignedURLParametersError() from Exception(json.dumps({
                "file": file,
                "transfer_type": transfer_type,
                "url": url,
            }))

        object_path = (file["name"]
            if transfer_type == "upload"
            else __send_to_s3(
                data=file["data"],
                name=file["name"],
                transfer_type=transfer_type,
                environment=environment,
            ))

        response = __invoke_lambda(
            expires=url["expires"],
            metadata=file.get("metadata"),
            object_path=object_path,
            url_type=url["url_type"],
            environment=environment,
        )

    except (
        EVChARTHelperPresignedURLParametersError,
        EVChARTHelperPresignedURLLambdaError,
        EVChARTHelperPresignedURLS3Error,
    ) as e:
        message = {"message": str(e)}
        logger.debug(json.dumps(message | {"base_exception": str(e.__cause__)}))

        response = {
            "error": json.dumps(message),
        }

    return response


def __invoke_lambda(
    expires: str,
    metadata: dict,
    object_path: str,
    url_type: str,
    environment: str,
) -> dict:
    lambda_environment_part = f"_{environment}" if os.environ.get("SUBENVIRONMENT") else ""

    try:
        response = json.loads(lambda_client.invoke(
            FunctionName=f"EV-ChART_APIGetPresignedUrl{lambda_environment_part}",
            Payload=bytes(
                json.dumps({
                    "queryStringParameters": {
                        "expires": expires,
                        "metadata": metadata,
                        "path": object_path,
                        "type": url_type,
                    },
                }),
                "utf-8",
            ),
        )["Payload"].read())

        if response["statusCode"] != 200:
            raise RuntimeError(json.dumps(response["body"]))

    except Exception as e:
        raise EVChARTHelperPresignedURLLambdaError() from e

    return response["body"]


def __send_to_s3(data: str, name: str, transfer_type: str, environment: str) -> str:
    bucket = f"ev-chart-artifact-data-{environment}-{os.environ['AWS_REGION']}"
    object_path = f"{transfer_type}/{str(uuid4())}/{name}"

    try:
        s3_resource.Object(bucket, object_path).put(Body=data)

    except Exception as e:
        raise EVChARTHelperPresignedURLS3Error() from e

    return object_path
