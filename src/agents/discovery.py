from src.utils.datetime_compat import utc_now


"""
Agent Discovery and Loading System

Intelligent discovery system for agents with cascade loading,
resource management, and dynamic instantiation.
"""

from dataclasses import dataclass, field
from datetime import timedelta
import importlib
import logging
import os
from pathlib import Path
from typing import Any

import yaml

from src.utils.logging_mixin import LoggerMixin

from .base_agent import BaseAgent


logger = logging.getLogger(__name__)


@dataclass
class AgentDefinition:
    """Complete agent definition with metadata and implementation."""

    id: str
    version: str
    description: str
    category: str
    runtime: "RuntimeConfig"
    dependencies: "DependencyConfig"
    tools: "ToolConfig"
    context: "ContextConfig"
    implementation: "ImplementationConfig"

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "AgentDefinition":
        """Create AgentDefinition from YAML content."""
        data = yaml.safe_load(yaml_content)

        return cls(
            id=data["metadata"]["id"],
            version=data["metadata"]["version"],
            description=data["metadata"]["description"],
            category=data["metadata"]["category"],
            runtime=RuntimeConfig(**data["runtime"]),
            dependencies=DependencyConfig(**data.get("dependencies", {})),
            tools=ToolConfig(**data["tools"]),
            context=ContextConfig(**data.get("context", {})),
            implementation=ImplementationConfig(**data["implementation"]),
        )


@dataclass
class RuntimeConfig:
    """Runtime configuration for agents."""

    model: str
    fallback_models: list[str] = field(default_factory=list)
    memory_requirement: str = "128MB"
    execution_mode: str = "async"
    timeout: int = 300


@dataclass
class DependencyConfig:
    """Dependencies configuration."""

    services: dict[str, str] = field(default_factory=dict)
    packages: list[str] = field(default_factory=list)


@dataclass
class ToolConfig:
    """Tools configuration."""

    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)


@dataclass
class ContextConfig:
    """Context configuration."""

    shared: list[str] = field(default_factory=list)
    project: list[str] = field(default_factory=list)


@dataclass
class ImplementationConfig:
    """Implementation configuration."""

    type: str  # 'markdown', 'python', 'javascript', 'remote'
    source: str | None = None
    module: str | None = None
    class_name: str | None = None
    url: str | None = None


