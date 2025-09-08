"""Comprehensive tests for src/database/base_service.py."""

from contextlib import asynccontextmanager, contextmanager
from unittest.mock import AsyncMock, Mock, patch

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.base_service import DatabaseService
from src.database.connection import DatabaseError


@contextmanager
def mock_sqlalchemy_select():
    """Helper context manager to mock SQLAlchemy select operations."""
    with patch("src.database.base_service.select") as mock_select:
        mock_query = Mock()
        mock_query.where.return_value = mock_query
        mock_select.return_value = mock_query
        yield mock_select, mock_query


class TestDatabaseService:
    """Comprehensive tests for DatabaseService class."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        manager = Mock()
        manager.get_session = AsyncMock()
        return manager

    @pytest.fixture
    def mock_session(self):
        """Create mock async session."""
        session = Mock(spec=AsyncSession)
        session.rollback = AsyncMock()
        session.commit = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def service(self, mock_db_manager):
        """Create DatabaseService instance with mocked dependencies."""
        with patch("src.database.base_service.get_database_manager", return_value=mock_db_manager):
            return DatabaseService()

    @pytest.mark.asyncio
    async def test_init(self):
        """Test DatabaseService initialization."""
        with patch("src.database.base_service.get_database_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager

            service = DatabaseService()

            mock_get_manager.assert_called_once()
            assert service._db_manager == mock_manager

    @pytest.mark.asyncio
    async def test_get_session_success(self, service, mock_session):
        """Test successful session context manager."""

        @asynccontextmanager
        async def mock_session_context():
            yield mock_session

        service._db_manager.get_session = mock_session_context

        async with service.get_session() as session:
            assert session == mock_session

    @pytest.mark.asyncio
    async def test_get_session_sqlalchemy_error(self, service, mock_session):
        """Test session context manager with SQLAlchemy error."""

        @asynccontextmanager
        async def mock_session_context():
            yield mock_session

        service._db_manager.get_session = mock_session_context

        with pytest.raises(DatabaseError, match="Database operation failed"):
            async with service.get_session() as session:
                raise SQLAlchemyError("Test SQL error")

        # Verify rollback was called
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_session_unexpected_error(self, service, mock_session):
        """Test session context manager with unexpected error."""

        @asynccontextmanager
        async def mock_session_context():
            yield mock_session

        service._db_manager.get_session = mock_session_context

        with pytest.raises(RuntimeError, match="Unexpected error"):
            async with service.get_session() as session:
                raise RuntimeError("Unexpected error")

        # Verify rollback was called
        mock_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_session_success(self, service, mock_session):
        """Test successful operation execution."""

        async def mock_operation(session, arg1, arg2, kwarg1=None):
            return f"result: {arg1}, {arg2}, {kwarg1}"

        with patch.object(service, "get_session") as mock_get_session:

            @asynccontextmanager
            async def session_context():
                yield mock_session

            mock_get_session.return_value = session_context()

            result = await service.execute_with_session(mock_operation, "value1", "value2", kwarg1="kwvalue")

            assert result == "result: value1, value2, kwvalue"

    @pytest.mark.asyncio
    async def test_execute_query_fetch_all(self, service, mock_session):
        """Test execute_query with fetch_all (default)."""
        mock_result = Mock()
        mock_result.fetchall.return_value = [("row1",), ("row2",)]
        mock_session.execute.return_value = mock_result

        with patch.object(service, "get_session") as mock_get_session:

            @asynccontextmanager
            async def session_context():
                yield mock_session

            mock_get_session.return_value = session_context()

            result = await service.execute_query("SELECT * FROM test", {"param": "value"})

            assert result == [("row1",), ("row2",)]
            mock_session.execute.assert_called_once()
            # Verify text() was called with the query
            call_args = mock_session.execute.call_args
            assert str(call_args[0][0]) == "SELECT * FROM test"
            assert call_args[0][1] == {"param": "value"}

    @pytest.mark.asyncio
    async def test_execute_query_fetch_one(self, service, mock_session):
        """Test execute_query with fetch_one=True."""
        mock_result = Mock()
        mock_result.fetchone.return_value = ("single_row",)
        mock_session.execute.return_value = mock_result

        with patch.object(service, "get_session") as mock_get_session:

            @asynccontextmanager
            async def session_context():
                yield mock_session

            mock_get_session.return_value = session_context()

            result = await service.execute_query("SELECT id FROM test", fetch_one=True)

            assert result == ("single_row",)
            mock_result.fetchone.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_fetch_scalar(self, service, mock_session):
        """Test execute_query with fetch_scalar=True."""
        mock_result = Mock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result

        with patch.object(service, "get_session") as mock_get_session:

            @asynccontextmanager
            async def session_context():
                yield mock_session

            mock_get_session.return_value = session_context()

            result = await service.execute_query("SELECT COUNT(*) FROM test", fetch_scalar=True)

            assert result == 42
            mock_result.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_no_parameters(self, service, mock_session):
        """Test execute_query without parameters."""
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        with patch.object(service, "get_session") as mock_get_session:

            @asynccontextmanager
            async def session_context():
                yield mock_session

            mock_get_session.return_value = session_context()

            result = await service.execute_query("SELECT * FROM empty_table")

            assert result == []
            # Verify empty dict was passed as parameters
            call_args = mock_session.execute.call_args
            assert call_args[0][1] == {}

    @pytest.mark.asyncio
    async def test_handle_integrity_error_unique_constraint(self, service):
        """Test handling unique constraint violation."""
        error = IntegrityError("statement", "params", "UNIQUE constraint failed")

        with pytest.raises(DatabaseError, match="User creation failed: User already exists"):
            await service.handle_integrity_error(error, "User creation", "User")

    @pytest.mark.asyncio
    async def test_handle_integrity_error_duplicate_key(self, service):
        """Test handling duplicate key error."""
        error = IntegrityError("statement", "params", "duplicate key value violates")

        with pytest.raises(DatabaseError, match="Operation failed: Duplicate entry"):
            await service.handle_integrity_error(error, "Operation")

    @pytest.mark.asyncio
    async def test_handle_integrity_error_foreign_key(self, service):
        """Test handling foreign key constraint violation."""
        error = IntegrityError("statement", "params", "FOREIGN KEY constraint failed")

        with pytest.raises(DatabaseError, match="Create relation failed: Referenced entity does not exist"):
            await service.handle_integrity_error(error, "Create relation", "Relation")

    @pytest.mark.asyncio
    async def test_handle_integrity_error_other(self, service):
        """Test handling other integrity errors."""
        error = IntegrityError("statement", "params", "CHECK constraint failed")

        with pytest.raises(DatabaseError, match="Test operation failed"):
            await service.handle_integrity_error(error, "Test operation")

    @pytest.mark.asyncio
    async def test_log_operation_success_full_info(self, service):
        """Test logging successful operation with all information."""
        with patch("src.database.base_service.logger") as mock_logger:
            await service.log_operation_success(
                "Create user",
                entity_id=123,
                entity_name="testuser",
                additional_info="with email verification",
            )

            mock_logger.info.assert_called_once_with(
                "%s%s%s%s",
                "Create user",
                " 'testuser'",
                " with ID 123",
                " - with email verification",
            )

    @pytest.mark.asyncio
    async def test_log_operation_success_minimal_info(self, service):
        """Test logging successful operation with minimal information."""
        with patch("src.database.base_service.logger") as mock_logger:
            await service.log_operation_success("Simple operation")

            mock_logger.info.assert_called_once_with("%s%s%s%s", "Simple operation", "", "", "")

    @pytest.mark.asyncio
    async def test_log_operation_error_with_entity(self, service):
        """Test logging operation error with entity name."""
        error = ValueError("Test error")

        with patch("src.database.base_service.logger") as mock_logger:
            await service.log_operation_error("Delete user", error, "testuser")

            mock_logger.error.assert_called_once_with("%s failed%s: %s", "Delete user", " for testuser", error)

    @pytest.mark.asyncio
    async def test_log_operation_error_without_entity(self, service):
        """Test logging operation error without entity name."""
        error = RuntimeError("Connection failed")

        with patch("src.database.base_service.logger") as mock_logger:
            await service.log_operation_error("Database connection", error)

            mock_logger.error.assert_called_once_with("%s failed%s: %s", "Database connection", "", error)

    @pytest.mark.asyncio
    async def test_check_entity_exists_true(self, service, mock_session):
        """Test check_entity_exists returns True when entity exists."""
        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = 123  # Non-None means exists
        mock_session.execute.return_value = mock_result

        # Mock SQLAlchemy select and where operations
        with patch("src.database.base_service.select") as mock_select:
            mock_query = Mock()
            mock_query.where.return_value = mock_query
            mock_select.return_value = mock_query

            # Mock model class
            mock_model = Mock()
            mock_model.id = Mock()
            mock_model.name = Mock()

            result = await service.check_entity_exists(mock_session, mock_model, {"name": "testuser"}, "User")

            assert result is True
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_entity_exists_false(self, service, mock_session):
        """Test check_entity_exists returns False when entity doesn't exist."""
        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None  # None means doesn't exist
        mock_session.execute.return_value = mock_result

        # Mock SQLAlchemy operations
        with patch("src.database.base_service.select") as mock_select:
            mock_query = Mock()
            mock_query.where.return_value = mock_query
            mock_select.return_value = mock_query

            mock_model = Mock()
            mock_model.id = Mock()
            mock_model.email = Mock()

            result = await service.check_entity_exists(mock_session, mock_model, {"email": "test@example.com"}, "User")

            assert result is False

    @pytest.mark.asyncio
    async def test_check_entity_exists_multiple_conditions(self, service, mock_session):
        """Test check_entity_exists with multiple filter conditions."""
        # Mock the query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = 456
        mock_session.execute.return_value = mock_result

        with mock_sqlalchemy_select():
            mock_model = Mock()
            mock_model.id = Mock()
            mock_model.name = Mock()
            mock_model.status = Mock()

            result = await service.check_entity_exists(
                mock_session,
                mock_model,
                {"name": "testuser", "status": "active"},
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_get_entity_by_conditions_found(self, service, mock_session):
        """Test get_entity_by_conditions when entity is found."""
        # Mock the entity and result
        mock_entity = {"id": 123, "username": "testuser"}
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute.return_value = mock_result

        with mock_sqlalchemy_select():
            mock_model = Mock()
            mock_model.username = Mock()

            result = await service.get_entity_by_conditions(mock_session, mock_model, {"username": "testuser"}, "User")

            assert result == mock_entity
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_entity_by_conditions_not_found(self, service, mock_session):
        """Test get_entity_by_conditions when entity is not found."""
        # Mock the result (no entity found)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with mock_sqlalchemy_select():
            mock_model = Mock()
            mock_model.id = Mock()

            result = await service.get_entity_by_conditions(mock_session, mock_model, {"id": 999}, "User")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_entity_by_conditions_multiple_filters(self, service, mock_session):
        """Test get_entity_by_conditions with multiple filter conditions."""
        # Mock the entity and result
        mock_entity = {"id": 789, "name": "test", "type": "admin", "active": True}
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute.return_value = mock_result

        with mock_sqlalchemy_select():
            mock_model = Mock()
            mock_model.name = Mock()
            mock_model.type = Mock()
            mock_model.active = Mock()

            result = await service.get_entity_by_conditions(
                mock_session,
                mock_model,
                {"name": "test", "type": "admin", "active": True},
            )

            assert result == mock_entity


class TestDatabaseServiceIntegration:
    """Integration-style tests for DatabaseService."""

    @pytest.fixture
    def service_with_real_manager(self):
        """Create service with real database manager (mocked at connection level)."""
        with patch("src.database.base_service.get_database_manager") as mock_get_manager:
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            return DatabaseService(), mock_manager

    @pytest.mark.asyncio
    async def test_full_operation_workflow(self):
        """Test complete workflow of database operation."""
        # Mock the database manager and session
        mock_manager = Mock()
        mock_session = Mock(spec=AsyncSession)
        mock_session.rollback = AsyncMock()
        mock_session.execute = AsyncMock()

        @asynccontextmanager
        async def mock_session_context():
            yield mock_session

        mock_manager.get_session = mock_session_context

        with patch("src.database.base_service.get_database_manager", return_value=mock_manager):
            service = DatabaseService()

            # Define a test operation
            async def test_operation(session, test_param):
                # Simulate database operation
                await session.execute("SELECT 1")
                return f"Success with {test_param}"

            # Execute the operation
            result = await service.execute_with_session(test_operation, "test_value")

            assert result == "Success with test_value"
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self):
        """Test error handling in complete workflow."""
        mock_manager = Mock()
        mock_session = Mock(spec=AsyncSession)
        mock_session.rollback = AsyncMock()

        @asynccontextmanager
        async def mock_session_context():
            yield mock_session

        mock_manager.get_session = mock_session_context

        with patch("src.database.base_service.get_database_manager", return_value=mock_manager):
            service = DatabaseService()

            # Define a failing operation
            async def failing_operation(session):
                raise IntegrityError("statement", "params", "UNIQUE constraint failed")

            # Test that the operation fails with proper error handling
            with pytest.raises(DatabaseError):
                async with service.get_session() as session:
                    await failing_operation(session)

            # Verify rollback was called
            mock_session.rollback.assert_called_once()


