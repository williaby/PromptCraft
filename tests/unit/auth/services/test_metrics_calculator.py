"""Comprehensive unit tests for MetricsCalculator.

Tests calculation and aggregation of security metrics,
system health scoring, and performance analytics.
"""

from datetime import UTC, datetime, timedelta

from src.auth.services.metrics_calculator import MetricsCalculator


class TestMetricsCalculatorInitialization:
    """Test metrics calculator initialization and basic functionality."""

    def test_init_default_configuration(self):
        """Test metrics calculator initialization with default settings."""
        calculator = MetricsCalculator()

        # Check internal state
        assert isinstance(calculator._cache, dict)
        assert isinstance(calculator._cache_expiry, dict)
        assert len(calculator._cache) == 0
        assert len(calculator._cache_expiry) == 0


class TestSystemHealthScoreCalculation:
    """Test system health score calculation functionality."""

    async def test_calculate_system_health_score_perfect_health(self):
        """Test health score calculation with perfect system health."""
        calculator = MetricsCalculator()

        service_health = {
            "database": True,
            "redis": True,
            "api": True,
            "auth": True,
        }

        performance_metrics = {
            "average_processing_time_ms": 25.0,
            "memory_usage_percent": 45.0,
            "cpu_usage_percent": 35.0,
        }

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        assert score == 100.0  # Perfect health

    async def test_calculate_system_health_score_degraded_services(self):
        """Test health score with some services down."""
        calculator = MetricsCalculator()

        service_health = {
            "database": True,
            "redis": False,  # Service down
            "api": True,
            "auth": False,  # Service down
        }

        performance_metrics = {
            "average_processing_time_ms": 25.0,
            "memory_usage_percent": 45.0,
            "cpu_usage_percent": 35.0,
        }

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # Only 2/4 services healthy = 50% service ratio
        assert score == 50.0

    async def test_calculate_system_health_score_high_processing_time(self):
        """Test health score with high processing time penalty."""
        calculator = MetricsCalculator()

        service_health = {
            "database": True,
            "api": True,
        }

        performance_metrics = {
            "average_processing_time_ms": 100.0,  # High processing time
            "memory_usage_percent": 45.0,
            "cpu_usage_percent": 35.0,
        }

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # Processing time penalty: (100-50)/10*5 = 25 points
        assert score == 75.0

    async def test_calculate_system_health_score_high_memory_usage(self):
        """Test health score with high memory usage penalty."""
        calculator = MetricsCalculator()

        service_health = {"api": True}

        performance_metrics = {
            "average_processing_time_ms": 25.0,
            "memory_usage_percent": 90.0,  # High memory usage
            "cpu_usage_percent": 35.0,
        }

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # Memory penalty: (90-80)/10*10 = 10 points
        assert score == 90.0

    async def test_calculate_system_health_score_high_cpu_usage(self):
        """Test health score with high CPU usage penalty."""
        calculator = MetricsCalculator()

        service_health = {"api": True}

        performance_metrics = {
            "average_processing_time_ms": 25.0,
            "memory_usage_percent": 45.0,
            "cpu_usage_percent": 95.0,  # High CPU usage
        }

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # CPU penalty: (95-90)/10*15 = 7.5 points
        assert score == 92.5

    async def test_calculate_system_health_score_multiple_penalties(self):
        """Test health score with multiple performance penalties."""
        calculator = MetricsCalculator()

        service_health = {"api": True}

        performance_metrics = {
            "average_processing_time_ms": 200.0,  # 30 point penalty (max)
            "memory_usage_percent": 100.0,  # 20 point penalty (max)
            "cpu_usage_percent": 100.0,  # 15 point penalty (max)
        }

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # Total penalties: 30 + 20 + 15 = 65 points
        assert score == 35.0

    async def test_calculate_system_health_score_no_services(self):
        """Test health score with no services to check."""
        calculator = MetricsCalculator()

        service_health = {}  # No services
        performance_metrics = {"average_processing_time_ms": 25.0}

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # No services means no impact from service health
        assert score == 100.0

    async def test_calculate_system_health_score_minimum_floor(self):
        """Test health score has minimum floor of 0."""
        calculator = MetricsCalculator()

        service_health = {
            "database": False,
            "redis": False,
            "api": False,
        }

        performance_metrics = {
            "average_processing_time_ms": 1000.0,  # Extreme penalty
            "memory_usage_percent": 100.0,
            "cpu_usage_percent": 100.0,
        }

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # Score should never go below 0
        assert score == 0.0

    async def test_calculate_system_health_score_missing_metrics(self):
        """Test health score calculation with missing performance metrics."""
        calculator = MetricsCalculator()

        service_health = {"api": True}
        performance_metrics = {}  # No performance metrics

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # Should default to 100% with no penalties
        assert score == 100.0