class AgentResourceManager:
    """Manage agent resources and prevent conflicts."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.AgentResourceManager")
        self.active_agents: dict[str, dict[str, Any]] = {}
        self.resource_limits = {
            "total_memory": 2048,  # MB
            "max_concurrent": 10,
            "model_limits": {
                "opus": 3,
                "sonnet": 8,
                "haiku": 15,
            },
        }

    def parse_memory_requirement(self, requirement: str) -> int:
        """Parse memory requirement string to MB."""
        requirement = requirement.upper().replace(" ", "")
        if requirement.endswith("GB"):
            return int(float(requirement[:-2]) * 1024)
        if requirement.endswith("MB"):
            return int(requirement[:-2])
        if requirement.endswith("KB"):
            return int(int(requirement[:-2]) / 1024)
        return 128  # Default 128MB

    def can_load_agent(self, agent_def: AgentDefinition) -> bool:
        """Check if resources available for agent."""

        # Check concurrent agent limit
        max_concurrent: int = self.resource_limits["max_concurrent"]  # type: ignore[assignment]
        if len(self.active_agents) >= max_concurrent:
            return False

        # Check memory
        current_usage = sum(self.parse_memory_requirement(agent["memory"]) for agent in self.active_agents.values())
        required = self.parse_memory_requirement(agent_def.runtime.memory_requirement)
        total_memory: int = self.resource_limits["total_memory"]  # type: ignore[assignment]
        if current_usage + required > total_memory:
            return False

        # Check model limits
        model = agent_def.runtime.model
        active_count = sum(1 for agent in self.active_agents.values() if agent["model"] == model)
        model_limits: dict[str, int] = self.resource_limits["model_limits"]  # type: ignore[assignment]
        return not active_count >= model_limits.get(model, 1)

    def allocate_resources(self, agent_id: str, agent_def: AgentDefinition) -> None:
        """Reserve resources for agent."""
        self.active_agents[agent_id] = {
            "memory": agent_def.runtime.memory_requirement,
            "model": agent_def.runtime.model,
            "started_at": utc_now(),
            "category": agent_def.category,
        }
        self.logger.info("Allocated resources for agent %s", agent_id)

    def release_resources(self, agent_id: str) -> None:
        """Release resources for agent."""
        if agent_id in self.active_agents:
            del self.active_agents[agent_id]
            self.logger.info("Released resources for agent %s", agent_id)

    def get_resource_usage(self) -> dict[str, Any]:
        """Get current resource usage statistics."""
        total_memory = sum(self.parse_memory_requirement(agent["memory"]) for agent in self.active_agents.values())

        model_usage: dict[str, int] = {}
        for agent in self.active_agents.values():
            model = agent["model"]
            model_usage[model] = model_usage.get(model, 0) + 1

        return {
            "active_agents": len(self.active_agents),
            "total_memory_mb": total_memory,
            "memory_utilization": (
                total_memory / int(str(self.resource_limits["total_memory"]))
                if self.resource_limits["total_memory"]
                else 0
            ),
            "model_usage": model_usage,
            "agent_details": dict(self.active_agents),
        }


class AgentDiscoverySystem(LoggerMixin):
    """Intelligent agent discovery with cascade loading."""

    def __init__(self) -> None:
        super().__init__()
        self.search_paths = [
            Path.home() / ".claude/agents",  # User-level
            Path.cwd() / ".agents",  # Project-level
            Path(__file__).parent / "defaults",  # Bundled defaults
        ]
        self.remote_registry = os.getenv("AGENT_REGISTRY_URL", "https://agents.promptcraft.ai")
        self.loaded_agents: dict[str, AgentDefinition] = {}
        self.agent_cache_ttl = timedelta(minutes=30)
        self.discovery_config = self._load_discovery_config()

    def _load_discovery_config(self) -> dict[str, Any]:
        """Load discovery configuration."""
        config_path = Path(".agents/discovery-config.yaml")
        if config_path.exists():
            try:
                result = yaml.safe_load(config_path.read_text())
                return result if isinstance(result, dict) else {}
            except Exception as e:
                self.logger.warning("Failed to load discovery config: %s", e)

        # Default configuration
        return {
            "default_priority_order": [
                "user_override",
                "project_specific",
                "bundled_default",
                "remote_registry",
            ],
            "cache_ttl_minutes": 30,
            "max_remote_agents": 5,
        }

    def discover_agent(self, agent_id: str) -> AgentDefinition:
        """Discover agent with intelligent fallback."""

        # 1. Check cache
        if agent_id in self.loaded_agents:
            self.logger.debug("Using cached definition for agent %s", agent_id)
            return self.loaded_agents[agent_id]

        # 2. Search in priority order
        priority_order = self.discovery_config.get("default_priority_order", [])

        for search_strategy in priority_order:
            try:
                if agent_def := self._search_by_strategy(agent_id, search_strategy):
                    # Validate dependencies
                    if self.validate_dependencies(agent_def):
                        self.loaded_agents[agent_id] = agent_def
                        self.logger.info("Discovered agent %s via %s", agent_id, search_strategy)
                        return agent_def
                    self.logger.warning("Agent %s dependencies not satisfied", agent_id)
            except Exception as e:
                self.logger.debug("Search strategy %s failed for %s: %s", search_strategy, agent_id, e)

        raise AgentNotFoundError(f"Agent {agent_id} not found in any search location")

    def _search_by_strategy(self, agent_id: str, strategy: str) -> AgentDefinition | None:
        """Search for agent using specific strategy."""

        if strategy == "user_override":
            return self._search_user_level(agent_id)
        if strategy == "project_specific":
            return self._search_project_level(agent_id)
        if strategy == "bundled_default":
            return self._search_bundled_defaults(agent_id)
        if strategy == "remote_registry":
            return self._search_remote_registry(agent_id)
        self.logger.warning("Unknown search strategy: %s", strategy)
        return None

    def _search_user_level(self, agent_id: str) -> AgentDefinition | None:
        """Search user-level agent definitions."""
        user_path = Path.home() / ".claude/agents"

        # Check both .md and .yaml formats
        for ext in [".md", ".yaml", ".yml"]:
            agent_file = user_path / f"{agent_id}{ext}"
            if agent_file.exists():
                content = agent_file.read_text()
                if ext == ".md":
                    return self._parse_markdown_agent(content)
                return AgentDefinition.from_yaml(content)

        return None

    def _search_project_level(self, agent_id: str) -> AgentDefinition | None:
        """Search project-level agent definitions."""
        project_paths = [
            Path(".agents/core"),
            Path(".agents/project"),
        ]

        for search_path in project_paths:
            for ext in [".yaml", ".yml"]:
                agent_file = search_path / f"{agent_id}{ext}"
                if agent_file.exists():
                    content = agent_file.read_text()
                    return AgentDefinition.from_yaml(content)

        return None

    def _search_bundled_defaults(self, agent_id: str) -> AgentDefinition | None:
        """Search bundled default agent definitions."""
        defaults_path = Path(".agents/defaults")

        for ext in [".yaml", ".yml"]:
            agent_file = defaults_path / f"{agent_id}{ext}"
            if agent_file.exists():
                content = agent_file.read_text()
                return AgentDefinition.from_yaml(content)

        return None

    def _search_remote_registry(self, agent_id: str) -> AgentDefinition | None:
        """Search remote agent registry."""
        # For now, this is a placeholder
        # In production, this would fetch from a remote registry
        self.logger.debug("Remote registry search not implemented for %s", agent_id)
        return None

    def _parse_markdown_agent(self, content: str) -> AgentDefinition:
        """Parse agent definition from markdown format (legacy)."""
        # Extract YAML frontmatter
        if content.startswith("---\n"):
            try:
                end_idx = content.find("\n---\n", 4)
                if end_idx != -1:
                    frontmatter = content[4:end_idx]
                    markdown_content = content[end_idx + 5 :]

                    metadata = yaml.safe_load(frontmatter)

                    # Convert to new format
                    return AgentDefinition(
                        id=metadata.get("name", "unknown"),
                        version="1.0.0",
                        description=metadata.get("description", ""),
                        category="legacy",
                        runtime=RuntimeConfig(
                            model=metadata.get("model", "haiku"),
                            memory_requirement="128MB",
                        ),
                        dependencies=DependencyConfig(),
                        tools=ToolConfig(
                            required=metadata.get("tools", []),
                        ),
                        context=ContextConfig(
                            shared=metadata.get("context_refs", []),
                        ),
                        implementation=ImplementationConfig(
                            type="markdown",
                            source=markdown_content,
                        ),
                    )
            except Exception as e:
                self.logger.error("Failed to parse markdown agent: %s", e)

        # Fallback for plain markdown
        return AgentDefinition(
            id="unknown",
            version="1.0.0",
            description="Legacy markdown agent",
            category="legacy",
            runtime=RuntimeConfig(model="haiku"),
            dependencies=DependencyConfig(),
            tools=ToolConfig(),
            context=ContextConfig(),
            implementation=ImplementationConfig(
                type="markdown",
                source=content,
            ),
        )

    def validate_dependencies(self, agent_def: AgentDefinition) -> bool:
        """Check if agent dependencies are available."""
        for service, endpoint in agent_def.dependencies.services.items():
            if service == "qdrant":
                if not self._check_qdrant_availability(endpoint):
                    self.logger.warning("Qdrant not available at %s", endpoint)
                    return False
            elif service == "zen_mcp":
                if not self._check_mcp_availability():
                    self.logger.warning("Zen MCP server not available")
                    return False

        return True

    def _check_qdrant_availability(self, endpoint: str) -> bool:
        """Check if Qdrant is available."""
        try:
            import requests

            response = requests.get(f"http://{endpoint}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _check_mcp_availability(self) -> bool:
        """Check if MCP server is available."""
        # This would integrate with the MCP discovery system
        return True  # Placeholder

    def get_available_agents(self) -> list[str]:
        """Get list of all discoverable agents."""
        agents = set()

        for search_path in self.search_paths:
            if search_path.exists():
                for file_path in search_path.rglob("*.yaml"):
                    agents.add(file_path.stem)
                for file_path in search_path.rglob("*.yml"):
                    agents.add(file_path.stem)
                for file_path in search_path.rglob("*.md"):
                    agents.add(file_path.stem)

        return sorted(agents)


class DynamicAgentLoader(LoggerMixin):
    """Load agents from various sources dynamically."""

    def __init__(self, discovery: AgentDiscoverySystem, resource_manager: AgentResourceManager) -> None:
        super().__init__()
        self.discovery = discovery
        self.resource_manager = resource_manager
        self.loaded_instances: dict[str, BaseAgent] = {}

    def load_agent(self, agent_id: str, config: dict[str, Any]) -> BaseAgent:
        """Load agent with appropriate implementation."""

        # Check if already loaded
        if agent_id in self.loaded_instances:
            return self.loaded_instances[agent_id]

        # Discover agent definition
        agent_def = self.discovery.discover_agent(agent_id)

        # Check resource availability
        if not self.resource_manager.can_load_agent(agent_def):
            raise ResourceError(f"Insufficient resources to load agent {agent_id}")

        # Choose implementation strategy
        try:
            if agent_def.implementation.type == "python":
                agent = self.load_python_agent(agent_def, config)
            elif agent_def.implementation.type == "markdown":
                agent = self.load_markdown_agent(agent_def, config)
            elif agent_def.implementation.type == "remote":
                agent = self.load_remote_agent(agent_def, config)
            else:
                raise ValueError(f"Unknown implementation type: {agent_def.implementation.type}")

            # Allocate resources
            self.resource_manager.allocate_resources(agent_id, agent_def)
            self.loaded_instances[agent_id] = agent

            return agent

        except Exception as e:
            self.logger.error(f"Failed to load agent {agent_id}: {e}")
            raise

    def load_markdown_agent(self, agent_def: AgentDefinition, config: dict[str, Any]) -> BaseAgent:
        """Create agent from markdown definition."""
        from .markdown_agent import MarkdownAgent

        # Load context files
        context_content = self.load_context(agent_def.context)

        source = agent_def.implementation.source
        if source is None:
            raise ValueError(f"Agent {agent_def.id} has no implementation source")

        return MarkdownAgent(
            agent_id=agent_def.id,
            definition=source,
            model=agent_def.runtime.model,
            tools=agent_def.tools.required,
            context=context_content,
            config=config,
        )

    def load_python_agent(self, agent_def: AgentDefinition, config: dict[str, Any]) -> BaseAgent:
        """Import and instantiate Python agent class."""
        if not agent_def.implementation.module or not agent_def.implementation.class_name:
            raise ValueError(f"Python agent {agent_def.id} missing module or class name")

        try:
            module = importlib.import_module(agent_def.implementation.module)
            agent_class = getattr(module, agent_def.implementation.class_name)
            instance = agent_class(config)
            return instance  # type: ignore[no-any-return]
        except Exception as e:
            raise ImportError(f"Failed to load Python agent {agent_def.id}: {e}")

    def load_remote_agent(self, agent_def: AgentDefinition, config: dict[str, Any]) -> BaseAgent:
        """Load remote agent via API."""
        # This would be implemented for remote agents
        raise NotImplementedError("Remote agent loading not yet implemented")

    def load_context(self, context_config: ContextConfig) -> str:
        """Load and combine context files."""
        context_parts = []

        # Load shared context
        for context_ref in context_config.shared:
            context_file = Path(context_ref.lstrip("/"))
            if context_file.exists():
                context_parts.append(context_file.read_text())

        # Load project context
        for context_ref in context_config.project:
            context_file = Path(context_ref.lstrip("./"))
            if context_file.exists():
                context_parts.append(context_file.read_text())

        return "\n\n---\n\n".join(context_parts)

    def unload_agent(self, agent_id: str) -> None:
        """Unload agent and free resources."""
        if agent_id in self.loaded_instances:
            del self.loaded_instances[agent_id]
            self.resource_manager.release_resources(agent_id)
            self.logger.info(f"Unloaded agent {agent_id}")


class AgentNotFoundError(Exception):
    """Raised when an agent cannot be found."""


class ResourceError(Exception):
    """Raised when insufficient resources are available."""
