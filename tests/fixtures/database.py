"""
Database fixtures for test isolation using PostgreSQL containers or SQLite fallback.

This module provides:
- Session-scoped PostgreSQL container management (when Docker available)
- SQLite fallback for environments without Docker
- Function-scoped transaction isolation  
- Automatic schema migration from SQL files
- Clean database state between tests
"""

from collections.abc import AsyncGenerator, Generator
import logging
from pathlib import Path
import time

import asyncpg
import pytest
from sqlalchemy import JSON, String
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.database.models import Base
from tests.fixtures.docker_utils import log_database_strategy, should_use_postgresql


logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def use_postgresql() -> bool:
    """Check if PostgreSQL containers should be used for testing."""
    return should_use_postgresql()


@pytest.fixture(scope="session")
def postgres_container(use_postgresql: bool) -> Generator[object | None, None, None]:
    """
    Session-scoped PostgreSQL container fixture (only if PostgreSQL is supported).
    
    Provides a clean PostgreSQL instance for the entire test session.
    Returns None if PostgreSQL is not supported.
    """
    if use_postgresql:
        try:
            from testcontainers.postgres import PostgresContainer
            with PostgresContainer("postgres:15-alpine") as postgres:
                # Wait for container to be ready
                time.sleep(2)
                log_database_strategy(use_postgres=True)
                yield postgres
        except Exception as e:
            logger.warning(f"Failed to start PostgreSQL container: {e}")
            log_database_strategy(use_postgres=False)
            yield None
    else:
        log_database_strategy(use_postgres=False)
        yield None


@pytest.fixture(scope="session")
def database_url(postgres_container: object | None, use_postgresql: bool) -> str:
    """
    Get the database connection URL (PostgreSQL container or SQLite fallback).
    
    Args:
        postgres_container: PostgreSQL container instance (None if unavailable)
        use_postgresql: Whether PostgreSQL should be used
        
    Returns:
        Database connection URL
    """
    if use_postgresql and postgres_container is not None:
        # Use PostgreSQL container with asyncpg
        original_url = postgres_container.get_connection_url()
        # Handle both postgresql:// and postgresql+psycopg2:// URLs
        if "+psycopg2" in original_url:
            asyncpg_url = original_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        else:
            asyncpg_url = original_url.replace("postgresql://", "postgresql+asyncpg://")
        logger.info(f"Converted PostgreSQL URL: {original_url} -> {asyncpg_url}")
        return asyncpg_url
    # Use SQLite fallback
    return "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def test_engine(database_url: str):
    """
    Create SQLAlchemy async engine for the test database.
    
    Args:
        database_url: Database connection URL (PostgreSQL or SQLite)
        
    Returns:
        Configured SQLAlchemy async engine
    """
    if database_url.startswith("postgresql"):
        # PostgreSQL configuration
        engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
            pool_recycle=300,
        )
    else:
        # SQLite configuration
        engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
        )
    
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def setup_database_schema(postgres_container: object | None, test_engine, database_url: str) -> None:
    """
    Apply database schema to the test database (PostgreSQL or SQLite).
    
    This fixture runs once per session and applies all schema:
    - PostgreSQL: Uses SQL schema files directly
    - SQLite: Creates SQLAlchemy tables with type compatibility fixes
    
    Args:
        postgres_container: PostgreSQL container instance (None if unavailable)
        test_engine: SQLAlchemy async engine
        database_url: Database connection URL
    """
    if database_url.startswith("postgresql") and postgres_container is not None:
        # PostgreSQL container schema setup
        from tests.fixtures.schema_loader import SchemaLoader
        
        # Get project root directory
        project_root = Path(__file__).parent.parent.parent
        
        # Create schema loader
        schema_loader = SchemaLoader(project_root)
        
        # Connect directly to PostgreSQL to apply schemas
        conn_params = {
            "host": postgres_container.get_container_host_ip(),
            "port": postgres_container.get_exposed_port(5432),
            "database": postgres_container.dbname,
            "user": postgres_container.username,
            "password": postgres_container.password,
        }
        
        conn = await asyncpg.connect(**conn_params)
        try:
            # Apply schemas using the loader (with validation and fixes)
            applied_schemas = await schema_loader.apply_schemas(conn)
            logger.info(f"Applied {len(applied_schemas)} PostgreSQL schema files")
            
            # Also create SQLAlchemy tables for auth models
            async with test_engine.begin() as conn_sa:
                await conn_sa.run_sync(Base.metadata.create_all)
                logger.info("Created SQLAlchemy auth tables in PostgreSQL")
                
        finally:
            await conn.close()
    else:
        # SQLite fallback schema setup
        logger.info("Setting up SQLite schema with type compatibility fixes")
        
        # Apply PostgreSQL-to-SQLite type compatibility fixes
        async with test_engine.begin() as conn:
            # Store original column types and temporarily replace with SQLite-compatible types
            original_types = {}
            for table in Base.metadata.tables.values():
                for column in table.columns:
                    type_name = column.type.__class__.__name__
                    if type_name == "JSONB":
                        original_types[(table.name, column.name)] = column.type
                        column.type = JSON()
                    elif type_name == "INET":
                        original_types[(table.name, column.name)] = column.type
                        column.type = String(45)  # IPv6 max length is 45 chars

            try:
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Created SQLAlchemy auth tables in SQLite")
            finally:
                # Restore original types after table creation
                for table in Base.metadata.tables.values():
                    for column in table.columns:
                        key = (table.name, column.name)
                        if key in original_types:
                            column.type = original_types[key]


@pytest.fixture(scope="function")
async def test_db_session(test_engine, setup_database_schema) -> AsyncGenerator[AsyncSession, None]:
    """
    Function-scoped database session with transaction isolation.
    
    Each test gets a clean database session wrapped in a transaction.
    The transaction is rolled back after the test completes, ensuring
    no data leaks between tests.
    
    Args:
        test_engine: SQLAlchemy async engine
        setup_database_schema: Ensures schema is applied
        
    Yields:
        Clean AsyncSession for the test
    """
    # Create session factory
    async_session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session_factory() as session:
        # Begin transaction
        trans = await session.begin()
        try:
            yield session
        finally:
            # Always rollback to ensure clean state
            try:
                await trans.rollback()
            except Exception as e:
                # Transaction may already be closed, log and continue
                logger.debug(f"Transaction already closed during rollback: {e}")


@pytest.fixture(scope="function")
async def override_get_db(test_db_session: AsyncSession):
    """
    Override the get_db dependency to use test database session.
    
    This fixture allows tests to use the same database session
    that will be rolled back after the test completes.
    
    Args:
        test_db_session: Test database session
        
    Returns:
        Function that yields the test database session
    """
    async def _get_test_db():
        yield test_db_session
    
    return _get_test_db


@pytest.fixture(scope="function")  
async def test_db_with_override(test_db_session: AsyncSession, override_get_db):
    """
    Convenience fixture that provides both session and override function.
    
    This is useful for tests that need both direct database access
    and dependency injection override.
    
    Args:
        test_db_session: Test database session
        override_get_db: Database dependency override function
        
    Returns:
        Tuple of (session, override_function)
    """
    return test_db_session, override_get_db


@pytest.fixture(scope="function")
async def clean_database_session(test_db_session: AsyncSession) -> AsyncSession:
    """
    Alias for test_db_session with clearer naming.
    
    Use this fixture when you want to emphasize that the database
    session is clean and isolated.
    
    Args:
        test_db_session: Test database session
        
    Returns:
        Clean, isolated database session
    """
    return test_db_session
