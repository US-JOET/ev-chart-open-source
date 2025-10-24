class EVChARTHelperPresignedURL(Exception):
    """Base exception class for presigned URL helper."""

class EVChARTHelperPresignedURLParametersError(EVChARTHelperPresignedURL):
    """EVChARTHelperPresignedURL exception class for parameter errors."""
    def __init__(self, *args):
        if not args:
            args = ("Missing or malformed parameters.",)

        super().__init__(*args)

class EVChARTHelperPresignedURLLambdaError(EVChARTHelperPresignedURL):
    """EVChARTHelperPresignedURL exception class for Lambda invocation errors."""
    def __init__(self, *args):
        if not args:
            args = ("Error invoking APIGetPresignedUrl.",)

        super().__init__(*args)

class EVChARTHelperPresignedURLS3Error(EVChARTHelperPresignedURL):
    """EVChARTHelperPresignedURL exception class for S3 errors."""
    def __init__(self, *args):
        if not args:
            args = ("Error uploading data to S3.",)

        super().__init__(*args)
