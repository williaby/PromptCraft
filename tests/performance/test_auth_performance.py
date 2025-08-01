"""Performance tests for enhanced Cloudflare Access authentication.

Tests authentication middleware performance against the <75ms requirement.
Validates database integration performance and graceful degradation.
"""

import asyncio
import statistics
import time
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.config import AuthenticationConfig
from src.auth.middleware import AuthenticationMiddleware
from src.auth.models import AuthenticatedUser, UserRole
from src.database import DatabaseManager, get_database_manager


@pytest.mark.performance
class TestAuthenticationPerformance:
    """Performance tests for authentication middleware."""

    @pytest.fixture
    async def mock_database_manager(self) -> AsyncGenerator[AsyncMock, None]:
        """Mock database manager for performance testing."""
        mock_manager = AsyncMock(spec=DatabaseManager)
        mock_session = AsyncMock(spec=AsyncSession)

        # Mock session context manager
        async def mock_get_session():
            yield mock_session

        mock_manager.get_session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_manager.get_session.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock database operations to be fast
        mock_session.execute = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.scalar_one_or_none = AsyncMock(return_value=None)
        mock_session.add = AsyncMock()

        with patch("src.auth.middleware.get_database_manager", return_value=mock_manager):
            yield mock_manager

    @pytest.fixture
    def auth_config(self) -> AuthenticationConfig:
        """Authentication configuration for testing."""
        return AuthenticationConfig(
            cloudflare_access_enabled=True,
            cloudflare_audience="test-audience",
            cloudflare_issuer="https://test.cloudflareaccess.com",
            auth_logging_enabled=True,
            rate_limiting_enabled=False,  # Disable for performance testing
        )

    @pytest.fixture
    def mock_jwt_validator(self) -> MagicMock:
        """Mock JWT validator for performance testing."""
        validator = MagicMock()
        validator.validate_token.return_value = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub", "email": "test@example.com"},
        )
        return validator

    @pytest.fixture
    def auth_middleware(
        self,
        auth_config: AuthenticationConfig,
        mock_jwt_validator: MagicMock,
        mock_database_manager: AsyncMock,
    ) -> AuthenticationMiddleware:
        """Create authentication middleware for testing."""
        app = FastAPI()
        return AuthenticationMiddleware(
            app=app,
            config=auth_config,
            jwt_validator=mock_jwt_validator,
            database_enabled=True,
        )

    @pytest.fixture
    def mock_request(self) -> Request:
        """Create mock request for testing."""
        request = MagicMock(spec=Request)
        request.url.path = "/api/test"
        request.method = "GET"
        request.headers = {
            "CF-Access-Jwt-Assertion": "mock-jwt-token",
            "CF-Connecting-IP": "192.168.1.100",
            "User-Agent": "Mozilla/5.0 Test Browser",
            "CF-Ray": "test-ray-id-12345",
        }
        request.state = MagicMock()
        return request

    async def test_jwt_validation_performance(
        self,
        auth_middleware: AuthenticationMiddleware,
        mock_request: Request,
    ):
        """Test JWT validation performance meets <75ms requirement."""
        # Warm up
        for _ in range(5):
            await auth_middleware._authenticate_request(mock_request)

        # Performance test
        times = []
        for _ in range(100):
            start_time = time.perf_counter()
            await auth_middleware._authenticate_request(mock_request)
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to milliseconds

        # Performance assertions
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        max_time = max(times)

        print("JWT Validation Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")

        # Requirements validation
        assert avg_time < 10.0, f"Average JWT validation time {avg_time:.2f}ms exceeds 10ms target"
        assert p95_time < 25.0, f"95th percentile JWT validation time {p95_time:.2f}ms exceeds 25ms target"
        assert max_time < 50.0, f"Maximum JWT validation time {max_time:.2f}ms exceeds 50ms target"

    async def test_database_session_update_performance(
        self,
        auth_middleware: AuthenticationMiddleware,
        mock_request: Request,
    ):
        """Test database session update performance."""
        authenticated_user = AuthenticatedUser(
            email="test@example.com",
            role=UserRole.USER,
            jwt_claims={"sub": "test-sub", "email": "test@example.com"},
        )

        # Warm up
        for _ in range(5):
            await auth_middleware._update_user_session(authenticated_user, mock_request)

        # Performance test
        times = []
        for _ in range(50):
            start_time = time.perf_counter()
            await auth_middleware._update_user_session(authenticated_user, mock_request)
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to milliseconds

        # Performance assertions
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        max_time = max(times)

        print("Database Session Update Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")

        # Requirements validation
        assert avg_time < 15.0, f"Average DB session update time {avg_time:.2f}ms exceeds 15ms target"
        assert p95_time < 30.0, f"95th percentile DB session update time {p95_time:.2f}ms exceeds 30ms target"

    async def test_end_to_end_authentication_performance(
        self,
        auth_middleware: AuthenticationMiddleware,
        mock_request: Request,
    ):
        """Test complete authentication flow performance against <75ms requirement."""

        async def mock_call_next(request: Request):
            return JSONResponse(content={"status": "success"})

        # Warm up
        for _ in range(10):
            await auth_middleware.dispatch(mock_request, mock_call_next)

        # Performance test
        times = []
        for _ in range(100):
            start_time = time.perf_counter()
            response = await auth_middleware.dispatch(mock_request, mock_call_next)
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)  # Convert to milliseconds

            # Verify successful response
            assert response.status_code == 200

        # Performance assertions
        avg_time = statistics.mean(times)
        p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
        max_time = max(times)

        print("End-to-End Authentication Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  95th percentile: {p95_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")

        # Critical requirement: <75ms performance target
        assert avg_time < 30.0, f"Average authentication time {avg_time:.2f}ms exceeds 30ms target"
        assert p95_time < 75.0, f"95th percentile authentication time {p95_time:.2f}ms exceeds 75ms requirement"
        assert max_time < 150.0, f"Maximum authentication time {max_time:.2f}ms exceeds 150ms limit"

    async def test_concurrent_authentication_performance(
        self,
        auth_middleware: AuthenticationMiddleware,
        mock_request: Request,
    ):
        """Test authentication performance under concurrent load."""

        async def mock_call_next(request: Request):
            return JSONResponse(content={"status": "success"})

        # Create multiple requests
        requests = [mock_request for _ in range(50)]

        # Warm up
        tasks = [auth_middleware.dispatch(req, mock_call_next) for req in requests[:5]]
        await asyncio.gather(*tasks)

        # Performance test with concurrent requests
        start_time = time.perf_counter()
        tasks = [auth_middleware.dispatch(req, mock_call_next) for req in requests]
        responses = await asyncio.gather(*tasks)
        end_time = time.perf_counter()

        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        avg_time_per_request = total_time / len(requests)
        requests_per_second = len(requests) / (total_time / 1000)

        print("Concurrent Authentication Performance:")
        print(f"  Total time for {len(requests)} requests: {total_time:.2f}ms")
        print(f"  Average time per request: {avg_time_per_request:.2f}ms")
        print(f"  Requests per second: {requests_per_second:.1f}")

        # Verify all responses were successful
        for response in responses:
            assert response.status_code == 200

        # Performance assertions
        assert (
            avg_time_per_request < 50.0
        ), f"Average concurrent request time {avg_time_per_request:.2f}ms exceeds 50ms target"
        assert requests_per_second > 20.0, f"Requests per second {requests_per_second:.1f} below 20 target"

    async def test_database_graceful_degradation_performance(
        self,
        auth_config: AuthenticationConfig,
        mock_jwt_validator: MagicMock,
        mock_request: Request,
    ):
        """Test performance when database is unavailable (graceful degradation)."""
        # Create middleware with failing database
        app = FastAPI()

        with patch("src.auth.middleware.get_database_manager") as mock_get_db:
            # Mock database failure
            mock_db = AsyncMock()
            mock_db.get_session.side_effect = Exception("Database unavailable")
            mock_get_db.return_value = mock_db

            auth_middleware = AuthenticationMiddleware(
                app=app,
                config=auth_config,
                jwt_validator=mock_jwt_validator,
                database_enabled=True,
            )

            async def mock_call_next(request: Request):
                return JSONResponse(content={"status": "success"})

            # Performance test with database failures
            times = []
            for _ in range(50):
                start_time = time.perf_counter()
                response = await auth_middleware.dispatch(mock_request, mock_call_next)
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)

                # Authentication should still succeed despite database failure
                assert response.status_code == 200

            # Performance assertions - should still be fast without database
            avg_time = statistics.mean(times)
            p95_time = statistics.quantiles(times, n=20)[18]

            print("Graceful Degradation Performance (DB Unavailable):")
            print(f"  Average: {avg_time:.2f}ms")
            print(f"  95th percentile: {p95_time:.2f}ms")

            # Should be even faster without database operations
            assert avg_time < 20.0, f"Average degraded performance {avg_time:.2f}ms exceeds 20ms target"
            assert p95_time < 40.0, f"95th percentile degraded performance {p95_time:.2f}ms exceeds 40ms target"


