"""
Data models for MCP Integration.

This module defines the data models used across the MCP integration
system, including workflow results, execution steps, and agent responses.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
from typing import Any


@dataclass
class WorkflowResult:
    """
    Result of a workflow step execution.

    Represents the outcome of executing a single step in a workflow,
    including success status, response content, and metadata.
    """

    step_id: str
    success: bool
    content: str
    confidence: float = 0.0
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    execution_time: float | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "step_id": self.step_id,
            "success": self.success,
            "content": self.content,
            "confidence": self.confidence,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowResult":
        """Create from dictionary representation."""
        timestamp = datetime.now(UTC)
        if data.get("timestamp"):
            timestamp = datetime.fromisoformat(data["timestamp"])

        return cls(
            step_id=data["step_id"],
            success=data["success"],
            content=data["content"],
            confidence=data.get("confidence", 0.0),
            error_message=data.get("error_message"),
            metadata=data.get("metadata", {}),
            execution_time=data.get("execution_time"),
            timestamp=timestamp,
        )

    def to_json(self) -> str:
        """Convert to JSON representation."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class WorkflowStep:
    """
    Definition of a workflow step.

    Represents a single step in a multi-step workflow, including
    input data, configuration, and execution parameters.
    """

    step_id: str
    agent_id: str
    input_data: dict[str, Any]
    timeout_seconds: float = 30.0
    retry_count: int = 3
    dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "input_data": self.input_data,
            "timeout_seconds": self.timeout_seconds,
            "retry_count": self.retry_count,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowStep":
        """Create from dictionary representation."""
        return cls(
            step_id=data["step_id"],
            agent_id=data["agent_id"],
            input_data=data["input_data"],
            timeout_seconds=data.get("timeout_seconds", 30.0),
            retry_count=data.get("retry_count", 3),
            dependencies=data.get("dependencies", []),
        )


@dataclass
class ModelMetadata:
    """
    Metadata for an AI model.

    Contains information about model capabilities, costs, and characteristics
    used for intelligent model selection and routing.
    """

    model_id: str
    name: str
    provider: str
    tier: str
    cost_per_token: float = 0.0
    specialization: str | None = None
    context_window: int = 4096
    max_tokens: int = 4096
    status: str = "active"
    channel: str = "stable"
    humaneval_score: float | None = None
    capabilities: list[str] = field(default_factory=list)

    @property
    def display_name(self) -> str:
        """Get formatted display name for UI."""
        emoji = "🆓" if self.cost_per_token == 0.0 else "💰"
        specialization_text = f" - {self.specialization.upper()}" if self.specialization else ""
        score_text = f" (Score: {self.humaneval_score})" if self.humaneval_score else ""

        return f"{emoji} {self.name}{specialization_text}{score_text}"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "model_id": self.model_id,
            "name": self.name,
            "provider": self.provider,
            "tier": self.tier,
            "cost_per_token": self.cost_per_token,
            "specialization": self.specialization,
            "context_window": self.context_window,
            "max_tokens": self.max_tokens,
            "status": self.status,
            "channel": self.channel,
            "humaneval_score": self.humaneval_score,
            "capabilities": self.capabilities,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ModelMetadata":
        """Create from dictionary representation."""
        return cls(
            model_id=data["model_id"],
            name=data["name"],
            provider=data["provider"],
            tier=data["tier"],
            cost_per_token=data.get("cost_per_token", 0.0),
            specialization=data.get("specialization"),
            context_window=data.get("context_window", 4096),
            max_tokens=data.get("max_tokens", 4096),
            status=data.get("status", "active"),
            channel=data.get("channel", "stable"),
            humaneval_score=data.get("humaneval_score"),
            capabilities=data.get("capabilities", []),
        )


@dataclass
class ModelRecommendation:
    """
    AI model recommendation with reasoning.

    Contains a recommended model along with the reasoning for the selection
    and alternative options.
    """

    model_id: str
    model_name: str
    tier: str
    reasoning: str
    confidence_score: float = 0.0
    estimated_cost: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "tier": self.tier,
            "reasoning": self.reasoning,
            "confidence_score": self.confidence_score,
            "estimated_cost": self.estimated_cost,
        }


@dataclass
class RoutingAnalysis:
    """
    Analysis result for routing decisions.

    Contains task analysis, complexity assessment, and model recommendations
    for intelligent routing decisions.
    """

    task_type: str
    complexity_score: float
    complexity_level: str
    indicators: list[str]
    reasoning: str
    primary_recommendation: ModelRecommendation
    alternatives: list[ModelRecommendation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "task_type": self.task_type,
            "complexity_score": self.complexity_score,
            "complexity_level": self.complexity_level,
            "indicators": self.indicators,
            "reasoning": self.reasoning,
            "primary_recommendation": self.primary_recommendation.to_dict(),
            "alternatives": [alt.to_dict() for alt in self.alternatives],
        }


@dataclass
class ExecutionResult:
    """
    Result of executing a request through the MCP system.

    Contains the response content, metadata about execution,
    and routing information.
    """

    success: bool
    content: str
    model_used: str
    response_time: float
    estimated_cost: float
    routing_analysis: RoutingAnalysis | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "success": self.success,
            "content": self.content,
            "model_used": self.model_used,
            "response_time": self.response_time,
            "estimated_cost": self.estimated_cost,
            "routing_analysis": self.routing_analysis.to_dict() if self.routing_analysis else None,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


# Model channel types
class ModelChannel:
    """Model channel constants."""

    STABLE = "stable"
    EXPERIMENTAL = "experimental"


# Model tier constants
class ModelTier:
    """Model tier constants."""

    FREE_CHAMPION = "free_champion"
    VALUE_TIER = "value_tier"
    OPEN_SOURCE = "open_source"
    HIGH_PERF = "high_perf"
    PREMIUM = "premium"


# Task type constants
class TaskType:
    """Task type constants."""

    CODE_GENERATION = "code_generation"
    DEBUGGING = "debugging"
    GENERAL = "general"
    ANALYSIS = "analysis"
    WRITING = "writing"
    MATH = "math"
    REASONING = "reasoning"


# MCP Connection Models for Smart Discovery

@dataclass
class MCPConnectionConfig:
    """Configuration for MCP server connection."""
    server_path: str
    env_vars: dict[str, str] = field(default_factory=dict)
    timeout: float = 30.0


@dataclass 
class MCPConnectionStatus:
    """Status of an MCP server connection."""
    connected: bool
    server_name: str
    url: str | None = None
    error_message: str | None = None
    last_check: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MCPHealthCheck:
    """Health check result for MCP server."""
    healthy: bool
    response_time: float | None = None
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


__all__ = [
    "ExecutionResult", 
    "MCPConnectionConfig",
    "MCPConnectionStatus",
    "MCPHealthCheck",
    "ModelChannel",
    "ModelMetadata",
    "ModelRecommendation",
    "ModelTier",
    "RoutingAnalysis",
    "TaskType",
    "WorkflowResult",
    "WorkflowStep",
]
