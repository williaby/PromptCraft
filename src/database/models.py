"""SQLAlchemy models for PromptCraft authentication and service token management.

This module defines database models for:
- Service token management and tracking (AUTH-2)
- User session management (AUTH-1)
- Authentication event logging (AUTH-1)
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.utils.datetime_compat import UTC


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


# Association tables for many-to-many relationships

user_roles_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("user_sessions.id"), primary_key=True),
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
)

role_permissions_table = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id"), primary_key=True),
)


class Role(Base):
    """Role model for role-based access control (RBAC)."""

    __tablename__ = "roles"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique role identifier",
    )

    # Role identification
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Role name (e.g., 'admin', 'user', 'viewer')",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Role description",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the role is active",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Role creation timestamp",
    )

    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Role last updated timestamp",
    )

    # Relationships
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions_table,
        back_populates="roles",
    )

    def __repr__(self) -> str:
        """Return string representation of the role."""
        status = "active" if self.is_active else "inactive"
        return f"<Role(name='{self.name}', {status})>"


class Permission(Base):
    """Permission model for role-based access control (RBAC)."""

    __tablename__ = "permissions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique permission identifier",
    )

    # Permission identification
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Permission name (e.g., 'read_users', 'write_data')",
    )

    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Resource the permission applies to",
    )

    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Action allowed (e.g., 'read', 'write', 'delete')",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Permission description",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the permission is active",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Permission creation timestamp",
    )

    # Relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=role_permissions_table,
        back_populates="permissions",
    )

    def __repr__(self) -> str:
        """Return string representation of the permission."""
        status = "active" if self.is_active else "inactive"
        return f"<Permission(name='{self.name}', resource='{self.resource}', action='{self.action}', {status})>"


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
        now_utc = datetime.now(UTC)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            # Assume naive expires_at is UTC
            expires_at = expires_at.replace(tzinfo=UTC)
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


class SecurityEventLogger(Base):
    """Security event model for general security event logging.

    Tracks security events for AUTH-4 Enhanced Security Event Logging system.
    Used by SecurityLogger for general security event logging and audit trail.
    """

    __tablename__ = "security_events"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique security event identifier",
    )

    # Event identification
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of security event",
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Event severity level",
    )

    # Event context
    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="User identifier if applicable",
    )

    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
        index=True,
        comment="IP address if applicable",
    )

    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="User agent string if applicable",
    )

    session_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Session identifier if applicable",
    )

    # Event details
    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Additional event details and metadata",
    )

    risk_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        index=True,
        comment="Event risk score (0-100)",
    )

    # Timestamps
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        comment="Event timestamp",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    def __repr__(self) -> str:
        """Return string representation of the security event."""
        return f"<SecurityEventLogger(id={self.id}, type='{self.event_type}', severity='{self.severity}')>"


class SecurityEvent(Base):
    """Security event model for monitoring and tracking.

    Tracks security events for monitoring, threat detection, and activity correlation.
    Used by SecurityMonitor for stateless multi-worker deployment.
    """

    __tablename__ = "security_events_monitor"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique security event identifier",
    )

    # Event identification
    entity_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Entity key (user:id or ip:address)",
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of security event",
    )

    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Event severity level",
    )

    # Event context
    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="User identifier if applicable",
    )

    ip_address: Mapped[str | None] = mapped_column(
        INET,
        nullable=True,
        index=True,
        comment="IP address if applicable",
    )

    risk_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Event risk score (0-100)",
    )

    # Event details
    event_details: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Additional event details and metadata",
    )

    # Timestamp
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        comment="Event timestamp",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    def __repr__(self) -> str:
        """Return string representation of the security event."""
        return f"<SecurityEvent(id={self.id}, entity='{self.entity_key}', type='{self.event_type}', severity='{self.severity}')>"


class BlockedEntity(Base):
    """Blocked entity model for IP and user blocking.

    Tracks blocked IPs and users for security monitoring.
    Used by SecurityMonitor for stateless multi-worker deployment.
    """

    __tablename__ = "blocked_entities"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique blocked entity identifier",
    )

    # Entity identification
    entity_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Entity key (user:id or ip:address)",
    )

    entity_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Entity type (ip or user)",
    )

    entity_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Entity value (IP address or user ID)",
    )

    # Block details
    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for blocking",
    )

    blocked_by: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="System or user that initiated the block",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether the block is currently active",
    )

    # Timestamps
    blocked_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="When the entity was blocked",
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        comment="When the block expires (NULL for permanent)",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    def __repr__(self) -> str:
        """Return string representation of the blocked entity."""
        status = "active" if self.is_active else "inactive"
        return f"<BlockedEntity(type='{self.entity_type}', value='{self.entity_value}', {status})>"

    @property
    def is_expired(self) -> bool:
        """Check if the block has expired."""
        if self.expires_at is None:
            return False
        # Ensure both datetimes are timezone-aware and in UTC
        now_utc = datetime.now(UTC)
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            # Assume naive expires_at is UTC
            expires_at = expires_at.replace(tzinfo=UTC)
        return now_utc > expires_at

    @property
    def is_valid_block(self) -> bool:
        """Check if the block is valid (active and not expired)."""
        return self.is_active and not self.is_expired


class ThreatScore(Base):
    """Threat score model for tracking entity threat levels.

    Tracks dynamic threat scores for IPs and users.
    Used by SecurityMonitor for stateless multi-worker deployment.
    """

    __tablename__ = "threat_scores"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique threat score identifier",
    )

    # Entity identification
    entity_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        comment="Entity key (user:id or ip:address)",
    )

    entity_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Entity type (ip or user)",
    )

    entity_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Entity value (IP address or user ID)",
    )

    # Score details
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current threat score",
    )

    last_updated: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
        comment="When the score was last updated",
    )

    # Metadata
    score_details: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Additional score calculation details",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    def __repr__(self) -> str:
        """Return string representation of the threat score."""
        return f"<ThreatScore(type='{self.entity_type}', value='{self.entity_value}', score={self.score})>"


class MonitoringThreshold(Base):
    """Monitoring threshold model for configuration.

    Stores monitoring thresholds and configuration for the security monitor.
    Used by SecurityMonitor for stateless multi-worker deployment.
    """

    __tablename__ = "monitoring_thresholds"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique threshold identifier",
    )

    # Threshold identification
    threshold_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        comment="Threshold name (e.g., 'alert_threshold', 'time_window')",
    )

    # Threshold configuration
    threshold_value: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Threshold value",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description of the threshold",
    )

    # Metadata
    threshold_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Additional threshold metadata and configuration",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the threshold is active",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp",
    )

    last_updated: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="When the threshold was last updated",
    )

    def __repr__(self) -> str:
        """Return string representation of the monitoring threshold."""
        status = "active" if self.is_active else "inactive"
        return f"<MonitoringThreshold(name='{self.threshold_name}', value={self.threshold_value}, {status})>"


# Export all models
__all__ = [
    "AuthenticationEvent",
    "Base",
    "BlockedEntity",
    "MonitoringThreshold",
    "Permission",
    "Role",
    "SecurityEvent",
    "SecurityEventLogger",
    "ServiceToken",
    "ThreatScore",
    "UserSession",
    "role_permissions_table",
    "user_roles_table",
]
