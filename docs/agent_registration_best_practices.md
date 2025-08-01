# Agent Registration Best Practices and Naming Conventions

## Overview

This document outlines best practices for agent registration, naming conventions, and organizational standards for the
PromptCraft Agent System. Following these guidelines ensures consistency, maintainability, and discoverability across
the agent ecosystem.

## Naming Conventions

### Agent ID Standards

Agent IDs serve as unique identifiers in the registry and must follow strict naming conventions:

#### Format Requirements

- **Pattern**: `snake_case` only
- **Characters**: Alphanumeric characters and underscores only
- **Length**: 3-50 characters
- **Uniqueness**: Must be globally unique within the registry

#### Valid Examples

```python
# Good agent IDs
"text_processor"
"security_analyzer"
"code_generator"
"data_transformer"
"claude_md_generator"
"create_framework_agent"
"irs_8867_validator"
"sql_injection_detector"
```

#### Invalid Examples

```python
# Invalid agent IDs
"text-processor"        # No dashes allowed
"textProcessor"         # No camelCase
"text.processor"        # No dots allowed
"text processor"        # No spaces allowed
"text/processor"        # No slashes allowed
"text_processor_"       # No trailing underscores
"_text_processor"       # No leading underscores
"tp"                    # Too short
"a" * 51                # Too long
```

### Agent Class Naming

Agent classes should follow Python class naming conventions with descriptive names:

#### Format Requirements

- **Pattern**: `PascalCase` with "Agent" suffix
- **Structure**: `{Purpose}Agent` or `{Domain}{Purpose}Agent`
- **Clarity**: Self-documenting and descriptive

#### Examples

```python
# Good agent class names
class TextProcessorAgent(BaseAgent):
    pass

class SecurityAnalyzerAgent(BaseAgent):
    pass

class CodeGeneratorAgent(BaseAgent):
    pass

class DataTransformerAgent(BaseAgent):
    pass

class ClaudeMdGeneratorAgent(BaseAgent):
    pass

class CreateFrameworkAgent(BaseAgent):
    pass
```

### File and Module Naming

Agent implementations should be organized in appropriately named files:

#### File Structure

```text
src/agents/
├── base_agent.py           # Base agent implementation
├── registry.py             # Agent registry
├── models.py               # Data models
├── exceptions.py           # Exception definitions
├── text_processor.py       # TextProcessorAgent
├── security_analyzer.py    # SecurityAnalyzerAgent
├── code_generator.py       # CodeGeneratorAgent
└── specialized/
    ├── __init__.py
    ├── create_framework.py  # CreateFrameworkAgent
    └── claude_md_generator.py # ClaudeMdGeneratorAgent
```

#### File Naming Rules

- **Pattern**: `snake_case.py`
- **Correspondence**: File name should match agent ID
- **Organization**: Group related agents in subdirectories
- **Imports**: Use relative imports within the agents package

## Registration Patterns

### Method 1: Decorator Registration (Recommended)

```python
from src.agents.registry import agent_registry
from src.agents.base_agent import BaseAgent

@agent_registry.register("text_processor")
class TextProcessorAgent(BaseAgent):
    """Agent for processing text content."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Agent-specific initialization

    async def execute(self, agent_input: AgentInput) -> AgentOutput:
        # Implementation
        pass
```

### Method 2: Explicit Registration

```python
class TextProcessorAgent(BaseAgent):
    """Agent for processing text content."""
    pass

# Register after class definition
agent_registry.register("text_processor")(TextProcessorAgent)
```

### Method 3: Conditional Registration

```python
class OptionalAgent(BaseAgent):
    """Agent that may not always be available."""
    pass

# Register only if conditions are met
if feature_enabled("optional_processing"):
    agent_registry.register("optional_processor")(OptionalAgent)
```

### Method 4: Batch Registration

```python
# Register multiple related agents
agents_to_register = [
    ("text_processor", TextProcessorAgent),
    ("text_analyzer", TextAnalyzerAgent),
    ("text_summarizer", TextSummarizerAgent),
]

for agent_id, agent_class in agents_to_register:
    agent_registry.register(agent_id)(agent_class)
```

## Organizational Standards

### Agent Categories

Organize agents into logical categories based on their primary function:

#### Core Processing Agents

