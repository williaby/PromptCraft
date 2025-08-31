#!/usr/bin/env python3
# nosemgrep
"""Migration script to create security monitor tables.

This script creates the necessary PostgreSQL tables for the stateless
SecurityMonitor implementation. Run this after converting from the
stateful version to the stateless version.

Usage:
    python scripts/migrate_security_monitor.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import inspect, text

from src.database.connection import get_database_manager
from src.database.models import Base


async def create_tables():
    """Create security monitor tables."""
    print("Starting security monitor database migration...")

    try:
        # Get database manager
        db_manager = get_database_manager()
        await db_manager.initialize()

        print("✓ Database connection established")

        # Create tables using SQLAlchemy metadata
        async with db_manager.get_session() as session:
            # Get the underlying engine from the session
            engine = session.get_bind()

            # Create tables for security monitor models
            async with engine.begin() as conn:
                # Create tables
                await conn.run_sync(Base.metadata.create_all)

                print("✓ Tables created successfully")

                # Insert default monitoring thresholds
                await conn.execute(
                    text(
                        """
                    INSERT INTO monitoring_thresholds (threshold_name, threshold_value, description, is_active, threshold_metadata)
                    VALUES
                    ('alert_threshold', 5, 'Number of events to trigger alert', true, '{"default": true, "created_by": "migration_script"}'),
                    ('time_window', 60, 'Time window in seconds for event correlation', true, '{"default": true, "created_by": "migration_script"}')
                    ON CONFLICT (threshold_name) DO NOTHING
                """,
                    ),
                )

                print("✓ Default thresholds inserted")

        # Verify tables exist
        async with db_manager.get_session() as session:
            # Check each table using SQLAlchemy inspector (safe from SQL injection)
            tables = ["security_events_monitor", "blocked_entities", "threat_scores", "monitoring_thresholds"]

            engine = session.get_bind()
            inspector = inspect(engine)
            existing_tables = inspector.get_table_names()

            for table in tables:
                if table in existing_tables:
                    print(f"✓ Table '{table}' verified")
                else:
                    print(f"✗ Table '{table}' not found!")
                    return False

        print("\n🎉 Migration completed successfully!")
        print("\nCreated tables:")
        print("  - security_events_monitor: Security events for monitoring")
        print("  - blocked_entities: Blocked IP addresses and users")
        print("  - threat_scores: Dynamic threat scores")
        print("  - monitoring_thresholds: Configuration thresholds")

        print("\nThe SecurityMonitor is now ready for stateless operation!")
        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False
    finally:
        await db_manager.close()


async def verify_migration():
    """Verify the migration was successful."""
    print("\nVerifying migration...")

    try:
        db_manager = get_database_manager()
        await db_manager.initialize()

        async with db_manager.get_session() as session:
            # Test basic operations on each table

            # Check monitoring thresholds
            result = await session.execute(text("SELECT COUNT(*) FROM monitoring_thresholds WHERE is_active = true"))
            threshold_count = result.scalar()
            print(f"✓ Found {threshold_count} active monitoring thresholds")

            # Verify indexes exist
            index_queries = [
                "SELECT indexname FROM pg_indexes WHERE tablename = 'security_events_monitor' AND indexname LIKE 'ix_%'",
                "SELECT indexname FROM pg_indexes WHERE tablename = 'blocked_entities' AND indexname LIKE 'ix_%'",
                "SELECT indexname FROM pg_indexes WHERE tablename = 'threat_scores' AND indexname LIKE 'ix_%'",
                "SELECT indexname FROM pg_indexes WHERE tablename = 'monitoring_thresholds' AND indexname LIKE 'ix_%'",
            ]

            total_indexes = 0
            for query in index_queries:
                result = await session.execute(text(query))
                indexes = result.fetchall()
                total_indexes += len(indexes)

            print(f"✓ Found {total_indexes} performance indexes")

        print("✓ Migration verification passed")
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        await db_manager.close()


async def show_usage_examples():
    """Show usage examples for the stateless SecurityMonitor."""
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES")
    print("=" * 60)

    print(
        """
The SecurityMonitor can now be used in a stateless manner:

```python
from src.auth.security_monitor import SecurityMonitor
from src.auth.models import SecurityEventResponse, EventType, EventSeverity

# Initialize monitor (no background tasks created)
monitor = SecurityMonitor(alert_threshold=5, time_window=60)
await monitor.initialize()

# Track events (stored in database)
event = SecurityEventResponse(
    id=uuid4(),
    event_type=EventType.AUTHENTICATION_FAILURE.value,
    severity=EventSeverity.HIGH.value,
    user_id="user123",
    ip_address="192.168.1.100",
    timestamp=datetime.now(timezone.utc),
    risk_score=75,
    details={"reason": "invalid_credentials"}
)
await monitor.track_event(event)

# Check threat scores (from database)
score = await monitor.get_threat_score("192.168.1.100", "ip")
print(f"Threat score: {score}")

# Block entities (stored in database)
await monitor.block_ip("192.168.1.100", "Suspicious activity")

# Check if blocked (database query)
blocked = await monitor.is_blocked_async("192.168.1.100", "ip")
print(f"Blocked: {blocked}")

# Get monitoring stats (database aggregation)
stats = await monitor.get_monitoring_stats()
print(f"Stats: {stats}")

# Cleanup old data (database operations)
cleanup = await monitor.cleanup_old_data(retention_hours=24)
print(f"Cleanup: {cleanup}")
```

Key Benefits:
- ✓ Multi-worker safe (no shared memory state)
- ✓ Persistent across restarts
- ✓ Scalable database storage
- ✓ Identical public API
- ✓ Automatic data retention
    """,
    )


def main():
    """Main migration function."""
    print("SecurityMonitor Stateless Migration")
    print("=" * 50)

    async def run_migration():
        success = await create_tables()
        if success:
            await verify_migration()
            await show_usage_examples()
        return success

    try:
        success = asyncio.run(run_migration())
        if success:
            print("\n✅ Migration completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Migration failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