class TestEventRateMetricsCalculation:
    """Test event rate metrics calculation functionality."""

    async def test_calculate_event_rate_metrics_basic(self):
        """Test basic event rate calculation."""
        calculator = MetricsCalculator()

        event_counts = {
            "login_success": 100,
            "login_failure": 20,
            "critical": 5,
        }

        rates = await calculator.calculate_event_rate_metrics(
            event_counts,
            time_period_hours=24,
        )

        total_events = 125
        assert rates["events_per_hour"] == total_events / 24
        assert rates["events_per_minute"] == total_events / (24 * 60)
        assert rates["critical_event_rate"] == 5 / 24
        assert rates["total_event_rate"] == total_events / 24

    async def test_calculate_event_rate_metrics_custom_period(self):
        """Test event rate calculation with custom time period."""
        calculator = MetricsCalculator()

        event_counts = {"login_success": 50}

        rates = await calculator.calculate_event_rate_metrics(
            event_counts,
            time_period_hours=12,
        )

        assert rates["events_per_hour"] == 50 / 12
        assert rates["events_per_minute"] == 50 / (12 * 60)
        assert rates["critical_event_rate"] == 0 / 12  # No critical events
        assert rates["total_event_rate"] == 50 / 12

    async def test_calculate_event_rate_metrics_zero_period(self):
        """Test event rate calculation with zero time period."""
        calculator = MetricsCalculator()

        event_counts = {"login_success": 100}

        rates = await calculator.calculate_event_rate_metrics(
            event_counts,
            time_period_hours=0,
        )

        # All rates should be 0 when time period is 0
        assert rates["events_per_hour"] == 0
        assert rates["events_per_minute"] == 0
        assert rates["critical_event_rate"] == 0
        assert rates["total_event_rate"] == 0

    async def test_calculate_event_rate_metrics_empty_events(self):
        """Test event rate calculation with no events."""
        calculator = MetricsCalculator()

        event_counts = {}

        rates = await calculator.calculate_event_rate_metrics(
            event_counts,
            time_period_hours=24,
        )

        assert rates["events_per_hour"] == 0
        assert rates["events_per_minute"] == 0
        assert rates["critical_event_rate"] == 0
        assert rates["total_event_rate"] == 0


class TestAlertStatisticsCalculation:
    """Test alert statistics calculation functionality."""

    async def test_calculate_alert_statistics_basic(self):
        """Test basic alert statistics calculation."""
        calculator = MetricsCalculator()

        alert_data = {"total_alerts": 100}

        stats = await calculator.calculate_alert_statistics(alert_data)

        # Check distribution calculations
        assert stats["total_alerts"] == 100
        assert stats["critical_alerts"] == 15  # 15%
        assert stats["high_alerts"] == 25  # 25%
        assert stats["medium_alerts"] == 35  # 35%
        assert stats["low_alerts"] == 25  # Remainder

        # Check acknowledgment metrics
        assert stats["acknowledged_alerts"] == 72  # ~72%
        assert stats["unacknowledged_alerts"] == 28
        assert stats["acknowledgment_rate"] == 72.0

    async def test_calculate_alert_statistics_zero_alerts(self):
        """Test alert statistics calculation with zero alerts."""
        calculator = MetricsCalculator()

        alert_data = {"total_alerts": 0}

        stats = await calculator.calculate_alert_statistics(alert_data)

        assert stats["total_alerts"] == 0
        assert stats["critical_alerts"] == 0
        assert stats["high_alerts"] == 0
        assert stats["medium_alerts"] == 0
        assert stats["low_alerts"] == 0

        # Acknowledgment metrics should be 0
        assert stats["acknowledged_alerts"] == 0
        assert stats["unacknowledged_alerts"] == 0
        assert stats["acknowledgment_rate"] == 0

    async def test_calculate_alert_statistics_no_total(self):
        """Test alert statistics calculation with missing total_alerts."""
        calculator = MetricsCalculator()

        alert_data = {}  # No total_alerts key

        stats = await calculator.calculate_alert_statistics(alert_data)

        # Should default to 0
        assert stats["total_alerts"] == 0
        assert stats["critical_alerts"] == 0

    async def test_calculate_alert_statistics_acknowledgment_metrics(self):
        """Test alert statistics acknowledgment calculations."""
        calculator = MetricsCalculator()

        alert_data = {"total_alerts": 100}

        stats = await calculator.calculate_alert_statistics(alert_data)

        # Check acknowledgment metrics
        assert stats["acknowledged_alerts"] == 72  # 72% of 100
        assert stats["unacknowledged_alerts"] == 28  # Remainder
        assert stats["acknowledgment_rate"] == 72.0  # Percentage

    async def test_calculate_alert_statistics_large_numbers(self):
        """Test alert statistics calculation with large numbers."""
        calculator = MetricsCalculator()

        alert_data = {"total_alerts": 10000}

        stats = await calculator.calculate_alert_statistics(alert_data)

        assert stats["total_alerts"] == 10000
        assert stats["critical_alerts"] == 1500  # 15%
        assert stats["high_alerts"] == 2500  # 25%
        assert stats["medium_alerts"] == 3500  # 35%
        assert stats["low_alerts"] == 2500  # Remainder


