"""Async PostgreSQL database connection management for PromptCraft.

This module provides async database connection management with:
- Connection pooling for optimal performance
- Proper session lifecycle management
- Configuration-based connection parameters
- Health checks and monitoring
- Configuration management from environment variables
- Performance monitoring and optimization
"""

import asyncio
import logging
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class DatabaseError(Exception):
    """Base exception for database operations."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize database error.

        Args:
            message: Error message
            original_error: Original exception if available
        """
        super().__init__(message)
        self.original_error = original_error


class DatabaseConnectionError(DatabaseError):
    """Exception for database connection failures."""


class DatabaseManager:
    """Manages async PostgreSQL database connections and sessions."""

    def __init__(self) -> None:
        """Initialize database manager with configuration."""
        self.settings = get_settings()
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._is_initialized = False
        self._connection_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        async with self._connection_lock:
            if self._engine is not None:
                logger.warning("Database already initialized")
                return

            try:
                # Build database URL
                db_url = await self._build_database_url()

                # Create async engine with connection pooling
                self._engine = create_async_engine(
                    db_url,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    pool_recycle=3600,  # 1 hour
                    echo=False,  # Set to True for SQL debugging
                )

                # Create session factory
                self._session_factory = async_sessionmaker(
                    bind=self._engine,
                    class_=AsyncSession,
                    expire_on_commit=False,
                )

                self._is_initialized = True
                logger.info("Database connection initialized")

            except Exception as e:
                logger.error("Failed to initialize database: %s", e)
                raise DatabaseConnectionError("Database initialization failed") from e

    async def _build_database_url(self) -> str:
        """Build database URL from configuration."""
        # Use database_url if provided
        if hasattr(self.settings, 'database_url') and self.settings.database_url:
            return self.settings.database_url.get_secret_value()

        # Build URL from components
        host = getattr(self.settings, "db_host", "192.168.1.16")
        port = getattr(self.settings, "db_port", 5432)
        database = getattr(self.settings, "db_name", "promptcraft")
        username = getattr(self.settings, "db_user", "promptcraft_app")

        password = ""
        if hasattr(self.settings, 'database_password') and self.settings.database_password:
            password = self.settings.database_password.get_secret_value()

        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._is_initialized = False
            logger.info("Database connections closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper lifecycle management."""
        if not self._session_factory:
            await self.initialize()

        if not self._session_factory:
            raise DatabaseConnectionError("Database session factory not available")

        async with self._session_factory() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error("Database session error, rolling back: %s", e)
                raise
            finally:
                await session.close()

    async def health_check(self) -> dict[str, Any]:
        """Perform database health check."""
        try:
            if not self._engine:
                return {"status": "unhealthy", "error": "Database not initialized"}

            async with self._engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                result.fetchone()

            return {
                "status": "healthy",
                "connection_pool": {
                    "size": self._engine.pool.size() if self._engine.pool else 0,
                    "checked_in": self._engine.pool.checkedin() if self._engine.pool else 0,
                    "checked_out": self._engine.pool.checkedout() if self._engine.pool else 0,
                },
            }
        except Exception as e:
            logger.error("Database health check failed: %s", e)
            return {"status": "unhealthy", "error": str(e)}


# Global database manager instance
_db_manager: DatabaseManager | None = None


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# Legacy compatibility functions
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (legacy compatibility)."""
    db_manager = get_database_manager()
    async with db_manager.get_session() as session:
        yield session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    db_manager = get_database_manager()
    async with db_manager.get_session() as session:
        yield session