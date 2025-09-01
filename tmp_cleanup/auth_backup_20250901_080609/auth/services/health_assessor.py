"""
Health Assessor Service

Handles system health assessment, service monitoring, and availability checks.
Extracted from router business logic for reusability and testability.
"""

from datetime import datetime
from enum import Enum
from typing import Any

import aiohttp

from src.utils.datetime_compat import UTC, timedelta


class HealthStatus(Enum):
    """Health status enumeration."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServiceHealthLevel(Enum):
    """Service health assessment levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class HealthAssessor:
    """Service for comprehensive system and service health assessment."""

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._cache_expiry: dict[str, datetime] = {}
        self._service_registry: dict[str, dict[str, Any]] = {}
        self._health_thresholds = {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 85.0,
            "memory_critical": 95.0,
            "disk_warning": 80.0,
            "disk_critical": 90.0,
            "response_time_warning": 1000.0,  # ms
            "response_time_critical": 5000.0,  # ms
            "service_availability_warning": 0.95,  # 95%
            "service_availability_critical": 0.80,  # 80%
        }

    async def assess_overall_system_health(
        self,
        service_health_data: dict[str, dict[str, Any]],
        system_metrics: dict[str, float],
        external_dependencies: dict[str, bool],
    ) -> dict[str, Any]:
        """Assess overall system health across all components.

        Args:
            service_health_data: Health status of internal services
            system_metrics: System resource metrics
            external_dependencies: External service availability

        Returns:
            Comprehensive system health assessment
        """
        assessment_time = datetime.now(UTC)

        # Assess individual components
        service_assessment = await self._assess_service_health(service_health_data)
        system_assessment = await self._assess_system_resources(system_metrics)
        dependency_assessment = await self._assess_external_dependencies(external_dependencies)

        # Calculate overall health score (0-100)
        health_weights = {
            "services": 0.5,  # 50% weight for internal services
            "system": 0.3,  # 30% weight for system resources
            "dependencies": 0.2,  # 20% weight for external dependencies
        }

        overall_score = (
            service_assessment["health_score"] * health_weights["services"]
            + system_assessment["health_score"] * health_weights["system"]
            + dependency_assessment["health_score"] * health_weights["dependencies"]
        )

        # Determine overall status based on score and critical failures
        overall_status = self._calculate_overall_status(
            overall_score,
            service_assessment["critical_failures"],
            system_assessment["critical_failures"],
            dependency_assessment["critical_failures"],
        )

        # Generate health recommendations
        recommendations = await self._generate_health_recommendations(
            service_assessment,
            system_assessment,
            dependency_assessment,
        )

        # Calculate system availability estimate
        availability_estimate = await self._calculate_availability_estimate(service_health_data, system_metrics)

        return {
            "overall_status": overall_status.value,
            "overall_score": round(overall_score, 1),
            "assessment_time": assessment_time,
            "component_assessments": {
                "services": service_assessment,
                "system_resources": system_assessment,
                "external_dependencies": dependency_assessment,
            },
            "health_summary": {
                "total_services": len(service_health_data),
                "healthy_services": service_assessment["healthy_count"],
                "degraded_services": service_assessment["degraded_count"],
                "unhealthy_services": service_assessment["unhealthy_count"],
                "critical_alerts": service_assessment["critical_failures"]
                + system_assessment["critical_failures"]
                + dependency_assessment["critical_failures"],
            },
            "availability_estimate": availability_estimate,
            "recommendations": recommendations,
            "next_assessment": assessment_time + timedelta(minutes=5),
        }

    async def assess_service_reliability(
        self,
        service_name: str,
        historical_data: list[dict[str, Any]],
        time_window_hours: int = 24,
    ) -> dict[str, Any]:
        """Assess service reliability metrics over time.

        Args:
            service_name: Name of the service to assess
            historical_data: Historical health check data
            time_window_hours: Analysis time window

        Returns:
            Service reliability assessment
        """
        if not historical_data:
            return {
                "service_name": service_name,
                "reliability_score": 0,
                "availability_percentage": 0,
                "error_rate": 100,
                "recommendations": ["Insufficient data for reliability assessment"],
            }

        # Calculate availability percentage
        total_checks = len(historical_data)
        successful_checks = sum(1 for check in historical_data if check.get("healthy", False))
        availability_percentage = (successful_checks / total_checks) * 100 if total_checks > 0 else 0

        # Calculate error rate
        error_rate = 100 - availability_percentage

        # Analyze response time trends
        response_times = [
            check.get("response_time_ms", 0) for check in historical_data if check.get("response_time_ms") is not None
        ]

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0

        # Calculate reliability score based on multiple factors
        reliability_factors = {
            "availability": availability_percentage / 100 * 40,  # 40% weight
            "response_time": max(0, (2000 - avg_response_time) / 2000 * 30),  # 30% weight
            "stability": self._calculate_stability_score(historical_data) * 20,  # 20% weight
            "recent_trend": self._calculate_trend_score(historical_data[-10:]) * 10,  # 10% weight
        }

        reliability_score = sum(reliability_factors.values())

        # Generate service-specific recommendations
        recommendations = []
        if availability_percentage < 95:
            recommendations.append(f"Service availability ({availability_percentage:.1f}%) below target (95%)")
        if avg_response_time > 1000:
            recommendations.append(f"Average response time ({avg_response_time:.0f}ms) exceeds threshold (1000ms)")
        if error_rate > 5:
            recommendations.append(f"Error rate ({error_rate:.1f}%) requires investigation")

        if not recommendations:
            recommendations.append("Service reliability within acceptable parameters")

        return {
            "service_name": service_name,
            "reliability_score": round(reliability_score, 1),
            "availability_percentage": round(availability_percentage, 2),
            "error_rate": round(error_rate, 2),
            "response_time_metrics": {
                "average_ms": round(avg_response_time, 1),
                "maximum_ms": max_response_time,
                "threshold_ms": self._health_thresholds["response_time_warning"],
            },
            "reliability_factors": {k: round(v, 1) for k, v in reliability_factors.items()},
            "trend_analysis": self._analyze_reliability_trends(historical_data),
            "recommendations": recommendations,
            "assessment_time": datetime.now(UTC),
        }

    async def predict_service_failures(
        self,
        service_metrics: dict[str, list[float]],
        prediction_window_minutes: int = 30,
    ) -> dict[str, Any]:
        """Predict potential service failures based on metric trends.

        Args:
            service_metrics: Historical metrics by service
            prediction_window_minutes: Prediction time window

        Returns:
            Service failure predictions
        """
        predictions = {}
        current_time = datetime.now(UTC)

        for service_name, metrics in service_metrics.items():
            if len(metrics) < 5:  # Need minimum data points
                predictions[service_name] = {
                    "failure_probability": 0,
                    "predicted_failure_time": None,
                    "confidence": 0,
                    "reason": "Insufficient data points",
                }
                continue

            # Analyze metric trends
            trend_analysis = self._analyze_metric_trends(metrics)

            # Calculate failure probability based on multiple indicators
            failure_indicators = {
                "response_time_trend": self._evaluate_response_time_trend(metrics),
                "error_rate_trend": self._evaluate_error_rate_trend(metrics),
                "resource_usage_trend": self._evaluate_resource_trend(metrics),
                "stability_degradation": self._evaluate_stability_degradation(metrics),
            }

            # Weight the indicators
            failure_probability = (
                failure_indicators["response_time_trend"] * 0.3
                + failure_indicators["error_rate_trend"] * 0.35
                + failure_indicators["resource_usage_trend"] * 0.2
                + failure_indicators["stability_degradation"] * 0.15
            )

            # Determine predicted failure time if probability is significant
            predicted_failure_time = None
            if failure_probability > 0.3:  # 30% threshold
                estimated_minutes = int((1 - failure_probability) * prediction_window_minutes)
                predicted_failure_time = current_time + timedelta(minutes=estimated_minutes)

            # Calculate confidence based on data quality and trend consistency
            confidence = self._calculate_prediction_confidence(metrics, trend_analysis)

            predictions[service_name] = {
                "failure_probability": round(failure_probability, 3),
                "predicted_failure_time": predicted_failure_time,
                "confidence": round(confidence, 2),
                "failure_indicators": {k: round(v, 3) for k, v in failure_indicators.items()},
                "trend_analysis": trend_analysis,
                "recommendation": self._generate_failure_prevention_recommendation(
                    failure_probability,
                    failure_indicators,
                ),
            }

        # Identify highest risk services
        high_risk_services = [
            service
            for service, pred in predictions.items()
            if pred["failure_probability"] > 0.5 and pred["confidence"] > 0.7
        ]

        return {
            "predictions": predictions,
            "high_risk_services": high_risk_services,
            "prediction_window_minutes": prediction_window_minutes,
            "overall_system_risk": self._calculate_overall_system_risk(predictions),
            "generated_at": current_time,
        }

    async def check_external_service_health(
        self,
        service_url: str,
        timeout_seconds: int = 5,
        expected_status_codes: list[int] | None = None,
    ) -> dict[str, Any]:
        """Check health of external service endpoint.

        Args:
            service_url: URL to check
            timeout_seconds: Request timeout
            expected_status_codes: Expected HTTP status codes

        Returns:
            External service health check result
        """
        if expected_status_codes is None:
            expected_status_codes = [200, 201, 202, 204]

        start_time = datetime.now(UTC)

        try:
            timeout = aiohttp.ClientTimeout(total=timeout_seconds)
            async with aiohttp.ClientSession(timeout=timeout) as session, session.get(service_url) as response:
                end_time = datetime.now(UTC)
                response_time = (end_time - start_time).total_seconds() * 1000

                is_healthy = response.status in expected_status_codes

                return {
                    "service_url": service_url,
                    "status": "healthy" if is_healthy else "unhealthy",
                    "http_status": response.status,
                    "response_time_ms": round(response_time, 2),
                    "checked_at": start_time,
                    "healthy": is_healthy,
                    "error_message": None if is_healthy else f"HTTP {response.status}",
                }

        except TimeoutError:
            return {
                "service_url": service_url,
                "status": "unhealthy",
                "http_status": None,
                "response_time_ms": timeout_seconds * 1000,
                "checked_at": start_time,
                "healthy": False,
                "error_message": f"Request timeout after {timeout_seconds} seconds",
            }
        except Exception as e:
            return {
                "service_url": service_url,
                "status": "unhealthy",
                "http_status": None,
                "response_time_ms": None,
                "checked_at": start_time,
                "healthy": False,
                "error_message": str(e),
            }

    # Private helper methods

    async def _assess_service_health(self, service_data: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Assess internal service health."""
        healthy_count = 0
        degraded_count = 0
        unhealthy_count = 0
        critical_failures = 0

        service_scores = []

        for _service_name, data in service_data.items():
            if data.get("healthy", False):
                healthy_count += 1
                service_scores.append(100)
            elif data.get("status") == "degraded":
                degraded_count += 1
                service_scores.append(60)
            else:
                unhealthy_count += 1
                service_scores.append(0)
                if data.get("severity") == "critical":
                    critical_failures += 1

        health_score = sum(service_scores) / len(service_scores) if service_scores else 0

        return {
            "health_score": health_score,
            "healthy_count": healthy_count,
            "degraded_count": degraded_count,
            "unhealthy_count": unhealthy_count,
            "critical_failures": critical_failures,
        }

    async def _assess_system_resources(self, metrics: dict[str, float]) -> dict[str, Any]:
        """Assess system resource health."""
        critical_failures = 0
        resource_scores = []

        # CPU assessment
        cpu_usage = metrics.get("cpu_usage_percent", 0)
        if cpu_usage > self._health_thresholds["cpu_critical"]:
            critical_failures += 1
            cpu_score = 0
        elif cpu_usage > self._health_thresholds["cpu_warning"]:
            cpu_score = 50
        else:
            cpu_score = 100
        resource_scores.append(cpu_score)

        # Memory assessment
        memory_usage = metrics.get("memory_usage_percent", 0)
        if memory_usage > self._health_thresholds["memory_critical"]:
            critical_failures += 1
            memory_score = 0
        elif memory_usage > self._health_thresholds["memory_warning"]:
            memory_score = 50
        else:
            memory_score = 100
        resource_scores.append(memory_score)

        # Disk assessment
        disk_usage = metrics.get("disk_usage_percent", 0)
        if disk_usage > self._health_thresholds["disk_critical"]:
            critical_failures += 1
            disk_score = 0
        elif disk_usage > self._health_thresholds["disk_warning"]:
            disk_score = 50
        else:
            disk_score = 100
        resource_scores.append(disk_score)

        health_score = sum(resource_scores) / len(resource_scores) if resource_scores else 0

        return {
            "health_score": health_score,
            "critical_failures": critical_failures,
            "resource_breakdown": {"cpu_score": cpu_score, "memory_score": memory_score, "disk_score": disk_score},
        }

    async def _assess_external_dependencies(self, dependencies: dict[str, bool]) -> dict[str, Any]:
        """Assess external dependency health."""
        if not dependencies:
            return {"health_score": 100, "critical_failures": 0}

        healthy_count = sum(1 for status in dependencies.values() if status)
        total_count = len(dependencies)
        critical_failures = total_count - healthy_count

        health_score = (healthy_count / total_count) * 100 if total_count > 0 else 100

        return {
            "health_score": health_score,
            "critical_failures": critical_failures,
            "healthy_dependencies": healthy_count,
            "total_dependencies": total_count,
        }

    def _calculate_overall_status(
        self,
        overall_score: float,
        service_failures: int,
        system_failures: int,
        dependency_failures: int,
    ) -> HealthStatus:
        """Calculate overall health status."""
        total_critical_failures = service_failures + system_failures + dependency_failures

        if total_critical_failures > 0 or overall_score < 50:
            return HealthStatus.UNHEALTHY
        if overall_score < 80:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY

    async def _generate_health_recommendations(
        self,
        service_assessment: dict[str, Any],
        system_assessment: dict[str, Any],
        dependency_assessment: dict[str, Any],
    ) -> list[str]:
        """Generate health improvement recommendations."""
        recommendations = []

        if service_assessment["critical_failures"] > 0:
            recommendations.append("Critical service failures require immediate attention")

        if service_assessment["unhealthy_count"] > 0:
            recommendations.append(f"{service_assessment['unhealthy_count']} services are unhealthy")

        if system_assessment["critical_failures"] > 0:
            recommendations.append("Critical system resource issues detected")

        if dependency_assessment["critical_failures"] > 0:
            recommendations.append("External dependency failures affecting system")

        if not recommendations:
            recommendations.append("All systems operating within normal parameters")

        return recommendations

    async def _calculate_availability_estimate(
        self,
        service_data: dict[str, dict[str, Any]],
        system_metrics: dict[str, float],
    ) -> dict[str, float]:
        """Calculate system availability estimates."""
        # This would typically use historical data
        # For now, provide estimates based on current health
        healthy_services = sum(1 for data in service_data.values() if data.get("healthy", False))
        total_services = len(service_data)

        service_availability = (healthy_services / total_services) if total_services > 0 else 1.0

        # Factor in system resources
        cpu_factor = max(0, (100 - system_metrics.get("cpu_usage_percent", 0)) / 100)
        memory_factor = max(0, (100 - system_metrics.get("memory_usage_percent", 0)) / 100)

        overall_availability = service_availability * 0.7 + (cpu_factor + memory_factor) / 2 * 0.3

        return {
            "current_estimated": round(overall_availability * 100, 2),
            "service_component": round(service_availability * 100, 2),
            "resource_component": round(((cpu_factor + memory_factor) / 2) * 100, 2),
        }

    def _calculate_stability_score(self, historical_data: list[dict[str, Any]]) -> float:
        """Calculate service stability score from historical data."""
        if len(historical_data) < 3:
            return 0.5  # Neutral score for insufficient data

        # Look for frequent state changes (instability indicator)
        state_changes = 0
        for i in range(1, len(historical_data)):
            if historical_data[i].get("healthy") != historical_data[i - 1].get("healthy"):
                state_changes += 1

        # Lower score for more frequent changes
        stability_score = max(0, 1 - (state_changes / len(historical_data)))
        return stability_score

    def _calculate_trend_score(self, recent_data: list[dict[str, Any]]) -> float:
        """Calculate trend score from recent health checks."""
        if len(recent_data) < 3:
            return 0.5

        successful_checks = sum(1 for check in recent_data if check.get("healthy", False))
        trend_score = successful_checks / len(recent_data)
        return trend_score

    def _analyze_reliability_trends(self, historical_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze reliability trends over time."""
        if len(historical_data) < 10:
            return {"trend": "insufficient_data", "direction": "stable"}

        # Split into two halves for comparison
        mid_point = len(historical_data) // 2
        first_half = historical_data[:mid_point]
        second_half = historical_data[mid_point:]

        first_half_availability = sum(1 for check in first_half if check.get("healthy", False)) / len(first_half)
        second_half_availability = sum(1 for check in second_half if check.get("healthy", False)) / len(second_half)

        if second_half_availability > first_half_availability * 1.05:
            trend = "improving"
        elif second_half_availability < first_half_availability * 0.95:
            trend = "degrading"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "first_half_availability": round(first_half_availability * 100, 1),
            "second_half_availability": round(second_half_availability * 100, 1),
            "change_percentage": round((second_half_availability - first_half_availability) * 100, 1),
        }

    def _analyze_metric_trends(self, metrics: list[float]) -> dict[str, Any]:
        """Analyze trends in metric data."""
        if len(metrics) < 3:
            return {"trend": "insufficient_data"}

        # Simple linear trend analysis
        recent_avg = sum(metrics[-3:]) / 3
        older_avg = sum(metrics[-6:-3]) / 3 if len(metrics) >= 6 else sum(metrics[:-3]) / len(metrics[:-3])

        trend_direction = (
            "increasing" if recent_avg > older_avg * 1.1 else "decreasing" if recent_avg < older_avg * 0.9 else "stable"
        )

        return {
            "trend": trend_direction,
            "recent_average": recent_avg,
            "older_average": older_avg,
            "change_rate": (recent_avg - older_avg) / older_avg if older_avg > 0 else 0,
        }

    def _evaluate_response_time_trend(self, metrics: list[float]) -> float:
        """Evaluate response time trend for failure prediction."""
        if len(metrics) < 3:
            return 0

        trend = self._analyze_metric_trends(metrics)
        if trend["trend"] == "increasing" and trend["change_rate"] > 0.2:  # 20% increase
            return min(1.0, trend["change_rate"])
        return 0

    def _evaluate_error_rate_trend(self, metrics: list[float]) -> float:
        """Evaluate error rate trend for failure prediction."""
        if len(metrics) < 3:
            return 0

        recent_errors = sum(metrics[-3:]) / 3
        if recent_errors > 0.1:  # 10% error rate threshold
            return min(1.0, recent_errors)
        return 0

    def _evaluate_resource_trend(self, metrics: list[float]) -> float:
        """Evaluate resource usage trend for failure prediction."""
        if len(metrics) < 3:
            return 0

        trend = self._analyze_metric_trends(metrics)
        if trend["trend"] == "increasing" and trend["recent_average"] > 0.8:  # 80% usage
            return min(1.0, trend["recent_average"])
        return 0

    def _evaluate_stability_degradation(self, metrics: list[float]) -> float:
        """Evaluate stability degradation for failure prediction."""
        if len(metrics) < 5:
            return 0

        # Calculate variance in recent metrics
        recent_metrics = metrics[-5:]
        mean = sum(recent_metrics) / len(recent_metrics)
        variance = sum((x - mean) ** 2 for x in recent_metrics) / len(recent_metrics)

        # Higher variance indicates instability
        return min(1.0, variance / mean if mean > 0 else 0)

    def _calculate_prediction_confidence(self, metrics: list[float], trend_analysis: dict[str, Any]) -> float:
        """Calculate confidence in failure prediction."""
        data_quality = min(1.0, len(metrics) / 20)  # More data = higher confidence
        trend_consistency = 0.8 if trend_analysis.get("trend") != "insufficient_data" else 0.2

        return (data_quality + trend_consistency) / 2

    def _generate_failure_prevention_recommendation(
        self,
        failure_probability: float,
        indicators: dict[str, float],
    ) -> str:
        """Generate recommendation for preventing service failure."""
        if failure_probability < 0.3:
            return "Service operating normally, continue monitoring"
        if failure_probability < 0.6:
            primary_indicator = max(indicators, key=indicators.get)
            return f"Monitor {primary_indicator.replace('_', ' ')} closely, consider proactive measures"
        return "High failure risk detected, implement immediate preventive actions"

    def _calculate_overall_system_risk(self, predictions: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Calculate overall system risk from service predictions."""
        if not predictions:
            return {"risk_level": "low", "risk_score": 0}

        high_risk_count = sum(1 for pred in predictions.values() if pred["failure_probability"] > 0.5)
        total_services = len(predictions)
        avg_failure_probability = sum(pred["failure_probability"] for pred in predictions.values()) / total_services

        if high_risk_count > total_services * 0.5:
            risk_level = "critical"
        elif high_risk_count > 0 or avg_failure_probability > 0.3:
            risk_level = "high"
        elif avg_failure_probability > 0.1:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "risk_level": risk_level,
            "risk_score": round(avg_failure_probability, 3),
            "high_risk_services": high_risk_count,
            "total_services": total_services,
        }
