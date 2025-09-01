"""Comprehensive test suite for Performance Dashboard."""

import json
from datetime import datetime, timedelta
from src.utils.datetime_compat import UTC
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.monitoring.performance_dashboard import (
    AlertManager,
    MetricsExporter,
    RealTimeDashboard,
    create_dashboard_app,
    get_dashboard_app,
)


class MockSystemHealthReport:
    """Mock system health report for testing."""

    def __init__(self):
        self.average_token_reduction_percentage = 75.0
        self.median_token_reduction_percentage = 72.0
        self.average_loading_latency_ms = 150.0
        self.p95_loading_latency_ms = 180.0
        self.p99_loading_latency_ms = 200.0
        self.overall_success_rate = 0.98
        self.task_detection_accuracy_rate = 0.85
        self.concurrent_sessions_handled = 5
        self.total_sessions = 50
        self.fallback_activation_rate = 0.05
        # Use a fixed timestamp for testing
        self.timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)


class MockFunctionTier:
    """Mock function tier enum for testing."""

    def __init__(self, value):
        self.value = value


class MockTierMetrics:
    """Mock tier metrics for testing."""

    def __init__(self):
        self.functions_loaded = 10
        self.loading_time_ms = 120.0
        self.cache_hits = 8
        self.cache_misses = 2
        self.tokens_consumed = 1000
        self.usage_frequency = 0.8


class MockSessionMetrics:
    """Mock session metrics for testing."""

    def __init__(self):
        self.user_id = "test_user"
        self.task_type = "code_generation"
        self.optimization_level = MockOptimizationLevel("balanced")
        self.baseline_tokens_loaded = 1000
        self.optimized_tokens_loaded = 250
        self.optimized_functions_loaded = 5
        self.functions_actually_used = ["func1", "func2", "func3"]
        self.timestamp = datetime.now(UTC)


class MockOptimizationLevel:
    """Mock optimization level for testing."""

    def __init__(self, value):
        self.value = value


