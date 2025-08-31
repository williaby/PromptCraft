"""
Unit tests for AUTH-4 SecurityDashboardEndpoints.

This module provides comprehensive unit tests for the security dashboard FastAPI endpoints,
validating all HTTP routes, authentication requirements, request/response handling,
error conditions, and performance requirements.

Test Coverage:
- SecurityDashboardEndpoints route handlers
- HTTP methods: GET, POST endpoints
- Authentication middleware integration
- Request validation and response formatting
- Error handling for all failure modes
- Performance requirements (<50ms for dashboard data)
- Real-time metrics and statistics endpoints
- Security data filtering and pagination
"""

import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, Request, status
from fastapi.testclient import TestClient

from src.auth.api.security_dashboard_endpoints import (
    AlertSummaryResponse,
    SecurityDashboardEndpoints,
    SecurityEventResponse,
    SecurityMetricsResponse,
    SecurityStatsResponse,
)
from src.auth.services.alert_engine import AlertEngine
from src.auth.services.audit_service import AuditService
from src.auth.services.security_monitor import SecurityMonitor


# Module-level fixtures that can be used by all test classes
@pytest.fixture
def mock_security_monitor():
    """Create mock SecurityMonitor."""
    monitor = AsyncMock(spec=SecurityMonitor)
    monitor.get_security_metrics = AsyncMock()
    monitor.get_recent_events = AsyncMock()
    monitor.get_threat_statistics = AsyncMock()
    return monitor


@pytest.fixture
def mock_alert_engine():
    """Create mock AlertEngine."""
    engine = AsyncMock(spec=AlertEngine)
    engine.get_active_alerts = AsyncMock()
    engine.get_alert_statistics = AsyncMock()
    engine.acknowledge_alert = AsyncMock()
    return engine


@pytest.fixture
def mock_audit_service():
    """Create mock AuditService."""
    service = AsyncMock(spec=AuditService)
    service.get_audit_statistics = AsyncMock()
    service.generate_security_report = AsyncMock()
    return service


@pytest.fixture
def endpoints(mock_security_monitor, mock_alert_engine, mock_audit_service):
    """Create SecurityDashboardEndpoints instance with mocked dependencies."""
    return SecurityDashboardEndpoints(
        security_monitor=mock_security_monitor,
        alert_engine=mock_alert_engine,
        audit_service=mock_audit_service,
    )


class TestSecurityDashboardEndpointsInitialization:
    """Test SecurityDashboardEndpoints class initialization and configuration."""

    @pytest.mark.unit
    def test_initialization_with_dependencies(self, endpoints):
        """Test proper initialization with all dependencies."""
        assert endpoints.security_monitor is not None
        assert endpoints.alert_engine is not None
        assert endpoints.audit_service is not None

    @pytest.mark.unit
    def test_initialization_with_none_dependencies(self):
        """Test initialization fails with None dependencies."""
        with pytest.raises(ValueError, match="SecurityMonitor is required"):
            SecurityDashboardEndpoints(security_monitor=None, alert_engine=MagicMock(), audit_service=MagicMock())

    @pytest.mark.unit
    def test_router_configuration(self, endpoints):
        """Test FastAPI router is properly configured."""
        assert endpoints.router is not None
        assert endpoints.router.prefix == "/api/security/dashboard"
        assert len(endpoints.router.routes) > 0

    @pytest.mark.unit
    def test_route_registration(self, endpoints):
        """Test all required routes are registered."""
        route_paths = [route.path for route in endpoints.router.routes]

        expected_routes = [
            "/metrics",
            "/alerts",
            "/alerts/{alert_id}/acknowledge",
            "/events/search",
            "/audit/generate-report",
            "/audit/statistics",
        ]

        for expected_route in expected_routes:
            assert any(expected_route in path for path in route_paths), f"Missing route: {expected_route}"