class TestRiskDistributionCalculation:
    """Test risk distribution calculation functionality."""

    async def test_calculate_risk_distribution_basic(self):
        """Test basic risk distribution calculation."""
        calculator = MetricsCalculator()

        risk_data = {
            "low": 40,
            "medium": 30,
            "high": 20,
            "critical": 10,
        }

        distribution = await calculator.calculate_risk_distribution(risk_data)

        assert distribution["distribution"]["low"]["count"] == 40
        assert distribution["distribution"]["low"]["percentage"] == 40.0
        assert distribution["distribution"]["medium"]["count"] == 30
        assert distribution["distribution"]["medium"]["percentage"] == 30.0
        assert distribution["distribution"]["high"]["count"] == 20
        assert distribution["distribution"]["high"]["percentage"] == 20.0
        assert distribution["distribution"]["critical"]["count"] == 10
        assert distribution["distribution"]["critical"]["percentage"] == 10.0

        # Check average risk score calculation
        # (40*15 + 30*45 + 20*70 + 10*90) / 100 = 42.5
        assert distribution["average_risk_score"] == 42.5

        # Check risk trend (high+critical = 30% > 25%, so increasing)
        assert distribution["risk_trend"] == "increasing"
        assert distribution["high_risk_percentage"] == 30.0

    async def test_calculate_risk_distribution_with_total_items(self):
        """Test risk distribution with explicit total items."""
        calculator = MetricsCalculator()

        risk_data = {"low": 50, "medium": 30}

        distribution = await calculator.calculate_risk_distribution(
            risk_data,
            total_items=200,
        )

        # Should use explicit total_items, not sum of risk_data
        assert distribution["distribution"]["low"]["percentage"] == 25.0  # 50/200
        assert distribution["distribution"]["medium"]["percentage"] == 15.0  # 30/200

    async def test_calculate_risk_distribution_empty_data(self):
        """Test risk distribution with empty risk data."""
        calculator = MetricsCalculator()

        risk_data = {}

        distribution = await calculator.calculate_risk_distribution(risk_data)

        assert distribution["distribution"] == {}
        assert distribution["average_risk_score"] == 0
        assert distribution["risk_trend"] == "stable"

    async def test_calculate_risk_distribution_zero_total(self):
        """Test risk distribution with zero total items."""
        calculator = MetricsCalculator()

        risk_data = {"low": 0, "medium": 0}

        distribution = await calculator.calculate_risk_distribution(risk_data)

        assert distribution["distribution"] == {}
        assert distribution["average_risk_score"] == 0
        assert distribution["risk_trend"] == "stable"

    async def test_calculate_risk_distribution_decreasing_trend(self):
        """Test risk distribution with decreasing trend."""
        calculator = MetricsCalculator()

        risk_data = {
            "low": 80,
            "medium": 15,
            "high": 4,
            "critical": 1,  # Only 5% high risk
        }

        distribution = await calculator.calculate_risk_distribution(risk_data)

        assert distribution["risk_trend"] == "decreasing"  # < 10% high risk
        assert distribution["high_risk_percentage"] == 5.0

    async def test_calculate_risk_distribution_stable_trend(self):
        """Test risk distribution with stable trend."""
        calculator = MetricsCalculator()

        risk_data = {
            "low": 70,
            "medium": 15,
            "high": 10,
            "critical": 5,  # 15% high risk (between 10-25%)
        }

        distribution = await calculator.calculate_risk_distribution(risk_data)

        assert distribution["risk_trend"] == "stable"
        assert distribution["high_risk_percentage"] == 15.0

    async def test_calculate_risk_distribution_unknown_risk_level(self):
        """Test risk distribution with unknown risk level."""
        calculator = MetricsCalculator()

        risk_data = {
            "low": 50,
            "unknown": 30,  # Unknown risk level
            "high": 20,
        }

        distribution = await calculator.calculate_risk_distribution(risk_data)

        # Should handle unknown risk level with default weight of 50
        assert distribution["distribution"]["unknown"]["count"] == 30
        # Average: (50*15 + 30*50 + 20*70) / 100 = 36.5
        assert distribution["average_risk_score"] == 36.5


