"""
API Router Test Fixtures

Comprehensive test fixtures for AUTH-4 API router testing.
Provides shared mock data, services, and utilities for all router tests.
"""

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.api.routers.alerts_router import router as alerts_router
from src.auth.api.routers.analytics_router import router as analytics_router
from src.auth.api.routers.audit_router import router as audit_router
from src.auth.api.routers.charts_router import router as charts_router
from src.auth.api.routers.events_router import router as events_router
from src.auth.api.routers.health_router import router as health_router
from src.auth.api.routers.metrics_router import router as metrics_router
from src.auth.api.routers.users_router import router as users_router

# =================== FASTAPI APPLICATION FIXTURES ===================


@pytest.fixture
def test_app() -> FastAPI:
    """Create FastAPI test application with all routers."""
    app = FastAPI(title="AUTH-4 Security Dashboard API Test")

    # Include all routers
    app.include_router(alerts_router)
    app.include_router(analytics_router)
    app.include_router(audit_router)
    app.include_router(charts_router)
    app.include_router(events_router)
    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(users_router)

    return app


@pytest.fixture
def test_client(test_app: FastAPI) -> TestClient:
    """Create FastAPI test client."""
    return TestClient(test_app)


# =================== MOCK SERVICE FIXTURES ===================


@pytest.fixture
def mock_security_service() -> AsyncMock:
    """Mock SecurityIntegrationService for all router tests."""
    mock = AsyncMock()
    # Chart router methods
    mock.get_event_timeline.return_value = []
    mock.get_user_risk_distribution.return_value = {"low": 40, "medium": 30, "high": 20, "critical": 10}
    mock.get_event_risk_distribution.return_value = {"low": 40, "medium": 30, "high": 20, "critical": 10}
    mock.get_alert_risk_distribution.return_value = {"low": 40, "medium": 30, "high": 20, "critical": 10}

    # Audit router methods
    mock.get_audit_event_summary.return_value = {"total_events": 0, "total_users": 0}
    mock.get_comprehensive_audit_statistics.return_value = {"stats": {}}
    mock.get_retention_policies.return_value = []
    mock.count_events_before_date.return_value = 0

    # Metrics router methods
    mock.get_comprehensive_metrics.return_value = {}

    # Health router methods
    mock.get_all_service_health.return_value = {}
    mock.check_database_health.return_value = {"status": "healthy"}

    # Analytics router methods
    mock.get_security_trends.return_value = {"trends": []}

    return mock


@pytest.fixture
def mock_alert_engine() -> AsyncMock:
    """Mock AlertEngine for alerts router tests."""
    mock = AsyncMock()
    mock.get_recent_alerts.return_value = []
    mock.get_alert_by_id.return_value = None
    mock.acknowledge_alert.return_value = {"status": "acknowledged"}
    return mock


@pytest.fixture
def mock_suspicious_activity_detector() -> AsyncMock:
    """Mock SuspiciousActivityDetector for user router tests."""
    mock = AsyncMock()
    # Users router methods
    mock.get_user_activity_summary.return_value = {
        "base_risk_score": 30,
        "failed_logins_today": 2,
        "unusual_location_count": 1,
        "off_hours_activity_count": 0,
        "total_logins": 45,
        "last_activity": datetime.now(UTC),
        "known_location_count": 3,
    }
    mock.get_user_suspicious_activities.return_value = [
        {"description": "Unusual login time detected"},
        {"description": "New device used for login"},
    ]

    # Analytics router methods
    mock.analyze_behavioral_patterns.return_value = []

    return mock


@pytest.fixture
def mock_audit_service() -> AsyncMock:
    """Mock AuditService for audit router tests."""
    mock = AsyncMock()
    mock.get_filtered_logs.return_value = {"logs": [], "total": 0, "page": 1}
    mock.export_logs.return_value = {"export_id": "audit-export-456", "format": "json"}
    return mock


# =================== SAMPLE DATA FIXTURES ===================


@pytest.fixture
def sample_alert_data() -> dict[str, Any]:
    """Sample alert data for testing."""
    return {
        "id": "alert-123",
        "title": "High Risk Login Detected",
        "description": "Multiple failed login attempts from unusual location",
        "severity": "high",
        "status": "active",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "user_id": "user-456",
        "metadata": {
            "ip_address": "192.168.1.100",
            "location": "Unknown",
            "failed_attempts": 5,
        },
    }


