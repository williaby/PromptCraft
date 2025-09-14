"""
Protocol Bridge for PromptCraft MCP Client

Translates between HTTP API requests and MCP tool calls, maintaining compatibility
while providing native MCP integration.
"""

import json
import logging
from typing import Any

from .models import (
    MCPToolCall,
    ModelListRequest,
    RouteAnalysisRequest,
    SmartExecutionRequest,
)


logger = logging.getLogger(__name__)


class MCPProtocolBridge:
    """
    Bridge between HTTP API requests and MCP tool calls.

    This class handles the translation between PromptCraft's HTTP API format
    and the MCP protocol used by zen-mcp-server.
    """

    def __init__(self) -> None:
        self.bridge_tool_name = "promptcraft_mcp_bridge"

    def http_to_mcp_request(self, endpoint: str, http_request: dict[str, Any]) -> MCPToolCall:
        """
        Convert HTTP API request to MCP tool call.

        Args:
            endpoint: HTTP endpoint path (e.g., "/api/promptcraft/route/analyze")
            http_request: HTTP request body as dict

        Returns:
            MCPToolCall: MCP tool call with translated parameters
        """
        try:
            # Determine action based on endpoint
            if endpoint.endswith("/route/analyze"):
                action = "analyze_route"
                # Validate and extract parameters for route analysis
                request = RouteAnalysisRequest(**http_request)
                arguments = {
                    "action": action,
                    "prompt": request.prompt,
                    "user_tier": request.user_tier,
                    "task_type": request.task_type,
                    "model": "flash",  # Default model for analysis
                }

            elif endpoint.endswith("/execute/smart"):
                action = "smart_execute"
                # Validate and extract parameters for smart execution
                smart_request = SmartExecutionRequest(**http_request)
                arguments = {
                    "action": action,
                    "prompt": smart_request.prompt,
                    "user_tier": smart_request.user_tier,
                    "channel": smart_request.channel,
                    "cost_optimization": str(smart_request.cost_optimization).lower(),
                    "include_reasoning": str(smart_request.include_reasoning).lower(),
                    "model": "auto",  # Let the bridge decide
                }

            elif endpoint.endswith("/models/available"):
                action = "list_models"
                # Validate and extract parameters for model listing
                models_request = ModelListRequest(**http_request)
                arguments = {
                    "action": action,
                    "user_tier": models_request.user_tier,
                    "channel": models_request.channel,
                    "include_metadata": str(models_request.include_metadata).lower(),
                    "format": models_request.format,
                    "model": "flash",  # Fast model for listing
                }

            else:
                raise ValueError(f"Unsupported endpoint: {endpoint}")

            logger.debug(f"Translated HTTP request to MCP: {action}")
            return MCPToolCall(name=self.bridge_tool_name, arguments=arguments)

        except Exception as e:
            logger.error(f"Failed to translate HTTP request to MCP: {e}")
            raise

    def mcp_to_http_response(self, endpoint: str, mcp_result: dict[str, Any]) -> dict[str, Any]:
        """
        Convert MCP tool result to HTTP API response.

        Args:
            endpoint: Original HTTP endpoint path
            mcp_result: MCP tool result as dict

        Returns:
            Dict[str, Any]: HTTP response in expected format
        """
        try:
            # Extract the actual result from MCP response
            # MCP results come wrapped in content array
            if isinstance(mcp_result, dict) and "content" in mcp_result:
                content_list = mcp_result["content"]
                if content_list and isinstance(content_list, list) and len(content_list) > 0:
                    # Extract text content and parse as JSON
                    # json imported at top level

                    text_content = content_list[0].get("text", "")
                    if "PromptCraft MCP Bridge Result:" in text_content:
                        # Extract JSON part after the header
                        json_start = text_content.find("{")
                        if json_start != -1:
                            json_content = text_content[json_start:]
                            try:
                                parsed_result = json.loads(json_content)
                            except json.JSONDecodeError:
                                # Fallback: use the raw content
                                parsed_result = {"content": text_content, "success": True}
                        else:
                            parsed_result = {"content": text_content, "success": True}
                    else:
                        parsed_result = {"content": text_content, "success": True}
                else:
                    parsed_result = {"error": "Empty MCP response", "success": False}
            else:
                parsed_result = mcp_result

            # Translate based on endpoint
            if endpoint.endswith("/route/analyze"):
                return self._format_route_analysis_response(parsed_result)
            if endpoint.endswith("/execute/smart"):
                return self._format_smart_execution_response(parsed_result)
            if endpoint.endswith("/models/available"):
                return self._format_model_list_response(parsed_result)
            # Generic response format
            return self._format_generic_response(parsed_result)

        except Exception as e:
            logger.error(f"Failed to translate MCP result to HTTP response: {e}")
            return {
                "success": False,
                "error": f"Bridge translation error: {e!s}",
                "raw_mcp_result": mcp_result,
            }

    def _format_route_analysis_response(self, mcp_result: dict[str, Any]) -> dict[str, Any]:
        """Format MCP result as route analysis response."""
        try:
            if not mcp_result.get("success", False):
                return {
                    "success": False,
                    "error": mcp_result.get("error", "Route analysis failed"),
                    "processing_time": mcp_result.get("processing_time", 0.0),
                }

            # Extract analysis and recommendations from MCP result
            analysis = mcp_result.get("analysis", {})
            recommendations = mcp_result.get("recommendations", {})

            return {
                "success": True,
                "analysis": {
                    "task_type": analysis.get("task_type", "general"),
                    "complexity_score": analysis.get("complexity_score", 0.5),
                    "complexity_level": analysis.get("complexity_level", "medium"),
                    "indicators": analysis.get("indicators", []),
                    "reasoning": analysis.get("reasoning", ""),
                },
                "recommendations": {
                    "primary_model": recommendations.get("primary_model", "claude-3-5-sonnet-20241022"),
                    "alternative_models": recommendations.get("alternative_models", []),
                    "estimated_cost": recommendations.get("estimated_cost", 0.01),
                    "confidence": recommendations.get("confidence", 0.85),
                },
                "processing_time": mcp_result.get("processing_time", 0.0),
                "bridge_version": mcp_result.get("bridge_version", "1.0.0"),
            }

        except Exception as e:
            logger.error(f"Error formatting route analysis response: {e}")
            return {"success": False, "error": str(e)}

    def _format_smart_execution_response(self, mcp_result: dict[str, Any]) -> dict[str, Any]:
        """Format MCP result as smart execution response."""
        try:
            if not mcp_result.get("success", False):
                return {
                    "success": False,
                    "error": mcp_result.get("error", "Smart execution failed"),
                    "processing_time": mcp_result.get("processing_time", 0.0),
                }

            # Extract response and metadata from MCP result
            response = mcp_result.get("response", {})
            execution_metadata = mcp_result.get("execution_metadata", {})

            return {
                "success": True,
                "result": {
                    "content": response.get("content", ""),
                    "model_used": response.get("model_used", "unknown"),
                    "reasoning": response.get("reasoning"),
                },
                "execution_metadata": {
                    "channel": execution_metadata.get("channel", "stable"),
                    "cost_optimization": execution_metadata.get("cost_optimization", True),
                    "processing_time": execution_metadata.get("processing_time", 0.0),
                    "estimated_cost": execution_metadata.get("estimated_cost", 0.01),
                },
                "bridge_version": mcp_result.get("bridge_version", "1.0.0"),
            }

        except Exception as e:
            logger.error(f"Error formatting smart execution response: {e}")
            return {"success": False, "error": str(e)}

    def _format_model_list_response(self, mcp_result: dict[str, Any]) -> dict[str, Any]:
        """Format MCP result as model list response."""
        try:
            if not mcp_result.get("success", False):
                return {
                    "success": False,
                    "error": mcp_result.get("error", "Model listing failed"),
                    "processing_time": mcp_result.get("processing_time", 0.0),
                }

            # Extract models and metadata from MCP result
            models = mcp_result.get("models", [])
            metadata = mcp_result.get("metadata", {})

            return {
                "success": True,
                "models": models,
                "metadata": {
                    "user_tier": metadata.get("user_tier"),
                    "channel": metadata.get("channel", "stable"),
                    "total_models": metadata.get("total_models", len(models)),
                    "format": metadata.get("format", "ui"),
                },
                "processing_time": mcp_result.get("processing_time", 0.0),
                "bridge_version": mcp_result.get("bridge_version", "1.0.0"),
            }

        except Exception as e:
            logger.error(f"Error formatting model list response: {e}")
            return {"success": False, "error": str(e)}

    def _format_generic_response(self, mcp_result: dict[str, Any]) -> dict[str, Any]:
        """Format MCP result as generic HTTP response."""
        return {
            "success": mcp_result.get("success", True),
            "result": mcp_result.get("content", mcp_result),
            "metadata": {
                "bridge_version": mcp_result.get("bridge_version", "1.0.0"),
                "processing_time": mcp_result.get("processing_time", 0.0),
            },
        }

    def validate_http_request(self, endpoint: str, request_data: dict[str, Any]) -> bool:
        """
        Validate HTTP request data for the given endpoint.

        Args:
            endpoint: HTTP endpoint path
            request_data: Request data to validate

        Returns:
            bool: True if request is valid, raises exception otherwise
        """
        try:
            if endpoint.endswith("/route/analyze"):
                RouteAnalysisRequest(**request_data)
            elif endpoint.endswith("/execute/smart"):
                SmartExecutionRequest(**request_data)
            elif endpoint.endswith("/models/available"):
                ModelListRequest(**request_data)
            else:
                raise ValueError(f"Unknown endpoint: {endpoint}")

            return True

        except Exception as e:
            logger.error(f"HTTP request validation failed for {endpoint}: {e}")
            raise

    def get_supported_endpoints(self) -> list[str]:
        """Get list of supported HTTP endpoints."""
        return [
            "/api/promptcraft/route/analyze",
            "/api/promptcraft/execute/smart",
            "/api/promptcraft/models/available",
        ]

    def get_endpoint_description(self, endpoint: str) -> str | None:
        """Get description for a supported endpoint."""
        descriptions = {
            "/api/promptcraft/route/analyze": "Analyze prompt complexity and provide model recommendations",
            "/api/promptcraft/execute/smart": "Execute prompt with optimal model routing",
            "/api/promptcraft/models/available": "Get list of available models for user tier",
        }
        return descriptions.get(endpoint)