class TestDatabaseServiceLogging:
    """Tests focused on logging functionality."""

    @pytest.fixture
    def service(self):
        """Create service with mocked database manager for logging tests."""
        with patch("src.database.base_service.get_database_manager"):
            return DatabaseService()

    @pytest.mark.asyncio
    async def test_debug_logging_in_check_entity_exists(self, service):
        """Test debug logging in check_entity_exists method."""
        mock_session = Mock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = 123
        mock_session.execute.return_value = mock_result

        with mock_sqlalchemy_select():
            mock_model = Mock()
            mock_model.id = Mock()
            mock_model.name = Mock()

            with patch("src.database.base_service.logger") as mock_logger:
                await service.check_entity_exists(mock_session, mock_model, {"name": "test"}, "TestEntity")

                mock_logger.debug.assert_called_once_with("Entity existence check for %s: %s", "TestEntity", True)

    @pytest.mark.asyncio
    async def test_debug_logging_in_get_entity_found(self, service):
        """Test debug logging when entity is found."""
        mock_session = Mock(spec=AsyncSession)
        mock_entity = {"id": 123}
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_entity
        mock_session.execute.return_value = mock_result

        with mock_sqlalchemy_select():
            mock_model = Mock()
            mock_model.id = Mock()

            with patch("src.database.base_service.logger") as mock_logger:
                await service.get_entity_by_conditions(mock_session, mock_model, {"id": 123}, "TestEntity")

                mock_logger.debug.assert_called_with("Found %s with conditions %s", "TestEntity", {"id": 123})

    @pytest.mark.asyncio
    async def test_debug_logging_in_get_entity_not_found(self, service):
        """Test debug logging when entity is not found."""
        mock_session = Mock(spec=AsyncSession)
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with mock_sqlalchemy_select():
            mock_model = Mock()
            mock_model.id = Mock()

            with patch("src.database.base_service.logger") as mock_logger:
                await service.get_entity_by_conditions(mock_session, mock_model, {"id": 999}, "TestEntity")

                mock_logger.debug.assert_called_with("No %s found with conditions %s", "TestEntity", {"id": 999})
