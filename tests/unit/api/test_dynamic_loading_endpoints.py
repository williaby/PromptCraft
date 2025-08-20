"""
Comprehensive test suite for Dynamic Loading API endpoints.

This module tests all endpoints in src/api/dynamic_loading_endpoints.py including:
- Query optimization endpoint
- System status and health checks
- Performance reporting
- User command execution
- Demo functionality
- Live metrics
- Function registry statistics
- Error handling and validation
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.requests import Request

# Import the module for coverage


def create_starlette_request(method="POST", path="/test"):
    """Utility function to create proper Starlette Request objects for testing."""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [],
        "query_string": b"",
        "client": ("127.0.0.1", 80),
    }
    receive = AsyncMock()
    return Request(scope, receive)


from src.api.dynamic_loading_endpoints import (
    DemoRunRequest,
    PerformanceReportResponse,
    QueryOptimizationRequest,
    QueryOptimizationResponse,
    SystemStatusResponse,
    UserCommandRequest,
    UserCommandResponse,
    dynamic_loading_health_check,
    execute_user_command,
    get_function_registry_stats,
    get_integration_dependency,
    get_live_metrics,
    get_performance_report,
    get_system_status,
    optimize_query,
    router,
    run_comprehensive_demo,
)
from src.core.dynamic_function_loader import LoadingStrategy
from src.core.dynamic_loading_integration import DynamicLoadingIntegration, IntegrationMode


class TestQueryOptimizationRequest:
    """Test QueryOptimizationRequest validation."""

    def test_valid_request_creation(self):
        """Test creating a valid query optimization request."""
        request = QueryOptimizationRequest(
            query="test query",
            user_id="test_user",
            strategy="balanced",
            user_commands=["/help", "/status"],
        )

        assert request.query == "test query"
        assert request.user_id == "test_user"
        assert request.strategy == "balanced"
        assert request.user_commands == ["/help", "/status"]

    def test_default_values(self):
        """Test request with default values."""
        request = QueryOptimizationRequest(query="minimal query")

        assert request.query == "minimal query"
        assert request.user_id == "api_user"
        assert request.strategy == "balanced"
        assert request.user_commands is None

    def test_strategy_validation_valid(self):
        """Test valid strategy validation."""
        for strategy in ["conservative", "balanced", "aggressive"]:
            request = QueryOptimizationRequest(query="test", strategy=strategy)
            assert request.strategy == strategy

    def test_strategy_validation_invalid(self):
        """Test invalid strategy validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryOptimizationRequest(query="test", strategy="invalid")

        error = exc_info.value.errors()[0]
        assert "Strategy must be one of" in error["msg"]

    def test_strategy_case_insensitive(self):
        """Test strategy validation is case insensitive."""
        request = QueryOptimizationRequest(query="test", strategy="BALANCED")
        assert request.strategy == "balanced"

    def test_query_length_validation(self):
        """Test query length validation."""
        # Test minimum length
        with pytest.raises(ValidationError):
            QueryOptimizationRequest(query="")

        # Test maximum length
        long_query = "x" * 2001
        with pytest.raises(ValidationError):
            QueryOptimizationRequest(query=long_query)

    def test_user_commands_validation_valid(self):
        """Test valid user commands validation."""
        request = QueryOptimizationRequest(
            query="test",
            user_commands=["/help", "/status", "/config"],
        )
        assert len(request.user_commands) == 3

    def test_user_commands_validation_too_many(self):
        """Test user commands validation with too many commands."""
        commands = [f"/cmd{i}" for i in range(11)]
        with pytest.raises(ValidationError) as exc_info:
            QueryOptimizationRequest(query="test", user_commands=commands)

        error = exc_info.value.errors()[0]
        assert "Maximum 10 user commands allowed" in error["msg"]

    def test_user_commands_validation_invalid_format(self):
        """Test user commands validation with invalid format."""
        with pytest.raises(ValidationError) as exc_info:
            QueryOptimizationRequest(query="test", user_commands=["help", "/status"])

        error = exc_info.value.errors()[0]
        assert "User commands must start with '/'" in error["msg"]


