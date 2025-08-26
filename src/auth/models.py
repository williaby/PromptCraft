"""Authentication models for PromptCraft."""

import re
import uuid
from datetime import UTC, datetime
from enum import Enum

# Create aliases for backward compatibility
EventSeverity = None  # Will be set after class definition
EventType = None  # Will be set after class definition
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from .constants import ROLE_ADMIN, ROLE_USER


class UserRole(str, Enum):
    """User roles for role-based access control."""

    ADMIN = ROLE_ADMIN
    USER = ROLE_USER
    VIEWER = "viewer"  # Not centralized yet, keeping as is


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


# Service Token Pydantic Models


class ServiceTokenCreate(BaseModel):
    """Service token creation model."""

    token_name: str = Field(..., min_length=1, max_length=255, description="Human-readable token name")
    is_active: bool = Field(default=True, description="Whether token is active")
    expires_at: datetime | None = Field(default=None, description="Token expiration datetime")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional token metadata")

    @validator("token_name")
    def validate_token_name(cls, v: str) -> str:  # noqa: N805
        """Validate and clean token name."""
        return v.strip()


class ServiceTokenUpdate(BaseModel):
    """Service token update model."""

    token_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Human-readable token name",
    )
    is_active: bool | None = Field(default=None, description="Whether token is active")
    expires_at: datetime | None = Field(default=None, description="Token expiration datetime")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional token metadata")

    @validator("token_name")
    def validate_token_name(cls, v: str | None) -> str | None:  # noqa: N805
        """Validate and clean token name."""
        if v is not None:
            return v.strip()
        return v


class ServiceTokenResponse(BaseModel):
    """Service token response model."""

    id: uuid.UUID = Field(..., description="Token unique identifier")
    token_name: str = Field(..., description="Human-readable token name")
    created_at: datetime = Field(..., description="Token creation timestamp")
    last_used: datetime | None = Field(default=None, description="Last usage timestamp")
    usage_count: int = Field(..., description="Total usage count")
    expires_at: datetime | None = Field(default=None, description="Token expiration timestamp")
    is_active: bool = Field(..., description="Whether token is active")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional token metadata")
    is_expired: bool = Field(..., description="Whether token is expired")
    is_valid: bool = Field(..., description="Whether token is valid (active and not expired)")

    @classmethod
    def from_orm_model(cls, token: Any) -> "ServiceTokenResponse":
        """Create response from SQLAlchemy model."""
        return cls(
            id=token.id,
            token_name=token.token_name,
            created_at=token.created_at,
            last_used=token.last_used,
            usage_count=token.usage_count,
            expires_at=token.expires_at,
            is_active=token.is_active,
            metadata=token.token_metadata,  # Note: SQLAlchemy model uses token_metadata
            is_expired=token.is_expired,
            is_valid=getattr(token, "is_valid", token.is_active and not token.is_expired),
        )


class ServiceTokenListResponse(BaseModel):
    """Service token list response model."""

    tokens: list[ServiceTokenResponse] = Field(..., description="List of tokens")
    total: int = Field(..., ge=0, description="Total number of tokens")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")


class TokenValidationRequest(BaseModel):
    """Token validation request model."""

    token: str = Field(..., min_length=1, description="Token to validate")

    @validator("token")
    def validate_token(cls, v: str) -> str:  # noqa: N805
        """Validate and clean token."""
        return v.strip()


class TokenValidationResponse(BaseModel):
    """Token validation response model."""

    valid: bool = Field(..., description="Whether token is valid")
    token_id: uuid.UUID | None = Field(default=None, description="Token ID if valid")
    token_name: str | None = Field(default=None, description="Token name if valid")
    expires_at: datetime | None = Field(default=None, description="Token expiration if valid")
    metadata: dict[str, Any] | None = Field(default=None, description="Token metadata if valid")
    error: str | None = Field(default=None, description="Error message if invalid")


# Security Event Models


