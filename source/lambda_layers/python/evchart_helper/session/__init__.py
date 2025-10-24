"""
evchart_helper.session

Helper module that handles validation of the user's session when requests come in to the API.
"""
from http.cookies import SimpleCookie
import os

from evchart_helper.boto3_manager import boto3_manager

dynamodb_resource = boto3_manager.resource("dynamodb")


class SessionManager: # pylint: disable=too-few-public-methods

    @staticmethod
    def check_session():
        """
            Used to grab the cookie from headers. Returns 403 if session is not
            valid (and env not dev).
        """
        def decorator(function):
            def wrapper(*args):
                event = args[0]
                event_cookies = (
                    event["headers"].get("Cookie", "")
                        or event["headers"].get("cookie", "")
                )

                user_session = SessionManager(event_cookies)
                if os.environ.get("ENVIRONMENT") not in ["dev"] and not user_session.session_valid:
                    return {
                        "statusCode": 403,
                        "headers": { "Access-Control-Allow-Origin": "*" },
                        "body": "Invalid session."
                    }

                return function(*args)

            return wrapper

        return decorator

    def __init__(self, cookie):
        """
            Collects cookie and user info, returns bool
            on session validity.
        """
        session_info = None

        self.identifier = None
        self.refresh_token = None

        if cookie:
            self._session_id = self.__get_session_from_cookie(cookie)
            if self._session_id:
                session_info = self.__get_user_info_from_session()
                if session_info:
                    session_info = session_info[0]
                    self.identifier = session_info["identifier"].lower()
                    self.refresh_token = session_info["refresh_token"]

        self.session_valid = bool(session_info)

    def __get_session_from_cookie(self, cookie):
        """
            Returns cookie or None from given session.
        """
        request_cookies = SimpleCookie()
        request_cookies.load(cookie)
        session_cookie = request_cookies.get("__Host-session_id")

        return session_cookie.value if session_cookie else None

    def __get_user_info_from_session(self):
        """
            Returns all info from Dynamo users table
            based on given session_id.
        """
        table = dynamodb_resource.Table("ev-chart_users")
        response = table.query(
            ExpressionAttributeNames={
                "#SID": "session_id"
            },
            ExpressionAttributeValues={
                ":sid": self._session_id
            },
            IndexName="gsi_session_id",
            KeyConditionExpression="#SID = :sid",
        ).get("Items")

        return response

    def clear_session(self):
        """
            If session is valid, updates Dynamo
            users table session_id field to None.
        """
        if not self.session_valid:
            return

        table = dynamodb_resource.Table("ev-chart_users")
        table.update_item(
            ExpressionAttributeNames={
                "#SID": "session_id"
            },
            ExpressionAttributeValues={
                ":sid": "None"
            },
            Key={
                "identifier": self.identifier.lower()
            },
            UpdateExpression="SET #SID = :sid"
        )

    def get_session_id(self):
        return self._session_id
