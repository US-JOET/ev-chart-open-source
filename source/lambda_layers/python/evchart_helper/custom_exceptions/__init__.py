"""
HOW TO CREATE AND INVOKE ERRORS
For all files that need to throw custom errors, import the exceptions file and
specific error.

Ex: from evchart_helper.CustomExceptions
 import EvChartMissingOrMalformedHeadersError

All errors have the following attributes: status_code, headers, message.

Specific errors have specific error codes and already have a default message
associated with each error, but a custom message can be added on, when creating
the error object. All errors except for EvChartAuthorizationTokenInvalidError
must pass in a log_obj in order to log the errors accordingly

Example of raising an error with a customized error message:

raise EvChartMissingOrMalformedHeadersError(
  log_obj=log, message="Invalid upload ID:{upload_id}"
)

When returning the needed object/payload back to the frontend, you can call
get_error_obj() to return the error object Ex: return error.get_error_obj()

HOW TO CREATE A CUSTOM EXCEPTION CLASS
Similar to the exceptions below, create your own custom class with the
prefix "EvChart".
Naming conventions:
Classes = CamelCaseDeclarations, functions = snake_case_declarations
In the Exceptions file, create a constructor and be sure to take in the
LogEvent obj, set the message and status_codes, then call the log error
function you just made in Logging class
In the constructor, ensure to call the appropriate logging standard:
log_level3_error (this will use logger.error) or
log_level4_error (this will use logger.warning)
Create a get_error_obj method, that will be used to return the payload
"""

import json
from evchart_helper.custom_logging import LogEvent


class ReturnErrObject():
    """Super class that holds the function to return the error object"""
    def get_error_obj(self):
        """Returns error object/payload: statusCode, headers, body"""

        self.headers= { "Access-Control-Allow-Origin": "*" }

        return {
            'statusCode' : self.status_code,
            'headers': self.headers,
            'body' : json.dumps(self.message)
        }


