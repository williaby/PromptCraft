"""Base classes for integration testing.

Provides base test classes with real FastAPI apps and database connections.
"""

from .integration_test_base import (
    AuthenticatedIntegrationTestBase,
    DatabaseIntegrationTestBase,
    FullIntegrationTestBase,
    IntegrationTestBase,
    ServiceTokenIntegrationTestBase,
    assert_error_response,
    assert_successful_response,
    wait_for_database_operation,
)


__all__ = [
    "AuthenticatedIntegrationTestBase",
    "DatabaseIntegrationTestBase",
    "FullIntegrationTestBase",
    "IntegrationTestBase",
    "ServiceTokenIntegrationTestBase",
    "assert_error_response",
    "assert_successful_response",
    "wait_for_database_operation",
]