@pytest.mark.performance
class TestDatabasePerformance:
    """Performance tests for database operations."""

    @pytest.fixture
    async def mock_database_manager(self) -> AsyncGenerator[DatabaseManager, None]:
        """Mock database manager for testing."""
        with (
            patch("src.database.connection.create_async_engine") as mock_engine_create,
            patch("src.database.connection.async_sessionmaker") as mock_session_maker,
        ):
            # Mock engine and session factory
            mock_engine = AsyncMock()
            mock_session_factory = AsyncMock()

            mock_engine_create.return_value = mock_engine
            mock_session_maker.return_value = mock_session_factory

            # Mock successful connection test
            mock_conn = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchone.return_value = [1]
            mock_conn.execute.return_value = mock_result
            mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)

            # Mock pool status
            mock_pool = MagicMock()
            mock_pool.size.return_value = 5
            mock_pool.checkedin.return_value = 3
            mock_pool.checkedout.return_value = 2
            mock_pool.overflow.return_value = 0
            mock_engine.pool = mock_pool

            manager = DatabaseManager()
            await manager.initialize()

            yield manager

    async def test_database_initialization_performance(self):
        """Test database initialization performance."""
        with (
            patch("src.database.connection.create_async_engine") as mock_engine_create,
            patch("src.database.connection.async_sessionmaker") as mock_session_maker,
        ):
            # Mock fast initialization
            mock_engine = AsyncMock()
            mock_session_factory = AsyncMock()

            mock_engine_create.return_value = mock_engine
            mock_session_maker.return_value = mock_session_factory

            # Mock connection test
            mock_conn = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchone.return_value = [1]
            mock_conn.execute.return_value = mock_result
            mock_engine.begin.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
            mock_engine.begin.return_value.__aexit__ = AsyncMock(return_value=None)

            # Performance test
            times = []
            for _ in range(10):
                start_time = time.perf_counter()
                manager = DatabaseManager()
                await manager.initialize()
                end_time = time.perf_counter()
                times.append((end_time - start_time) * 1000)
                await manager.close()

            avg_time = statistics.mean(times)
            max_time = max(times)

            print("Database Initialization Performance:")
            print(f"  Average: {avg_time:.2f}ms")
            print(f"  Maximum: {max_time:.2f}ms")

            # Should initialize quickly
            assert avg_time < 50.0, f"Average initialization time {avg_time:.2f}ms exceeds 50ms target"
            assert max_time < 100.0, f"Maximum initialization time {max_time:.2f}ms exceeds 100ms target"

    async def test_health_check_performance(
        self,
        mock_database_manager: DatabaseManager,
    ):
        """Test database health check performance."""
        # Performance test
        times = []
        for _ in range(20):
            start_time = time.perf_counter()
            health_status = await mock_database_manager.health_check()
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)

            # Verify health check returns expected data
            assert "status" in health_status
            assert "response_time_ms" in health_status

        avg_time = statistics.mean(times)
        max_time = max(times)

        print("Database Health Check Performance:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Maximum: {max_time:.2f}ms")

        # Health checks should be very fast
        assert avg_time < 5.0, f"Average health check time {avg_time:.2f}ms exceeds 5ms target"
        assert max_time < 20.0, f"Maximum health check time {max_time:.2f}ms exceeds 20ms target"