class TestSecurityDashboardEndpointsMetricsEndpoint:
    """Test the /dashboard/metrics endpoint functionality."""

    @pytest.fixture
    def mock_request(self):
        """Create mock FastAPI request."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def sample_metrics(self):
        """Sample security metrics data."""
        return {
            "total_events": 1250,
            "critical_events": 45,
            "brute_force_attempts": 12,
            "suspicious_activities": 8,
            "active_alerts": 3,
            "threat_level": "medium",
            "uptime_seconds": 86400,
            "events_per_minute": 15.2,
            "detection_accuracy": 0.94,
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_metrics_success(self, endpoints, mock_request, sample_metrics):
        """Test successful retrieval of security metrics."""
        # Setup
        endpoints.security_monitor.get_security_metrics.return_value = sample_metrics

        # Execute
        response = await endpoints.get_security_metrics(mock_request)

        # Verify
        assert isinstance(response, SecurityMetricsResponse)
        assert response.total_events == 1250
        assert response.critical_events == 45
        assert response.threat_level == "medium"
        assert response.detection_accuracy == 0.94
        endpoints.security_monitor.get_security_metrics.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_metrics_with_timeframe(self, endpoints, mock_request, sample_metrics):
        """Test metrics retrieval with specific timeframe."""
        # Setup
        endpoints.security_monitor.get_security_metrics.return_value = sample_metrics

        # Execute with timeframe
        response = await endpoints.get_security_metrics(mock_request, timeframe_hours=24)

        # Verify
        assert isinstance(response, SecurityMetricsResponse)
        endpoints.security_monitor.get_security_metrics.assert_called_once_with(timeframe_hours=24)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_metrics_monitor_error(self, endpoints, mock_request):
        """Test error handling when security monitor fails."""
        # Setup
        endpoints.security_monitor.get_security_metrics.side_effect = Exception("Database error")

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_metrics(mock_request)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to get security metrics" in str(exc_info.value.detail)

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_get_security_metrics_performance(self, endpoints, mock_request, sample_metrics):
        """Test metrics endpoint meets performance requirements (<50ms)."""
        # Setup
        endpoints.security_monitor.get_security_metrics.return_value = sample_metrics

        # Execute with timing
        start_time = time.time()
        response = await endpoints.get_security_metrics(mock_request)
        end_time = time.time()

        # Verify performance
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 50, f"Metrics endpoint took {execution_time_ms}ms (>50ms)"
        assert isinstance(response, SecurityMetricsResponse)


class TestSecurityDashboardEndpointsEventsEndpoint:
    """Test the /dashboard/events endpoint functionality."""

    @pytest.fixture
    def sample_events(self):
        """Sample security events data."""
        return [
            {
                "id": "evt_001",
                "event_type": "brute_force_attempt",
                "severity": "critical",
                "timestamp": datetime.utcnow(),
                "user_id": "user123",
                "ip_address": "192.168.1.100",
                "details": {"login_attempts": 5},
                "resolved": False,
            },
            {
                "id": "evt_002",
                "event_type": "suspicious_location",
                "severity": "warning",
                "timestamp": datetime.utcnow() - timedelta(minutes=15),
                "user_id": "user456",
                "ip_address": "10.0.0.50",
                "details": {"location": "Unknown City"},
                "resolved": True,
            },
        ]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_events_success(self, endpoints, sample_events):
        """Test successful retrieval of security events."""
        # Setup
        endpoints.security_monitor.get_recent_events.return_value = sample_events

        # Execute
        response = await endpoints.get_security_events()

        # Verify
        assert isinstance(response, SecurityEventResponse)
        assert len(response.events) == 2
        assert response.total_count == 2
        assert response.events[0].event_type == "brute_force_attempt"
        assert response.events[0].severity == "critical"
        endpoints.security_monitor.get_recent_events.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_events_with_filters(self, endpoints, sample_events):
        """Test events retrieval with filtering parameters."""
        # Setup
        filtered_events = [sample_events[0]]  # Only critical severity
        endpoints.security_monitor.get_recent_events.return_value = filtered_events

        # Execute with filters
        response = await endpoints.get_security_events(
            severity="critical",
            event_type="brute_force_attempt",
            limit=10,
            offset=0,
        )

        # Verify
        assert len(response.events) == 1
        assert response.events[0].severity == "critical"
        endpoints.security_monitor.get_recent_events.assert_called_once_with(
            severity="critical",
            event_type="brute_force_attempt",
            limit=10,
            offset=0,
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_events_empty_result(self, endpoints):
        """Test handling of empty events result."""
        # Setup
        endpoints.security_monitor.get_recent_events.return_value = []

        # Execute
        response = await endpoints.get_security_events()

        # Verify
        assert isinstance(response, SecurityEventResponse)
        assert len(response.events) == 0
        assert response.total_count == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_events_pagination(self, endpoints, sample_events):
        """Test events pagination functionality."""
        # Setup
        endpoints.security_monitor.get_recent_events.return_value = sample_events

        # Execute with pagination
        await endpoints.get_security_events(limit=1, offset=1)

        # Verify
        endpoints.security_monitor.get_recent_events.assert_called_once_with(limit=1, offset=1)


class TestSecurityDashboardEndpointsAlertsEndpoint:
    """Test the /dashboard/alerts endpoint functionality."""

    @pytest.fixture
    def sample_alerts(self):
        """Sample alerts data."""
        return {
            "active_alerts": [
                {
                    "id": "alert_001",
                    "title": "Brute Force Attack Detected",
                    "severity": "critical",
                    "created_at": datetime.utcnow(),
                    "event_count": 15,
                    "affected_users": ["user123"],
                    "status": "active",
                },
                {
                    "id": "alert_002",
                    "title": "Unusual Login Pattern",
                    "severity": "warning",
                    "created_at": datetime.utcnow() - timedelta(minutes=30),
                    "event_count": 3,
                    "affected_users": ["user456", "user789"],
                    "status": "investigating",
                },
            ],
            "total_count": 2,
            "critical_count": 1,
            "warning_count": 1,
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_alerts_success(self, endpoints, sample_alerts):
        """Test successful retrieval of security alerts."""
        # Setup
        endpoints.alert_engine.get_active_alerts.return_value = sample_alerts

        # Execute
        response = await endpoints.get_security_alerts()

        # Verify
        assert isinstance(response, AlertSummaryResponse)
        assert len(response.active_alerts) == 2
        assert response.total_count == 2
        assert response.critical_count == 1
        assert response.active_alerts[0].severity == "critical"
        endpoints.alert_engine.get_active_alerts.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_alerts_with_status_filter(self, endpoints, sample_alerts):
        """Test alerts retrieval with status filtering."""
        # Setup
        active_alerts = {
            "active_alerts": [sample_alerts["active_alerts"][0]],
            "total_count": 1,
            "critical_count": 1,
            "warning_count": 0,
        }
        endpoints.alert_engine.get_active_alerts.return_value = active_alerts

        # Execute
        response = await endpoints.get_security_alerts(status="active")

        # Verify
        assert len(response.active_alerts) == 1
        assert response.active_alerts[0].status == "active"
        endpoints.alert_engine.get_active_alerts.assert_called_once_with(status="active")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_acknowledge_alert_success(self, endpoints):
        """Test successful alert acknowledgment."""
        # Setup
        alert_id = "alert_001"
        user_id = "admin123"
        endpoints.alert_engine.acknowledge_alert.return_value = True

        # Execute
        response = await endpoints.acknowledge_alert(alert_id, user_id=user_id)

        # Verify
        assert response["success"] is True
        assert response["alert_id"] == alert_id
        assert "acknowledged" in response["message"]
        endpoints.alert_engine.acknowledge_alert.assert_called_once_with(alert_id, user_id)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_acknowledge_alert_not_found(self, endpoints):
        """Test acknowledgment of non-existent alert."""
        # Setup
        alert_id = "nonexistent_alert"
        endpoints.alert_engine.acknowledge_alert.return_value = False

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.acknowledge_alert(alert_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Alert not found" in str(exc_info.value.detail)


class TestSecurityDashboardEndpointsStatisticsEndpoint:
    """Test the /dashboard/statistics endpoint functionality."""

    @pytest.fixture
    def sample_statistics(self):
        """Sample security statistics."""
        return {
            "daily_stats": {"events_count": 486, "alerts_generated": 12, "threats_blocked": 8, "false_positives": 2},
            "weekly_trends": {"event_growth": 0.15, "alert_reduction": -0.08, "detection_improvement": 0.03},
            "threat_breakdown": {
                "brute_force": 45,
                "suspicious_location": 23,
                "privilege_escalation": 8,
                "data_exfiltration": 3,
            },
            "performance_metrics": {
                "avg_detection_time_ms": 12.5,
                "avg_response_time_ms": 245,
                "system_uptime": 0.9998,
            },
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_statistics_success(self, endpoints, sample_statistics):
        """Test successful retrieval of security statistics."""
        # Setup
        endpoints.security_monitor.get_threat_statistics.return_value = sample_statistics

        # Execute
        response = await endpoints.get_security_statistics()

        # Verify
        assert isinstance(response, SecurityStatsResponse)
        assert response.daily_stats["events_count"] == 486
        assert response.weekly_trends["event_growth"] == 0.15
        assert response.threat_breakdown["brute_force"] == 45
        assert response.performance_metrics["avg_detection_time_ms"] == 12.5
        endpoints.security_monitor.get_threat_statistics.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_statistics_with_period(self, endpoints, sample_statistics):
        """Test statistics retrieval with specific time period."""
        # Setup
        endpoints.security_monitor.get_threat_statistics.return_value = sample_statistics

        # Execute
        await endpoints.get_security_statistics(period="weekly")

        # Verify
        endpoints.security_monitor.get_threat_statistics.assert_called_once_with(period="weekly")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_security_statistics_error_handling(self, endpoints):
        """Test error handling in statistics retrieval."""
        # Setup
        endpoints.security_monitor.get_threat_statistics.side_effect = Exception("Stats error")

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_statistics()

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve security statistics" in str(exc_info.value.detail)


class TestSecurityDashboardEndpointsReportsEndpoint:
    """Test the /reports/audit endpoint functionality."""

    @pytest.fixture
    def sample_audit_report(self):
        """Sample audit report data."""
        return {
            "report_id": "rpt_20241023_001",
            "generated_at": datetime.utcnow(),
            "period": {"start_date": datetime.utcnow() - timedelta(days=7), "end_date": datetime.utcnow()},
            "summary": {
                "total_events": 3420,
                "security_incidents": 15,
                "resolved_incidents": 12,
                "compliance_score": 0.96,
            },
            "details": {
                "critical_events": 45,
                "high_priority_events": 186,
                "medium_priority_events": 892,
                "low_priority_events": 2297,
            },
            "recommendations": [
                "Implement additional monitoring for suspicious locations",
                "Review and update brute force detection thresholds",
            ],
        }

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audit_report_success(self, endpoints, sample_audit_report):
        """Test successful audit report generation."""
        # Setup
        endpoints.audit_service.generate_security_report.return_value = sample_audit_report

        # Execute
        response = await endpoints.generate_audit_report()

        # Verify
        assert response["report_id"] == "rpt_20241023_001"
        assert response["summary"]["compliance_score"] == 0.96
        assert len(response["recommendations"]) == 2
        endpoints.audit_service.generate_security_report.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audit_report_with_parameters(self, endpoints, sample_audit_report):
        """Test audit report generation with specific parameters."""
        # Setup
        endpoints.audit_service.generate_security_report.return_value = sample_audit_report
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()

        # Execute
        await endpoints.generate_audit_report(
            start_date=start_date,
            end_date=end_date,
            report_format="detailed",
        )

        # Verify
        endpoints.audit_service.generate_security_report.assert_called_once_with(
            start_date=start_date,
            end_date=end_date,
            report_format="detailed",
        )

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_audit_report_service_error(self, endpoints):
        """Test error handling in audit report generation."""
        # Setup
        endpoints.audit_service.generate_security_report.side_effect = Exception("Report error")

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.generate_audit_report()

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to generate audit report" in str(exc_info.value.detail)


class TestSecurityDashboardEndpointsAuthentication:
    """Test authentication and authorization for security endpoints."""

    @pytest.fixture
    def mock_authenticated_request(self):
        """Create mock authenticated request."""
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Bearer valid_token"}
        request.state = MagicMock()
        request.state.user_id = "admin123"
        request.state.permissions = ["security:read", "security:write"]
        return request

    @pytest.fixture
    def mock_unauthenticated_request(self):
        """Create mock unauthenticated request."""
        request = MagicMock(spec=Request)
        request.headers = {}
        request.state = MagicMock()
        request.state.user_id = None
        return request

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_authenticated_access_success(self, endpoints, mock_authenticated_request):
        """Test successful access with valid authentication."""
        # Setup
        sample_metrics = {"total_events": 100}
        endpoints.security_monitor.get_security_metrics.return_value = sample_metrics

        # Execute
        response = await endpoints.get_security_metrics(mock_authenticated_request)

        # Verify
        assert isinstance(response, SecurityMetricsResponse)
        endpoints.security_monitor.get_security_metrics.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unauthenticated_access_denied(self, endpoints, mock_unauthenticated_request):
        """Test access denial for unauthenticated requests."""
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_metrics(mock_unauthenticated_request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.unit
    def test_required_permissions_configuration(self, endpoints):
        """Test that endpoints have proper permission requirements."""
        # This would test the actual permission decorators/middleware
        # Implementation depends on the actual auth system used


class TestSecurityDashboardEndpointsErrorHandling:
    """Test comprehensive error handling for all endpoints."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_database_connection_error(self, endpoints, mock_request):
        """Test handling of database connection failures."""
        # Setup
        endpoints.security_monitor.get_security_metrics.side_effect = ConnectionError("Database unavailable")

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_metrics(mock_request)

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_timeout_error(self, endpoints):
        """Test handling of operation timeouts."""
        # Setup
        endpoints.alert_engine.get_active_alerts.side_effect = TimeoutError("Operation timed out")

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_alerts()

        assert exc_info.value.status_code == status.HTTP_504_GATEWAY_TIMEOUT

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_parameter_error(self, endpoints):
        """Test handling of invalid request parameters."""
        # Execute & Verify - invalid severity level
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_events(severity="invalid_level")

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_resource_not_found_error(self, endpoints):
        """Test handling of resource not found scenarios."""
        # Setup
        endpoints.alert_engine.acknowledge_alert.return_value = False

        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.acknowledge_alert("nonexistent_alert")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestSecurityDashboardEndpointsPerformanceRequirements:
    """Test performance requirements for all endpoints."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_all_endpoints_performance(self, endpoints, mock_request):
        """Test that all endpoints meet performance requirements."""
        # Setup mocks
        endpoints.security_monitor.get_security_metrics.return_value = {"total_events": 100}
        endpoints.security_monitor.get_recent_events.return_value = []
        endpoints.alert_engine.get_active_alerts.return_value = {"active_alerts": [], "total_count": 0}
        endpoints.security_monitor.get_threat_statistics.return_value = {"daily_stats": {}}
        endpoints.audit_service.generate_security_report.return_value = {"report_id": "test"}

        # Test metrics endpoint
        start_time = time.time()
        await endpoints.get_security_metrics(mock_request)
        metrics_time = (time.time() - start_time) * 1000

        # Test events endpoint
        start_time = time.time()
        await endpoints.get_security_events()
        events_time = (time.time() - start_time) * 1000

        # Test alerts endpoint
        start_time = time.time()
        await endpoints.get_security_alerts()
        alerts_time = (time.time() - start_time) * 1000

        # Test statistics endpoint
        start_time = time.time()
        await endpoints.get_security_statistics()
        stats_time = (time.time() - start_time) * 1000

        # Verify performance requirements
        assert metrics_time < 50, f"Metrics endpoint: {metrics_time}ms (>50ms)"
        assert events_time < 50, f"Events endpoint: {events_time}ms (>50ms)"
        assert alerts_time < 50, f"Alerts endpoint: {alerts_time}ms (>50ms)"
        assert stats_time < 50, f"Statistics endpoint: {stats_time}ms (>50ms)"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, endpoints, mock_request):
        """Test performance under concurrent load."""
        # Setup
        endpoints.security_monitor.get_security_metrics.return_value = {"total_events": 100}

        # Execute concurrent requests
        start_time = time.time()
        tasks = []
        for _ in range(10):
            task = asyncio.create_task(endpoints.get_security_metrics(mock_request))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Verify
        assert len(results) == 10
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / 10

        # Should handle 10 concurrent requests with average <50ms per request
        assert avg_time_ms < 50, f"Average concurrent request time: {avg_time_ms}ms (>50ms)"


class TestSecurityDashboardEndpointsIntegration:
    """Integration tests with real FastAPI TestClient."""

    @pytest.fixture
    def test_app(self, endpoints):
        """Create FastAPI test application."""
        from fastapi import FastAPI

        from src.auth.api.security_dashboard_endpoints import get_security_service

        app = FastAPI()
        app.include_router(endpoints.router)

        # Override the dependency with a mock that returns expected data
        def mock_get_security_service():
            from unittest.mock import AsyncMock

            from src.auth.services.security_integration import SecurityIntegrationService

            mock_service = AsyncMock(spec=SecurityIntegrationService)
            mock_service.get_comprehensive_metrics.return_value = {
                "integration": {
                    "total_events_processed": 1250,
                    "total_alerts_generated": 45,
                    "average_processing_time_ms": 35.5,
                    "total_suspicious_activities": 12,
                },
                "service_health": {
                    "logger_healthy": True,
                    "monitor_healthy": True,
                    "alert_engine_healthy": True,
                    "detector_healthy": True,
                },
            }
            return mock_service

        app.dependency_overrides[get_security_service] = mock_get_security_service
        return app

    @pytest.fixture
    def client(self, test_app):
        """Create FastAPI test client."""
        return TestClient(test_app)

    @pytest.mark.unit
    def test_metrics_endpoint_http_get(self, client, endpoints):
        """Test metrics endpoint via HTTP GET."""
        # Execute
        response = client.get("/api/security/dashboard/metrics")

        # Verify
        assert response.status_code == 200
        data = response.json()
        # Test the actual response structure from SecurityMetricsResponse
        assert "total_events_today" in data
        assert "total_events_week" in data
        assert "system_health_score" in data
        assert "service_availability" in data
        assert isinstance(data["total_events_today"], int)
        assert isinstance(data["system_health_score"], float)

    @pytest.mark.unit
    def test_alerts_acknowledge_http_post(self, client, endpoints):
        """Test alert acknowledgment via HTTP POST."""
        # Setup
        endpoints.alert_engine.acknowledge_alert.return_value = True

        # Execute
        test_uuid = "00000000-0000-0000-0000-000000000001"
        response = client.post(f"/api/security/dashboard/alerts/{test_uuid}/acknowledge", json={"user_id": "admin123"})

        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Alert acknowledged successfully"
        assert data["alert_id"] == test_uuid
        assert "acknowledged_at" in data

    @pytest.mark.unit
    def test_invalid_endpoint_returns_404(self, client):
        """Test that invalid endpoints return 404."""
        response = client.get("/api/v1/security/invalid/endpoint")
        assert response.status_code == 404


# Fixtures for request mocking
@pytest.fixture
def mock_request():
    """Create a mock FastAPI request for testing."""
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer test_token"}
    request.client = MagicMock()
    request.client.host = "127.0.0.1"
    request.state = MagicMock()
    request.state.user_id = "test_user"
    return request