- **Purpose**: Fundamental processing operations
- **Examples**: `text_processor`, `data_transformer`, `content_analyzer`
- **Naming**: `{operation}_{type}` or `{type}_{operation}`

#### Domain-Specific Agents

- **Purpose**: Specialized domain knowledge
- **Examples**: `security_analyzer`, `code_generator`, `create_framework`
- **Naming**: `{domain}_{operation}` or `{domain}_{specialty}`

#### Integration Agents

- **Purpose**: External system integration
- **Examples**: `azure_ai_client`, `qdrant_vector_store`, `github_integration`
- **Naming**: `{system}_{operation}` or `{system}_{client_type}`

#### Utility Agents

- **Purpose**: Supporting functionality
- **Examples**: `file_processor`, `format_converter`, `validation_agent`
- **Naming**: `{utility}_{operation}`

### Directory Structure

```text
src/agents/
├── core/                   # Core processing agents
│   ├── text_processor.py
│   ├── data_transformer.py
│   └── content_analyzer.py
├── domain/                 # Domain-specific agents
│   ├── security/
│   │   ├── security_analyzer.py
│   │   └── vulnerability_scanner.py
│   ├── code/
│   │   ├── code_generator.py
│   │   └── code_reviewer.py
│   └── create/
│       ├── create_framework.py
│       └── prompt_enhancer.py
├── integration/            # Integration agents
│   ├── azure_ai_client.py
│   ├── qdrant_client.py
│   └── github_integration.py
├── utility/               # Utility agents
│   ├── file_processor.py
│   ├── format_converter.py
│   └── validation_agent.py
└── specialized/           # Specialized implementations
    ├── claude_md_generator.py
    └── irs_8867_validator.py
```

## Configuration Standards

### Standard Configuration Fields

All agents should support these standard configuration fields:

```python
standard_config = {
    # Required fields
    "agent_id": str,           # Unique identifier
    "timeout": float,          # Execution timeout in seconds

    # Optional standard fields
    "max_retries": int,        # Maximum retry attempts (default: 3)
    "log_level": str,          # Logging level (default: "INFO")
    "enable_metrics": bool,    # Enable metrics collection (default: True)
    "enable_tracing": bool,    # Enable distributed tracing (default: True)

    # Performance settings
    "max_concurrent": int,     # Maximum concurrent executions
    "memory_limit": str,       # Memory limit (e.g., "512MB")
    "cpu_limit": float,        # CPU limit (e.g., 0.5 for 50%)

    # Feature flags
    "enable_caching": bool,    # Enable response caching
    "enable_batching": bool,   # Enable batch processing
    "strict_mode": bool,       # Enable strict validation
}
```

### Agent-Specific Configuration

```python
# Example: Security analyzer configuration
security_config = {
    **standard_config,
    "agent_id": "security_analyzer",

    # Agent-specific settings
    "vulnerability_db_url": str,
    "severity_threshold": str,
    "scan_timeout": float,
    "enable_deep_scan": bool,
    "exclude_patterns": List[str],
}

# Example: Code generator configuration
code_generator_config = {
    **standard_config,
    "agent_id": "code_generator",

    # Agent-specific settings
    "target_language": str,
    "framework": str,
    "code_style": str,
    "include_tests": bool,
    "include_docs": bool,
}
```

## Capability Definition Standards

### Standard Capability Fields

All agents must define capabilities for proper discovery and routing:

```python
def get_capabilities(self) -> Dict[str, Any]:
    """Standard capability definition."""
    return {
        # Identity
        "agent_id": self.agent_id,
        "agent_type": self.__class__.__name__,
        "version": "1.0.0",
        "description": "Brief description of agent functionality",

        # Input/Output types
        "input_types": ["text", "json", "csv"],
        "output_types": ["text", "json", "analysis"],

        # Specialization
        "specialization": "domain_specific_specialty",
        "tags": ["processing", "analysis", "security"],

        # Performance characteristics
        "performance": {
            "max_input_length": 10000,
            "average_processing_time": 0.5,
            "memory_usage": "medium",
            "cpu_intensive": False,
            "io_intensive": False,
        },

        # Features
        "features": {
            "supports_streaming": False,
            "supports_batch": True,
            "requires_context": False,
            "stateful": False,
            "async_execution": True,
        },

        # Requirements
        "requirements": {
            "min_memory": "256MB",
            "gpu_required": False,
            "external_dependencies": ["numpy", "pandas"],
            "network_access": True,
        },

        # Compatibility
        "compatibility": {
            "python_version": ">=3.11",
            "platform": ["linux", "windows", "macos"],
            "architecture": ["x86_64", "aarch64"],
        }
    }
```