@pytest.fixture
def sample_multiple_alerts() -> list[dict[str, Any]]:
    """Sample multiple alerts for testing pagination."""
    base_time = datetime.now(UTC)
    return [
        {
            "id": f"alert-{i}",
            "title": f"Security Alert #{i}",
            "description": f"Alert description {i}",
            "severity": ["low", "medium", "high", "critical"][i % 4],
            "status": ["active", "acknowledged", "resolved"][i % 3],
            "created_at": base_time - timedelta(hours=i),
            "updated_at": base_time - timedelta(hours=i),
            "user_id": f"user-{i}",
            "metadata": {"source": f"source-{i}"},
        }
        for i in range(15)
    ]


@pytest.fixture
def sample_security_trends() -> dict[str, Any]:
    """Sample security trends data for analytics testing."""
    base_time = datetime.now(UTC)
    return {
        "trends": [
            {
                "timestamp": base_time - timedelta(hours=i),
                "failed_logins": 10 + i,
                "successful_logins": 100 + i * 2,
                "alerts_generated": 2 + i // 2,
                "risk_score_avg": 25.5 + i,
            }
            for i in range(24)
        ],
        "summary": {
            "total_events": 1250,
            "trend_direction": "stable",
            "risk_level_change": "no_change",
        },
    }


@pytest.fixture
def sample_audit_logs() -> dict[str, Any]:
    """Sample audit logs for audit router testing."""
    base_time = datetime.now(UTC)
    return {
        "logs": [
            {
                "id": f"log-{i}",
                "timestamp": base_time - timedelta(minutes=i * 5),
                "user_id": f"user-{i % 3}",
                "action": ["login", "logout", "password_change", "profile_update"][i % 4],
                "resource": f"resource-{i}",
                "ip_address": f"192.168.1.{100 + i}",
                "user_agent": "Mozilla/5.0 Test Browser",
                "success": i % 7 != 0,  # Some failures
                "metadata": {"session_id": f"session-{i}"},
            }
            for i in range(20)
        ],
        "total": 20,
        "page": 1,
        "pages": 2,
    }


@pytest.fixture
def sample_security_events() -> dict[str, Any]:
    """Sample security events for events router testing."""
    base_time = datetime.now(UTC)
    return {
        "events": [
            {
                "id": f"event-{i}",
                "timestamp": base_time - timedelta(minutes=i * 10),
                "event_type": ["login_failure", "suspicious_access", "policy_violation", "security_scan"][i % 4],
                "severity": ["info", "warning", "error", "critical"][i % 4],
                "user_id": f"user-{i % 5}",
                "ip_address": f"10.0.0.{50 + i}",
                "description": f"Security event description {i}",
                "metadata": {
                    "source": "security_monitor",
                    "detection_method": "rule_based",
                    "risk_score": 30 + i * 2,
                },
            }
            for i in range(25)
        ],
        "total": 25,
        "page": 1,
    }


@pytest.fixture
def sample_timeline_data() -> list[dict[str, Any]]:
    """Sample timeline data for charts testing."""
    base_time = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    return [
        {
            "timestamp": base_time - timedelta(hours=i),
            "event_count": 15 + (i * 3) % 20,  # Varying event counts
        }
        for i in range(24)
    ]


@pytest.fixture
def sample_risk_distribution() -> dict[str, int]:
    """Sample risk distribution data for charts testing."""
    return {
        "low": 40,
        "medium": 30,
        "high": 20,
        "critical": 10,
    }


@pytest.fixture
def sample_service_health() -> dict[str, Any]:
    """Sample service health data for health router testing."""
    return {
        "security_monitor": {
            "status": "healthy",
            "response_time": 0.15,
            "last_check": datetime.now(UTC),
            "details": {"active_monitors": 5, "failed_checks": 0},
        },
        "audit_service": {
            "status": "degraded",
            "response_time": 1.25,
            "last_check": datetime.now(UTC),
            "details": {"queue_size": 1200, "processing_delay": "2m"},
        },
        "alert_engine": {
            "status": "healthy",
            "response_time": 0.08,
            "last_check": datetime.now(UTC),
            "details": {"active_rules": 12, "alerts_pending": 3},
        },
    }


@pytest.fixture
def sample_database_health() -> dict[str, Any]:
    """Sample database health data for health router testing."""
    return {
        "status": "healthy",
        "connection_pool": {
            "active_connections": 8,
            "max_connections": 20,
            "pool_usage": "40%",
        },
        "query_performance": {
            "avg_response_time": 0.045,
            "slow_queries": 2,
            "failed_queries": 0,
        },
        "last_backup": datetime.now(UTC) - timedelta(hours=6),
    }


