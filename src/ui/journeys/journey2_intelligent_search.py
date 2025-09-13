"""
Journey 2: Intelligent Search Interface

This module implements the OpenRouter execution interface for enhanced prompts
created in Journey 1, with placeholder for future HyDE-powered search integration.
"""

import logging
import time
from typing import Any

import gradio as gr

from src.mcp_integration.openrouter_client import OpenRouterClient
from src.mcp_integration.zen_stdio_client import ZenStdioMCPClient
from src.utils.logging_mixin import LoggerMixin


logger = logging.getLogger(__name__)

# Response processing constants
MAX_RESPONSE_LENGTH = 10000  # Maximum response length to display
RESPONSE_PREVIEW_LENGTH = 500  # Response preview length
ERROR_RECOVERY_TIMEOUT = 5.0  # Timeout for error recovery


class Journey2IntelligentSearch(LoggerMixin):
    """
    Journey 2: Intelligent Search implementation with OpenRouter execution.

    Features:
    - Execute enhanced prompts from Journey 1 through OpenRouter
    - Model selection and configuration
    - Response formatting and display
    - Error handling and recovery
    - Cost tracking and attribution
    - Placeholder for future HyDE search integration
    """

    def __init__(self) -> None:
        super().__init__()
        self.openrouter_client = OpenRouterClient()
        self.zen_client = ZenStdioMCPClient()
        self.mcp_enabled = True  # Enable MCP routing by default
        self._routing_metadata: dict[str, Any] = {}  # Track routing decisions

    async def _execute_with_intelligent_routing(
        self,
        enhanced_prompt: str,
        user_tier: str,
        workflow_step: dict[str, Any],
    ) -> tuple[list[Any], dict[str, Any]]:
        """
        Execute with intelligent routing: zen MCP first, OpenRouter fallback.

        Args:
            enhanced_prompt: The prompt to execute
            user_tier: User access tier
            workflow_step: Workflow step configuration

        Returns:
            Tuple of (responses, routing_metadata)
        """
        routing_metadata = {
            "routing_method": "unknown",
            "zen_attempted": False,
            "zen_success": False,
            "fallback_used": False,
            "routing_time_ms": 0,
            "error_details": None,
        }

        routing_start = time.time()

        # Phase 1: Try zen MCP routing if enabled
        if self.mcp_enabled:
            routing_metadata["zen_attempted"] = True
            try:
                self.logger.info("🚀 Attempting zen MCP intelligent routing...")

                # Connect to zen MCP server
                zen_connected = await self.zen_client.connect()

                if zen_connected:
                    # Try to get model recommendations first
                    recommendations = await self.zen_client.get_model_recommendations(enhanced_prompt)

                    if recommendations:
                        self.logger.info(
                            "✅ Zen routing - Recommended model: %s",
                            recommendations.primary_recommendation.model_name,
                        )
                        routing_metadata["recommended_model"] = recommendations.primary_recommendation.model_name
                        routing_metadata["task_type"] = recommendations.task_type
                        routing_metadata["complexity_level"] = recommendations.complexity_level

                    # Execute with zen routing
                    result = await self.zen_client.execute_with_routing(enhanced_prompt)

                    if result["success"]:
                        # Convert zen result to Response format
                        from src.mcp_integration.mcp_client import Response  # Avoid circular imports

                        response = Response(
                            agent_id="zen_routing",
                            content=result["result"]["content"],
                            metadata=result["result"]["routing_metadata"],
                            confidence=result["result"]["routing_metadata"].get("confidence", 0.9),
                            processing_time=result["result"]["response_time"],
                            success=True,
                        )

                        routing_metadata["zen_success"] = True
                        routing_metadata["routing_method"] = "zen_mcp"
                        routing_metadata["model_used"] = result["result"]["model_used"]
                        routing_metadata["cost_optimized"] = result["result"]["routing_metadata"].get(
                            "cost_optimized",
                            False,
                        )

                        await self.zen_client.disconnect()
                        routing_metadata["routing_time_ms"] = (time.time() - routing_start) * 1000

                        self.logger.info("✅ Zen MCP routing successful!")
                        return ([response], routing_metadata)
                    self.logger.warning("⚠️ Zen execution failed: %s", result["error"])
                    routing_metadata["error_details"] = result["error"]

                else:
                    self.logger.warning("⚠️ Could not connect to zen MCP server")
                    routing_metadata["error_details"] = "Connection failed"

                # Ensure cleanup on failure
                await self.zen_client.disconnect()

            except Exception as e:
                self.logger.error("❌ Zen MCP routing error: %s", e)
                routing_metadata["error_details"] = str(e)
                # Ensure cleanup on exception
                try:
                    await self.zen_client.disconnect()
                except Exception as e:
                    self.logger.debug("Error during zen client disconnect: %s", e)

        # Phase 2: Fallback to OpenRouter (existing logic)
        routing_metadata["fallback_used"] = True
        routing_metadata["routing_method"] = "openrouter_fallback"

        self.logger.info("🔄 Falling back to OpenRouter routing...")

        try:
            # Ensure OpenRouter connection
            await self.openrouter_client.connect()

            # Execute the workflow step
            from src.mcp_integration.mcp_client import WorkflowStep  # Avoid circular imports

            step = WorkflowStep(
                step_id=workflow_step["step_id"],
                agent_id=workflow_step["agent_id"],
                input_data=workflow_step["input_data"],
                timeout_seconds=workflow_step["timeout_seconds"],
            )

            responses = await self.openrouter_client.orchestrate_agents([step])

            routing_metadata["routing_time_ms"] = (time.time() - routing_start) * 1000

            if responses and len(responses) > 0 and responses[0].success:
                self.logger.info("✅ OpenRouter fallback successful!")
                return (responses, routing_metadata)
            error_msg = responses[0].error_message if responses and len(responses) > 0 else "Unknown error"
            routing_metadata["error_details"] = error_msg
            raise Exception(f"OpenRouter execution failed: {error_msg}")

        except Exception as e:
            self.logger.error("❌ OpenRouter fallback also failed: %s", e)
            routing_metadata["error_details"] = f"Both zen and OpenRouter failed: {e}"
            routing_metadata["routing_time_ms"] = (time.time() - routing_start) * 1000
            raise e

    async def execute_prompt(
        self,
        enhanced_prompt: str,
        model_mode: str,
        custom_model: str,
        temperature: float,
        max_tokens: int,
        user_tier: str = "limited",
    ) -> tuple[str, str, str, str]:
        """
        Execute enhanced prompt through OpenRouter API.

        Args:
            enhanced_prompt: Enhanced prompt to execute
            model_mode: Model selection mode
            custom_model: Custom model selection
            temperature: Response creativity
            max_tokens: Maximum tokens for response
            user_tier: User access tier

        Returns:
            Tuple of (response_content, model_attribution, execution_stats, error_message)
        """
        start_time = time.time()

        try:
            # Validate inputs
            if not enhanced_prompt or not enhanced_prompt.strip():
                return (
                    "",
                    "",
                    "",
                    "❌ Error: No prompt provided. Please create an enhanced prompt in Journey 1 first.",
                )

            # Determine model based on user tier and selection
            selected_model = self._select_model(model_mode, custom_model, user_tier)

            # Prepare OpenRouter request
            workflow_step = {
                "step_id": "journey2_execute",
                "agent_id": "journey2_search",
                "input_data": {
                    "query": enhanced_prompt,
                    "task_type": "general",
                    "allow_premium": user_tier in ["admin", "full"],
                    "user_tier": user_tier,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
                "timeout_seconds": 30.0,
            }

            # Execute with intelligent routing (zen MCP → OpenRouter fallback)
            try:
                responses, routing_metadata = await self._execute_with_intelligent_routing(
                    enhanced_prompt,
                    user_tier,
                    workflow_step,
                )

                # Store routing metadata for use in response
                self._routing_metadata = routing_metadata

                if responses and len(responses) > 0:
                    response = responses[0]
                    if response.success:
                        response_time = time.time() - start_time

                        # Calculate cost estimation
                        actual_model = routing_metadata.get("model_used", selected_model)
                        estimated_cost = self._calculate_cost(actual_model, len(enhanced_prompt), len(response.content))

                        # Determine routing display info
                        routing_icon = "🚀" if routing_metadata.get("zen_success") else "🔄"
                        routing_method = "zen MCP" if routing_metadata.get("zen_success") else "OpenRouter"
                        routing_color = "#4CAF50" if routing_metadata.get("zen_success") else "#FF9800"

                        # Create model attribution with routing info
                        model_attribution = f"""
                        <div class="model-attribution">
                            <strong>🤖 Model Used:</strong> {actual_model} |
                            <strong>⏱️ Response Time:</strong> {response_time:.2f}s |
                            <strong>💰 Cost:</strong> ${estimated_cost:.4f} |
                            <strong>🎯 Confidence:</strong> {response.confidence:.1%} |
                            <span style="color: {routing_color};"><strong>{routing_icon} Routed via:</strong> {routing_method}</span>
                        </div>
                        """

                        # Create enhanced execution stats with routing info
                        routing_stats = ""
                        if routing_metadata.get("zen_success"):
                            routing_stats = f"""
                                <li><strong>🚀 zen MCP Routing:</strong> Successful</li>
                                <li><strong>Task Type:</strong> {routing_metadata.get("task_type", "N/A")}</li>
                                <li><strong>Complexity:</strong> {routing_metadata.get("complexity_level", "N/A")}</li>
                                <li><strong>Cost Optimized:</strong> {'Yes' if routing_metadata.get("cost_optimized") else 'No'}</li>
                                <li><strong>Routing Time:</strong> {routing_metadata.get("routing_time_ms", 0):.1f}ms</li>
                            """
                        elif routing_metadata.get("fallback_used"):
                            routing_stats = f"""
                                <li><strong>🔄 Fallback Mode:</strong> OpenRouter (zen unavailable)</li>
                                <li><strong>zen Attempted:</strong> {'Yes' if routing_metadata.get("zen_attempted") else 'No'}</li>
                                <li><strong>Routing Time:</strong> {routing_metadata.get("routing_time_ms", 0):.1f}ms</li>
                            """

                        execution_stats = f"""
                        <div class="execution-stats">
                            <h4>📊 Execution Statistics</h4>
                            <ul>
                                <li><strong>Model:</strong> {actual_model}</li>
                                <li><strong>Temperature:</strong> {temperature}</li>
                                <li><strong>Max Tokens:</strong> {max_tokens}</li>
                                <li><strong>Response Length:</strong> {len(response.content)} characters</li>
                                <li><strong>Processing Time:</strong> {response_time:.2f} seconds</li>
                                <li><strong>User Tier:</strong> {user_tier}</li>
                                {routing_stats}
                            </ul>
                        </div>
                        """

                        return (
                            response.content,
                            model_attribution,
                            execution_stats,
                            "",
                        )
                    error_msg = response.error_message or "Unknown execution error"
                    return (
                        "",
                        "",
                        "",
                        f"❌ Execution Error: {error_msg}",
                    )
                return (
                    "",
                    "",
                    "",
                    "❌ No response received from OpenRouter. Please try again.",
                )

            except Exception as api_error:
                self.logger.error("OpenRouter API error: %s", api_error)
                return (
                    "",
                    "",
                    "",
                    f"❌ API Error: {api_error!s}. Please check your configuration and try again.",
                )

        except Exception as e:
            self.logger.error("Journey 2 execution error: %s", e)
            return (
                "",
                "",
                "",
                f"❌ Execution Error: {e!s}. Please try again or contact support.",
            )

    def _select_model(self, model_mode: str, custom_model: str, user_tier: str) -> str:
        """Select appropriate model based on mode and user tier."""
        # Enforce tier restrictions
        if user_tier == "limited":
            # Limited users can only use free models
            if model_mode in {"free_mode", "basic"}:
                return "deepseek/deepseek-chat:free"
            self.logger.warning("Limited user attempted to use %s, defaulting to free model", model_mode)
            return "deepseek/deepseek-chat:free"

        # Full and admin users have access to all models
        if model_mode == "custom" and custom_model:
            return custom_model
        if model_mode == "free_mode":
            return "deepseek/deepseek-chat:free"
        if model_mode == "premium":
            return "anthropic/claude-3-5-sonnet-20241022"
        # standard
        return "openai/gpt-4o-mini"

    def _calculate_cost(self, model: str, input_length: int, output_length: int) -> float:
        """Calculate estimated cost for the request."""
        # Cost per 1K tokens (estimated)
        costs = {
            "deepseek/deepseek-chat:free": 0.0,
            "meta-llama/llama-3.3-70b-instruct:free": 0.0,
            "openai/gpt-4o-mini": 0.00015,
            "anthropic/claude-3-5-sonnet-20241022": 0.003,
            "openai/gpt-4o": 0.005,
        }

        cost_per_1k = costs.get(model, 0.002)  # Default cost if model not in list
        total_chars = input_length + output_length
        estimated_tokens = total_chars / 4  # Rough estimation: 4 chars per token
        return (estimated_tokens / 1000) * cost_per_1k

    def create_transfer_from_journey1(self, enhanced_prompt: str, create_breakdown: dict) -> dict[str, str]:
        """
        Create a transfer object from Journey 1 data.

        Args:
            enhanced_prompt: Enhanced prompt from Journey 1
            create_breakdown: C.R.E.A.T.E. framework breakdown

        Returns:
            Dictionary with transfer data
        """
        return {
            "enhanced_prompt": enhanced_prompt,
            "context": create_breakdown.get("context", ""),
            "request": create_breakdown.get("request", ""),
            "examples": create_breakdown.get("examples", ""),
            "augmentations": create_breakdown.get("augmentations", ""),
            "tone_format": create_breakdown.get("tone_format", ""),
            "evaluation": create_breakdown.get("evaluation", ""),
            "transfer_timestamp": str(time.time()),
            "source": "journey1_smart_templates",
        }

    def format_response_for_display(self, response_content: str) -> str:
        """
        Format response content for better display.

        Args:
            response_content: Raw response from AI model

        Returns:
            Formatted response content
        """
        if not response_content:
            return "No response content available."

        # Limit response length for display
        if len(response_content) > MAX_RESPONSE_LENGTH:
            truncated_content = response_content[:MAX_RESPONSE_LENGTH]
            return f"{truncated_content}\n\n... (Response truncated for display. Total length: {len(response_content)} characters)"

        return response_content

    def extract_key_insights(self, response_content: str) -> str:
        """
        Extract key insights from the response for quick overview.

        Args:
            response_content: AI model response

        Returns:
            Key insights summary
        """
        if not response_content or len(response_content) < 100:
            return "Response too short for insight extraction."

        # Simple extraction - take first paragraph or first few sentences
        lines = response_content.split("\n")
        non_empty_lines = [line.strip() for line in lines if line.strip()]

        if not non_empty_lines:
            return "No key insights available."

        # Take first substantial paragraph
        for line in non_empty_lines:
            if len(line) > 50:  # Substantial content
                if len(line) > RESPONSE_PREVIEW_LENGTH:
                    return f"{line[:RESPONSE_PREVIEW_LENGTH]}..."
                return line

        # Fallback: take first few lines
        insight_lines = non_empty_lines[:3]
        insight_text = " ".join(insight_lines)

        if len(insight_text) > RESPONSE_PREVIEW_LENGTH:
            return f"{insight_text[:RESPONSE_PREVIEW_LENGTH]}..."

        return insight_text

    def validate_prompt_for_execution(self, prompt: str) -> tuple[bool, str]:
        """
        Validate prompt before execution.

        Args:
            prompt: Prompt to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if not prompt or not prompt.strip():
            return False, "Prompt is empty. Please provide a valid prompt."

        if len(prompt) > 50000:  # 50K character limit
            return False, f"Prompt is too long ({len(prompt)} characters). Maximum allowed is 50,000 characters."

        if len(prompt.strip()) < 10:
            return False, "Prompt is too short. Please provide at least 10 characters of meaningful content."

        return True, "Prompt is valid for execution."

    def get_available_models_for_tier(self, user_tier: str) -> list[tuple[str, str]]:
        """
        Get available models for the user's tier.

        Args:
            user_tier: User access tier

        Returns:
            List of (display_name, model_id) tuples
        """
        if user_tier == "limited":
            return [
                ("🆓 DeepSeek Chat (Free)", "deepseek/deepseek-chat:free"),
                ("🆓 Llama 3.3 70B (Free)", "meta-llama/llama-3.3-70b-instruct:free"),
            ]
        if user_tier == "full":
            return [
                ("🆓 DeepSeek Chat (Free)", "deepseek/deepseek-chat:free"),
                ("🆓 Llama 3.3 70B (Free)", "meta-llama/llama-3.3-70b-instruct:free"),
                ("⚡ GPT-4o Mini", "openai/gpt-4o-mini"),
                ("🚀 Claude 3.5 Sonnet", "anthropic/claude-3-5-sonnet-20241022"),
            ]
        # admin
        return [
            ("🆓 DeepSeek Chat (Free)", "deepseek/deepseek-chat:free"),
            ("🆓 Llama 3.3 70B (Free)", "meta-llama/llama-3.3-70b-instruct:free"),
            ("⚡ GPT-4o Mini", "openai/gpt-4o-mini"),
            ("🚀 Claude 3.5 Sonnet", "anthropic/claude-3-5-sonnet-20241022"),
            ("🚀 GPT-4o", "openai/gpt-4o"),
        ]

    def create_execution_interface(
        self,
        user_tier: str = "limited",
        transfer_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create the Journey 2 execution interface components.

        Args:
            user_tier: User access tier
            transfer_data: Optional data transferred from Journey 1

        Returns:
            Dictionary of Gradio components
        """
        # Pre-fill with transfer data if available
        initial_prompt = transfer_data.get("enhanced_prompt", "") if transfer_data else ""

        return {
            "prompt_input": gr.Textbox(
                label="Enhanced Prompt to Execute",
                placeholder="Paste your enhanced prompt from Journey 1 here, or create one manually...",
                lines=8,
                max_lines=15,
                value=initial_prompt,
            ),
            "model_selector": gr.Dropdown(
                label=f"🤖 AI Model ({user_tier.title()} Tier)",
                choices=self.get_available_models_for_tier(user_tier),
                value=self.get_available_models_for_tier(user_tier)[0][1],
            ),
            "temperature": gr.Slider(
                minimum=0.0,
                maximum=2.0,
                value=0.7,
                step=0.1,
                label="🌡️ Creativity (Temperature)",
            ),
            "max_tokens": gr.Slider(
                minimum=100,
                maximum=4000,
                value=2000,
                step=100,
                label="📏 Max Response Length",
            ),
            "execute_button": gr.Button("🚀 Execute Prompt", variant="primary"),
            "clear_button": gr.Button("🗑️ Clear", variant="secondary"),
            "response_output": gr.Textbox(
                label="AI Response",
                lines=12,
                max_lines=20,
                interactive=False,
            ),
            "model_attribution": gr.HTML(
                """
                <div class="model-attribution">
                    <strong>Status:</strong> Ready to execute
                </div>
                """,
            ),
            "execution_stats": gr.HTML(
                """
                <div class="execution-stats">
                    <h4>📊 Execution Statistics</h4>
                    <p>Execute a prompt to see statistics</p>
                </div>
                """,
            ),
            "error_display": gr.HTML(""),
        }