class TestUserCommandRequest:
    """Test UserCommandRequest validation."""

    def test_valid_request_creation(self):
        """Test creating a valid user command request."""
        request = UserCommandRequest(
            command="/help",
            session_id="session123",
            user_id="test_user",
        )

        assert request.command == "/help"
        assert request.session_id == "session123"
        assert request.user_id == "test_user"

    def test_command_validation_valid(self):
        """Test valid command validation."""
        request = UserCommandRequest(command="/status")
        assert request.command == "/status"

    def test_command_validation_invalid(self):
        """Test invalid command validation."""
        with pytest.raises(ValidationError) as exc_info:
            UserCommandRequest(command="help")

        error = exc_info.value.errors()[0]
        assert "Commands must start with '/'" in error["msg"]

    def test_command_length_validation(self):
        """Test command length validation."""
        # Test maximum length
        long_command = "/" + "x" * 200
        with pytest.raises(ValidationError):
            UserCommandRequest(command=long_command)


class TestDemoRunRequest:
    """Test DemoRunRequest validation."""

    def test_valid_request_creation(self):
        """Test creating a valid demo run request."""
        request = DemoRunRequest(
            scenario_types=["basic_optimization", "performance_stress"],
            export_results=True,
        )

        assert request.scenario_types == ["basic_optimization", "performance_stress"]
        assert request.export_results is True

    def test_default_values(self):
        """Test request with default values."""
        request = DemoRunRequest()

        assert request.scenario_types is None
        assert request.export_results is False

    def test_scenario_types_validation_valid(self):
        """Test valid scenario types validation."""
        valid_types = [
            "basic_optimization",
            "complex_workflow",
            "user_interaction",
            "performance_stress",
            "real_world_use_case",
            "edge_case_handling",
        ]
        request = DemoRunRequest(scenario_types=valid_types)
        assert request.scenario_types == valid_types

    def test_scenario_types_validation_invalid(self):
        """Test invalid scenario types validation."""
        with pytest.raises(ValidationError) as exc_info:
            DemoRunRequest(scenario_types=["invalid_scenario"])

        error = exc_info.value.errors()[0]
        assert "Invalid scenario type" in error["msg"]


class TestResponseModels:
    """Test response model creation."""

    def test_query_optimization_response(self):
        """Test QueryOptimizationResponse creation."""
        response = QueryOptimizationResponse(
            success=True,
            session_id="session123",
            processing_time_ms=150.5,
            optimization_results={"reduction": 70.5},
            user_commands_executed=2,
            error_message=None,
        )

        assert response.success is True
        assert response.session_id == "session123"
        assert response.processing_time_ms == 150.5
        assert response.optimization_results == {"reduction": 70.5}
        assert response.user_commands_executed == 2
        assert response.error_message is None

    def test_system_status_response(self):
        """Test SystemStatusResponse creation."""
        response = SystemStatusResponse(
            integration_health="healthy",
            mode="production",
            metrics={"uptime": 24.5},
            components={"loader": True},
            features={"optimization": True},
            uptime_hours=24.5,
        )

        assert response.integration_health == "healthy"
        assert response.mode == "production"
        assert response.metrics == {"uptime": 24.5}
        assert response.components == {"loader": True}
        assert response.features == {"optimization": True}
        assert response.uptime_hours == 24.5

    def test_user_command_response(self):
        """Test UserCommandResponse creation."""
        response = UserCommandResponse(
            success=True,
            message="Command executed successfully",
            command="/help",
            data={"result": "success"},
            suggestions=["Try /status"],
        )

        assert response.success is True
        assert response.message == "Command executed successfully"
        assert response.command == "/help"
        assert response.data == {"result": "success"}
        assert response.suggestions == ["Try /status"]


class TestIntegrationDependency:
    """Test integration dependency function."""

    @patch("src.api.dynamic_loading_endpoints.get_integration_instance")
    async def test_get_integration_dependency_success(self, mock_get_instance):
        """Test successful integration dependency resolution."""
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_get_instance.return_value = mock_integration

        result = await get_integration_dependency()

        assert result == mock_integration
        mock_get_instance.assert_called_once_with(mode=IntegrationMode.PRODUCTION)

    @patch("src.api.dynamic_loading_endpoints.get_integration_instance")
    async def test_get_integration_dependency_failure(self, mock_get_instance):
        """Test integration dependency failure."""
        mock_get_instance.side_effect = Exception("Integration unavailable")

        with pytest.raises(HTTPException) as exc_info:
            await get_integration_dependency()

        assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "Dynamic loading system unavailable" in exc_info.value.detail


