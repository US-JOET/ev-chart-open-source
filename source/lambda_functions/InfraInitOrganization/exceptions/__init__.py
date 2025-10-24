class InfraInitOrganizationBaseException(Exception):
    """Base exception class for InfraInitOrganization."""

class InfraInitOrganizationGenericError(InfraInitOrganizationBaseException):
    """InfraInitOrganization exception class for generic errors (wrapper)."""
    def __init__(self, *args):
        if not args:
            args = ("InfraInitOrganization: Error encountered.",)

        super().__init__(*args)
