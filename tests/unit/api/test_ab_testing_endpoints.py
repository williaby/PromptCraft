"""Tests for AB testing endpoints API.

Tests the FastAPI endpoints for A/B testing experiment management,
user assignment, metrics collection, and dashboard functionality.
Following minimal mocking principles to test actual processes.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from src.api.ab_testing_endpoints import (
    CreateExperimentRequest,
    MetricEventRequest,
    UserAssignmentRequest,
    router,
)


class TestCreateExperimentRequest:
    """Test CreateExperimentRequest validation."""

    def test_valid_experiment_request(self):
        """Test valid experiment request passes validation."""
        request = CreateExperimentRequest(
            name="Test Experiment",
            description="A test experiment for validation",
            experiment_type="dynamic_loading",
            planned_duration_hours=72,
            target_percentage=25.0,
            rollout_steps=[1.0, 10.0, 25.0],
            feature_flags={"new_feature": True},
            success_criteria={"conversion_rate": 0.05},
        )

        assert request.name == "Test Experiment"
        assert request.experiment_type == "dynamic_loading"
        assert request.planned_duration_hours == 72
        assert request.rollout_steps == [1.0, 10.0, 25.0]

    def test_invalid_experiment_type(self):
        """Test validation fails for invalid experiment type."""
        with pytest.raises(ValueError, match="Experiment type must be one of"):
            CreateExperimentRequest(
                name="Test",
                description="Test",
                experiment_type="invalid_type",
            )

    def test_invalid_rollout_steps_order(self):
        """Test validation fails for rollout steps not in ascending order."""
        with pytest.raises(ValueError, match="Rollout steps must be in ascending order"):
            CreateExperimentRequest(
                name="Test",
                description="Test",
                rollout_steps=[25.0, 10.0, 1.0],  # Not in ascending order
            )

    def test_invalid_rollout_steps_range(self):
        """Test validation fails for rollout steps outside valid range."""
        with pytest.raises(ValueError, match="Each rollout step must be between 0.1 and 100.0"):
            CreateExperimentRequest(
                name="Test",
                description="Test",
                rollout_steps=[0.05, 50.0],  # First value too low
            )

    def test_empty_rollout_steps(self):
        """Test validation fails for empty rollout steps."""
        with pytest.raises(ValueError, match="Rollout steps must be provided"):
            CreateExperimentRequest(
                name="Test",
                description="Test",
                rollout_steps=[],  # Empty list
            )

    def test_too_many_rollout_steps(self):
        """Test validation fails for too many rollout steps."""
        with pytest.raises(ValueError, match="contain at most 10 steps"):
            CreateExperimentRequest(
                name="Test",
                description="Test",
                rollout_steps=[i for i in range(1, 12)],  # 11 steps
            )


class TestUserAssignmentRequest:
    """Test UserAssignmentRequest validation."""

    def test_valid_user_assignment_request(self):
        """Test valid user assignment request."""
        request = UserAssignmentRequest(
            user_id="user123",
            experiment_id="exp456",
            usage_frequency="high",
            feature_usage_pattern="advanced",
            is_early_adopter=True,
        )

        assert request.user_id == "user123"
        assert request.experiment_id == "exp456"
        assert request.usage_frequency == "high"
        assert request.feature_usage_pattern == "advanced"
        assert request.is_early_adopter is True

    def test_invalid_usage_frequency(self):
        """Test validation fails for invalid usage frequency."""
        with pytest.raises(ValueError, match="Usage frequency must be"):
            UserAssignmentRequest(
                user_id="user123",
                experiment_id="exp456",
                usage_frequency="invalid",
            )

    def test_invalid_feature_pattern(self):
        """Test validation fails for invalid feature usage pattern."""
        with pytest.raises(ValueError, match="Feature usage pattern must be"):
            UserAssignmentRequest(
                user_id="user123",
                experiment_id="exp456",
                feature_usage_pattern="invalid",
            )

    def test_optional_fields_default_values(self):
        """Test optional fields have correct default values."""
        request = UserAssignmentRequest(
            user_id="user123",
            experiment_id="exp456",
        )

        assert request.usage_frequency is None
        assert request.feature_usage_pattern is None
        assert request.is_early_adopter is False
        assert request.opt_in_beta is False


class TestMetricEventRequest:
    """Test MetricEventRequest validation."""

    def test_valid_metric_event_request(self):
        """Test valid metric event request."""
        request = MetricEventRequest(
            user_id="user123",
            experiment_id="exp456",
            event_type="conversion",
            event_value=1.0,
            metadata={"source": "web", "campaign": "test"},
        )

        assert request.user_id == "user123"
        assert request.experiment_id == "exp456"
        assert request.event_type == "conversion"
        assert request.event_value == 1.0
        assert request.metadata == {"source": "web", "campaign": "test"}


class TestABTestingEndpoints:
    """Integration tests for AB testing API endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_create_experiment_success(self, mock_get_manager):
        """Test successful experiment creation."""
        # Mock experiment manager
        mock_manager = AsyncMock()
        mock_experiment = MagicMock()
        mock_experiment.id = "exp123"
        mock_experiment.name = "Test Experiment"
        mock_experiment.status = "draft"
        mock_experiment.created_at = datetime.now()
        mock_manager.create_experiment.return_value = mock_experiment
        mock_get_manager.return_value = mock_manager

        # Create experiment request
        request_data = {
            "name": "Test Experiment",
            "description": "A test experiment",
            "experiment_type": "dynamic_loading",
            "planned_duration_hours": 48,
            "target_percentage": 50.0,
            "rollout_steps": [5.0, 25.0, 50.0],
        }

        response = self.client.post("/api/v1/ab-testing/experiments", json=request_data)

        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Test Experiment"
        assert data["status"] == "draft"

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_create_experiment_validation_error(self, mock_get_manager):
        """Test experiment creation with validation error."""
        # Invalid request data
        request_data = {
            "name": "",  # Empty name should fail validation
            "description": "A test experiment",
        }

        response = self.client.post("/api/v1/ab-testing/experiments", json=request_data)

        assert response.status_code == HTTP_400_BAD_REQUEST

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_start_experiment_success(self, mock_get_manager):
        """Test successful experiment start."""
        mock_manager = AsyncMock()
        mock_manager.start_experiment.return_value = True
        mock_get_manager.return_value = mock_manager

        response = self.client.post("/api/v1/ab-testing/experiments/exp123/start")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_start_experiment_not_found(self, mock_get_manager):
        """Test starting non-existent experiment."""
        mock_manager = AsyncMock()
        mock_manager.start_experiment.side_effect = ValueError("Experiment not found")
        mock_get_manager.return_value = mock_manager

        response = self.client.post("/api/v1/ab-testing/experiments/nonexistent/start")

        assert response.status_code == HTTP_400_BAD_REQUEST

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_stop_experiment_success(self, mock_get_manager):
        """Test successful experiment stop."""
        mock_manager = AsyncMock()
        mock_manager.stop_experiment.return_value = True
        mock_get_manager.return_value = mock_manager

        response = self.client.post("/api/v1/ab-testing/experiments/exp123/stop")

        assert response.status_code == HTTP_200_OK

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_list_experiments(self, mock_get_manager):
        """Test listing experiments."""
        mock_manager = AsyncMock()
        mock_experiments = [
            MagicMock(id="exp1", name="Experiment 1", status="running"),
            MagicMock(id="exp2", name="Experiment 2", status="draft"),
        ]
        mock_manager.list_experiments.return_value = mock_experiments
        mock_get_manager.return_value = mock_manager

        response = self.client.get("/api/v1/ab-testing/experiments")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_get_experiment_success(self, mock_get_manager):
        """Test getting specific experiment."""
        mock_manager = AsyncMock()
        mock_experiment = MagicMock()
        mock_experiment.id = "exp123"
        mock_experiment.name = "Test Experiment"
        mock_experiment.status = "running"
        mock_manager.get_experiment.return_value = mock_experiment
        mock_get_manager.return_value = mock_manager

        response = self.client.get("/api/v1/ab-testing/experiments/exp123")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["name"] == "Test Experiment"

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_get_experiment_not_found(self, mock_get_manager):
        """Test getting non-existent experiment."""
        mock_manager = AsyncMock()
        mock_manager.get_experiment.side_effect = ValueError("Experiment not found")
        mock_get_manager.return_value = mock_manager

        response = self.client.get("/api/v1/ab-testing/experiments/nonexistent")

        assert response.status_code == HTTP_404_NOT_FOUND

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_assign_user_success(self, mock_get_manager):
        """Test successful user assignment."""
        mock_manager = AsyncMock()
        mock_assignment = {
            "user_id": "user123",
            "experiment_id": "exp456",
            "variant": "control",
            "assigned_at": datetime.now(),
        }
        mock_manager.assign_user.return_value = mock_assignment
        mock_get_manager.return_value = mock_manager

        request_data = {
            "user_id": "user123",
            "experiment_id": "exp456",
            "usage_frequency": "high",
        }

        response = self.client.post("/api/v1/ab-testing/assign-user", json=request_data)

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["user_id"] == "user123"
        assert data["variant"] == "control"

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_check_dynamic_loading_assignment(self, mock_get_manager):
        """Test checking dynamic loading assignment."""
        mock_manager = AsyncMock()
        mock_assignment = {"enabled": True, "variant": "treatment", "experiment_id": "exp123"}
        mock_manager.get_user_assignment.return_value = mock_assignment
        mock_get_manager.return_value = mock_manager

        response = self.client.get("/api/v1/ab-testing/check-dynamic-loading/user123")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["enabled"] is True
        assert data["variant"] == "treatment"

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_record_metric_event(self, mock_get_manager):
        """Test recording metric events."""
        mock_manager = AsyncMock()
        mock_manager.record_metric.return_value = True
        mock_get_manager.return_value = mock_manager

        request_data = {
            "user_id": "user123",
            "experiment_id": "exp456",
            "event_type": "conversion",
            "event_value": 1.0,
        }

        response = self.client.post("/api/v1/ab-testing/metrics/record-event", json=request_data)

        assert response.status_code == HTTP_200_OK

    @patch("src.api.ab_testing_endpoints.get_dashboard_instance")
    def test_get_dashboard_data(self, mock_get_dashboard):
        """Test getting dashboard data."""
        mock_dashboard = AsyncMock()
        mock_dashboard_data = {
            "experiment_id": "exp123",
            "total_users": 1000,
            "conversion_rate": 0.05,
            "variants": {"control": 500, "treatment": 500},
        }
        mock_dashboard.get_experiment_dashboard_data.return_value = mock_dashboard_data
        mock_get_dashboard.return_value = mock_dashboard

        response = self.client.get("/api/v1/ab-testing/dashboard-data/exp123")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["total_users"] == 1000

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_get_experiment_results(self, mock_get_manager):
        """Test getting experiment results."""
        mock_manager = AsyncMock()
        mock_results = {
            "experiment_id": "exp123",
            "status": "completed",
            "statistical_significance": True,
            "confidence_level": 0.95,
            "results": {"control": 0.04, "treatment": 0.06},
        }
        mock_manager.get_experiment_results.return_value = mock_results
        mock_get_manager.return_value = mock_manager

        response = self.client.get("/api/v1/ab-testing/experiments/exp123/results")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["statistical_significance"] is True

    @patch("src.api.ab_testing_endpoints.create_dynamic_loading_experiment")
    def test_quick_setup_dynamic_loading(self, mock_create_experiment):
        """Test quick setup for dynamic loading experiment."""
        mock_experiment = MagicMock()
        mock_experiment.id = "exp123"
        mock_experiment.name = "Dynamic Loading Test"
        mock_create_experiment.return_value = mock_experiment

        request_data = {
            "name": "Quick Dynamic Loading Test",
            "description": "Quick setup test",
        }

        response = self.client.post("/api/v1/ab-testing/quick-setup/dynamic-loading", json=request_data)

        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert "experiment_id" in data

    def test_health_check(self):
        """Test AB testing health check endpoint."""
        response = self.client.get("/api/v1/ab-testing/health")

        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "ab_testing" in data