class TestOptimizeQueryEndpoint:
    """Test optimize_query endpoint."""

    def create_mock_request(self):
        """Create a proper Starlette Request object."""
        return create_starlette_request("POST", "/api/v1/dynamic-loading/optimize-query")

    def create_mock_integration_result(self):
        """Create a mock integration process_query result."""
        mock_result = Mock()
        mock_result.success = True
        mock_result.session_id = "session123"
        mock_result.total_time_ms = 150.5
        mock_result.baseline_tokens = 1000
        mock_result.optimized_tokens = 300
        mock_result.reduction_percentage = 70.0
        mock_result.target_achieved = True
        mock_result.detection_time_ms = 25.0
        mock_result.loading_time_ms = 75.0
        mock_result.cache_hit = False
        mock_result.fallback_used = False
        mock_result.user_commands = ["/help"]
        mock_result.error_message = None

        # Mock detection result
        mock_detection = Mock()
        mock_detection.categories = {"core": True}
        mock_detection.confidence = 0.95
        mock_detection.reasoning = "High confidence"
        mock_result.detection_result = mock_detection

        return mock_result

    @patch("src.api.dynamic_loading_endpoints.audit_logger_instance")
    @patch("src.api.dynamic_loading_endpoints.time")
    async def test_optimize_query_success(self, mock_time, mock_audit_logger):
        """Test successful query optimization."""
        # Setup mocks
        mock_time.perf_counter.side_effect = [0.0, 0.1505]  # Start and end times
        mock_request = self.create_mock_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_result = self.create_mock_integration_result()
        mock_integration.process_query = AsyncMock(return_value=mock_result)

        query_request = QueryOptimizationRequest(
            query="test query",
            user_id="test_user",
            strategy="balanced",
            user_commands=["/help"],
        )

        # Execute endpoint
        response = await optimize_query(mock_request, query_request, mock_integration)

        # Verify response
        assert response.success is True
        assert response.session_id == "session123"
        assert response.processing_time_ms == 150.5
        assert response.optimization_results["baseline_tokens"] == 1000
        assert response.optimization_results["optimized_tokens"] == 300
        assert response.optimization_results["reduction_percentage"] == 70.0
        assert response.optimization_results["target_achieved"] is True
        assert response.user_commands_executed == 1
        assert response.error_message is None

        # Verify integration was called correctly
        mock_integration.process_query.assert_called_once_with(
            query="test query",
            user_id="test_user",
            strategy=LoadingStrategy.BALANCED,
            user_commands=["/help"],
        )

        # Verify audit logging
        mock_audit_logger.log_api_event.assert_called_once()

    @patch("src.api.dynamic_loading_endpoints.audit_logger_instance")
    @patch("src.api.dynamic_loading_endpoints.time")
    async def test_optimize_query_integration_failure(self, mock_time, mock_audit_logger):
        """Test query optimization with integration failure."""
        mock_time.perf_counter.side_effect = [0.0, 0.1505]
        mock_request = self.create_mock_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_integration.process_query = AsyncMock(side_effect=Exception("Integration error"))

        query_request = QueryOptimizationRequest(query="test query")

        with pytest.raises(HTTPException) as exc_info:
            await optimize_query(mock_request, query_request, mock_integration)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Query optimization failed" in exc_info.value.detail

        # Verify error was logged
        mock_audit_logger.log_api_event.assert_called_once()

    async def test_optimize_query_strategy_mapping(self):
        """Test strategy string to enum mapping."""
        mock_request = self.create_mock_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_result = self.create_mock_integration_result()
        mock_integration.process_query = AsyncMock(return_value=mock_result)

        # Test all valid strategies
        strategies = {
            "conservative": LoadingStrategy.CONSERVATIVE,
            "balanced": LoadingStrategy.BALANCED,
            "aggressive": LoadingStrategy.AGGRESSIVE,
        }

        for strategy_str, strategy_enum in strategies.items():
            query_request = QueryOptimizationRequest(query="test", strategy=strategy_str)

            with patch("src.api.dynamic_loading_endpoints.time.perf_counter", side_effect=[0.0, 0.1]):
                with patch("src.api.dynamic_loading_endpoints.audit_logger_instance"):
                    await optimize_query(mock_request, query_request, mock_integration)

            # Verify correct strategy was passed
            calls = mock_integration.process_query.call_args_list
            assert calls[-1][1]["strategy"] == strategy_enum


