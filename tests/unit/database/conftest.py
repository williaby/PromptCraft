"""Test fixtures for database unit tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.config.settings import ApplicationSettings


@pytest.fixture
def mock_settings():
    """Mock application settings for testing."""
    settings = MagicMock(spec=ApplicationSettings)
    settings.db_host = "localhost"
    settings.db_port = 5432
    settings.db_name = "test_db"
    settings.db_user = "test_user"
    settings.db_password = "test_password"
    settings.db_pool_size = 5
    settings.db_pool_max_overflow = 10
    settings.db_pool_timeout = 30
    settings.db_pool_recycle = 3600
    settings.db_echo = False
    settings.environment = "test"
    return settings


@pytest.fixture
def mock_async_engine():
    """Mock async database engine."""
    engine = AsyncMock(spec=AsyncEngine)

    # Mock connection context manager
    mock_conn = AsyncMock()
    mock_result = MagicMock()
    mock_result.fetchone.return_value = [1]
    mock_conn.execute.return_value = mock_result
    mock_conn.commit = AsyncMock()

    # Create proper async context manager for connect()
    mock_connection_context = AsyncMock()
    mock_connection_context.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_connection_context.__aexit__ = AsyncMock(return_value=None)
    engine.connect.return_value = mock_connection_context

    # Also support begin() for legacy compatibility
    mock_begin_context = AsyncMock()
    mock_begin_context.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_begin_context.__aexit__ = AsyncMock(return_value=None)
    engine.begin.return_value = mock_begin_context

    # Mock pool
    mock_pool = MagicMock()
    mock_pool.size.return_value = 5
    mock_pool.checkedin.return_value = 3
    mock_pool.checkedout.return_value = 2
    mock_pool.overflow.return_value = 0
    engine.pool = mock_pool

    # Mock dispose
    engine.dispose = AsyncMock()

    return engine


@pytest.fixture
def mock_session_factory():
    """Mock session factory."""
    factory = MagicMock(spec=async_sessionmaker)
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock session operations
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.add = AsyncMock()

    # Create an async context manager mock
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    # Make the factory return the context manager when called
    factory.return_value = mock_context_manager

    return factory


@pytest.fixture
def mock_async_session():
    """Mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.add = AsyncMock()
    return session
