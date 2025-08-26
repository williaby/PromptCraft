"""Database fixtures for testing AUTH-4 security system.

This module provides comprehensive database fixtures and mocks for testing
the security event logging and monitoring system.
"""

import asyncio
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import SecurityEventCreate


class MockSecurityEventsDatabase:
    """Mock implementation of SecurityEventsDatabase for testing."""

    def __init__(self, db_path: str = ":memory:", **kwargs):
        """Initialize mock database."""
        self.db_path = db_path
        self.database_path = Path(db_path) if db_path != ":memory:" else None
        self.max_connections = kwargs.get("max_connections", 10)
        self.connection_timeout = kwargs.get("connection_timeout", 30.0)
        self.enable_wal = kwargs.get("enable_wal", True)
        self._events = []
        self._connection_pool = []
        self._is_initialized = False
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize database with schema."""
        self._is_initialized = True
        # Create mock schema
        self._events = []

    async def close(self) -> None:
        """Close database connections."""
        self._is_initialized = False
        self._events.clear()

    async def create_event(self, event) -> str:
        """Create a new security event."""
        event_id = str(uuid4())
        # Handle both SecurityEventCreate objects and dict inputs
        if hasattr(event, "dict"):
            event_data = event.dict()
        elif isinstance(event, dict):
            event_data = event
        else:
            # Fallback for other types
            event_data = event.__dict__ if hasattr(event, "__dict__") else {}

        self._events.append({"id": event_id, "timestamp": datetime.now(UTC), **event_data})
        return event_id

    async def get_event_by_id(self, event_id: str) -> dict[str, Any] | None:
        """Get event by ID."""
        for event in self._events:
            if event["id"] == event_id:
                return event
        return None

    async def get_events_by_user_id(self, user_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get events by user ID."""
        user_events = [e for e in self._events if e.get("user_id") == user_id]
        return user_events[:limit]

    async def get_events_by_type(self, event_type: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get events by type."""
        type_events = [e for e in self._events if e.get("event_type") == event_type]
        return type_events[:limit]

    async def get_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        """Get events by date range."""
        range_events = [e for e in self._events if start_date <= e["timestamp"] <= end_date]
        return range_events[:limit]

    async def cleanup_expired_events(self, days: int = 30) -> int:
        """Cleanup expired events."""
        cutoff = datetime.now(UTC) - timedelta(days=days)
        original_count = len(self._events)
        self._events = [e for e in self._events if e["timestamp"] > cutoff]
        return original_count - len(self._events)

    async def vacuum_database(self) -> None:
        """Vacuum database (no-op for mock)."""

    def get_connection(self):
        """Get database connection."""
        return MagicMock()

    async def execute_query(self, query: str, params: dict | None = None) -> Any:
        """Execute arbitrary query."""
        return []


class MockDatabaseManager:
    """Mock implementation of DatabaseManager for testing."""

    def __init__(self):
        """Initialize mock database manager."""
        self._engine = None
        self._session_factory = None
        self._is_initialized = False
        self._health_check_cache = {}

    async def initialize(self) -> None:
        """Initialize mock database."""
        self._is_initialized = True

    async def close(self) -> None:
        """Close mock database."""
        self._is_initialized = False

    async def get_session(self) -> AsyncSession:
        """Get mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock(return_value=MagicMock())
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        return session

    async def health_check(self) -> dict[str, Any]:
        """Perform health check."""
        return {
            "status": "healthy",
            "database": "mock",
            "connection_pool": {"size": 10, "checked_out": 0, "overflow": 0, "total": 10},
        }

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._is_initialized


@pytest.fixture
async def mock_security_database():
    """Provide a mock SecurityEventsDatabase for testing."""
    db = MockSecurityEventsDatabase(":memory:")
    await db.initialize()
    yield db
    await db.close()


@pytest.fixture
async def temp_security_database():
    """Provide a temporary file-based SecurityEventsDatabase for testing."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    db_path = temp_file.name
    temp_file.close()

    db = MockSecurityEventsDatabase(db_path)
    await db.initialize()

    yield db

    await db.close()
    if db.database_path and db.database_path.exists():
        db.database_path.unlink(missing_ok=True)


@pytest.fixture
async def mock_database_manager():
    """Provide a mock DatabaseManager for testing."""
    manager = MockDatabaseManager()
    await manager.initialize()
    yield manager
    await manager.close()


@pytest.fixture
def mock_database_session():
    """Provide a mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    session.add = Mock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_connection_pool():
    """Provide a mock connection pool."""
    pool = MagicMock()
    pool.size = 10
    pool.checked_out = 0
    pool.overflow = 0
    pool.total = 10
    pool.acquire = AsyncMock()
    pool.release = AsyncMock()
    return pool


@pytest.fixture
def sample_security_event():
    """Provide a sample SecurityEventCreate for testing."""
    return SecurityEventCreate(
        event_type="login_attempt",
        severity="medium",
        user_id="test-user-123",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser",
        details={"action": "login", "result": "success", "method": "password"},
    )


@pytest.fixture
def sample_security_events():
    """Provide multiple sample security events."""
    events = []
    for i in range(10):
        events.append(
            SecurityEventCreate(
                event_type="login_attempt" if i % 2 == 0 else "api_access",
                severity="low" if i < 3 else "medium" if i < 7 else "high",
                user_id=f"user-{i % 3}",
                ip_address=f"192.168.1.{100 + i}",
                user_agent="Test Browser",
                details={"action": f"action-{i}", "index": i},
            ),
        )
    return events


@pytest.fixture
async def populated_security_database(mock_security_database, sample_security_events):
    """Provide a pre-populated security database."""
    for event in sample_security_events:
        await mock_security_database.create_event(event)
    return mock_security_database