### Capability Categories

#### Input/Output Types

```python
# Standard input types
INPUT_TYPES = [
    "text",           # Plain text content
    "json",           # JSON structured data
    "csv",            # CSV formatted data
    "xml",            # XML structured data
    "yaml",           # YAML configuration
    "markdown",       # Markdown formatted text
    "html",           # HTML content
    "binary",         # Binary data
    "image",          # Image data
    "code",           # Source code
]

# Standard output types
OUTPUT_TYPES = [
    "text",           # Plain text response
    "json",           # JSON structured response
    "analysis",       # Analysis results
    "report",         # Formatted report
    "code",           # Generated code
    "configuration",  # Configuration files
    "documentation",  # Documentation
    "visualization",  # Charts/graphs
]
```

#### Specialization Areas

```python
# Domain specializations
SPECIALIZATIONS = [
    "text_processing",
    "data_analysis",
    "code_generation",
    "security_analysis",
    "content_creation",
    "format_conversion",
    "validation",
    "integration",
    "orchestration",
    "monitoring",
]
```

## Registration Best Practices

### 1. Early Registration

Register agents early in the application lifecycle:

```python
# In __init__.py or main.py
def register_core_agents():
    """Register core system agents."""
    from .text_processor import TextProcessorAgent
    from .data_transformer import DataTransformerAgent

    agent_registry.register("text_processor")(TextProcessorAgent)
    agent_registry.register("data_transformer")(DataTransformerAgent)

# Call during application startup
register_core_agents()
```

### 2. Conditional Registration

Register agents based on availability and configuration:

```python
def register_optional_agents():
    """Register optional agents based on configuration."""

    # Check feature flags
    if config.get("enable_security_scanning"):
        from .security_analyzer import SecurityAnalyzerAgent
        agent_registry.register("security_analyzer")(SecurityAnalyzerAgent)

    # Check dependencies
    try:
        import openai
        from .openai_client import OpenAIClientAgent
        agent_registry.register("openai_client")(OpenAIClientAgent)
    except ImportError:
        logger.warning("OpenAI not available, skipping OpenAI agent registration")

    # Check external services
    if check_service_availability("azure_ai"):
        from .azure_ai_client import AzureAIClientAgent
        agent_registry.register("azure_ai_client")(AzureAIClientAgent)
```

### 3. Validation and Testing

Validate agent registration during startup:

```python
def validate_agent_registration():
    """Validate all registered agents."""

    required_agents = [
        "text_processor",
        "data_transformer",
        "security_analyzer",
    ]

    missing_agents = []
    for agent_id in required_agents:
        if agent_id not in agent_registry:
            missing_agents.append(agent_id)

    if missing_agents:
        raise AgentRegistrationError(
            f"Required agents not registered: {missing_agents}",
            error_code="MISSING_REQUIRED_AGENTS"
        )

    # Test agent instantiation
    for agent_id in required_agents:
        try:
            test_config = {"agent_id": agent_id}
            agent = agent_registry.get_agent(agent_id, test_config)
            logger.info(f"Successfully validated agent: {agent_id}")
        except Exception as e:
            logger.error(f"Failed to validate agent {agent_id}: {e}")
            raise
```

### 4. Registry Monitoring

Monitor registry health and performance:

```python
def monitor_registry_health():
    """Monitor registry health and performance."""

    status = agent_registry.get_registry_status()

    # Log registry statistics
    logger.info(f"Registry status: {status}")

    # Check for performance issues
    if status["cached_instances"] > 100:
        logger.warning("High number of cached instances, consider cleanup")

    # Check for memory leaks
    if status["memory_usage"] > threshold:
        logger.error("Registry memory usage exceeds threshold")

    # Validate agent capabilities
    for agent_id in agent_registry.list_agents():
        try:
            agent = agent_registry.get_cached_agent(agent_id, {"agent_id": agent_id})
            capabilities = agent.get_capabilities()

            # Validate capability structure
            required_fields = ["agent_id", "agent_type", "input_types", "output_types"]
            for field in required_fields:
                if field not in capabilities:
                    logger.warning(f"Agent {agent_id} missing capability field: {field}")

        except Exception as e:
            logger.error(f"Failed to validate capabilities for {agent_id}: {e}")
```

