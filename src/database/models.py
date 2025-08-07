"""SQLAlchemy models for PromptCraft authentication and service token management.

This module defines database models for:
- Service token management and tracking (AUTH-2)
- User session management (AUTH-1)
- Authentication event logging (AUTH-1)
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import TIMESTAMP, Boolean, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class ServiceToken(Base):
    """Service token model for API authentication and tracking."""

    __tablename__ = "service_tokens"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique service token identifier",
    )

    # Token identification
    token_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Human-readable token name (e.g., 'ci-cd-pipeline')",
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="SHA-256 hash of the token for secure storage",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Token creation timestamp",
    )

    last_used: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Last time this token was used for authentication",
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Token expiration time (NULL for no expiration)",
    )

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of times this token has been used",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the token is active and can be used",
    )

    # Metadata
    token_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata about the token (permissions, environment, etc.)",
    )

    def __repr__(self) -> str:
        """Return string representation of the service token."""
        status = "active" if self.is_active else "inactive"
        return f"<ServiceToken(name='{self.token_name}', {status}, uses={self.usage_count})>"

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        if self.expires_at is None:
            return False
        # Ensure both datetimes are timezone-aware and in UTC
        now_utc = datetime.now(timezone.utc)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            # Assume naive expires_at is UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return now_utc > expires_at

    @property
    def is_valid(self) -> bool:
        """Check if the token is valid (active and not expired)."""
        return self.is_active and not self.is_expired


class UserSession(Base):
    """User session tracking model for authenticated users.

    Tracks user sessions, preferences, and metadata for enhanced
    authentication experience and user behavior analysis.
    """

    __tablename__ = "user_sessions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique session identifier",
    )

    # User identification
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User email address from Cloudflare Access JWT",
    )

    cloudflare_sub: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Cloudflare Access subject identifier",
    )

    # Session tracking
    first_seen: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="First time this user was seen",
    )

    last_seen: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last time this user was seen",
    )

    session_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of sessions for this user",
    )

    # User data
    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="User preferences and settings",
    )

    user_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Additional user metadata and context",
    )

    def __repr__(self) -> str:
        """Return string representation of the user session."""
        return f"<UserSession(id={self.id}, email='{self.email}', sessions={self.session_count})>"


class AuthenticationEvent(Base):
    """Authentication event model for audit logging and analytics.

    Tracks all authentication attempts, successes, and failures
    for security monitoring and performance analysis.
    """

    __tablename__ = "authentication_events"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique event identifier",
    )

    # Event identification
    user_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User email (from JWT or 'unknown' for failures)",
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of authentication event (login, token_refresh, etc.)",
    )

    # Request context
    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
        comment="Client IP address",
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Client user agent string",
    )

    cloudflare_ray_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Cloudflare Ray ID for request tracing",
    )

    # Event outcome
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="Whether the authentication was successful",
    )

    # Event details
    error_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Error details for failed authentication attempts",
    )

    performance_metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Performance metrics (timing, etc.) for the authentication",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Event timestamp",
    )

    def __repr__(self) -> str:
        """Return string representation of the authentication event."""
        status = "SUCCESS" if self.success else "FAILED"
        return f"<AuthenticationEvent(id={self.id}, user='{self.user_email}', type='{self.event_type}', {status})>"


# Export all models
__all__ = [
    "AuthenticationEvent",
    "Base",
    "ServiceToken",
    "UserSession",
]