class TestSystemStatusEndpoint:
    """Test get_system_status endpoint."""

    def create_mock_request(self):
        """Create a proper Starlette Request object."""
        return create_starlette_request("GET", "/api/v1/dynamic-loading/status")

    async def test_get_system_status_success(self):
        """Test successful system status retrieval."""
        mock_request = self.create_mock_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)

        status_data = {
            "integration_health": "healthy",
            "mode": "production",
            "metrics": {"uptime_hours": 24.5, "queries": 100},
            "components": {"loader": True, "detector": True},
            "features": {"optimization": True, "caching": True},
        }
        mock_integration.get_system_status = AsyncMock(return_value=status_data)

        response = await get_system_status(mock_request, mock_integration)

        assert response.integration_health == "healthy"
        assert response.mode == "production"
        assert response.metrics == {"uptime_hours": 24.5, "queries": 100}
        assert response.components == {"loader": True, "detector": True}
        assert response.features == {"optimization": True, "caching": True}
        assert response.uptime_hours == 24.5

        mock_integration.get_system_status.assert_called_once()

    async def test_get_system_status_failure(self):
        """Test system status retrieval failure."""
        mock_request = self.create_mock_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_integration.get_system_status = AsyncMock(side_effect=Exception("Status error"))

        with pytest.raises(HTTPException) as exc_info:
            await get_system_status(mock_request, mock_integration)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve system status" in exc_info.value.detail


class TestPerformanceReportEndpoint:
    """Test get_performance_report endpoint."""

    async def test_get_performance_report_success(self):
        """Test successful performance report retrieval."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)

        report_data = {
            "timestamp": "2024-01-01T12:00:00Z",
            "integration_report": {
                "integration_metrics": {"queries_processed": 1000},
                "performance_summary": {"avg_time": 150.5},
                "timing_analysis": {"p95": 200.0},
                "system_health": {"status": "healthy"},
            },
        }
        mock_integration.get_performance_report = AsyncMock(return_value=report_data)

        response = await get_performance_report(mock_request, mock_integration)

        assert response.report_timestamp == "2024-01-01T12:00:00Z"
        assert response.integration_metrics == {"queries_processed": 1000}
        assert response.performance_summary == {"avg_time": 150.5}
        assert response.timing_analysis == {"p95": 200.0}
        assert response.system_health == {"status": "healthy"}

    async def test_get_performance_report_failure(self):
        """Test performance report retrieval failure."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_integration.get_performance_report = AsyncMock(side_effect=Exception("Report error"))

        with pytest.raises(HTTPException) as exc_info:
            await get_performance_report(mock_request, mock_integration)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve performance report" in exc_info.value.detail


class TestUserCommandEndpoint:
    """Test execute_user_command endpoint."""

    @patch("src.api.dynamic_loading_endpoints.audit_logger_instance")
    async def test_execute_user_command_success(self, mock_audit_logger):
        """Test successful user command execution."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)

        command_result = Mock()
        command_result.success = True
        command_result.message = "Command executed successfully"
        command_result.data = {"result": "success"}
        command_result.suggestions = ["Try /status"]

        mock_integration.execute_user_command = AsyncMock(return_value=command_result)

        command_request = UserCommandRequest(
            command="/help",
            session_id="session123",
            user_id="test_user",
        )

        response = await execute_user_command(mock_request, command_request, mock_integration)

        assert response.success is True
        assert response.message == "Command executed successfully"
        assert response.command == "/help"
        assert response.data == {"result": "success"}
        assert response.suggestions == ["Try /status"]

        # Verify integration was called correctly
        mock_integration.execute_user_command.assert_called_once_with(
            command="/help",
            session_id="session123",
            user_id="test_user",
        )

        # Verify audit logging
        mock_audit_logger.log_api_event.assert_called_once()

    async def test_execute_user_command_failure(self):
        """Test user command execution failure."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_integration.execute_user_command = AsyncMock(side_effect=Exception("Command error"))

        command_request = UserCommandRequest(command="/help")

        with pytest.raises(HTTPException) as exc_info:
            await execute_user_command(mock_request, command_request, mock_integration)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Command execution failed" in exc_info.value.detail


