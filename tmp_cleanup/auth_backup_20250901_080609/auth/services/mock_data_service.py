"""
Mock Data Service

Provides mock data generation for security analytics and testing.
Extracted from router business logic for reusability and centralized management.
"""

import random
import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from src.utils.datetime_compat import UTC, timedelta


class DataGenerationMode(Enum):
    """Mock data generation modes."""

    REALISTIC = "realistic"
    TESTING = "testing"
    DEMO = "demo"
    STRESS = "stress"


class MockDataService:
    """Service for generating mock security and analytics data."""

    def __init__(self, mode: DataGenerationMode = DataGenerationMode.REALISTIC) -> None:
        self.mode = mode
        self._cache: dict[str, Any] = {}

        # Realistic data distribution patterns
        self._event_types = [
            "user_login",
            "user_logout",
            "password_change",
            "permission_change",
            "data_access",
            "file_upload",
            "file_download",
            "api_request",
            "system_change",
            "security_alert",
            "failed_login",
            "suspicious_activity",
        ]

        self._risk_levels = ["low", "medium", "high", "critical"]
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Chrome/91.0.4472.124 Safari/537.36",
        ]

        self._ip_ranges = ["192.168.1.", "10.0.0.", "172.16.0.", "203.0.113.", "198.51.100.", "93.184.216."]

    async def generate_security_events(
        self,
        count: int = 100,
        days_back: int = 30,
        event_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate mock security events.

        Args:
            count: Number of events to generate
            days_back: Days of historical data
            event_types: Specific event types to generate

        Returns:
            List of mock security events
        """
        if event_types is None:
            event_types = self._event_types

        events = []
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(days=days_back)

        for _i in range(count):
            # Generate timestamp within the range
            time_offset = random.random() * (end_time - start_time).total_seconds()  # nosec B311
            event_time = start_time + timedelta(seconds=time_offset)

            # Select event type with realistic distribution
            event_type = self._select_weighted_event_type(event_types)

            # Generate event data
            event = {
                "event_id": str(uuid.uuid4()),
                "event_type": event_type,
                "timestamp": event_time,
                "user_id": f"user_{random.randint(1000, 9999)}",  # nosec B311
                "ip_address": self._generate_ip_address(),
                "user_agent": random.choice(self._user_agents),  # nosec B311
                "risk_score": self._generate_risk_score(event_type),
                "details": self._generate_event_details(event_type),
                "session_id": str(uuid.uuid4())[:16],
                "location": self._generate_location(),
                "success": self._generate_success_status(event_type),
            }

            events.append(event)

        # Sort by timestamp
        events.sort(key=lambda x: x["timestamp"])
        return events

    async def generate_user_activity_data(
        self,
        user_count: int = 50,
        activity_window_days: int = 30,
    ) -> dict[str, list[dict[str, Any]]]:
        """Generate mock user activity data.

        Args:
            user_count: Number of users to generate data for
            activity_window_days: Days of activity data

        Returns:
            Dictionary mapping user_ids to activity lists
        """
        user_activities = {}

        for i in range(user_count):
            user_id = f"user_{1000 + i}"

            # Generate user profile
            user_profile = {
                "user_id": user_id,
                "role": random.choice(["admin", "user", "viewer", "analyst"]),  # nosec B311
                "department": random.choice(["IT", "Finance", "HR", "Marketing", "Operations"]),  # nosec B311
                "risk_level": random.choice(self._risk_levels),  # nosec B311
                "last_login": datetime.now(UTC) - timedelta(days=random.randint(0, 7)),  # nosec B311
            }

            # Generate activities for this user
            activity_count = (
                random.randint(10, 100)  # nosec B311
                if self.mode == DataGenerationMode.REALISTIC
                else random.randint(5, 20)  # nosec B311
            )
            activities = []

            for _j in range(activity_count):
                activity_time = datetime.now(UTC) - timedelta(
                    days=random.randint(0, activity_window_days),  # nosec B311
                    hours=random.randint(0, 23),  # nosec B311
                    minutes=random.randint(0, 59),  # nosec B311
                )

                activity = {
                    "timestamp": activity_time,
                    "action": random.choice(  # nosec B311
                        ["login", "logout", "file_access", "api_call", "data_export"],
                    ),
                    "resource": f"resource_{random.randint(1, 100)}",  # nosec B311
                    "ip_address": self._generate_ip_address(),
                    "success": random.random() > 0.1,  # nosec B311
                    "duration_seconds": random.randint(1, 3600),  # nosec B311
                    "bytes_transferred": random.randint(1024, 1048576),  # nosec B311
                }
                activities.append(activity)

            activities.sort(key=lambda x: x["timestamp"])
            user_activities[user_id] = {"profile": user_profile, "activities": activities}

        return user_activities

    async def generate_system_metrics(
        self,
        hours_back: int = 24,
        granularity_minutes: int = 15,
    ) -> list[dict[str, Any]]:
        """Generate mock system performance metrics.

        Args:
            hours_back: Hours of metrics data
            granularity_minutes: Minutes between data points

        Returns:
            List of system metric snapshots
        """
        metrics = []
        end_time = datetime.now(UTC)
        start_time = end_time - timedelta(hours=hours_back)

        current_time = start_time
        while current_time <= end_time:
            # Generate realistic system metrics with some noise
            cpu_base = 35.0 + random.gauss(0, 10)
            memory_base = 60.0 + random.gauss(0, 15)

            metric = {
                "timestamp": current_time,
                "cpu_usage_percent": max(0, min(100, cpu_base)),
                "memory_usage_percent": max(0, min(100, memory_base)),
                "disk_usage_percent": random.uniform(20, 80),  # nosec B311
                "network_io_mbps": random.uniform(10, 1000),  # nosec B311
                "disk_io_iops": random.randint(100, 5000),  # nosec B311
                "active_connections": random.randint(50, 500),  # nosec B311
                "response_time_ms": random.uniform(50, 500),  # nosec B311
                "error_rate_percent": random.uniform(0, 5),  # nosec B311
                "throughput_rps": random.randint(100, 1000),  # nosec B311
            }

            metrics.append(metric)
            current_time += timedelta(minutes=granularity_minutes)

        return metrics

    async def generate_behavioral_patterns(
        self,
        pattern_count: int = 10,
        min_confidence: float = 70.0,
    ) -> list[dict[str, Any]]:
        """Generate mock behavioral patterns for analysis.

        Args:
            pattern_count: Number of patterns to generate
            min_confidence: Minimum confidence score

        Returns:
            List of behavioral pattern data
        """
        patterns = []
        pattern_types = [
            "unusual_access",
            "anomalous_login",
            "data_exfiltration",
            "privilege_escalation",
            "lateral_movement",
            "brute_force",
            "time_anomaly",
            "location_anomaly",
            "device_anomaly",
        ]

        for _i in range(pattern_count):
            pattern_type = random.choice(pattern_types)  # nosec B311
            confidence = random.uniform(min_confidence, 100.0)  # nosec B311

            # Generate pattern based on type
            affected_users = random.randint(1, 20)  # nosec B311
            risk_score = self._calculate_pattern_risk_score(pattern_type, confidence)

            pattern = {
                "pattern_id": f"pattern_{uuid.uuid4().hex[:8]}",
                "pattern_type": pattern_type,
                "description": self._generate_pattern_description(pattern_type),
                "confidence_score": round(confidence, 1),
                "risk_score": risk_score,
                "affected_users": affected_users,
                "first_observed": datetime.now(UTC) - timedelta(days=random.randint(1, 30)),  # nosec B311
                "last_observed": datetime.now(UTC) - timedelta(hours=random.randint(1, 24)),  # nosec B311
                "frequency": random.choice(["rare", "occasional", "frequent", "persistent"]),  # nosec B311
                "indicators": self._generate_pattern_indicators(pattern_type),
                "related_events": random.randint(5, 100),  # nosec B311
            }

            patterns.append(pattern)

        return patterns

    async def generate_alert_data(self, alert_count: int = 25, days_back: int = 7) -> list[dict[str, Any]]:
        """Generate mock security alert data.

        Args:
            alert_count: Number of alerts to generate
            days_back: Days of alert history

        Returns:
            List of security alerts
        """
        alerts = []
        alert_types = [
            "Failed Login Attempts",
            "Suspicious File Access",
            "Privilege Escalation",
            "Data Exfiltration",
            "Malware Detection",
            "Network Anomaly",
            "Policy Violation",
            "Unauthorized Access",
            "Brute Force Attack",
        ]

        for _i in range(alert_count):
            alert_time = datetime.now(UTC) - timedelta(
                days=random.randint(0, days_back),  # nosec B311
                hours=random.randint(0, 23),  # nosec B311
            )

            alert_type = random.choice(alert_types)  # nosec B311
            severity = random.choices(["low", "medium", "high", "critical"], weights=[40, 35, 20, 5])[0]  # nosec B311

            alert = {
                "alert_id": str(uuid.uuid4()),
                "alert_type": alert_type,
                "severity": severity,
                "timestamp": alert_time,
                "status": random.choice(["open", "investigating", "resolved", "closed"]),  # nosec B311
                "assigned_to": f"analyst_{random.randint(1, 5)}" if random.random() > 0.3 else None,  # nosec B311
                "source_ip": self._generate_ip_address(),
                "affected_user": f"user_{random.randint(1000, 9999)}",  # nosec B311
                "description": f"{alert_type} detected for user",
                "evidence_count": random.randint(1, 10),  # nosec B311
                "false_positive_likelihood": random.uniform(0, 30),  # nosec B311
                "remediation_steps": [
                    f"Step 1: Investigate {alert_type.lower()}",
                    "Step 2: Contact affected user",
                    "Step 3: Review system logs",
                ],
            }

            alerts.append(alert)

        return sorted(alerts, key=lambda x: x["timestamp"], reverse=True)

    async def generate_investigation_data(
        self,
        start_time: datetime,
        end_time: datetime,
        entity_count: int = 5,
    ) -> dict[str, list[dict[str, Any]]]:
        """Generate mock investigation data for incident analysis.

        Args:
            entity_count: Number of entities to investigate
            start_time: Investigation start time
            end_time: Investigation end time

        Returns:
            Investigation data with entities and events
        """
        investigation_data = {"entities": []}

        for _i in range(entity_count):
            entity_type = random.choice(["user", "ip_address", "device"])  # nosec B311

            if entity_type == "user":
                entity_id = f"user_{random.randint(1000, 9999)}"  # nosec B311
            elif entity_type == "ip_address":
                entity_id = self._generate_ip_address()
            else:  # device
                entity_id = f"device_{uuid.uuid4().hex[:8]}"

            # Generate events for this entity
            event_count = random.randint(3, 25)  # nosec B311
            events = []

            for j in range(event_count):
                event_time = start_time + timedelta(
                    seconds=random.uniform(0, (end_time - start_time).total_seconds()),  # nosec B311
                )

                event = {
                    "timestamp": event_time,
                    "event_type": random.choice(self._event_types),  # nosec B311
                    "risk_score": random.randint(1, 100),  # nosec B311
                    "description": f"Security event {j+1} for {entity_id}",
                }
                events.append(event)

            # Generate anomaly indicators
            anomaly_indicators = []
            if random.random() > 0.5:  # nosec B311
                anomaly_indicators.extend(["Unusual access time", "Multiple failed attempts", "Geographic anomaly"])

            entity_data = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "risk_score": random.randint(20, 95),  # nosec B311
                "anomaly_indicators": anomaly_indicators,
                "events": sorted(events, key=lambda x: x["timestamp"]),
            }

            investigation_data["entities"].append(entity_data)

        return investigation_data

    def _select_weighted_event_type(self, event_types: list[str]) -> str:
        """Select event type with realistic weighting."""
        # Weight common events higher
        weights = []
        for event_type in event_types:
            if event_type in ["user_login", "api_request", "data_access"]:
                weights.append(3)  # Common events
            elif event_type in ["failed_login", "suspicious_activity", "security_alert"]:
                weights.append(1)  # Security events
            else:
                weights.append(2)  # Regular events

        return random.choices(event_types, weights=weights)[0]  # nosec B311

    def _generate_ip_address(self) -> str:
        """Generate a realistic IP address."""
        ip_range = random.choice(self._ip_ranges)  # nosec B311
        last_octet = random.randint(1, 254)  # nosec B311
        return f"{ip_range}{last_octet}"

    def _generate_risk_score(self, event_type: str) -> int:
        """Generate risk score based on event type."""
        if event_type in ["failed_login", "suspicious_activity", "security_alert"]:
            return random.randint(60, 95)  # nosec B311
        if event_type in ["permission_change", "system_change"]:
            return random.randint(40, 80)  # nosec B311
        return random.randint(10, 50)  # nosec B311

    def _generate_event_details(self, event_type: str) -> dict[str, Any]:
        """Generate event-specific details."""
        details = {
            "source": random.choice(["web", "api", "mobile", "desktop"]),  # nosec B311
            "protocol": random.choice(["https", "http", "ssh", "ftp"]),  # nosec B311
        }

        if event_type == "file_upload":
            details.update(
                {
                    "file_size": random.randint(1024, 10485760),  # nosec B311
                    "file_type": random.choice(["pdf", "doc", "xls", "img", "txt"]),  # nosec B311
                },
            )
        elif event_type == "data_access":
            details.update(
                {
                    "database": random.choice(["users", "transactions", "logs"]),  # nosec B311
                    "query_type": random.choice(["select", "insert", "update", "delete"]),  # nosec B311
                },
            )

        return details

    def _generate_location(self) -> dict[str, str]:
        """Generate realistic location data."""
        locations = [
            {"country": "US", "state": "CA", "city": "San Francisco"},
            {"country": "US", "state": "NY", "city": "New York"},
            {"country": "UK", "state": "England", "city": "London"},
            {"country": "DE", "state": "Bavaria", "city": "Munich"},
            {"country": "JP", "state": "Tokyo", "city": "Tokyo"},
        ]
        return random.choice(locations)  # nosec B311

    def _generate_success_status(self, event_type: str) -> bool:
        """Generate success status based on event type."""
        if event_type == "failed_login":
            return False
        if event_type in ["suspicious_activity", "security_alert"]:
            return random.random() > 0.7  # nosec B311
        return random.random() > 0.05  # nosec B311

    def _calculate_pattern_risk_score(self, pattern_type: str, confidence: float) -> int:
        """Calculate risk score for behavioral pattern."""
        base_risk = {
            "data_exfiltration": 90,
            "privilege_escalation": 85,
            "lateral_movement": 80,
            "brute_force": 70,
            "unusual_access": 60,
            "anomalous_login": 50,
            "time_anomaly": 40,
            "location_anomaly": 45,
            "device_anomaly": 35,
        }.get(pattern_type, 50)

        # Adjust based on confidence
        confidence_factor = confidence / 100.0
        return int(base_risk * confidence_factor)

    def _generate_pattern_description(self, pattern_type: str) -> str:
        """Generate description for behavioral pattern."""
        descriptions = {
            "unusual_access": "Unusual resource access patterns detected",
            "anomalous_login": "Login behavior differs from historical patterns",
            "data_exfiltration": "Potential data exfiltration activity identified",
            "privilege_escalation": "Possible privilege escalation attempts",
            "lateral_movement": "Lateral movement patterns across systems",
            "brute_force": "Brute force attack patterns detected",
            "time_anomaly": "Activity outside normal time windows",
            "location_anomaly": "Geographic access anomalies identified",
            "device_anomaly": "Unusual device or browser patterns",
        }
        return descriptions.get(pattern_type, f"Pattern of type {pattern_type} detected")

    def _generate_pattern_indicators(self, pattern_type: str) -> list[str]:
        """Generate indicators for behavioral pattern."""
        all_indicators = {
            "unusual_access": [
                "Access to restricted resources",
                "Multiple resource access in short time",
                "Access outside normal working hours",
            ],
            "anomalous_login": [
                "Multiple failed login attempts",
                "Login from new geographic location",
                "Unusual login timing patterns",
            ],
            "data_exfiltration": [
                "Large data downloads",
                "Access to sensitive databases",
                "Data compression activities",
            ],
            "privilege_escalation": [
                "Attempts to access admin functions",
                "Permission modification requests",
                "Elevated command execution",
            ],
        }

        indicators = all_indicators.get(pattern_type, ["Generic suspicious activity"])
        return random.sample(indicators, min(len(indicators), random.randint(1, 3)))  # nosec B311

    async def get_cached_data(self, cache_key: str) -> Any | None:
        """Get cached mock data if available."""
        return self._cache.get(cache_key)

    async def set_cached_data(self, cache_key: str, data: Any) -> None:
        """Cache mock data for reuse."""
        self._cache[cache_key] = data

    async def clear_cache(self) -> None:
        """Clear the mock data cache."""
        self._cache.clear()

    async def get_user_risk_profile(self, user_id: str) -> dict[str, Any]:
        """Generate user risk profile data for a specific user.

        Args:
            user_id: User identifier

        Returns:
            User risk profile data dictionary
        """
        # Generate deterministic but varied risk scores based on user_id
        risk_score = hash(user_id) % 100

        # Determine risk level based on score
        if risk_score < 30:
            risk_level = "low"
        elif risk_score < 60:
            risk_level = "medium"
        elif risk_score < 80:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Generate mock suspicious activities based on risk level
        suspicious_activities = []
        if risk_score > 40:
            suspicious_activities.append("unusual_time")
        if risk_score > 60:
            suspicious_activities.append("new_location")
        if risk_score > 80:
            suspicious_activities.append("unusual_device")

        # Generate recommendations based on risk level
        recommendations = []
        if risk_level == "medium":
            recommendations.extend(["Enable MFA", "Review login locations"])
        elif risk_level == "high":
            recommendations.extend(["Enable MFA", "Monitor closely", "Review permissions"])
        elif risk_level == "critical":
            recommendations.extend(["Immediate security review", "Contact user", "Consider lockout"])

        return {
            "user_id": user_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "total_logins": hash(user_id + "logins") % 500 + 10,
            "failed_logins_today": hash(user_id + "failed") % 10,
            "last_activity": datetime.now(UTC) - timedelta(hours=hash(user_id) % 48),
            "known_locations": hash(user_id + "locations") % 10 + 1,
            "suspicious_activities": suspicious_activities,
            "recommendations": recommendations,
        }

    async def get_event_timeline_data(self, hours_back: int = 24) -> dict[str, Any]:
        """Generate event timeline data for dashboard charts.

        Args:
            hours_back: Hours of historical data to include

        Returns:
            Timeline data formatted for chart display
        """
        current_time = datetime.now(UTC)
        start_time = current_time - timedelta(hours=hours_back)

        timeline_data = []
        interval_minutes = 60  # 1-hour intervals

        current_interval = start_time
        while current_interval < current_time:
            # Generate mock event counts for this interval
            base_count = hash(current_interval.isoformat()) % 50 + 10  # 10-60 events

            data_point = {
                "timestamp": current_interval,
                "event_count": base_count,
                "total_events": base_count,
                "login_success": int(base_count * 0.7),
                "login_failure": int(base_count * 0.15),
                "suspicious_activity": int(base_count * 0.1),
                "alerts_generated": int(base_count * 0.05),
            }

            timeline_data.append(data_point)
            current_interval += timedelta(minutes=interval_minutes)

        return {
            "timeline": timeline_data,
            "metadata": {
                "start_time": start_time.isoformat(),
                "end_time": current_time.isoformat(),
                "granularity": "hour",
                "data_points": len(timeline_data),
                "total_hours": hours_back,
            },
        }

    async def get_risk_distribution_data(self) -> dict[str, Any]:
        """Generate risk score distribution data for dashboard charts.

        Returns:
            Risk distribution data for pie/bar charts
        """
        # Generate realistic risk distribution
        risk_distribution_data = [
            {"risk_level": "low", "count": 150},
            {"risk_level": "medium", "count": 75},
            {"risk_level": "high", "count": 25},
            {"risk_level": "critical", "count": 5},
        ]

        total_users = sum(item["count"] for item in risk_distribution_data)

        # Convert to percentage
        for item in risk_distribution_data:
            item["percentage"] = (item["count"] / total_users * 100) if total_users > 0 else 0

        return {
            "distribution": risk_distribution_data,
            "total_users": total_users,
            "chart_data": [
                {"label": item["risk_level"].title(), "value": item["count"], "percentage": item["percentage"]}
                for item in risk_distribution_data
            ],
        }