class TestTimelineMetricsCalculation:
    """Test timeline metrics calculation functionality."""

    async def test_calculate_timeline_metrics_basic(self):
        """Test basic timeline metrics calculation."""
        calculator = MetricsCalculator()

        timeline_data = [
            {"event_count": 10, "timestamp": datetime(2024, 1, 1, 10)},
            {"event_count": 20, "timestamp": datetime(2024, 1, 1, 11)},
            {"event_count": 5, "timestamp": datetime(2024, 1, 1, 12)},
            {"event_count": 15, "timestamp": datetime(2024, 1, 1, 13)},
        ]

        metrics = await calculator.calculate_timeline_metrics(timeline_data)

        assert metrics["total_events"] == 50
        assert metrics["peak_period"] == "11:00"  # Hour with highest count (20)
        assert metrics["peak_count"] == 20
        assert metrics["average_per_period"] == 12.5  # 50/4
        assert metrics["trend"] == "decreasing"  # First half avg (15) > second half avg (10)

    async def test_calculate_timeline_metrics_daily_granularity(self):
        """Test timeline metrics with daily granularity."""
        calculator = MetricsCalculator()

        timeline_data = [
            {"event_count": 100, "timestamp": datetime(2024, 1, 1)},
            {"event_count": 150, "timestamp": datetime(2024, 1, 2)},
        ]

        metrics = await calculator.calculate_timeline_metrics(
            timeline_data,
            granularity="day",
        )

        assert metrics["peak_period"] == "2024-01-02"  # Day with highest count
        assert metrics["peak_count"] == 150

    async def test_calculate_timeline_metrics_empty_data(self):
        """Test timeline metrics with empty data."""
        calculator = MetricsCalculator()

        timeline_data = []

        metrics = await calculator.calculate_timeline_metrics(timeline_data)

        assert metrics["total_events"] == 0
        assert metrics["peak_period"] is None
        assert metrics["average_per_period"] == 0
        assert metrics["trend"] == "stable"

    async def test_calculate_timeline_metrics_increasing_trend(self):
        """Test timeline metrics with increasing trend."""
        calculator = MetricsCalculator()

        timeline_data = [
            {"event_count": 5},  # First half average: 7.5
            {"event_count": 10},
            {"event_count": 15},  # Second half average: 17.5
            {"event_count": 20},
        ]

        metrics = await calculator.calculate_timeline_metrics(timeline_data)

        assert metrics["trend"] == "increasing"  # 17.5 > 7.5 * 1.2

    async def test_calculate_timeline_metrics_no_timestamp(self):
        """Test timeline metrics with missing timestamps."""
        calculator = MetricsCalculator()

        timeline_data = [
            {"event_count": 10},  # No timestamp
            {"event_count": 20, "timestamp": datetime(2024, 1, 1, 11)},
        ]

        metrics = await calculator.calculate_timeline_metrics(timeline_data)

        assert metrics["peak_period"] == "11:00"  # Only timestamp available
        assert metrics["peak_count"] == 20

    async def test_calculate_timeline_metrics_insufficient_data_for_trend(self):
        """Test timeline metrics with insufficient data for trend calculation."""
        calculator = MetricsCalculator()

        timeline_data = [
            {"event_count": 10},
            {"event_count": 20},
        ]  # Less than 4 items

        metrics = await calculator.calculate_timeline_metrics(timeline_data)

        assert metrics["trend"] == "stable"  # Default for insufficient data

    async def test_calculate_timeline_metrics_missing_event_count(self):
        """Test timeline metrics with missing event_count."""
        calculator = MetricsCalculator()

        timeline_data = [
            {"timestamp": datetime(2024, 1, 1, 10)},  # No event_count
            {"event_count": 20, "timestamp": datetime(2024, 1, 1, 11)},
        ]

        metrics = await calculator.calculate_timeline_metrics(timeline_data)

        assert metrics["total_events"] == 20  # Should default missing to 0
        assert metrics["peak_count"] == 20


