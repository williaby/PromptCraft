"""SQLAlchemy models for PromptCraft authentication and service token management.

This module defines database models for:
- Service token management and tracking
- User session management
- Authentication event logging
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import TIMESTAMP, Boolean, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .connection import Base


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
        comment="Last usage timestamp",
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="Token expiration timestamp (NULL = no expiration)",
    )

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total number of times token has been used",
    )

    # Status and configuration
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether token is active and can be used",
    )

    # Additional metadata
    token_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional token metadata (permissions, scope, etc.)",
    )

    def __repr__(self) -> str:
        """String representation of service token."""
        status = "active" if self.is_active else "inactive"
        return f"<ServiceToken(name='{self.token_name}', status='{status}', uses={self.usage_count})>"

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at.replace(tzinfo=None)

    @property
    def is_valid(self) -> bool:
        """Check if token is valid (active and not expired)."""
        return self.is_active and not self.is_expired

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary (excluding sensitive data)."""
        return {
            "id": str(self.id),
            "token_name": self.token_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "usage_count": self.usage_count,
            "is_active": self.is_active,
            "is_expired": self.is_expired,
            "metadata": self.token_metadata,
        }


class UserSession(Base):
    """User session model for tracking authenticated user sessions."""

    __tablename__ = "user_sessions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique session identifier",
    )

    # User identification
    email: Mapped[str] = mapped_column(String(255), nullable=False, comment="User email from Cloudflare Access")

    cloudflare_sub: Mapped[str] = mapped_column(String(255), nullable=False, comment="Cloudflare subject identifier")

    # Session timestamps
    first_seen: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="First session timestamp",
    )

    last_seen: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Last activity timestamp",
    )

    # Session tracking
    session_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Number of sessions for this user",
    )

    # User preferences and metadata
    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="User preferences and settings",
    )

    user_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Additional user metadata",
    )

    def __repr__(self) -> str:
        """String representation of user session."""
        return f"<UserSession(email='{self.email}', sessions={self.session_count})>"


class AuthenticationEvent(Base):
    """Authentication event model for audit logging."""

    __tablename__ = "authentication_events"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique event identifier",
    )

    # User identification
    user_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="User email (if user authentication)",
    )

    service_token_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Service token name (if service token authentication)",
    )

    # Event details
    event_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="Type of authentication event")

    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether authentication was successful",
    )

    # Request context
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="Client IP address (IPv4 or IPv6)",
    )

    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="Client user agent string")

    endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="API endpoint accessed")

    # Cloudflare context
    cloudflare_ray_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Cloudflare Ray ID for request tracing",
    )

    # Error details
    error_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Error details for failed authentications",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Event timestamp",
    )

    def __repr__(self) -> str:
        """String representation of authentication event."""
        status = "success" if self.success else "failure"
        return f"<AuthenticationEvent(type='{self.event_type}', status='{status}')>"
