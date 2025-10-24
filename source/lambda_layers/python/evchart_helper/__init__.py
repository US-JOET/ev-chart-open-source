"""
evchart_helper

A primary helper module for the application the contains many ease-of-use function and class
definitions.  This file contains the Aurora and ApplicationStatus helper classes.
"""
import json
import logging
import os
import time
import pymysql

from evchart_helper.boto3_manager import boto3_manager

cloudwatch_client = boto3_manager.client("cloudwatch")
secretsmanager_client = boto3_manager.client("secretsmanager")
ssm_client = boto3_manager.client("ssm")

logger = logging.getLogger("AuroraDatabase")
logger.setLevel(logging.DEBUG)


class ApplicationStatus:

    def __init__(self, event):
        self._user_scope = (
            event["requestContext"]["authorizer"]["claims"].get("org_type") or
            event["requestContext"]["authorizer"]["claims"].get("scope")
        )

    def is_maintenance(self):
        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_path = f"/{sub_environment}" if sub_environment else ""

        return ssm_client.get_parameter(
            Name=f"/ev-chart/status{sub_environment_path}/maintenance"
        )["Parameter"]["Value"] == "True"

    def user_is_permitted(self):
        return (not self.is_maintenance()) or self._user_scope == "joet"


class AuroraDatabaseBaseException(Exception):
    """Base exception class for AuroraDatabase."""


class AuroraDatabaseCloudWatchPushMetricError(AuroraDatabaseBaseException):
    """
    AuroraDatabase exception class for errors stemming from failing to push CloudWatch custom metric
    data.
    """
    def __init__(self, *args):
        if not args:
            args = (
                "There was an issue pushing CloudWatch custom metric data.",
            )

        super().__init__(*args)


class AuroraDatabase:

    @staticmethod
    def __push_metric(connect_elapsed_time):
        try:
            cloudwatch_client.put_metric_data(
                Namespace="EV-ChART",
                MetricData=[
                    {
                        "Dimensions": [
                            {
                                "Name": "FunctionName",
                                "Value": os.environ["AWS_LAMBDA_FUNCTION_NAME"]
                            }
                        ],
                        "MetricName": "DBConnectionTime",
                        "Unit": "Milliseconds",
                        "Value": connect_elapsed_time,
                    },
                    {
                        "Dimensions": [
                            {
                                "Name": "FunctionName",
                                "Value": "All Functions"
                            }
                        ],
                        "MetricName": "DBConnectionTime",
                        "Unit": "Milliseconds",
                        "Value": connect_elapsed_time,
                    }
                ]
            )

        except Exception as e:
            raise AuroraDatabaseCloudWatchPushMetricError() from e

    def __get_db_parameters(self):
        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_path = \
            f"/{sub_environment}" if sub_environment else ""

        self._db_parameters = {
            parameter["Name"].split("/")[-1]: parameter["Value"]
            for parameter in ssm_client.get_parameters_by_path(
                Path=f"/ev-chart/aurora{sub_environment_path}"
            )["Parameters"]
        }
        self._db_credentials = json.loads(secretsmanager_client.get_secret_value(
            SecretId=self._db_parameters["master_user_secret_arn"]
        )["SecretString"])

    def __init__(self):
        self._db_connection = None
        self._db_credentials = None
        self._db_parameters = None

    def close_connection(self):
        self._db_connection.close()
        self._db_connection = None

    def get_connection(self, use_read_only=False):
        if self._db_connection and self._db_connection.open:
            self.close_connection()

        self.__get_db_parameters()

        connection_params = {
            "host": self._db_parameters["endpoint_address"],
            "password": self._db_credentials["password"],
            "port": int(self._db_parameters["endpoint_port"]),
            "user": self._db_credentials["username"],
            "database": self._db_parameters.get("evchart-database-name")
        }

        from feature_toggle import FeatureToggleService # pylint:disable=C0415
        from feature_toggle.feature_enums import Feature # pylint:disable=C0415

        feature_toggle_service = FeatureToggleService()
        if not use_read_only and feature_toggle_service.get_feature_toggle_by_enum(
            Feature.USE_RDS_PROXY, logger
        ) == "True":
            connection_params["host"] = self._db_parameters["proxy_endpoint_address"]

        elif use_read_only:
            connection_params["host"] = self._db_parameters["read_endpoint_address"]

        connect_start_time = time.time_ns()
        self._db_connection = pymysql.connect(**connection_params)
        # Total time to connect in milliseconds.
        connect_elapsed_time = (time.time_ns() - connect_start_time) / 1e+6

        if os.environ["ENVIRONMENT"] in ["dev"]:
            try:
                AuroraDatabase.__push_metric(connect_elapsed_time)

            except AuroraDatabaseCloudWatchPushMetricError as e:
                logger.debug(json.dumps({
                    "exception": str(e),
                    "base_exception": str(e.__cause__)
                }))

        self._db_connection.ping()
        return self._db_connection

aurora = AuroraDatabase()
