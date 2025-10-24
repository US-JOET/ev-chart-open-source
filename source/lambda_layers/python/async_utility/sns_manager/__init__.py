"""
async_utility.sns_manager

Helper functions that work with the SQS queues used in the processing flow for uploaded module data.
"""
from collections import namedtuple
import logging
import os
import json
from pathlib import Path
from time import sleep
from evchart_helper import boto3_manager
from evchart_helper.custom_exceptions import EvChartSQSError

logger = logging.getLogger()

def send_sns_message(attributes, data):
    """
        Helper function to send s3 messages
        Given message attributes and data,
        Publishes message to sns topic,
        Returns bool on success/fail (true/false).
    """
    #logger.debug("send_to_sns attributes: %s; data: %s", attributes, data)
    sns = boto3_manager.client("sns")

    topic_arn = get_topic_arn()
    sns_attributes = {}
    message_group = list(attributes.keys())[0]
    for key, value in attributes.items():
        sns_attributes[key] = {"DataType": "String", "StringValue": value}

    deduplication_id = message_group + '_' + Path(data.get("key")).stem
    try:
        sns.publish(
        TopicArn=topic_arn,
        Message= json.dumps(data),
        MessageAttributes= sns_attributes,
        MessageGroupId=message_group,
        MessageDeduplicationId=deduplication_id
        )
    except Exception:
        return False
    else:
        return True

def get_topic_arn():
    """
        Returns async sns topic arn based on environment/sub-environment
    """
    ssm = boto3_manager.client("ssm")

    sub_environment = os.environ.get("SUBENVIRONMENT")
    sub_environment = f"/{sub_environment}" if sub_environment else ""
    topic_arn = ssm.get_parameter(
            Name=f"/ev-chart/async{sub_environment}/async-topic-arn"
        )["Parameter"]["Value"]

    return topic_arn

def get_org_name_from_path(key):
    """
        Given s3 object key
        Returns org name
    """
    return Path(key).parent.name

def get_parent_org_name_from_path(key):
    """
        Given s3 object key
        Returns parent org name if it exists, otherwise returns None
    """
    parent_org = Path(key).parent.parent.name
    if parent_org.lower() == "uploads":
        return None
    return parent_org

def process_sns_message(record):
    """
        Given SQS record, processes sns message,
        Returns namedtuple that contains:
            sns message
            sns message attributes
            s3 bucket
            s3 object key
            EV-ChART upload_id
            EV-ChART org name
            EV-ChART parent_org name (or None)
            EV-ChART recipient_type
    """
    try:
        message = json.loads(record["body"])
        message_attribute = record.get("messageAttributes")
        key = message.get("key")
        bucket = message.get("bucket")
        if not message_attribute or not key or not bucket:
            raise EvChartSQSError(message="Missing key/attributes")
        logging.info("Proccessing SNS/SQS Message: %s; Message Attributes: %s", message, message_attribute)
        return_obj = namedtuple("Desc", ["message", "message_attribute", "bucket", "key", "upload_id", "org_name", "parent_org", "recipient_type"])
        return return_obj(
            message,
            message_attribute,
            bucket,
            key,
            Path(key).stem,
            get_org_name_from_path(key),
            get_parent_org_name_from_path(key),
            message.get("recipient_type")
        )
    except KeyError as e:
        raise EvChartSQSError(message=f"{repr(e)}")
