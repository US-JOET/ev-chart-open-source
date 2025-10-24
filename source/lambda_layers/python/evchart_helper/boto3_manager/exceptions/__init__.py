class Boto3ManagerBaseException(Exception):
    """Base exception class for Boto3Manager."""

class Boto3ManagerClientTypeError(Boto3ManagerBaseException):
    """Boto3Manager exception class for unsupported boto3 client types."""
    def __init__(self, *args):
        if not args:
            args = ("Unsupported value entered for boto3 client type.",)

        super().__init__(*args)