@pytest.fixture
def sample_system_metrics() -> dict[str, Any]:
    """Sample system metrics for metrics router testing."""
    return {
        "system_health_score": 87.5,
        "total_events_today": 1234,
        "active_alerts": 5,
        "resolved_alerts": 15,
        "avg_response_time": 0.234,
        "error_rate": 0.023,
        "uptime_percentage": 99.95,
        "services_status": {
            "security_monitor": "healthy",
            "audit_service": "degraded",
            "alert_engine": "healthy",
            "suspicious_detector": "healthy",
        },
        "performance_metrics": {
            "cpu_usage": 23.5,
            "memory_usage": 67.8,
            "disk_usage": 34.2,
            "network_latency": 12.3,
        },
        "security_metrics": {
            "failed_login_attempts": 45,
            "blocked_ips": 12,
            "security_events": 89,
            "risk_score_avg": 32.1,
        },
    }


@pytest.fixture
def sample_user_activity() -> dict[str, Any]:
    """Sample user activity data for users router testing."""
    return {
        "base_risk_score": 30,
        "failed_logins_today": 8,
        "unusual_location_count": 4,
        "off_hours_activity_count": 6,
        "total_logins": 120,
        "last_activity": datetime.now(UTC) - timedelta(hours=2),
        "known_location_count": 5,
    }


@pytest.fixture
def sample_suspicious_activities() -> list[dict[str, Any]]:
    """Sample suspicious activities for users router testing."""
    return [
        {"description": "Multiple failed login attempts detected"},
        {"description": "Unusual login time (3:00 AM)"},
        {"description": "New device used for authentication"},
        {"description": "Login from suspicious IP address"},
        {"description": "Rapid succession of password attempts"},
    ]


# =================== UTILITY FIXTURES ===================


@pytest.fixture
def mock_external_service_checks() -> dict[str, MagicMock]:
    """Mock external service checks for health router testing."""
    return {
        "check_qdrant_health": MagicMock(return_value={"status": "healthy", "response_time": 0.05}),
        "check_redis_health": MagicMock(return_value={"status": "healthy", "response_time": 0.02}),
        "check_external_api_health": MagicMock(return_value={"status": "degraded", "response_time": 2.1}),
    }


@pytest.fixture
def csv_export_content() -> str:
    """Sample CSV export content for testing."""
    return """timestamp,event_type,user_id,severity,description
2025-01-27T10:00:00Z,login_failure,user-1,warning,Failed login attempt
2025-01-27T09:30:00Z,suspicious_access,user-2,error,Unusual access pattern detected
2025-01-27T09:00:00Z,policy_violation,user-3,critical,Security policy violation"""


@pytest.fixture
def json_export_content() -> dict[str, Any]:
    """Sample JSON export content for testing."""
    return {
        "export_metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "format": "json",
            "record_count": 3,
        },
        "data": [
            {
                "timestamp": "2025-01-27T10:00:00Z",
                "event_type": "login_failure",
                "user_id": "user-1",
                "severity": "warning",
                "description": "Failed login attempt",
            },
            {
                "timestamp": "2025-01-27T09:30:00Z",
                "event_type": "suspicious_access",
                "user_id": "user-2",
                "severity": "error",
                "description": "Unusual access pattern detected",
            },
        ],
    }


# =================== PERFORMANCE TEST FIXTURES ===================


@pytest.fixture
def performance_test_data() -> dict[str, Any]:
    """Large dataset for performance testing."""
    base_time = datetime.now(UTC)
    return {
        "large_alert_list": [
            {
                "id": f"perf-alert-{i}",
                "title": f"Performance Test Alert {i}",
                "severity": ["low", "medium", "high", "critical"][i % 4],
                "status": ["active", "acknowledged"][i % 2],
                "created_at": base_time - timedelta(seconds=i),
            }
            for i in range(1000)
        ],
        "large_event_list": [
            {
                "id": f"perf-event-{i}",
                "event_type": f"perf_event_{i % 10}",
                "timestamp": base_time - timedelta(seconds=i),
                "user_id": f"perf-user-{i % 100}",
                "severity": ["info", "warning", "error"][i % 3],
            }
            for i in range(5000)
        ],
    }


# =================== ERROR SIMULATION FIXTURES ===================


@pytest.fixture
def error_simulation_service() -> AsyncMock:
    """Mock service that raises various exceptions for error testing."""
    mock = AsyncMock()

    # Configure different error scenarios
    mock.get_nonexistent_item.side_effect = Exception("Item not found")
    mock.timeout_operation.side_effect = TimeoutError("Operation timed out")
    mock.database_error.side_effect = Exception("Database connection failed")
    mock.validation_error.side_effect = ValueError("Invalid input parameters")

    return mock


