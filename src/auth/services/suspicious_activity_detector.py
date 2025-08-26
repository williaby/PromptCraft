"""Suspicious activity detection engine with pattern analysis and anomaly detection.

This module provides comprehensive suspicious activity detection with:
- IP geolocation anomaly detection for unusual login locations
- Time-based pattern analysis for off-hours activity
- User agent fingerprinting for device/browser anomalies
- Velocity-based detection for impossible travel scenarios
- Behavioral pattern learning and deviation detection
- Risk scoring based on multiple factors
- Configurable detection rules and thresholds

Performance target: < 100ms per activity analysis
Architecture: Real-time pattern analysis with historical baseline learning
"""

import hashlib
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from src.auth.database.security_events_postgres import SecurityEventsDatabase
from src.auth.security_logger import SecurityLogger


class AnomalyType(str, Enum):
    """Types of anomalies detected."""

    NEW_LOCATION = "new_location"
    UNUSUAL_TIME = "unusual_time"
    RAPID_REQUESTS = "rapid_requests"
    MULTIPLE_FAILURES = "multiple_failures"
    CREDENTIAL_STUFFING = "credential_stuffing"
    IP_HOPPING = "ip_hopping"


from typing import Any

from ..models import SecurityEventCreate, SecurityEventType


class SuspiciousActivityType(str, Enum):
    """Types of suspicious activities for classification."""

    # Location-based anomalies
    GEOLOCATION_ANOMALY = "geolocation_anomaly"
    IMPOSSIBLE_TRAVEL = "impossible_travel"
    NEW_LOCATION = "new_location"

    # Time-based anomalies
    OFF_HOURS_ACCESS = "off_hours_access"
    UNUSUAL_TIME_PATTERN = "unusual_time_pattern"

    # Device/browser anomalies
    NEW_USER_AGENT = "new_user_agent"
    SUSPICIOUS_USER_AGENT = "suspicious_user_agent"
    USER_AGENT_ROTATION = "user_agent_rotation"

    # Behavioral anomalies
    VELOCITY_ANOMALY = "velocity_anomaly"
    ACCESS_PATTERN_CHANGE = "access_pattern_change"
    REPEATED_FAILURES = "repeated_failures"

    # Account anomalies
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DORMANT_ACCOUNT_ACTIVATION = "dormant_account_activation"


@dataclass
class SuspiciousActivityConfig:
    """Configuration for suspicious activity detection."""

    # Geolocation settings
    enable_geolocation_check: bool = True
    max_distance_km: float = 1000.0  # Max reasonable distance between logins
    impossible_travel_speed_kmh: float = 900.0  # Commercial flight speed

    # Time-based settings
    enable_time_analysis: bool = True
    business_hours_start: int = 8  # 8 AM
    business_hours_end: int = 18  # 6 PM
    weekend_risk_multiplier: float = 1.5

    # User agent settings
    enable_user_agent_analysis: bool = True
    suspicious_user_agent_patterns: set[str] = field(
        default_factory=lambda: {
            "curl",
            "wget",
            "python-requests",
            "bot",
            "crawler",
            "scanner",
            "postman",
            "insomnia",
            "sqlmap",
            "nmap",
            "masscan",
        },
    )

    # Behavioral settings
    enable_behavioral_analysis: bool = True
    historical_window_days: int = 30  # Days to analyze for patterns
    minimum_baseline_events: int = 10  # Min events needed for baseline

    # Risk scoring
    base_risk_score: int = 10
    max_risk_score: int = 100
    risk_threshold_suspicious: int = 40
    risk_threshold_critical: int = 70


@dataclass
class LocationData:
    """IP address geolocation data."""

    ip_address: str
    country: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    isp: str | None = None
    is_proxy: bool = False
    is_tor: bool = False

    # Calculated fields
    location_hash: str | None = None

    def __post_init__(self):
        """Generate location hash for comparison."""
        if self.latitude and self.longitude:
            location_str = f"{self.country}:{self.city}:{self.latitude:.2f}:{self.longitude:.2f}"
            self.location_hash = hashlib.md5(location_str.encode()).hexdigest()[:16]


