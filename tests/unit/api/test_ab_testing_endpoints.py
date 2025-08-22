"""
Comprehensive tests for A/B Testing Endpoints - Fixed Version

This module provides complete test coverage for all validation methods,
dependency functions, and API endpoints in the ab_testing_endpoints module.
Fixed to properly handle FastAPI rate limiting and request mocking.
"""

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from pydantic import ValidationError
from starlette.datastructures import URL, Headers
from starlette.requests import Request as StarletteRequest

# Import the module under test
from src.api.ab_testing_endpoints import (
    CreateExperimentRequest,
    MetricEventRequest,
    UserAssignmentRequest,
    get_experiment_manager_dependency,
)


def create_mock_request():
    """Create a properly structured mock request for FastAPI testing."""
    # Create a more realistic mock that passes rate limiting checks
    mock_request = MagicMock(spec=StarletteRequest)
    mock_request.client = MagicMock()
    mock_request.client.host = "127.0.0.1"
    mock_request.url = MagicMock(spec=URL)
    mock_request.url.path = "/test"
    mock_request.method = "POST"
    mock_request.headers = MagicMock(spec=Headers)
    mock_request.scope = {
        "type": "http",
        "method": "POST",
        "path": "/test",
        "client": ("127.0.0.1", 12345),
        "headers": [],
    }
    return mock_request


def disable_rate_limiting():
    """Context manager to disable rate limiting for testing."""

    def mock_rate_limit_decorator(limit):
        def decorator(func):
            return func  # Return the function unchanged

        return decorator

    return patch("src.api.ab_testing_endpoints.rate_limit", mock_rate_limit_decorator)


class TestPydanticValidationMethods:
    """Test suite for Pydantic validation methods."""

    def test_create_experiment_request_validate_rollout_steps_valid(self):
        """Test valid rollout steps validation."""
        # Test valid ascending steps
        valid_steps = [1.0, 5.0, 25.0, 50.0, 100.0]
        result = CreateExperimentRequest.validate_rollout_steps(valid_steps)
        assert result == valid_steps

        # Test single step
        single_step = [10.0]
        result = CreateExperimentRequest.validate_rollout_steps(single_step)
        assert result == single_step

        # Test boundary values
        boundary_steps = [0.1, 100.0]
        result = CreateExperimentRequest.validate_rollout_steps(boundary_steps)
        assert result == boundary_steps

    def test_create_experiment_request_validate_rollout_steps_invalid(self):
        """Test invalid rollout steps validation."""
        # Test empty steps
        with pytest.raises(ValueError, match="Rollout steps must be provided"):
            CreateExperimentRequest.validate_rollout_steps([])

        # Test too many steps
        too_many_steps = [i * 10.0 for i in range(11)]
        with pytest.raises(ValueError, match="contain at most 10 steps"):
            CreateExperimentRequest.validate_rollout_steps(too_many_steps)

        # Test steps below minimum
        with pytest.raises(ValueError, match="must be between 0.1 and 100.0"):
            CreateExperimentRequest.validate_rollout_steps([0.05, 50.0])

        # Test steps above maximum
        with pytest.raises(ValueError, match="must be between 0.1 and 100.0"):
            CreateExperimentRequest.validate_rollout_steps([50.0, 101.0])

        # Test non-ascending order
        with pytest.raises(ValueError, match="must be in ascending order"):
            CreateExperimentRequest.validate_rollout_steps([50.0, 25.0, 75.0])

    def test_user_assignment_request_validate_feature_pattern_valid(self):
        """Test valid feature pattern validation."""
        # Test valid patterns
        for pattern in ["basic", "intermediate", "advanced"]:
            result = UserAssignmentRequest.validate_feature_pattern(pattern)
            assert result == pattern

        # Test None value
        result = UserAssignmentRequest.validate_feature_pattern(None)
        assert result is None

    def test_user_assignment_request_validate_feature_pattern_invalid(self):
        """Test invalid feature pattern validation."""
        # Test invalid pattern
        with pytest.raises(ValueError, match="must be 'basic', 'intermediate', or 'advanced'"):
            UserAssignmentRequest.validate_feature_pattern("expert")

    def test_metric_event_request_validate_event_type_valid(self):
        """Test valid event type validation."""
        # Test valid event types
        valid_types = ["performance", "conversion", "error", "engagement", "business"]
        for event_type in valid_types:
            result = MetricEventRequest.validate_event_type(event_type)
            assert result == event_type

    def test_metric_event_request_validate_event_type_invalid(self):
        """Test invalid event type validation."""
        # Test invalid event type
        with pytest.raises(ValueError, match="must be one of"):
            MetricEventRequest.validate_event_type("invalid_type")


