# Agent Extension Guidelines

## Overview

This document provides comprehensive guidelines for external teams to extend the PromptCraft Agent System with custom
agents. The system is designed to be modular, extensible, and maintainable, following established patterns and
conventions.

## Architecture Overview

### Core Components

- **BaseAgent**: Abstract base class defining the agent contract
- **AgentRegistry**: Central registry for agent discovery and management
- **AgentInput/AgentOutput**: Standardized data models for agent communication
- **Exception Handling**: Comprehensive error handling and propagation
- **Observability**: Structured logging and OpenTelemetry integration

### Extension Points

External teams can extend the system by:

1. **Custom Agent Implementation**: Create new agent classes inheriting from BaseAgent
2. **Specialized Input/Output Models**: Define custom data models for specific use cases
3. **Custom Exception Types**: Implement domain-specific error handling
4. **Observability Enhancement**: Add custom metrics and tracing
5. **Registry Extensions**: Implement custom discovery and capability matching

## Agent Development Guidelines

### 1. Basic Agent Structure

```python
from src.agents.base_agent import BaseAgent
from src.agents.models import AgentInput, AgentOutput
from src.agents.registry import agent_registry

@agent_registry.register("my_custom_agent")
class MyCustomAgent(BaseAgent):
    """Custom agent for specific functionality."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Custom initialization logic
        self.custom_parameter = config.get("custom_parameter", "default_value")

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """
        Core agent execution logic.

        Args:
            agent_input: Input data for the agent

        Returns:
            AgentOutput: Agent response with results
        """
        # Process input
        result = self.process_content(agent_input.content)

        # Return standardized output
        return self._create_output(
            content=result,
            metadata={"processed": True},
            confidence=0.95,
            request_id=agent_input.request_id
        )

    def get_capabilities(self) -> Dict[str, Any]:
        """Define agent capabilities for discovery."""
        return {
            "agent_id": self.agent_id,
            "agent_type": "CustomAgent",
            "input_types": ["text", "json"],
            "output_types": ["text", "analysis"],
            "specialization": "custom_processing",
            "max_input_length": 10000,
            "supports_streaming": False,
            "requires_context": False
        }
```

### 2. Configuration Management

#### Required Configuration Fields

```python
# Minimum required configuration
config = {
    "agent_id": "my_custom_agent",  # Must be unique, snake_case
    "timeout": 30.0,                # Default timeout in seconds
    "max_retries": 3,               # Maximum retry attempts
    "log_level": "INFO"             # Logging level
}

# Optional configuration fields
config.update({
    "custom_parameter": "value",
    "api_endpoint": "https://api.example.com",
    "batch_size": 100,
    "enable_caching": True
})
```

#### Configuration Validation

```python
def _validate_configuration(self) -> None:
    """Validate agent-specific configuration."""
    super()._validate_configuration()

    # Validate custom parameters
    if not isinstance(self.config.get("custom_parameter"), str):
        raise AgentConfigurationError(
            message="custom_parameter must be a string",
            error_code="INVALID_CONFIG_VALUE",
            context={"parameter": "custom_parameter"},
            agent_id=self.agent_id
        )

    # Validate API endpoint if provided
    endpoint = self.config.get("api_endpoint")
    if endpoint and not endpoint.startswith("https://"):
        raise AgentConfigurationError(
            message="api_endpoint must use HTTPS",
            error_code="INVALID_CONFIG_VALUE",
            context={"endpoint": endpoint},
            agent_id=self.agent_id
        )
```

### 3. Error Handling Best Practices

#### Custom Exception Types

```python
from src.agents.exceptions import AgentError

class CustomAgentError(AgentError):
    """Custom agent-specific error."""

    def __init__(
        self,
        message: str,
        error_code: str = "CUSTOM_AGENT_ERROR",
        context: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            context=context,
            agent_id=agent_id,
            request_id=request_id
        )
```

#### Error Handling in Execute Method

