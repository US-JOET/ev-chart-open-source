class APIGetPresignedUrlBaseException(Exception):
    """Base exception class for APIGetPresignedUrl."""

class APIGetPresignedUrlGenerationError(APIGetPresignedUrlBaseException):
    """APIGetPresignedUrl exception class for any errors generating the presigned URL."""
    def __init__(self, *args):
        if not args:
            args = ("Unable to generate presigned URL.",)

        super().__init__(*args)

        self.status_code = 500

class APIGetPresignedUrlInvalidQuery(APIGetPresignedUrlBaseException):
    """APIGetPresignedUrl exception class for invalid query strings."""
    def __init__(self, *args):
        if not args:
            args = ("Invalid request query.",)

        super().__init__(*args)

        self.status_code = 400
