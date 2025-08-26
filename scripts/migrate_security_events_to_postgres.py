#!/usr/bin/env python3
"""
Security Events Database Migration Script
=========================================

Migrates security events from SQLite to PostgreSQL for AUTH-4 database consolidation.

This script:
1. Connects to the existing SQLite security_events.db
2. Extracts all security events and metadata
3. Initializes PostgreSQL security events database
4. Migrates all data with proper type conversion
5. Validates migration success
6. Creates backup of original SQLite database

Usage:
    python scripts/migrate_security_events_to_postgres.py [--dry-run] [--backup-dir PATH]

Requirements:
- PostgreSQL server running at configured host
- SQLite security_events.db file present
- Write permissions for backup directory
"""

import argparse
import asyncio
import json
import logging
import shutil
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
from src.auth.models import SecurityEventCreate, SecurityEventSeverity, SecurityEventType

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SecurityEventsMigrator:
    """Migrates security events from SQLite to PostgreSQL."""

    def __init__(self, sqlite_path: str, backup_dir: str | None = None, dry_run: bool = False):
        """Initialize migrator.

        Args:
            sqlite_path: Path to SQLite database file
            backup_dir: Directory for backup files (defaults to ./backups)
            dry_run: If True, only analyze data without making changes
        """
        self.sqlite_path = Path(sqlite_path)
        self.backup_dir = Path(backup_dir or "./backups")
        self.dry_run = dry_run
        self.pg_db = None

        # Migration statistics
        self.stats = {
            "total_events": 0,
            "migrated_events": 0,
            "failed_events": 0,
            "events_by_type": {},
            "events_by_severity": {},
        }

    async def initialize_postgresql(self) -> None:
        """Initialize PostgreSQL database connection."""
        try:
            self.pg_db = SecurityEventsPostgreSQL()
            await self.pg_db.initialize()
            logger.info("PostgreSQL database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL database: {e}")
            raise

    def get_sqlite_connection(self) -> sqlite3.Connection:
        """Get SQLite database connection."""
        if not self.sqlite_path.exists():
            raise FileNotFoundError(f"SQLite database not found: {self.sqlite_path}")

        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to SQLite database: {e}")
            raise

    def analyze_sqlite_database(self) -> dict[str, Any]:
        """Analyze SQLite database structure and content."""
        analysis = {
            "exists": self.sqlite_path.exists(),
            "size_bytes": 0,
            "tables": [],
            "security_events_count": 0,
            "schema_info": {},
        }

        if not analysis["exists"]:
            return analysis

        analysis["size_bytes"] = self.sqlite_path.stat().st_size

        try:
            with self.get_sqlite_connection() as conn:
                cursor = conn.cursor()

                # Get table list
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                analysis["tables"] = [row[0] for row in cursor.fetchall()]

                # Check if security_events table exists
                if "security_events" in analysis["tables"]:
                    # Get table schema
                    cursor.execute("PRAGMA table_info(security_events)")
                    schema = cursor.fetchall()
                    analysis["schema_info"] = {
                        "columns": [{"name": row[1], "type": row[2], "nullable": not row[3]} for row in schema],
                    }

                    # Count events
                    cursor.execute("SELECT COUNT(*) FROM security_events")
                    analysis["security_events_count"] = cursor.fetchone()[0]

                    # Get sample event for structure analysis
                    if analysis["security_events_count"] > 0:
                        cursor.execute("SELECT * FROM security_events LIMIT 1")
                        sample = cursor.fetchone()
                        analysis["sample_event"] = dict(sample) if sample else None

        except Exception as e:
            analysis["error"] = str(e)
            logger.warning(f"Error analyzing SQLite database: {e}")

        return analysis

    def extract_sqlite_events(self) -> list[dict[str, Any]]:
        """Extract all security events from SQLite database."""
        events = []

        try:
            with self.get_sqlite_connection() as conn:
                cursor = conn.cursor()

                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='security_events'")
                if not cursor.fetchone():
                    logger.info("No security_events table found in SQLite database")
                    return events

                # Extract all events
                cursor.execute(
                    """
                    SELECT id, timestamp, event_type, severity, user_id, ip_address,
                           user_agent, session_id, details, risk_score, source
                    FROM security_events
                    ORDER BY timestamp ASC
                """,
                )

                for row in cursor.fetchall():
                    event_data = dict(row)

                    # Parse details JSON if present
                    if event_data.get("details"):
                        try:
                            event_data["details"] = json.loads(event_data["details"])
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse details JSON for event {event_data.get('id')}")
                            event_data["details"] = {}

                    events.append(event_data)

                    # Update statistics
                    event_type = event_data.get("event_type", "unknown")
                    severity = event_data.get("severity", "unknown")

                    self.stats["events_by_type"][event_type] = self.stats["events_by_type"].get(event_type, 0) + 1
                    self.stats["events_by_severity"][severity] = self.stats["events_by_severity"].get(severity, 0) + 1

                self.stats["total_events"] = len(events)
                logger.info(f"Extracted {len(events)} events from SQLite database")

        except Exception as e:
            logger.error(f"Failed to extract events from SQLite: {e}")
            raise

        return events

    def convert_to_postgres_format(self, sqlite_event: dict[str, Any]) -> SecurityEventCreate:
        """Convert SQLite event to PostgreSQL SecurityEventCreate format."""
        try:
            # Map event type
            event_type_str = sqlite_event.get("event_type", "UNKNOWN")
            try:
                event_type = SecurityEventType(event_type_str)
            except ValueError:
                logger.warning(f"Unknown event type '{event_type_str}', using UNKNOWN")
                event_type = SecurityEventType.UNKNOWN

            # Map severity
            severity_str = sqlite_event.get("severity", "INFO")
            try:
                severity = SecurityEventSeverity(severity_str)
            except ValueError:
                logger.warning(f"Unknown severity '{severity_str}', using INFO")
                severity = SecurityEventSeverity.INFO

            # Parse timestamp
            timestamp_str = sqlite_event.get("timestamp")
            if timestamp_str:
                try:
                    # Try parsing ISO format first
                    if "T" in timestamp_str:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    else:
                        # Try parsing as Unix timestamp
                        timestamp = datetime.fromtimestamp(float(timestamp_str), tz=UTC)
                except (ValueError, TypeError):
                    logger.warning(f"Failed to parse timestamp '{timestamp_str}', using current time")
                    timestamp = datetime.now(UTC)
            else:
                timestamp = datetime.now(UTC)

            # Ensure timezone awareness
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=UTC)

            return SecurityEventCreate(
                event_type=event_type,
                severity=severity,
                user_id=sqlite_event.get("user_id"),
                ip_address=sqlite_event.get("ip_address"),
                user_agent=sqlite_event.get("user_agent"),
                session_id=sqlite_event.get("session_id"),
                details=sqlite_event.get("details"),
                risk_score=sqlite_event.get("risk_score", 0),
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(f"Failed to convert event: {e}")
            raise

    async def migrate_events_to_postgres(self, events: list[dict[str, Any]]) -> None:
        """Migrate events to PostgreSQL database."""
        if self.dry_run:
            logger.info(f"DRY RUN: Would migrate {len(events)} events to PostgreSQL")
            return

        if not self.pg_db:
            raise RuntimeError("PostgreSQL database not initialized")

        failed_events = []

        for i, sqlite_event in enumerate(events):
            try:
                # Convert to PostgreSQL format
                pg_event = self.convert_to_postgres_format(sqlite_event)

                # Insert into PostgreSQL
                await self.pg_db.log_security_event(pg_event)

                self.stats["migrated_events"] += 1

                if (i + 1) % 100 == 0:
                    logger.info(f"Migrated {i + 1}/{len(events)} events")

            except Exception as e:
                logger.error(f"Failed to migrate event {sqlite_event.get('id', 'unknown')}: {e}")
                failed_events.append({"event": sqlite_event, "error": str(e)})
                self.stats["failed_events"] += 1

        if failed_events:
            logger.warning(f"Failed to migrate {len(failed_events)} events")
            # Save failed events for manual review
            failed_file = self.backup_dir / f"failed_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            failed_file.parent.mkdir(parents=True, exist_ok=True)
            with failed_file.open("w") as f:
                json.dump(failed_events, f, indent=2, default=str)
            logger.info(f"Failed events saved to: {failed_file}")

    def create_backup(self) -> Path:
        """Create backup of original SQLite database."""
        if not self.sqlite_path.exists():
            raise FileNotFoundError(f"Source database not found: {self.sqlite_path}")

        self.backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"security_events_backup_{timestamp}.db"

        if not self.dry_run:
            shutil.copy2(self.sqlite_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
        else:
            logger.info(f"DRY RUN: Would create backup at: {backup_path}")

        return backup_path

    async def validate_migration(self) -> bool:
        """Validate that migration was successful."""
        if self.dry_run or not self.pg_db:
            return True

        try:
            # Count events in PostgreSQL
            # Note: This would require implementing a count method in the PostgreSQL database class
            # For now, we'll rely on the migration statistics

            expected_count = self.stats["total_events"]
            migrated_count = self.stats["migrated_events"]

            success = migrated_count == expected_count

            if success:
                logger.info("Migration validation successful")
            else:
                logger.error(f"Migration validation failed: expected {expected_count}, migrated {migrated_count}")

            return success

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False

    def print_migration_summary(self) -> None:
        """Print migration summary statistics."""
        print("\n" + "=" * 60)
        print("SECURITY EVENTS MIGRATION SUMMARY")
        print("=" * 60)
        print(f"SQLite Database: {self.sqlite_path}")
        print(f"Backup Directory: {self.backup_dir}")
        print(f"Dry Run Mode: {self.dry_run}")
        print()
        print("MIGRATION STATISTICS:")
        print(f"  Total Events Found: {self.stats['total_events']}")
        print(f"  Successfully Migrated: {self.stats['migrated_events']}")
        print(f"  Failed Migrations: {self.stats['failed_events']}")
        print()

        if self.stats["events_by_type"]:
            print("EVENTS BY TYPE:")
            for event_type, count in sorted(self.stats["events_by_type"].items()):
                print(f"  {event_type}: {count}")
            print()

        if self.stats["events_by_severity"]:
            print("EVENTS BY SEVERITY:")
            for severity, count in sorted(self.stats["events_by_severity"].items()):
                print(f"  {severity}: {count}")
            print()

        if self.stats["migrated_events"] == self.stats["total_events"] and self.stats["failed_events"] == 0:
            print("✅ MIGRATION COMPLETED SUCCESSFULLY")
        elif self.stats["failed_events"] > 0:
            print("⚠️  MIGRATION COMPLETED WITH ERRORS")
        else:
            print("❌ MIGRATION FAILED")

        print("=" * 60)


async def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(
        description="Migrate security events from SQLite to PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--sqlite-path",
        default="security_events.db",
        help="Path to SQLite database file (default: security_events.db)",
    )

    parser.add_argument("--backup-dir", default="./backups", help="Directory for backup files (default: ./backups)")

    parser.add_argument("--dry-run", action="store_true", help="Analyze data without making changes")

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting security events database migration")

    try:
        # Initialize migrator
        migrator = SecurityEventsMigrator(
            sqlite_path=args.sqlite_path,
            backup_dir=args.backup_dir,
            dry_run=args.dry_run,
        )

        # Analyze SQLite database
        logger.info("Analyzing SQLite database...")
        analysis = migrator.analyze_sqlite_database()

        if not analysis["exists"]:
            logger.error(f"SQLite database not found: {args.sqlite_path}")
            return 1

        logger.info(f"SQLite database size: {analysis['size_bytes']} bytes")
        logger.info(f"Tables found: {analysis['tables']}")
        logger.info(f"Security events count: {analysis['security_events_count']}")

        if analysis["security_events_count"] == 0:
            logger.info("No security events to migrate")
            migrator.print_migration_summary()
            return 0

        # Create backup
        logger.info("Creating backup of SQLite database...")
        backup_path = migrator.create_backup()

        # Initialize PostgreSQL
        logger.info("Initializing PostgreSQL database...")
        await migrator.initialize_postgresql()

        # Extract events from SQLite
        logger.info("Extracting events from SQLite...")
        events = migrator.extract_sqlite_events()

        if not events:
            logger.info("No events found to migrate")
            migrator.print_migration_summary()
            return 0

        # Migrate events to PostgreSQL
        logger.info(f"Migrating {len(events)} events to PostgreSQL...")
        await migrator.migrate_events_to_postgres(events)

        # Validate migration
        logger.info("Validating migration...")
        validation_success = await migrator.validate_migration()

        # Print summary
        migrator.print_migration_summary()

        if not validation_success:
            logger.error("Migration validation failed")
            return 1

        logger.info("Migration completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1

    finally:
        # Cleanup
        if hasattr(migrator, "pg_db") and migrator.pg_db:
            await migrator.pg_db.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