```python
async def execute(self, agent_input: AgentInput) -> AgentOutput:
    """Execute with proper error handling."""
    try:
        # Validate input
        if not agent_input.content:
            raise CustomAgentError(
                message="Content cannot be empty",
                error_code="EMPTY_CONTENT",
                agent_id=self.agent_id,
                request_id=agent_input.request_id
            )

        # Process content
        result = await self.process_content(agent_input.content)

        return self._create_output(
            content=result,
            confidence=0.95,
            request_id=agent_input.request_id
        )

    except Exception as e:
        # Handle unexpected errors
        if isinstance(e, AgentError):
            raise

        # Wrap non-agent errors
        raise CustomAgentError(
            message=f"Unexpected error during processing: {str(e)}",
            error_code="PROCESSING_ERROR",
            context={"original_error": str(e), "error_type": type(e).__name__},
            agent_id=self.agent_id,
            request_id=agent_input.request_id
        )
```

### 4. Observability Integration

#### Structured Logging

```python
from src.utils.observability import create_structured_logger, log_agent_event

class MyCustomAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.custom_logger = create_structured_logger(f"custom_agent.{self.agent_id}")

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        # Log processing start
        self.custom_logger.info(
            f"Starting custom processing for request {agent_input.request_id}",
            request_id=agent_input.request_id,
            agent_id=self.agent_id,
            content_type=type(agent_input.content).__name__,
            content_length=len(str(agent_input.content))
        )

        # Process content
        result = await self.process_content(agent_input.content)

        # Log completion
        log_agent_event(
            event_type="custom_processing_completed",
            agent_id=self.agent_id,
            message=f"Custom processing completed for request {agent_input.request_id}",
            request_id=agent_input.request_id,
            result_length=len(result),
            processing_stage="completion"
        )

        return self._create_output(content=result, request_id=agent_input.request_id)
```

#### Custom Metrics

```python
from src.utils.observability import get_metrics_collector

class MyCustomAgent(BaseAgent):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.metrics = get_metrics_collector()

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        # Record custom metrics
        self.metrics.increment_counter("custom_agent_requests_total")

        start_time = time.time()

        try:
            result = await self.process_content(agent_input.content)

            # Record success metrics
            self.metrics.increment_counter("custom_agent_requests_success")
            self.metrics.record_duration(
                "custom_processing_duration_seconds",
                time.time() - start_time
            )

            return self._create_output(content=result, request_id=agent_input.request_id)

        except Exception as e:
            # Record failure metrics
            self.metrics.increment_counter("custom_agent_requests_failed")
            raise
```

### 5. Testing Guidelines

#### Unit Testing Structure

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock

class TestMyCustomAgent:
    """Test suite for MyCustomAgent."""

    @pytest.fixture
    def agent_config(self):
        """Standard agent configuration for testing."""
        return {
            "agent_id": "test_custom_agent",
            "timeout": 30.0,
            "custom_parameter": "test_value"
        }

    @pytest.fixture
    def agent(self, agent_config):
        """Agent instance for testing."""
        return MyCustomAgent(agent_config)

    @pytest.mark.asyncio
    async def test_execute_success(self, agent):
        """Test successful execution."""
        agent_input = AgentInput(
            content="test content",
            request_id="test-request-123"
        )

        result = await agent.execute(agent_input)

        assert isinstance(result, AgentOutput)
        assert result.agent_id == "test_custom_agent"
        assert result.request_id == "test-request-123"
        assert result.confidence > 0.0

    @pytest.mark.asyncio
    async def test_execute_empty_content_error(self, agent):
        """Test error handling for empty content."""
        agent_input = AgentInput(
            content="",
            request_id="test-request-456"
        )

        with pytest.raises(CustomAgentError) as excinfo:
            await agent.execute(agent_input)

        assert excinfo.value.error_code == "EMPTY_CONTENT"
        assert excinfo.value.agent_id == "test_custom_agent"
        assert excinfo.value.request_id == "test-request-456"

    def test_get_capabilities(self, agent):
        """Test capability definition."""
        capabilities = agent.get_capabilities()

        assert capabilities["agent_id"] == "test_custom_agent"
        assert capabilities["agent_type"] == "CustomAgent"
        assert "text" in capabilities["input_types"]
        assert "specialization" in capabilities

    def test_configuration_validation(self, agent_config):
        """Test configuration validation."""
        # Test invalid custom_parameter
        agent_config["custom_parameter"] = 123

        with pytest.raises(AgentConfigurationError) as excinfo:
            MyCustomAgent(agent_config)

        assert "custom_parameter must be a string" in excinfo.value.message
