"""Add security monitor tables for stateless design.

Revision ID: 20250125_add_security_monitor_tables
Revises: N/A
Create Date: 2025-01-25

Migration to support stateless SecurityMonitor by adding:
- security_events_monitor: Security events for monitoring
- blocked_entities: Blocked IPs and users
- threat_scores: Dynamic threat scores
- monitoring_thresholds: Configuration thresholds
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

# revision identifiers
revision = "20250125_add_security_monitor_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create security monitor tables for stateless design."""

    # Create security_events_monitor table
    op.create_table(
        "security_events_monitor",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("entity_key", sa.String(255), nullable=False, index=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("severity", sa.String(50), nullable=False, index=True),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("ip_address", INET, nullable=True, index=True),
        sa.Column("risk_score", sa.Integer, nullable=False, default=0),
        sa.Column("event_details", JSONB, nullable=False, server_default="{}"),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False, index=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        comment="Security events for monitoring and threat detection",
    )

    # Create indexes for security_events_monitor
    op.create_index("ix_security_events_monitor_entity_key", "security_events_monitor", ["entity_key"])
    op.create_index("ix_security_events_monitor_event_type", "security_events_monitor", ["event_type"])
    op.create_index("ix_security_events_monitor_severity", "security_events_monitor", ["severity"])
    op.create_index("ix_security_events_monitor_user_id", "security_events_monitor", ["user_id"])
    op.create_index("ix_security_events_monitor_ip_address", "security_events_monitor", ["ip_address"])
    op.create_index("ix_security_events_monitor_timestamp", "security_events_monitor", ["timestamp"])

    # Composite indexes for common queries
    op.create_index(
        "ix_security_events_monitor_entity_timestamp",
        "security_events_monitor",
        ["entity_key", "timestamp"],
    )
    op.create_index("ix_security_events_monitor_type_severity", "security_events_monitor", ["event_type", "severity"])

    # Create blocked_entities table
    op.create_table(
        "blocked_entities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("entity_key", sa.String(255), nullable=False, unique=True),
        sa.Column("entity_type", sa.String(20), nullable=False, index=True),
        sa.Column("entity_value", sa.String(255), nullable=False, index=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("blocked_by", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True, index=True),
        sa.Column("blocked_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        comment="Blocked IP addresses and users for security monitoring",
    )

    # Create indexes for blocked_entities
    op.create_index("ix_blocked_entities_entity_key", "blocked_entities", ["entity_key"])
    op.create_index("ix_blocked_entities_entity_type", "blocked_entities", ["entity_type"])
    op.create_index("ix_blocked_entities_entity_value", "blocked_entities", ["entity_value"])
    op.create_index("ix_blocked_entities_is_active", "blocked_entities", ["is_active"])
    op.create_index("ix_blocked_entities_blocked_at", "blocked_entities", ["blocked_at"])

    # Composite index for active blocks lookup
    op.create_index("ix_blocked_entities_active_lookup", "blocked_entities", ["entity_key", "is_active"])

    # Create threat_scores table
    op.create_table(
        "threat_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("entity_key", sa.String(255), nullable=False, unique=True),
        sa.Column("entity_type", sa.String(20), nullable=False, index=True),
        sa.Column("entity_value", sa.String(255), nullable=False, index=True),
        sa.Column("score", sa.Integer, nullable=False, default=0),
        sa.Column(
            "last_updated",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            index=True,
        ),
        sa.Column("score_details", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        comment="Dynamic threat scores for IPs and users",
    )

    # Create indexes for threat_scores
    op.create_index("ix_threat_scores_entity_key", "threat_scores", ["entity_key"])
    op.create_index("ix_threat_scores_entity_type", "threat_scores", ["entity_type"])
    op.create_index("ix_threat_scores_entity_value", "threat_scores", ["entity_value"])
    op.create_index("ix_threat_scores_last_updated", "threat_scores", ["last_updated"])
    op.create_index("ix_threat_scores_score", "threat_scores", ["score"])

    # Create monitoring_thresholds table
    op.create_table(
        "monitoring_thresholds",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("threshold_name", sa.String(100), nullable=False, unique=True),
        sa.Column("threshold_value", sa.Integer, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("threshold_metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("last_updated", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        comment="Monitoring thresholds and configuration",
    )

    # Create indexes for monitoring_thresholds
    op.create_index("ix_monitoring_thresholds_threshold_name", "monitoring_thresholds", ["threshold_name"])
    op.create_index("ix_monitoring_thresholds_is_active", "monitoring_thresholds", ["is_active"])

    # Insert default monitoring thresholds
    op.execute(
        """
        INSERT INTO monitoring_thresholds (id, threshold_name, threshold_value, description, is_active, threshold_metadata)
        VALUES
        (gen_random_uuid(), 'alert_threshold', 5, 'Number of events to trigger alert', true, '{"default": true, "created_by": "migration"}'),
        (gen_random_uuid(), 'time_window', 60, 'Time window in seconds for event correlation', true, '{"default": true, "created_by": "migration"}')
    """,
    )


def downgrade() -> None:
    """Drop security monitor tables."""

    # Drop tables in reverse order
    op.drop_table("monitoring_thresholds")
    op.drop_table("threat_scores")
    op.drop_table("blocked_entities")
    op.drop_table("security_events_monitor")