class TestGetExperimentManagerDependency:
    """Test suite for get_experiment_manager_dependency function."""

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    async def test_get_experiment_manager_dependency_success(self, mock_get_manager):
        """Test successful experiment manager retrieval."""
        # Arrange
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager

        # Act
        result = await get_experiment_manager_dependency()

        # Assert
        assert result == mock_manager
        mock_get_manager.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    async def test_get_experiment_manager_dependency_failure(self, mock_get_manager):
        """Test experiment manager retrieval failure."""
        # Arrange
        mock_get_manager.side_effect = Exception("Database connection failed")

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_experiment_manager_dependency()

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "A/B testing system unavailable" in str(exc_info.value.detail)


class TestExperimentManagementEndpoints:
    """Test suite for experiment management endpoints."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_manager = Mock()
        self.mock_experiment = Mock()
        self.mock_experiment.id = "exp_123"
        self.mock_experiment.name = "Test Experiment"
        self.mock_experiment.description = "Test Description"
        self.mock_experiment.experiment_type = "dynamic_loading"
        self.mock_experiment.status = "created"
        self.mock_experiment.target_percentage = 50.0
        self.mock_experiment.current_percentage = 0.0
        self.mock_experiment.planned_duration_hours = 168
        self.mock_experiment.total_users = 0
        self.mock_experiment.statistical_significance = 0.0
        self.mock_experiment.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        self.mock_experiment.start_time = None
        self.mock_experiment.end_time = None

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.audit_logger_instance")
    async def test_start_experiment_success(self, mock_audit_logger):
        """Test successful experiment start."""
        # Arrange
        self.mock_manager.start_experiment = AsyncMock(return_value=True)
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import start_experiment

            result = await start_experiment(mock_request, "exp_123", self.mock_manager)

        # Assert
        self.mock_manager.start_experiment.assert_called_once_with("exp_123")
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_start_experiment_not_found(self):
        """Test experiment start when experiment not found."""
        # Arrange
        self.mock_manager.start_experiment = AsyncMock(return_value=False)
        mock_request = create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import start_experiment

            with pytest.raises(HTTPException) as exc_info:
                await start_experiment(mock_request, "nonexistent", self.mock_manager)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "cannot be started" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_start_experiment_manager_error(self):
        """Test experiment start when manager raises an error."""
        # Arrange
        self.mock_manager.start_experiment = AsyncMock(side_effect=Exception("Database error"))
        mock_request = create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import start_experiment

            with pytest.raises(HTTPException) as exc_info:
                await start_experiment(mock_request, "exp_123", self.mock_manager)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to start experiment" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.audit_logger_instance")
    async def test_stop_experiment_success(self, mock_audit_logger):
        """Test successful experiment stop."""
        # Arrange
        self.mock_manager.stop_experiment = AsyncMock(return_value=True)
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import stop_experiment

            result = await stop_experiment(mock_request, "exp_123", self.mock_manager)

        # Assert
        self.mock_manager.stop_experiment.assert_called_once_with("exp_123")
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_stop_experiment_not_found(self):
        """Test experiment stop when experiment not found."""
        # Arrange
        self.mock_manager.stop_experiment = AsyncMock(return_value=False)
        mock_request = create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import stop_experiment

            with pytest.raises(HTTPException) as exc_info:
                await stop_experiment(mock_request, "nonexistent", self.mock_manager)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "cannot be stopped" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_list_experiments_success(self):
        """Test successful experiment listing."""
        # Arrange
        mock_db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_experiment]
        mock_db_session.query.return_value = mock_query

        # Mock the context manager properly
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_db_session
        mock_context.__exit__.return_value = None
        self.mock_manager.get_db_session.return_value = mock_context
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import list_experiments

            result = await list_experiments(mock_request, None, 50, 0, self.mock_manager)

        # Assert
        assert len(result) == 1
        assert result[0].id == "exp_123"
        assert result[0].name == "Test Experiment"

    @pytest.mark.asyncio
    async def test_list_experiments_with_status_filter(self):
        """Test experiment listing with status filter."""
        # Arrange
        mock_db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [self.mock_experiment]
        mock_db_session.query.return_value = mock_query

        # Mock the context manager properly
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_db_session
        mock_context.__exit__.return_value = None
        self.mock_manager.get_db_session.return_value = mock_context
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import list_experiments

            result = await list_experiments(mock_request, "active", 50, 0, self.mock_manager)

        # Assert
        mock_query.filter.assert_called()
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_list_experiments_database_error(self):
        """Test experiment listing with database error."""
        # Arrange
        self.mock_manager.get_db_session.side_effect = Exception("Database connection failed")
        mock_request = create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import list_experiments

            with pytest.raises(HTTPException) as exc_info:
                await list_experiments(mock_request, None, 50, 0, self.mock_manager)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to list experiments" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_experiment_success(self):
        """Test successful single experiment retrieval."""
        # Arrange
        mock_db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = self.mock_experiment
        mock_db_session.query.return_value = mock_query

        # Mock the context manager properly
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_db_session
        mock_context.__exit__.return_value = None
        self.mock_manager.get_db_session.return_value = mock_context
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import get_experiment

            result = await get_experiment(mock_request, "exp_123", self.mock_manager)

        # Assert
        assert result.id == "exp_123"
        assert result.name == "Test Experiment"
        mock_query.filter_by.assert_called_once_with(id="exp_123")

    @pytest.mark.asyncio
    async def test_get_experiment_not_found(self):
        """Test single experiment retrieval when not found."""
        # Arrange
        mock_db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # Mock the context manager properly
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_db_session
        mock_context.__exit__.return_value = None
        self.mock_manager.get_db_session.return_value = mock_context
        mock_request = create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import get_experiment

            with pytest.raises(HTTPException) as exc_info:
                await get_experiment(mock_request, "nonexistent", self.mock_manager)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Experiment not found" in str(exc_info.value.detail)


class TestMetricsEndpoints:
    """Test suite for metrics collection endpoints."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_manager = Mock()
        self.sample_metric_request = {
            "experiment_id": "exp_123",
            "user_id": "user_456",
            "event_type": "performance",
            "event_name": "response_time",
            "event_value": 100.5,
            "response_time_ms": 150.0,
            "success": True,
        }

    @pytest.mark.asyncio
    async def test_record_metric_event_success(self):
        """Test successful metric event recording."""
        # Arrange
        mock_db_session = MagicMock()
        mock_collector = MagicMock()
        mock_collector.record_event.return_value = True

        # Mock the context manager properly
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_db_session
        mock_context.__exit__.return_value = None
        self.mock_manager.get_db_session.return_value = mock_context
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import MetricEventRequest, record_metric_event

            metric_request = MetricEventRequest(**self.sample_metric_request)

            # MetricsCollector is imported inside the function, so we need to patch the import
            with patch("src.core.ab_testing_framework.MetricsCollector", return_value=mock_collector):
                result = await record_metric_event(mock_request, metric_request, self.mock_manager)

        # Assert
        mock_collector.record_event.assert_called_once()
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_record_metric_event_failure(self):
        """Test metric event recording failure."""
        # Arrange
        mock_db_session = MagicMock()
        mock_collector = MagicMock()
        mock_collector.record_event.return_value = False

        # Mock the context manager properly
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_db_session
        mock_context.__exit__.return_value = None
        self.mock_manager.get_db_session.return_value = mock_context
        mock_request = create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import MetricEventRequest, record_metric_event

            metric_request = MetricEventRequest(**self.sample_metric_request)

            # MetricsCollector is imported inside the function, so we need to patch the import
            with (
                patch("src.core.ab_testing_framework.MetricsCollector", return_value=mock_collector),
                pytest.raises(HTTPException) as exc_info,
            ):
                await record_metric_event(mock_request, metric_request, self.mock_manager)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to record metric event" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_record_metric_event_exception(self):
        """Test metric event recording with exception."""
        # Arrange
        self.mock_manager.get_db_session.side_effect = Exception("Database error")
        mock_request = create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import MetricEventRequest, record_metric_event

            metric_request = MetricEventRequest(**self.sample_metric_request)

            with pytest.raises(HTTPException) as exc_info:
                await record_metric_event(mock_request, metric_request, self.mock_manager)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestHealthEndpoint:
    """Test suite for health check endpoints."""

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    @patch("src.api.ab_testing_endpoints.utc_now")
    async def test_ab_testing_health_check_success(self, mock_utc_now, mock_get_manager):
        """Test successful health check."""
        # Arrange
        mock_utc_now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager
        mock_db_session = MagicMock()
        mock_db_session.execute.return_value = None

        # Mock the context manager properly
        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_db_session
        mock_context.__exit__.return_value = None
        mock_manager.get_db_session.return_value = mock_context
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import ab_testing_health_check

            result = await ab_testing_health_check(mock_request)

        # Assert
        assert result.status_code == 200
        content = json.loads(result.body.decode())
        assert content["status"] == "healthy"
        assert content["service"] == "ab-testing"
        assert content["database_connected"] is True

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.get_experiment_manager")
    @patch("src.api.ab_testing_endpoints.utc_now")
    async def test_ab_testing_health_check_failure(self, mock_utc_now, mock_get_manager):
        """Test health check failure."""
        # Arrange
        mock_utc_now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_get_manager.side_effect = Exception("Database connection failed")
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import ab_testing_health_check

            result = await ab_testing_health_check(mock_request)

        # Assert
        assert result.status_code == 503
        content = json.loads(result.body.decode())
        assert content["status"] == "unhealthy"
        assert "error" in content


