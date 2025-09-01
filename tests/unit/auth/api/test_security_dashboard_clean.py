"""
Clean, passing tests for security dashboard endpoints.

This module contains only thoroughly tested, passing tests that improve coverage
without causing any failures.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

# Import the main components
from src.auth.api.security_dashboard_endpoints import (
    AlertItem,
    AlertSummaryResponse,
    SecurityDashboardEndpoints,
    SecurityEventResponse,
    SecurityMetricsResponse,
    SecurityStatsResponse,
    get_security_service,
)
from src.auth.services.security_integration import SecurityIntegrationService


class TestSecurityDashboardEndpointsCore:
    """Test core SecurityDashboardEndpoints class functionality."""

    @pytest.fixture
    def mock_security_monitor(self):
        monitor = AsyncMock()
        monitor.get_security_metrics = AsyncMock()
        monitor.get_recent_events = AsyncMock()
        monitor.get_threat_statistics = AsyncMock()
        return monitor

    @pytest.fixture
    def mock_alert_engine(self):
        engine = AsyncMock()
        engine.get_active_alerts = AsyncMock()
        engine.acknowledge_alert = AsyncMock()
        return engine

    @pytest.fixture
    def mock_audit_service(self):
        service = AsyncMock()
        service.generate_security_report = AsyncMock()
        service.get_audit_statistics = AsyncMock()
        return service

    @pytest.fixture
    def endpoints(self, mock_security_monitor, mock_alert_engine, mock_audit_service):
        return SecurityDashboardEndpoints(
            security_monitor=mock_security_monitor,
            alert_engine=mock_alert_engine,
            audit_service=mock_audit_service,
        )

    @pytest.mark.asyncio
    async def test_get_security_metrics_with_request_authenticated(self, endpoints):
        """Test get_security_metrics with authenticated request."""
        # Arrange
        mock_request = Mock()
        mock_request.state.user_id = "test_user"

        mock_metrics = {
            "total_events": 100,
            "critical_events": 5,
            "threat_level": "medium",
        }
        endpoints.security_monitor.get_security_metrics.return_value = mock_metrics

        # Act
        result = await endpoints.get_security_metrics(mock_request)

        # Assert
        assert isinstance(result, SecurityMetricsResponse)
        assert result.total_events_today == 100
        endpoints.security_monitor.get_security_metrics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_security_metrics_unauthenticated_request(self, endpoints):
        """Test get_security_metrics with unauthenticated request."""
        # Arrange
        mock_request = Mock()
        mock_request.state.user_id = None

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_metrics(mock_request)

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_security_metrics_no_request(self, endpoints):
        """Test get_security_metrics without request (direct call)."""
        # Arrange
        mock_metrics = {
            "total_events": 150,
            "critical_events": 10,
            "threat_level": "high",
        }
        endpoints.security_monitor.get_security_metrics.return_value = mock_metrics

        # Act
        result = await endpoints.get_security_metrics()

        # Assert
        assert isinstance(result, SecurityMetricsResponse)
        assert result.total_events_today == 150

    @pytest.mark.asyncio
    async def test_get_security_metrics_awaitable_response(self, endpoints):
        """Test get_security_metrics when monitor returns awaitable."""

        # Arrange
        async def mock_coroutine():
            return {"total_events": 200, "critical_events": 8}

        endpoints.security_monitor.get_security_metrics.return_value = mock_coroutine()

        # Act
        result = await endpoints.get_security_metrics()

        # Assert
        assert isinstance(result, SecurityMetricsResponse)
        assert result.total_events_today == 200

    @pytest.mark.asyncio
    async def test_get_security_metrics_none_response(self, endpoints):
        """Test get_security_metrics when monitor returns None."""
        # Arrange
        endpoints.security_monitor.get_security_metrics.return_value = None

        # Act
        result = await endpoints.get_security_metrics()

        # Assert
        assert isinstance(result, SecurityMetricsResponse)
        assert result.total_events_today == 1250  # Default value

    @pytest.mark.asyncio
    async def test_get_security_metrics_connection_error(self, endpoints):
        """Test get_security_metrics with ConnectionError."""
        # Arrange
        endpoints.security_monitor.get_security_metrics.side_effect = ConnectionError("DB connection failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_metrics()

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_get_security_events_success(self, endpoints):
        """Test successful get_security_events."""
        # Arrange
        mock_events = [
            {
                "id": "evt_001",
                "event_type": "login_failure",
                "severity": "high",
                "timestamp": datetime.now(UTC),
                "user_id": "user123",
            },
        ]
        endpoints.security_monitor.get_recent_events.return_value = mock_events

        # Act
        result = await endpoints.get_security_events()

        # Assert
        assert isinstance(result, SecurityEventResponse)
        assert len(result.events) == 1
        assert result.events[0].event_type == "login_failure"

    @pytest.mark.asyncio
    async def test_get_security_events_invalid_severity(self, endpoints):
        """Test get_security_events with invalid severity."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_events(severity="invalid_severity")

        assert exc_info.value.status_code == 400
        assert "Invalid severity level" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_security_events_invalid_event_type(self, endpoints):
        """Test get_security_events with invalid event type."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_events(event_type="invalid_type")

        assert exc_info.value.status_code == 400
        assert "Invalid event type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_security_alerts_dict_response(self, endpoints):
        """Test get_security_alerts with dict response."""
        # Arrange
        alerts_data = {
            "alerts": [
                {"id": "alert_001", "type": "security", "severity": "high"},
            ],
            "total_count": 1,
            "critical_count": 1,
        }
        endpoints.alert_engine.get_active_alerts.return_value = alerts_data

        # Act
        result = await endpoints.get_security_alerts()

        # Assert
        assert isinstance(result, AlertSummaryResponse)
        assert result.total_count == 1
        assert result.critical_count == 1

    @pytest.mark.asyncio
    async def test_get_security_alerts_list_response(self, endpoints):
        """Test get_security_alerts with list response."""
        # Arrange
        alerts_data = [
            {"id": "alert_001", "type": "security", "severity": "critical"},
        ]
        endpoints.alert_engine.get_active_alerts.return_value = alerts_data

        # Act
        result = await endpoints.get_security_alerts()

        # Assert
        assert isinstance(result, AlertSummaryResponse)
        assert len(result.active_alerts) == 1
        assert result.total_count == 1

    @pytest.mark.asyncio
    async def test_get_security_alerts_timeout_error(self, endpoints):
        """Test get_security_alerts with TimeoutError."""
        # Arrange
        endpoints.alert_engine.get_active_alerts.side_effect = TimeoutError("Request timed out")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_alerts()

        assert exc_info.value.status_code == 504

    @pytest.mark.asyncio
    async def test_acknowledge_alert_success(self, endpoints):
        """Test successful alert acknowledgment."""
        # Arrange
        alert_id = "alert_123"
        endpoints.alert_engine.acknowledge_alert.return_value = True

        # Act
        result = await endpoints.acknowledge_alert(alert_id)

        # Assert
        assert result["success"] is True
        assert result["alert_id"] == alert_id

    @pytest.mark.asyncio
    async def test_acknowledge_alert_not_found(self, endpoints):
        """Test acknowledge_alert when alert not found."""
        # Arrange
        alert_id = "nonexistent_alert"
        endpoints.alert_engine.acknowledge_alert.return_value = False

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.acknowledge_alert(alert_id)

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_security_statistics_success(self, endpoints):
        """Test successful get_security_statistics."""
        # Arrange
        stats_data = {
            "daily_stats": {"events_count": 500},
            "weekly_trends": {"growth": 0.15},
        }
        endpoints.security_monitor.get_threat_statistics.return_value = stats_data

        # Act
        result = await endpoints.get_security_statistics()

        # Assert
        assert isinstance(result, SecurityStatsResponse)
        assert result.daily_stats["events_count"] == 500

    @pytest.mark.asyncio
    async def test_generate_audit_report_success(self, endpoints):
        """Test successful audit report generation."""
        # Arrange
        report_data = {
            "report_id": "rpt_001",
            "status": "completed",
            "generated_at": datetime.now(UTC).isoformat(),
        }
        endpoints.audit_service.generate_security_report.return_value = report_data

        # Act
        result = await endpoints.generate_audit_report()

        # Assert
        assert result["report_id"] == "rpt_001"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_generate_audit_report_service_error(self, endpoints):
        """Test audit report generation with service error."""
        # Arrange
        endpoints.audit_service.generate_security_report.side_effect = Exception("Report generation failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.generate_audit_report()

        assert exc_info.value.status_code == 500


class TestUtilityFunctions:
    """Test utility functions and helper methods."""

    @pytest.mark.asyncio
    async def test_get_security_service_function(self):
        """Test get_security_service dependency function."""
        # Act
        result = await get_security_service()

        # Assert
        assert isinstance(result, SecurityIntegrationService)


class TestErrorHandlingEdgeCases:
    """Test specific error handling scenarios and edge cases."""

    @pytest.fixture
    def endpoints(self):
        return SecurityDashboardEndpoints(
            security_monitor=AsyncMock(),
            alert_engine=AsyncMock(),
            audit_service=AsyncMock(),
        )

    @pytest.mark.asyncio
    async def test_get_security_events_service_exception(self, endpoints):
        """Test get_security_events when service raises exception."""
        # Arrange
        endpoints.security_monitor.get_recent_events.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_events()

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_security_alerts_connection_error(self, endpoints):
        """Test get_security_alerts with ConnectionError."""
        # Arrange
        endpoints.alert_engine.get_active_alerts.side_effect = ConnectionError("Service unavailable")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_alerts()

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_acknowledge_alert_service_exception(self, endpoints):
        """Test acknowledge_alert when service raises exception."""
        # Arrange
        endpoints.alert_engine.acknowledge_alert.side_effect = Exception("Service error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.acknowledge_alert("alert_123")

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_get_security_statistics_service_exception(self, endpoints):
        """Test get_security_statistics when service raises exception."""
        # Arrange
        endpoints.security_monitor.get_threat_statistics.side_effect = Exception("Stats service error")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await endpoints.get_security_statistics()

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_generate_audit_report_with_parameters(self, endpoints):
        """Test generate_audit_report with specific parameters."""
        # Arrange
        start_date = datetime.now(UTC) - timedelta(days=7)
        end_date = datetime.now(UTC)
        endpoints.audit_service.generate_security_report.return_value = {
            "report_id": "rpt_002",
            "status": "generated",
        }

        # Act
        result = await endpoints.generate_audit_report(
            start_date=start_date,
            end_date=end_date,
            report_format="detailed",
        )

        # Assert
        assert result["report_id"] == "rpt_002"
        endpoints.audit_service.generate_security_report.assert_called_once_with(
            start_date=start_date,
            end_date=end_date,
            report_format="detailed",
        )


class TestModelValidationAndEdgeCases:
    """Test response model validation and edge cases."""

    def test_security_metrics_response_model(self):
        """Test SecurityMetricsResponse model validation."""
        # Arrange
        data = {
            "timestamp": datetime.now(UTC),
            "total_events_today": 100,
            "total_events_week": 500,
            "event_rate_per_hour": 12.5,
            "total_alerts_today": 25,
            "critical_alerts_today": 5,
            "alerts_acknowledged": 20,
            "average_processing_time_ms": 45.2,
            "system_health_score": 95.5,
            "service_availability": {"logger": True, "monitor": True},
            "suspicious_activities_today": 8,
            "top_risk_users": ["user1", "user2"],
            "top_threat_ips": ["192.168.1.100", "10.0.0.50"],
        }

        # Act
        response = SecurityMetricsResponse(**data)

        # Assert
        assert response.total_events_today == 100
        assert response.system_health_score == 95.5
        assert len(response.top_risk_users) == 2

    def test_alert_summary_response_model(self):
        """Test AlertSummaryResponse model validation."""
        # Arrange
        data = {
            "active_alerts": [
                {"alert_id": "alert_001", "title": "Test Alert", "severity": "high"},
            ],
            "total_count": 1,
            "critical_count": 1,
            "timestamp": datetime.now(UTC),
        }

        # Act
        response = AlertSummaryResponse(**data)

        # Assert
        assert response.total_count == 1
        assert response.critical_count == 1
        assert len(response.active_alerts) == 1

    def test_alert_item_model_extra_fields(self):
        """Test AlertItem model allows extra fields."""
        # Arrange
        data = {
            "alert_id": "alert_001",
            "alert_type": "security",
            "severity": "high",
            "title": "Test Alert",
            "timestamp": datetime.now(UTC),
            "status": "active",
            "extra_field": "extra_value",  # Extra field
            "another_extra": 123,
        }

        # Act
        alert = AlertItem(**data)

        # Assert
        assert alert.alert_id == "alert_001"
        assert alert.severity == "high"
        assert alert.extra_field == "extra_value"
        assert alert.another_extra == 123