class SecurityEventType(str, Enum):
    """Security event types for comprehensive monitoring coverage."""

    # Authentication events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    SESSION_EXPIRED = "session_expired"

    # Service token events
    SERVICE_TOKEN_AUTH = "service_token_auth"
    SERVICE_TOKEN_CREATED = "service_token_created"
    SERVICE_TOKEN_REVOKED = "service_token_revoked"
    SERVICE_TOKEN_EXPIRED = "service_token_expired"

    # Account security events
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKOUT = "account_lockout"
    ACCOUNT_UNLOCK = "account_unlock"

    # Suspicious activity events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # System events
    SYSTEM_ERROR = "system_error"
    SECURITY_ALERT = "security_alert"
    CONFIGURATION_CHANGED = "configuration_changed"
    AUDIT_LOG_GENERATED = "audit_log_generated"
    SYSTEM_MAINTENANCE = "system_maintenance"


class SecurityEventSeverity(str, Enum):
    """Security event severity levels for proper alerting and response."""

    INFO = "info"  # Normal operations, informational logging
    WARNING = "warning"  # Potential security concerns, failed attempts
    CRITICAL = "critical"  # Active threats, system errors, brute force


class SecurityEventBase(BaseModel):
    """Base security event model with common fields."""

    event_type: SecurityEventType = Field(..., description="Type of security event")
    severity: SecurityEventSeverity = Field(..., description="Event severity level")
    user_id: str | None = Field(None, max_length=255, description="User identifier (email or token name)")
    ip_address: str | None = Field(None, max_length=45, description="Client IP address (IPv4 or IPv6)")
    user_agent: str | None = Field(None, max_length=500, description="User agent string")
    session_id: str | None = Field(None, max_length=255, description="Session identifier")
    details: dict[str, Any] | None = Field(default_factory=dict, description="Additional event details (JSON)")
    risk_score: int = Field(0, ge=0, le=100, description="Risk score from 0-100")

    @validator("ip_address")
    def validate_ip_address(cls, v):
        """Validate IP address format."""
        if v is None:
            return v

        # Basic IPv4 pattern validation
        ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        # Basic IPv6 pattern validation (simplified)
        ipv6_pattern = r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|^::1$|^::$"

        if re.match(ipv4_pattern, v) or re.match(ipv6_pattern, v):
            return v

        # Allow localhost and private networks for development
        if v in ["localhost", "127.0.0.1", "::1"] or v.startswith("192.168.") or v.startswith("10."):
            return v

        return v  # Return as-is for complex IPv6 addresses or unknown formats

    @validator("user_agent")
    def validate_user_agent(cls, v):
        """Sanitize user agent string to prevent injection attacks."""
        if v is None:
            return v

        # Remove potentially dangerous characters but keep useful info
        sanitized = re.sub(r'[<>"\']', "", v)
        return sanitized[:500]  # Enforce max length

    @validator("details")
    def validate_details(cls, v):
        """Validate and sanitize details JSON."""
        if v is None:
            return {}

        # Ensure all keys are strings and values are JSON-serializable
        sanitized = {}
        for key, value in v.items():
            if isinstance(key, str) and len(key) <= 100:  # Reasonable key length limit
                if isinstance(value, (str, int, float, bool, type(None))):
                    sanitized[key] = value
                else:
                    # Convert complex types to string representation
                    sanitized[key] = str(value)[:1000]  # Limit value length

        return sanitized


class SecurityEventCreate(SecurityEventBase):
    """Model for creating new security events."""

    timestamp: datetime | None = Field(
        default_factory=lambda: datetime.now(UTC), description="Event timestamp",
    )


class SecurityEvent(SecurityEventBase):
    """Complete security event model with database fields."""

    id: UUID | None = Field(default_factory=uuid4, description="Unique event identifier")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Event timestamp")

    class Config:
        """Pydantic configuration."""

        orm_mode = True  # Enable ORM integration
        validate_assignment = True  # Validate on assignment
        use_enum_values = True  # Use enum values in serialization


class SecurityEventResponse(BaseModel):
    """Response model for security events (API responses)."""

    id: UUID = Field(..., description="Event identifier")
    event_type: str = Field(..., description="Event type")
    severity: str = Field(..., description="Event severity")
    user_id: str | None = Field(None, description="User identifier")
    ip_address: str | None = Field(None, description="IP address")
    timestamp: datetime = Field(..., description="Event timestamp")
    risk_score: int = Field(..., description="Risk score 0-100")
    details: dict[str, Any] = Field(default_factory=dict, description="Event details")

    class Config:
        """Pydantic configuration."""

        orm_mode = True


# Create aliases for backward compatibility
EventSeverity = SecurityEventSeverity
EventType = SecurityEventType