## Error Handling and Troubleshooting

### Common Registration Errors

#### Duplicate Agent ID

```python
# Error: Agent ID already registered
try:
    agent_registry.register("existing_agent")(NewAgent)
except AgentRegistrationError as e:
    if e.error_code == "DUPLICATE_AGENT_ID":
        logger.error(f"Agent ID already exists: {e.agent_id}")
        # Options:
        # 1. Use different ID
        # 2. Unregister existing agent first
        # 3. Check if this is expected behavior
```

#### Invalid Agent ID Format

```python
# Error: Invalid agent ID format
try:
    agent_registry.register("invalid-agent-id")(MyAgent)
except AgentRegistrationError as e:
    if e.error_code == "INVALID_AGENT_ID":
        logger.error(f"Invalid agent ID format: {e.message}")
        # Fix: Use snake_case format
        agent_registry.register("invalid_agent_id")(MyAgent)
```

#### Agent Class Validation Failed

```python
# Error: Agent class doesn't inherit from BaseAgent
try:
    agent_registry.register("my_agent")(InvalidClass)
except AgentRegistrationError as e:
    if e.error_code == "INVALID_AGENT_CLASS":
        logger.error(f"Agent class validation failed: {e.message}")
        # Fix: Ensure class inherits from BaseAgent
        class ValidAgent(BaseAgent):
            pass
```

### Debugging Registration Issues

```python
def debug_registration_issues():
    """Debug common registration issues."""

    # Check registry state
    status = agent_registry.get_registry_status()
    print(f"Registry status: {status}")

    # List all registered agents
    agents = agent_registry.list_agents()
    print(f"Registered agents: {agents}")

    # Check agent capabilities
    for agent_id in agents:
        try:
            agent = agent_registry.get_cached_agent(agent_id, {"agent_id": agent_id})
            capabilities = agent.get_capabilities()
            print(f"Agent {agent_id} capabilities: {capabilities}")
        except Exception as e:
            print(f"Error getting capabilities for {agent_id}: {e}")

    # Test agent instantiation
    for agent_id in agents:
        try:
            test_config = {"agent_id": agent_id}
            agent = agent_registry.get_agent(agent_id, test_config)
            print(f"Successfully instantiated: {agent_id}")
        except Exception as e:
            print(f"Failed to instantiate {agent_id}: {e}")
```

## Migration and Versioning

### Agent Versioning

```python
class TextProcessorAgentV2(BaseAgent):
    """Version 2 of the text processor agent."""

    def get_capabilities(self) -> Dict[str, Any]:
        capabilities = super().get_capabilities()
        capabilities.update({
            "version": "2.0.0",
            "deprecated_features": ["old_format_support"],
            "new_features": ["streaming_support", "batch_processing"],
        })
        return capabilities

# Register with versioned ID
agent_registry.register("text_processor_v2")(TextProcessorAgentV2)
```

### Migration Strategies

```python
def migrate_agents():
    """Migrate from old agent registrations to new ones."""

    # Unregister deprecated agents
    deprecated_agents = ["old_text_processor", "legacy_analyzer"]
    for agent_id in deprecated_agents:
        if agent_id in agent_registry:
            agent_registry.unregister(agent_id)
            logger.info(f"Unregistered deprecated agent: {agent_id}")

    # Register new agents
    new_agents = [
        ("text_processor", TextProcessorAgent),
        ("content_analyzer", ContentAnalyzerAgent),
    ]

    for agent_id, agent_class in new_agents:
        agent_registry.register(agent_id)(agent_class)
        logger.info(f"Registered new agent: {agent_id}")
```

## Performance Optimization

### Lazy Loading