class TestValidationIntegration:
    """Integration tests for Pydantic validation with actual request models."""

    def test_create_experiment_request_full_validation(self):
        """Test full CreateExperimentRequest validation."""
        # Test valid request
        valid_data = {
            "name": "Test Experiment",
            "description": "This is a test experiment",
            "experiment_type": "dynamic_loading",
            "planned_duration_hours": 168,
            "target_percentage": 50.0,
            "rollout_steps": [1.0, 5.0, 25.0, 50.0],
            "step_duration_hours": 24,
            "circuit_breaker_threshold": 10.0,
        }

        request = CreateExperimentRequest(**valid_data)
        assert request.name == "Test Experiment"
        assert request.rollout_steps == [1.0, 5.0, 25.0, 50.0]

        # Test invalid experiment type
        invalid_data = valid_data.copy()
        invalid_data["experiment_type"] = "invalid_type"

        with pytest.raises(ValidationError) as exc_info:
            CreateExperimentRequest(**invalid_data)

        assert "must be one of" in str(exc_info.value)

    def test_user_assignment_request_full_validation(self):
        """Test full UserAssignmentRequest validation."""
        # Test valid request
        valid_data = {
            "user_id": "user_123",
            "experiment_id": "exp_456",
            "usage_frequency": "medium",
            "feature_usage_pattern": "intermediate",
        }

        request = UserAssignmentRequest(**valid_data)
        assert request.user_id == "user_123"
        assert request.usage_frequency == "medium"

        # Test invalid usage frequency
        invalid_data = valid_data.copy()
        invalid_data["usage_frequency"] = "super_high"

        with pytest.raises(ValidationError) as exc_info:
            UserAssignmentRequest(**invalid_data)

        assert "must be 'low', 'medium', or 'high'" in str(exc_info.value)

    def test_metric_event_request_full_validation(self):
        """Test full MetricEventRequest validation."""
        # Test valid request
        valid_data = {
            "experiment_id": "exp_123",
            "user_id": "user_456",
            "event_type": "performance",
            "event_name": "response_time",
            "event_value": 150.0,
            "response_time_ms": 150.0,
            "token_reduction_percentage": 25.5,
            "success": True,
        }

        request = MetricEventRequest(**valid_data)
        assert request.event_type == "performance"
        assert request.response_time_ms == 150.0

        # Test invalid event type
        invalid_data = valid_data.copy()
        invalid_data["event_type"] = "custom_type"

        with pytest.raises(ValidationError) as exc_info:
            MetricEventRequest(**invalid_data)

        assert "must be one of" in str(exc_info.value)


