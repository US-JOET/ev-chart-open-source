"""
IdleUserReport

On a schedule, manage the user table in DynamoDB and set appropriate statuses based on the last time
the user logged in.  Pending (waiting for first login) users will be set to Expired after 30 days
and Active users will be set to Deactivated once idle (have not logged in) for more than 400 days.
"""
from datetime import datetime, timedelta, UTC
import os

from evchart_helper.boto3_manager import boto3_manager
from evchart_helper.custom_logging import LogEvent
from evchart_helper.custom_exceptions import EvChartDatabaseDynamoQueryError


class IdleUserReport:
    def __init__(self, log_event):
        self.expirations = []
        self.deactivations = []
        self.now = datetime.now(UTC)
        self.log_event = log_event

        self.dynamodb = boto3_manager.resource('dynamodb')
        self.ssm = boto3_manager.client("ssm")

        self.max_idle_time, self.max_pending_time = \
            (timedelta(days=x) for x in self.time_parameters())
        self.table = self.dynamodb.Table(self.table_name())

    def get_parameters(self, path):
        parameter_list = self.ssm.get_parameters_by_path(Path=path)
        return {
            p["Name"]: p
            for p in parameter_list.get("Parameters", [])
        }

    def table_name(self):
        parameter_prefix = "/ev-chart/dynamodb/"
        parameter_name = "table"
        default = "ev-chart_users"
        dynamodb_parameters = self.get_parameters(parameter_prefix)
        try:
            return dynamodb_parameters[
                f"{parameter_prefix}{parameter_name}"
            ]["Value"]
        except ValueError:
            return default

    def time_parameters(self):
        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_path = f"/{sub_environment}" if sub_environment else ""

        prefix = f"/ev-chart/lambda{sub_environment_path}/idle-user-report/"
        dynamodb_parameters = self.get_parameters(prefix)

        try:
            max_idle = int(dynamodb_parameters[f"{prefix}max-idle"]["Value"])
        except (KeyError, TypeError):
            max_idle = 60

        try:
            max_pending = \
                int(dynamodb_parameters[f"{prefix}max-pending"]["Value"])
        except (KeyError, TypeError):
            max_pending = 14

        return max_idle, max_pending

    def check_pending_account(self, item):
        if item.get('account_status') == 'Pending':
            last_status = \
                datetime.fromisoformat(item.get('last_generated', str(datetime.now(UTC))))
            if self.now - last_status > self.max_pending_time:
                self.expirations.append(item['identifier'])

    def check_idle_account(self, item):
        if 'last_generated' in item:
            last_generated = datetime.fromisoformat(item['last_generated'])
            if self.now - last_generated > self.max_idle_time:
                self.deactivations.append(item['identifier'])

    def parse_response(self, response):
        for item in response.get('Items', []):
            self.check_idle_account(item)
            self.check_pending_account(item)

    def scan_accounts(self):
        try:
            response = self.table.scan()
            self.parse_response(response)
            while "LastEvaluatedKey" in response:
                response = self.table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                self.parse_response(response)
        except Exception as e:
            raise EvChartDatabaseDynamoQueryError(
                operation="SELECT",
                log_obj=self.log_event,
                message=f"IdleUserReport unable to scan table: {e}"
            ) from e

    def set_expirations_deactivations(self):
        for identifier in self.expirations:
            try:
                self.table.update_item(
                    Key={'identifier': identifier},
                    UpdateExpression='SET account_status = :status',
                    ExpressionAttributeValues={':status': "Expired"}
                )
                self.log_event.log_successful_request(
                    message=f"set user to expired: [{identifier}]",
                    status_code=201
                )
            except Exception as e:
                raise EvChartDatabaseDynamoQueryError(
                    operation="INSERT",
                    log_obj=self.log_event,
                    message=(
                        f"IdleUserReport unable to expire user {identifier}: "
                        f"{e}"
                    )
                ) from e

        for identifier in self.deactivations:
            try:
                self.table.update_item(
                    Key={'identifier': identifier},
                    UpdateExpression='SET account_status = :status',
                    ExpressionAttributeValues={':status': "Deactivated"}
                )
                self.log_event.log_successful_request(
                    message=f"set user to deactivated: [{identifier}]",
                    status_code=201
                )
            except Exception as e:
                raise EvChartDatabaseDynamoQueryError(
                    operation="INSERT",
                    log_obj=self.log_event,
                    message=(
                        f"IdleUserReport unable to deactivate user "
                        f"[{identifier}]: {e}"
                    )
                ) from e

    def summary(self):
        return {
            'expirations': self.expirations,
            'deactivations': self.deactivations
        }


def handler(event, _context):
    log_event = LogEvent(
        event=event, api="IdleUserReport", action_type="MODIFY"
    )
    idle_user_report = IdleUserReport(log_event=log_event)
    idle_user_report.scan_accounts()
    idle_user_report.set_expirations_deactivations()
    return idle_user_report.summary()


if __name__ == "__main__":
    print(handler(None, None))
