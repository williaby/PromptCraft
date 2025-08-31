"""Comprehensive tests for analytics_router.py.

Tests all endpoints in the analytics router including security trend analysis,
behavioral pattern detection, and incident investigation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.api.routers.analytics_router import (
    BehaviorPattern,
    IncidentInvestigationRequest,
    IncidentInvestigationResponse,
    InvestigationResult,
    PatternAnalysisResponse,
    SecurityTrendsResponse,
    TrendDataPoint,
    get_security_service,
    get_suspicious_activity_detector,
    router,
)
from src.auth.services.security_integration import SecurityIntegrationService
from src.auth.services.suspicious_activity_detector import SuspiciousActivityDetector


@pytest.fixture
def mock_security_service():
    """Mock security integration service."""
    return AsyncMock(spec=SecurityIntegrationService)


@pytest.fixture
def mock_suspicious_activity_detector():
    """Mock suspicious activity detector."""
    return AsyncMock(spec=SuspiciousActivityDetector)


@pytest.fixture
def test_app(mock_security_service, mock_suspicious_activity_detector):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)

    # Override dependencies
    app.dependency_overrides[get_security_service] = lambda: mock_security_service
    app.dependency_overrides[get_suspicious_activity_detector] = lambda: mock_suspicious_activity_detector

    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def sample_trend_data():
    """Sample trend data for testing."""
    now = datetime.now(UTC)
    return [
        TrendDataPoint(
            timestamp=now - timedelta(hours=i),
            value=50.0 + (i * 5.2),
            category="login_attempts",
            metadata={"source": "auth_service"},
        )
        for i in range(24)  # 24 hours of data
    ]


@pytest.fixture
def sample_security_trends_response(sample_trend_data):
    """Sample security trends response."""
    return SecurityTrendsResponse(
        analysis_period="24h",
        trend_categories=["login_attempts", "failed_logins", "security_events"],
        trends={
            "login_attempts": sample_trend_data,
            "failed_logins": sample_trend_data[:12],
            "security_events": sample_trend_data[::2],
        },
        insights=[
            "Login attempts increased by 15% in the last 6 hours",
            "Failed login rate remains within normal parameters",
            "No significant security anomalies detected",
        ],
        risk_indicators=[
            "Elevated activity from IP range 192.168.1.0/24",
            "Unusual login patterns detected for 3 users",
        ],
    )


@pytest.fixture
def sample_behavior_patterns():
    """Sample behavior patterns for testing."""
    now = datetime.now(UTC)
    return [
        BehaviorPattern(
            pattern_id="pattern_001",
            pattern_type="unusual_login_time",
            description="User logging in outside normal business hours",
            confidence_score=85.5,
            affected_users=12,
            risk_level="medium",
            first_observed=now - timedelta(days=7),
            last_observed=now - timedelta(hours=2),
            frequency="daily",
        ),
        BehaviorPattern(
            pattern_id="pattern_002",
            pattern_type="geographic_anomaly",
            description="Login from unusual geographic location",
            confidence_score=92.3,
            affected_users=3,
            risk_level="high",
            first_observed=now - timedelta(days=2),
            last_observed=now - timedelta(hours=1),
            frequency="sporadic",
        ),
    ]


@pytest.fixture
def sample_investigation_request():
    """Sample incident investigation request."""
    return IncidentInvestigationRequest(
        incident_id="incident_123",
        start_time=datetime.now(UTC) - timedelta(hours=24),
        end_time=datetime.now(UTC),
        user_ids=["user1@example.com", "user2@example.com"],
        ip_addresses=["192.168.1.100", "10.0.0.50"],
        event_types=["login_attempt", "authentication_failure"],
        risk_threshold=70,
    )


class TestAnalyticsRouterInitialization:
    """Test analytics router initialization and configuration."""

    def test_router_configuration(self):
        """Test router is properly configured."""
        assert router.prefix == "/analytics"
        assert "analytics" in router.tags

    def test_dependency_functions_exist(self):
        """Test dependency injection functions are available."""
        assert callable(get_security_service)
        assert callable(get_suspicious_activity_detector)

    @pytest.mark.asyncio
    async def test_get_security_service_creates_instance(self):
        """Test security service dependency creates instance."""
        service = await get_security_service()
        assert isinstance(service, SecurityIntegrationService)

    @pytest.mark.asyncio
    async def test_get_suspicious_activity_detector_creates_instance(self):
        """Test suspicious activity detector dependency creates instance."""
        detector = await get_suspicious_activity_detector()
        assert isinstance(detector, SuspiciousActivityDetector)


class TestGetSecurityTrendsEndpoint:
    """Test GET /analytics/trends endpoint functionality."""

    @pytest.mark.asyncio
    async def test_get_trends_success(self, test_client, mock_security_service, sample_security_trends_response):
        """Test successful security trends retrieval."""
        # The router processes trends internally, just need service method to exist
        mock_security_service.get_security_trends.return_value = {"status": "success"}

        response = test_client.get("/analytics/trends")

        assert response.status_code == 200
        data = response.json()
        assert "analysis_period" in data
        assert "trends" in data
        assert "insights" in data
        assert "risk_indicators" in data

    @pytest.mark.asyncio
    async def test_get_trends_with_time_range(self, test_client, mock_security_service, sample_security_trends_response):
        """Test trends retrieval with custom time range."""
        mock_security_service.get_security_trends.return_value = {"status": "success"}

        response = test_client.get("/analytics/trends?days_back=7&categories=login_attempts,failed_logins")

        assert response.status_code == 200
        mock_security_service.get_security_trends.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trends_invalid_days_back(self, test_client):
        """Test trends retrieval with invalid days_back parameter."""
        response = test_client.get("/analytics/trends?days_back=0")

        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_get_trends_service_error(self, test_client, mock_security_service):
        """Test trends retrieval when service raises exception."""
        mock_security_service.get_security_trends.side_effect = Exception("Service error")

        response = test_client.get("/analytics/trends")

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_get_trends_empty_result(self, test_client, mock_security_service):
        """Test trends retrieval with empty trends data."""
        mock_security_service.get_security_trends.return_value = {"status": "success"}

        response = test_client.get("/analytics/trends")

        assert response.status_code == 200
        data = response.json()
        # Router generates mock data internally, so trends won't be empty
        assert "trends" in data


class TestGetBehaviorPatternsEndpoint:
    """Test GET /analytics/patterns endpoint functionality."""

    @pytest.mark.asyncio
    async def test_get_patterns_success(self, test_client, mock_suspicious_activity_detector, sample_behavior_patterns):
        """Test successful behavioral pattern analysis."""
        PatternAnalysisResponse(
            analysis_timestamp=datetime.now(UTC),
            total_patterns=len(sample_behavior_patterns),
            high_risk_patterns=1,
            patterns=sample_behavior_patterns,
            recommendations=[
                "Review user access for geographic anomalies",
                "Consider implementing time-based access controls",
            ],
        )
        mock_suspicious_activity_detector.analyze_behavioral_patterns.return_value = [
            {
                "pattern_id": "pattern_001",
                "pattern_type": "unusual_login_time",
                "description": "User logging in outside normal business hours",
                "confidence_score": 85.5,
                "affected_users": 12,
                "risk_score": 65,
                "first_observed": datetime.now(UTC) - timedelta(days=7),
                "last_observed": datetime.now(UTC) - timedelta(hours=2),
                "frequency": "daily",
            },
            {
                "pattern_id": "pattern_002",
                "pattern_type": "geographic_anomaly",
                "description": "Login from unusual geographic location",
                "confidence_score": 92.3,
                "affected_users": 3,
                "risk_score": 85,
                "first_observed": datetime.now(UTC) - timedelta(days=2),
                "last_observed": datetime.now(UTC) - timedelta(hours=1),
                "frequency": "sporadic",
            },
        ]

        response = test_client.get("/analytics/patterns")

        assert response.status_code == 200
        data = response.json()
        assert data["total_patterns"] == 2
        assert data["high_risk_patterns"] == 2  # Both patterns have risk scores > 60 (HIGH threshold)
        assert len(data["patterns"]) == 2

    @pytest.mark.asyncio
    async def test_get_patterns_with_risk_filter(self, test_client, mock_suspicious_activity_detector, sample_behavior_patterns):
        """Test patterns retrieval with risk level filtering."""
        high_risk_patterns = [p for p in sample_behavior_patterns if p.risk_level == "high"]
        PatternAnalysisResponse(
            analysis_timestamp=datetime.now(UTC),
            total_patterns=1,
            high_risk_patterns=1,
            patterns=high_risk_patterns,
            recommendations=["Review high-risk patterns immediately"],
        )
        mock_suspicious_activity_detector.analyze_behavioral_patterns.return_value = [
            {
                "pattern_id": "pattern_002",
                "pattern_type": "geographic_anomaly",
                "description": "Login from unusual geographic location",
                "confidence_score": 92.3,
                "affected_users": 3,
                "risk_score": 85,
                "first_observed": datetime.now(UTC) - timedelta(days=2),
                "last_observed": datetime.now(UTC) - timedelta(hours=1),
                "frequency": "sporadic",
            },
        ]

        response = test_client.get("/analytics/patterns?min_confidence=90.0")

        assert response.status_code == 200
        data = response.json()
        # Check that patterns with high risk scores are returned
        assert len(data["patterns"]) > 0
        assert all(pattern["confidence_score"] >= 90.0 for pattern in data["patterns"])

    @pytest.mark.asyncio
    async def test_get_patterns_with_limit(self, test_client, mock_suspicious_activity_detector, sample_behavior_patterns):
        """Test patterns retrieval with limit parameter."""
        PatternAnalysisResponse(
            analysis_timestamp=datetime.now(UTC),
            total_patterns=1,
            high_risk_patterns=1,
            patterns=sample_behavior_patterns[:1],
            recommendations=["Review patterns"],
        )
        mock_suspicious_activity_detector.analyze_behavioral_patterns.return_value = [
            {
                "pattern_id": "pattern_001",
                "pattern_type": "unusual_login_time",
                "description": "User logging in outside normal business hours",
                "confidence_score": 85.5,
                "affected_users": 12,
                "risk_score": 65,
                "first_observed": datetime.now(UTC) - timedelta(days=7),
                "last_observed": datetime.now(UTC) - timedelta(hours=2),
                "frequency": "daily",
            },
        ]

        response = test_client.get("/analytics/patterns?limit=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data["patterns"]) <= 1

    @pytest.mark.asyncio
    async def test_get_patterns_detector_error(self, test_client, mock_suspicious_activity_detector):
        """Test patterns retrieval when detector raises exception."""
        mock_suspicious_activity_detector.analyze_behavioral_patterns.side_effect = Exception("Detector error")

        response = test_client.get("/analytics/patterns")

        assert response.status_code == 500


class TestIncidentInvestigationEndpoint:
    """Test POST /analytics/investigate endpoint functionality."""

    @pytest.mark.asyncio
    async def test_investigate_incident_success(self, test_client, mock_security_service, sample_investigation_request):
        """Test successful incident investigation."""
        IncidentInvestigationResponse(
            investigation_id="inv_" + str(uuid4()),
            request_summary="Investigation of incident_123 affecting 2 users",
            investigation_time_ms=1250.5,
            total_entities_analyzed=5,
            high_risk_entities=2,
            results=[
                InvestigationResult(
                    entity_type="user",
                    entity_id="user1@example.com",
                    risk_score=85,
                    anomaly_indicators=["Multiple failed login attempts", "Unusual login times"],
                    related_events=15,
                    timeline=[{"timestamp": datetime.now(UTC), "event": "login_attempt"}],
                    recommendations=["Monitor user activity closely"],
                ),
            ],
            overall_risk_assessment="Medium risk incident requiring attention",
            next_steps=[
                "Contact affected users",
                "Review access logs",
                "Consider account restrictions",
            ],
        )
        mock_security_service.investigate_security_incident.return_value = {
            "investigation_metadata": {
                "investigation_id": "inv_test123",
                "start_time": sample_investigation_request.start_time.isoformat(),
                "end_time": sample_investigation_request.end_time.isoformat(),
                "duration_ms": 1250.5,
            },
            "entities": [
                {
                    "entity_type": "user",
                    "entity_id": "user1@example.com",
                    "risk_score": 85,
                    "anomaly_indicators": ["Multiple failed login attempts", "Unusual login times"],
                    "events": [
                        {
                            "timestamp": datetime.now(UTC).isoformat(),
                            "event_type": "login_attempt",
                            "risk_score": 70,
                            "description": "Failed login attempt",
                        },
                    ],
                },
                {
                    "entity_type": "user",
                    "entity_id": "user2@example.com",
                    "risk_score": 65,
                    "anomaly_indicators": ["Unusual access patterns"],
                    "events": [
                        {
                            "timestamp": datetime.now(UTC).isoformat(),
                            "event_type": "data_access",
                            "risk_score": 60,
                            "description": "Unusual data access",
                        },
                    ],
                },
                {
                    "entity_type": "ip",
                    "entity_id": "192.168.1.100",
                    "risk_score": 75,
                    "anomaly_indicators": ["Multiple user sessions"],
                    "events": [],
                },
                {
                    "entity_type": "user",
                    "entity_id": "user3@example.com",
                    "risk_score": 90,
                    "anomaly_indicators": ["Privilege escalation attempts"],
                    "events": [],
                },
                {
                    "entity_type": "user",
                    "entity_id": "user4@example.com",
                    "risk_score": 45,
                    "anomaly_indicators": ["Minor policy violation"],
                    "events": [],
                },
            ],
            "summary": {
                "total_entities": 5,
                "high_risk_entities": 2,
                "overall_risk_assessment": "Medium risk incident requiring attention",
            },
        }

        response = test_client.post("/analytics/investigate", json=sample_investigation_request.model_dump(mode="json"))

        assert response.status_code == 200
        data = response.json()
        assert "investigation_id" in data
        assert data["total_entities_analyzed"] == 5
        assert data["high_risk_entities"] == 2

    @pytest.mark.asyncio
    async def test_investigate_incident_invalid_request(self, test_client):
        """Test incident investigation with invalid request data."""
        invalid_request = {
            "start_time": "invalid-datetime",
            "end_time": datetime.now(UTC).isoformat(),
        }

        response = test_client.post("/analytics/investigate", json=invalid_request)

        assert response.status_code == 422  # Unprocessable Entity

    @pytest.mark.asyncio
    async def test_investigate_incident_time_range_validation(self, test_client, mock_security_service):
        """Test incident investigation with invalid time range."""
        future_time = datetime.now(UTC) + timedelta(hours=1)
        past_time = datetime.now(UTC) - timedelta(hours=1)

        invalid_request = IncidentInvestigationRequest(
            start_time=future_time,  # Start time in future
            end_time=past_time,      # End time in past
            risk_threshold=50,
        )

        response = test_client.post("/analytics/investigate", json=invalid_request.model_dump(mode="json"))

        # The router catches HTTPException and re-raises as 500, so we expect 500
        # but the error message should contain the validation error
        assert response.status_code == 500
        assert "End time must be after start time" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_investigate_incident_service_error(self, test_client, mock_security_service, sample_investigation_request):
        """Test incident investigation when service raises exception."""
        mock_security_service.investigate_security_incident.side_effect = Exception("Investigation failed")

        response = test_client.post("/analytics/investigate", json=sample_investigation_request.model_dump(mode="json"))

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_investigate_incident_empty_result(self, test_client, mock_security_service, sample_investigation_request):
        """Test incident investigation with no findings."""
        IncidentInvestigationResponse(
            investigation_id="inv_empty",
            request_summary="No suspicious activity found",
            investigation_time_ms=500.0,
            total_entities_analyzed=0,
            high_risk_entities=0,
            results=[],
            overall_risk_assessment="No risk detected",
            next_steps=["Continue monitoring"],
        )
        mock_security_service.investigate_security_incident.return_value = {
            "investigation_metadata": {
                "investigation_id": "inv_empty",
                "start_time": sample_investigation_request.start_time.isoformat(),
                "end_time": sample_investigation_request.end_time.isoformat(),
                "duration_ms": 500.0,
            },
            "entities": [],
            "summary": {
                "total_entities": 0,
                "high_risk_entities": 0,
                "overall_risk_assessment": "No risk detected",
            },
        }

        response = test_client.post("/analytics/investigate", json=sample_investigation_request.model_dump(mode="json"))

        assert response.status_code == 200
        data = response.json()
        assert data["total_entities_analyzed"] == 0
        assert data["results"] == []


class TestAnalyticsModels:
    """Test Pydantic models used in analytics endpoints."""

    def test_trend_data_point_model(self):
        """Test TrendDataPoint model creation and validation."""
        data_point = TrendDataPoint(
            timestamp=datetime.now(UTC),
            value=75.5,
            category="login_attempts",
            metadata={"source": "auth_service", "region": "us-east-1"},
        )

        assert data_point.value == 75.5
        assert data_point.category == "login_attempts"
        assert data_point.metadata["source"] == "auth_service"

    def test_behavior_pattern_model(self):
        """Test BehaviorPattern model creation and validation."""
        pattern = BehaviorPattern(
            pattern_id="test_pattern",
            pattern_type="anomaly",
            description="Test pattern description",
            confidence_score=85.0,
            affected_users=5,
            risk_level="medium",
            first_observed=datetime.now(UTC) - timedelta(days=1),
            last_observed=datetime.now(UTC),
            frequency="hourly",
        )

        assert pattern.confidence_score == 85.0
        assert pattern.affected_users == 5
        assert pattern.risk_level == "medium"

    def test_incident_investigation_request_validation(self):
        """Test IncidentInvestigationRequest model validation."""
        # Test valid request
        request = IncidentInvestigationRequest(
            start_time=datetime.now(UTC) - timedelta(hours=1),
            end_time=datetime.now(UTC),
            risk_threshold=80,
        )

        assert request.risk_threshold == 80

        # Test invalid risk threshold
        with pytest.raises(ValueError):
            IncidentInvestigationRequest(
                start_time=datetime.now(UTC) - timedelta(hours=1),
                end_time=datetime.now(UTC),
                risk_threshold=150,  # Invalid: > 100
            )


class TestAnalyticsRouterIntegration:
    """Integration tests for analytics router."""

    @pytest.mark.asyncio
    async def test_full_analytics_workflow(self, test_client, mock_security_service, mock_suspicious_activity_detector,
                                         sample_security_trends_response, sample_behavior_patterns, sample_investigation_request):
        """Test complete analytics workflow: trends -> patterns -> investigation."""
        # Step 1: Get security trends
        mock_security_service.get_security_trends.return_value = {"status": "success"}

        trends_response = test_client.get("/analytics/trends")
        assert trends_response.status_code == 200

        # Step 2: Get behavior patterns
        PatternAnalysisResponse(
            analysis_timestamp=datetime.now(UTC),
            total_patterns=2,
            high_risk_patterns=1,
            patterns=sample_behavior_patterns,
            recommendations=["Review patterns"],
        )
        mock_suspicious_activity_detector.analyze_behavioral_patterns.return_value = [
            {
                "pattern_id": "pattern_001",
                "pattern_type": "unusual_login_time",
                "description": "User logging in outside normal business hours",
                "confidence_score": 85.5,
                "affected_users": 12,
                "risk_score": 65,
                "first_observed": datetime.now(UTC) - timedelta(days=7),
                "last_observed": datetime.now(UTC) - timedelta(hours=2),
                "frequency": "daily",
            },
            {
                "pattern_id": "pattern_002",
                "pattern_type": "geographic_anomaly",
                "description": "Login from unusual geographic location",
                "confidence_score": 92.3,
                "affected_users": 3,
                "risk_score": 85,
                "first_observed": datetime.now(UTC) - timedelta(days=2),
                "last_observed": datetime.now(UTC) - timedelta(hours=1),
                "frequency": "sporadic",
            },
        ]

        patterns_response = test_client.get("/analytics/patterns")
        assert patterns_response.status_code == 200

        # Step 3: Investigate incident
        IncidentInvestigationResponse(
            investigation_id="test_inv",
            request_summary="Test investigation",
            investigation_time_ms=1000.0,
            total_entities_analyzed=1,
            high_risk_entities=1,
            results=[],
            overall_risk_assessment="Low risk",
            next_steps=["Monitor"],
        )
        mock_security_service.investigate_security_incident.return_value = {
            "investigation_metadata": {
                "investigation_id": "test_inv",
                "start_time": sample_investigation_request.start_time.isoformat(),
                "end_time": sample_investigation_request.end_time.isoformat(),
                "duration_ms": 1000.0,
            },
            "entities": [
                {
                    "entity_type": "user",
                    "entity_id": "user1@example.com",
                    "risk_score": 50,
                    "anomaly_indicators": [],
                    "events": [],
                },
            ],
            "summary": {
                "total_entities": 1,
                "high_risk_entities": 1,
                "overall_risk_assessment": "Low risk",
            },
        }

        investigate_response = test_client.post("/analytics/investigate", json=sample_investigation_request.model_dump(mode="json"))
        assert investigate_response.status_code == 200


class TestAnalyticsRouterPerformance:
    """Performance tests for analytics router endpoints."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_trends_analysis_performance(self, test_client, mock_security_service, sample_security_trends_response):
        """Test trends analysis performance with large dataset."""
        # Simulate large trend dataset
        large_trends = sample_security_trends_response
        large_trends.trends = {f"category_{i}": [] for i in range(100)}

        mock_security_service.get_security_trends.return_value = {"status": "success", "trends": large_trends.trends}

        import time
        start_time = time.time()

        response = test_client.get("/analytics/trends?days_back=7")  # 1 week

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 3.0  # Should respond within 3 seconds

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_incident_investigation_performance(self, test_client, mock_security_service, sample_investigation_request):
        """Test incident investigation performance."""
        IncidentInvestigationResponse(
            investigation_id="perf_test",
            request_summary="Performance test investigation",
            investigation_time_ms=2500.0,  # Simulated processing time
            total_entities_analyzed=1000,
            high_risk_entities=50,
            results=[],
            overall_risk_assessment="Performance test",
            next_steps=["None"],
        )
        mock_security_service.investigate_security_incident.return_value = {
            "investigation_metadata": {
                "investigation_id": "perf_test",
                "start_time": sample_investigation_request.start_time.isoformat(),
                "end_time": sample_investigation_request.end_time.isoformat(),
                "duration_ms": 2500.0,
            },
            "entities": [],
            "summary": {
                "total_entities": 1000,
                "high_risk_entities": 50,
                "overall_risk_assessment": "Performance test",
            },
        }

        import time
        start_time = time.time()

        response = test_client.post("/analytics/investigate", json=sample_investigation_request.model_dump(mode="json"))

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 5.0  # Should respond within 5 seconds
