#!/usr/bin/env python3
"""Validation script for AUTH-2 service token management implementation.

This script validates the database foundation components for service token management:
- Database connection and configuration
- SQLAlchemy models and migrations
- Type safety and validation
- Performance optimization (indexes, connection pooling)
- Security best practices

Run this script to ensure the AUTH-2 implementation meets all requirements.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text

from src.config.settings import get_settings
from src.database.connection import DatabaseManager, database_health_check, initialize_database
from src.database.models import ServiceToken

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class AuthImplementationValidator:
    """Comprehensive validator for AUTH-2 service token implementation."""

    def __init__(self) -> None:
        """Initialize validator."""
        self.settings = get_settings()
        self.db_manager = DatabaseManager()
        self.validation_results: list[dict[str, Any]] = []

    def log_result(self, test_name: str, passed: bool, message: str, details: Any = None) -> None:
        """Log validation result."""
        result = {"test": test_name, "passed": passed, "message": message, "details": details}
        self.validation_results.append(result)

        if passed:
            logger.info("✅ %s: %s", test_name, message)
        else:
            logger.error("❌ %s: %s", test_name, message)
            if details:
                logger.error("   Details: %s", details)

    async def validate_database_configuration(self) -> None:
        """Validate database configuration and settings."""
        logger.info("Validating database configuration...")

        try:
            # Test basic configuration access
            has_db_url = self.settings.database_url is not None
            has_db_password = self.settings.database_password is not None

            self.log_result(
                "Database Configuration",
                True,
                f"Configuration loaded: database_url={'present' if has_db_url else 'not set'}, password={'present' if has_db_password else 'not set'}",
            )

            # Check we have some database configuration
            if not has_db_url and not has_db_password:
                self.log_result(
                    "Configuration Validation",
                    False,
                    "No database configuration found - need either database_url or database_password",
                )
            else:
                self.log_result("Configuration Validation", True, "Database configuration is available")

        except Exception as e:
            self.log_result("Database Configuration", False, f"Configuration validation failed: {e!s}", str(e))

    async def validate_database_connection(self) -> None:
        """Validate database connection functionality."""
        logger.info("Validating database connection...")

        try:
            # Initialize database connection
            await initialize_database()

            self.log_result("Database Connection", True, "Database connection initialized successfully")

            # Test health check
            health_ok = await database_health_check()
            self.log_result(
                "Database Health Check",
                health_ok,
                "Health check passed" if health_ok else "Health check failed",
            )

        except Exception as e:
            self.log_result("Database Connection", False, f"Database connection error: {e!s}", str(e))

    async def validate_sqlalchemy_models(self) -> None:
        """Validate SQLAlchemy models and Pydantic schemas."""
        logger.info("Validating SQLAlchemy models...")

        try:
            # Test ServiceToken model structure
            token_columns = ServiceToken.__table__.columns.keys()
            expected_columns = {
                "id",
                "token_name",
                "token_hash",
                "created_at",
                "last_used",
                "expires_at",
                "usage_count",
                "is_active",
                "token_metadata",
            }

            missing_columns = expected_columns - set(token_columns)
            if missing_columns:
                raise ValueError(f"Missing columns: {missing_columns}")

            self.log_result("ServiceToken Model", True, f"Model has all required columns: {sorted(token_columns)}")

            # Test table constraints
            constraints = [c.name for c in ServiceToken.__table__.constraints]
            expected_constraints = ["valid_expiration_date", "non_negative_usage_count"]

            for constraint in expected_constraints:
                if constraint in constraints:
                    self.log_result(f"Constraint {constraint}", True, f"Constraint {constraint} is properly defined")
                else:
                    self.log_result(f"Constraint {constraint}", False, f"Missing constraint: {constraint}")

            # Test indexes
            indexes = [idx.name for idx in ServiceToken.__table__.indexes]
            if indexes:
                self.log_result(
                    "Database Indexes",
                    True,
                    f"Found {len(indexes)} indexes for performance optimization",
                    indexes,
                )
            else:
                self.log_result("Database Indexes", False, "No indexes found - performance may be poor")

        except Exception as e:
            self.log_result("SQLAlchemy Models", False, f"Model validation failed: {e!s}", str(e))

    async def validate_model_methods(self) -> None:
        """Validate model methods and properties."""
        logger.info("Validating model methods...")

        try:
            # Test ServiceToken methods
            token = ServiceToken()
            token.expires_at = None

            # Test is_expired property with no expiration
            if not token.is_expired:
                self.log_result(
                    "ServiceToken is_expired (no expiry)",
                    True,
                    "Non-expiring token correctly reports not expired",
                )
            else:
                self.log_result(
                    "ServiceToken is_expired (no expiry)",
                    False,
                    "Non-expiring token incorrectly reports expired",
                )

            # Test to_dict method
            token_dict = token.to_dict()
            if isinstance(token_dict, dict) and "token_name" in token_dict:
                self.log_result("ServiceToken to_dict", True, "to_dict method works correctly")
            else:
                self.log_result("ServiceToken to_dict", False, "to_dict method failed")

        except Exception as e:
            self.log_result("Model Methods", False, f"Model method validation failed: {e!s}", str(e))

    async def validate_database_session(self) -> None:
        """Validate database session functionality."""
        logger.info("Validating database session management...")

        try:
            # Test session creation and cleanup using the get_db dependency
            from src.database.connection import get_db

            async for session in get_db():
                result = await session.execute(text("SELECT 1 as test_value"))
                value = result.scalar()

                if value == 1:
                    self.log_result("Database Session", True, "Session creation and query execution successful")
                else:
                    self.log_result("Database Session", False, f"Unexpected query result: {value}")
                break  # Only test the first session

        except Exception as e:
            self.log_result("Database Session", False, f"Session management failed: {e!s}", str(e))

    async def validate_migration_script(self) -> None:
        """Validate database migration script."""
        logger.info("Validating migration script...")

        migration_path = Path(__file__).parent.parent / "src" / "database" / "migrations" / "001_auth_schema.sql"

        try:
            if not migration_path.exists():
                self.log_result("Migration Script", False, f"Migration script not found at {migration_path}")
                return

            migration_content = migration_path.read_text()

            # Check for required SQL components
            required_components = [
                "CREATE TABLE service_tokens",
                "CREATE TABLE user_sessions",
                "CREATE TABLE authentication_events",
                "CREATE INDEX",
                "uuid-ossp",
            ]

            missing_components = []
            for component in required_components:
                if component not in migration_content:
                    missing_components.append(component)

            if missing_components:
                self.log_result("Migration Script", False, f"Missing components: {missing_components}")
            else:
                self.log_result(
                    "Migration Script",
                    True,
                    "Migration script contains all required components",
                    {"size_kb": len(migration_content) // 1024},
                )

        except Exception as e:
            self.log_result("Migration Script", False, f"Migration script validation failed: {e!s}", str(e))

    async def validate_security_features(self) -> None:
        """Validate security features and best practices."""
        logger.info("Validating security features...")

        try:
            # Check that sensitive data is properly handled
            settings_dict = self.settings.model_dump()

            # Verify database_password is not exposed
            if "database_password" in settings_dict:
                db_password = settings_dict["database_password"]
                if db_password and not str(db_password).startswith("**"):
                    self.log_result("Password Security", False, "Database password may be exposed in settings dump")
                else:
                    self.log_result("Password Security", True, "Database password is properly masked")

            # Check connection security
            health_ok = await database_health_check()
            self.log_result(
                "Connection Security",
                health_ok,
                "Database health check works without exposing credentials",
            )

            # Verify SecretStr usage
            if hasattr(self.settings, "database_password") and self.settings.database_password:
                secret_value = self.settings.database_password.get_secret_value()
                if isinstance(secret_value, str):
                    self.log_result("SecretStr Usage", True, "Database password properly uses SecretStr")
                else:
                    self.log_result("SecretStr Usage", False, "Database password SecretStr not working properly")

        except Exception as e:
            self.log_result("Security Features", False, f"Security validation failed: {e!s}", str(e))

    def print_summary(self) -> bool:
        """Print validation summary and return overall success."""
        logger.info("\n" + "=" * 80)
        logger.info("AUTH-2 IMPLEMENTATION VALIDATION SUMMARY")
        logger.info("=" * 80)

        passed_count = sum(1 for result in self.validation_results if result["passed"])
        total_count = len(self.validation_results)
        success_rate = (passed_count / total_count * 100) if total_count > 0 else 0

        logger.info(f"Tests Passed: {passed_count}/{total_count} ({success_rate:.1f}%)")
        logger.info("")

        # Group results by category
        categories = {}
        for result in self.validation_results:
            category = result["test"].split()[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(result)

        for category, results in categories.items():
            category_passed = sum(1 for r in results if r["passed"])
            category_total = len(results)
            logger.info(f"{category}: {category_passed}/{category_total}")

            for result in results:
                status = "✅" if result["passed"] else "❌"
                logger.info(f"  {status} {result['test']}: {result['message']}")

        logger.info("")

        if success_rate == 100:
            logger.info("🎉 All validations passed! AUTH-2 implementation is ready.")
            return True
        if success_rate >= 80:
            logger.warning("⚠️  Most validations passed, but some issues need attention.")
            return False
        logger.error("🚨 Multiple validation failures - implementation needs work.")
        return False

    async def run_all_validations(self) -> bool:
        """Run all validation tests."""
        logger.info("Starting AUTH-2 implementation validation...")
        logger.info("=" * 80)

        try:
            await self.validate_database_configuration()
            await self.validate_database_connection()
            await self.validate_sqlalchemy_models()
            await self.validate_model_methods()
            await self.validate_database_session()
            await self.validate_migration_script()
            await self.validate_security_features()

            return self.print_summary()

        except Exception as e:
            logger.error("Validation failed with unexpected error: %s", e)
            return False


async def main() -> None:
    """Main validation function."""
    validator = AuthImplementationValidator()
    success = await validator.run_all_validations()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
