"""Common type aliases for authentication system to reduce verbosity."""

from src.auth import ServiceTokenUser
from src.auth.models import AuthenticatedUser


# Type alias for authenticated users (either JWT or service token)
AuthenticatedUserType = AuthenticatedUser | ServiceTokenUser

__all__ = ["AuthenticatedUserType"]
