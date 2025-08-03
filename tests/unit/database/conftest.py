"""Test fixtures for database tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from src.config.settings import ApplicationSettings


@pytest.fixture
def mock_settings():
    """Mock application settings for testing."""
    settings = MagicMock(spec=ApplicationSettings)
    settings.database_host = "localhost"
    settings.database_port = 5432
    settings.database_name = "test_db"
    settings.database_username = "test_user"
    settings.database_timeout = 30.0
    settings.database_password = None
    settings.database_url = None
    return settings


@pytest.fixture
def mock_async_engine():
    """Mock SQLAlchemy async engine."""
    engine = AsyncMock(spec=AsyncEngine)
    engine.connect = AsyncMock()
    engine.dispose = AsyncMock()

    # Mock pool
    mock_pool = MagicMock()
    mock_pool.size.return_value = 10
    mock_pool.checkedin.return_value = 8
    mock_pool.checkedout.return_value = 2
    mock_pool.overflow.return_value = 0
    mock_pool.invalidated.return_value = 0
    engine.pool = mock_pool

    return engine


@pytest.fixture
def mock_async_session():
    """Mock SQLAlchemy async session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_database_session():
    """Mock database session for testing."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session
