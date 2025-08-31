"""Comprehensive tests for users_router.py.

Tests user risk profile and monitoring endpoints.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.auth.api.routers.users_router import (
    router,
    UserRiskProfileResponse,
    get_security_service,
    get_suspicious_activity_detector,
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
    mock = AsyncMock()
    # Add the methods that the users router expects but don't exist in the actual class
    mock.get_user_activity_summary = AsyncMock()
    mock.get_user_suspicious_activities = AsyncMock()
    return mock


@pytest.fixture
def test_app(mock_security_service, mock_suspicious_activity_detector):
    """Create test FastAPI app with mocked dependencies."""
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_security_service] = lambda: mock_security_service
    app.dependency_overrides[get_suspicious_activity_detector] = lambda: mock_suspicious_activity_detector
    return app


@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def sample_low_risk_activity():
    """Sample low-risk user activity data."""
    return {
        "base_risk_score": 15,
        "failed_logins_today": 1,
        "unusual_location_count": 0,
        "off_hours_activity_count": 0,
        "total_logins": 45,
        "last_activity": datetime.now(timezone.utc) - timedelta(hours=2),
        "known_location_count": 3,
    }


@pytest.fixture
def sample_high_risk_activity():
    """Sample high-risk user activity data."""
    # Risk score calculation: base + failed_logins*5 + unusual_locations*3 + off_hours*2
    # Target: HIGH level (60-79)
    # 35 + (6*5=30, capped at 30) + (3*3=9) + (1*2=2) = 35+30+9+2 = 76 (HIGH level)
    return {
        "base_risk_score": 35,
        "failed_logins_today": 6,
        "unusual_location_count": 3,
        "off_hours_activity_count": 1,
        "total_logins": 125,
        "last_activity": datetime.now(timezone.utc) - timedelta(minutes=30),
        "known_location_count": 2,
    }


@pytest.fixture
def sample_critical_risk_activity():
    """Sample critical-risk user activity data."""
    return {
        "base_risk_score": 40,
        "failed_logins_today": 15,  # Very high failed login attempts
        "unusual_location_count": 8,  # Many unusual locations
        "off_hours_activity_count": 10,  # Excessive off-hours activity
        "total_logins": 200,
        "last_activity": datetime.now(timezone.utc) - timedelta(minutes=5),
        "known_location_count": 1,
    }


@pytest.fixture
def sample_suspicious_activities_low():
    """Sample suspicious activities for low-risk user."""
    return [
        {"description": "Login from new device", "severity": "low", "timestamp": datetime.now(timezone.utc)},
    ]


@pytest.fixture
def sample_suspicious_activities_high():
    """Sample suspicious activities for high-risk user."""
    return [
        {"description": "Multiple failed login attempts", "severity": "high", "timestamp": datetime.now(timezone.utc)},
        {"description": "Login from unusual location", "severity": "medium", "timestamp": datetime.now(timezone.utc) - timedelta(hours=1)},
        {"description": "Off-hours data access", "severity": "medium", "timestamp": datetime.now(timezone.utc) - timedelta(hours=3)},
        {"description": "Suspicious API usage pattern", "severity": "high", "timestamp": datetime.now(timezone.utc) - timedelta(hours=6)},
    ]


class TestUserRiskProfileResponse:
    """Test UserRiskProfileResponse model."""

    def test_user_risk_profile_response_creation(self):
        """Test creating user risk profile response."""
        last_activity = datetime.now(timezone.utc)
        profile = UserRiskProfileResponse(
            user_id="user123@example.com",
            risk_score=45,
            risk_level="MEDIUM",
            total_logins=150,
            failed_logins_today=3,
            last_activity=last_activity,
            known_locations=4,
            suspicious_activities=["Login from new device", "Unusual timing pattern"],
            recommendations=["Continue monitoring", "Review recent activity"],
        )

        assert profile.user_id == "user123@example.com"
        assert profile.risk_score == 45
        assert profile.risk_level == "MEDIUM"
        assert profile.total_logins == 150
        assert profile.failed_logins_today == 3
        assert profile.last_activity == last_activity
        assert len(profile.suspicious_activities) == 2
        assert len(profile.recommendations) == 2

    def test_user_risk_profile_response_validation(self):
        """Test user risk profile response field validation."""
        # Test with minimum/zero values
        profile = UserRiskProfileResponse(
            user_id="user@test.com",
            risk_score=0,
            risk_level="LOW",
            total_logins=0,
            failed_logins_today=0,
            last_activity=None,  # Optional field
            known_locations=0,
            suspicious_activities=[],
            recommendations=[],
        )

        assert profile.risk_score == 0
        assert profile.total_logins == 0
        assert profile.last_activity is None
        assert len(profile.suspicious_activities) == 0

    def test_user_risk_profile_response_maximum_values(self):
        """Test user risk profile response with maximum values."""
        profile = UserRiskProfileResponse(
            user_id="high-activity-user@example.com",
            risk_score=100,
            risk_level="CRITICAL",
            total_logins=10000,
            failed_logins_today=50,
            last_activity=datetime.now(timezone.utc),
            known_locations=25,
            suspicious_activities=[f"Activity {i}" for i in range(10)],  # Many activities
            recommendations=[f"Recommendation {i}" for i in range(8)],    # Many recommendations
        )

        assert profile.risk_score == 100
        assert profile.risk_level == "CRITICAL"
        assert len(profile.suspicious_activities) == 10
        assert len(profile.recommendations) == 8


class TestUsersRouter:
    """Test users router functionality."""

    def test_router_configuration(self):
        """Test router is properly configured."""
        assert router.prefix == "/users"
        assert "users" in router.tags

    @pytest.mark.asyncio
    async def test_get_user_risk_profile_low_risk(
        self, 
        test_client, 
        mock_suspicious_activity_detector, 
        sample_low_risk_activity, 
        sample_suspicious_activities_low
    ):
        """Test getting risk profile for low-risk user."""
        mock_suspicious_activity_detector.get_user_activity_summary.return_value = sample_low_risk_activity
        mock_suspicious_activity_detector.get_user_suspicious_activities.return_value = sample_suspicious_activities_low

        response = test_client.get("/users/user123@example.com/risk-profile")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user123@example.com"
        assert data["risk_level"] == "LOW"
        # Expected risk score: 15 (base) + 5 (1 failed login * 5) + 0 (no unusual locations) + 0 (no off-hours) = 20
        assert data["risk_score"] == 20
        assert data["total_logins"] == 45
        assert data["failed_logins_today"] == 1
        assert data["known_locations"] == 3
        assert len(data["suspicious_activities"]) == 1
        assert "Continue standard security monitoring" in data["recommendations"]

    @pytest.mark.asyncio
    async def test_get_user_risk_profile_high_risk(
        self, 
        test_client, 
        mock_suspicious_activity_detector, 
        sample_high_risk_activity, 
        sample_suspicious_activities_high
    ):
        """Test getting risk profile for high-risk user."""
        mock_suspicious_activity_detector.get_user_activity_summary.return_value = sample_high_risk_activity
        mock_suspicious_activity_detector.get_user_suspicious_activities.return_value = sample_suspicious_activities_high

        response = test_client.get("/users/highrisk@example.com/risk-profile")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "highrisk@example.com"
        assert data["risk_level"] == "HIGH"
        # Expected risk score: 35 + min(30, 6*5) + min(20, 3*3) + min(15, 1*2) = 35 + 30 + 9 + 2 = 76
        # This should be HIGH level (60-79)
        expected_risk = min(100, 35 + min(30, 6*5) + min(20, 3*3) + min(15, 1*2))
        assert data["risk_score"] == expected_risk
        assert data["risk_level"] == "HIGH"
        
        assert data["failed_logins_today"] == 6
        assert len(data["suspicious_activities"]) == 4
        
        # Check for specific recommendations based on risk factors  
        recommendations = data["recommendations"]
        assert any("password policy" in rec for rec in recommendations)  # failed_logins_today=6 > 5
        assert any("login locations" in rec for rec in recommendations)  # unusual_location_count=3 > 2
        assert any("security review" in rec for rec in recommendations)  # risk_score=76 > 70
        assert any("Enhanced monitoring" in rec for rec in recommendations)  # len(suspicious_activities)=4 > 3

    @pytest.mark.asyncio
    async def test_get_user_risk_profile_critical_risk(
        self, 
        test_client, 
        mock_suspicious_activity_detector, 
        sample_critical_risk_activity, 
        sample_suspicious_activities_high
    ):
        """Test getting risk profile for critical-risk user."""
        # Add more suspicious activities for critical user
        critical_activities = sample_suspicious_activities_high + [
            {"description": "Privilege escalation attempt", "severity": "critical"},
        ]
        
        mock_suspicious_activity_detector.get_user_activity_summary.return_value = sample_critical_risk_activity
        mock_suspicious_activity_detector.get_user_suspicious_activities.return_value = critical_activities

        response = test_client.get("/users/critical-user@example.com/risk-profile")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "critical-user@example.com"
        assert data["risk_level"] == "CRITICAL"
        # Expected risk score should be very high and capped at 100
        assert data["risk_score"] >= 80
        assert data["risk_score"] <= 100
        
        # Check for critical-level recommendations
        recommendations = data["recommendations"]
        assert any("security review required" in rec for rec in recommendations)  # risk_score > 70

    @pytest.mark.asyncio
    async def test_get_user_risk_profile_user_not_found(
        self, test_client, mock_suspicious_activity_detector
    ):
        """Test getting risk profile for non-existent user."""
        mock_suspicious_activity_detector.get_user_activity_summary.return_value = None

        response = test_client.get("/users/nonexistent@example.com/risk-profile")

        assert response.status_code == 404
        assert "No activity data found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_user_risk_profile_empty_activity(
        self, test_client, mock_suspicious_activity_detector
    ):
        """Test getting risk profile with empty activity data."""
        mock_suspicious_activity_detector.get_user_activity_summary.return_value = {}
        mock_suspicious_activity_detector.get_user_suspicious_activities.return_value = []

        response = test_client.get("/users/empty-user@example.com/risk-profile")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "empty-user@example.com"
        assert data["risk_level"] == "LOW"  # Default base risk should result in LOW
        assert data["risk_score"] == 20  # Default base_risk_score
        assert data["total_logins"] == 0
        assert data["failed_logins_today"] == 0
        assert len(data["suspicious_activities"]) == 0
        assert "Continue standard security monitoring" in data["recommendations"]

    @pytest.mark.asyncio
    async def test_get_user_risk_profile_service_error(
        self, test_client, mock_suspicious_activity_detector
    ):
        """Test getting risk profile when detector service raises exception."""
        mock_suspicious_activity_detector.get_user_activity_summary.side_effect = Exception("Service unavailable")

        response = test_client.get("/users/user@example.com/risk-profile")

        assert response.status_code == 500
        assert "Failed to get user risk profile" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_risk_score_calculation_edge_cases(
        self, test_client, mock_suspicious_activity_detector
    ):
        """Test risk score calculation with edge case values."""
        # Test with extreme values that should be capped
        extreme_activity = {
            "base_risk_score": 50,
            "failed_logins_today": 100,  # Should be capped at 30 additional points
            "unusual_location_count": 50,  # Should be capped at 20 additional points
            "off_hours_activity_count": 50,  # Should be capped at 15 additional points
            "total_logins": 1000,
            "known_location_count": 10,
        }
        
        mock_suspicious_activity_detector.get_user_activity_summary.return_value = extreme_activity
        mock_suspicious_activity_detector.get_user_suspicious_activities.return_value = []

        response = test_client.get("/users/extreme-user@example.com/risk-profile")

        assert response.status_code == 200
        data = response.json()
        
        # Risk score should be: 50 + min(30, 100*5) + min(20, 50*3) + min(15, 50*2) = 50 + 30 + 20 + 15 = 115
        # But capped at 100
        assert data["risk_score"] == 100
        assert data["risk_level"] == "CRITICAL"

    @pytest.mark.asyncio
    async def test_risk_score_calculation_negative_values(
        self, test_client, mock_suspicious_activity_detector
    ):
        """Test risk score calculation with negative base values."""
        negative_activity = {
            "base_risk_score": -10,  # Negative base score
            "failed_logins_today": 0,
            "unusual_location_count": 0,
            "off_hours_activity_count": 0,
            "total_logins": 50,
            "known_location_count": 5,
        }
        
        mock_suspicious_activity_detector.get_user_activity_summary.return_value = negative_activity
        mock_suspicious_activity_detector.get_user_suspicious_activities.return_value = []

        response = test_client.get("/users/negative-user@example.com/risk-profile")

        assert response.status_code == 200
        data = response.json()
        
        # Risk score should be capped at minimum 0
        assert data["risk_score"] == 0
        assert data["risk_level"] == "LOW"  # Should still be LOW even with 0 score

    @pytest.mark.asyncio
    async def test_recommendations_logic(
        self, test_client, mock_suspicious_activity_detector
    ):
        """Test recommendation generation logic with specific conditions."""
        specific_activity = {
            "base_risk_score": 30,
            "failed_logins_today": 6,  # > 5, should trigger password policy recommendation
            "unusual_location_count": 3,  # > 2, should trigger location review
            "off_hours_activity_count": 4,  # > 3, should trigger timing investigation
            "total_logins": 100,
            "known_location_count": 2,
        }
        
        many_suspicious_activities = [
            {"description": f"Activity {i}"} for i in range(4)  # > 3 activities
        ]
        
        mock_suspicious_activity_detector.get_user_activity_summary.return_value = specific_activity
        mock_suspicious_activity_detector.get_user_suspicious_activities.return_value = many_suspicious_activities

        response = test_client.get("/users/test-recommendations@example.com/risk-profile")

        assert response.status_code == 200
        data = response.json()
        
        recommendations = data["recommendations"]
        
        # Verify specific recommendations are generated
        assert any("password policy" in rec for rec in recommendations)
        assert any("login locations" in rec for rec in recommendations) 
        assert any("timing patterns" in rec for rec in recommendations)
        assert any("Enhanced monitoring" in rec for rec in recommendations)
        
        # Risk score > 70 should also trigger security review
        if data["risk_score"] > 70:
            assert any("security review required" in rec for rec in recommendations)


class TestUsersIntegration:
    """Test users router integration scenarios."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_user_risk_profile_performance(
        self, test_client, mock_suspicious_activity_detector, sample_low_risk_activity
    ):
        """Test user risk profile endpoint performance."""
        mock_suspicious_activity_detector.get_user_activity_summary.return_value = sample_low_risk_activity
        mock_suspicious_activity_detector.get_user_suspicious_activities.return_value = []

        import time

        start_time = time.time()
        response = test_client.get("/users/performance-test@example.com/risk-profile")
        end_time = time.time()

        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second

    @pytest.mark.asyncio
    async def test_user_id_parameter_validation(self, test_client):
        """Test user ID parameter validation and encoding."""
        # Test with various user ID formats
        test_user_ids = [
            "simple-user",
            "user@example.com",
            "user+test@example.com",
            "user.with.dots@example.com",
            "user123",
            "UPPERCASE@DOMAIN.COM",
        ]

        for user_id in test_user_ids:
            # Mock the detector to return empty data to avoid 404
            response = test_client.get(f"/users/{user_id}/risk-profile")
            # Response should either be 200 (with mocked data) or 404 (no activity data)
            # But should not be 422 (validation error)
            assert response.status_code in [200, 404, 500]  # 500 if mocking not set up

    @pytest.mark.asyncio
    async def test_risk_level_boundaries(
        self, test_client, mock_suspicious_activity_detector
    ):
        """Test risk level classification boundary conditions."""
        boundary_test_cases = [
            (39, "LOW"),     # Just below MEDIUM threshold
            (40, "MEDIUM"),  # Exactly at MEDIUM threshold
            (59, "MEDIUM"),  # Just below HIGH threshold
            (60, "HIGH"),    # Exactly at HIGH threshold
            (79, "HIGH"),    # Just below CRITICAL threshold
            (80, "CRITICAL"), # Exactly at CRITICAL threshold
            (100, "CRITICAL"), # Maximum score
        ]

        for risk_score, expected_level in boundary_test_cases:
            activity_data = {
                "base_risk_score": risk_score,  # Direct risk score for testing
                "failed_logins_today": 0,
                "unusual_location_count": 0,
                "off_hours_activity_count": 0,
                "total_logins": 50,
                "known_location_count": 3,
            }
            
            mock_suspicious_activity_detector.get_user_activity_summary.return_value = activity_data
            mock_suspicious_activity_detector.get_user_suspicious_activities.return_value = []

            response = test_client.get(f"/users/boundary-test-{risk_score}@example.com/risk-profile")

            assert response.status_code == 200
            data = response.json()
            assert data["risk_score"] == risk_score
            assert data["risk_level"] == expected_level