```

#### Integration Testing

```python
@pytest.mark.integration
class TestMyCustomAgentIntegration:
    """Integration tests for MyCustomAgent."""

    @pytest.fixture
    def registry(self):
        """Registry with custom agent registered."""
        registry = AgentRegistry()
        registry.register("integration_test_agent")(MyCustomAgent)
        yield registry
        registry.clear()

    @pytest.mark.asyncio
    async def test_registry_integration(self, registry):
        """Test agent integration with registry."""
        config = {
            "agent_id": "integration_test_agent",
            "custom_parameter": "integration_value"
        }

        # Get agent from registry
        agent = registry.get_agent("integration_test_agent", config)

        # Test execution
        agent_input = AgentInput(content="integration test")
        result = await agent.process(agent_input)

        assert isinstance(result, AgentOutput)
        assert result.agent_id == "integration_test_agent"

    @pytest.mark.asyncio
    async def test_capability_discovery(self, registry):
        """Test capability-based agent discovery."""
        config = {"agent_id": "integration_test_agent"}
        agent = registry.get_agent("integration_test_agent", config)

        # Test capability discovery
        text_agents = registry.find_agents_by_type("text")
        custom_agents = registry.find_agents_by_capability("specialization", "custom_processing")

        assert "integration_test_agent" in text_agents
        assert "integration_test_agent" in custom_agents
```

### 6. Performance Considerations

#### Async/Await Best Practices

```python
async def execute(self, agent_input: AgentInput) -> AgentOutput:
    """Efficient async execution."""

    # Use async context managers for resources
    async with self.get_async_resource() as resource:
        # Concurrent operations where possible
        tasks = [
            self.process_part_a(agent_input.content),
            self.process_part_b(agent_input.context),
            self.validate_input(agent_input)
        ]

        results = await asyncio.gather(*tasks)

        # Combine results
        final_result = self.combine_results(results)

        return self._create_output(
            content=final_result,
            request_id=agent_input.request_id
        )
```

#### Memory Management

```python
async def execute(self, agent_input: AgentInput) -> AgentOutput:
    """Memory-efficient execution."""

    # Use generators for large data processing
    def process_chunks(content):
        for chunk in self.chunk_content(content):
            yield self.process_chunk(chunk)

    # Process in batches to avoid memory issues
    results = []
    for batch in self.batch_generator(agent_input.content, batch_size=1000):
        batch_results = await self.process_batch(batch)
        results.extend(batch_results)

        # Cleanup intermediate results
        del batch_results

    return self._create_output(
        content=self.combine_results(results),
        request_id=agent_input.request_id
    )
```

### 7. Security Considerations

#### Input Validation

```python
def validate_input(self, agent_input: AgentInput) -> None:
    """Validate and sanitize input."""

    # Content validation
    if len(agent_input.content) > self.config.get("max_input_length", 10000):
        raise CustomAgentError(
            message="Input content exceeds maximum length",
            error_code="INPUT_TOO_LONG",
            context={"max_length": self.config.get("max_input_length")},
            agent_id=self.agent_id,
            request_id=agent_input.request_id
        )

    # Sanitize content
    sanitized_content = self.sanitize_content(agent_input.content)
    if sanitized_content != agent_input.content:
        self.logger.warning(
            f"Input content was sanitized for request {agent_input.request_id}",
            request_id=agent_input.request_id,
            agent_id=self.agent_id
        )
```

#### Secret Management

```python
def __init__(self, config: Dict[str, Any]):
    super().__init__(config)

    # Never log sensitive configuration
    safe_config = {k: v for k, v in config.items() if k not in ["api_key", "secret"]}
    self.logger.info(f"Initialized agent with config: {safe_config}")

    # Use environment variables for secrets
    self.api_key = os.getenv("CUSTOM_AGENT_API_KEY")
    if not self.api_key:
        raise AgentConfigurationError(
            message="API key not found in environment variables",
            error_code="MISSING_API_KEY",
            agent_id=self.agent_id
        )
```

## Registration and Deployment

### 1. Agent Registration

```python
# Method 1: Decorator registration
@agent_registry.register("my_custom_agent")
class MyCustomAgent(BaseAgent):
    pass

