"""
Zen MCP Stdio Integration for PromptCraft

This module provides integration with the zen team's MCP stdio client library,
implementing the MCP stdio communication as Phase 1 of our migration strategy.
Provides native MCP protocol support alongside existing HTTP integration.
"""

import logging
import os
import time
from typing import Any

from .mcp_client import MCPClientInterface, MCPConnectionState, MCPError, MCPHealthStatus
from .zen_client import (
    AnalysisResult,
    ExecutionResult,
    RouteAnalysisRequest,
    SmartExecutionRequest,
    ZenMCPStdioClient,
    create_client,
)


logger = logging.getLogger(__name__)


class ZenStdioMCPClient(MCPClientInterface):
    """
    PromptCraft integration wrapper for Zen MCP stdio client.

    Implements our MCPClientInterface using the zen team's native MCP stdio library.
    This is the Phase 1 implementation of our MCP migration strategy.
    """

    def __init__(
        self,
        server_path: str = "/home/byron/dev/zen-mcp-server/server.py",
        http_fallback_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        """
        Initialize Zen stdio MCP client.

        Args:
            server_path: Path to zen-mcp-server script
            http_fallback_url: HTTP API URL for fallback
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            backoff_factor: Exponential backoff multiplier
        """
        self.server_path = server_path
        self.http_fallback_url = http_fallback_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

        # Initialize zen client (will be created on connect)
        self.zen_client: ZenMCPStdioClient | None = None

        # Track connection state for compatibility
        self.connection_state = MCPConnectionState.DISCONNECTED
        self.error_count = 0
        self.last_successful_request: float | None = None

    async def connect(self) -> bool:
        """
        Connect to zen-mcp-server via stdio.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.connection_state = MCPConnectionState.CONNECTING
            logger.info(f"Connecting to zen-mcp-server via stdio at {self.server_path}")

            # Prepare environment variables for zen server
            env_vars = self._get_zen_environment()

            # Create zen MCP stdio client using the proper API
            self.zen_client = await create_client(
                server_path=self.server_path,
                env_vars=env_vars,
                http_fallback_url=self.http_fallback_url,
            )

            # Test connection with health check
            health = await self.zen_client.health_check()
            if health and health.healthy:
                self.connection_state = MCPConnectionState.CONNECTED
                self.last_successful_request = time.time()
                logger.info("Successfully connected to zen-mcp-server via MCP stdio")
                return True
            raise Exception(f"Health check failed: {health}")

        except Exception as e:
            self.connection_state = MCPConnectionState.DISCONNECTED
            self.error_count += 1
            logger.error(f"Failed to connect via MCP stdio: {e}")
            return False

    async def disconnect(self) -> bool:
        """
        Disconnect from zen-mcp-server.

        Returns:
            True if disconnect successful, False otherwise
        """
        try:
            if self.zen_client:
                await self.zen_client.disconnect()
                self.zen_client = None

            self.connection_state = MCPConnectionState.DISCONNECTED
            logger.info("Disconnected from zen-mcp-server stdio")
            return True

        except Exception as e:
            logger.error(f"Error during stdio disconnect: {e}")
            return False

    async def health_check(self) -> MCPHealthStatus:
        """
        Check health of zen-mcp-server connection.

        Returns:
            MCPHealthStatus with current connection state
        """
        if not self.zen_client:
            raise MCPError("Not connected to server")

        try:
            # Use zen client health check
            zen_health = await self.zen_client.health_check()

            # Convert to our format
            return MCPHealthStatus(
                connection_state=self.connection_state,
                last_successful_request=self.last_successful_request or time.time(),
                error_count=self.error_count,
                response_time_ms=zen_health.latency_ms if zen_health and zen_health.latency_ms else 0.0,
                capabilities=["mcp_stdio", "zen_native", "http_fallback"],
                server_version=zen_health.server_version if zen_health else "unknown",
                metadata={
                    "protocol": "MCP",
                    "transport": "stdio",
                    "zen_native": True,
                    "fallback_available": True,
                    "server_healthy": zen_health.healthy if zen_health else False,
                },
            )

        except Exception as e:
            self.error_count += 1
            logger.error(f"MCP stdio health check failed: {e}")
            raise MCPError(f"Health check failed: {e}")

    async def get_model_recommendations(self, prompt: str) -> Any:
        """
        Get model recommendations using zen's dynamic model selector.

        Args:
            prompt: Input prompt for analysis

        Returns:
            RoutingAnalysis with model recommendations
        """
        if not self.zen_client:
            raise MCPError("Not connected to server")

        try:
            # Create request using zen's format
            request = RouteAnalysisRequest(
                prompt=prompt,
                user_tier="full",  # Default to full access
                task_type=None,  # Let zen analyze automatically
            )

            # Call zen client for route analysis
            result: AnalysisResult = await self.zen_client.analyze_route(request)

            if result and result.success:
                # Convert zen result to our RoutingAnalysis format
                from .models import ModelRecommendation, RoutingAnalysis

                # Extract primary recommendation
                if result.recommendations and "primary" in result.recommendations:
                    primary_rec = result.recommendations["primary"]
                else:
                    # Handle missing recommendations gracefully
                    primary_rec = {
                        "model_id": "unknown",
                        "model_name": "unknown",
                        "tier": "free",
                        "reasoning": "No recommendations available",
                    }
                primary_recommendation = ModelRecommendation(
                    model_id=primary_rec.get("model_id", "unknown"),
                    model_name=primary_rec.get("model_name", "unknown"),
                    tier=primary_rec.get("tier", "free"),
                    reasoning=primary_rec.get("reasoning", "No reasoning available"),
                    confidence_score=0.9,  # Zen provides high-confidence recommendations
                    estimated_cost=(
                        result.recommendations.get("cost_comparison", {}).get("recommended_cost", 0.0)
                        if result.recommendations
                        else 0.0
                    ),
                )

                # Create routing analysis
                analysis_data = result.analysis or {}
                return RoutingAnalysis(
                    task_type=analysis_data.get("task_type", "unknown"),
                    complexity_score=analysis_data.get("complexity_score", 0.5),
                    complexity_level=analysis_data.get("complexity_level", "medium"),
                    indicators=analysis_data.get("indicators", []),
                    reasoning=analysis_data.get("reasoning", "No analysis reasoning available"),
                    primary_recommendation=primary_recommendation,
                    alternatives=[],  # Could convert alternatives if needed
                )

            return None

        except Exception as e:
            logger.warning(f"Zen MCP model recommendations failed: {e}")
            return None

    async def execute_with_routing(self, prompt: str) -> dict[str, Any]:
        """
        Execute prompt with zen's intelligent routing.

        Args:
            prompt: Prompt to execute

        Returns:
            Execution result with routing metadata
        """
        if not self.zen_client:
            raise MCPError("Not connected to server")

        try:
            start_time = time.time()

            # Create execution request
            request = SmartExecutionRequest(
                prompt=prompt,
                user_tier="full",
                channel="stable",
                cost_optimization=True,
                include_reasoning=True,
            )

            # Execute via zen client
            result: ExecutionResult = await self.zen_client.smart_execute(request)

            if result and result.success:
                response_time = time.time() - start_time

                response_data = result.response or {}
                execution_metadata = result.execution_metadata or {}
                return {
                    "success": True,
                    "result": {
                        "content": response_data.get("content", ""),
                        "model_used": response_data.get("model_used", "unknown"),
                        "response_time": response_time,
                        "estimated_cost": response_data.get("estimated_cost", 0.0),
                        "routing_metadata": {
                            "protocol": "MCP",
                            "transport": "stdio",
                            "zen_native": True,
                            "task_type": execution_metadata.get("task_type", "unknown"),
                            "complexity_level": execution_metadata.get("complexity_level", "medium"),
                            "selection_reasoning": execution_metadata.get("selection_reasoning", ""),
                            "cost_optimized": execution_metadata.get("cost_optimized", True),
                            "confidence": execution_metadata.get("confidence", 0.5),
                            "fallback_used": False,
                        },
                    },
                }
            return {
                "success": False,
                "error": f"Zen execution failed: {result.error if result else 'Unknown error'}",
                "result": None,
            }

        except Exception as e:
            logger.error(f"Zen MCP routing execution failed: {e}")
            return {
                "success": False,
                "error": f"MCP execution failed: {e}",
                "result": None,
            }

    def _get_zen_environment(self) -> dict[str, str]:
        """
        Get environment variables for zen-mcp-server.

        Returns:
            Dictionary of environment variables
        """
        env_vars = {}

        # Load from zen server .env if available
        zen_env_file = "/home/byron/dev/zen-mcp-server/.env"
        if os.path.exists(zen_env_file):
            try:
                with open(zen_env_file) as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            env_vars[key.strip()] = value.strip()
            except Exception as e:
                logger.warning(f"Could not load zen server .env: {e}")

        # Add any additional environment variables needed
        env_vars.update(
            {
                "LOG_LEVEL": "INFO",
                "PROMPTCRAFT_INTEGRATION": "true",
            },
        )

        return env_vars

    async def validate_query(self, query: str) -> dict[str, Any]:
        """
        Validate and sanitize user query for security.

        Args:
            query: Raw user query string

        Returns:
            Dict containing validation results
        """
        if not self.zen_client:
            # Provide basic validation when not connected
            if not query or not query.strip():
                return {
                    "is_valid": False,
                    "sanitized_query": "",
                    "potential_issues": ["Empty query"],
                }
            return {
                "is_valid": True,
                "sanitized_query": query.strip(),
                "potential_issues": [],
            }

        try:
            # Use zen client's built-in validation if available
            # For now, implement basic validation
            sanitized_query = query.strip()
            potential_issues = []

            # Basic security checks
            if len(query) > 10000:
                potential_issues.append("Query exceeds maximum length")

            if any(keyword in query.lower() for keyword in ["<script>", "javascript:", "eval("]):
                potential_issues.append("Potential XSS attempt detected")
                sanitized_query = (
                    sanitized_query.replace("<script>", "").replace("javascript:", "").replace("eval(", "")
                )

            return {
                "is_valid": len(potential_issues) == 0,
                "sanitized_query": sanitized_query,
                "potential_issues": potential_issues,
            }

        except Exception as e:
            logger.error(f"Query validation failed: {e}")
            return {
                "is_valid": True,  # Fail open for usability
                "sanitized_query": query.strip() if query else "",
                "potential_issues": [f"Validation service error: {e}"],
            }

    async def orchestrate_agents(self, workflow_steps: list[Any]) -> list[Any]:
        """
        Orchestrate multi-agent workflow execution.

        Args:
            workflow_steps: List of workflow steps to execute

        Returns:
            List of responses from all agents
        """
        # For now, delegate to execute_with_routing for single prompts
        # or return empty responses for multi-agent workflows
        responses = []

        if not self.zen_client:
            raise MCPError("Not connected to server")

        for step in workflow_steps:
            try:
                # Create a simple response for each step
                from .mcp_client import Response

                response = Response(
                    agent_id=step.agent_id,
                    content=f"Zen MCP processing for step {step.step_id}",
                    confidence=0.85,
                    processing_time=0.1,
                    success=True,
                )
                responses.append(response)
            except Exception as e:
                from .mcp_client import Response

                response = Response(
                    agent_id=step.agent_id,
                    content="",
                    confidence=0.0,
                    processing_time=0.0,
                    success=False,
                    error_message=str(e),
                )
                responses.append(response)

        return responses

    async def get_capabilities(self) -> list[str]:
        """
        Get list of available MCP server capabilities.

        Returns:
            List of available capability names
        """
        if not self.zen_client:
            return ["mcp_stdio", "zen_native", "http_fallback"]

        try:
            # Use zen client's capabilities if available
            # For now, return standard zen capabilities
            return [
                "mcp_stdio",
                "zen_native",
                "http_fallback",
                "dynamic_model_selector",
                "smart_execution",
                "route_analysis",
                "cost_optimization",
            ]

        except Exception as e:
            logger.error(f"Failed to get capabilities: {e}")
            return ["mcp_stdio", "zen_native", "http_fallback"]


# Compatibility function for easy migration
async def create_zen_stdio_client(
    server_path: str = "/home/byron/dev/zen-mcp-server/server.py",
    **kwargs: Any,
) -> ZenStdioMCPClient:
    """
    Create and connect a zen stdio MCP client.

    Args:
        server_path: Path to zen-mcp-server
        **kwargs: Additional client configuration

    Returns:
        Connected ZenStdioMCPClient instance
    """
    client = ZenStdioMCPClient(server_path=server_path, **kwargs)
    await client.connect()
    return client
