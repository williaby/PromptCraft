"""Base classes for integration testing with real dependencies.

Provides FastAPI test client with real services and database connections.
"""

import asyncio
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest
import pytest_asyncio

from src.api.auth_endpoints import audit_router, auth_router, system_router
from src.auth.middleware import require_authentication, require_role


class IntegrationTestBase:
    """Base class for integration tests with real FastAPI app and services."""

    @pytest.fixture
    def test_app(self) -> FastAPI:
        """Create FastAPI app with real routers for testing."""
        app = FastAPI(
            title="Test PromptCraft API",
            version="0.1.0-test",
        )

        # Add real routers
        app.include_router(auth_router, prefix="/api/v1")
        app.include_router(system_router, prefix="/api/v1")
        app.include_router(audit_router, prefix="/api/v1")

        return app

    @pytest.fixture
    def test_client(self, test_app) -> TestClient:
        """Create test client with real FastAPI app."""
        return TestClient(test_app)

    @pytest_asyncio.fixture
    async def async_test_client(self, test_app) -> AsyncGenerator[AsyncClient, None]:
        """Create async test client for testing async endpoints."""
        async with AsyncClient(app=test_app, base_url="http://testserver") as client:
            yield client


class AuthenticatedIntegrationTestBase(IntegrationTestBase):
    """Integration test base with authentication setup."""

    @pytest.fixture
    def authenticated_app(self, test_app, admin_user):
        """FastAPI app with authentication that returns admin user."""

        # Override authentication to return test user
        def mock_auth():
            return admin_user

        def mock_admin_role(request):
            return admin_user

        test_app.dependency_overrides[require_authentication] = mock_auth
        test_app.dependency_overrides[require_role] = lambda request, role: admin_user

        yield test_app

        # Clean up overrides
        test_app.dependency_overrides.clear()

    @pytest.fixture
    def authenticated_client(self, authenticated_app):
        """Test client with admin authentication."""
        return TestClient(authenticated_app)


class ServiceTokenIntegrationTestBase(IntegrationTestBase):
    """Integration test base with service token authentication."""

    @pytest.fixture
    def service_token_app(self, test_app, test_service_user):
        """FastAPI app with service token authentication."""

        def mock_auth():
            return test_service_user

        test_app.dependency_overrides[require_authentication] = mock_auth

        yield test_app

        test_app.dependency_overrides.clear()

    @pytest.fixture
    def service_token_client(self, service_token_app):
        """Test client with service token authentication."""
        return TestClient(service_token_app)


class DatabaseIntegrationTestBase(IntegrationTestBase):
    """Integration test base with database operations."""

    @pytest_asyncio.fixture
    async def db_test_app(self, test_app, test_db_with_override):
        """FastAPI app with real database connection."""
        # Unpack the test database session and override function
        test_db_session, override_get_db = test_db_with_override

        # Apply the database dependency override to the FastAPI app
        from src.database.connection import get_db

        test_app.dependency_overrides[get_db] = override_get_db

        yield test_app

        # Clean up the override
        if get_db in test_app.dependency_overrides:
            del test_app.dependency_overrides[get_db]

    @pytest.fixture
    def db_test_client(self, db_test_app):
        """Test client with real database connection."""
        return TestClient(db_test_app)


class FullIntegrationTestBase(DatabaseIntegrationTestBase, AuthenticatedIntegrationTestBase):
    """Complete integration test base with database and authentication."""

    @pytest.fixture
    def full_integration_app(self, test_app, test_db_with_override, admin_user):
        """FastAPI app with database and authentication."""
        # Unpack the test database session and override function
        test_db_session, override_get_db = test_db_with_override

        def mock_auth():
            return admin_user

        def mock_admin_role(request):
            return admin_user

        # Apply all dependency overrides
        from src.database.connection import get_db

        test_app.dependency_overrides[get_db] = override_get_db
        test_app.dependency_overrides[require_authentication] = mock_auth
        test_app.dependency_overrides[require_role] = lambda request, role: admin_user

        yield test_app

        test_app.dependency_overrides.clear()

    @pytest.fixture
    def full_integration_client(self, full_integration_app):
        """Test client with database and authentication."""
        return TestClient(full_integration_app)


# Utility functions for common test patterns
def assert_successful_response(response, expected_status: int = 200):
    """Assert response is successful and return JSON data."""
    assert (
        response.status_code == expected_status
    ), f"Expected {expected_status}, got {response.status_code}: {response.text}"
    return response.json()


def assert_error_response(response, expected_status: int, expected_message: str | None = None):
    """Assert response is an error with optional message check."""
    assert response.status_code == expected_status
    if expected_message:
        data = response.json()
        assert expected_message in data.get("detail", "")


async def wait_for_database_operation(db_session, query, timeout: float = 5.0):
    """Wait for database operation to complete with timeout."""
    start_time = asyncio.get_event_loop().time()

    while True:
        result = await db_session.execute(query)
        if result.scalar_one_or_none() is not None:
            return result

        if asyncio.get_event_loop().time() - start_time > timeout:
            raise TimeoutError(f"Database operation timed out after {timeout}s")

        await asyncio.sleep(0.1)
