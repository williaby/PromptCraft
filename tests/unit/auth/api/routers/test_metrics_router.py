"""Comprehensive tests for metrics_router.py.

Tests system metrics and performance monitoring endpoints.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.api.routers.metrics_router import (
    SecurityMetricsResponse,
    get_security_service,
    router,
)
from src.auth.services.security_integration import SecurityIntegrationService


@pytest.fixture
def mock_security_service():
    """Mock security integration service."""
    return AsyncMock(spec=SecurityIntegrationService)


@pytest.fixture
def test_app(mock_security_service):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_security_service] = lambda: mock_security_service
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def sample_comprehensive_metrics():
    """Sample comprehensive metrics data."""
    return {
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
            "detector_healthy": False,  # One service unhealthy
        },
    }


@pytest.fixture
def sample_degraded_metrics():
    """Sample metrics with degraded performance."""
    return {
        "integration": {
            "total_events_processed": 2500,
            "total_alerts_generated": 125,
            "average_processing_time_ms": 85.2,  # High processing time
            "total_suspicious_activities": 28,
        },
        "service_health": {
            "logger_healthy": False,  # Multiple services unhealthy
            "monitor_healthy": False,
            "alert_engine_healthy": True,
            "detector_healthy": True,
        },
    }


class TestSecurityMetricsResponse:
    """Test SecurityMetricsResponse model."""

    def test_security_metrics_response_creation(self):
        """Test creating security metrics response."""
        timestamp = datetime.now(UTC)
        metrics = SecurityMetricsResponse(
            timestamp=timestamp,
            total_events_today=1250,
            total_events_week=8750,
            event_rate_per_hour=52.0,
            total_alerts_today=45,
            critical_alerts_today=9,
            alerts_acknowledged=32,
            average_processing_time_ms=35.5,
            system_health_score=85.0,
            service_availability={
                "logger": True,
                "monitor": True,
                "alert_engine": False,
                "detector": True,
            },
            suspicious_activities_today=12,
            top_risk_users=["user_1", "user_2", "user_3"],
            top_threat_ips=["192.168.1.100", "10.0.0.50"],
        )

        assert metrics.total_events_today == 1250
        assert metrics.event_rate_per_hour == 52.0
        assert metrics.system_health_score == 85.0
        assert len(metrics.service_availability) == 4
        assert metrics.service_availability["alert_engine"] is False

    def test_security_metrics_response_validation(self):
        """Test security metrics response field validation."""
        timestamp = datetime.now(UTC)

        # Test with minimum values
        metrics = SecurityMetricsResponse(
            timestamp=timestamp,
            total_events_today=0,
            total_events_week=0,
            event_rate_per_hour=0.0,
            total_alerts_today=0,
            critical_alerts_today=0,
            alerts_acknowledged=0,
            average_processing_time_ms=0.0,
            system_health_score=0.0,
            service_availability={},
            suspicious_activities_today=0,
            top_risk_users=[],
            top_threat_ips=[],
        )

        assert metrics.total_events_today == 0
        assert metrics.system_health_score == 0.0
        assert len(metrics.service_availability) == 0

    def test_security_metrics_response_large_values(self):
        """Test security metrics response with large values."""
        timestamp = datetime.now(UTC)

        # Test with large realistic values
        metrics = SecurityMetricsResponse(
            timestamp=timestamp,
            total_events_today=50000,
            total_events_week=350000,
            event_rate_per_hour=2083.33,
            total_alerts_today=500,
            critical_alerts_today=100,
            alerts_acknowledged=350,
            average_processing_time_ms=150.75,
            system_health_score=100.0,
            service_availability={
                "logger": True,
                "monitor": True,
                "alert_engine": True,
                "detector": True,
                "audit": True,
            },
            suspicious_activities_today=85,
            top_risk_users=[f"user_{i}" for i in range(1, 11)],  # 10 users
            top_threat_ips=[f"10.0.0.{i}" for i in range(1, 21)],  # 20 IPs
        )

        assert metrics.total_events_today == 50000
        assert metrics.event_rate_per_hour == 2083.33
        assert len(metrics.top_risk_users) == 10
        assert len(metrics.top_threat_ips) == 20


class TestMetricsRouter:
    """Test metrics router functionality."""

    def test_router_configuration(self):
        """Test router is properly configured."""
        assert router.prefix == "/metrics"
        assert "metrics" in router.tags

    @pytest.mark.asyncio
    async def test_get_security_metrics_success(
        self,
        test_client,
        mock_security_service,
        sample_comprehensive_metrics,
    ):
        """Test successful security metrics retrieval."""
        mock_security_service.get_comprehensive_metrics.return_value = sample_comprehensive_metrics

        response = test_client.get("/metrics/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_events_today"] == 1250
        assert data["total_events_week"] == 8750  # 1250 * 7
        assert abs(data["event_rate_per_hour"] - 52.0833) < 0.001  # 1250 / 24 (rounded)
        assert data["total_alerts_today"] == 45
        assert data["critical_alerts_today"] == 9  # 45 * 0.2
        assert data["alerts_acknowledged"] == 31  # 45 * 0.7 (rounded down)
        assert data["average_processing_time_ms"] == 35.5
        assert data["suspicious_activities_today"] == 12
        assert len(data["top_risk_users"]) == 5
        assert len(data["top_threat_ips"]) == 5

    @pytest.mark.asyncio
    async def test_get_security_metrics_with_custom_hours(
        self,
        test_client,
        mock_security_service,
        sample_comprehensive_metrics,
    ):
        """Test security metrics with custom hours parameter."""
        mock_security_service.get_comprehensive_metrics.return_value = sample_comprehensive_metrics

        response = test_client.get("/metrics/?hours_back=48")

        assert response.status_code == 200
        data = response.json()
        assert "timestamp" in data
        assert data["total_events_today"] == 1250
        # Verify the service was called (though response doesn't change based on hours_back in current implementation)

    @pytest.mark.asyncio
    async def test_get_security_metrics_health_score_calculation(
        self,
        test_client,
        mock_security_service,
        sample_degraded_metrics,
    ):
        """Test system health score calculation with degraded services."""
        mock_security_service.get_comprehensive_metrics.return_value = sample_degraded_metrics

        response = test_client.get("/metrics/")

        assert response.status_code == 200
        data = response.json()

        # Verify health score calculation
        # Start with 100, subtract for:
        # - High processing time (85.2 > 50): subtract min(30, (85.2-50)/10*5) = min(30, 17.6) = 17.6
        # - logger_healthy=False: subtract 20
        # - monitor_healthy=False: subtract 15
        # Total: 100 - 17.6 - 20 - 15 = 47.4
        expected_health_score = max(0, 100 - 17.6 - 20 - 15)
        assert abs(data["system_health_score"] - expected_health_score) < 1.0  # Allow small rounding differences

        # Verify service availability
        assert data["service_availability"]["logger"] is False
        assert data["service_availability"]["monitor"] is False
        assert data["service_availability"]["alert_engine"] is True
        assert data["service_availability"]["detector"] is True

    @pytest.mark.asyncio
    async def test_get_security_metrics_zero_events(
        self,
        test_client,
        mock_security_service,
    ):
        """Test security metrics with zero events."""
        zero_metrics = {
            "integration": {
                "total_events_processed": 0,
                "total_alerts_generated": 0,
                "average_processing_time_ms": 0.0,
                "total_suspicious_activities": 0,
            },
            "service_health": {
                "logger_healthy": True,
                "monitor_healthy": True,
                "alert_engine_healthy": True,
                "detector_healthy": True,
            },
        }

        mock_security_service.get_comprehensive_metrics.return_value = zero_metrics

        response = test_client.get("/metrics/")

        assert response.status_code == 200
        data = response.json()
        assert data["total_events_today"] == 0
        assert data["total_events_week"] == 0
        assert data["event_rate_per_hour"] == 0  # Should handle division by zero
        assert data["total_alerts_today"] == 0
        assert data["system_health_score"] == 100.0  # Should be perfect with all services healthy

    @pytest.mark.asyncio
    async def test_get_security_metrics_service_error(
        self,
        test_client,
        mock_security_service,
    ):
        """Test security metrics when service raises exception."""
        mock_security_service.get_comprehensive_metrics.side_effect = Exception("Service unavailable")

        response = test_client.get("/metrics/")

        assert response.status_code == 500
        assert "Failed to retrieve security metrics" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_security_metrics_query_parameter_validation(self, test_client):
        """Test query parameter validation."""
        # Test hours_back too small
        response = test_client.get("/metrics/?hours_back=0")
        assert response.status_code == 422  # Validation error

        # Test hours_back too large
        response = test_client.get("/metrics/?hours_back=200")
        assert response.status_code == 422  # Validation error

        # Test valid range
        response = test_client.get("/metrics/?hours_back=72")
        # Should succeed (assuming service is properly mocked)


class TestExportSecurityMetrics:
    """Test security metrics export functionality."""

    @pytest.mark.asyncio
    async def test_export_metrics_json_format(
        self,
        test_client,
        mock_security_service,
        sample_comprehensive_metrics,
    ):
        """Test exporting metrics in JSON format."""
        mock_security_service.get_comprehensive_metrics.return_value = sample_comprehensive_metrics

        response = test_client.get("/metrics/export?format=json")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert "timestamp" in data
        assert data["total_events_today"] == 1250

    @pytest.mark.asyncio
    async def test_export_metrics_csv_format(
        self,
        test_client,
        mock_security_service,
        sample_comprehensive_metrics,
    ):
        """Test exporting metrics in CSV format."""
        mock_security_service.get_comprehensive_metrics.return_value = sample_comprehensive_metrics

        response = test_client.get("/metrics/export?format=csv")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "security_metrics.csv" in response.headers["content-disposition"]

        # Verify CSV content structure
        csv_content = response.content.decode("utf-8")
        lines = csv_content.strip().split("\n")
        assert len(lines) == 2  # Header + data row

        header = lines[0]
        assert "timestamp" in header
        assert "total_events_today" in header
        assert "system_health_score" in header

        data_row = lines[1]
        assert "1250" in data_row  # total_events_today
        assert "45" in data_row  # total_alerts_today

    @pytest.mark.asyncio
    async def test_export_metrics_with_custom_hours(
        self,
        test_client,
        mock_security_service,
        sample_comprehensive_metrics,
    ):
        """Test exporting metrics with custom hours parameter."""
        mock_security_service.get_comprehensive_metrics.return_value = sample_comprehensive_metrics

        response = test_client.get("/metrics/export?format=json&hours_back=48")

        assert response.status_code == 200
        data = response.json()
        assert data["total_events_today"] == 1250

    @pytest.mark.asyncio
    async def test_export_metrics_invalid_format(self, test_client):
        """Test exporting metrics with invalid format."""
        response = test_client.get("/metrics/export?format=xml")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_export_metrics_service_error(
        self,
        test_client,
        mock_security_service,
    ):
        """Test export when service raises exception."""
        mock_security_service.get_comprehensive_metrics.side_effect = Exception("Export failed")

        response = test_client.get("/metrics/export?format=json")

        assert response.status_code == 500
        assert "Failed to export security metrics" in response.json()["detail"]


class TestMetricsIntegration:
    """Test metrics router integration scenarios."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_metrics_endpoint_performance(
        self,
        test_client,
        mock_security_service,
        sample_comprehensive_metrics,
    ):
        """Test metrics endpoint performance."""
        mock_security_service.get_comprehensive_metrics.return_value = sample_comprehensive_metrics

        import time

        start_time = time.time()
        response = test_client.get("/metrics/")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_export_endpoint_performance(
        self,
        test_client,
        mock_security_service,
        sample_comprehensive_metrics,
    ):
        """Test export endpoint performance."""
        mock_security_service.get_comprehensive_metrics.return_value = sample_comprehensive_metrics

        import time

        start_time = time.time()
        response = test_client.get("/metrics/export?format=csv")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds

    @pytest.mark.asyncio
    async def test_metrics_consistency_between_endpoints(
        self,
        test_client,
        mock_security_service,
        sample_comprehensive_metrics,
    ):
        """Test that metrics are consistent between main and export endpoints."""
        mock_security_service.get_comprehensive_metrics.return_value = sample_comprehensive_metrics

        # Get metrics from main endpoint
        main_response = test_client.get("/metrics/")
        main_data = main_response.json()

        # Get metrics from export endpoint (JSON format)
        export_response = test_client.get("/metrics/export?format=json")
        export_data = export_response.json()

        # Compare key metrics
        assert main_data["total_events_today"] == export_data["total_events_today"]
        assert main_data["total_alerts_today"] == export_data["total_alerts_today"]
        assert main_data["system_health_score"] == export_data["system_health_score"]
        assert main_data["suspicious_activities_today"] == export_data["suspicious_activities_today"]

    @pytest.mark.asyncio
    async def test_extreme_metric_values(
        self,
        test_client,
        mock_security_service,
    ):
        """Test handling of extreme metric values."""
        extreme_metrics = {
            "integration": {
                "total_events_processed": 1000000,  # Very high event count
                "total_alerts_generated": 50000,  # Very high alert count
                "average_processing_time_ms": 500.0,  # Very slow processing
                "total_suspicious_activities": 10000,
            },
            "service_health": {
                "logger_healthy": False,
                "monitor_healthy": False,
                "alert_engine_healthy": False,
                "detector_healthy": False,  # All services unhealthy
            },
        }

        mock_security_service.get_comprehensive_metrics.return_value = extreme_metrics

        response = test_client.get("/metrics/")

        assert response.status_code == 200
        data = response.json()

        assert data["total_events_today"] == 1000000
        assert abs(data["event_rate_per_hour"] - 41666.666666666664) < 0.01  # 1000000 / 24

        # Health score should be 10.0 (100 - 30 for processing time - 20 logger - 15 monitor - 15 alert_engine - 10 detector)
        assert data["system_health_score"] == 10.0

        # All services should be unavailable
        assert all(status is False for status in data["service_availability"].values())

    @pytest.mark.asyncio
    async def test_metrics_with_edge_case_calculations(
        self,
        test_client,
        mock_security_service,
    ):
        """Test metrics calculations with edge cases."""
        edge_case_metrics = {
            "integration": {
                "total_events_processed": 1,  # Minimum meaningful value
                "total_alerts_generated": 1,
                "average_processing_time_ms": 49.99,  # Just under the 50ms threshold
                "total_suspicious_activities": 1,
            },
            "service_health": {
                "logger_healthy": True,
                "monitor_healthy": True,
                "alert_engine_healthy": True,
                "detector_healthy": True,
            },
        }

        mock_security_service.get_comprehensive_metrics.return_value = edge_case_metrics

        response = test_client.get("/metrics/")

        assert response.status_code == 200
        data = response.json()

        assert data["total_events_today"] == 1
        assert data["total_events_week"] == 7
        assert abs(data["event_rate_per_hour"] - (1 / 24)) < 0.001  # Approximately 0.042

        # Health score should be 100 (all services healthy, processing time under threshold)
        assert data["system_health_score"] == 100.0

        assert data["critical_alerts_today"] == 0  # int(1 * 0.2) = 0
        assert data["alerts_acknowledged"] == 0  # int(1 * 0.7) = 0