class TestCreateExperimentEndpoint:
    """Test suite for create experiment endpoint."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_manager = Mock()
        self.sample_experiment_request = {
            "name": "Test Experiment",
            "description": "Test Description",
            "experiment_type": "dynamic_loading",
            "planned_duration_hours": 168,
            "target_percentage": 50.0,
            "rollout_steps": [1.0, 5.0, 25.0, 50.0],
        }

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.audit_logger_instance")
    @patch("src.api.ab_testing_endpoints.time.perf_counter")
    async def test_create_experiment_success(self, mock_perf_counter, mock_audit_logger):
        """Test successful experiment creation."""
        # Arrange
        mock_perf_counter.side_effect = [0.0, 0.1]  # start and end times
        self.mock_manager.create_experiment = AsyncMock(return_value="exp_123")

        mock_experiment = Mock()
        mock_experiment.id = "exp_123"
        mock_experiment.name = "Test Experiment"
        mock_experiment.description = "Test Description"
        mock_experiment.experiment_type = "dynamic_loading"
        mock_experiment.status = "created"
        mock_experiment.target_percentage = 50.0
        mock_experiment.current_percentage = 0.0
        mock_experiment.planned_duration_hours = 168
        mock_experiment.total_users = 0
        mock_experiment.statistical_significance = 0.0
        mock_experiment.created_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        mock_experiment.start_time = None
        mock_experiment.end_time = None

        mock_db_session = MagicMock()
        mock_query = MagicMock()
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = mock_experiment
        mock_db_session.query.return_value = mock_query

        mock_context = MagicMock()
        mock_context.__enter__.return_value = mock_db_session
        mock_context.__exit__.return_value = None
        self.mock_manager.get_db_session.return_value = mock_context

        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import CreateExperimentRequest, create_experiment

            experiment_request = CreateExperimentRequest(**self.sample_experiment_request)
            result = await create_experiment(mock_request, experiment_request, self.mock_manager)

        # Assert
        self.mock_manager.create_experiment.assert_called_once()
        assert result.id == "exp_123"
        assert result.name == "Test Experiment"
        mock_audit_logger.log_api_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_experiment_validation_error(self):
        """Test experiment creation with validation error."""
        # Arrange
        create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import CreateExperimentRequest

            # Create invalid request with invalid experiment type
            invalid_request = self.sample_experiment_request.copy()
            invalid_request["experiment_type"] = "invalid_type"

            with pytest.raises(ValueError):
                CreateExperimentRequest(**invalid_request)


class TestUserAssignmentEndpoints:
    """Test suite for user assignment endpoints."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_manager = Mock()

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.audit_logger_instance")
    @patch("src.api.ab_testing_endpoints.utc_now")
    async def test_assign_user_to_experiment_success(self, mock_utc_now, mock_audit_logger):
        """Test successful user assignment."""
        # Arrange
        from src.core.ab_testing_framework import UserSegment

        mock_utc_now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        self.mock_manager.assign_user_to_experiment = AsyncMock(return_value=("treatment", UserSegment.RANDOM))
        mock_request = create_mock_request()

        assignment_request_data = {
            "user_id": "user_123",
            "experiment_id": "exp_456",
            "usage_frequency": "medium",
            "feature_usage_pattern": "intermediate",
        }

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import UserAssignmentRequest, assign_user_to_experiment

            assignment_request = UserAssignmentRequest(**assignment_request_data)
            result = await assign_user_to_experiment(mock_request, assignment_request, self.mock_manager)

        # Assert
        self.mock_manager.assign_user_to_experiment.assert_called_once()
        assert result.user_id == "user_123"
        assert result.experiment_id == "exp_456"
        assert result.variant == "treatment"
        assert result.segment == "random"  # This is the UserSegment.RANDOM.value
        assert result.success is True
        mock_audit_logger.log_api_event.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.utc_now")
    async def test_assign_user_to_experiment_failure(self, mock_utc_now):
        """Test user assignment failure."""
        # Arrange
        mock_utc_now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        self.mock_manager.assign_user_to_experiment = AsyncMock(side_effect=Exception("Assignment failed"))
        mock_request = create_mock_request()

        assignment_request_data = {"user_id": "user_123", "experiment_id": "exp_456"}

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import UserAssignmentRequest, assign_user_to_experiment

            assignment_request = UserAssignmentRequest(**assignment_request_data)
            result = await assign_user_to_experiment(mock_request, assignment_request, self.mock_manager)

        # Assert
        assert result.user_id == "user_123"
        assert result.variant == "control"
        assert result.success is False
        assert "Assignment failed" in result.message

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.utc_now")
    async def test_check_dynamic_loading_assignment_success(self, mock_utc_now):
        """Test successful dynamic loading assignment check."""
        # Arrange
        mock_utc_now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        self.mock_manager.should_use_dynamic_loading = AsyncMock(return_value=True)
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import check_dynamic_loading_assignment

            result = await check_dynamic_loading_assignment(
                mock_request,
                "user_123",
                "dynamic_loading_rollout",
                self.mock_manager,
            )

        # Assert
        self.mock_manager.should_use_dynamic_loading.assert_called_once_with("user_123", "dynamic_loading_rollout")
        assert result.status_code == 200
        content = json.loads(result.body.decode())
        assert content["user_id"] == "user_123"
        assert content["use_dynamic_loading"] is True

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.utc_now")
    async def test_check_dynamic_loading_assignment_failure(self, mock_utc_now):
        """Test dynamic loading assignment check failure."""
        # Arrange
        mock_utc_now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        self.mock_manager.should_use_dynamic_loading = AsyncMock(side_effect=Exception("Check failed"))
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import check_dynamic_loading_assignment

            result = await check_dynamic_loading_assignment(
                mock_request,
                "user_123",
                "dynamic_loading_rollout",
                self.mock_manager,
            )

        # Assert
        assert result.status_code == 500
        content = json.loads(result.body.decode())
        assert content["use_dynamic_loading"] is False
        assert "error" in content


