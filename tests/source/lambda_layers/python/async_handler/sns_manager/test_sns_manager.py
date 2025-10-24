import json
import pytest
from async_utility.sns_manager import process_sns_message
from evchart_helper.custom_exceptions import EvChartSQSError

upload_file_path = "./tests/sample_data/all_columns_module_9.csv"
upload_checksum = "0d810e7fbf2f435b93a7b51d26e7df28e3b8747a322a33dcf2a4db8dbae63ce0"
upload_id = "852ade96-4075-4766-9b97-5e9379b31ab0.csv"
upload_bucket_name = "ev-chart-artifact-data-unit-test"

invalid_file_upload_id = "bad_file.csv"
invalid_file_path = "./tests/sample_data/all_invalid_data_type_mod_9.csv"

def get_event_object(key):
    body = json.dumps({"key": f"{key}", "bucket": "ev-chart-artifact-data-unit-test", "recipient_type": "test"})
    event_object = {
        "Records": [
            {
                "messageId": "51248983-6efb-45b0-9cda-f46361fa9d72",
                "receiptHandle": "AQEBqCbgdpKlmJL40F05hhpnE1xeptUFxy",
                "body": body,
                "attributes": {
                    "ApproximateReceiveCount": "103",
                    "AWSTraceHeader": "Root=1-668eec57-5e679a8a2d0a16b4648ed22a;Parent=6c23033f58bdb3e0;Sampled=0;Lineage=55dd22b6:0",
                    "SentTimestamp": "1720642650042",
                    "SequenceNumber": "18887228592120303616",
                    "MessageGroupId": "file-integrity",
                    "SenderId": "AIDAYRRVD2ENU4DSO2WBX",
                    "MessageDeduplicationId": "45afed0266b31e646042a6ba6df527f9f56fd03ffffe2394a25bc26c0daf1393",
                    "ApproximateFirstReceiveTimestamp": "1720642650042",
                },
                "messageAttributes": {
                    "file-integrity": {
                        "stringValue": "passed",
                        "stringListValues": [],
                        "binaryListValues": [],
                        "dataType": "String",
                    }
                },
                "md5OfBody": "4e526238faa82b32acce4a960b3ce94b",
                "md5OfMessageAttributes": "ff166bff27dc389fd27095b28acb74b8",
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:414275662771:evchart-file-integrity.fifo",
                "awsRegion": "us-east-1",
            }
        ]
    }
    return event_object

def get_file_content(file_path):
    with open(file_path, "rb") as f:
        return f.read()

def test_extract_message_given_valid_record_return_message():
    key = "testing_datavalidation2.csv"
    bucket = "ev-chart-artifact-data-unit-test"
    event_object = get_event_object(key)
    message_record = event_object["Records"][0]
    message = process_sns_message(message_record)

    assert message.key == key
    assert message.bucket == bucket

def test_extract_message_given_no_body_throws_error():
    event_object = get_event_object(upload_id)
    message_record = event_object["Records"][0]
    del message_record["body"]
    with pytest.raises(EvChartSQSError):
        process_sns_message(message_record)

def test_extract_message_given_no_attributes_throws_error():
    event_object = get_event_object(upload_id)
    message_record = event_object["Records"][0]
    del message_record["messageAttributes"]
    with pytest.raises(EvChartSQSError):
        process_sns_message(message_record)

def test_extract_message_given_no_bucket_in_body_raise_error():
    event_object = get_event_object(upload_id)
    message_record = event_object["Records"][0]
    message_record["body"] = '{"key": "testing_datavalidation2.csv"}'
    with pytest.raises(EvChartSQSError):
        process_sns_message(message_record)

def test_extract_message_given_no_key_in_body_raise_error():
    event_object = get_event_object(upload_id)
    message_record = event_object["Records"][0]
    message_record["body"] = '{"bucket": "ev-chart-artifact-data-unit-test"}'
    with pytest.raises(EvChartSQSError):
        process_sns_message(message_record)
