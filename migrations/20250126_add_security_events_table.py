"""Add security_events table for SecurityLogger.

Revision ID: 20250126_add_security_events_table
Revises: 20250125_add_security_monitor_tables
Create Date: 2025-01-26

Migration to add security_events table for AUTH-4 SecurityLogger component.
This table is separate from security_events_monitor and serves the general
security event logging functionality.
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

# revision identifiers
revision = "20250126_add_security_events_table"
down_revision = "20250125_add_security_monitor_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create security_events table for SecurityLogger."""

    # Create security_events table
    op.create_table(
        "security_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("severity", sa.String(50), nullable=False, index=True),
        sa.Column("user_id", sa.String(255), nullable=True, index=True),
        sa.Column("ip_address", INET, nullable=True, index=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("session_id", sa.String(255), nullable=True, index=True),
        sa.Column("details", JSONB, nullable=False, server_default="{}"),
        sa.Column("risk_score", sa.Integer, nullable=False, default=0, index=True),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), nullable=False, index=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        comment="General security events for AUTH-4 Enhanced Security Event Logging",
    )

    # Create indexes for security_events
    op.create_index("ix_security_events_event_type", "security_events", ["event_type"])
    op.create_index("ix_security_events_severity", "security_events", ["severity"])
    op.create_index("ix_security_events_user_id", "security_events", ["user_id"])
    op.create_index("ix_security_events_ip_address", "security_events", ["ip_address"])
    op.create_index("ix_security_events_session_id", "security_events", ["session_id"])
    op.create_index("ix_security_events_risk_score", "security_events", ["risk_score"])
    op.create_index("ix_security_events_timestamp", "security_events", ["timestamp"])

    # Composite indexes for common SecurityLogger queries
    op.create_index("ix_security_events_user_timestamp", "security_events", ["user_id", "timestamp"])
    op.create_index("ix_security_events_type_severity", "security_events", ["event_type", "severity"])
    op.create_index("ix_security_events_severity_timestamp", "security_events", ["severity", "timestamp"])


def downgrade() -> None:
    """Drop security_events table."""
    op.drop_table("security_events")