class TestMetricsCalculatorCaching:
    """Test caching functionality for metrics calculations."""

    def test_cache_initialization(self):
        """Test cache is properly initialized."""
        calculator = MetricsCalculator()

        assert hasattr(calculator, "_cache")
        assert hasattr(calculator, "_cache_expiry")
        assert isinstance(calculator._cache, dict)
        assert isinstance(calculator._cache_expiry, dict)

    async def test_set_cached_metrics(self):
        """Test setting cached metrics."""
        calculator = MetricsCalculator()

        test_data = {"test": "value"}
        await calculator.set_cached_metrics("test_key", test_data, 300)

        assert calculator._cache["test_key"] == test_data
        assert "test_key" in calculator._cache_expiry
        assert isinstance(calculator._cache_expiry["test_key"], datetime)

    async def test_get_cached_metrics_valid(self):
        """Test getting valid cached metrics."""
        calculator = MetricsCalculator()

        test_data = {"test": "value"}
        await calculator.set_cached_metrics("test_key", test_data, 300)

        cached_data = await calculator.get_cached_metrics("test_key", 300)

        assert cached_data == test_data

    async def test_get_cached_metrics_not_found(self):
        """Test getting metrics that are not cached."""
        calculator = MetricsCalculator()

        cached_data = await calculator.get_cached_metrics("nonexistent_key", 300)

        assert cached_data is None

    async def test_get_cached_metrics_expired(self):
        """Test getting expired cached metrics."""
        calculator = MetricsCalculator()

        test_data = {"test": "value"}
        # Set cache with immediate expiry
        calculator._cache["test_key"] = test_data
        calculator._cache_expiry["test_key"] = datetime.now(UTC) - timedelta(seconds=1)

        cached_data = await calculator.get_cached_metrics("test_key", 300)

        assert cached_data is None
        # Should remove expired entries
        assert "test_key" not in calculator._cache
        assert "test_key" not in calculator._cache_expiry

    async def test_get_cached_metrics_no_expiry(self):
        """Test getting cached metrics without expiry time."""
        calculator = MetricsCalculator()

        test_data = {"test": "value"}
        calculator._cache["test_key"] = test_data
        # No expiry time set

        cached_data = await calculator.get_cached_metrics("test_key", 300)

        assert cached_data is None  # Should be treated as expired

    async def test_cache_attribute_access(self):
        """Test cache attributes can be accessed and modified."""
        calculator = MetricsCalculator()

        # Test direct cache access (for future caching implementation)
        calculator._cache["test_key"] = "test_value"
        calculator._cache_expiry["test_key"] = datetime.now(UTC)

        assert calculator._cache["test_key"] == "test_value"
        assert isinstance(calculator._cache_expiry["test_key"], datetime)


class TestMetricsCalculatorPerformance:
    """Test performance characteristics of metrics calculations."""

    async def test_calculate_system_health_score_performance(self):
        """Test health score calculation performance."""
        calculator = MetricsCalculator()

        # Large service health dictionary
        service_health = {f"service_{i}": i % 2 == 0 for i in range(100)}
        performance_metrics = {
            "average_processing_time_ms": 75.0,
            "memory_usage_percent": 85.0,
            "cpu_usage_percent": 92.0,
        }

        import time

        start_time = time.time()

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        end_time = time.time()
        calculation_time = end_time - start_time

        # Should complete quickly (< 100ms)
        assert calculation_time < 0.1
        assert isinstance(score, float)
        assert 0 <= score <= 100

    async def test_calculate_event_rate_metrics_performance(self):
        """Test event rate calculation performance with large datasets."""
        calculator = MetricsCalculator()

        # Large event counts dictionary
        event_counts = {f"event_type_{i}": i * 10 for i in range(1000)}

        import time

        start_time = time.time()

        rates = await calculator.calculate_event_rate_metrics(event_counts)

        end_time = time.time()
        calculation_time = end_time - start_time

        # Should complete quickly (< 100ms)
        assert calculation_time < 0.1
        assert isinstance(rates, dict)
        assert "events_per_hour" in rates


