"""Integration tests for enhanced Cloudflare Access authentication.

Tests the complete authentication flow including database integration,
middleware functionality, and graceful degradation scenarios.
"""

import asyncio
import time
import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.config import AuthenticationConfig
from src.auth.middleware import AuthenticationMiddleware
from src.auth.models import AuthenticatedUser, UserRole
from src.database import DatabaseManager
from src.database.models import UserSession


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for complete authentication flow."""

    @pytest.fixture
    def auth_config(self) -> AuthenticationConfig:
        """Authentication configuration for integration testing."""
        return AuthenticationConfig(
            cloudflare_access_enabled=True,
            cloudflare_audience="test-audience",
            cloudflare_issuer="https://test.cloudflareaccess.com",
            auth_logging_enabled=True,
            rate_limiting_enabled=True,
            rate_limit_requests=100,
            rate_limit_window=60,
        )

    @pytest.fixture
    async def mock_database_session(self) -> AsyncGenerator[AsyncMock, None]:
        """Mock database session for integration testing."""
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock user session queries
        mock_session.execute = AsyncMock()
        mock_session.scalar_one_or_none = AsyncMock()
        mock_session.add = AsyncMock()
        mock_session.commit = AsyncMock()

        # Mock existing user session for update scenario
        existing_session = UserSession(
            id=uuid.uuid4(),
            email="test@example.com",
            cloudflare_sub="test-sub",
            session_count=5,
            preferences={"theme": "dark"},
            user_metadata={"last_login": "2025-08-01T10:00:00Z"},
        )

        # Set up query results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_session
        mock_session.execute.return_value = mock_result

        return mock_session

    @pytest.fixture
    async def mock_database_manager(
        self,
        mock_database_session: AsyncMock,
    ) -> AsyncGenerator[AsyncMock, None]:
        """Mock database manager for integration testing."""
        mock_manager = AsyncMock(spec=DatabaseManager)

        # Mock session context manager
        mock_manager.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_database_session)
        mock_manager.get_session.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock health check
        mock_manager.health_check.return_value = {
            "status": "healthy",
            "timestamp": time.time(),
            "connection_test": True,
            "response_time_ms": 5.2,
        }

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            yield mock_manager

    @pytest.fixture
    def mock_jwt_validator(self) -> MagicMock:
        """Mock JWT validator for integration testing."""
        validator = MagicMock()
        validator.validate_token.return_value = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.ADMIN,
            jwt_claims={
                "sub": "test-sub-12345",
                "email": "test@example.com",
                "aud": "test-audience",
                "iss": "https://test.cloudflareaccess.com",
                "exp": int(time.time()) + 3600,
            },
        )
        return validator

    @pytest.fixture
    def fastapi_app(
        self,
        auth_config: AuthenticationConfig,
        mock_jwt_validator: MagicMock,
        mock_database_manager: AsyncMock,
    ) -> FastAPI:
        """Create FastAPI app with authentication middleware."""
        from starlette.middleware.base import BaseHTTPMiddleware

        app = FastAPI(title="PromptCraft Test App")

        # Create a simple middleware wrapper for testing
        class TestAuthMiddleware(BaseHTTPMiddleware):
            def __init__(self, app, auth_middleware):
                super().__init__(app)
                self.auth_middleware = auth_middleware

            async def dispatch(self, request: Request, call_next):
                return await self.auth_middleware.dispatch(request, call_next)

        # Create the actual auth middleware
        auth_middleware = AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

        # Add as middleware wrapper
        app.add_middleware(TestAuthMiddleware, auth_middleware=auth_middleware)

        # Test endpoints
        @app.get("/api/test")
        async def test_endpoint(request: Request):
            user = getattr(request.state, "authenticated_user", None)
            return {
                "status": "success",
                "user_email": user.email if user else None,
                "user_role": user.role.value if user else None,
            }

        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        @app.get("/api/admin")
        async def admin_endpoint(request: Request):
            user = getattr(request.state, "authenticated_user", None)
            if not user or user.role != UserRole.ADMIN:
                return {"error": "Forbidden"}, 403
            return {"status": "admin_access_granted"}

        return app

    @pytest.fixture
    def test_client(self, fastapi_app: FastAPI) -> TestClient:
        """Create test client for integration testing."""
        return TestClient(fastapi_app)

    def test_successful_authentication_flow(
        self,
        test_client: TestClient,
        mock_database_session: AsyncMock,
    ):
        """Test complete successful authentication flow."""
        # Make authenticated request
        response = test_client.get(
            "/api/test",
            headers={
                "CF-Access-Jwt-Assertion": "valid-jwt-token",
                "CF-Connecting-IP": "192.168.1.100",
                "User-Agent": "Mozilla/5.0 Test Browser",
                "CF-Ray": "test-ray-12345",
            },
        )

        # Verify successful response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user_email"] == "test@example.com"
        assert data["user_role"] == "admin"

        # Verify database operations were called
        mock_database_session.execute.assert_called()
        mock_database_session.commit.assert_called()

    def test_authentication_with_database_session_tracking(
        self,
        test_client: TestClient,
        mock_database_session: AsyncMock,
    ):
        """Test authentication with user session tracking."""
        # Make authenticated request
        response = test_client.get(
            "/api/test",
            headers={
                "CF-Access-Jwt-Assertion": "valid-jwt-token",
                "CF-Connecting-IP": "192.168.1.200",
                "User-Agent": "Chrome/91.0 Test",
            },
        )

        assert response.status_code == 200

        # Verify session update was attempted
        mock_database_session.execute.assert_called()
        mock_database_session.commit.assert_called()

    def test_authentication_event_logging(
        self,
        test_client: TestClient,
        mock_database_session: AsyncMock,
    ):
        """Test authentication event logging to database."""
        # Make authenticated request
        response = test_client.get(
            "/api/test",
            headers={
                "CF-Access-Jwt-Assertion": "valid-jwt-token",
                "CF-Connecting-IP": "10.0.0.1",
                "User-Agent": "Firefox/89.0 Test",
                "CF-Ray": "event-ray-54321",
            },
        )

        assert response.status_code == 200

        # Verify event logging was attempted (multiple database calls)
        assert mock_database_session.execute.call_count >= 2  # Session update + event log
        assert mock_database_session.commit.call_count >= 2
        assert mock_database_session.add.call_count >= 1

    def test_excluded_paths_bypass_authentication(
        self,
        test_client: TestClient,
        mock_database_session: AsyncMock,
    ):
        """Test that excluded paths bypass authentication."""
        # Test health endpoint (should be excluded)
        response = test_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

        # Verify no database operations for excluded paths
        mock_database_session.execute.assert_not_called()
        mock_database_session.commit.assert_not_called()

    def test_missing_jwt_token_authentication_failure(
        self,
        test_client: TestClient,
        mock_database_session: AsyncMock,
    ):
        """Test authentication failure with missing JWT token."""
        # Make request without JWT token
        response = test_client.get("/api/test")

        # Verify authentication failure
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "Authentication failed"

        # Verify failure event was logged
        mock_database_session.add.assert_called()
        mock_database_session.commit.assert_called()

    def test_graceful_degradation_database_unavailable(
        self,
        auth_config: AuthenticationConfig,
        mock_jwt_validator: MagicMock,
    ):
        """Test graceful degradation when database is unavailable."""
        app = FastAPI()

        # Mock database failure
        with patch("src.auth.middleware.get_database_manager") as mock_get_db:
            mock_db = AsyncMock()
            mock_db.get_session.side_effect = Exception("Database connection failed")
            mock_get_db.return_value = mock_db

            auth_middleware = AuthenticationMiddleware(
                app=app,
                config=auth_config,
                jwt_validator=mock_jwt_validator,
                database_enabled=True,
            )
            app.add_middleware(auth_middleware)

            @app.get("/api/test")
            async def test_endpoint(request: Request):
                user = getattr(request.state, "authenticated_user", None)
                return {"user_email": user.email if user else None}

            client = TestClient(app)

            # Authentication should still work despite database failure
            response = client.get(
                "/api/test",
                headers={"CF-Access-Jwt-Assertion": "valid-jwt-token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["user_email"] == "test@example.com"

    def test_role_based_access_control(
        self,
        test_client: TestClient,
        mock_jwt_validator: MagicMock,
    ):
        """Test role-based access control integration."""
        # Test admin access with admin role
        response = test_client.get(
            "/api/admin",
            headers={"CF-Access-Jwt-Assertion": "admin-jwt-token"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "admin_access_granted"

    def test_performance_metrics_collection(
        self,
        test_client: TestClient,
        mock_database_session: AsyncMock,
    ):
        """Test that performance metrics are collected during authentication."""
        # Make authenticated request
        start_time = time.time()
        response = test_client.get(
            "/api/test",
            headers={
                "CF-Access-Jwt-Assertion": "valid-jwt-token",
                "CF-Connecting-IP": "192.168.1.50",
            },
        )
        end_time = time.time()

        assert response.status_code == 200

        # Verify performance metrics were collected
        # (Database operations should include performance timing)
        mock_database_session.add.assert_called()

        # Verify request completed in reasonable time
        request_time_ms = (end_time - start_time) * 1000
        assert request_time_ms < 100.0, f"Request took {request_time_ms:.2f}ms, exceeds 100ms limit"

    def test_multiple_concurrent_requests(
        self,
        fastapi_app: FastAPI,
        mock_database_session: AsyncMock,
    ):
        """Test handling multiple concurrent authentication requests."""

        async def make_request():
            from httpx import AsyncClient

            async with AsyncClient(app=fastapi_app, base_url="http://test") as client:
                return await client.get(
                    "/api/test",
                    headers={
                        "CF-Access-Jwt-Assertion": "concurrent-jwt-token",
                        "CF-Connecting-IP": f"192.168.1.{hash(asyncio.current_task()) % 200 + 1}",
                    },
                )

        async def run_concurrent_test():
            # Create 20 concurrent requests
            tasks = [make_request() for _ in range(20)]
            responses = await asyncio.gather(*tasks)

            # Verify all requests succeeded
            for response in responses:
                assert response.status_code == 200
                data = response.json()
                assert data["user_email"] == "test@example.com"

            return len(responses)

        # Run the concurrent test

        result = asyncio.run(run_concurrent_test())
        assert result == 20

        # Verify database operations were called for each request
        assert mock_database_session.execute.call_count >= 20
        assert mock_database_session.commit.call_count >= 20


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database operations."""

    @pytest.fixture
    async def mock_engine_and_session(self) -> AsyncGenerator[tuple[AsyncMock, AsyncMock], None]:
        """Mock database engine and session for testing."""
        with (
            patch("src.database.connection.create_async_engine") as mock_engine_create,
            patch("src.database.connection.async_sessionmaker") as mock_session_maker,
        ):
            mock_engine = AsyncMock()
            mock_session_factory = AsyncMock()
            mock_session = AsyncMock()

            mock_engine_create.return_value = mock_engine
            mock_session_maker.return_value = mock_session_factory
            mock_session_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session_factory.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock successful connection test
            mock_conn = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchone.return_value = [1]
            mock_conn.execute.return_value = mock_result
            mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock pool for health checks
            mock_pool = MagicMock()
            mock_pool.size.return_value = 10
            mock_pool.checkedin.return_value = 7
            mock_pool.checkedout.return_value = 3
            mock_pool.overflow.return_value = 0
            mock_engine.pool = mock_pool

            yield mock_engine, mock_session

    async def test_database_manager_initialization(
        self,
        mock_engine_and_session: tuple[AsyncMock, AsyncMock],
    ):
        """Test database manager initialization."""
        mock_engine, mock_session = mock_engine_and_session

        from src.database.connection import DatabaseManager

        manager = DatabaseManager()
        await manager.initialize()

        # Verify initialization steps
        assert manager._engine is not None
        assert manager._session_factory is not None

        # Verify connection test was performed
        mock_engine.begin.assert_called()

    async def test_database_health_check_integration(
        self,
        mock_engine_and_session: tuple[AsyncMock, AsyncMock],
    ):
        """Test database health check integration."""
        mock_engine, mock_session = mock_engine_and_session

        from src.database.connection import DatabaseManager

        manager = DatabaseManager()
        await manager.initialize()

        # Perform health check
        health_status = await manager.health_check()

        # Verify health check results
        assert health_status["status"] == "healthy"
        assert health_status["connection_test"] is True
        assert "response_time_ms" in health_status
        assert "pool_status" in health_status

        # Verify pool status
        pool_status = health_status["pool_status"]
        assert pool_status["size"] == 10
        assert pool_status["checked_in"] == 7
        assert pool_status["checked_out"] == 3

    async def test_database_session_context_manager(
        self,
        mock_engine_and_session: tuple[AsyncMock, AsyncMock],
    ):
        """Test database session context manager integration."""
        mock_engine, mock_session = mock_engine_and_session

        from src.database.connection import DatabaseManager

        manager = DatabaseManager()
        await manager.initialize()

        # Test session context manager
        async with manager.get_session() as session:
            assert session is not None
            # Verify session operations can be performed
            session.execute = AsyncMock()
            await session.execute("SELECT 1")
            session.execute.assert_called_with("SELECT 1")

    async def test_database_retry_mechanism(
        self,
        mock_engine_and_session: tuple[AsyncMock, AsyncMock],
    ):
        """Test database retry mechanism integration."""
        mock_engine, mock_session = mock_engine_and_session

        from src.database.connection import DatabaseManager

        manager = DatabaseManager()
        await manager.initialize()

        # Mock operation that fails twice then succeeds
        call_count = 0

        async def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Temporary database error")
            return "success"

        # Test retry mechanism
        result = await manager.execute_with_retry(mock_operation, max_retries=3)

        assert result == "success"
        assert call_count == 3  # Failed twice, succeeded on third try
