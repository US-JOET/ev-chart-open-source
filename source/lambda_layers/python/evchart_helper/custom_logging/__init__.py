"""
evchart_helper.custom_logging

Logging functions are referenced in both api functions and Exceptions.py
helper file. There are 2 classes: LogError and LogEvent
LogEvent: Class that logs all successful requests and errors raised
"""

import copy
import logging
import json
import os

logger = logging.getLogger("EV-ChART_Logging")
logger.setLevel(logging.INFO)


# common log messages for all APIs
class LogEvent:
    # pylint: disable=too-many-instance-attributes
    """Logs first api invocation and successful requests"""

    def __init__(self, event, api, action_type):
        """
        Constructor used to create log object and also logs first
        api invocation

        Arguments:
            event -- event passed in from handler

            api -- name of api folder

            action_type -- "READ", "MODIFY", "CREATE"

        Invocation Example:
            log = LogEvent(event, "APIPostStation", "create")
        """
        # sets attributes for all events
        self.application = "EV-ChART"
        self.log_level = 6
        self.api = api
        self.operation = api
        self.action_type = action_type.upper()
        self.result = "SUCCESS"
        self.valid_auth_token = None
        self.message = None
        self.status_code = None
        self.module_info = None

        try:
            environment = os.environ.get(
                "SUBENVIRONMENT", os.environ["ENVIRONMENT"]
            )
            self.environment = environment

            if "claims" in event["requestContext"]["authorizer"]:
                claims = event["requestContext"]["authorizer"]["claims"]
                self.method = event["httpMethod"].upper()
                self.user_name = claims["email"]
                self.org_id = claims["org_id"]
                self.org_friendly_id = claims["org_friendly_id"]
                self.org_name = claims["org_name"]
                self.recipient_type = claims.get("org_type") or claims["scope"]
                self.role = claims["role"]

                if "name" in claims:
                    self.name = claims["name"]
                elif "name" not in claims:
                    self.name = claims["email"]

            # calls helper function to log the first event upon creation of
            # the log object
            self.valid_auth_token = True
            self.log_first_api_invocation()

        except Exception:  # pylint: disable=broad-exception-caught
            # NOTE: cannot raise custom exceptions due to error in
            #       "possible circular import"
            self.valid_auth_token = False

    # returns the status of auth token
    def is_auth_token_valid(self):
        return self.valid_auth_token

    # returns dict of values found in auth token
    def get_auth_token(self):
        auth_token = {}
        if self.valid_auth_token:
            auth_token["email"] = self.user_name
            auth_token["org_id"] = self.org_id
            auth_token["org_friendly_id"] = self.org_friendly_id
            auth_token["org_name"] = self.org_name
            auth_token["recipient_type"] = self.recipient_type
            auth_token["name"] = self.name
            auth_token["role"] = self.role
        return auth_token

    # logging the event upon first invocation of api
    def log_first_api_invocation(self):
        """Logs first api invocation upon creation of log object"""
        self.message = "API Invocation"
        logger.info(json.dumps(vars(self), default=str))

    def log_info(self, message, module_info=None):
        """Logs custom info: log_level, message, status_code, module_info

        Arguments:
            message -- string for a short success message

            module_info -- string for year, quarter, module ID
            (default to None)

        Invocation Example:

        log.log_info(message="Success post request",
        module_info="module_id: 222" )
        """
        self.log_level = logging.INFO
        self.message = message
        self.module_info = module_info

        new_self = copy.deepcopy(self)
        del new_self.result

        # logs attributes of object as a dict
        logger.info(json.dumps(vars(new_self), default=str))

    def log_debug(self, message, module_info=None):
        """
        Logs custom debug: log_level, message, status_code, module_info

        Arguments:
            message -- string for a short success message

            module_info -- string for year, quarter, module ID
            (default to None)

        Invocation Example:

        log.log_debug(message="Debugging this line of code",
        module_info="module_id: 222" )
        """
        self.log_level = logging.DEBUG
        self.message = message
        self.module_info = module_info

        new_self = copy.deepcopy(self)
        del new_self.result

        # logs attributes of object as a dict
        logger.debug(json.dumps(vars(new_self), default=str))

    # logging successful request for: APIImportModuleData, APIPostStation,
    # APISubmitModuleData, APIUpdateSubmissionStatus, takes in
    # message, status_code, and optional: module_info
    # note: module_info only necessary for APIImportModuleData
    def log_successful_request(self, message, status_code, module_info=None):
        """
        Logs successful request: log_level, message, status_code, module_info

        Arguments:
            message -- string for a short success message

            status_code -- POST request = 200; PUT request = 201

            module_info -- string for year, quarter, module ID
            (default to None)

        Invocation Example:

        log.log_successful_request(message="Success post request",
        status_code=201, module_info="module_id: 222" )
        """
        self.log_level = 6
        self.message = message
        self.status_code = status_code
        self.module_info = module_info

        # logs attributes of object as a dict
        logger.info(json.dumps(vars(self), default=str))

    def log_custom_exception(self, message, status_code, log_level):
        """
        Logs the custom exception that was raised: log_level, message,
        status_code, module_info

        Arguments:
            message -- error message

            status_code -- error-code

            log_level -- Level 4: user error, Level 3: system error

        Invocation Example:

        log.log_custom_exception(message="Invalid auth token",
        status_code=401, log_level=4")
        """
        self.log_level = log_level
        self.message = message
        self.status_code = status_code
        self.result = "FAILURE"

        # logs attributes of object as a dict
        if log_level == 4:
            logger.warning(json.dumps(vars(self), default=str))
        elif log_level == 3:
            logger.error(json.dumps(vars(self), default=str))

    # takes an err_obj and uses logger.warning to log the log_level,
    # message, and status_code, used for majority custom error logging
    # LEVEL 4 ERRORS: invocation error, malformed error,
    def log_level4_error(self, err_obj):
        """Logs: log_level = 4, message, status_code

        Arguments:
            err_obj -- error object that contains a message and status_code

        Invocation Example:
            log_obj.log_missing_or_malformed_header_error(err_obj= err)
        """
        self.log_level = 4
        self.message = err_obj.message
        self.status_code = err_obj.status_code
        self.result = "FAILURE"

        # logs attributes of object as a dict
        # logger.warning(vars(self))
        logger.warning(json.dumps(vars(self), default=str))

    # takes an err_obj and uses logger.warning to log the log_level,
    # message, operation, status_code. Used for database error logging
    # LEVEL 3 ERRORS: system level error, requires intervention
    def log_level3_error(self, err_obj, operation=None):
        """Logs: log_level = 3, message, status_code

        Arguments:
            err_obj -- error object that contains a message and status_code

            operation -- "CONNECT", "SELECT", "INSERT"

        Invocation Example:
            log_obj.log_database_aurora_query_error(err_obj= err)
        """
        self.log_level = 3
        self.message = err_obj.message
        self.status_code = err_obj.status_code
        self.result = "FAILURE"
        if operation:
            self.operation = operation

        # logs attributes of object as a dict
        logger.error(json.dumps(vars(self), default=str))

    # used only for unit tests
    def get_log_obj(self):
        return vars(self)

    def get_logger(self):
        return logging.getLogger("EV-ChART_Logging")
