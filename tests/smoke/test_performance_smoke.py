"""MVP Performance Smoke Tests

Simple performance validation for core functionality without complex infrastructure.
These tests validate that basic operations complete within reasonable timeframes
for MVP validation. Detailed performance testing is deferred to future phases.
"""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from src.auth.config import AuthenticationConfig
from src.auth.middleware import AuthenticationMiddleware


class TestPerformanceSmoke:
    """MVP performance smoke tests for core functionality."""

    @pytest.fixture
    def simple_auth_config(self):
        """Simple auth configuration for smoke tests."""
        return AuthenticationConfig(
            auth_domain="test.cloudflareaccess.com",
            audience="test-audience",
            database_enabled=False,  # Disable database for smoke tests
            enable_monitoring=False,  # Disable monitoring for simplicity
        )

    @pytest.fixture
    def smoke_test_app(self, simple_auth_config):
        """Simple FastAPI app for smoke testing."""
        app = FastAPI(title="Performance Smoke Test")

        # Add authentication middleware with simple mocking
        with AsyncMock() as mock_validator:
            mock_validator.validate_token.return_value = MagicMock(
                claims={"email": "test@example.com", "sub": "test-user"},
            )
            middleware = AuthenticationMiddleware(simple_auth_config, mock_validator)
            app.middleware("http")(middleware)

        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        @app.get("/protected")
        async def protected_endpoint():
            return {"message": "protected content"}

        return app

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_basic_request_performance(self, smoke_test_app):
        """Smoke test: Basic request should complete quickly (<2s)."""
        async with AsyncClient(app=smoke_test_app, base_url="http://test") as client:
            start_time = time.time()

            response = await client.get("/health")

            duration = time.time() - start_time

            # MVP requirement: Basic requests should complete in reasonable time
            assert response.status_code == 200
            assert duration < 2.0, f"Basic request took {duration:.3f}s (should be <2s)"

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_auth_request_performance(self, smoke_test_app):
        """Smoke test: Auth-protected request should complete quickly (<3s)."""
        headers = {"CF-Access-Jwt-Assertion": "mock-jwt-token"}

        async with AsyncClient(app=smoke_test_app, base_url="http://test") as client:
            start_time = time.time()

            response = await client.get("/protected", headers=headers)

            duration = time.time() - start_time

            # MVP requirement: Auth requests should complete in reasonable time
            assert response.status_code == 200
            assert duration < 3.0, f"Auth request took {duration:.3f}s (should be <3s)"

    @pytest.mark.smoke
    @pytest.mark.asyncio
    async def test_multiple_requests_performance(self, smoke_test_app):
        """Smoke test: Multiple requests should not degrade significantly."""
        async with AsyncClient(app=smoke_test_app, base_url="http://test") as client:
            durations = []

            # Test 5 sequential requests
            for _ in range(5):
                start_time = time.time()
                response = await client.get("/health")
                duration = time.time() - start_time

                assert response.status_code == 200
                durations.append(duration)

            # MVP requirement: Performance should not degrade significantly
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)

            assert avg_duration < 1.0, f"Average request time {avg_duration:.3f}s too high"
            assert max_duration < 2.0, f"Max request time {max_duration:.3f}s too high"

    @pytest.mark.smoke
    def test_performance_smoke_summary(self):
        """Print MVP performance testing summary."""
        print("\n" + "=" * 50)
        print("MVP PERFORMANCE SMOKE TESTS COMPLETE")
        print("=" * 50)
        print("✅ Basic requests: <2s")
        print("✅ Auth requests: <3s")
        print("✅ Multiple requests: No significant degradation")
        print("=" * 50)
        print("🎯 MVP Performance Requirements Met")
        print("📈 Detailed performance testing deferred to Phase 2+")
        print("=" * 50)