# Method 2: Explicit registration
agent_registry.register("my_custom_agent")(MyCustomAgent)

# Method 3: Conditional registration
if some_condition:
    agent_registry.register("conditional_agent")(ConditionalAgent)
```

### 2. Configuration Management

```python
# Load configuration from environment
config = {
    "agent_id": "my_custom_agent",
    "timeout": float(os.getenv("AGENT_TIMEOUT", "30.0")),
    "custom_parameter": os.getenv("CUSTOM_PARAMETER", "default"),
    "api_endpoint": os.getenv("API_ENDPOINT", "https://api.example.com")
}

# Validate configuration
agent = MyCustomAgent(config)
```

### 3. Deployment Checklist

- [ ] Agent class inherits from BaseAgent
- [ ] execute() method is implemented and async
- [ ] get_capabilities() returns comprehensive capability information
- [ ] Configuration validation is implemented
- [ ] Error handling uses agent-specific exceptions
- [ ] Logging and metrics are integrated
- [ ] Unit tests achieve >90% coverage
- [ ] Integration tests validate registry integration
- [ ] Performance tests validate under load
- [ ] Security review completed
- [ ] Documentation updated

## Advanced Topics

### 1. Custom Input/Output Models

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class CustomAgentInput(BaseModel):
    """Custom input model for specialized agents."""
    content: str = Field(..., description="Primary content to process")
    processing_mode: str = Field("standard", description="Processing mode")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    batch_items: List[str] = Field(default_factory=list)

class CustomAgentOutput(BaseModel):
    """Custom output model for specialized agents."""
    results: List[str] = Field(..., description="Processing results")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, float] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
```

### 2. Capability-Based Discovery

```python
def get_capabilities(self) -> Dict[str, Any]:
    """Enhanced capability definition."""
    return {
        "agent_id": self.agent_id,
        "agent_type": "CustomAgent",
        "version": "1.0.0",
        "input_types": ["text", "json", "csv"],
        "output_types": ["text", "json", "analysis"],
        "specialization": "data_processing",
        "performance": {
            "max_input_length": 100000,
            "average_processing_time": 0.5,
            "memory_usage": "medium",
            "cpu_intensive": False
        },
        "features": {
            "supports_streaming": True,
            "supports_batch": True,
            "requires_context": False,
            "stateful": False
        },
        "requirements": {
            "min_memory": "512MB",
            "gpu_required": False,
            "external_dependencies": ["numpy", "pandas"]
        }
    }
```

### 3. Multi-Agent Coordination

```python
class CoordinatingAgent(BaseAgent):
    """Agent that coordinates with other agents."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.registry = config.get("registry", agent_registry)

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        """Execute with coordination."""

        # Find specialized agents
        text_agents = self.registry.find_agents_by_type("text")
        analysis_agents = self.registry.find_agents_by_capability("specialization", "analysis")

        # Coordinate processing
        text_result = await self.delegate_to_agent(text_agents[0], agent_input)
        analysis_result = await self.delegate_to_agent(analysis_agents[0], text_result)

        return self._create_output(
            content=analysis_result.content,
            metadata={"coordination": True, "agents_used": [text_agents[0], analysis_agents[0]]},
            request_id=agent_input.request_id
        )

    async def delegate_to_agent(self, agent_id: str, input_data) -> AgentOutput:
        """Delegate processing to another agent."""
        agent = self.registry.get_agent(agent_id, {"agent_id": agent_id})
        return await agent.process(input_data)
```

## Support and Resources

### Documentation

- [API Reference](./api_reference.md)
- [Agent Registry Documentation](./agent_registry.md)
- [Error Handling Guide](./error_handling.md)
- [Testing Framework](./testing_framework.md)

### Community

- GitHub Issues: [PromptCraft Issues](https://github.com/promptcraft/issues)
- Discord: [PromptCraft Community](https://discord.gg/promptcraft)
- Stack Overflow: Tag `promptcraft-agents`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your agent following these guidelines
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

### License

All custom agents must be compatible with the PromptCraft license terms.

---

*This document is maintained by the PromptCraft Agent System team. For questions or clarifications, please open an
issue or contact the maintainers.*
