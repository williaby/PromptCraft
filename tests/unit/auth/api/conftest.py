"""
Configuration and fixtures for AUTH-4 API router tests.

Automatically imports all API router fixtures and provides test configuration.
"""

# Import all fixtures from the central fixtures file
# This makes them available to all test files in this directory
import pytest
from tests.fixtures.api_router_fixtures import *  # noqa: F403

# =================== TEST CONFIGURATION ===================

# Configure pytest markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.api,
]


# =================== ADDITIONAL LOCAL FIXTURES ===================


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically set up test environment for all API router tests."""
    # This fixture runs automatically before each test
    # Can be used to set environment variables, initialize logging, etc.
    import os

    # Ensure test environment is properly configured
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Cleanup after test (if needed)


@pytest.fixture
def api_test_config():
    """Configuration for API router tests."""
    return {
        "max_response_time": 2.0,  # seconds
        "default_page_size": 10,
        "max_page_size": 100,
        "test_user_id": "test-user-123",
        "test_session_timeout": 300,  # seconds
    }
