"""SQLAlchemy models for PromptCraft authentication database.

This module defines database models for enhanced Cloudflare Access authentication:
- UserSession: User session tracking and metadata storage
- AuthenticationEvent: Authentication event logging and audit trail
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import TIMESTAMP, Boolean, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class UserSession(Base):
    """User session tracking model for authenticated users.

    Tracks user sessions, preferences, and metadata for enhanced
    authentication experience and user behavior analysis.
    """

    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User email from JWT token",
    )

    cloudflare_sub: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Cloudflare subject identifier from JWT",
    )

    first_seen: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        comment="First authentication timestamp",
    )

    last_seen: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Most recent authentication timestamp",
    )

    session_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="Total number of authentication sessions",
    )

    preferences: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="'{}'::jsonb",
        comment="User preferences and settings",
    )

    user_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default="'{}'::jsonb",
        comment="Additional user metadata and tracking data",
    )

    def __repr__(self) -> str:
        """String representation of UserSession."""
        return f"<UserSession(id={self.id}, email='{self.email}', sessions={self.session_count})>"


class AuthenticationEvent(Base):
    """Authentication event logging model for audit trail.

    Logs all authentication attempts and events for security
    monitoring, audit compliance, and performance analysis.
    """

    __tablename__ = "authentication_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    user_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="User email from authentication attempt",
    )

    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of authentication event (login, refresh, validation)",
    )

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
        String(100),
        nullable=True,
        index=True,
        comment="Cloudflare Ray ID for request tracing",
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
        comment="Whether authentication was successful",
    )

    error_details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Error details for failed authentication attempts",
    )

    performance_metrics: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Performance timing metrics for the authentication request",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=func.now(),
        server_default=func.now(),
        index=True,
        comment="Event creation timestamp",
    )

    def __repr__(self) -> str:
        """String representation of AuthenticationEvent."""
        success_str = "SUCCESS" if self.success else "FAILED"
        return (
            f"<AuthenticationEvent(id={self.id}, email='{self.user_email}', type='{self.event_type}', {success_str})>"
        )


# Export models for easy importing
__all__ = ["AuthenticationEvent", "Base", "UserSession"]
