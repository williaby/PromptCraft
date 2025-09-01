"""
Risk Analyzer Service

Handles user risk assessment, behavioral analysis, and anomaly detection.
Extracted from router business logic for reusability and testability.
"""

from datetime import datetime, timedelta
from typing import Any

from src.utils.datetime_compat import UTC


class RiskAnalyzer:
    """Service for analyzing user risk profiles and detecting behavioral anomalies."""

    def __init__(self) -> None:
        self._risk_cache: dict[str, Any] = {}
        self._behavioral_patterns: dict[str, list[dict[str, Any]]] = {}
        self._baseline_metrics: dict[str, dict[str, float]] = {}

    async def analyze_user_risk_profile(
        self,
        user_id: str,
        activity_data: dict[str, Any],
        time_window_hours: int = 168,
    ) -> dict[str, Any]:
        """Analyze comprehensive user risk profile.

        Args:
            user_id: User identifier
            activity_data: User activity and event data
            time_window_hours: Analysis window in hours

        Returns:
            Comprehensive risk profile analysis
        """
        try:
            current_time = datetime.now(UTC)

            # Calculate base risk factors
            login_risk = await self._analyze_login_patterns(user_id, activity_data)
            access_risk = await self._analyze_access_patterns(user_id, activity_data)
            behavioral_risk = await self._analyze_behavioral_anomalies(user_id, activity_data)
            temporal_risk = await self._analyze_temporal_patterns(user_id, activity_data)

            # Calculate overall risk score (0-100)
            risk_weights = {"login_risk": 0.25, "access_risk": 0.30, "behavioral_risk": 0.25, "temporal_risk": 0.20}

            overall_risk_score = (
                login_risk["risk_score"] * risk_weights["login_risk"]
                + access_risk["risk_score"] * risk_weights["access_risk"]
                + behavioral_risk["risk_score"] * risk_weights["behavioral_risk"]
                + temporal_risk["risk_score"] * risk_weights["temporal_risk"]
            )

            # Determine risk level
            risk_level = self._calculate_risk_level(overall_risk_score)

            # Generate risk indicators and recommendations
            risk_indicators = []
            recommendations = []

            # Collect indicators from all analyses
            risk_indicators.extend(login_risk.get("indicators", []))
            risk_indicators.extend(access_risk.get("indicators", []))
            risk_indicators.extend(behavioral_risk.get("indicators", []))
            risk_indicators.extend(temporal_risk.get("indicators", []))

            # Generate targeted recommendations
            if overall_risk_score >= 80:
                recommendations.extend(
                    [
                        "Immediate security review required",
                        "Consider temporary access restriction",
                        "Escalate to security team",
                    ],
                )
            elif overall_risk_score >= 60:
                recommendations.extend(
                    [
                        "Enhanced monitoring recommended",
                        "Review recent access patterns",
                        "Consider additional authentication factors",
                    ],
                )
            elif overall_risk_score >= 40:
                recommendations.append("Continue standard monitoring")
            else:
                recommendations.append("Low risk - maintain baseline monitoring")

            # Add specific recommendations based on risk factors
            if login_risk["risk_score"] > 60:
                recommendations.append("Review login locations and device patterns")
            if access_risk["risk_score"] > 60:
                recommendations.append("Audit data access permissions and patterns")
            if behavioral_risk["risk_score"] > 60:
                recommendations.append("Investigate behavioral anomalies and context")

            return {
                "user_id": user_id,
                "analysis_timestamp": current_time,
                "time_window_hours": time_window_hours,
                "overall_risk_score": round(overall_risk_score, 1),
                "risk_level": risk_level,
                "risk_factors": {
                    "login_patterns": login_risk,
                    "access_patterns": access_risk,
                    "behavioral_anomalies": behavioral_risk,
                    "temporal_patterns": temporal_risk,
                },
                "risk_indicators": list(set(risk_indicators)),  # Remove duplicates
                "recommendations": recommendations,
                "confidence_score": self._calculate_confidence_score(activity_data),
                "last_activity": activity_data.get("last_activity_timestamp"),
            }

        except Exception as e:
            return {
                "user_id": user_id,
                "analysis_timestamp": datetime.now(UTC),
                "error": f"Risk analysis failed: {e!s}",
                "overall_risk_score": 50.0,  # Default moderate risk on error
                "risk_level": "MEDIUM",
                "confidence_score": 0.0,
            }

    async def detect_suspicious_activities(
        self,
        activity_data: list[dict[str, Any]],
        sensitivity: float = 0.7,
        time_window_hours: int = 24,
    ) -> list[dict[str, Any]]:
        """Detect suspicious activities using behavioral analysis.

        Args:
            activity_data: List of user activities to analyze
            sensitivity: Detection sensitivity (0.0-1.0)
            time_window_hours: Analysis time window

        Returns:
            List of suspicious activity detections
        """
        suspicious_activities = []

        if not activity_data:
            return suspicious_activities

        current_time = datetime.now(UTC)
        cutoff_time = current_time - timedelta(hours=time_window_hours)

        # Filter to time window
        recent_activities = [
            activity for activity in activity_data if activity.get("timestamp", current_time) >= cutoff_time
        ]

        # Analyze patterns for each user
        user_activities = {}
        for activity in recent_activities:
            user_id = activity.get("user_id", "unknown")
            if user_id not in user_activities:
                user_activities[user_id] = []
            user_activities[user_id].append(activity)

        for user_id, activities in user_activities.items():
            user_suspicious = await self._detect_user_suspicious_patterns(user_id, activities, sensitivity)
            suspicious_activities.extend(user_suspicious)

        # Sort by suspicion score descending
        suspicious_activities.sort(key=lambda x: x.get("suspicion_score", 0), reverse=True)

        return suspicious_activities

    async def calculate_anomaly_score(
        self,
        user_id: str,
        current_behavior: dict[str, Any],
        historical_baseline: dict[str, Any] | None = None,
    ) -> tuple[float, list[str]]:
        """Calculate anomaly score for current user behavior.

        Args:
            user_id: User identifier
            current_behavior: Current behavioral metrics
            historical_baseline: Historical baseline (calculated if not provided)

        Returns:
            Tuple of (anomaly_score, anomaly_reasons)
        """
        try:
            # Get or calculate baseline
            if not historical_baseline:
                historical_baseline = await self._get_user_baseline(user_id)

            if not historical_baseline:
                return 0.0, ["No baseline data available"]

            anomaly_score = 0.0
            anomaly_reasons = []

            # Analyze key behavioral metrics
            behavioral_metrics = [
                "login_frequency",
                "session_duration",
                "access_volume",
                "geographic_variance",
                "device_variance",
                "time_of_day_variance",
            ]

            for metric in behavioral_metrics:
                current_value = current_behavior.get(metric, 0)
                baseline_value = historical_baseline.get(metric, 0)
                baseline_std = historical_baseline.get(f"{metric}_std", 0)

                if baseline_std > 0:
                    # Calculate z-score
                    z_score = abs(current_value - baseline_value) / baseline_std

                    # Convert z-score to anomaly contribution (0-100)
                    metric_anomaly = min(z_score * 20, 100)  # Cap at 100

                    if metric_anomaly > 50:  # Significant deviation
                        anomaly_score += metric_anomaly
                        anomaly_reasons.append(
                            f"Unusual {metric.replace('_', ' ')}: {current_value} vs baseline {baseline_value:.1f}",
                        )

            # Normalize anomaly score (average of contributing metrics)
            if len(anomaly_reasons) > 0:
                anomaly_score = min(anomaly_score / len(behavioral_metrics), 100)

            return round(anomaly_score, 1), anomaly_reasons

        except Exception as e:
            return 0.0, [f"Anomaly calculation error: {e!s}"]

    async def _analyze_login_patterns(self, user_id: str, activity_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze login patterns for risk assessment."""
        login_events = activity_data.get("login_events", [])

        if not login_events:
            return {"risk_score": 0.0, "indicators": [], "analysis": "No login data available"}

        risk_score = 0.0
        indicators = []

        # Analyze login frequency
        login_count = len(login_events)
        if login_count > 50:  # High frequency logins
            risk_score += 20
            indicators.append(f"High login frequency: {login_count} attempts")

        # Analyze failed logins
        failed_logins = [e for e in login_events if not e.get("success", True)]
        if len(failed_logins) > 5:
            risk_score += 30
            indicators.append(f"Multiple failed logins: {len(failed_logins)}")

        # Analyze geographic variance
        locations = {e.get("location", "unknown") for e in login_events}
        if len(locations) > 3:
            risk_score += 25
            indicators.append(f"Multiple login locations: {len(locations)}")

        # Analyze time patterns
        login_hours = [e.get("timestamp", datetime.now(UTC)).hour for e in login_events]
        unusual_hours = [h for h in login_hours if h < 6 or h > 22]
        if len(unusual_hours) > len(login_hours) * 0.3:
            risk_score += 15
            indicators.append("Unusual login times detected")

        return {
            "risk_score": min(risk_score, 100),
            "indicators": indicators,
            "analysis": {
                "total_logins": login_count,
                "failed_logins": len(failed_logins),
                "unique_locations": len(locations),
                "unusual_time_percentage": len(unusual_hours) / max(len(login_hours), 1) * 100,
            },
        }

    async def _analyze_access_patterns(self, user_id: str, activity_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze data access patterns for risk assessment."""
        access_events = activity_data.get("access_events", [])

        if not access_events:
            return {"risk_score": 0.0, "indicators": [], "analysis": "No access data available"}

        risk_score = 0.0
        indicators = []

        # Analyze volume of access
        access_count = len(access_events)
        if access_count > 100:  # High volume access
            risk_score += 15
            indicators.append(f"High access volume: {access_count} events")

        # Analyze sensitive data access
        sensitive_access = [e for e in access_events if e.get("sensitivity", "").lower() in ["high", "critical"]]
        if len(sensitive_access) > access_count * 0.2:
            risk_score += 25
            indicators.append(f"High sensitive data access: {len(sensitive_access)} events")

        # Analyze access pattern deviation
        access_types = {}
        for event in access_events:
            access_type = event.get("access_type", "unknown")
            access_types[access_type] = access_types.get(access_type, 0) + 1

        # Check for unusual access type distribution
        if len(access_types) > 5:  # Many different access types
            risk_score += 10
            indicators.append(f"Diverse access patterns: {len(access_types)} types")

        # Analyze bulk operations
        bulk_operations = [e for e in access_events if e.get("record_count", 1) > 100]
        if len(bulk_operations) > 0:
            risk_score += 20
            indicators.append(f"Bulk data operations detected: {len(bulk_operations)}")

        return {
            "risk_score": min(risk_score, 100),
            "indicators": indicators,
            "analysis": {
                "total_access_events": access_count,
                "sensitive_access_count": len(sensitive_access),
                "access_type_diversity": len(access_types),
                "bulk_operations": len(bulk_operations),
            },
        }

    async def _analyze_behavioral_anomalies(self, user_id: str, activity_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze behavioral anomalies for risk assessment."""
        behavior_metrics = activity_data.get("behavior_metrics", {})

        if not behavior_metrics:
            return {"risk_score": 0.0, "indicators": [], "analysis": "No behavioral data available"}

        risk_score = 0.0
        indicators = []

        # Analyze session duration anomalies
        avg_session_duration = behavior_metrics.get("avg_session_duration_minutes", 30)
        if avg_session_duration > 480:  # > 8 hours
            risk_score += 20
            indicators.append(f"Unusually long sessions: {avg_session_duration:.0f} minutes")
        elif avg_session_duration < 2:  # < 2 minutes
            risk_score += 15
            indicators.append(f"Unusually short sessions: {avg_session_duration:.1f} minutes")

        # Analyze activity velocity
        actions_per_minute = behavior_metrics.get("actions_per_minute", 1.0)
        if actions_per_minute > 10:  # Very high activity
            risk_score += 25
            indicators.append(f"High activity velocity: {actions_per_minute:.1f} actions/min")
        elif actions_per_minute < 0.1:  # Very low activity
            risk_score += 10
            indicators.append(f"Low activity velocity: {actions_per_minute:.2f} actions/min")

        # Analyze error rates
        error_rate = behavior_metrics.get("error_rate_percent", 0)
        if error_rate > 20:
            risk_score += 15
            indicators.append(f"High error rate: {error_rate:.1f}%")

        # Analyze navigation patterns
        unique_pages_visited = behavior_metrics.get("unique_pages_visited", 5)
        total_page_views = behavior_metrics.get("total_page_views", 10)

        if total_page_views > 0:
            page_repetition_ratio = unique_pages_visited / total_page_views
            if page_repetition_ratio < 0.1:  # Very repetitive navigation
                risk_score += 15
                indicators.append("Highly repetitive navigation pattern")

        return {
            "risk_score": min(risk_score, 100),
            "indicators": indicators,
            "analysis": {
                "avg_session_duration": avg_session_duration,
                "actions_per_minute": actions_per_minute,
                "error_rate": error_rate,
                "page_repetition_ratio": unique_pages_visited / max(total_page_views, 1),
            },
        }

    async def _analyze_temporal_patterns(self, user_id: str, activity_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze temporal access patterns for risk assessment."""
        temporal_data = activity_data.get("temporal_patterns", {})

        if not temporal_data:
            return {"risk_score": 0.0, "indicators": [], "analysis": "No temporal data available"}

        risk_score = 0.0
        indicators = []

        # Analyze off-hours activity
        off_hours_percentage = temporal_data.get("off_hours_percentage", 0)
        if off_hours_percentage > 30:
            risk_score += 20
            indicators.append(f"High off-hours activity: {off_hours_percentage:.1f}%")

        # Analyze weekend activity
        weekend_percentage = temporal_data.get("weekend_percentage", 0)
        if weekend_percentage > 40:
            risk_score += 15
            indicators.append(f"High weekend activity: {weekend_percentage:.1f}%")

        # Analyze activity clustering
        activity_clustering_score = temporal_data.get("clustering_score", 0)
        if activity_clustering_score > 80:  # Highly clustered = potential automation
            risk_score += 25
            indicators.append("Potential automated activity patterns")

        # Analyze time zone consistency
        timezone_variance = temporal_data.get("timezone_variance", 0)
        if timezone_variance > 3:  # Multiple timezones
            risk_score += 10
            indicators.append(f"Multiple timezone activity: {timezone_variance} zones")

        return {
            "risk_score": min(risk_score, 100),
            "indicators": indicators,
            "analysis": {
                "off_hours_percentage": off_hours_percentage,
                "weekend_percentage": weekend_percentage,
                "clustering_score": activity_clustering_score,
                "timezone_variance": timezone_variance,
            },
        }

    async def _detect_user_suspicious_patterns(
        self,
        user_id: str,
        activities: list[dict[str, Any]],
        sensitivity: float,
    ) -> list[dict[str, Any]]:
        """Detect suspicious patterns for a specific user."""
        suspicious_patterns = []

        if len(activities) < 2:
            return suspicious_patterns

        # Pattern 1: Rapid sequential actions
        rapid_actions = await self._detect_rapid_actions(user_id, activities, sensitivity)
        suspicious_patterns.extend(rapid_actions)

        # Pattern 2: Unusual access sequences
        unusual_sequences = await self._detect_unusual_sequences(user_id, activities, sensitivity)
        suspicious_patterns.extend(unusual_sequences)

        # Pattern 3: Privilege escalation attempts
        escalation_attempts = await self._detect_escalation_attempts(user_id, activities, sensitivity)
        suspicious_patterns.extend(escalation_attempts)

        return suspicious_patterns

    async def _detect_rapid_actions(
        self,
        user_id: str,
        activities: list[dict[str, Any]],
        sensitivity: float,
    ) -> list[dict[str, Any]]:
        """Detect suspiciously rapid action sequences."""
        suspicious = []

        # Sort by timestamp
        sorted_activities = sorted(activities, key=lambda x: x.get("timestamp", datetime.min.replace(tzinfo=UTC)))

        rapid_threshold = timedelta(seconds=1 / sensitivity)  # Adjust based on sensitivity

        for i in range(1, len(sorted_activities)):
            current = sorted_activities[i]
            previous = sorted_activities[i - 1]

            time_diff = current.get("timestamp", datetime.max.replace(tzinfo=UTC)) - previous.get(
                "timestamp",
                datetime.min.replace(tzinfo=UTC),
            )

            if time_diff < rapid_threshold:
                suspicious.append(
                    {
                        "pattern_type": "rapid_actions",
                        "user_id": user_id,
                        "suspicion_score": (1 - time_diff.total_seconds()) * 100,
                        "description": f"Extremely rapid actions: {time_diff.total_seconds():.2f}s apart",
                        "activities": [previous, current],
                        "timestamp": current.get("timestamp"),
                    },
                )

        return suspicious

    async def _detect_unusual_sequences(
        self,
        user_id: str,
        activities: list[dict[str, Any]],
        sensitivity: float,
    ) -> list[dict[str, Any]]:
        """Detect unusual action sequences."""
        suspicious = []

        # Look for unusual patterns in action types
        action_sequence = [activity.get("action_type", "unknown") for activity in activities]

        # Pattern: Same action repeated many times
        for action_type in set(action_sequence):
            count = action_sequence.count(action_type)
            if count > len(action_sequence) * (0.8 / sensitivity):  # High repetition
                suspicious.append(
                    {
                        "pattern_type": "repetitive_actions",
                        "user_id": user_id,
                        "suspicion_score": min(count * 10, 100),
                        "description": f"Highly repetitive action: {action_type} repeated {count} times",
                        "action_type": action_type,
                        "repetition_count": count,
                        "timestamp": activities[-1].get("timestamp") if activities else datetime.now(UTC),
                    },
                )

        return suspicious

    async def _detect_escalation_attempts(
        self,
        user_id: str,
        activities: list[dict[str, Any]],
        sensitivity: float,
    ) -> list[dict[str, Any]]:
        """Detect potential privilege escalation attempts."""
        suspicious = []

        # Look for admin-like actions from regular users
        admin_actions = ["user_management", "permission_change", "system_config", "security_setting", "role_assignment"]

        user_admin_actions = [activity for activity in activities if activity.get("action_type", "") in admin_actions]

        if len(user_admin_actions) > 0:
            base_suspicion = len(user_admin_actions) * 30
            suspicion_score = min(base_suspicion * sensitivity, 100)

            if suspicion_score > 50:  # Significant suspicion
                suspicious.append(
                    {
                        "pattern_type": "privilege_escalation",
                        "user_id": user_id,
                        "suspicion_score": suspicion_score,
                        "description": f"Potential privilege escalation: {len(user_admin_actions)} admin actions",
                        "admin_actions": user_admin_actions,
                        "timestamp": (
                            user_admin_actions[-1].get("timestamp") if user_admin_actions else datetime.now(UTC)
                        ),
                    },
                )

        return suspicious

    async def _get_user_baseline(self, user_id: str) -> dict[str, Any] | None:
        """Get user behavioral baseline (mock implementation)."""
        # In production, this would query historical data
        baseline_key = f"baseline_{user_id}"

        if baseline_key not in self._baseline_metrics:
            # Generate mock baseline
            self._baseline_metrics[baseline_key] = {
                "login_frequency": 3.2,
                "login_frequency_std": 1.1,
                "session_duration": 45.5,
                "session_duration_std": 15.2,
                "access_volume": 25.0,
                "access_volume_std": 8.5,
                "geographic_variance": 1.2,
                "geographic_variance_std": 0.4,
                "device_variance": 1.8,
                "device_variance_std": 0.6,
                "time_of_day_variance": 2.5,
                "time_of_day_variance_std": 1.0,
            }

        return self._baseline_metrics.get(baseline_key)

    def _calculate_risk_level(self, risk_score: float) -> str:
        """Calculate risk level from numeric score."""
        if risk_score >= 80:
            return "CRITICAL"
        if risk_score >= 60:
            return "HIGH"
        if risk_score >= 40:
            return "MEDIUM"
        return "LOW"

    def _calculate_confidence_score(self, activity_data: dict[str, Any]) -> float:
        """Calculate confidence in risk assessment based on data quality."""
        confidence_factors = []

        # Data volume factor
        login_events = len(activity_data.get("login_events", []))
        access_events = len(activity_data.get("access_events", []))
        total_events = login_events + access_events

        if total_events >= 50:
            confidence_factors.append(95.0)
        elif total_events >= 20:
            confidence_factors.append(80.0)
        elif total_events >= 10:
            confidence_factors.append(60.0)
        else:
            confidence_factors.append(30.0)

        # Data recency factor
        last_activity = activity_data.get("last_activity_timestamp")
        if last_activity:
            hours_since_activity = (datetime.now(UTC) - last_activity).total_seconds() / 3600
            if hours_since_activity <= 24:
                confidence_factors.append(90.0)
            elif hours_since_activity <= 72:
                confidence_factors.append(75.0)
            elif hours_since_activity <= 168:
                confidence_factors.append(50.0)
            else:
                confidence_factors.append(25.0)
        else:
            confidence_factors.append(40.0)

        # Data completeness factor
        has_behavior_metrics = bool(activity_data.get("behavior_metrics"))
        has_temporal_patterns = bool(activity_data.get("temporal_patterns"))

        completeness_score = 50.0  # Base
        if has_behavior_metrics:
            completeness_score += 25.0
        if has_temporal_patterns:
            completeness_score += 25.0

        confidence_factors.append(completeness_score)

        # Return average confidence
        return round(sum(confidence_factors) / len(confidence_factors), 1)
