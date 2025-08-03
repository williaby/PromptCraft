"""Async PostgreSQL database connection management for PromptCraft.

This module provides async database connection management with:
- Connection pooling for performance
- Proper session lifecycle management
- Configuration-based connection parameters
- Health checks and monitoring
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


class DatabaseManager:
    """Manages async PostgreSQL database connections and sessions."""

    def __init__(self) -> None:
        """Initialize database manager with configuration."""
        self.settings = get_settings()
        self._engine = None
        self._session_factory = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._engine is not None:
            logger.warning("Database already initialized")
            return

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

    async def _build_database_url(self) -> str:
        """Build database URL from configuration."""
        # Use database_url if provided
        if self.settings.database_url:
            return self.settings.database_url.get_secret_value()

        # Build URL from components
        host = getattr(self.settings, "db_host", "192.168.1.16")
        port = getattr(self.settings, "db_port", 5432)
        database = getattr(self.settings, "db_name", "promptcraft")
        username = getattr(self.settings, "db_user", "promptcraft_app")

        password = ""
        if self.settings.database_password:
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

        async with self._session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def health_check(self) -> bool:
        """Check database connectivity and health."""
        try:
            async with self.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def get_pool_status(self) -> dict:
        """Get connection pool status."""
        if not self._is_initialized:
            return {"status": "not_initialized"}

        return {
            "status": "initialized",
            "pool_size": getattr(self._engine.pool, "size", 0) if self._engine else 0,
            "checked_in": getattr(self._engine.pool, "checkedin", 0) if self._engine else 0,
            "checked_out": getattr(self._engine.pool, "checkedout", 0) if self._engine else 0,
        }

    # Alias for compatibility with tests
    async def session(self):
        """Alias for get_session for test compatibility."""
        return self.get_session()


# Global database manager instance
_db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions.

    Yields:
        AsyncSession: Database session for request
    """
    async with _db_manager.get_session() as session:
        yield session


async def initialize_database() -> None:
    """Initialize database connections."""
    await _db_manager.initialize()


async def close_database() -> None:
    """Close database connections."""
    await _db_manager.close()


async def database_health_check() -> bool:
    """Check database health."""
    return await _db_manager.health_check()