class EvChartMissingOrMalformedHeadersError(Exception, ReturnErrObject):
    """
    Error thrown in GET requests when request heders are invalid or missing from the event
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 400

        Arguments:
            log_obj -- LogEvent() object optional

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartMissingOrMalformedHeadersError(log_obj= log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 400
        self.message = "EvChartMissingOrMalformedHeadersError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)


class EvChartUpdateStatusError(Exception, ReturnErrObject):
    """
    Error thrown when account_status of a user cannot be updated
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 404

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartMissingOrMalformedBodyError(log_object= log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 400
        self.message = "EvChartRecordNotFoundError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)


class EvChartMissingOrMalformedBodyError(Exception, ReturnErrObject):
    """
    Error thrown in POST or PUT requests when the request body is invalid or missing from the event
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 406

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartMissingOrMalformedBodyError(log_object= log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 406
        self.message = "EvChartMissingOrMalformedBodyError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)


class EvChartMissingOrMalformedPathParameterError(Exception, ReturnErrObject):
    """
    Error thrown when the path parameters is invalid or missing from the event
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 400

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartMissingOrMalformedBodyError(log_object= log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 400
        self.message = "EvChartMissingOrMalformedPathParameterError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)

class EvChartUnableToDeleteItemError(Exception, ReturnErrObject):
    """
    Error thrown in POST or PUT requests when the request body is invalid or missing from the event
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 406

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartUnableToDeleteItemError(log_object= log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 409
        self.message = "EvChartUnableToDeleteItemError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)


class EvChartInvalidEmailError(Exception, ReturnErrObject):
    """
    Error thrown when validating emails that do not conform to established email address standard
    (e.g. the regular expression [^@]+@[^@]+\.[^@]+).
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 406

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartMissingOrMalformedBodyError(log_object= log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 406
        self.message = "EvChartInvalidEmailError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)


class EvChartAuthorizationTokenInvalidError(Exception, ReturnErrObject):
    """
    Error thrown when authorization token is invalid
    Note: When the error is thrown or raised, it will also be logged
    """
    #constructor that sets the error message of the object when first made, has a default constructor if no message is passed
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 401

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartAuthorizationTokenInvalidError(message="custom error message")

        Note: This does not take a log object because log object attributes come from auth token. Therefore you cannot pull log attributes if token is invalid
        """
        self.log_level = 4
        self.status_code = 401
        self.message = "EvChartAuthorizationTokenInvalidError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)


class EvChartUserNotAuthorizedError(Exception, ReturnErrObject):
    """
    Error thrown when the current user is not allowed to perform api action: viewing module uploads not uploaded by your organization, uploading for an unauthorized DR
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 403

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartUserNotAuthorizedError(log_obj= log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 403
        self.message = "EvChartUserNotAuthorizedError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)

class EvChartInvalidAPIKey(Exception, ReturnErrObject):
    """
    Error thrown when ther is no api key in the event, the api key is not associated with an org or api key is not active
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 403

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartUserNotAuthorizedError(log_obj= log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 403
        self.message = "EvChartUserNotAuthorizedError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)

class EvChartPayloadError(Exception, ReturnErrObject):
    #constructor that sets the error message of the object when first made, has a default constructor if no message is passed
    """
    Error thrown when payload received is malformed
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 413

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartPayloadError(log_obj= log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 413
        self.message = "EvChartPayloadError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)


class EvChartJsonOutputError(Exception, ReturnErrObject):
    #constructor that sets the error message of the object when first made, has a default constructor if no message is passed
    """
    Error thrown when there is an issue with formatting output for the frontend
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartJsonOutputError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartJsonOutputError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)


class EvChartDatabaseAuroraQueryError(Exception, ReturnErrObject):
    #constructor that sets the error message of the object when first made, has a default constructor if no message is passed
    """
    Error thrown during the execution of queries againast the aurora database. This error is purely a database error, not a logic error
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, operation=None, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartDatabaseAuroraQueryError(message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartDatabaseAuroraQueryError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)


#Thrown during the execution of queries against the dynamo database. This error is purely a database error, when the database is queried. This should not be thrown when evaluating for logic.
class EvChartDatabaseDynamoQueryError(Exception, ReturnErrObject):
    """
    Error thrown during the execution of queries againast the dynamo database. This error is purely a database error, not a logic error
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, operation=None, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartDatabaseDynamoQueryError(message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartDatabaseDynamoQueryError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)


#Thrown when there is a duplicate primary key entry error returned from Aurora during insert functions
class EvChartDatabaseAuroraDuplicateItemError(Exception, ReturnErrObject):
    """
    Thrown when there is a duplicate primary key entry error returned from Aurora during insert functions
    """
    def __init__(self, operation=None, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 409

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartDatabaseAuroraDuplicateItemError(message="custom error message")
        """
        self.log_level = 3
        self.status_code = 409
        self.message = "EvChartDatabaseAuroraDuplicateItemError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)


class EvChartFeatureStoreConnectionError(Exception, ReturnErrObject):
    """
    Error thrown during the request of Parameter Store. This error is an thrown by aws when trying to connect
    to the service where we store our Features
    """
    def __init__(self, operation=None, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartFeatureStoreConnectionError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartFeatureStoreConnectionError raised, unable to connect to parameter store. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartFeatureToggleNotFoundError(Exception, ReturnErrObject):
    """
    Error thrown when feature toggle can not be found.
    """
    def __init__(self, operation=None, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartFeatureStoreConnectionError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartFeatureToggleNotFoundError raised, unable to find feature toggle. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartDynamoConnectionError(Exception, ReturnErrObject):
    """
    Error thrown during the request of dynamoDB
    """
    def __init__(self, operation=None, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartDynamoConnectionError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartDynamoConnectionError raised, unable to connect to dynamodb. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartLambdaConnectionError(Exception, ReturnErrObject):
    """
    Error thrown during the request of lambda
    """
    def __init__(self, operation=None, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartLambdaConnectionError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartLambdaConnectionError raised, unable to connect to lambda function. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)



class EvChartInvalidDataError(Exception, ReturnErrObject):
    """
    Error thrown when data is invalid or incorrect
    (for checking enum values, etc)
    Note: When the error is thrown or raised, it will also be logged
    """
    # constructor that sets the error message of the object when first made,
    # has a default constructor if no message is passed
    def __init__(self, log_obj=None, message=None):
        """
        When the error is thrown or raised, it will also be logged.
        Sets status_code to 422

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartInvalidDataError(message="custom error message")

        Note: This does not take a log object because log object attributes
        come from auth token. Therefore you cannot pull log attributes if token
        is invalid
        """
        self.log_level = 4
        self.status_code = 422
        self.message = "EvChartInvalidDataError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)


class EvChartDatabaseHandlerConnectionError(Exception, ReturnErrObject):
    """
    Error thrown trying to connect to Aurora database.
    """
    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartDatabaseHandlerConnectionError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartDatabaseHandlerConnectionError raised, unable to connect to RDS. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)


class EvChartInvalidCSVError(Exception, ReturnErrObject):
    #constructor that sets the error message of the object when first made,
    # has a default constructor if no message is passed
    """
    Error thrown when there is an issue with formatting output for the
          frontend from a CSV
    Note: When the error is thrown or raised, it will also be logged
    """
    def __init__(self, log_obj=None, message=None):
        """
        When the error is thrown or raised, it will also be logged.
        Sets status_code to 406

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartInvalidCSVError(log_obj=log, message="custom error message")
        """
        self.log_level = 4
        self.status_code = 406
        self.message = "EvChartInvalidCSVError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)


class EvChartDatabaseDynamoDuplicateItemError(Exception, ReturnErrObject):
    """
    Thrown when there is a duplicate primary key entry error returned from
    Aurora during insert functions
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 409

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartDatabaseDynamoDuplicateItemError(message="custom error message")
        """
        self.log_level = 4
        self.status_code = 409
        self.message = "EvChartDatabaseDynamoDuplicateItemError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)

class EvChartEmailError(Exception, ReturnErrObject):
    """
    Thrown when there is an issue in the email handler or email sender
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartEmailError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartEmailError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartModuleValidationError(Exception, ReturnErrObject):
    """
    Thrown when there is an issue in the email handler or email sender
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartModuleValidationError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartModuleValidationError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartFileNotFoundError(Exception, ReturnErrObject):
    """
    Thrown when a file is not found such as in load_module_definitions
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartModuleValidationError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartFileNotFoundError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)


class EvChartAsynchronousS3Error(Exception, ReturnErrObject):
    """
    Thrown when there is an issue in the email handler or email sender
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartModuleValidationError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartAsynchronousS3Error raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)
class EvChartS3GetObjectError(Exception, ReturnErrObject):
    """
    Thrown when there is an issue pulling an S3 object
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartModuleValidationError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartS3GetObjectError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartSNSError(Exception, ReturnErrObject):
    """
    Thrown when there is an issue sending an sns message
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartModuleValidationError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartSNSError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartSQSError(Exception, ReturnErrObject):
    """
    Thrown when there is an error related to SQS
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartModuleValidationError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartSQSError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartS3CorruptedObjectError(Exception, ReturnErrObject):
    """
    Thrown when there is an issue pulling an S3 object checksum does not match expected checksum
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartModuleValidationError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartS3CorruptedObjectError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartModuleStatusError(Exception, ReturnErrObject):
    """
    Error thrown when module is unable to be viewed due to current status
    (for checking enum values, etc)
    Note: When the error is thrown or raised, it will also be logged
    """
    # constructor that sets the error message of the object when first made,
    # has a default constructor if no message is passed
    def __init__(self, log_obj=None, message=None):
        """
        When the error is thrown or raised, it will also be logged.
        Sets status_code to 422

        Arguments:
            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartModuleStatusError(message="custom error message")

        Note: This does not take a log object because log object attributes
        come from auth token. Therefore you cannot pull log attributes if token
        is invalid
        """
        self.log_level = 4
        self.status_code = 422
        self.message = "EvChartModuleStatusError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(self)

class EvChartAPIKeyGenerationError(Exception, ReturnErrObject):
    """
    Thrown when there is an issue sending an sns message
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartAPIKeyGenerationError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartAPIKeyGenerationError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)

class EvChartAPIS2SError(Exception, ReturnErrObject):
    """
    Thrown when there is an issue during an S2S API call
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartAPIS2SError(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartAPIS2SError raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)


class EvChartDatabaseIntegrityError(Exception, ReturnErrObject):
    """
        Thrown when drift is detected between running Aurora instance and
        database central config
    """

    def __init__(self, log_obj=None, message=None):
        """
            When the error is thrown or raised, it will also be logged.
            Sets status_code to 500.
            Note that process ran successfully, but errors logged

            Arguments:
                log_obj -- LogEvent() object

                message -- string custom error message (defaulted to None)

            Invocation Example:
                EvChartDatabaseIntegrityError(
                    log_obj=log, message="custom error message"
                )
        """
        self.log_level = 4
        self.status_code = 500
        self.message = message or "EvChartDatabaseIntegrityError raised. "

        if isinstance(log_obj, LogEvent):
            log_obj.log_level4_error(err_obj=self)


class EvChartUnknownException(Exception, ReturnErrObject):
    """
    Thrown when there is an exception that is not caught by other exception classes.
    Similar to a default/ catch all exception
    """

    def __init__(self, log_obj=None, message=None):
        """When the error is thrown or raised, it will also be logged. Sets status_code to 500

        Arguments:
            log_obj -- LogEvent() object

            message -- string custom error message (defaulted to None)

        Invocation Example:
            EvChartUnknownException(log_obj= log, message="custom error message")
        """
        self.log_level = 3
        self.status_code = 500
        self.message = "EvChartUnknownException raised. "
        if message is not None:
            self.message += f"{message}"

        #checks if log object is present, and if it is, then log the object
        if isinstance(log_obj, LogEvent):
            log_obj.log_level3_error(err_obj=self)
