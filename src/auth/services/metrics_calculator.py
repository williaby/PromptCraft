"""
Metrics Calculator Service

Handles calculation and aggregation of security metrics.
Extracted from router business logic for reusability and testability.
"""

from datetime import datetime, timezone, timedelta
from typing import Any


class MetricsCalculator:
    """Service for calculating security metrics and system health scores."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._cache_expiry: dict[str, datetime] = {}

    async def calculate_system_health_score(
        self,
        service_health: dict[str, bool],
        performance_metrics: dict[str, float],
    ) -> float:
        """Calculate overall system health score.

        Args:
            service_health: Dictionary of service health statuses
            performance_metrics: Performance metric values

        Returns:
            Health score from 0-100
        """
        health_score = 100.0

        # Service health impact (50% of score)
        healthy_services = sum(1 for status in service_health.values() if status)
        total_services = len(service_health)

        if total_services > 0:
            service_ratio = healthy_services / total_services
            health_score *= service_ratio

        # Performance impact (50% of score)
        avg_processing_time = performance_metrics.get("average_processing_time_ms", 0)
        if avg_processing_time > 50:
            # Penalty for slow processing: reduce score by up to 30 points
            penalty = min(30, (avg_processing_time - 50) / 10 * 5)
            health_score -= penalty

        # Memory usage impact
        memory_usage = performance_metrics.get("memory_usage_percent", 0)
        if memory_usage > 80:
            health_score -= min(20, (memory_usage - 80) / 10 * 10)

        # CPU usage impact
        cpu_usage = performance_metrics.get("cpu_usage_percent", 0)
        if cpu_usage > 90:
            health_score -= min(15, (cpu_usage - 90) / 10 * 15)

        return max(0, health_score)

    async def calculate_event_rate_metrics(
        self,
        event_counts: dict[str, int],
        time_period_hours: int = 24,
    ) -> dict[str, float]:
        """Calculate event rate metrics.

        Args:
            event_counts: Event counts by type
            time_period_hours: Time period for rate calculation

        Returns:
            Dictionary of calculated rates
        """
        total_events = sum(event_counts.values())

        return {
            "events_per_hour": total_events / time_period_hours if time_period_hours > 0 else 0,
            "events_per_minute": total_events / (time_period_hours * 60) if time_period_hours > 0 else 0,
            "critical_event_rate": event_counts.get("critical", 0) / time_period_hours if time_period_hours > 0 else 0,
            "total_event_rate": total_events / time_period_hours if time_period_hours > 0 else 0,
        }

    async def calculate_alert_statistics(self, alert_data: dict[str, Any]) -> dict[str, Any]:
        """Calculate alert-related statistics.

        Args:
            alert_data: Raw alert data

        Returns:
            Calculated alert statistics
        """
        total_alerts = alert_data.get("total_alerts", 0)

        # Estimate distribution (in production, this would use real data)
        critical_alerts = int(total_alerts * 0.15)  # ~15% critical
        high_alerts = int(total_alerts * 0.25)  # ~25% high
        medium_alerts = int(total_alerts * 0.35)  # ~35% medium
        low_alerts = total_alerts - critical_alerts - high_alerts - medium_alerts

        acknowledged_alerts = int(total_alerts * 0.72)  # ~72% acknowledged

        return {
            "total_alerts": total_alerts,
            "critical_alerts": critical_alerts,
            "high_alerts": high_alerts,
            "medium_alerts": medium_alerts,
            "low_alerts": low_alerts,
            "acknowledged_alerts": acknowledged_alerts,
            "unacknowledged_alerts": total_alerts - acknowledged_alerts,
            "acknowledgment_rate": (acknowledged_alerts / total_alerts * 100) if total_alerts > 0 else 0,
        }

    async def calculate_risk_distribution(
        self,
        risk_data: dict[str, int],
        total_items: int | None = None,
    ) -> dict[str, Any]:
        """Calculate risk distribution percentages and metrics.

        Args:
            risk_data: Risk level counts
            total_items: Total items (calculated if not provided)

        Returns:
            Risk distribution analysis
        """
        if total_items is None:
            total_items = sum(risk_data.values())

        if total_items == 0:
            return {"distribution": {}, "average_risk_score": 0, "risk_trend": "stable"}

        # Calculate percentages
        distribution = {}
        weighted_risk_sum = 0

        risk_weights = {"low": 15, "medium": 45, "high": 70, "critical": 90}

        for risk_level, count in risk_data.items():
            percentage = (count / total_items) * 100
            distribution[risk_level] = {"count": count, "percentage": round(percentage, 1)}

            # Add to weighted sum for average calculation
            weight = risk_weights.get(risk_level.lower(), 50)
            weighted_risk_sum += count * weight

        average_risk_score = weighted_risk_sum / total_items if total_items > 0 else 0

        # Determine risk trend (simplified logic)
        high_risk_percentage = (
            (risk_data.get("high", 0) + risk_data.get("critical", 0)) / total_items * 100 if total_items > 0 else 0
        )

        if high_risk_percentage > 25:
            risk_trend = "increasing"
        elif high_risk_percentage < 10:
            risk_trend = "decreasing"
        else:
            risk_trend = "stable"

        return {
            "distribution": distribution,
            "average_risk_score": round(average_risk_score, 1),
            "risk_trend": risk_trend,
            "high_risk_percentage": round(high_risk_percentage, 1),
        }

    async def calculate_timeline_metrics(
        self,
        timeline_data: list[dict[str, Any]],
        granularity: str = "hour",
    ) -> dict[str, Any]:
        """Calculate timeline-based metrics.

        Args:
            timeline_data: List of time-stamped data points
            granularity: Time granularity (hour, day)

        Returns:
            Timeline metrics and analysis
        """
        if not timeline_data:
            return {"total_events": 0, "peak_period": None, "average_per_period": 0, "trend": "stable"}

        total_events = sum(item.get("event_count", 0) for item in timeline_data)
        peak_count = 0
        peak_period = None

        # Find peak activity period
        for item in timeline_data:
            event_count = item.get("event_count", 0)
            if event_count > peak_count:
                peak_count = event_count
                timestamp = item.get("timestamp")
                if timestamp:
                    if granularity == "hour":
                        peak_period = timestamp.strftime("%H:00")
                    else:
                        peak_period = timestamp.strftime("%Y-%m-%d")

        average_per_period = total_events / len(timeline_data) if timeline_data else 0

        # Simple trend calculation (compare first half vs second half)
        if len(timeline_data) >= 4:
            mid_point = len(timeline_data) // 2
            first_half_avg = sum(item.get("event_count", 0) for item in timeline_data[:mid_point]) / mid_point
            second_half_avg = sum(item.get("event_count", 0) for item in timeline_data[mid_point:]) / (
                len(timeline_data) - mid_point
            )

            if second_half_avg > first_half_avg * 1.2:
                trend = "increasing"
            elif second_half_avg < first_half_avg * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "total_events": total_events,
            "peak_period": peak_period,
            "peak_count": peak_count,
            "average_per_period": round(average_per_period, 1),
            "trend": trend,
        }

    async def get_cached_metrics(self, cache_key: str, cache_ttl_seconds: int = 300) -> Any | None:
        """Get cached metrics if still valid.

        Args:
            cache_key: Cache key identifier
            cache_ttl_seconds: Cache time-to-live in seconds

        Returns:
            Cached data if valid, None otherwise
        """
        if cache_key not in self._cache:
            return None

        expiry_time = self._cache_expiry.get(cache_key)
        if not expiry_time or datetime.now(timezone.utc) > expiry_time:
            # Remove expired cache entry
            self._cache.pop(cache_key, None)
            self._cache_expiry.pop(cache_key, None)
            return None

        return self._cache[cache_key]

    async def set_cached_metrics(self, cache_key: str, data: Any, cache_ttl_seconds: int = 300) -> None:
        """Cache metrics data.

        Args:
            cache_key: Cache key identifier
            data: Data to cache
            cache_ttl_seconds: Cache time-to-live in seconds
        """
        self._cache[cache_key] = data
        self._cache_expiry[cache_key] = datetime.now(timezone.utc) + timedelta(seconds=cache_ttl_seconds)
