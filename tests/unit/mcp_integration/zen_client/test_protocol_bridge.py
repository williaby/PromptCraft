"""Comprehensive tests for MCPProtocolBridge."""

import json
from unittest.mock import patch

from pydantic import ValidationError
import pytest

from src.mcp_integration.zen_client.models import (
    MCPToolCall,
)
from src.mcp_integration.zen_client.protocol_bridge import MCPProtocolBridge


class TestMCPProtocolBridge:
    """Test MCPProtocolBridge functionality."""

    def test_initialization(self):
        """Test protocol bridge initialization."""
        bridge = MCPProtocolBridge()

        assert bridge.bridge_tool_name == "promptcraft_mcp_bridge"

    def test_http_to_mcp_request_route_analysis(self, sample_route_analysis_request):
        """Test HTTP to MCP conversion for route analysis."""
        bridge = MCPProtocolBridge()

        request_data = sample_route_analysis_request.dict()
        endpoint = "/api/promptcraft/route/analyze"

        mcp_call = bridge.http_to_mcp_request(endpoint, request_data)

        assert isinstance(mcp_call, MCPToolCall)
        assert mcp_call.name == "promptcraft_mcp_bridge"
        assert mcp_call.arguments["action"] == "analyze_route"
        assert mcp_call.arguments["prompt"] == request_data["prompt"]
        assert mcp_call.arguments["user_tier"] == request_data["user_tier"]
        assert mcp_call.arguments["task_type"] == request_data["task_type"]
        assert mcp_call.arguments["model"] == "flash"

    def test_http_to_mcp_request_smart_execution(self, sample_smart_execution_request):
        """Test HTTP to MCP conversion for smart execution."""
        bridge = MCPProtocolBridge()

        request_data = sample_smart_execution_request.dict()
        endpoint = "/api/promptcraft/execute/smart"

        mcp_call = bridge.http_to_mcp_request(endpoint, request_data)

        assert mcp_call.name == "promptcraft_mcp_bridge"
        assert mcp_call.arguments["action"] == "smart_execute"
        assert mcp_call.arguments["prompt"] == request_data["prompt"]
        assert mcp_call.arguments["channel"] == request_data["channel"]
        assert mcp_call.arguments["cost_optimization"] == request_data["cost_optimization"]
        assert mcp_call.arguments["model"] == "auto"

    def test_http_to_mcp_request_model_list(self, sample_model_list_request):
        """Test HTTP to MCP conversion for model listing."""
        bridge = MCPProtocolBridge()

        request_data = sample_model_list_request.dict()
        endpoint = "/api/promptcraft/models/available"

        mcp_call = bridge.http_to_mcp_request(endpoint, request_data)

        assert mcp_call.name == "promptcraft_mcp_bridge"
        assert mcp_call.arguments["action"] == "list_models"
        assert mcp_call.arguments["user_tier"] == request_data["user_tier"]
        assert mcp_call.arguments["include_metadata"] == request_data["include_metadata"]
        assert mcp_call.arguments["format"] == request_data["format"]
        assert mcp_call.arguments["model"] == "flash"

    def test_http_to_mcp_request_unsupported_endpoint(self):
        """Test HTTP to MCP conversion for unsupported endpoint."""
        bridge = MCPProtocolBridge()

        with pytest.raises(ValueError, match="Unsupported endpoint"):
            bridge.http_to_mcp_request("/unsupported/endpoint", {})

    def test_http_to_mcp_request_invalid_data(self):
        """Test HTTP to MCP conversion with invalid request data."""
        bridge = MCPProtocolBridge()

        # Missing required fields for route analysis
        invalid_data = {"prompt": "test"}  # Missing user_tier
        endpoint = "/api/promptcraft/route/analyze"

        with pytest.raises(ValidationError):
            bridge.http_to_mcp_request(endpoint, invalid_data)

    def test_mcp_to_http_response_route_analysis(self):
        """Test MCP to HTTP conversion for route analysis response."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "content": [
                {
                    "text": "PromptCraft MCP Bridge Result: "
                    + json.dumps(
                        {
                            "success": True,
                            "analysis": {
                                "task_type": "generation",
                                "complexity_score": 0.7,
                                "complexity_level": "medium",
                                "indicators": ["creative_task"],
                                "reasoning": "Creative generation task",
                            },
                            "recommendations": {
                                "primary_model": "claude-3-5-sonnet-20241022",
                                "alternative_models": ["gpt-4-turbo"],
                                "estimated_cost": 0.05,
                                "confidence": 0.85,
                            },
                            "processing_time": 1.2,
                            "bridge_version": "1.0.0",
                        },
                    ),
                },
            ],
        }
        endpoint = "/api/promptcraft/route/analyze"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        assert response["success"] is True
        assert response["analysis"]["complexity_score"] == 0.7
        assert response["recommendations"]["primary_model"] == "claude-3-5-sonnet-20241022"
        assert response["processing_time"] == 1.2

    def test_mcp_to_http_response_smart_execution(self):
        """Test MCP to HTTP conversion for smart execution response."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "content": [
                {
                    "text": "PromptCraft MCP Bridge Result: "
                    + json.dumps(
                        {
                            "success": True,
                            "response": {
                                "content": "Generated content",
                                "model_used": "claude-3-5-sonnet",
                                "reasoning": "Task analysis...",
                            },
                            "execution_metadata": {
                                "channel": "stable",
                                "cost_optimization": True,
                                "processing_time": 2.1,
                                "estimated_cost": 0.08,
                            },
                            "bridge_version": "1.0.0",
                        },
                    ),
                },
            ],
        }
        endpoint = "/api/promptcraft/execute/smart"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        assert response["success"] is True
        assert response["result"]["content"] == "Generated content"
        assert response["execution_metadata"]["processing_time"] == 2.1

    def test_mcp_to_http_response_model_list(self):
        """Test MCP to HTTP conversion for model list response."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "content": [
                {
                    "text": "PromptCraft MCP Bridge Result: "
                    + json.dumps(
                        {
                            "success": True,
                            "models": ["claude-3-5-sonnet", "gpt-4-turbo", "gemini-pro"],
                            "metadata": {
                                "user_tier": "premium",
                                "channel": "stable",
                                "total_models": 3,
                                "format": "ui",
                            },
                            "processing_time": 0.3,
                            "bridge_version": "1.0.0",
                        },
                    ),
                },
            ],
        }
        endpoint = "/api/promptcraft/models/available"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        assert response["success"] is True
        assert len(response["models"]) == 3
        assert "claude-3-5-sonnet" in response["models"]
        assert response["metadata"]["total_models"] == 3

    def test_mcp_to_http_response_error_format(self):
        """Test MCP to HTTP conversion with error response."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "content": [
                {
                    "text": "PromptCraft MCP Bridge Result: "
                    + json.dumps({"success": False, "error": "Analysis failed: Invalid input", "processing_time": 0.1}),
                },
            ],
        }
        endpoint = "/api/promptcraft/route/analyze"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        assert response["success"] is False
        assert response["error"] == "Analysis failed: Invalid input"
        assert response["processing_time"] == 0.1

    def test_mcp_to_http_response_empty_content(self):
        """Test MCP to HTTP conversion with empty content."""
        bridge = MCPProtocolBridge()

        mcp_result = {"content": []}
        endpoint = "/api/promptcraft/route/analyze"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        assert response["success"] is False
        assert "Empty MCP response" in response["error"]

    def test_mcp_to_http_response_no_content_key(self):
        """Test MCP to HTTP conversion with no content key."""
        bridge = MCPProtocolBridge()

        mcp_result = {"result": "direct result"}
        endpoint = "/api/promptcraft/route/analyze"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        # Should use the result directly and format as route analysis
        assert "success" in response

    def test_mcp_to_http_response_invalid_json_content(self):
        """Test MCP to HTTP conversion with invalid JSON in content."""
        bridge = MCPProtocolBridge()

        mcp_result = {"content": [{"text": "PromptCraft MCP Bridge Result: invalid json content"}]}
        endpoint = "/api/other/generic"  # Use a non-specific endpoint for generic response

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        assert response["success"] is True
        assert "invalid json content" in str(response["result"])

    def test_mcp_to_http_response_no_bridge_prefix(self):
        """Test MCP to HTTP conversion without bridge prefix."""
        bridge = MCPProtocolBridge()

        mcp_result = {"content": [{"text": "Some other response format"}]}
        endpoint = "/api/other/generic"  # Use a non-specific endpoint for generic response

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        assert response["success"] is True
        assert response["result"] == "Some other response format"

    def test_mcp_to_http_response_unsupported_endpoint(self):
        """Test MCP to HTTP conversion for unsupported endpoint."""
        bridge = MCPProtocolBridge()

        mcp_result = {"content": [{"text": "test"}]}
        endpoint = "/unsupported/endpoint"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        # Should use generic response format
        assert response["success"] is True
        assert response["result"] == "test"

    def test_mcp_to_http_response_exception_handling(self):
        """Test MCP to HTTP conversion with resilient JSON handling."""
        bridge = MCPProtocolBridge()

        # Invalid JSON should fall back to default response structure
        mcp_result = {"content": [{"text": "PromptCraft MCP Bridge Result: {"}]}  # Invalid JSON
        endpoint = "/api/promptcraft/route/analyze"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        # Should be resilient and return a valid response with defaults
        assert response["success"] is True
        assert "analysis" in response
        assert "recommendations" in response
        assert response["analysis"]["task_type"] == "general"

    def test_format_route_analysis_response_success(self):
        """Test formatting route analysis response for success case."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "success": True,
            "analysis": {
                "task_type": "coding",
                "complexity_score": 0.8,
                "complexity_level": "high",
                "indicators": ["technical_task", "long_prompt"],
                "reasoning": "Complex coding task",
            },
            "recommendations": {
                "primary_model": "claude-3-5-sonnet-20241022",
                "alternative_models": ["gpt-4-turbo", "deepseek-coder"],
                "estimated_cost": 0.12,
                "confidence": 0.92,
            },
            "processing_time": 1.8,
            "bridge_version": "1.0.0",
        }

        response = bridge._format_route_analysis_response(mcp_result)

        assert response["success"] is True
        assert response["analysis"]["complexity_score"] == 0.8
        assert response["recommendations"]["confidence"] == 0.92
        assert response["bridge_version"] == "1.0.0"

    def test_format_route_analysis_response_failure(self):
        """Test formatting route analysis response for failure case."""
        bridge = MCPProtocolBridge()

        mcp_result = {"success": False, "error": "Invalid prompt format", "processing_time": 0.05}

        response = bridge._format_route_analysis_response(mcp_result)

        assert response["success"] is False
        assert response["error"] == "Invalid prompt format"
        assert response["processing_time"] == 0.05

    def test_format_route_analysis_response_missing_data(self):
        """Test formatting route analysis response with missing data."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "success": True,
            # Missing analysis and recommendations
        }

        response = bridge._format_route_analysis_response(mcp_result)

        assert response["success"] is True
        assert response["analysis"]["complexity_score"] == 0.5  # Default value
        assert response["recommendations"]["primary_model"] == "claude-3-5-sonnet-20241022"

    def test_format_route_analysis_response_exception(self):
        """Test formatting route analysis response with exception."""
        bridge = MCPProtocolBridge()

        # Force exception by passing invalid type
        mcp_result = "invalid type"

        response = bridge._format_route_analysis_response(mcp_result)

        assert response["success"] is False
        assert "error" in response

    def test_format_smart_execution_response_success(self):
        """Test formatting smart execution response for success case."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "success": True,
            "response": {
                "content": "Generated Python code",
                "model_used": "claude-3-5-sonnet",
                "reasoning": "Code generation analysis",
            },
            "execution_metadata": {
                "channel": "beta",
                "cost_optimization": False,
                "processing_time": 3.2,
                "estimated_cost": 0.15,
            },
            "bridge_version": "1.0.0",
        }

        response = bridge._format_smart_execution_response(mcp_result)

        assert response["success"] is True
        assert response["result"]["content"] == "Generated Python code"
        assert response["execution_metadata"]["estimated_cost"] == 0.15
        assert response["bridge_version"] == "1.0.0"

    def test_format_smart_execution_response_failure(self):
        """Test formatting smart execution response for failure case."""
        bridge = MCPProtocolBridge()

        mcp_result = {"success": False, "error": "Model quota exceeded", "processing_time": 0.1}

        response = bridge._format_smart_execution_response(mcp_result)

        assert response["success"] is False
        assert response["error"] == "Model quota exceeded"

    def test_format_model_list_response_success(self):
        """Test formatting model list response for success case."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "success": True,
            "models": ["claude-3-5-sonnet", "claude-3-haiku", "gpt-4o"],
            "metadata": {"user_tier": "enterprise", "channel": "experimental", "total_models": 3, "format": "api"},
            "processing_time": 0.2,
            "bridge_version": "1.0.0",
        }

        response = bridge._format_model_list_response(mcp_result)

        assert response["success"] is True
        assert len(response["models"]) == 3
        assert response["metadata"]["user_tier"] == "enterprise"
        assert response["bridge_version"] == "1.0.0"

    def test_format_model_list_response_failure(self):
        """Test formatting model list response for failure case."""
        bridge = MCPProtocolBridge()

        mcp_result = {"success": False, "error": "User tier not found", "processing_time": 0.05}

        response = bridge._format_model_list_response(mcp_result)

        assert response["success"] is False
        assert response["error"] == "User tier not found"

    def test_format_generic_response(self):
        """Test generic response formatting."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "success": True,
            "content": "Generic response content",
            "bridge_version": "1.0.0",
            "processing_time": 0.8,
        }

        response = bridge._format_generic_response(mcp_result)

        assert response["success"] is True
        assert response["result"] == "Generic response content"
        assert response["metadata"]["bridge_version"] == "1.0.0"
        assert response["metadata"]["processing_time"] == 0.8

    def test_format_generic_response_no_content(self):
        """Test generic response formatting with no content field."""
        bridge = MCPProtocolBridge()

        mcp_result = {"success": True, "data": "Some data", "processing_time": 0.3}

        response = bridge._format_generic_response(mcp_result)

        assert response["success"] is True
        assert response["result"]["data"] == "Some data"

    def test_validate_http_request_route_analysis(self, sample_route_analysis_request):
        """Test HTTP request validation for route analysis."""
        bridge = MCPProtocolBridge()

        request_data = sample_route_analysis_request.dict()
        endpoint = "/api/promptcraft/route/analyze"

        # Should not raise exception
        result = bridge.validate_http_request(endpoint, request_data)
        assert result is True

    def test_validate_http_request_smart_execution(self, sample_smart_execution_request):
        """Test HTTP request validation for smart execution."""
        bridge = MCPProtocolBridge()

        request_data = sample_smart_execution_request.dict()
        endpoint = "/api/promptcraft/execute/smart"

        result = bridge.validate_http_request(endpoint, request_data)
        assert result is True

    def test_validate_http_request_model_list(self, sample_model_list_request):
        """Test HTTP request validation for model list."""
        bridge = MCPProtocolBridge()

        request_data = sample_model_list_request.dict()
        endpoint = "/api/promptcraft/models/available"

        result = bridge.validate_http_request(endpoint, request_data)
        assert result is True

    def test_validate_http_request_invalid_data(self):
        """Test HTTP request validation with invalid data."""
        bridge = MCPProtocolBridge()

        invalid_data = {"prompt": "test"}  # Missing required fields
        endpoint = "/api/promptcraft/route/analyze"

        with pytest.raises(ValidationError):
            bridge.validate_http_request(endpoint, invalid_data)

    def test_validate_http_request_unknown_endpoint(self):
        """Test HTTP request validation for unknown endpoint."""
        bridge = MCPProtocolBridge()

        with pytest.raises(ValueError, match="Unknown endpoint"):
            bridge.validate_http_request("/unknown/endpoint", {})

    def test_get_supported_endpoints(self):
        """Test getting supported endpoints."""
        bridge = MCPProtocolBridge()

        endpoints = bridge.get_supported_endpoints()

        assert len(endpoints) == 3
        assert "/api/promptcraft/route/analyze" in endpoints
        assert "/api/promptcraft/execute/smart" in endpoints
        assert "/api/promptcraft/models/available" in endpoints

    def test_get_endpoint_description_valid(self):
        """Test getting description for valid endpoints."""
        bridge = MCPProtocolBridge()

        description = bridge.get_endpoint_description("/api/promptcraft/route/analyze")
        assert "Analyze prompt complexity" in description

        description = bridge.get_endpoint_description("/api/promptcraft/execute/smart")
        assert "Execute prompt with optimal" in description

        description = bridge.get_endpoint_description("/api/promptcraft/models/available")
        assert "Get list of available models" in description

    def test_get_endpoint_description_invalid(self):
        """Test getting description for invalid endpoint."""
        bridge = MCPProtocolBridge()

        description = bridge.get_endpoint_description("/unknown/endpoint")
        assert description is None


class TestProtocolBridgeEdgeCases:
    """Test edge cases and error conditions for protocol bridge."""

    def test_mcp_to_http_response_deeply_nested_json(self):
        """Test MCP response with deeply nested JSON content gets parsed and formatted properly."""
        bridge = MCPProtocolBridge()

        complex_data = {
            "success": True,
            "analysis": {"task_type": "custom", "complexity_score": 0.8},
            "recommendations": {"primary_model": "test-model"},
        }

        mcp_result = {"content": [{"text": "PromptCraft MCP Bridge Result: " + json.dumps(complex_data)}]}
        endpoint = "/api/promptcraft/route/analyze"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        assert response["success"] is True
        assert response["analysis"]["task_type"] == "custom"
        assert response["analysis"]["complexity_score"] == 0.8
        assert response["recommendations"]["primary_model"] == "test-model"

    def test_http_to_mcp_request_with_optional_fields(self):
        """Test HTTP to MCP conversion with optional fields."""
        bridge = MCPProtocolBridge()

        # Route analysis with optional task_type
        minimal_data = {
            "prompt": "Test prompt",
            "user_tier": "basic",
            # task_type is optional and should default
        }
        endpoint = "/api/promptcraft/route/analyze"

        mcp_call = bridge.http_to_mcp_request(endpoint, minimal_data)

        assert mcp_call.arguments["prompt"] == "Test prompt"
        assert mcp_call.arguments["user_tier"] == "basic"
        assert "task_type" in mcp_call.arguments

    def test_mcp_to_http_response_malformed_bridge_result(self):
        """Test MCP response with malformed bridge result format falls back gracefully."""
        bridge = MCPProtocolBridge()

        mcp_result = {"content": [{"text": "PromptCraft MCP Bridge Result: {incomplete json"}]}
        endpoint = "/api/promptcraft/route/analyze"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        assert response["success"] is True
        assert "analysis" in response
        assert "recommendations" in response
        assert response["analysis"]["task_type"] == "general"

    def test_response_formatting_with_missing_optional_fields(self):
        """Test response formatting when optional fields are missing."""
        bridge = MCPProtocolBridge()

        # Minimal MCP result for route analysis
        mcp_result = {
            "success": True,
            # Missing analysis and recommendations
        }

        response = bridge._format_route_analysis_response(mcp_result)

        assert response["success"] is True
        assert "analysis" in response
        assert "recommendations" in response
        # Should have default values

    def test_multiple_content_entries_in_mcp_result(self):
        """Test MCP result with multiple content entries."""
        bridge = MCPProtocolBridge()

        mcp_result = {
            "content": [{"text": "First entry"}, {"text": 'PromptCraft MCP Bridge Result: {"success": true}'}],
        }
        endpoint = "/api/promptcraft/route/analyze"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        # Should process the first entry
        assert response["success"] is True

    @patch("json.loads")
    def test_json_parsing_exception_handling(self, mock_json_loads):
        """Test exception handling during JSON parsing falls back gracefully."""
        bridge = MCPProtocolBridge()

        mock_json_loads.side_effect = json.JSONDecodeError("Invalid JSON", "doc", 0)

        mcp_result = {"content": [{"text": 'PromptCraft MCP Bridge Result: {"test": "data"}'}]}
        endpoint = "/api/promptcraft/route/analyze"

        response = bridge.mcp_to_http_response(endpoint, mcp_result)

        # Should fall back to structured response with defaults
        assert response["success"] is True
        assert "analysis" in response
        assert "recommendations" in response

    def test_bridge_tool_name_customization(self):
        """Test that bridge tool name can be customized."""
        bridge = MCPProtocolBridge()
        original_name = bridge.bridge_tool_name

        bridge.bridge_tool_name = "custom_bridge_tool"

        endpoint = "/api/promptcraft/route/analyze"
        request_data = {"prompt": "test", "user_tier": "basic"}

        mcp_call = bridge.http_to_mcp_request(endpoint, request_data)

        assert mcp_call.name == "custom_bridge_tool"

        # Restore original name
        bridge.bridge_tool_name = original_name
