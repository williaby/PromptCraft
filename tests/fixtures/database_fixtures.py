"""Comprehensive database fixtures for dependency injection testing.

This module provides database fixtures that support proper dependency injection
patterns for testing services that depend on database connections.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.config.settings import ApplicationSettings
from src.database.connection import DatabaseManager


@pytest.fixture
def mock_database_settings():
    """Mock application settings for database testing."""
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
def mock_database_engine():
    """Mock async database engine with proper context manager support."""
    engine = AsyncMock(spec=AsyncEngine)

    # Mock connection and result objects
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

    # Mock pool with metrics support
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
def mock_database_session_factory():
    """Mock session factory with proper async session support."""
    factory = MagicMock(spec=async_sessionmaker)
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock session operations
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.add = AsyncMock()
    mock_session.delete = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Create an async context manager mock
    mock_context_manager = MagicMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)

    # Make the factory return the context manager when called
    factory.return_value = mock_context_manager

    return factory


@pytest.fixture
def mock_database_session():
    """Mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.add = AsyncMock()
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_database_manager(mock_database_settings, mock_database_engine, mock_database_session_factory):
    """Mock database manager with dependency injection support."""
    manager = MagicMock(spec=DatabaseManager)

    # Configure the manager with mocked components
    manager._engine = mock_database_engine
    manager._session_factory = mock_database_session_factory
    manager._settings = mock_database_settings
    manager._is_initialized = True

    # Mock methods
    manager.initialize = AsyncMock()
    manager.close = AsyncMock()
    manager.health_check = AsyncMock(
        return_value={
            "status": "healthy",
            "engine_initialized": True,
            "connection_test": True,
            "response_time_ms": 5.0,
            "pool_status": {"metrics_available": True},
        },
    )

    # Mock get_session as async context manager
    async def mock_get_session():
        session = mock_database_session()
        try:
            yield session
        finally:
            await session.close()

    manager.get_session.return_value = mock_get_session()

    return manager


@pytest.fixture
def database_manager_factory():
    """Factory fixture for creating database managers with custom dependencies."""

    def create_manager(settings=None, engine=None, session_factory=None):
        """Create a database manager with optional custom dependencies."""
        manager = DatabaseManager()

        if settings:
            manager._settings = settings
        if engine:
            manager._engine = engine
        if session_factory:
            manager._session_factory = session_factory

        return manager

    return create_manager


@pytest.fixture
def mock_database_dependency_injection():
    """Fixture for testing services that use database dependency injection."""

    class MockDatabaseService:
        """Mock service that demonstrates dependency injection pattern."""

        def __init__(self, database_manager: DatabaseManager = None):
            self.database_manager = database_manager or DatabaseManager()

        async def get_data(self):
            """Example method that uses database."""
            async with self.database_manager.get_session() as session:
                result = await session.execute("SELECT 1")
                return result.fetchone()

    return MockDatabaseService


@pytest.fixture
def isolated_database_config():
    """Provide isolated database configuration for testing."""
    with (
        patch.dict("os.environ", {}, clear=True),
        patch("src.config.settings._env_file_settings", return_value={}),
    ):
        yield


@pytest.fixture
async def database_integration_test_manager():
    """Provide a database manager for integration testing with real async operations."""
    # This would be used for integration tests that need actual database connections
    # For unit tests, use the mock fixtures above

    class IntegrationDatabaseManager:
        """Wrapper for testing database integration scenarios."""

        def __init__(self):
            self.manager = None
            self._initialized = False

        async def initialize(self, settings=None):
            """Initialize with custom settings for testing."""
            if settings:
                with patch("src.database.connection.get_settings", return_value=settings):
                    self.manager = DatabaseManager()
                    await self.manager.initialize()
            else:
                self.manager = DatabaseManager()
                await self.manager.initialize()

            self._initialized = True

        async def cleanup(self):
            """Clean up resources."""
            if self.manager and self._initialized:
                await self.manager.close()
                self._initialized = False

    integration_manager = IntegrationDatabaseManager()
    yield integration_manager
    await integration_manager.cleanup()


# Export the fixtures for easy importing
__all__ = [
    "database_integration_test_manager",
    "database_manager_factory",
    "isolated_database_config",
    "mock_database_dependency_injection",
    "mock_database_engine",
    "mock_database_manager",
    "mock_database_session",
    "mock_database_session_factory",
    "mock_database_settings",
]