```python
class LazyAgentRegistry:
    """Registry with lazy agent loading."""

    def __init__(self):
        self._agent_classes = {}
        self._agent_loaders = {}

    def register_lazy(self, agent_id: str, loader_func: Callable):
        """Register agent with lazy loading."""
        self._agent_loaders[agent_id] = loader_func

    def get_agent(self, agent_id: str, config: Dict[str, Any]):
        """Get agent with lazy loading."""
        if agent_id not in self._agent_classes:
            if agent_id in self._agent_loaders:
                self._agent_classes[agent_id] = self._agent_loaders[agent_id]()
            else:
                raise AgentNotFoundError(f"Agent not found: {agent_id}")

        return self._agent_classes[agent_id](config)

# Usage
def load_text_processor():
    from .text_processor import TextProcessorAgent
    return TextProcessorAgent

lazy_registry = LazyAgentRegistry()
lazy_registry.register_lazy("text_processor", load_text_processor)
```

### Caching Strategies

```python
class CachingAgentRegistry:
    """Registry with intelligent caching."""

    def __init__(self):
        self._instance_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def get_cached_agent(self, agent_id: str, config: Dict[str, Any]):
        """Get cached agent instance."""
        cache_key = self._get_cache_key(agent_id, config)

        if cache_key in self._instance_cache:
            self._cache_hits += 1
            return self._instance_cache[cache_key]

        self._cache_misses += 1
        agent = self.get_agent(agent_id, config)
        self._instance_cache[cache_key] = agent
        return agent

    def _get_cache_key(self, agent_id: str, config: Dict[str, Any]) -> str:
        """Generate cache key for agent configuration."""
        # Only include cache-relevant config fields
        cache_config = {
            k: v for k, v in config.items()
            if k in ["agent_id", "version", "mode"]
        }
        return f"{agent_id}:{hash(frozenset(cache_config.items()))}"
```

## Testing and Validation

### Registration Testing

```python
def test_agent_registration():
    """Test agent registration functionality."""

    # Test successful registration
    @agent_registry.register("test_agent")
    class TestAgent(BaseAgent):
        async def execute(self, agent_input: AgentInput) -> AgentOutput:
            return self._create_output("test result")

    assert "test_agent" in agent_registry

    # Test duplicate registration error
    with pytest.raises(AgentRegistrationError):
        @agent_registry.register("test_agent")
        class DuplicateAgent(BaseAgent):
            pass

    # Test invalid ID format
    with pytest.raises(AgentRegistrationError):
        @agent_registry.register("invalid-id")
        class InvalidIdAgent(BaseAgent):
            pass

    # Cleanup
    agent_registry.unregister("test_agent")
```

### Capability Testing

```python
def test_agent_capabilities():
    """Test agent capability definitions."""

    @agent_registry.register("capability_test_agent")
    class CapabilityTestAgent(BaseAgent):
        def get_capabilities(self) -> Dict[str, Any]:
            return {
                "agent_id": self.agent_id,
                "agent_type": "CapabilityTestAgent",
                "input_types": ["text"],
                "output_types": ["text"],
                "specialization": "testing",
            }

    # Test capability discovery
    text_agents = agent_registry.find_agents_by_type("text")
    assert "capability_test_agent" in text_agents

    testing_agents = agent_registry.find_agents_by_capability("specialization", "testing")
    assert "capability_test_agent" in testing_agents

    # Cleanup
    agent_registry.unregister("capability_test_agent")
```

## Documentation Requirements

### Agent Documentation Template

```python
class ExampleAgent(BaseAgent):
    """
    Example agent for demonstration purposes.

    This agent processes text input and returns analyzed results.
    It demonstrates proper documentation, error handling, and
    capability definition.

    Capabilities:
        - Text processing and analysis
        - Sentiment analysis
        - Entity extraction
        - Content summarization

    Configuration:
        - agent_id: Unique identifier for the agent
        - max_length: Maximum input length (default: 10000)
        - analysis_mode: Analysis mode ("basic" or "advanced")
        - include_entities: Whether to include entity extraction

    Example:
        ```python
        config = {
            "agent_id": "example_agent",
            "max_length": 5000,
            "analysis_mode": "advanced",
            "include_entities": True
        }
        agent = ExampleAgent(config)

        input_data = AgentInput(content="Text to analyze")
        result = await agent.execute(input_data)
        ```

    Raises:
        AgentConfigurationError: If configuration is invalid
        AgentExecutionError: If processing fails
        AgentTimeoutError: If execution times out

    Returns:
        AgentOutput: Analysis results with metadata
    """
```

---

*This document is part of the PromptCraft Agent System documentation suite. For updates and additional information,
refer to the main documentation repository.*
