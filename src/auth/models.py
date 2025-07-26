"""Authentication models for PromptCraft."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    """User roles for role-based access control."""

    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class AuthenticatedUser(BaseModel):
    """Authenticated user model from JWT token."""

    email: str = Field(..., description="User email from JWT claims")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    jwt_claims: dict[str, Any] = Field(..., description="All JWT claims")
    
    @property
    def user_id(self) -> str | None:
        """Get user ID from JWT 'sub' claim."""
        return self.jwt_claims.get("sub")

    class Config:
        """Pydantic configuration."""

        # Allow arbitrary types for JWT claims
        arbitrary_types_allowed = True


class JWTValidationError(Exception):
    """Exception raised during JWT validation."""

    def __init__(self, message: str, error_type: str = "validation_error") -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class JWKSError(Exception):
    """Exception raised during JWKS operations."""

    def __init__(self, message: str, error_type: str = "jwks_error") -> None:
        super().__init__(message)
        self.error_type = error_type
        self.message = message


class AuthenticationError(Exception):
    """Exception raised during authentication."""

    def __init__(self, message: str, status_code: int = 401) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
