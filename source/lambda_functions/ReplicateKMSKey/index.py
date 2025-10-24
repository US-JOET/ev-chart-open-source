"""
ReplicateKMSKey

A function run as part of a CloudFormation custom resource, it will replicate the "ev-chart/general"
KMS multi-region key to the specified region.  This is not a process supported by CloudFormation
natively and must be done in this, or a similar, way.
"""
import logging

import cfnresponse
from evchart_helper.boto3_manager import boto3_manager

kms_client = boto3_manager.client("kms")
kms_client_dr = boto3_manager.client("kms", region_name="us-east-2")

logger = logging.getLogger("ReplicateKMSKey")
logger.setLevel(logging.INFO)


def get_primary_kms_id():
    return kms_client.describe_key(
        KeyId="alias/ev-chart/general"
    )["KeyMetadata"]["KeyId"]


def get_primary_kms_policy(primary_kms_id):
    return kms_client.get_key_policy(
        KeyId=primary_kms_id,
        PolicyName="default"
    )["Policy"]


def handler(event, context):
    request_type = event["RequestType"]
    status = cfnresponse.SUCCESS

    try:
        if request_type == "Create":
            primary_kms_id = get_primary_kms_id()
            primary_kms_policy = get_primary_kms_policy(primary_kms_id)

            try:
                kms_client.replicate_key(
                    # The Lambda is not managing the key beyond making it; the policy allows normal
                    # IAM users to manage it.
                    BypassPolicyLockoutSafetyCheck=True,
                    Description="General EV-ChART CMK replica.",
                    KeyId=primary_kms_id,
                    Policy=primary_kms_policy,
                    ReplicaRegion="us-east-2"
                )

            except kms_client.exceptions.AlreadyExistsException:
                logger.info("Key already exists; ignoring replication.")

            try:
                kms_client_dr.create_alias(
                    AliasName="alias/ev-chart/general",
                    TargetKeyId=primary_kms_id
                )

            except kms_client_dr.exceptions.AlreadyExistsException:
                logger.info("Key alias already exists; updating.")

                kms_client_dr.update_alias(
                    AliasName="alias/ev-chart/general",
                    TargetKeyId=primary_kms_id
                )

    except Exception as e: # pylint: disable=broad-exception-caught
        logger.exception(e)

        status = cfnresponse.FAILED

    cfnresponse.send(event, context, status, {})