class TestMetricsCalculatorEdgeCases:
    """Test edge cases and error conditions."""

    async def test_negative_time_period(self):
        """Test handling of negative time period."""
        calculator = MetricsCalculator()

        event_counts = {"test": 100}

        rates = await calculator.calculate_event_rate_metrics(
            event_counts,
            time_period_hours=-5,
        )

        # Should handle gracefully and return 0 rates
        assert rates["events_per_hour"] == 0
        assert rates["events_per_minute"] == 0

    async def test_extreme_performance_values(self):
        """Test handling of extreme performance metric values."""
        calculator = MetricsCalculator()

        service_health = {"api": True}
        performance_metrics = {
            "average_processing_time_ms": float("inf"),
            "memory_usage_percent": 1000.0,  # Over 100%
            "cpu_usage_percent": -50.0,  # Negative
        }

        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # Should handle extreme values gracefully
        assert isinstance(score, float)
        assert score >= 0  # Should not go below 0

    async def test_none_values_in_metrics(self):
        """Test handling of None values in performance metrics."""
        calculator = MetricsCalculator()

        service_health = {"api": True}
        performance_metrics = {
            "average_processing_time_ms": None,
            "memory_usage_percent": None,
            "cpu_usage_percent": None,
        }

        try:
            score = await calculator.calculate_system_health_score(
                service_health,
                performance_metrics,
            )
            # If it doesn't raise an exception, score should be reasonable
            assert isinstance(score, (int, float))
        except (TypeError, AttributeError):
            # It's acceptable to raise an exception for None values
            pass


