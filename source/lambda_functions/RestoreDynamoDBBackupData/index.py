import logging
from evchart_helper.boto3_manager import boto3_manager

dynamodb_resource = boto3_manager.resource("dynamodb")

logger = logging.getLogger("RestoreDynamoDBBackupData")
logger.setLevel(logging.DEBUG)

# BEGIN CONFIGURATION
DYNAMODB_TEMP_TABLE_NAME = ""
DYNAMODB_TARGET_TABLE_NAME = ""
# END CONFIGURATION


def apply_data_to_target_table(table_data: list) -> None:
    table = dynamodb_resource.Table(DYNAMODB_TARGET_TABLE_NAME)

    with table.batch_writer() as batch:
        for item in table_data:
            batch.put_item(Item=item)


def get_temp_table_data(exclusive_start_key: dict=None) -> list:
    table = dynamodb_resource.Table(DYNAMODB_TEMP_TABLE_NAME)

    options = {}
    if exclusive_start_key:
        options["ExclusiveStartKey"] = exclusive_start_key
    response = table.scan(**options)

    temp_table_data = response.get("Items", [])
    # Recursively call DynamoDB in case of pagination.
    if response.get("LastEvaluatedKey"):
        temp_table_data.extend(get_temp_table_data(response["LastEvaluatedKey"]))

    return temp_table_data


def handler(_event: dict, _context: dict) -> None:
    try:
        temp_table_data = get_temp_table_data()
        apply_data_to_target_table(temp_table_data)

    except Exception as e:
        logger.debug(repr(e))
