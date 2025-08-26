"""Alter security_events table for SecurityLogger compatibility.

Revision ID: 20250126_alter_security_events_for_logger
Revises: 20250126_add_security_events_table
Create Date: 2025-01-26

Migration to modify the existing security_events table to match SecurityLogger expectations.
The table was created with monitor-style columns but SecurityLogger expects different schema.
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "20250126_alter_security_events_for_logger"
down_revision = "20250126_add_security_events_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Alter security_events table to match SecurityLogger expectations."""

    # Drop entity_key column (not used by SecurityLogger)
    op.drop_column("security_events", "entity_key")

    # Rename event_details to details
    op.alter_column("security_events", "event_details", new_column_name="details")

    # Add missing columns for SecurityLogger
    op.add_column(
        "security_events", sa.Column("user_agent", sa.Text, nullable=True, comment="User agent string if applicable"),
    )
    op.add_column(
        "security_events",
        sa.Column("session_id", sa.String(255), nullable=True, index=True, comment="Session identifier if applicable"),
    )

    # Create indexes for new columns
    op.create_index("ix_security_events_session_id", "security_events", ["session_id"])


def downgrade() -> None:
    """Revert security_events table changes."""

    # Remove added columns
    op.drop_index("ix_security_events_session_id", "security_events")
    op.drop_column("security_events", "session_id")
    op.drop_column("security_events", "user_agent")

    # Rename details back to event_details
    op.alter_column("security_events", "details", new_column_name="event_details")

    # Add back entity_key column
    op.add_column(
        "security_events",
        sa.Column(
            "entity_key", sa.String(255), nullable=False, index=True, comment="Entity key (user:id or ip:address)",
        ),
    )