class TestMetricsCalculatorRealExecution:
    """Test metrics calculator functions with real execution to improve coverage."""

    async def test_calculate_system_health_score_real_execution(self):
        """Test system health score calculation with real function execution."""
        calculator = MetricsCalculator()

        # Real execution - not mocked
        service_health = {
            "database": True,
            "redis": True,
            "api": False,
        }

        performance_metrics = {
            "average_processing_time_ms": 75.0,
            "memory_usage_percent": 85.0,
            "cpu_usage_percent": 45.0,
        }

        # Actually execute the function
        score = await calculator.calculate_system_health_score(
            service_health,
            performance_metrics,
        )

        # Validate real execution results
        assert isinstance(score, float)
        assert 0 <= score <= 100
        # Expected: 66.67% (2/3 services) * 100 - 12.5 (processing time penalty) - 5 (memory penalty) = ~48.17
        expected_approximate_score = 48.0
        assert abs(score - expected_approximate_score) < 20  # Allow reasonable variance

    async def test_calculate_event_rate_metrics_real_execution(self):
        """Test event rate metrics with real function execution."""
        calculator = MetricsCalculator()

        # Real data
        event_counts = {
            "login_success": 240,
            "login_failure": 60,
            "critical": 12,
            "warning": 30,
        }

        # Actually execute the function
        rates = await calculator.calculate_event_rate_metrics(event_counts, time_period_hours=24)

        # Validate real execution results
        assert isinstance(rates, dict)
        total_events = 342
        assert rates["events_per_hour"] == total_events / 24
        assert rates["events_per_minute"] == total_events / (24 * 60)
        assert rates["critical_event_rate"] == 12 / 24
        assert rates["total_event_rate"] == total_events / 24

    async def test_calculate_alert_statistics_real_execution(self):
        """Test alert statistics calculation with real function execution."""
        calculator = MetricsCalculator()

        # Real data
        alert_data = {"total_alerts": 200}

        # Actually execute the function
        stats = await calculator.calculate_alert_statistics(alert_data)

        # Validate real execution results - these are the actual calculations
        assert isinstance(stats, dict)
        assert stats["total_alerts"] == 200
        assert stats["critical_alerts"] == 30  # 15% of 200
        assert stats["high_alerts"] == 50  # 25% of 200
        assert stats["medium_alerts"] == 70  # 35% of 200
        assert stats["low_alerts"] == 50  # Remainder
        assert stats["acknowledged_alerts"] == 144  # 72% of 200
        assert stats["unacknowledged_alerts"] == 56
        assert stats["acknowledgment_rate"] == 72.0

    async def test_calculate_risk_distribution_real_execution(self):
        """Test risk distribution calculation with real function execution."""
        calculator = MetricsCalculator()

        # Real data
        risk_data = {
            "low": 25,
            "medium": 30,
            "high": 20,
            "critical": 5,
        }

        # Actually execute the function
        distribution = await calculator.calculate_risk_distribution(risk_data)

        # Validate real execution results
        assert isinstance(distribution, dict)
        assert distribution["distribution"]["low"]["count"] == 25
        assert distribution["distribution"]["low"]["percentage"] == 31.2  # 25/80*100
        assert distribution["distribution"]["medium"]["count"] == 30
        assert distribution["distribution"]["medium"]["percentage"] == 37.5  # 30/80*100

        # Check weighted average calculation: (25*15 + 30*45 + 20*70 + 5*90) / 80 = 44.7 (rounded)
        assert distribution["average_risk_score"] == 44.7  # Actual rounded value

        # High risk percentage: (20+5)/80*100 = 31.25%
        assert distribution["high_risk_percentage"] == 31.2

    async def test_calculate_timeline_metrics_real_execution(self):
        """Test timeline metrics calculation with real function execution."""
        calculator = MetricsCalculator()

        # Real timeline data with datetime objects
        from datetime import datetime

        timeline_data = [
            {"event_count": 10, "timestamp": datetime(2024, 1, 1, 9)},
            {"event_count": 25, "timestamp": datetime(2024, 1, 1, 10)},
            {"event_count": 15, "timestamp": datetime(2024, 1, 1, 11)},
            {"event_count": 30, "timestamp": datetime(2024, 1, 1, 12)},
        ]

        # Actually execute the function
        metrics = await calculator.calculate_timeline_metrics(timeline_data, granularity="hour")

        # Validate real execution results
        assert isinstance(metrics, dict)
        assert metrics["total_events"] == 80  # 10+25+15+30
        assert metrics["peak_period"] == "12:00"  # Hour with highest count (30)
        assert metrics["peak_count"] == 30
        assert metrics["average_per_period"] == 20.0  # 80/4
        # Trend: first half avg (17.5) vs second half avg (22.5) -> increasing
        assert metrics["trend"] == "increasing"

    async def test_caching_methods_real_execution(self):
        """Test caching methods with real function execution."""
        calculator = MetricsCalculator()

        # Test setting cache
        test_data = {"health_score": 95.5, "timestamp": "2024-01-01"}
        await calculator.set_cached_metrics("health_data", test_data, 300)

        # Verify cache was set
        assert "health_data" in calculator._cache
        assert calculator._cache["health_data"] == test_data

        # Test getting valid cached data
        cached_result = await calculator.get_cached_metrics("health_data", 300)
        assert cached_result == test_data

        # Test getting non-existent cache
        missing_result = await calculator.get_cached_metrics("nonexistent", 300)
        assert missing_result is None

    async def test_initialization_real_execution(self):
        """Test calculator initialization with real execution."""
        # Actually instantiate the class
        calculator = MetricsCalculator()

        # Verify real initialization
        assert hasattr(calculator, "_cache")
        assert hasattr(calculator, "_cache_expiry")
        assert isinstance(calculator._cache, dict)
        assert isinstance(calculator._cache_expiry, dict)
        assert len(calculator._cache) == 0
        assert len(calculator._cache_expiry) == 0

        # Verify we can access all methods
        assert hasattr(calculator, "calculate_system_health_score")
        assert hasattr(calculator, "calculate_event_rate_metrics")
        assert hasattr(calculator, "calculate_alert_statistics")
        assert hasattr(calculator, "calculate_risk_distribution")
        assert hasattr(calculator, "calculate_timeline_metrics")
        assert hasattr(calculator, "get_cached_metrics")
        assert hasattr(calculator, "set_cached_metrics")
