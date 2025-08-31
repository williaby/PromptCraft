"""Comprehensive tests for events_router.py.

Tests security event search endpoint functionality.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.api.routers.events_router import (
    SecurityEventResponse,
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
def sample_events():
    """Sample security events for testing."""
    return [
        SecurityEventResponse(
            id=str(uuid4()),
            event_type="login_failure",
            severity="critical",
            timestamp=datetime.now(UTC) - timedelta(hours=1),
            user_id="user1@example.com",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            risk_score=85,
            details={"reason": "invalid_password", "attempts": 5},
            tags=["brute_force", "suspicious"],
        ),
        SecurityEventResponse(
            id=str(uuid4()),
            event_type="login_success",
            severity="info",
            timestamp=datetime.now(UTC) - timedelta(hours=2),
            user_id="user2@example.com",
            ip_address="10.0.0.50",
            user_agent="Chrome/91.0",
            risk_score=10,
            details={"method": "password", "duration": "normal"},
            tags=["normal_activity"],
        ),
    ]


class TestEventsRouter:
    """Test events router functionality."""

    def test_router_configuration(self):
        """Test router is properly configured."""
        assert router.prefix == "/events"
        assert "events" in router.tags

    @pytest.mark.asyncio
    async def test_search_events_success(self, test_client, mock_security_service, sample_events):
        """Test successful event search."""
        # Return a dictionary structure that matches what the router expects
        search_results = {
            "events": [
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "timestamp": event.timestamp,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "risk_score": event.risk_score,
                    "details": event.details,
                    "tags": event.tags,
                }
                for event in sample_events
            ],
            "total_count": len(sample_events),
        }
        mock_security_service.search_security_events.return_value = search_results

        search_request = {
            "start_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
            "end_date": datetime.now(UTC).isoformat(),
            "limit": 100,
            "offset": 0,
        }

        response = test_client.post("/events/search", json=search_request)

        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 2
        assert data["total_count"] == 2
        assert "search_time_ms" in data
        assert isinstance(data["search_time_ms"], (int, float))
        assert data["search_time_ms"] >= 0

    @pytest.mark.asyncio
    async def test_search_events_with_filters(self, test_client, mock_security_service, sample_events):
        """Test event search with various filters."""
        filtered_events = [sample_events[0]]  # Only high severity event
        # Return a dictionary structure that matches what the router expects
        search_results = {
            "events": [
                {
                    "id": str(event.id),
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "timestamp": event.timestamp,
                    "user_id": event.user_id,
                    "ip_address": event.ip_address,
                    "user_agent": event.user_agent,
                    "risk_score": event.risk_score,
                    "details": event.details,
                    "tags": event.tags,
                }
                for event in filtered_events
            ],
            "total_count": 1,
        }
        mock_security_service.search_security_events.return_value = search_results

        search_request = {
            "start_date": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
            "end_date": datetime.now(UTC).isoformat(),
            "severity_levels": ["critical"],
            "event_types": ["login_failure"],
            "risk_score_min": 80,
            "user_id": "user1@example.com",
        }

        response = test_client.post("/events/search", json=search_request)

        if response.status_code != 200:
            print(f"Error response: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert len(data["events"]) == 1
        assert data["events"][0]["severity"] == "critical"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_search_performance(self, test_client, mock_security_service):
        """Test search performance with large result set."""
        # Return a dictionary structure that matches what the router expects
        large_results = {
            "events": [],  # Empty for performance test
            "total_count": 10000,
        }
        mock_security_service.search_security_events.return_value = large_results

        search_request = {
            "start_date": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
            "end_date": datetime.now(UTC).isoformat(),
            "limit": 1000,
        }

        import time

        start_time = time.time()

        response = test_client.post("/events/search", json=search_request)

        end_time = time.time()
        response_time = end_time - start_time

        assert response.status_code == 200
        assert response_time < 2.0  # Should respond within 2 seconds