@dataclass
class RiskScore:
    """Risk score calculation result."""

    def __init__(self, score: int = 0, factors: list[str] | None = None):
        self.score = min(max(score, 0), 100)  # Clamp between 0-100
        self.factors = factors or []
        self.level = self._calculate_level()

    def _calculate_level(self) -> str:
        """Calculate risk level based on score."""
        if self.score >= 80:
            return "critical"
        if self.score >= 60:
            return "high"
        if self.score >= 40:
            return "medium"
        return "low"


class ActivityPattern:
    """Activity pattern for tracking user behavior."""

    def __init__(self):
        self.ip_addresses: set[str] = set()
        self.user_agents: set[str] = set()
        self.access_times: list[datetime] = []
        self.failed_attempts: int = 0
        self.successful_attempts: int = 0
        self.risk_events: list[str] = []


class BehaviorProfile:
    """User behavior profile for pattern analysis."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.login_patterns: dict[str, Any] = {}
        self.activity_patterns: list[ActivityPattern] = []
        self.risk_events: list[str] = []
        self.baseline_established: bool = False


class UserPattern:
    """Historical user behavior patterns for anomaly detection."""

    user_id: str

    # Location patterns
    known_locations: set[str] = field(default_factory=set)  # Location hashes
    known_countries: set[str] = field(default_factory=set)
    known_ips: set[str] = field(default_factory=set)

    # Time patterns
    typical_login_hours: dict[int, int] = field(default_factory=dict)  # Hour -> count
    typical_days: dict[int, int] = field(default_factory=dict)  # Day of week -> count

    # Device patterns
    known_user_agents: set[str] = field(default_factory=set)
    user_agent_hashes: set[str] = field(default_factory=set)

    # Activity patterns
    average_session_duration_minutes: float = 0.0
    typical_activity_volume: float = 0.0
    last_activity_time: datetime | None = None

    # Statistics
    total_logins: int = 0
    first_seen: datetime | None = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ActivityAnalysisResult:
    """Result of suspicious activity analysis."""

    is_suspicious: bool = False
    risk_score: int = 0
    detected_activities: list[SuspiciousActivityType] = field(default_factory=list)
    risk_factors: dict[str, Any] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)

    # Analysis details
    location_analysis: dict[str, Any] = field(default_factory=dict)
    time_analysis: dict[str, Any] = field(default_factory=dict)
    user_agent_analysis: dict[str, Any] = field(default_factory=dict)
    behavioral_analysis: dict[str, Any] = field(default_factory=dict)


class SuspiciousActivityDetector:
    """Comprehensive suspicious activity detection engine."""

    def __init__(
        self,
        config: SuspiciousActivityConfig | None = None,
        suspicious_threshold: float | None = None,
        anomaly_threshold: float | None = None,
        learning_period_days: int | None = None,
        min_baseline_events: int | None = None,
        db: Any | None = None,
        security_logger: Any | None = None,
    ) -> None:
        """Initialize suspicious activity detector.

        Args:
            config: Detection configuration (uses defaults if None)
            suspicious_threshold: Override for suspicious activity threshold
            anomaly_threshold: Override for anomaly detection threshold
            learning_period_days: Override for learning period
            min_baseline_events: Override for minimum baseline events
            db: Database connection (optional)
            security_logger: Security logger instance (optional)
        """
        self.config = config or SuspiciousActivityConfig()

        # Apply overrides if provided (create new attributes if needed)
        if suspicious_threshold is not None:
            self.config.risk_threshold_suspicious = int(suspicious_threshold * 100)
        if anomaly_threshold is not None:
            self.config.risk_threshold_critical = int(anomaly_threshold * 100)
        if learning_period_days is not None:
            self.config.historical_window_days = learning_period_days
        if min_baseline_events is not None:
            self.config.minimum_baseline_events = min_baseline_events

        # Expose commonly used thresholds as attributes for backward compatibility
        # Use existing config values or provide defaults
        self.suspicious_threshold = getattr(self.config, "risk_threshold_suspicious", 40) / 100.0
        self.anomaly_threshold = getattr(self.config, "risk_threshold_critical", 80) / 100.0
        self.critical_threshold = getattr(self.config, "risk_threshold_critical", 80) / 100.0
        self.max_failed_attempts = getattr(self.config, "max_failed_attempts", 5)
        self.learning_period_days = getattr(self.config, "historical_window_days", 30)
        self.min_baseline_events = getattr(self.config, "minimum_baseline_events", 10)

        # Store optional dependencies
        self._db = db if db is not None else SecurityEventsDatabase()
        self._security_logger = security_logger if security_logger is not None else SecurityLogger()

        # User pattern storage (in production, this would use database)
        self.user_patterns: dict[str, UserPattern] = {}

        # IP location cache (in production, this would use external geolocation service)
        self.location_cache: dict[str, LocationData] = {}

        # Activity tracking for velocity analysis
        self.recent_activities: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Initialize known suspicious IP patterns
        self._initialize_threat_intelligence()

    async def initialize(self) -> None:
        """Initialize the suspicious activity detector and dependencies.

        This method ensures all dependencies are initialized and threat intelligence is updated.
        It's idempotent and can be called multiple times safely.
        """
        # Initialize database
        if hasattr(self._db, "initialize"):
            await self._db.initialize()

        # Initialize security logger
        if hasattr(self._security_logger, "initialize"):
            await self._security_logger.initialize()

        # Update threat intelligence (in production, this would fetch fresh data)
        self._initialize_threat_intelligence()

    def _initialize_threat_intelligence(self) -> None:
        """Initialize threat intelligence data (simplified for demo)."""
        # In production, this would integrate with threat intelligence feeds
        self.known_malicious_ips: set[str] = set()
        self.known_proxy_ips: set[str] = set()
        self.tor_exit_nodes: set[str] = set()

    async def analyze_activity(
        self, event: SecurityEventCreate, additional_context: dict[str, Any] | None = None,
    ) -> ActivityAnalysisResult:
        """Analyze activity for suspicious patterns.

        Args:
            event: Security event to analyze
            additional_context: Additional context data

        Returns:
            Analysis result with risk assessment and recommendations
        """
        start_time = time.time()

        result = ActivityAnalysisResult()

        try:
            # Only analyze relevant event types
            if not self._should_analyze_event(event):
                return result

            # Get or create user pattern
            user_pattern = await self._get_user_pattern(event.user_id)

            # Perform different types of analysis
            if self.config.enable_geolocation_check and event.ip_address:
                location_result = await self._analyze_location(event, user_pattern)
                result.location_analysis = location_result
                self._merge_analysis_results(result, location_result)

            if self.config.enable_time_analysis:
                time_result = await self._analyze_time_patterns(event, user_pattern)
                result.time_analysis = time_result
                self._merge_analysis_results(result, time_result)

            if self.config.enable_user_agent_analysis and event.user_agent:
                ua_result = await self._analyze_user_agent(event, user_pattern)
                result.user_agent_analysis = ua_result
                self._merge_analysis_results(result, ua_result)

            if self.config.enable_behavioral_analysis:
                behavioral_result = await self._analyze_behavioral_patterns(event, user_pattern)
                result.behavioral_analysis = behavioral_result
                self._merge_analysis_results(result, behavioral_result)

            # Update user pattern with new data
            await self._update_user_pattern(event, user_pattern)

            # Generate recommendations based on findings
            result.recommendations = self._generate_recommendations(result)

            # Final risk assessment
            result.is_suspicious = result.risk_score >= self.config.risk_threshold_suspicious

            # Track processing time (should be < 100ms)
            processing_time_ms = (time.time() - start_time) * 1000
            result.risk_factors["analysis_time_ms"] = processing_time_ms

            return result

        except Exception as e:
            print(f"Error in activity analysis: {e}")
            # Return safe default result
            result.risk_score = self.config.base_risk_score
            result.risk_factors["analysis_error"] = str(e)
            return result

    def _should_analyze_event(self, event: SecurityEventCreate) -> bool:
        """Check if event should be analyzed for suspicious activity."""
        analyzable_events = {
            SecurityEventType.LOGIN_SUCCESS,
            SecurityEventType.LOGIN_FAILURE,
            SecurityEventType.SERVICE_TOKEN_AUTH,
            SecurityEventType.SUSPICIOUS_ACTIVITY,
        }
        return event.event_type in analyzable_events and event.user_id

    async def _get_user_pattern(self, user_id: str | None) -> UserPattern | None:
        """Get or create user pattern for analysis."""
        if not user_id:
            return None

        if user_id not in self.user_patterns:
            self.user_patterns[user_id] = UserPattern(user_id=user_id, first_seen=datetime.now(UTC))

        return self.user_patterns[user_id]

    async def _analyze_location(
        self, event: SecurityEventCreate, user_pattern: UserPattern | None,
    ) -> dict[str, Any]:
        """Analyze location-based suspicious activity."""
        result = {"detected_activities": [], "risk_factors": {}, "risk_score_delta": 0}

        if not event.ip_address or not user_pattern:
            return result

        # Get location data for IP
        location = await self._get_location_data(event.ip_address)

        if not location or not location.location_hash:
            result["risk_factors"]["unknown_location"] = True
            result["risk_score_delta"] += 10
            return result

        # Check for new location
        if location.location_hash not in user_pattern.known_locations:
            result["detected_activities"].append(SuspiciousActivityType.NEW_LOCATION)
            result["risk_factors"]["new_location"] = {"country": location.country, "city": location.city}
            result["risk_score_delta"] += 15

        # Check for geolocation anomaly (distance from known locations)
        if user_pattern.known_locations:
            min_distance = await self._calculate_min_distance_to_known_locations(location, user_pattern.known_locations)

            if min_distance > self.config.max_distance_km:
                result["detected_activities"].append(SuspiciousActivityType.GEOLOCATION_ANOMALY)
                result["risk_factors"]["distance_anomaly"] = {
                    "distance_km": min_distance,
                    "threshold_km": self.config.max_distance_km,
                }
                result["risk_score_delta"] += min(30, int(min_distance / 1000 * 10))

        # Check for impossible travel
        if user_pattern.last_activity_time and user_pattern.known_locations:
            time_diff_hours = (event.timestamp - user_pattern.last_activity_time).total_seconds() / 3600

            if time_diff_hours < 24:  # Only check for recent activity
                max_possible_distance = time_diff_hours * self.config.impossible_travel_speed_kmh
                min_distance = await self._calculate_min_distance_to_known_locations(
                    location, user_pattern.known_locations,
                )

                if min_distance > max_possible_distance:
                    result["detected_activities"].append(SuspiciousActivityType.IMPOSSIBLE_TRAVEL)
                    result["risk_factors"]["impossible_travel"] = {
                        "required_speed_kmh": min_distance / time_diff_hours if time_diff_hours > 0 else float("inf"),
                        "max_possible_speed_kmh": self.config.impossible_travel_speed_kmh,
                        "time_diff_hours": time_diff_hours,
                    }
                    result["risk_score_delta"] += 40

        # Check for proxy/VPN/Tor usage
        if location.is_proxy or location.is_tor:
            result["risk_factors"]["anonymization_service"] = {"is_proxy": location.is_proxy, "is_tor": location.is_tor}
            result["risk_score_delta"] += 25 if location.is_tor else 15

        return result

    async def _analyze_time_patterns(
        self, event: SecurityEventCreate, user_pattern: UserPattern | None,
    ) -> dict[str, Any]:
        """Analyze time-based suspicious activity."""
        result = {"detected_activities": [], "risk_factors": {}, "risk_score_delta": 0}

        if not event.timestamp or not user_pattern:
            return result

        event_time = event.timestamp
        hour = event_time.hour
        day_of_week = event_time.weekday()  # 0 = Monday, 6 = Sunday

        # Check for off-hours access
        is_business_hours = self.config.business_hours_start <= hour < self.config.business_hours_end
        is_weekend = day_of_week >= 5  # Saturday, Sunday

        if not is_business_hours or is_weekend:
            result["detected_activities"].append(SuspiciousActivityType.OFF_HOURS_ACCESS)
            result["risk_factors"]["off_hours"] = {"hour": hour, "day_of_week": day_of_week, "is_weekend": is_weekend}
            risk_delta = 10
            if is_weekend:
                risk_delta = int(risk_delta * self.config.weekend_risk_multiplier)
            result["risk_score_delta"] += risk_delta

        # Check against user's typical patterns (if we have enough data)
        if user_pattern.total_logins >= self.config.minimum_baseline_events:
            # Analyze hour pattern
            total_hour_logins = sum(user_pattern.typical_login_hours.values())
            if total_hour_logins > 0:
                hour_frequency = user_pattern.typical_login_hours.get(hour, 0) / total_hour_logins

                if hour_frequency < 0.05:  # Less than 5% of typical logins at this hour
                    result["detected_activities"].append(SuspiciousActivityType.UNUSUAL_TIME_PATTERN)
                    result["risk_factors"]["unusual_hour_pattern"] = {
                        "hour": hour,
                        "frequency": hour_frequency,
                        "threshold": 0.05,
                    }
                    result["risk_score_delta"] += 20

            # Analyze day pattern
            total_day_logins = sum(user_pattern.typical_days.values())
            if total_day_logins > 0:
                day_frequency = user_pattern.typical_days.get(day_of_week, 0) / total_day_logins

                if day_frequency < 0.1:  # Less than 10% of typical logins on this day
                    result["risk_factors"]["unusual_day_pattern"] = {
                        "day_of_week": day_of_week,
                        "frequency": day_frequency,
                        "threshold": 0.1,
                    }
                    result["risk_score_delta"] += 15

        return result

    async def _analyze_user_agent(
        self, event: SecurityEventCreate, user_pattern: UserPattern | None,
    ) -> dict[str, Any]:
        """Analyze user agent for suspicious patterns."""
        result = {"detected_activities": [], "risk_factors": {}, "risk_score_delta": 0}

        if not event.user_agent or not user_pattern:
            return result

        user_agent = event.user_agent.lower()
        user_agent_hash = hashlib.md5(event.user_agent.encode()).hexdigest()[:16]

        # Check for suspicious user agent patterns
        for pattern in self.config.suspicious_user_agent_patterns:
            if pattern in user_agent:
                result["detected_activities"].append(SuspiciousActivityType.SUSPICIOUS_USER_AGENT)
                result["risk_factors"]["suspicious_user_agent"] = {
                    "pattern": pattern,
                    "user_agent": event.user_agent[:100],  # Truncate for logging
                }
                result["risk_score_delta"] += 35
                break

        # Check for new user agent
        if user_agent_hash not in user_pattern.user_agent_hashes:
            result["detected_activities"].append(SuspiciousActivityType.NEW_USER_AGENT)
            result["risk_factors"]["new_user_agent"] = {"user_agent": event.user_agent[:100]}
            result["risk_score_delta"] += 10

        # Check for user agent rotation (too many different user agents)
        if len(user_pattern.user_agent_hashes) > 10:  # More than 10 different user agents
            recent_agents = len(user_pattern.user_agent_hashes)
            if recent_agents / max(user_pattern.total_logins, 1) > 0.5:  # More than 50% rotation
                result["detected_activities"].append(SuspiciousActivityType.USER_AGENT_ROTATION)
                result["risk_factors"]["user_agent_rotation"] = {
                    "unique_user_agents": recent_agents,
                    "total_logins": user_pattern.total_logins,
                    "rotation_ratio": recent_agents / user_pattern.total_logins,
                }
                result["risk_score_delta"] += 25

        return result

    async def _analyze_behavioral_patterns(
        self, event: SecurityEventCreate, user_pattern: UserPattern | None,
    ) -> dict[str, Any]:
        """Analyze behavioral patterns for anomalies."""
        result = {"detected_activities": [], "risk_factors": {}, "risk_score_delta": 0}

        if not user_pattern:
            return result

        # Check for dormant account activation
        if user_pattern.last_activity_time:
            inactivity_days = (event.timestamp - user_pattern.last_activity_time).days
            if inactivity_days > 90:  # More than 90 days inactive
                result["detected_activities"].append(SuspiciousActivityType.DORMANT_ACCOUNT_ACTIVATION)
                result["risk_factors"]["dormant_account"] = {
                    "inactivity_days": inactivity_days,
                    "last_activity": user_pattern.last_activity_time.isoformat(),
                }
                result["risk_score_delta"] += min(30, inactivity_days // 30 * 10)

        # Track activity for velocity analysis
        if event.user_id:
            current_time = time.time()
            self.recent_activities[event.user_id].append(current_time)

            # Check for velocity anomalies (too much activity in short time)
            recent_window = current_time - 3600  # Last hour
            recent_count = sum(1 for t in self.recent_activities[event.user_id] if t > recent_window)

            if recent_count > 50:  # More than 50 activities in last hour
                result["detected_activities"].append(SuspiciousActivityType.VELOCITY_ANOMALY)
                result["risk_factors"]["velocity_anomaly"] = {"activities_last_hour": recent_count, "threshold": 50}
                result["risk_score_delta"] += 20

        # Check for repeated failures (if this is a login failure)
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            failure_window = current_time - 300  # Last 5 minutes
            recent_failures = sum(
                1 for t in self.recent_activities.get(f"{event.user_id}_failures", []) if t > failure_window
            )

            if recent_failures >= 3:
                result["detected_activities"].append(SuspiciousActivityType.REPEATED_FAILURES)
                result["risk_factors"]["repeated_failures"] = {"failures_last_5min": recent_failures, "threshold": 3}
                result["risk_score_delta"] += 15

            # Track failure for future analysis
            if event.user_id:
                if f"{event.user_id}_failures" not in self.recent_activities:
                    self.recent_activities[f"{event.user_id}_failures"] = deque(maxlen=50)
                self.recent_activities[f"{event.user_id}_failures"].append(current_time)

        return result

    async def _update_user_pattern(self, event: SecurityEventCreate, user_pattern: UserPattern | None) -> None:
        """Update user pattern with new event data."""
        if not user_pattern or not event.user_id:
            return

        # Update location data
        if event.ip_address:
            location = await self._get_location_data(event.ip_address)
            if location and location.location_hash:
                user_pattern.known_locations.add(location.location_hash)
                if location.country:
                    user_pattern.known_countries.add(location.country)
            user_pattern.known_ips.add(event.ip_address)

        # Update time patterns
        if event.timestamp:
            hour = event.timestamp.hour
            day_of_week = event.timestamp.weekday()

            user_pattern.typical_login_hours[hour] = user_pattern.typical_login_hours.get(hour, 0) + 1
            user_pattern.typical_days[day_of_week] = user_pattern.typical_days.get(day_of_week, 0) + 1

        # Update user agent patterns
        if event.user_agent:
            user_agent_hash = hashlib.md5(event.user_agent.encode()).hexdigest()[:16]
            user_pattern.known_user_agents.add(event.user_agent)
            user_pattern.user_agent_hashes.add(user_agent_hash)

        # Update general statistics
        user_pattern.total_logins += 1
        user_pattern.last_activity_time = event.timestamp
        user_pattern.last_updated = datetime.now(UTC)

    async def _get_location_data(self, ip_address: str) -> LocationData | None:
        """Get location data for IP address (simplified implementation)."""
        if ip_address in self.location_cache:
            return self.location_cache[ip_address]

        # In production, this would call a real geolocation service
        # For now, simulate basic location detection
        location = LocationData(ip_address=ip_address)

        # Simulate some basic geolocation patterns
        if ip_address.startswith("192.168.") or ip_address.startswith("10.") or ip_address.startswith("127."):
            # Private IP addresses
            location.country = "Local"
            location.city = "Local Network"
            location.latitude = 0.0
            location.longitude = 0.0
        else:
            # Simulate public IP geolocation (in production, use MaxMind, IPInfo, etc.)
            ip_hash = hashlib.md5(ip_address.encode()).hexdigest()

            # Simple hash-based simulation
            location.country = ["US", "GB", "DE", "FR", "JP", "AU"][int(ip_hash[:2], 16) % 6]
            location.city = f"City_{ip_hash[:4]}"
            location.latitude = float(int(ip_hash[4:6], 16)) - 128  # -128 to 127
            location.longitude = float(int(ip_hash[6:8], 16)) - 128

            # Simulate proxy/Tor detection
            location.is_proxy = int(ip_hash[8:10], 16) < 20  # ~8% chance
            location.is_tor = int(ip_hash[10:12], 16) < 5  # ~2% chance

        # Cache the result
        self.location_cache[ip_address] = location

        return location

    async def _calculate_min_distance_to_known_locations(
        self, current_location: LocationData, known_location_hashes: set[str],
    ) -> float:
        """Calculate minimum distance to any known location."""
        if not current_location.latitude or not current_location.longitude:
            return 0.0

        min_distance = float("inf")

        # Find all locations that match known hashes
        for location in self.location_cache.values():
            if location.location_hash in known_location_hashes and location.latitude and location.longitude:

                distance = self._calculate_distance(
                    current_location.latitude, current_location.longitude, location.latitude, location.longitude,
                )
                min_distance = min(min_distance, distance)

        return min_distance if min_distance != float("inf") else 0.0

    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        import math

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        # Radius of earth in kilometers
        r = 6371

        return c * r

    def _merge_analysis_results(self, main_result: ActivityAnalysisResult, analysis_result: dict[str, Any]) -> None:
        """Merge analysis results into main result."""
        main_result.detected_activities.extend(analysis_result.get("detected_activities", []))
        main_result.risk_factors.update(analysis_result.get("risk_factors", {}))
        main_result.risk_score += analysis_result.get("risk_score_delta", 0)

        # Cap risk score at maximum
        main_result.risk_score = min(main_result.risk_score, self.config.max_risk_score)

    def _generate_recommendations(self, result: ActivityAnalysisResult) -> list[str]:
        """Generate security recommendations based on analysis results."""
        recommendations = []

        if SuspiciousActivityType.GEOLOCATION_ANOMALY in result.detected_activities:
            recommendations.append("Verify user location and consider requiring additional authentication")

        if SuspiciousActivityType.IMPOSSIBLE_TRAVEL in result.detected_activities:
            recommendations.append("Investigate potential account compromise - impossible travel detected")

        if SuspiciousActivityType.SUSPICIOUS_USER_AGENT in result.detected_activities:
            recommendations.append("Block or monitor automated tool usage")

        if SuspiciousActivityType.OFF_HOURS_ACCESS in result.detected_activities:
            recommendations.append("Consider implementing time-based access controls")

        if SuspiciousActivityType.VELOCITY_ANOMALY in result.detected_activities:
            recommendations.append("Implement rate limiting and monitor for automated attacks")

        if SuspiciousActivityType.DORMANT_ACCOUNT_ACTIVATION in result.detected_activities:
            recommendations.append("Require account verification after extended inactivity")

        if result.risk_score >= self.config.risk_threshold_critical:
            recommendations.append("CRITICAL: Consider immediate account lockout and investigation")

        return recommendations

    async def get_user_risk_profile(self, user_id: str) -> dict[str, Any]:
        """Get comprehensive risk profile for a user."""
        user_pattern = self.user_patterns.get(user_id)

        if not user_pattern:
            return {"error": "User not found"}

        return {
            "user_id": user_id,
            "total_logins": user_pattern.total_logins,
            "first_seen": user_pattern.first_seen.isoformat() if user_pattern.first_seen else None,
            "last_activity": user_pattern.last_activity_time.isoformat() if user_pattern.last_activity_time else None,
            "known_locations": len(user_pattern.known_locations),
            "known_countries": list(user_pattern.known_countries),
            "known_ips": len(user_pattern.known_ips),
            "known_user_agents": len(user_pattern.known_user_agents),
            "typical_login_hours": dict(user_pattern.typical_login_hours),
            "typical_days": dict(user_pattern.typical_days),
            "risk_assessment": (
                "established" if user_pattern.total_logins >= self.config.minimum_baseline_events else "new_user"
            ),
        }