# =================== DEPENDENCY OVERRIDE UTILITIES ===================


def create_mock_dependency_overrides(
    mock_security_service: AsyncMock,
    mock_suspicious_activity_detector: AsyncMock | None = None,
    mock_audit_service: AsyncMock | None = None,
    mock_alert_engine: AsyncMock | None = None,
) -> dict[str, Any]:
    """Create dependency overrides for FastAPI testing."""
    from src.auth.api.routers.alerts_router import get_alert_engine
    from src.auth.api.routers.alerts_router import get_security_service as get_alerts_security_service
    from src.auth.api.routers.analytics_router import get_security_service as get_analytics_security_service
    from src.auth.api.routers.analytics_router import get_suspicious_activity_detector as get_analytics_detector
    from src.auth.api.routers.audit_router import get_audit_service
    from src.auth.api.routers.audit_router import get_security_service as get_audit_security_service
    from src.auth.api.routers.charts_router import get_security_service as get_charts_security_service
    from src.auth.api.routers.events_router import get_security_service as get_events_security_service
    from src.auth.api.routers.health_router import get_security_service as get_health_security_service
    from src.auth.api.routers.metrics_router import get_security_service as get_metrics_security_service
    from src.auth.api.routers.users_router import get_security_service as get_users_security_service
    from src.auth.api.routers.users_router import get_suspicious_activity_detector

    overrides = {
        get_alerts_security_service: lambda: mock_security_service,
        get_analytics_security_service: lambda: mock_security_service,
        get_audit_security_service: lambda: mock_security_service,
        get_charts_security_service: lambda: mock_security_service,
        get_events_security_service: lambda: mock_security_service,
        get_health_security_service: lambda: mock_security_service,
        get_metrics_security_service: lambda: mock_security_service,
        get_users_security_service: lambda: mock_security_service,
    }

    if mock_suspicious_activity_detector:
        overrides[get_suspicious_activity_detector] = lambda: mock_suspicious_activity_detector
        overrides[get_analytics_detector] = lambda: mock_suspicious_activity_detector

    if mock_audit_service:
        overrides[get_audit_service] = lambda: mock_audit_service

    if mock_alert_engine:
        overrides[get_alert_engine] = lambda: mock_alert_engine

    return overrides


# =================== TEST UTILITY FUNCTIONS ===================


def assert_performance_response_time(response_time: float, max_time: float = 2.0) -> None:
    """Assert that response time is within acceptable limits."""
    assert response_time < max_time, f"Response time {response_time}s exceeds limit of {max_time}s"


def assert_pagination_response(data: dict[str, Any], expected_total: int | None = None) -> None:
    """Assert that pagination response has required fields."""
    required_fields = ["total", "page"]
    for field in required_fields:
        assert field in data, f"Response missing required pagination field: {field}"

    if expected_total is not None:
        assert data["total"] == expected_total, f"Expected total {expected_total}, got {data['total']}"


def assert_security_response_format(data: dict[str, Any], required_fields: list[str]) -> None:
    """Assert that security response has required fields and proper format."""
    for field in required_fields:
        assert field in data, f"Response missing required field: {field}"

    # Common security response validations
    if "timestamp" in data:
        assert isinstance(data["timestamp"], (str, datetime)), "Timestamp must be string or datetime"

    if "severity" in data:
        valid_severities = ["info", "low", "warning", "medium", "error", "high", "critical"]
        assert data["severity"] in valid_severities, f"Invalid severity: {data['severity']}"


def create_test_timeline_data(hours: int = 24) -> list[dict[str, Any]]:
    """Create test timeline data for chart testing."""
    base_time = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)
    return [
        {
            "timestamp": base_time - timedelta(hours=i),
            "event_count": 10 + (i * 2) % 25,  # Varying counts with pattern
        }
        for i in range(hours)
    ]


def create_test_user_activity(
    risk_score: int = 30,
    failed_logins: int = 2,
    unusual_locations: int = 1,
    off_hours: int = 0,
) -> dict[str, Any]:
    """Create customized test user activity data."""
    return {
        "base_risk_score": risk_score,
        "failed_logins_today": failed_logins,
        "unusual_location_count": unusual_locations,
        "off_hours_activity_count": off_hours,
        "total_logins": 50 + risk_score,
        "last_activity": datetime.now(UTC) - timedelta(hours=1),
        "known_location_count": max(1, 5 - unusual_locations),
    }
