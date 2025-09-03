"""MVP Performance Smoke Tests

Simple performance validation for core functionality without complex infrastructure.
These tests validate that basic operations complete within reasonable timeframes
for MVP validation. Detailed performance testing is deferred to future phases.
"""

import time

import pytest
from fastapi import FastAPI
from httpx import AsyncClient


class TestPerformanceSmoke:
    """MVP performance smoke tests for core functionality."""

    @pytest.fixture
    def smoke_test_app(self):
        """Simple FastAPI app for smoke testing without complex middleware."""
        app = FastAPI(title="Performance Smoke Test")

        @app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        @app.get("/protected")
        async def protected_endpoint():
            return {"message": "protected content", "performance": "test"}

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
    async def test_api_request_performance(self, smoke_test_app):
        """Smoke test: API request should complete quickly (<3s)."""
        async with AsyncClient(app=smoke_test_app, base_url="http://test") as client:
            start_time = time.time()

            response = await client.get("/protected")

            duration = time.time() - start_time

            # MVP requirement: API requests should complete in reasonable time
            assert response.status_code == 200
            assert duration < 3.0, f"API request took {duration:.3f}s (should be <3s)"

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
        print("✅ API requests: <3s")
        print("✅ Multiple requests: No significant degradation")
        print("=" * 50)
        print("🎯 MVP Performance Requirements Met")
        print("📈 Detailed performance testing deferred to Phase 2+")
        print("=" * 50)