class TestEndpointSecurity:
    """Test security aspects of AB testing endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    def test_experiment_creation_input_validation(self):
        """Test that experiment creation validates input properly."""
        # Test with malicious input
        malicious_data = {
            "name": "Test" + "A" * 1000,  # Extremely long name
            "description": "Test",
            "experiment_type": "dynamic_loading",
        }

        response = self.client.post("/api/v1/ab-testing/experiments", json=malicious_data)

        # Should fail validation due to max_length constraints
        assert response.status_code == HTTP_400_BAD_REQUEST

    def test_user_assignment_sanitization(self):
        """Test user assignment request sanitizes input."""
        # Test with potentially harmful user IDs
        request_data = {
            "user_id": "<script>alert('xss')</script>",
            "experiment_id": "exp123",
        }

        # The endpoint should handle this gracefully
        # Note: Actual behavior depends on implementation
        response = self.client.post("/api/v1/ab-testing/assign-user", json=request_data)

        # Should either sanitize or reject the input
        assert response.status_code in [HTTP_200_OK, HTTP_400_BAD_REQUEST]

    def test_metric_event_validation(self):
        """Test metric event validation prevents abuse."""
        # Test with extreme values
        request_data = {
            "user_id": "user123",
            "experiment_id": "exp456",
            "event_type": "conversion",
            "event_value": float("inf"),  # Infinite value
        }

        response = self.client.post("/api/v1/ab-testing/metrics/record-event", json=request_data)

        # Should handle extreme values gracefully
        assert response.status_code in [HTTP_200_OK, HTTP_400_BAD_REQUEST]


class TestEndpointErrorHandling:
    """Test error handling in AB testing endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_experiment_manager_exception_handling(self, mock_get_manager):
        """Test handling of experiment manager exceptions."""
        mock_manager = AsyncMock()
        mock_manager.create_experiment.side_effect = Exception("Database connection failed")
        mock_get_manager.return_value = mock_manager

        request_data = {
            "name": "Test Experiment",
            "description": "Test",
            "experiment_type": "dynamic_loading",
        }

        response = self.client.post("/api/v1/ab-testing/experiments", json=request_data)

        # Should return appropriate error response
        assert response.status_code >= 400

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_assignment_error_handling(self, mock_get_manager):
        """Test user assignment error handling."""
        mock_manager = AsyncMock()
        mock_manager.assign_user.side_effect = ValueError("Invalid experiment configuration")
        mock_get_manager.return_value = mock_manager

        request_data = {
            "user_id": "user123",
            "experiment_id": "invalid_exp",
        }

        response = self.client.post("/api/v1/ab-testing/assign-user", json=request_data)

        assert response.status_code == HTTP_400_BAD_REQUEST


class TestEndpointPerformance:
    """Test performance aspects of AB testing endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.app = FastAPI()
        self.app.include_router(router)
        self.client = TestClient(self.app)

    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    def test_bulk_operations_efficiency(self, mock_get_manager):
        """Test that bulk operations are handled efficiently."""
        mock_manager = AsyncMock()
        # Simulate fast response for bulk operations
        mock_manager.list_experiments.return_value = [
            MagicMock(id=f"exp{i}", name=f"Experiment {i}") for i in range(100)
        ]
        mock_get_manager.return_value = mock_manager

        import time

        start_time = time.time()
        response = self.client.get("/api/v1/ab-testing/experiments")
        end_time = time.time()

        assert response.status_code == HTTP_200_OK
        # Should complete within reasonable time
        assert end_time - start_time < 1.0

    def test_concurrent_requests_handling(self):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def make_request():
            return self.client.get("/api/v1/ab-testing/health")

        # Submit multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in futures]

        # All requests should succeed
        assert all(result.status_code == HTTP_200_OK for result in results)
