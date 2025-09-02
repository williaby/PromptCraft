"""Database fixtures for integration testing.

Provides real database connections and fixtures for testing without mocking.
Uses in-memory SQLite for performance and isolation.
"""

from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import JSON, String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )

    # Create all tables - patch PostgreSQL types to SQLite-compatible types
    async with engine.begin() as conn:
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
            await conn.run_sync(Base.metadata.create_all)
        finally:
            # Restore original types after table creation
            for table in Base.metadata.tables.values():
                for column in table.columns:
                    key = (table.name, column.name)
                    if key in original_types:
                        column.type = original_types[key]

    yield engine

    # Cleanup
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide database session with automatic rollback for test isolation."""
    async_session = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Use nested transaction that we can roll back
        transaction = await session.begin()

        try:
            yield session
        finally:
            # Always rollback to maintain test isolation, but only if transaction is still active
            try:
                if transaction.is_active:
                    await transaction.rollback()
            except Exception:
                # If rollback fails, transaction might already be closed - that's okay
                pass


@pytest_asyncio.fixture(scope="function")
async def test_db_with_override(test_db_session):
    """Database session that overrides the global get_db dependency."""

    async def mock_get_db():
        yield test_db_session

    # Patch the get_db function globally
    with patch("src.database.connection.get_db", mock_get_db):
        yield test_db_session


@pytest.fixture
def sync_test_engine():
    """Synchronous SQLite engine for tests that need sync operations."""
    engine = create_engine("sqlite:///:memory:", echo=False)

    # Create all tables synchronously
    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
def sync_test_session(sync_test_engine):
    """Synchronous database session for legacy tests."""
    Session = sessionmaker(bind=sync_test_engine)
    session = Session()

    try:
        yield session
    finally:
        session.rollback()
        session.close()
