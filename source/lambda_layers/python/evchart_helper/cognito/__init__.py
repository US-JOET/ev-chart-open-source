"""
evchart_helper.cognito

A module that provides helper details for the AWS Cognito implementation, generally for use with the
Lambda functions that involve generation of the JWT.
"""
import base64
import os

from evchart_helper.boto3_manager import boto3_manager

cognito_client = boto3_manager.client("cognito-idp")
ssm_client = boto3_manager.client("ssm")


class CognitoUserPool: # pylint: disable=too-few-public-methods

    def __init__(self):
        user_pool_data = self.__get_user_pool_info()

        self.callback_urls = user_pool_data["user_pool_callback_urls"]
        self.client_id = user_pool_data["user_pool_client_id"]
        self.client_secret = user_pool_data["user_pool_client_secret"]
        self.domain = user_pool_data["user_pool_domain"]
        self.logout_urls = user_pool_data["user_pool_logout_urls"]
        self.id = user_pool_data["user_pool_id"]

    def __get_user_pool_info(self):
        """
            Build a dict that contains the information for the deployed AWS Cognito user pool and
            client.
        """
        parameters_response = {
            parameter["Name"]: parameter["Value"]
            for parameter in ssm_client.get_parameters_by_path(
                Path="/ev-chart/cognito",
                Recursive=True
            )["Parameters"]
        }

        sub_environment = os.environ.get("SUBENVIRONMENT")
        sub_environment_path = f"/{sub_environment}" if sub_environment else ""
        user_pool_client_id = parameters_response[f"/ev-chart/cognito{sub_environment_path}/user_pool_client_id"] # pylint: disable=line-too-long

        client_response = cognito_client.describe_user_pool_client(
            ClientId=user_pool_client_id,
            UserPoolId=parameters_response["/ev-chart/cognito/user_pool_id"]
        )["UserPoolClient"]

        user_pool_data = {
            "user_pool_callback_urls": client_response["CallbackURLs"],
            "user_pool_client_id": user_pool_client_id,
            "user_pool_client_secret": client_response["ClientSecret"],
            "user_pool_domain": parameters_response["/ev-chart/cognito/user_pool_domain"],
            "user_pool_logout_urls": client_response["LogoutURLs"],
            "user_pool_id": parameters_response["/ev-chart/cognito/user_pool_id"]
        }

        return user_pool_data

    def get_basic_auth_string(self):
        """
            Returns the basic auth string for the relevant AWS Cognito user pool client.
        """
        base_string_b = (
            f"{self.client_id}:{self.client_secret}".encode("utf-8")
        )

        return base64.b64encode(base_string_b).decode("utf-8")


cognito = CognitoUserPool()
