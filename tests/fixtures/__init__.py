"""Test fixtures package for PromptCraft testing infrastructure with dependency injection support."""

# API router fixtures removed as part of auth simplification
# Note: service_container_fixtures temporarily disabled due to missing auth.database module
# from .service_container_fixtures import (
#     ContainerTestHelper,
#     MockServiceFactory,
#     clean_container,
#     container_config,
#     container_lifecycle_context,
#     container_metrics_validator,
#     container_test_helper,
#     custom_container_with_mocks,
#     empty_container,
#     error_simulating_container_factory,
#     initialized_mock_container,
#     initialized_test_container,
#     integration_test_container,
#     invalid_container_configs,
#     mock_service_container,
#     mock_service_factory,
#     performance_container,
#     request_scoped_container,
#     service_dependency_chain,
#     test_environment_container,
# Integration testing fixtures (new)
from .auth_fixtures import (
    admin_user,
    auth_middleware_admin,
    auth_middleware_user,
    authenticated_request,
    multiple_service_tokens,
    real_service_token_manager,
    regular_user,
    service_token_request,
    test_authenticated_user,
    test_service_token,
    test_service_user,
)
from .database import (
    test_db_session,
    test_db_with_override,
    test_engine,
)
from .database_fixtures import (
    database_integration_test_manager,
    database_manager_factory,
    isolated_database_config,
    mock_database_dependency_injection,
    mock_database_engine,
    mock_database_manager,
    mock_database_session,
    mock_database_session_factory,
    mock_database_settings,
)
from .security_service_mocks import (
    MockAlertEngine,
    MockAuditService,
    MockSecurityLogger,
    MockSecurityMonitor,
    MockSuspiciousActivityDetector,
    all_security_services,
    clear_test_event_registry,
    mock_security_logger,
    mock_security_monitor,
)


__all__ = [
    # "ContainerTestHelper",  # Disabled due to missing auth.database module
    "MockAlertEngine",
    "MockAuditService",
    "MockSecurityLogger",
    "MockSecurityMonitor",
    # "MockServiceFactory",  # Disabled due to missing auth.database module
    "MockSuspiciousActivityDetector",
    "admin_user",
    "all_security_services",
    "auth_middleware_admin",
    "auth_middleware_user",
    "authenticated_request",
    # "clean_container",  # Disabled due to missing auth.database module
    "clear_test_event_registry",
    # "container_config",  # Disabled due to missing auth.database module
    # "container_lifecycle_context",  # Disabled due to missing auth.database module
    # "container_metrics_validator",  # Disabled due to missing auth.database module
    # "container_test_helper",  # Disabled due to missing auth.database module
    # "custom_container_with_mocks",  # Disabled due to missing auth.database module
    "database_integration_test_manager",
    "database_manager_factory",
    # "empty_container",  # Disabled due to missing auth.database module
    # "error_simulating_container_factory",  # Disabled due to missing auth.database module
    # "initialized_mock_container",  # Disabled due to missing auth.database module
    # "initialized_test_container",  # Disabled due to missing auth.database module
    # "integration_test_container",  # Disabled due to missing auth.database module
    # "invalid_container_configs",  # Disabled due to missing auth.database module
    "isolated_database_config",
    "mock_database_dependency_injection",
    "mock_database_engine",
    "mock_database_manager",
    "mock_database_session",
    "mock_database_session_factory",
    "mock_database_settings",
    "mock_security_logger",
    "mock_security_monitor",
    "multiple_service_tokens",
    "real_service_token_manager",
    "regular_user",
    "service_token_request",
    "sync_test_engine",
    "sync_test_session",
    "test_authenticated_user",
    "test_db_session",
    "test_db_with_override",
    # "mock_service_container",  # Disabled due to missing auth.database module
    # "mock_service_factory",  # Disabled due to missing auth.database module
    # "performance_container",  # Disabled due to missing auth.database module
    # "request_scoped_container",  # Disabled due to missing auth.database module
    # "service_dependency_chain",  # Disabled due to missing auth.database module
    # "test_environment_container",  # Disabled due to missing auth.database module
    # Integration testing fixtures
    "test_engine",
    "test_service_token",
    "test_service_user",
]