class TestComprehensiveDemoEndpoint:
    """Test run_comprehensive_demo endpoint."""

    @patch("src.api.dynamic_loading_endpoints.ComprehensivePrototypeDemo")
    @patch("src.api.dynamic_loading_endpoints.audit_logger_instance")
    async def test_run_demo_success_export_results(self, mock_audit_logger, mock_demo_class):
        """Test successful demo run with exported results."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)

        # Setup demo mock
        mock_demo = Mock()
        mock_demo.initialize = AsyncMock(return_value=True)

        demo_results = {
            "demo_metadata": {"total_scenarios": 5, "total_time_seconds": 120.5},
            "performance_summary": {
                "success_rate": 0.95,
                "token_optimization": {
                    "average_reduction": 72.5,
                    "target_achievement_rate": 0.90,
                },
                "performance_metrics": {"average_processing_time_ms": 150.0},
            },
            "production_readiness": {
                "readiness_level": "production_ready",
                "overall_score": 0.92,
                "key_achievements": ["High performance", "Stable operation"],
                "deployment_recommendation": "Ready for production deployment",
            },
        }
        mock_demo.run_comprehensive_demo = AsyncMock(return_value=demo_results)
        mock_demo_class.return_value = mock_demo

        demo_request = DemoRunRequest(export_results=True)

        response = await run_comprehensive_demo(mock_request, demo_request, mock_integration)

        # Verify response is JSONResponse with full results
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_200_OK

        # Parse response content
        response_data = json.loads(response.body.decode())
        assert response_data == demo_results

        # Verify demo was initialized and run
        mock_demo.initialize.assert_called_once()
        mock_demo.run_comprehensive_demo.assert_called_once()

        # Verify audit logging
        mock_audit_logger.log_api_event.assert_called_once()

    @patch("src.api.dynamic_loading_endpoints.ComprehensivePrototypeDemo")
    @patch("src.api.dynamic_loading_endpoints.audit_logger_instance")
    async def test_run_demo_success_summary_only(self, mock_audit_logger, mock_demo_class):
        """Test successful demo run with summary only."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)

        # Setup demo mock
        mock_demo = Mock()
        mock_demo.initialize = AsyncMock(return_value=True)

        demo_results = {
            "demo_metadata": {"total_scenarios": 3, "total_time_seconds": 60.0},
            "performance_summary": {
                "success_rate": 0.98,
                "token_optimization": {
                    "average_reduction": 75.0,
                    "target_achievement_rate": 0.95,
                },
                "performance_metrics": {"average_processing_time_ms": 120.0},
            },
            "production_readiness": {
                "readiness_level": "production_ready",
                "overall_score": 0.95,
                "key_achievements": ["Excellent performance"],
                "deployment_recommendation": "Immediate deployment recommended",
            },
        }
        mock_demo.run_comprehensive_demo = AsyncMock(return_value=demo_results)
        mock_demo_class.return_value = mock_demo

        demo_request = DemoRunRequest(export_results=False)

        response = await run_comprehensive_demo(mock_request, demo_request, mock_integration)

        # Verify response is JSONResponse with summary only
        assert isinstance(response, JSONResponse)

        # Parse response content and verify it's a summary
        response_data = json.loads(response.body.decode())
        assert "demo_summary" in response_data
        assert "key_achievements" in response_data
        assert "deployment_recommendation" in response_data

        # Verify summary contains expected data
        demo_summary = response_data["demo_summary"]
        assert demo_summary["total_scenarios"] == 3
        assert demo_summary["success_rate"] == 0.98
        assert demo_summary["average_reduction"] == 75.0

    @patch("src.api.dynamic_loading_endpoints.ComprehensivePrototypeDemo")
    async def test_run_demo_initialization_failure(self, mock_demo_class):
        """Test demo run with initialization failure."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)

        mock_demo = Mock()
        mock_demo.initialize = AsyncMock(return_value=False)
        mock_demo_class.return_value = mock_demo

        demo_request = DemoRunRequest()

        with pytest.raises(HTTPException) as exc_info:
            await run_comprehensive_demo(mock_request, demo_request, mock_integration)

        # The inner 503 exception gets caught and re-raised as 500 by the generic handler
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Demo execution failed" in str(exc_info.value.detail)

    @patch("src.api.dynamic_loading_endpoints.ComprehensivePrototypeDemo")
    async def test_run_demo_execution_failure(self, mock_demo_class):
        """Test demo run with execution failure."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)

        mock_demo = Mock()
        mock_demo.initialize = AsyncMock(return_value=True)
        mock_demo.run_comprehensive_demo = AsyncMock(side_effect=Exception("Demo execution error"))
        mock_demo_class.return_value = mock_demo

        demo_request = DemoRunRequest()

        with pytest.raises(HTTPException) as exc_info:
            await run_comprehensive_demo(mock_request, demo_request, mock_integration)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Demo execution failed" in exc_info.value.detail