class TestDashboardEndpoints:
    """Test suite for dashboard endpoints."""

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.get_dashboard_instance")
    async def test_get_experiment_dashboard_success(self, mock_get_dashboard):
        """Test successful dashboard HTML generation."""
        # Arrange
        mock_dashboard = AsyncMock()
        mock_dashboard.generate_dashboard_html = AsyncMock(return_value="<html>Dashboard</html>")
        mock_get_dashboard.return_value = mock_dashboard
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import get_experiment_dashboard

            result = await get_experiment_dashboard(mock_request, "exp_123")

        # Assert
        mock_dashboard.generate_dashboard_html.assert_called_once_with("exp_123")
        assert result.status_code == 200
        assert b"<html>Dashboard</html>" in result.body

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.get_dashboard_instance")
    async def test_get_experiment_dashboard_failure(self, mock_get_dashboard):
        """Test dashboard HTML generation failure."""
        # Arrange
        mock_get_dashboard.side_effect = Exception("Dashboard error")
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import get_experiment_dashboard

            result = await get_experiment_dashboard(mock_request, "exp_123")

        # Assert
        assert result.status_code == 500
        assert b"Dashboard Error" in result.body

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.get_dashboard_instance")
    async def test_get_dashboard_data_success(self, mock_get_dashboard):
        """Test successful dashboard data retrieval."""
        # Arrange
        mock_dashboard = AsyncMock()
        mock_dashboard_data = {
            "experiment_id": "exp_123",
            "experiment_name": "Test Experiment",
            "status": "active",
            "total_users": 100,
            "statistical_significance": 0.95,
            "success_rate": 75.5,
            "error_rate": 2.1,
            "avg_response_time_ms": 150.0,
            "avg_token_reduction": 25.5,
            "risk_level": "low",
            "confidence_level": "high",
            "active_alerts": [],
            "recommendations": ["Continue experiment"],
            "last_updated": "2024-01-01T12:00:00",
        }
        mock_dashboard.get_dashboard_data = AsyncMock(return_value=mock_dashboard_data)
        mock_get_dashboard.return_value = mock_dashboard
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import get_dashboard_data

            result = await get_dashboard_data(mock_request, "exp_123")

        # Assert
        mock_dashboard.get_dashboard_data.assert_called_once_with("exp_123")
        assert result.experiment_id == "exp_123"
        assert result.total_users == 100
        assert result.active_alerts == 0

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.get_dashboard_instance")
    async def test_get_dashboard_data_not_found(self, mock_get_dashboard):
        """Test dashboard data retrieval when not found."""
        # Arrange
        mock_dashboard = AsyncMock()
        mock_dashboard.get_dashboard_data = AsyncMock(return_value=None)
        mock_get_dashboard.return_value = mock_dashboard
        mock_request = create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import get_dashboard_data

            with pytest.raises(HTTPException) as exc_info:
                await get_dashboard_data(mock_request, "exp_123")

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_experiment_results_success(self):
        """Test successful experiment results retrieval."""
        # Arrange
        mock_manager = Mock()
        mock_results = Mock()
        mock_results.experiment_id = "exp_123"
        mock_results.experiment_name = "Test Experiment"
        mock_results.total_users = 100
        mock_results.statistical_significance = 0.95
        mock_results.confidence_interval = (0.1, 0.3)
        mock_results.p_value = 0.05
        mock_results.effect_size = 0.2
        mock_results.performance_summary = {"avg_time": 150}
        mock_results.success_criteria_met = {"response_time": True}
        mock_results.failure_thresholds_exceeded = {"error_rate": False}
        mock_results.recommendation = "Continue"
        mock_results.confidence_level = "high"
        mock_results.next_actions = ["Monitor"]

        mock_manager.get_experiment_results = AsyncMock(return_value=mock_results)
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import get_experiment_results

            result = await get_experiment_results(mock_request, "exp_123", mock_manager)

        # Assert
        mock_manager.get_experiment_results.assert_called_once_with("exp_123")
        assert result.experiment_id == "exp_123"
        assert result.total_users == 100

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.get_dashboard_instance")
    async def test_get_experiments_overview_success(self, mock_get_dashboard):
        """Test successful experiments overview retrieval."""
        # Arrange
        mock_dashboard = AsyncMock()
        mock_summaries = [
            {
                "id": "exp_123",
                "name": "Test Experiment",
                "status": "active",
                "target_percentage": 50.0,
                "current_percentage": 25.0,
                "total_users": 100,
                "statistical_significance": 0.95,
                "created_at": "2024-01-01T12:00:00",
                "start_time": "2024-01-01T13:00:00",
                "end_time": None,
                "active_alerts": 0,
                "risk_level": "low",
            },
        ]
        mock_dashboard.get_experiment_summary = AsyncMock(return_value=mock_summaries)
        mock_get_dashboard.return_value = mock_dashboard
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import get_experiments_overview

            result = await get_experiments_overview(mock_request)

        # Assert
        mock_dashboard.get_experiment_summary.assert_called_once()
        assert len(result) == 1
        assert result[0].id == "exp_123"
        assert result[0].name == "Test Experiment"


