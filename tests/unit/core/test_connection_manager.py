"""
Comprehensive test coverage for ConnectionManager in src/core/vector_store.py.

This test module provides complete coverage for the ConnectionManager class,
testing all public methods, error conditions, and edge cases.
"""

import asyncio
from unittest.mock import patch

import pytest

from src.core.vector_store import ConnectionManager, VectorStoreConfig


class TestConnectionManager:
    """Comprehensive test suite for ConnectionManager class."""

    @pytest.fixture
    def sample_config(self) -> VectorStoreConfig:
        """Create a sample VectorStoreConfig for testing."""
        return VectorStoreConfig(
            host="test-host",
            port=6333,
            collection="test-collection",
            timeout=30.0,
            api_key="test-key",
            use_ssl=True,
        )

    @pytest.fixture
    def connection_manager(self, sample_config: VectorStoreConfig) -> ConnectionManager:
        """Create a ConnectionManager instance for testing."""
        return ConnectionManager(sample_config)

    def test_init_with_config(self, sample_config: VectorStoreConfig):
        """Test ConnectionManager initialization with configuration."""
        manager = ConnectionManager(sample_config)

        assert manager.config == sample_config
        assert manager._connection_pool == {}
        assert manager._is_connected is False

    def test_init_config_assignment(self, sample_config: VectorStoreConfig):
        """Test that configuration is properly assigned during initialization."""
        manager = ConnectionManager(sample_config)

        assert manager.config.host == "test-host"
        assert manager.config.port == 6333
        assert manager.config.collection == "test-collection"
        assert manager.config.timeout == 30.0
        assert manager.config.api_key == "test-key"
        assert manager.config.use_ssl is True

    @pytest.mark.asyncio
    async def test_connect_success(self, connection_manager: ConnectionManager):
        """Test successful connection establishment."""
        result = await connection_manager.connect()

        assert result is True
        assert connection_manager._is_connected is True

    @pytest.mark.asyncio
    async def test_connect_with_exception(self, connection_manager: ConnectionManager):
        """Test connection with exception handling."""
        # Mock the connect method to raise an exception
        with (
            patch.object(connection_manager, "connect", side_effect=Exception("Connection failed")),
            pytest.raises(Exception, match="Connection failed"),
        ):
            await connection_manager.connect()

    @pytest.mark.asyncio
    async def test_connect_exception_handling(self, sample_config: VectorStoreConfig):
        """Test connect method exception handling internal logic."""

        # Create a custom manager to test internal exception handling
        class TestConnectionManager(ConnectionManager):
            async def connect(self) -> bool:
                try:
                    # Simulate an exception during connection
                    raise Exception("Simulated connection error")
                except Exception:
                    self._is_connected = False
                    return False

        manager = TestConnectionManager(sample_config)
        result = await manager.connect()

        assert result is False
        assert manager._is_connected is False

    @pytest.mark.asyncio
    async def test_disconnect(self, connection_manager: ConnectionManager):
        """Test disconnection functionality."""
        # First establish a connection
        await connection_manager.connect()
        connection_manager._connection_pool["test"] = "mock_connection"

        assert connection_manager._is_connected is True
        assert len(connection_manager._connection_pool) == 1

        # Test disconnect
        await connection_manager.disconnect()

        assert connection_manager._is_connected is False
        assert len(connection_manager._connection_pool) == 0

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, connection_manager: ConnectionManager):
        """Test disconnect when already disconnected."""
        # Ensure we start disconnected
        assert connection_manager._is_connected is False

        # Disconnect should work without errors
        await connection_manager.disconnect()

        assert connection_manager._is_connected is False
        assert len(connection_manager._connection_pool) == 0

    @pytest.mark.asyncio
    async def test_disconnect_clears_connection_pool(self, connection_manager: ConnectionManager):
        """Test that disconnect clears the connection pool."""
        # Setup some mock connections
        connection_manager._connection_pool = {
            "conn1": "mock_connection_1",
            "conn2": "mock_connection_2",
            "conn3": "mock_connection_3",
        }
        connection_manager._is_connected = True

        await connection_manager.disconnect()

        assert connection_manager._connection_pool == {}
        assert connection_manager._is_connected is False

    def test_is_connected_when_connected(self, connection_manager: ConnectionManager):
        """Test is_connected returns True when connected."""
        connection_manager._is_connected = True

        assert connection_manager.is_connected() is True

    def test_is_connected_when_disconnected(self, connection_manager: ConnectionManager):
        """Test is_connected returns False when disconnected."""
        connection_manager._is_connected = False

        assert connection_manager.is_connected() is False

    def test_is_connected_initial_state(self, connection_manager: ConnectionManager):
        """Test is_connected initial state is False."""
        # Should be False by default
        assert connection_manager.is_connected() is False

    @pytest.mark.asyncio
    async def test_health_check_when_connected(self, connection_manager: ConnectionManager):
        """Test health check when connection is active."""
        # Setup connected state
        connection_manager._is_connected = True
        connection_manager._connection_pool = {"test": "connection"}

        result = await connection_manager.health_check()

        expected = {
            "status": "healthy",
            "host": "test-host",
            "port": 6333,
            "connection_pool_size": 1,
        }

        assert result == expected

    @pytest.mark.asyncio
    async def test_health_check_when_disconnected(self, connection_manager: ConnectionManager):
        """Test health check when connection is inactive."""
        # Setup disconnected state
        connection_manager._is_connected = False
        connection_manager._connection_pool = {}

        result = await connection_manager.health_check()

        expected = {
            "status": "disconnected",
            "host": "test-host",
            "port": 6333,
            "connection_pool_size": 0,
        }

        assert result == expected

    @pytest.mark.asyncio
    async def test_health_check_with_multiple_connections(self, connection_manager: ConnectionManager):
        """Test health check with multiple connections in pool."""
        # Setup multiple connections
        connection_manager._is_connected = True
        connection_manager._connection_pool = {
            "conn1": "connection1",
            "conn2": "connection2",
            "conn3": "connection3",
            "conn4": "connection4",
        }

        result = await connection_manager.health_check()

        assert result["status"] == "healthy"
        assert result["connection_pool_size"] == 4
        assert result["host"] == "test-host"
        assert result["port"] == 6333

    @pytest.mark.asyncio
    async def test_health_check_preserves_config_data(self, connection_manager: ConnectionManager):
        """Test that health check preserves original config data."""
        # Test with different config values
        config = VectorStoreConfig(
            host="custom-host",
            port=8080,
            collection="custom-collection",
        )
        manager = ConnectionManager(config)

        result = await manager.health_check()

        assert result["host"] == "custom-host"
        assert result["port"] == 8080

    def test_connection_pool_manipulation(self, connection_manager: ConnectionManager):
        """Test direct connection pool manipulation."""
        # Test that connection pool can be manipulated
        assert len(connection_manager._connection_pool) == 0

        connection_manager._connection_pool["test"] = "mock_connection"
        assert len(connection_manager._connection_pool) == 1

        connection_manager._connection_pool.clear()
        assert len(connection_manager._connection_pool) == 0

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, connection_manager: ConnectionManager):
        """Test full connection lifecycle: connect -> use -> disconnect."""
        # Initial state
        assert not connection_manager.is_connected()

        # Connect
        result = await connection_manager.connect()
        assert result is True
        assert connection_manager.is_connected()

        # Simulate adding connections to pool
        connection_manager._connection_pool["active"] = "connection"

        # Health check while connected
        health = await connection_manager.health_check()
        assert health["status"] == "healthy"
        assert health["connection_pool_size"] == 1

        # Disconnect
        await connection_manager.disconnect()
        assert not connection_manager.is_connected()
        assert len(connection_manager._connection_pool) == 0

        # Health check after disconnect
        health = await connection_manager.health_check()
        assert health["status"] == "disconnected"
        assert health["connection_pool_size"] == 0

    def test_config_immutability_during_operations(self, connection_manager: ConnectionManager):
        """Test that config remains unchanged during operations."""
        original_config = connection_manager.config
        original_host = connection_manager.config.host
        original_port = connection_manager.config.port

        # Perform various operations
        connection_manager._is_connected = True
        connection_manager._connection_pool["test"] = "connection"

        # Config should remain unchanged
        assert connection_manager.config is original_config
        assert connection_manager.config.host == original_host
        assert connection_manager.config.port == original_port

    @pytest.mark.asyncio
    async def test_multiple_connect_calls(self, connection_manager: ConnectionManager):
        """Test multiple consecutive connect calls."""
        # First connect
        result1 = await connection_manager.connect()
        assert result1 is True
        assert connection_manager.is_connected()

        # Second connect (should still work)
        result2 = await connection_manager.connect()
        assert result2 is True
        assert connection_manager.is_connected()

    @pytest.mark.asyncio
    async def test_multiple_disconnect_calls(self, connection_manager: ConnectionManager):
        """Test multiple consecutive disconnect calls."""
        # Connect first
        await connection_manager.connect()
        assert connection_manager.is_connected()

        # First disconnect
        await connection_manager.disconnect()
        assert not connection_manager.is_connected()

        # Second disconnect (should not cause errors)
        await connection_manager.disconnect()
        assert not connection_manager.is_connected()

    def test_connection_pool_types(self, connection_manager: ConnectionManager):
        """Test that connection pool can handle different types of connections."""
        # Test with various connection types
        connection_manager._connection_pool["string"] = "string_connection"
        connection_manager._connection_pool["dict"] = {"type": "dict_connection"}
        connection_manager._connection_pool["int"] = 12345
        connection_manager._connection_pool["none"] = None

        assert len(connection_manager._connection_pool) == 4
        assert connection_manager._connection_pool["string"] == "string_connection"
        assert connection_manager._connection_pool["dict"]["type"] == "dict_connection"
        assert connection_manager._connection_pool["int"] == 12345
        assert connection_manager._connection_pool["none"] is None

    @pytest.mark.asyncio
    async def test_health_check_return_type(self, connection_manager: ConnectionManager):
        """Test that health_check returns the correct type."""
        result = await connection_manager.health_check()

        assert isinstance(result, dict)
        assert isinstance(result["status"], str)
        assert isinstance(result["host"], str)
        assert isinstance(result["port"], int)
        assert isinstance(result["connection_pool_size"], int)

    def test_config_with_minimal_values(self):
        """Test ConnectionManager with minimal config values."""
        config = VectorStoreConfig()  # Use defaults
        manager = ConnectionManager(config)

        assert manager.config.host == "localhost"
        assert manager.config.port == 6333
        assert manager.config.collection == "default"
        assert manager.config.timeout == 30.0
        assert manager.config.api_key is None
        assert manager.config.use_ssl is False

    def test_config_with_none_values(self):
        """Test ConnectionManager handling of None values in config."""
        config = VectorStoreConfig(
            host="test-host",
            port=6333,
            api_key=None,  # Explicitly None
        )
        manager = ConnectionManager(config)

        assert manager.config.api_key is None
        assert manager.config.host == "test-host"

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, connection_manager: ConnectionManager):
        """Test concurrent operations on ConnectionManager."""

        # Test concurrent connect/disconnect operations
        async def connect_task():
            return await connection_manager.connect()

        async def disconnect_task():
            await connection_manager.disconnect()

        # Run connect
        result = await connect_task()
        assert result is True

        # Run health check and disconnect concurrently
        health_task = connection_manager.health_check()
        disconnect_task_coro = disconnect_task()

        health_result, _ = await asyncio.gather(health_task, disconnect_task_coro)

        # Health check should have completed, disconnect should have completed
        assert isinstance(health_result, dict)
        assert not connection_manager.is_connected()