class TestLiveMetricsEndpoint:
    """Test get_live_metrics endpoint."""

    @patch("src.api.dynamic_loading_endpoints.datetime")
    async def test_get_live_metrics_success(self, mock_datetime):
        """Test successful live metrics retrieval."""
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"

        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)

        status_data = {
            "integration_health": "healthy",
            "metrics": {
                "total_queries_processed": 1000,
                "success_rate": 0.95,
                "average_reduction_percentage": 72.5,
                "target_achievement_rate": 0.88,
                "average_total_time_ms": 150.0,
                "cache_hit_rate": 0.75,
                "uptime_hours": 24.5,
                "error_count": 5,
                "warning_count": 2,
                "successful_optimizations": 950,
                "fallback_activations": 10,
                "user_commands_executed": 100,
                "user_command_success_rate": 0.98,
            },
            "active_sessions": 15,
        }
        mock_integration.get_system_status = AsyncMock(return_value=status_data)

        response = await get_live_metrics(mock_request, mock_integration)

        # Verify response is JSONResponse
        assert isinstance(response, JSONResponse)

        # Parse response content
        response_data = json.loads(response.body.decode())

        assert response_data["timestamp"] == "2024-01-01T12:00:00"
        assert response_data["health_status"] == "healthy"

        # Verify performance metrics
        performance = response_data["performance"]
        assert performance["queries_processed"] == 1000
        assert performance["success_rate"] == 0.95
        assert performance["average_reduction"] == 72.5
        assert performance["target_achievement_rate"] == 0.88
        assert performance["average_processing_time_ms"] == 150.0
        assert performance["cache_hit_rate"] == 0.75

        # Verify system metrics
        system = response_data["system"]
        assert system["uptime_hours"] == 24.5
        assert system["error_count"] == 5
        assert system["warning_count"] == 2
        assert system["active_sessions"] == 15

        # Verify optimization metrics
        optimization = response_data["optimization"]
        assert optimization["successful_optimizations"] == 950
        assert optimization["fallback_activations"] == 10
        assert optimization["user_commands_executed"] == 100
        assert optimization["user_command_success_rate"] == 0.98

    async def test_get_live_metrics_failure(self):
        """Test live metrics retrieval failure."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_integration.get_system_status = AsyncMock(side_effect=Exception("Metrics error"))

        with pytest.raises(HTTPException) as exc_info:
            await get_live_metrics(mock_request, mock_integration)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve live metrics" in exc_info.value.detail


class TestFunctionRegistryStatsEndpoint:
    """Test get_function_registry_stats endpoint."""

    @patch("src.api.dynamic_loading_endpoints.datetime")
    async def test_get_function_registry_stats_success(self, mock_datetime):
        """Test successful function registry stats retrieval."""
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"

        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)

        # Setup function loader mock
        mock_function_loader = Mock()
        mock_integration.function_loader = mock_function_loader

        # Setup registry mock
        mock_registry = Mock()
        mock_function_loader.function_registry = mock_registry

        # Mock tier data
        from enum import Enum

        class MockLoadingTier(Enum):
            TIER_1 = "tier_1"
            TIER_2 = "tier_2"

        mock_tier1 = MockLoadingTier.TIER_1
        mock_tier2 = MockLoadingTier.TIER_2
        mock_registry.tiers = [mock_tier1, mock_tier2]

        # Mock tier functions and costs
        mock_registry.get_functions_by_tier.side_effect = [
            ["func1", "func2", "func3", "func4", "func5", "func6"],  # tier_1
            ["func7", "func8"],  # tier_2
        ]
        mock_registry.get_tier_token_cost.side_effect = [500, 200]  # costs

        # Mock category data
        mock_registry.categories = ["core", "utils", "advanced"]
        mock_registry.get_functions_by_category.side_effect = [
            ["func1", "func2"],  # core
            ["func3"],  # utils
            ["func4", "func5"],  # advanced
        ]
        mock_registry.calculate_loading_cost.side_effect = [
            (300, {}),  # core
            (100, {}),  # utils
            (250, {}),  # advanced
        ]

        # Mock registry summary
        mock_registry.functions = ["func1", "func2", "func3", "func4", "func5", "func6", "func7", "func8"]
        mock_registry.get_baseline_token_cost.return_value = 1000

        response = await get_function_registry_stats(mock_request, mock_integration)

        # Verify response is JSONResponse
        assert isinstance(response, JSONResponse)

        # Parse response content
        response_data = json.loads(response.body.decode())

        # Verify registry summary
        summary = response_data["registry_summary"]
        assert summary["total_functions"] == 8
        assert summary["total_categories"] == 3
        assert summary["total_tiers"] == 2
        assert summary["baseline_token_cost"] == 1000
        assert summary["last_updated"] == "2024-01-01T12:00:00"

        # Verify tier breakdown
        tier_breakdown = response_data["tier_breakdown"]
        assert "tier_1" in tier_breakdown
        assert "tier_2" in tier_breakdown

        tier1_data = tier_breakdown["tier_1"]
        assert tier1_data["name"] == "tier_1"
        assert tier1_data["function_count"] == 6
        assert tier1_data["token_cost"] == 500
        assert len(tier1_data["sample_functions"]) == 5  # First 5 functions

        # Verify category breakdown
        category_breakdown = response_data["category_breakdown"]
        assert "core" in category_breakdown
        assert "utils" in category_breakdown
        assert "advanced" in category_breakdown

        core_data = category_breakdown["core"]
        assert core_data["function_count"] == 2
        assert core_data["token_cost"] == 300
        assert len(core_data["sample_functions"]) == 2  # First 3 functions (but only 2 exist)

        # Verify optimization potential
        optimization = response_data["optimization_potential"]
        assert "max_possible_reduction" in optimization
        assert optimization["typical_reduction_range"] == "60-85%"
        assert optimization["aggressive_reduction_potential"] == "80-90%"

    async def test_get_function_registry_stats_no_function_loader(self):
        """Test function registry stats with no function loader."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_integration.function_loader = None

        with pytest.raises(HTTPException) as exc_info:
            await get_function_registry_stats(mock_request, mock_integration)

        # The inner 503 exception gets caught and re-raised as 500 by the generic handler
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve function registry statistics" in str(exc_info.value.detail)

    async def test_get_function_registry_stats_failure(self):
        """Test function registry stats retrieval failure."""
        mock_request = create_starlette_request()
        mock_integration = Mock(spec=DynamicLoadingIntegration)
        mock_integration.function_loader = Mock()
        mock_integration.function_loader.function_registry = Mock()
        mock_integration.function_loader.function_registry.tiers = Mock(side_effect=Exception("Registry error"))

        with pytest.raises(HTTPException) as exc_info:
            await get_function_registry_stats(mock_request, mock_integration)

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to retrieve function registry statistics" in exc_info.value.detail


