"""Alembic environment configuration for PromptCraft-Hybrid database migrations.

This module integrates Alembic with the PromptCraft settings system and SQLAlchemy models
to provide secure, environment-aware database migrations.
"""

import logging
from logging.config import fileConfig
import os
from pathlib import Path
import sys

from sqlalchemy import engine_from_config, pool

from alembic import context


# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.config.settings import get_settings
    from src.database.models import Base

    SETTINGS_AVAILABLE = True
except ImportError as e:
    logging.warning("Could not import PromptCraft settings or models: %s", e)
    SETTINGS_AVAILABLE = False
    Base = None

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
if SETTINGS_AVAILABLE and Base is not None:
    target_metadata = Base.metadata
    logging.info("Loaded PromptCraft database models for migration autogeneration")
else:
    target_metadata = None
    logging.warning("Database models not available - autogenerate will not work")


def get_database_url() -> str:
    """Get the database URL from application settings with fallback options.

    Returns:
        Database connection URL string
    """
    # Try to get URL from application settings first
    if SETTINGS_AVAILABLE:
        try:
            settings = get_settings(validate_on_startup=False)

            # Use database_url if available, otherwise construct from components
            if settings.database_url:
                db_url = settings.database_url.get_secret_value()
                # Ensure we use psycopg2 for synchronous connections in migrations
                if db_url.startswith("postgresql://"):
                    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
                logging.info("Using database URL from settings")
                return db_url

            # Construct URL from individual components with psycopg2 driver
            if settings.db_password:
                password = settings.db_password.get_secret_value()
            else:
                password = "password"  # Default for development

            db_url = (
                f"postgresql+psycopg2://{settings.db_user}:{password}"
                f"@{settings.db_host}:{settings.db_port}/{settings.db_name}"
            )
            logging.info("Constructed database URL from settings components")
            return db_url

        except Exception as e:
            logging.warning("Could not load database URL from settings: %s", e)

    # Fallback to environment variables
    env_db_url = os.getenv("PROMPTCRAFT_DATABASE_URL")
    if env_db_url:
        # Ensure we use psycopg2 for synchronous connections in migrations
        if env_db_url.startswith("postgresql://"):
            env_db_url = env_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        logging.info("Using database URL from environment variable")
        return env_db_url

    # Final fallback to Alembic config (should be updated for production)
    config_url = config.get_main_option("sqlalchemy.url")
    if config_url and not config_url.startswith("driver://"):
        logging.info("Using database URL from alembic.ini")
        return config_url

    # Development fallback - use psycopg2 driver for synchronous connections
    dev_url = "postgresql+psycopg2://promptcraft_rw:password@192.168.1.16:5435/promptcraft_auth"
    logging.warning("Using development fallback database URL - NOT FOR PRODUCTION")
    return dev_url


def configure_migration_context(connection=None, url=None):
    """Configure the migration context with common settings.

    Args:
        connection: Database connection for online mode
        url: Database URL for offline mode
    """
    # Configuration options for migration context
    context_config = {
        "target_metadata": target_metadata,
        "compare_type": True,  # Detect column type changes
        "compare_server_default": True,  # Detect default value changes
        "include_object": include_object,  # Custom inclusion rules
        "render_as_batch": True,  # Support for SQLite and other limitations
    }

    if connection:
        context_config["connection"] = connection
    else:
        context_config["url"] = url
        context_config["literal_binds"] = True
        context_config["dialect_opts"] = {"paramstyle": "named"}

    context.configure(**context_config)


def include_object(object, name, type_, reflected, compare_to):
    """Determine whether to include an object in migration autogeneration.

    This function allows fine-grained control over what database objects
    are included in migrations.

    Args:
        object: The schema object (table, column, index, etc.)
        name: The name of the object
        type_: The type of the object
        reflected: Whether the object was reflected from the database
        compare_to: The corresponding object being compared to

    Returns:
        True if the object should be included in migrations
    """
    # Skip temp tables and system tables
    if type_ == "table" and (name.startswith("temp_") or name.startswith("tmp_") or name.startswith("alembic_")):
        return False

    # Include all PromptCraft tables
    if type_ == "table" and any(
        prefix in name
        for prefix in [
            "roles",
            "permissions",
            "service_tokens",
            "user_sessions",
            "authentication_events",
            "security_events",
            "blocked_entities",
            "threat_scores",
            "monitoring_thresholds",
        ]
    ):
        return True

    # Default: include everything else
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = get_database_url()
    logging.info("Running migrations in offline mode")

    configure_migration_context(url=url)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get database URL from our settings system
    database_url = get_database_url()

    # Create engine configuration
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = database_url

    # Additional engine configuration for production safety
    configuration.setdefault("sqlalchemy.pool_pre_ping", "true")
    configuration.setdefault("sqlalchemy.pool_recycle", "3600")
    configuration.setdefault("sqlalchemy.echo", "false")

    # Create the engine
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Use NullPool for migrations to avoid connection issues
    )

    logging.info("Running migrations in online mode")

    with connectable.connect() as connection:
        configure_migration_context(connection=connection)

        with context.begin_transaction():
            context.run_migrations()


# Migration execution
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
