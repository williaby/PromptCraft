"""
Data models for PromptCraft MCP Client Library

Defines request/response models for MCP stdio communication with zen-mcp-server.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MCPToolCall(BaseModel):
    """Model for MCP tool call requests."""

    name: str = Field(..., description="Tool name to call")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class MCPToolResult(BaseModel):
    """Model for MCP tool call results."""

    content: list[dict[str, Any]] = Field(default_factory=list, description="Tool response content")
    isError: bool = Field(False, description="Whether the result is an error")


class RouteAnalysisRequest(BaseModel):
    """Request for route analysis via MCP."""

    prompt: str = Field(..., description="The prompt to analyze")
    user_tier: str = Field(..., description="User tier: free|limited|full|premium|admin")
    task_type: str | None = Field(None, description="Optional task type hint")


class SmartExecutionRequest(BaseModel):
    """Request for smart execution via MCP."""

    prompt: str = Field(..., description="The enhanced prompt from Journey 1")
    user_tier: str = Field(..., description="User tier: free|limited|full|premium|admin")
    channel: str = Field("stable", description="Model channel: stable|experimental")
    cost_optimization: bool = Field(True, description="Enable cost optimization")
    include_reasoning: bool = Field(True, description="Include reasoning in response")


class ModelListRequest(BaseModel):
    """Request for available models via MCP."""

    user_tier: str | None = Field(None, description="Filter by user tier")
    channel: str = Field("stable", description="Model channel: stable|experimental")
    include_metadata: bool = Field(True, description="Include detailed metadata")
    format: str = Field("ui", description="Response format: ui|api")


class AnalysisResult(BaseModel):
    """Result from route analysis."""

    success: bool = Field(..., description="Whether analysis was successful")
    analysis: dict[str, Any] | None = Field(None, description="Analysis details")
    recommendations: dict[str, Any] | None = Field(None, description="Model recommendations")
    processing_time: float = Field(..., description="Processing time in seconds")
    error: str | None = Field(None, description="Error message if failed")


class ExecutionResult(BaseModel):
    """Result from smart execution."""

    success: bool = Field(..., description="Whether execution was successful")
    response: dict[str, Any] | None = Field(None, description="Execution response")
    execution_metadata: dict[str, Any] | None = Field(None, description="Execution metadata")
    processing_time: float = Field(..., description="Processing time in seconds")
    error: str | None = Field(None, description="Error message if failed")


class ModelListResult(BaseModel):
    """Result from model listing."""

    success: bool = Field(..., description="Whether listing was successful")
    models: list[dict[str, Any]] | None = Field(None, description="Available models")
    metadata: dict[str, Any] | None = Field(None, description="Response metadata")
    processing_time: float = Field(..., description="Processing time in seconds")
    error: str | None = Field(None, description="Error message if failed")


class MCPConnectionConfig(BaseModel):
    """Configuration for MCP stdio connection."""

    server_path: str = Field(..., description="Path to zen-mcp-server executable")
    env_vars: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    timeout: float = Field(30.0, description="Connection timeout in seconds")
    max_retries: int = Field(3, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")


class MCPConnectionStatus(BaseModel):
    """Status of MCP stdio connection."""

    connected: bool = Field(..., description="Whether connection is active")
    process_id: int | None = Field(None, description="Server process ID")
    uptime: float | None = Field(None, description="Connection uptime in seconds")
    last_activity: datetime | None = Field(None, description="Last activity timestamp")
    error_count: int = Field(0, description="Number of errors encountered")


class MCPHealthCheck(BaseModel):
    """Health check result for MCP connection."""

    healthy: bool = Field(..., description="Whether connection is healthy")
    latency_ms: float | None = Field(None, description="Connection latency in milliseconds")
    server_version: str | None = Field(None, description="Server version")
    available_tools: list[str] | None = Field(None, description="Available tools")
    error: str | None = Field(None, description="Error message if unhealthy")


class FallbackConfig(BaseModel):
    """Configuration for HTTP fallback behavior."""

    enabled: bool = Field(True, description="Whether HTTP fallback is enabled")
    http_base_url: str = Field("http://localhost:8000", description="Base URL for HTTP API")
    fallback_timeout: float = Field(10.0, description="HTTP request timeout")
    circuit_breaker_threshold: int = Field(5, description="Error threshold for circuit breaker")
    circuit_breaker_reset_time: float = Field(60.0, description="Circuit breaker reset time in seconds")


class BridgeMetrics(BaseModel):
    """Metrics for MCP bridge performance."""

    total_requests: int = Field(0, description="Total number of requests")
    successful_requests: int = Field(0, description="Number of successful requests")
    failed_requests: int = Field(0, description="Number of failed requests")
    mcp_requests: int = Field(0, description="Number of MCP requests")
    http_fallback_requests: int = Field(0, description="Number of HTTP fallback requests")
    average_latency_ms: float = Field(0.0, description="Average request latency in milliseconds")
    last_request_time: datetime | None = Field(None, description="Timestamp of last request")
    uptime: float = Field(0.0, description="Bridge uptime in seconds")