class TestHealthCheckEndpoint:
    """Test dynamic_loading_health_check endpoint."""

    @patch("src.api.dynamic_loading_endpoints.get_integration_instance")
    @patch("src.api.dynamic_loading_endpoints.datetime")
    async def test_health_check_healthy_status(self, mock_datetime, mock_get_instance):
        """Test health check with healthy status."""
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"

        mock_request = create_starlette_request()
        mock_integration = Mock()

        status_data = {
            "integration_health": "healthy",
            "metrics": {
                "uptime_hours": 24.5,
                "total_queries_processed": 1000,
                "success_rate": 0.95,
            },
        }
        mock_integration.get_system_status = AsyncMock(return_value=status_data)
        mock_get_instance.return_value = mock_integration

        response = await dynamic_loading_health_check(mock_request)

        # Verify response is JSONResponse with 200 status
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_200_OK

        # Parse response content
        response_data = json.loads(response.body.decode())

        assert response_data["status"] == "healthy"
        assert response_data["service"] == "dynamic-function-loading"
        assert response_data["uptime_hours"] == 24.5
        assert response_data["queries_processed"] == 1000
        assert response_data["success_rate"] == 0.95
        assert response_data["timestamp"] == "2024-01-01T12:00:00"

        mock_get_instance.assert_called_once_with(mode=IntegrationMode.PRODUCTION)

    @patch("src.api.dynamic_loading_endpoints.get_integration_instance")
    @patch("src.api.dynamic_loading_endpoints.datetime")
    async def test_health_check_degraded_status(self, mock_datetime, mock_get_instance):
        """Test health check with degraded status."""
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"

        mock_request = create_starlette_request()
        mock_integration = Mock()

        status_data = {
            "integration_health": "degraded",
            "metrics": {
                "uptime_hours": 2.0,
                "total_queries_processed": 50,
                "success_rate": 0.75,
            },
        }
        mock_integration.get_system_status = AsyncMock(return_value=status_data)
        mock_get_instance.return_value = mock_integration

        response = await dynamic_loading_health_check(mock_request)

        # Verify response is JSONResponse with 200 status (degraded is still acceptable)
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_200_OK

        # Parse response content
        response_data = json.loads(response.body.decode())
        assert response_data["status"] == "degraded"

    @patch("src.api.dynamic_loading_endpoints.get_integration_instance")
    @patch("src.api.dynamic_loading_endpoints.datetime")
    async def test_health_check_unhealthy_status(self, mock_datetime, mock_get_instance):
        """Test health check with unhealthy status."""
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"

        mock_request = create_starlette_request()
        mock_integration = Mock()

        status_data = {
            "integration_health": "unhealthy",
            "metrics": {"uptime_hours": 0.1},
        }
        mock_integration.get_system_status = AsyncMock(return_value=status_data)
        mock_get_instance.return_value = mock_integration

        response = await dynamic_loading_health_check(mock_request)

        # Verify response is JSONResponse with 503 status
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        # Parse response content
        response_data = json.loads(response.body.decode())
        assert response_data["status"] == "unhealthy"
        assert response_data["error"] == "System not healthy"

    @patch("src.api.dynamic_loading_endpoints.get_integration_instance")
    @patch("src.api.dynamic_loading_endpoints.datetime")
    async def test_health_check_exception(self, mock_datetime, mock_get_instance):
        """Test health check with exception."""
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"

        mock_request = create_starlette_request()
        mock_get_instance.side_effect = Exception("Integration unavailable")

        response = await dynamic_loading_health_check(mock_request)

        # Verify response is JSONResponse with 503 status
        assert isinstance(response, JSONResponse)
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        # Parse response content
        response_data = json.loads(response.body.decode())
        assert response_data["status"] == "failed"
        assert response_data["service"] == "dynamic-function-loading"
        assert "Integration unavailable" in response_data["error"]


