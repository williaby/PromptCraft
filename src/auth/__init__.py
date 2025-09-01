"""Authentication module for PromptCraft.

This module provides JWT-based authentication using Cloudflare Access tokens.
It includes:
- JWT token validation against Cloudflare JWKS endpoint
- Email-based user identification and role mapping
- FastAPI middleware for authentication
- Rate limiting to prevent DOS attacks
- Secure caching of JWKS with TTL support
"""

from .exceptions import AuthExceptionHandler
from .service_token_manager import ServiceTokenManager  # Preserved component

# Recreate ServiceTokenUser class to avoid importing complex middleware
class ServiceTokenUser:
    """Represents an authenticated service token user."""

    def __init__(self, token_id: str, token_name: str, metadata: dict, usage_count: int = 0) -> None:
        """Initialize service token user.

        Args:
            token_id: Unique token identifier
            token_name: Human-readable token name
            metadata: Token metadata including permissions
            usage_count: Current usage count
        """
        self.token_id = token_id
        self.token_name = token_name
        self.metadata = metadata or {}
        self.usage_count = usage_count

    def has_permission(self, permission: str) -> bool:
        """Check if the service token has a specific permission.

        Args:
            permission: Permission to check

        Returns:
            True if token has the permission
        """
        return permission in self.metadata.get("permissions", [])

    @property
    def permissions(self) -> list[str]:
        """Get list of permissions for this token."""
        return self.metadata.get("permissions", [])

from .models import (
    AuthenticatedUser,
    AuthenticationError,
    JWKSError,
    JWTValidationError,
    SecurityEvent,
    SecurityEventCreate,
    SecurityEventResponse,
    SecurityEventSeverity,
    SecurityEventType,
    UserRole,
)

# Compatibility functions that redirect to auth_simple for simple auth scenarios
# but preserve the complex auth functionality for API endpoints that need it

def require_authentication(request=None):
    """Compatibility wrapper for authentication requirement.
    
    This preserves the API signature while the actual implementation
    may vary based on the authentication system in use.
    """
    # For API endpoints that use service tokens, we keep the complex logic
    # For simple web auth, this would redirect to auth_simple
    from .middleware import ServiceTokenUser
    # This is a simplified version - the actual middleware handles the complex logic
    if hasattr(request, 'user'):
        return request.user
    return None

def require_role(request, role):
    """Compatibility wrapper for role requirement."""
    # Simplified role checking
    user = require_authentication(request)
    if user and hasattr(user, 'role') and str(user.role) == role:
        return user
    return None

def get_current_user(request):
    """Compatibility wrapper for getting current user."""
    return require_authentication(request)

def setup_authentication(app):
    """Compatibility wrapper for authentication setup."""
    # This would be replaced by auth_simple setup in main.py
    pass

# Mock middleware class for compatibility
class AuthenticationMiddleware:
    """Compatibility class - actual middleware is in auth_simple."""
    pass

__all__ = [
    "AuthExceptionHandler",
    "AuthenticatedUser",
    "AuthenticationError",
    "AuthenticationMiddleware",
    "ServiceTokenManager",
    "ServiceTokenUser",
    "JWKSError",
    "JWTValidationError",
    "SecurityEvent",
    "SecurityEventCreate",
    "SecurityEventResponse",
    "SecurityEventSeverity",
    "SecurityEventType",
    "UserRole",
    "get_current_user",
    "require_authentication",
    "require_role",
    "setup_authentication",
]
