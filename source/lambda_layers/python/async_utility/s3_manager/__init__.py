"""
async_utility.s3_manager

Helper functions that work with the S3 bucket used with uploading module data.
"""
import logging
from botocore.exceptions import ClientError
from evchart_helper import boto3_manager
from evchart_helper.custom_exceptions import (
    EvChartS3GetObjectError,
)

logger = logging.getLogger()


def get_s3_data(bucket, key):
    """
        Given S3 bucket and object key,
        Returns decoded s3 object body (csv data) and object metadata.
    """
    s3_object = get_s3_object(bucket, key)
    s3_body = s3_object["Body"].read().decode("utf-8")
    s3_metadata = s3_object["Metadata"]
    return s3_body, s3_metadata


def get_s3_object(bucket, key):
    """
        Given S3 bucket and object key,
        Returns S3 object returned from boto3.
    """
    try:
        s3 = boto3_manager.resource("s3")
        response = s3.Object(bucket, key)
        return response.get()
    except ClientError as e:
        raise EvChartS3GetObjectError(
            message=f"Error No such key: {key} in S3 bucket: {bucket} : {e}"
        ) from e
    except Exception as e:
        raise EvChartS3GetObjectError(
            message=(
                f"an error occured while getting s3 object {key} "
                f"from bucket {bucket}: {e}"
            )
        ) from e