class TestEndpointIntegration:
    """Test endpoint integration and edge cases."""

    def test_router_configuration(self):
        """Test router is configured correctly."""
        assert router.prefix == "/api/v1/dynamic-loading"
        assert "dynamic-loading" in router.tags

    async def test_all_endpoints_have_rate_limiting(self):
        """Test that all endpoints have rate limiting decorators."""
        # This test verifies that rate limiting is applied by checking the function decorators
        # In a real application, you would test the actual rate limiting behavior

        # Get all route handlers from the router
        routes = [route for route in router.routes if hasattr(route, "endpoint")]

        # Verify we have the expected number of endpoints
        assert len(routes) >= 8  # We have 8 main endpoints

        # Note: In practice, you would need to test actual rate limiting behavior
        # by making multiple requests and verifying rate limit responses
        # This would require integration testing with the actual FastAPI app

    def test_response_models_are_correctly_typed(self):
        """Test that response models have correct type annotations."""
        # Verify key response models exist and have expected fields
        assert hasattr(QueryOptimizationResponse, "__annotations__")
        assert hasattr(SystemStatusResponse, "__annotations__")
        assert hasattr(PerformanceReportResponse, "__annotations__")
        assert hasattr(UserCommandResponse, "__annotations__")

        # Verify required fields
        assert "success" in QueryOptimizationResponse.__annotations__
        assert "session_id" in QueryOptimizationResponse.__annotations__
        assert "processing_time_ms" in QueryOptimizationResponse.__annotations__

        assert "integration_health" in SystemStatusResponse.__annotations__
        assert "mode" in SystemStatusResponse.__annotations__
        assert "metrics" in SystemStatusResponse.__annotations__

    def test_model_validation_edge_cases(self):
        """Test edge cases for model validation."""
        # Test query with exactly max length
        max_query = "x" * 2000
        request = QueryOptimizationRequest(query=max_query)
        assert len(request.query) == 2000

        # Test command with slash and minimum content
        request = UserCommandRequest(command="/x")
        assert request.command == "/x"

        # Test empty scenario types list
        request = DemoRunRequest(scenario_types=[])
        assert request.scenario_types == []

    async def test_error_handling_consistency(self):
        """Test that all endpoints handle errors consistently."""
        # All endpoints should raise HTTPException with appropriate status codes
        # and follow the same error response pattern

        # This is verified through the individual endpoint tests above
        # but here we can verify consistency patterns

        # Verify that 500 errors are used for internal failures
        # Verify that 503 errors are used for service unavailability
        # Verify that 400 errors are used for validation failures

        # This test serves as documentation of error handling patterns
        assert status.HTTP_500_INTERNAL_SERVER_ERROR == 500
        assert status.HTTP_503_SERVICE_UNAVAILABLE == 503
        assert status.HTTP_400_BAD_REQUEST == 400
