"""
Markdown Agent Implementation

Dynamically created agent from markdown definitions.
"""

import logging
from typing import Any

from .base_agent import BaseAgent
from .models import AgentInput, AgentOutput


logger = logging.getLogger(__name__)


class MarkdownAgent(BaseAgent):
    """Agent implementation based on markdown definition."""

    def __init__(
        self,
        agent_id: str,
        definition: str,
        model: str,
        tools: list[str],
        context: str,
        config: dict[str, Any],
    ) -> None:
        """Initialize markdown-based agent.

        Args:
            agent_id: Unique identifier for the agent
            definition: Markdown content defining agent behavior
            model: AI model to use (opus, sonnet, haiku)
            tools: List of available tools
            context: Combined context from various sources
            config: Agent configuration
        """
        # Prepare config dict for BaseAgent
        agent_config = {
            "agent_id": agent_id,
            "model": model,
            "tools": tools,
            **config,
        }

        super().__init__(agent_config)

        self.definition = definition
        self.context = context
        self.model = model

        self.logger.info("Initialized MarkdownAgent %s with model %s", agent_id, model)

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """Execute the agent using the BaseAgent interface.

        Args:
            agent_input: Standard agent input

        Returns:
            Standard agent output
        """
        try:
            # Convert AgentInput to Dict format for internal processing
            input_data = {
                "content": agent_input.content,
            }

            # Add context if available
            if agent_input.context:
                input_data["additional_context"] = str(agent_input.context)

            # Process using internal method
            result = await self._process_internal(input_data)

            # Convert to AgentOutput format
            return self._create_output(
                content=result["response"] if result["success"] else f"Error: {result.get('error', 'Unknown error')}",
                metadata={
                    "agent_id": result.get("agent_id", self.agent_id),
                    "model_used": result.get("model_used", self.model),
                    "success": result["success"],
                },
                confidence=1.0 if result["success"] else 0.0,
                request_id=agent_input.request_id,
            )

        except Exception as e:
            self.logger.error("Error in execute method: %s", e)
            return self._create_output(
                content=f"Agent execution failed: {e!s}",
                metadata={"success": False, "error": str(e)},
                confidence=0.0,
                request_id=agent_input.request_id,
            )

    async def process(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Legacy process method for backwards compatibility."""
        return await self._process_internal(input_data)

    async def _process_internal(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Process input using the markdown-defined behavior.

        Args:
            input_data: Input data containing the task/query

        Returns:
            Dict containing the agent's response
        """
        try:
            # Construct the prompt from the definition and context
            prompt = self._build_prompt(input_data)

            # Use the configured model to process
            response = await self._call_model(prompt, input_data)

            return {
                "success": True,
                "response": response,
                "agent_id": self.agent_id,
                "model_used": self.model,
            }

        except Exception as e:
            self.logger.error("Error processing input: %s", e)
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id,
            }

    def _build_prompt(self, input_data: dict[str, Any]) -> str:
        """Build the complete prompt from definition, context, and input."""

        parts = []

        # Add context if available
        if self.context:
            parts.append("# Context\n")
            parts.append(self.context)
            parts.append("\n")

        # Add agent definition
        parts.append("# Agent Instructions\n")
        parts.append(self.definition)
        parts.append("\n")

        # Add the specific task/query
        if "task" in input_data:
            parts.append("# Task\n")
            parts.append(str(input_data["task"]))
        elif "query" in input_data:
            parts.append("# Query\n")
            parts.append(str(input_data["query"]))
        elif "prompt" in input_data:
            parts.append("# Request\n")
            parts.append(str(input_data["prompt"]))

        # Add any additional context from input
        if "additional_context" in input_data:
            parts.append("\n# Additional Context\n")
            parts.append(str(input_data["additional_context"]))

        return "".join(parts)

    async def _call_model(self, prompt: str, input_data: dict[str, Any]) -> str:
        """Call the AI model with the constructed prompt."""

        # For now, this is a placeholder that would integrate with
        # the actual model calling infrastructure (Claude, OpenAI, etc.)
        #
        # In a real implementation, this would:
        # 1. Use the self.model to determine which API to call
        # 2. Handle model-specific formatting
        # 3. Manage rate limiting and retries
        # 4. Apply any agent-specific processing

        self.logger.info("Calling model %s with prompt length: %s", self.model, len(prompt))

        # Placeholder response - in real implementation this would call actual models
        return f"[MarkdownAgent {self.agent_id}] Processed with {self.model}: {input_data.get('task', input_data.get('content', 'unknown task'))}"

    def get_capabilities(self) -> dict[str, Any]:
        """Return agent capabilities and metadata."""
        tools = self.config.get("tools", [])
        return {
            "agent_id": self.agent_id,
            "type": "markdown",
            "model": self.model,
            "tools": tools,
            "description": "Dynamically created agent from markdown definition",
            "supports_streaming": False,
            "supports_tools": len(tools) > 0,
        }

    async def validate_input(self, input_data: dict[str, Any]) -> bool:
        """Validate that input data contains required fields."""
        required_fields = ["task", "query", "prompt"]
        return any(field in input_data for field in required_fields)

    def __str__(self) -> str:
        """String representation of the agent."""
        return f"MarkdownAgent(id={self.agent_id}, model={self.model})"