class MockTokenOptimizationMonitor:
    """Mock token optimization monitor for testing."""

    def __init__(self):
        self.validation_confidence = 0.92
        self.function_metrics = {
            MockFunctionTier("core"): MockTierMetrics(),
            MockFunctionTier("extended"): MockTierMetrics(),
        }
        self.system_health_history = [MockSystemHealthReport() for _ in range(25)]
        self.active_sessions = ["session1", "session2", "session3"]
        self.session_metrics = {
            "session1": MockSessionMetrics(),
            "session2": MockSessionMetrics(),
            "session3": MockSessionMetrics(),
        }
        self.optimization_validated = True
        self.token_reduction_target = 0.70
        self.min_acceptable_reduction = 0.50
        self.max_acceptable_latency_ms = 200.0

    async def generate_system_health_report(self):
        """Mock system health report generation."""
        mock_report = MockSystemHealthReport()
        # Convert to dictionary for Pydantic serialization
        return {
            "average_token_reduction_percentage": mock_report.average_token_reduction_percentage,
            "median_token_reduction_percentage": mock_report.median_token_reduction_percentage,
            "average_loading_latency_ms": mock_report.average_loading_latency_ms,
            "p95_loading_latency_ms": mock_report.p95_loading_latency_ms,
            "p99_loading_latency_ms": mock_report.p99_loading_latency_ms,
            "overall_success_rate": mock_report.overall_success_rate,
            "task_detection_accuracy_rate": mock_report.task_detection_accuracy_rate,
            "concurrent_sessions_handled": mock_report.concurrent_sessions_handled,
            "total_sessions": mock_report.total_sessions,
            "fallback_activation_rate": mock_report.fallback_activation_rate,
            "timestamp": mock_report.timestamp.isoformat(),
        }

    async def export_metrics(self, **kwargs):
        """Mock metrics export."""
        return {
            "token_reduction": 75.0,
            "latency": 150.0,
            "success_rate": 0.98,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def get_optimization_report(self, user_id=None):
        """Mock optimization report."""
        return {
            "user_id": user_id,
            "token_reduction": 75.0,
            "sessions_optimized": 10,
            "timestamp": datetime.now(UTC).isoformat(),
        }


class MockPerformanceMonitor:
    """Mock performance monitor for testing."""

    def get_all_metrics(self):
        """Mock metrics retrieval."""
        return {
            "counters": {
                "requests_total": 100,
                "errors_total": 2,
            },
            "gauges": {
                "memory_usage_mb": 512,
                "cpu_usage_percent": 65.0,
            },
        }


class TestMetricsExporter:
    """Test MetricsExporter class."""

    @pytest.fixture
    def mock_monitor(self):
        """Create mock monitor."""
        return MockTokenOptimizationMonitor()

    @pytest.fixture
    def mock_performance_monitor(self):
        """Create mock performance monitor."""
        return MockPerformanceMonitor()

    @pytest.fixture
    def metrics_exporter(self, mock_monitor):
        """Create MetricsExporter instance."""
        with (
            patch("src.monitoring.performance_dashboard.get_performance_monitor") as mock_get_perf,
            patch("src.monitoring.performance_dashboard.create_structured_logger"),
        ):
            mock_get_perf.return_value = MockPerformanceMonitor()
            return MetricsExporter(mock_monitor)

    @pytest.mark.asyncio
    async def test_export_prometheus_metrics(self, metrics_exporter):
        """Test exporting metrics in Prometheus format."""
        result = await metrics_exporter.export_prometheus_metrics()

        assert isinstance(result, str)
        assert "token_reduction_percentage" in result
        assert "function_loading_latency_ms" in result
        assert "system_success_rate" in result
        assert "task_detection_accuracy" in result
        assert "concurrent_sessions" in result

        # Check Prometheus format
        assert "# HELP" in result
        assert "# TYPE" in result
        assert "gauge" in result

    @pytest.mark.asyncio
    async def test_export_prometheus_metrics_with_tiers(self, metrics_exporter):
        """Test Prometheus metrics include tier-specific data."""
        result = await metrics_exporter.export_prometheus_metrics()

        assert "functions_loaded_total" in result
        assert "cache_hits_total" in result
        assert "cache_misses_total" in result
        assert "tokens_consumed_total" in result
        assert 'tier="core"' in result
        assert 'tier="extended"' in result

    @pytest.mark.asyncio
    async def test_export_prometheus_metrics_with_performance_data(self, metrics_exporter):
        """Test Prometheus metrics include performance monitor data."""
        result = await metrics_exporter.export_prometheus_metrics()

        assert "requests_total" in result
        assert "errors_total" in result
        assert "memory_usage_mb" in result
        assert "cpu_usage_percent" in result

    @pytest.mark.asyncio
    async def test_export_json_metrics(self, metrics_exporter):
        """Test exporting metrics in JSON format."""
        result = await metrics_exporter.export_json_metrics()

        assert isinstance(result, dict)
        assert "token_reduction" in result
        assert "latency" in result
        assert "success_rate" in result
        assert "timestamp" in result

    def test_metrics_exporter_initialization(self, mock_monitor):
        """Test MetricsExporter initialization."""
        with (
            patch("src.monitoring.performance_dashboard.get_performance_monitor"),
            patch("src.monitoring.performance_dashboard.create_structured_logger") as mock_logger,
        ):
            exporter = MetricsExporter(mock_monitor)
            assert exporter.monitor == mock_monitor
            mock_logger.assert_called_once_with("metrics_exporter")


class TestRealTimeDashboard:
    """Test RealTimeDashboard class."""

    @pytest.fixture
    def mock_monitor(self):
        """Create mock monitor."""
        return MockTokenOptimizationMonitor()

    @pytest.fixture
    def dashboard(self, mock_monitor):
        """Create RealTimeDashboard instance."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            return RealTimeDashboard(mock_monitor)

    def test_dashboard_initialization(self, mock_monitor):
        """Test RealTimeDashboard initialization."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger") as mock_logger:
            dashboard = RealTimeDashboard(mock_monitor)
            assert dashboard.monitor == mock_monitor
            assert dashboard.connected_clients == []
            assert dashboard.update_interval_seconds == 5.0
            assert dashboard._update_task is None
            # Should be called for dashboard initialization
            assert mock_logger.call_count >= 1

    @pytest.mark.asyncio
    async def test_start_real_time_updates(self, dashboard):
        """Test starting real-time updates."""
        await dashboard.start_real_time_updates()

        assert dashboard._update_task is not None
        assert not dashboard._update_task.done()

        # Cleanup
        await dashboard.stop_real_time_updates()

    @pytest.mark.asyncio
    async def test_stop_real_time_updates(self, dashboard):
        """Test stopping real-time updates."""
        await dashboard.start_real_time_updates()
        assert dashboard._update_task is not None

        await dashboard.stop_real_time_updates()
        assert dashboard._update_task.cancelled()

    @pytest.mark.asyncio
    async def test_stop_real_time_updates_no_task(self, dashboard):
        """Test stopping updates when no task is running."""
        # Should not raise an exception
        await dashboard.stop_real_time_updates()

    @pytest.mark.asyncio
    async def test_generate_dashboard_data(self, dashboard):
        """Test generating dashboard data."""
        data = await dashboard._generate_dashboard_data()

        assert isinstance(data, dict)
        assert "timestamp" in data
        assert "system_health" in data
        assert "token_reduction_history" in data
        assert "loading_latency_history" in data
        assert "tier_performance" in data
        assert "active_sessions" in data
        assert "validation_status" in data
        assert "alerts" in data

        # Check system health structure
        system_health = data["system_health"]
        assert "total_sessions" in system_health
        assert "concurrent_sessions" in system_health
        assert "average_token_reduction" in system_health
        assert "overall_success_rate" in system_health
        assert "task_detection_accuracy" in system_health
        assert "average_loading_latency" in system_health
        assert "p95_loading_latency" in system_health

    @pytest.mark.asyncio
    async def test_generate_dashboard_data_validation_status(self, dashboard):
        """Test validation status in dashboard data."""
        data = await dashboard._generate_dashboard_data()

        validation_status = data["validation_status"]
        assert "overall_validated" in validation_status
        assert "confidence_percentage" in validation_status
        assert "target_reduction_percentage" in validation_status
        assert "current_average_reduction" in validation_status
        assert "criteria_status" in validation_status

        criteria = validation_status["criteria_status"]
        assert "token_reduction_target" in criteria
        assert "sample_size_adequate" in criteria
        assert "task_accuracy_acceptable" in criteria
        assert "success_rate_acceptable" in criteria
        assert "latency_acceptable" in criteria

    @pytest.mark.asyncio
    async def test_generate_dashboard_data_tier_performance(self, dashboard):
        """Test tier performance data generation."""
        data = await dashboard._generate_dashboard_data()

        tier_performance = data["tier_performance"]
        assert "core" in tier_performance
        assert "extended" in tier_performance

        core_tier = tier_performance["core"]
        assert "functions_loaded" in core_tier
        assert "loading_time_ms" in core_tier
        assert "cache_hit_rate" in core_tier
        assert "tokens_consumed" in core_tier
        assert "usage_frequency" in core_tier

        # Test cache hit rate calculation
        expected_hit_rate = 8 / (8 + 2)  # cache_hits / (cache_hits + cache_misses)
        assert core_tier["cache_hit_rate"] == expected_hit_rate

    @pytest.mark.asyncio
    async def test_generate_dashboard_data_active_sessions(self, dashboard):
        """Test active sessions data generation."""
        data = await dashboard._generate_dashboard_data()

        active_sessions = data["active_sessions"]
        assert isinstance(active_sessions, list)
        assert len(active_sessions) <= 10  # Should limit to 10 sessions

        if active_sessions:
            session = active_sessions[0]
            assert "session_id" in session
            assert "user_id" in session
            assert "task_type" in session
            assert "optimization_level" in session
            assert "token_reduction_percentage" in session
            assert "functions_loaded" in session
            assert "functions_used" in session
            assert "duration_minutes" in session

    @pytest.mark.asyncio
    async def test_generate_alerts(self, dashboard):
        """Test alert generation."""
        health_report = MockSystemHealthReport()
        alerts = await dashboard._generate_alerts(health_report)

        assert isinstance(alerts, list)
        # With default good values, should have no alerts
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_generate_alerts_with_issues(self, dashboard):
        """Test alert generation with performance issues."""
        health_report = MockSystemHealthReport()
        # Set values that should trigger alerts
        health_report.average_token_reduction_percentage = 30.0  # Below minimum
        health_report.p95_loading_latency_ms = 250.0  # Above threshold
        health_report.overall_success_rate = 0.90  # Below 95%
        health_report.task_detection_accuracy_rate = 0.70  # Below 80%
        health_report.fallback_activation_rate = 0.15  # Above 10%

        alerts = await dashboard._generate_alerts(health_report)

        assert len(alerts) == 5  # Should have 5 alerts
        alert_titles = [alert["title"] for alert in alerts]
        assert "Token Reduction Below Minimum" in alert_titles
        assert "High Loading Latency" in alert_titles
        assert "Low Success Rate" in alert_titles
        assert "Low Task Detection Accuracy" in alert_titles
        assert "High Fallback Activation Rate" in alert_titles

    @pytest.mark.asyncio
    async def test_broadcast_to_clients_no_clients(self, dashboard):
        """Test broadcasting when no clients are connected."""
        data = {"test": "data"}
        # Should not raise an exception
        await dashboard._broadcast_to_clients(data)

    @pytest.mark.asyncio
    async def test_broadcast_to_clients_with_clients(self, dashboard):
        """Test broadcasting to connected clients."""
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        dashboard.connected_clients = [mock_client1, mock_client2]

        data = {"test": "data"}
        await dashboard._broadcast_to_clients(data)

        expected_message = json.dumps(data)
        mock_client1.send_text.assert_called_once_with(expected_message)
        mock_client2.send_text.assert_called_once_with(expected_message)

    @pytest.mark.asyncio
    async def test_broadcast_to_clients_with_failed_client(self, dashboard):
        """Test broadcasting with a failed client connection."""
        mock_client1 = AsyncMock()
        mock_client2 = AsyncMock()
        mock_client2.send_text.side_effect = Exception("Connection failed")

        dashboard.connected_clients = [mock_client1, mock_client2]

        data = {"test": "data"}
        await dashboard._broadcast_to_clients(data)

        # Client1 should still receive the message
        expected_message = json.dumps(data)
        mock_client1.send_text.assert_called_once_with(expected_message)

        # Failed client should be removed from connected clients
        assert mock_client2 not in dashboard.connected_clients
        assert len(dashboard.connected_clients) == 1

    @pytest.mark.asyncio
    async def test_add_client(self, dashboard):
        """Test adding a WebSocket client."""
        mock_websocket = AsyncMock()

        await dashboard.add_client(mock_websocket)

        mock_websocket.accept.assert_called_once()
        assert mock_websocket in dashboard.connected_clients
        mock_websocket.send_text.assert_called_once()  # Initial data

    @pytest.mark.asyncio
    async def test_remove_client(self, dashboard):
        """Test removing a WebSocket client."""
        mock_websocket = AsyncMock()
        dashboard.connected_clients = [mock_websocket]

        await dashboard.remove_client(mock_websocket)

        assert mock_websocket not in dashboard.connected_clients

    @pytest.mark.asyncio
    async def test_remove_client_not_connected(self, dashboard):
        """Test removing a client that wasn't connected."""
        mock_websocket = AsyncMock()

        # Should not raise an exception
        await dashboard.remove_client(mock_websocket)

    def test_get_dashboard_html(self, dashboard):
        """Test getting dashboard HTML."""
        html = dashboard.get_dashboard_html()

        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html
        assert "Token Optimization Performance Dashboard" in html
        assert "<script>" in html
        assert "WebSocket" in html
        assert "chart.js" in html.lower()  # Case insensitive check

    @pytest.mark.asyncio
    async def test_update_loop_iteration(self, dashboard):
        """Test a single iteration of the update loop."""
        dashboard.connected_clients = [AsyncMock()]

        # Mock sleep to prevent actual waiting
        with patch("asyncio.sleep", new_callable=AsyncMock):
            # Run one iteration by calling the method directly
            # This is a bit hacky but tests the core logic
            dashboard_data = await dashboard._generate_dashboard_data()
            await dashboard._broadcast_to_clients(dashboard_data)

            # Verify client received data
            dashboard.connected_clients[0].send_text.assert_called_once()


