"""
evchart_helper.user_emums

Helper enums for users.
"""
from enum import Enum

class Roles(Enum):
    """
        Maps the backend definition of a role for a user to a user-friendly string to be referenced
        where appropriate.
    """
    admin = "Administrator"
    viewer = "Viewer"
