"""Initial migration from existing models

Revision ID: 001
Revises:
Create Date: 2025-09-11 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create initial database schema from existing SQL files."""

    # Create roles table
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create permissions table
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("resource", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create service_tokens table
    op.create_table(
        "service_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("last_4_chars", sa.String(length=4), nullable=False),
        sa.Column("scope", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("usage_count", sa.Integer(), nullable=True),
        sa.Column("max_usage_count", sa.Integer(), nullable=True),
        sa.Column("allowed_ips", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )

    # Create user_sessions table
    op.create_table(
        "user_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("user_tier", sa.String(length=50), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("cloudflare_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("last_accessed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )

    # Create authentication_events table
    op.create_table(
        "authentication_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create security_events table
    op.create_table(
        "security_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("source_ip", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("endpoint", sa.String(length=255), nullable=True),
        sa.Column("method", sa.String(length=10), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("user_email", sa.String(length=255), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create blocked_entities table
    op.create_table(
        "blocked_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_value", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("blocked_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("blocked_until", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("is_permanent", sa.Boolean(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity_type", "entity_value", name="unique_entity"),
    )

    # Create threat_scores table
    op.create_table(
        "threat_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_value", sa.String(length=255), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.Column("last_incident_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("incident_count", sa.Integer(), nullable=False),
        sa.Column("decay_rate", sa.Float(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("entity_type", "entity_value", name="unique_threat_entity"),
    )

    # Create monitoring_thresholds table
    op.create_table(
        "monitoring_thresholds",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("threshold_value", sa.Float(), nullable=False),
        sa.Column("comparison_operator", sa.String(length=10), nullable=False),
        sa.Column("time_window_minutes", sa.Integer(), nullable=False),
        sa.Column("alert_severity", sa.String(length=20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Create indexes for performance
    op.create_index("idx_service_tokens_active", "service_tokens", ["is_active"])
    op.create_index("idx_service_tokens_expires", "service_tokens", ["expires_at"])
    op.create_index("idx_user_sessions_active", "user_sessions", ["is_active"])
    op.create_index("idx_user_sessions_expires", "user_sessions", ["expires_at"])
    op.create_index("idx_user_sessions_email", "user_sessions", ["user_email"])
    op.create_index("idx_auth_events_email", "authentication_events", ["user_email"])
    op.create_index("idx_auth_events_created", "authentication_events", ["created_at"])
    op.create_index("idx_security_events_created", "security_events", ["created_at"])
    op.create_index("idx_security_events_severity", "security_events", ["severity"])
    op.create_index("idx_blocked_entities_type_value", "blocked_entities", ["entity_type", "entity_value"])
    op.create_index("idx_threat_scores_entity", "threat_scores", ["entity_type", "entity_value"])


def downgrade() -> None:
    """Drop all tables."""

    # Drop indexes first
    op.drop_index("idx_threat_scores_entity", table_name="threat_scores")
    op.drop_index("idx_blocked_entities_type_value", table_name="blocked_entities")
    op.drop_index("idx_security_events_severity", table_name="security_events")
    op.drop_index("idx_security_events_created", table_name="security_events")
    op.drop_index("idx_auth_events_created", table_name="authentication_events")
    op.drop_index("idx_auth_events_email", table_name="authentication_events")
    op.drop_index("idx_user_sessions_email", table_name="user_sessions")
    op.drop_index("idx_user_sessions_expires", table_name="user_sessions")
    op.drop_index("idx_user_sessions_active", table_name="user_sessions")
    op.drop_index("idx_service_tokens_expires", table_name="service_tokens")
    op.drop_index("idx_service_tokens_active", table_name="service_tokens")

    # Drop tables in reverse order
    op.drop_table("monitoring_thresholds")
    op.drop_table("threat_scores")
    op.drop_table("blocked_entities")
    op.drop_table("security_events")
    op.drop_table("authentication_events")
    op.drop_table("user_sessions")
    op.drop_table("service_tokens")
    op.drop_table("permissions")
    op.drop_table("roles")