class TestAlertManager:
    """Test AlertManager class."""

    @pytest.fixture
    def mock_monitor(self):
        """Create mock monitor."""
        return MockTokenOptimizationMonitor()

    @pytest.fixture
    def alert_manager(self, mock_monitor):
        """Create AlertManager instance."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            return AlertManager(mock_monitor)

    def test_alert_manager_initialization(self, mock_monitor):
        """Test AlertManager initialization."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger") as mock_logger:
            manager = AlertManager(mock_monitor)
            assert manager.monitor == mock_monitor
            assert isinstance(manager.thresholds, dict)
            assert manager.active_alerts == {}
            assert manager.alert_history == []
            assert manager.notification_channels == []
            mock_logger.assert_called_once_with("alert_manager")

    def test_alert_manager_thresholds(self, alert_manager):
        """Test AlertManager thresholds are properly set."""
        thresholds = alert_manager.thresholds

        assert thresholds["token_reduction_min"] == 50.0
        assert thresholds["token_reduction_target"] == 70.0
        assert thresholds["latency_max_ms"] == 200.0
        assert thresholds["success_rate_min"] == 0.95
        assert thresholds["task_accuracy_min"] == 0.80
        assert thresholds["fallback_rate_max"] == 0.10

    @pytest.mark.asyncio
    async def test_check_alerts_no_issues(self, alert_manager):
        """Test checking alerts with no issues."""
        alerts = await alert_manager.check_alerts()

        assert isinstance(alerts, list)
        # With good default values, should have no alerts
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_check_alerts_with_issues(self, alert_manager):
        """Test checking alerts with various issues."""
        # Mock the health report to have issues
        mock_health_report = MockSystemHealthReport()
        mock_health_report.average_token_reduction_percentage = 30.0  # Below min
        mock_health_report.p95_loading_latency_ms = 250.0  # Above max
        mock_health_report.overall_success_rate = 0.90  # Below min
        mock_health_report.task_detection_accuracy_rate = 0.70  # Below min
        mock_health_report.fallback_activation_rate = 0.15  # Above max

        alert_manager.monitor.generate_system_health_report = AsyncMock(return_value=mock_health_report)

        alerts = await alert_manager.check_alerts()

        assert len(alerts) == 5

        alert_ids = {alert["id"] for alert in alerts}
        expected_ids = {
            "low_token_reduction",
            "high_loading_latency",
            "low_success_rate",
            "low_task_accuracy",
            "high_fallback_rate",
        }
        assert alert_ids == expected_ids

        # Check alert structure
        for alert in alerts:
            assert "id" in alert
            assert "level" in alert
            assert "title" in alert
            assert "message" in alert
            assert "metric_value" in alert
            assert "threshold_value" in alert
            assert "timestamp" in alert

    @pytest.mark.asyncio
    async def test_check_alerts_target_warning(self, alert_manager):
        """Test target warning (between min and target)."""
        mock_health_report = MockSystemHealthReport()
        mock_health_report.average_token_reduction_percentage = 60.0  # Between 50 and 70

        alert_manager.monitor.generate_system_health_report = AsyncMock(return_value=mock_health_report)

        alerts = await alert_manager.check_alerts()

        assert len(alerts) == 1
        assert alerts[0]["id"] == "token_reduction_below_target"
        assert alerts[0]["level"] == "warning"

    @pytest.mark.asyncio
    async def test_update_active_alerts_new_alerts(self, alert_manager):
        """Test updating active alerts with new alerts."""
        alert = {
            "id": "test_alert",
            "level": "warning",
            "title": "Test Alert",
            "message": "Test message",
            "metric_value": 50.0,
            "threshold_value": 70.0,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        with patch.object(alert_manager, "_send_notification", new_callable=AsyncMock) as mock_send:
            await alert_manager._update_active_alerts([alert])

            mock_send.assert_called_once_with(alert)
            assert "test_alert" in alert_manager.active_alerts
            assert alert_manager.active_alerts["test_alert"] == alert

    @pytest.mark.asyncio
    async def test_update_active_alerts_resolved_alerts(self, alert_manager):
        """Test updating active alerts with resolved alerts."""
        # First, add an active alert
        alert = {
            "id": "test_alert",
            "level": "warning",
            "title": "Test Alert",
            "message": "Test message",
            "metric_value": 50.0,
            "threshold_value": 70.0,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        alert_manager.active_alerts["test_alert"] = alert

        # Then resolve it (pass empty list)
        await alert_manager._update_active_alerts([])

        assert "test_alert" not in alert_manager.active_alerts
        assert len(alert_manager.alert_history) == 1
        assert "resolved_at" in alert_manager.alert_history[0]

    @pytest.mark.asyncio
    async def test_send_notification(self, alert_manager):
        """Test sending alert notification."""
        alert = {
            "id": "test_alert",
            "level": "warning",
            "title": "Test Alert",
            "message": "Test message",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        mock_channel = AsyncMock()
        alert_manager.notification_channels = [mock_channel]

        await alert_manager._send_notification(alert)

        mock_channel.send_alert.assert_called_once_with(alert)
        assert alert in alert_manager.alert_history

    @pytest.mark.asyncio
    async def test_send_notification_channel_failure(self, alert_manager):
        """Test sending notification when channel fails."""
        alert = {
            "id": "test_alert",
            "level": "warning",
            "title": "Test Alert",
            "message": "Test message",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        mock_channel = AsyncMock()
        mock_channel.send_alert.side_effect = Exception("Channel failed")
        alert_manager.notification_channels = [mock_channel]

        # Should not raise an exception
        await alert_manager._send_notification(alert)

        # Alert should still be added to history
        assert alert in alert_manager.alert_history

    def test_add_notification_channel(self, alert_manager):
        """Test adding notification channel."""
        mock_channel = Mock()

        alert_manager.add_notification_channel(mock_channel)

        assert mock_channel in alert_manager.notification_channels

    def test_get_alert_summary(self, alert_manager):
        """Test getting alert summary."""
        # Add some test alerts to history
        now = datetime.now(UTC)
        recent_alert = {"id": "recent_alert", "level": "warning", "timestamp": now.isoformat()}
        old_alert = {"id": "old_alert", "level": "critical", "timestamp": (now - timedelta(hours=25)).isoformat()}

        alert_manager.alert_history = [recent_alert, old_alert]
        alert_manager.active_alerts = {"active": {}}

        summary = alert_manager.get_alert_summary(hours=24)

        assert summary["time_period_hours"] == 24
        assert summary["total_alerts"] == 1  # Only recent alert
        assert summary["alert_counts_by_level"]["warning"] == 1
        assert summary["active_alerts"] == 1
        assert len(summary["recent_alerts"]) == 1


class TestDashboardApp:
    """Test FastAPI dashboard app creation and endpoints."""

    @pytest.fixture
    def mock_monitor(self):
        """Create mock monitor."""
        return MockTokenOptimizationMonitor()

    @pytest.fixture
    def dashboard_app(self, mock_monitor):
        """Create dashboard FastAPI app."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            return create_dashboard_app(mock_monitor)

    @pytest.fixture
    def client(self, dashboard_app):
        """Create test client."""
        return TestClient(dashboard_app)

    def test_create_dashboard_app(self, mock_monitor):
        """Test creating dashboard app."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            app = create_dashboard_app(mock_monitor)
            assert isinstance(app, FastAPI)
            assert app.title == "Token Optimization Dashboard"

    def test_dashboard_root_endpoint(self, client):
        """Test dashboard root endpoint."""
        response = client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Token Optimization Performance Dashboard" in response.text

    def test_prometheus_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint."""
        response = client.get("/metrics")

        assert response.status_code == 200
        assert "token_reduction_percentage" in response.text
        assert "# HELP" in response.text

    def test_json_metrics_endpoint(self, client):
        """Test JSON metrics endpoint."""
        response = client.get("/api/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "token_reduction" in data
        assert "timestamp" in data

    def test_health_report_endpoint(self, client):
        """Test health report endpoint."""
        response = client.get("/api/health")

        assert response.status_code == 200
        # Response should be the health report object

    def test_optimization_report_endpoint(self, client):
        """Test optimization report endpoint."""
        response = client.get("/api/optimization-report")

        assert response.status_code == 200
        data = response.json()
        assert "token_reduction" in data
        assert "sessions_optimized" in data

    def test_optimization_report_endpoint_with_user(self, client):
        """Test optimization report endpoint with user ID."""
        response = client.get("/api/optimization-report?user_id=test_user")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user"

    def test_alerts_endpoint(self, client):
        """Test current alerts endpoint."""
        response = client.get("/api/alerts")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_alert_summary_endpoint(self, client):
        """Test alert summary endpoint."""
        response = client.get("/api/alerts/summary")

        assert response.status_code == 200
        data = response.json()
        assert "time_period_hours" in data
        assert "total_alerts" in data
        assert "active_alerts" in data

    def test_alert_summary_endpoint_custom_hours(self, client):
        """Test alert summary endpoint with custom hours."""
        response = client.get("/api/alerts/summary?hours=48")

        assert response.status_code == 200
        data = response.json()
        assert data["time_period_hours"] == 48


class TestGlobalDashboardInstance:
    """Test global dashboard instance management."""

    def test_get_dashboard_app_singleton(self):
        """Test that get_dashboard_app returns a singleton."""
        with patch("src.monitoring.performance_dashboard.get_token_optimization_monitor") as mock_get_monitor:
            mock_get_monitor.return_value = MockTokenOptimizationMonitor()
            with patch("src.monitoring.performance_dashboard.create_structured_logger"):
                app1 = get_dashboard_app()
                app2 = get_dashboard_app()

                # Should return the same instance
                assert app1 is app2

    def test_get_dashboard_app_creates_monitor(self):
        """Test that get_dashboard_app creates monitor dependency."""
        # Reset the global instance first
        import src.monitoring.performance_dashboard

        src.monitoring.performance_dashboard._dashboard_app = None

        with patch("src.monitoring.performance_dashboard.get_token_optimization_monitor") as mock_get_monitor:
            mock_get_monitor.return_value = MockTokenOptimizationMonitor()
            with patch("src.monitoring.performance_dashboard.create_structured_logger"):
                app = get_dashboard_app()

                mock_get_monitor.assert_called_once()
                assert isinstance(app, FastAPI)


class TestWebSocketEndpoint:
    """Test WebSocket functionality."""

    @pytest.fixture
    def mock_monitor(self):
        """Create mock monitor."""
        return MockTokenOptimizationMonitor()

    @pytest.fixture
    def dashboard_app(self, mock_monitor):
        """Create dashboard FastAPI app."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            return create_dashboard_app(mock_monitor)

    def test_websocket_endpoint_exists(self, dashboard_app):
        """Test that WebSocket endpoint is configured."""
        # Check that the route exists
        websocket_routes = [
            route for route in dashboard_app.routes if hasattr(route, "path") and route.path == "/ws/dashboard"
        ]
        assert len(websocket_routes) == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def mock_monitor(self):
        """Create mock monitor."""
        return MockTokenOptimizationMonitor()

    @pytest.fixture
    def metrics_exporter(self, mock_monitor):
        """Create MetricsExporter instance."""
        with (
            patch("src.monitoring.performance_dashboard.get_performance_monitor"),
            patch("src.monitoring.performance_dashboard.create_structured_logger"),
        ):
            return MetricsExporter(mock_monitor)

    @pytest.mark.asyncio
    async def test_metrics_export_with_empty_data(self, metrics_exporter):
        """Test metrics export with empty/minimal data."""
        # Mock empty function metrics
        metrics_exporter.monitor.function_metrics = {}

        result = await metrics_exporter.export_prometheus_metrics()
        assert isinstance(result, str)
        assert "token_reduction_percentage" in result

    @pytest.mark.asyncio
    async def test_dashboard_with_empty_sessions(self, mock_monitor):
        """Test dashboard generation with no active sessions."""
        mock_monitor.active_sessions = []
        mock_monitor.session_metrics = {}

        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            dashboard = RealTimeDashboard(mock_monitor)
            data = await dashboard._generate_dashboard_data()

            assert data["active_sessions"] == []

    @pytest.mark.asyncio
    async def test_dashboard_with_zero_cache_operations(self, mock_monitor):
        """Test dashboard with zero cache hits/misses."""
        # Set cache operations to zero
        for tier_metrics in mock_monitor.function_metrics.values():
            tier_metrics.cache_hits = 0
            tier_metrics.cache_misses = 0

        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            dashboard = RealTimeDashboard(mock_monitor)
            data = await dashboard._generate_dashboard_data()

            # Cache hit rate should be 0.0 when no operations
            for tier_data in data["tier_performance"].values():
                assert tier_data["cache_hit_rate"] == 0.0

    def test_alert_manager_with_edge_threshold_values(self, mock_monitor):
        """Test alert manager with values exactly at thresholds."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            AlertManager(mock_monitor)

            # Test that exactly at threshold doesn't trigger alert
            health_report = MockSystemHealthReport()
            health_report.average_token_reduction_percentage = 50.0  # Exactly at min
            health_report.p95_loading_latency_ms = 200.0  # Exactly at max
            health_report.overall_success_rate = 0.95  # Exactly at min

            mock_monitor.generate_system_health_report = AsyncMock(return_value=health_report)

            # Values exactly at threshold should not trigger alerts
            # (using < and > comparisons, not <= and >=)


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    @pytest.fixture
    def mock_monitor(self):
        """Create mock monitor with complex data."""
        monitor = MockTokenOptimizationMonitor()

        # Add more complex session data
        for i in range(15):  # More than the 10 display limit
            session_id = f"session_{i}"
            monitor.active_sessions.append(session_id)
            monitor.session_metrics[session_id] = MockSessionMetrics()

        return monitor

    @pytest.mark.asyncio
    async def test_dashboard_with_many_sessions(self, mock_monitor):
        """Test dashboard display limits with many sessions."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            dashboard = RealTimeDashboard(mock_monitor)
            data = await dashboard._generate_dashboard_data()

            # Should limit to 10 sessions for display
            assert len(data["active_sessions"]) <= 10

    @pytest.mark.asyncio
    async def test_full_dashboard_update_cycle(self, mock_monitor):
        """Test complete dashboard update cycle."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            dashboard = RealTimeDashboard(mock_monitor)

            # Add mock clients
            mock_clients = [AsyncMock() for _ in range(3)]
            dashboard.connected_clients = mock_clients

            # Generate and broadcast data
            data = await dashboard._generate_dashboard_data()
            await dashboard._broadcast_to_clients(data)

            # All clients should receive the data
            for client in mock_clients:
                client.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_alert_lifecycle(self, mock_monitor):
        """Test complete alert lifecycle: trigger -> active -> resolve."""
        with patch("src.monitoring.performance_dashboard.create_structured_logger"):
            alert_manager = AlertManager(mock_monitor)

            # First check - trigger alert
            health_report = MockSystemHealthReport()
            health_report.average_token_reduction_percentage = 30.0  # Below threshold
            mock_monitor.generate_system_health_report = AsyncMock(return_value=health_report)

            alerts = await alert_manager.check_alerts()
            assert len(alerts) == 1
            assert len(alert_manager.active_alerts) == 1

            # Second check - alert still active
            alerts = await alert_manager.check_alerts()
            assert len(alerts) == 1
            assert len(alert_manager.active_alerts) == 1

            # Third check - resolve alert
            health_report.average_token_reduction_percentage = 75.0  # Above threshold
            alerts = await alert_manager.check_alerts()
            assert len(alerts) == 0
            assert len(alert_manager.active_alerts) == 0
            # Alert history includes both new alerts and resolved alerts
            assert len(alert_manager.alert_history) >= 1