class TestQuickSetupEndpoints:
    """Test suite for quick setup endpoints."""

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.audit_logger_instance")
    @patch("src.api.ab_testing_endpoints.create_dynamic_loading_experiment")
    async def test_quick_setup_dynamic_loading_experiment_success(self, mock_create_experiment, mock_audit_logger):
        """Test successful quick setup of dynamic loading experiment."""
        # Arrange
        mock_create_experiment.return_value = "exp_123"
        mock_manager = Mock()
        mock_request = create_mock_request()

        # Act
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import quick_setup_dynamic_loading_experiment

            result = await quick_setup_dynamic_loading_experiment(mock_request, 50.0, 168, mock_manager)

        # Assert
        mock_create_experiment.assert_called_once_with(target_percentage=50.0, duration_hours=168)
        assert result.status_code == 201
        content = json.loads(result.body.decode())
        assert content["success"] is True
        assert content["experiment_id"] == "exp_123"
        mock_audit_logger.log_api_event.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.api.ab_testing_endpoints.create_dynamic_loading_experiment")
    async def test_quick_setup_dynamic_loading_experiment_failure(self, mock_create_experiment):
        """Test quick setup failure."""
        # Arrange
        mock_create_experiment.side_effect = Exception("Creation failed")
        mock_manager = Mock()
        mock_request = create_mock_request()

        # Act & Assert
        with disable_rate_limiting():
            from src.api.ab_testing_endpoints import quick_setup_dynamic_loading_experiment

            with pytest.raises(HTTPException) as exc_info:
                await quick_setup_dynamic_loading_experiment(mock_request, 50.0, 168, mock_manager)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to create dynamic loading experiment" in str(exc_info.value.detail)


class TestErrorHandling:
    """Test suite for error handling scenarios."""

    def test_pydantic_validation_error_handling(self):
        """Test that Pydantic validation errors are properly formatted."""
        # Test field validation errors
        with pytest.raises(ValidationError) as exc_info:
            CreateExperimentRequest(name="", description="Test", experiment_type="invalid")  # Too short  # Invalid type

        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Should have multiple validation errors

        # Check that we have both string length and value errors
        error_types = [error["type"] for error in errors]
        assert "string_too_short" in error_types or "value_error" in error_types
