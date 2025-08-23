#!/usr/bin/env python3
"""Database migration script for PromptCraft AUTH-3 implementation.

This script executes database migrations to set up the AUTH-3 Role-Based
Access Control system on top of the existing AUTH-1 and AUTH-2 infrastructure.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text

from src.database.connection import get_database_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_migration(migration_file: str) -> bool:
    """Execute a database migration script.

    Args:
        migration_file: Path to the SQL migration file

    Returns:
        True if migration was successful, False otherwise
    """
    migration_path = Path(__file__).parent.parent / "src" / "database" / "migrations" / migration_file

    if not migration_path.exists():
        logger.error("Migration file not found: %s", migration_path)
        return False

    try:
        # Read migration SQL
        migration_sql = migration_path.read_text(encoding="utf-8")
        logger.info("Loaded migration: %s (%d characters)", migration_file, len(migration_sql))

        # Get database manager
        db_manager = get_database_manager()
        await db_manager.initialize()

        # Execute migration
        async with db_manager.get_session() as session:
            # Execute the migration SQL
            logger.info("Executing migration: %s", migration_file)
            await session.execute(text(migration_sql))
            await session.commit()
            logger.info("Migration completed successfully: %s", migration_file)

        return True

    except Exception as e:
        logger.error("Migration failed: %s", e)
        return False


async def check_migration_status() -> dict[str, bool]:
    """Check which migrations have been applied.

    Returns:
        Dict mapping migration names to their execution status
    """
    try:
        db_manager = get_database_manager()
        await db_manager.initialize()

        status = {}

        async with db_manager.get_session() as session:
            # Check if AUTH-1/AUTH-2 tables exist (001 migration)
            result = await session.execute(
                text(
                    """
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name IN ('user_sessions', 'service_tokens')
                )
            """,
                ),
            )
            status["001_auth_schema.sql"] = bool(result.scalar())

            # Check if AUTH-3 tables exist (002 migration)
            result = await session.execute(
                text(
                    """
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name IN ('roles', 'permissions', 'role_permissions', 'user_roles')
                )
            """,
                ),
            )
            status["002_auth_rbac_schema.sql"] = bool(result.scalar())

        return status

    except Exception as e:
        logger.error("Failed to check migration status: %s", e)
        return {}


async def main() -> None:
    """Main migration execution function."""
    logger.info("PromptCraft Database Migration Tool")
    logger.info("=====================================")

    # Check current migration status
    logger.info("Checking current migration status...")
    status = await check_migration_status()

    for migration, applied in status.items():
        status_text = "✓ Applied" if applied else "✗ Not Applied"
        logger.info("  %s: %s", migration, status_text)

    # Determine which migrations to run
    migrations_to_run = []

    # Always ensure 001 is applied first
    if not status.get("001_auth_schema.sql", False):
        migrations_to_run.append("001_auth_schema.sql")

    # Apply 002 if not already applied
    if not status.get("002_auth_rbac_schema.sql", False):
        migrations_to_run.append("002_auth_rbac_schema.sql")

    if not migrations_to_run:
        logger.info("All migrations are already applied. Nothing to do.")
        return

    # Run pending migrations
    logger.info("Running pending migrations...")
    all_successful = True

    for migration in migrations_to_run:
        logger.info("Running migration: %s", migration)
        success = await run_migration(migration)

        if success:
            logger.info("✓ Migration successful: %s", migration)
        else:
            logger.error("✗ Migration failed: %s", migration)
            all_successful = False
            break

    if all_successful:
        logger.info("All migrations completed successfully!")
        logger.info("AUTH-3 Role-Based Access Control system is now ready.")
    else:
        logger.error("Migration process failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    # Check environment
    if not os.getenv("DATABASE_URL") and not all(
        [os.getenv("DB_HOST"), os.getenv("DB_NAME"), os.getenv("DB_USER"), os.getenv("DB_PASSWORD")],
    ):
        logger.error("Database configuration not found. Please set DATABASE_URL or DB_* environment variables.")
        sys.exit(1)

    # Run migrations
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Migration interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        sys.exit(1)
