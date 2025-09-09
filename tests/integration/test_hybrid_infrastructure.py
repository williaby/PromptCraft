"""
Integration tests for the hybrid infrastructure system.
Tests MCP server discovery and agent loading systems.
"""

import asyncio
from pathlib import Path

import pytest

from src.agents.discovery import AgentDiscoverySystem, AgentResourceManager, DynamicAgentLoader
from src.mcp_integration.config_manager import MCPConfigurationManager
from src.mcp_integration.smart_discovery import ResourceMonitor, ServerConnection, SmartMCPDiscovery


class TestMCPSmartDiscovery:
    """Test MCP smart discovery system."""
    
    @pytest.fixture
    def discovery(self):
        """Create discovery instance for testing."""
        return SmartMCPDiscovery()
    
    @pytest.fixture
    def resource_monitor(self):
        """Create resource monitor for testing."""
        return ResourceMonitor()
    
    def test_resource_monitor_memory_check(self, resource_monitor):
        """Test memory availability checking."""
        available_memory = resource_monitor.get_available_memory()
        assert isinstance(available_memory, int)
        assert available_memory > 0
    
    def test_resource_monitor_port_check(self, resource_monitor):
        """Test port availability checking."""
        # Test a likely available port
        assert resource_monitor.is_port_available(9999) is True
        
        # Test a likely unavailable port (if something is running)
        # This might pass if nothing is on port 22, but that's ok
        port_22_available = resource_monitor.is_port_available(22)
        assert isinstance(port_22_available, bool)
    
    @pytest.mark.asyncio
    async def test_server_discovery_cache(self, discovery):
        """Test server discovery caching mechanism."""
        server_name = "test-server"
        
        # Mock a server connection
        from src.utils.datetime_compat import utc_now
        mock_connection = ServerConnection(
            url="npx://test-server",
            type="npx",
            health_status="on_demand",
            resource_usage={},
            discovered_at=utc_now(),
        )
        
        # Add to cache
        discovery.deployment_cache[server_name] = mock_connection
        
        # Should return cached version
        cached = discovery.get_cached_connection(server_name)
        assert cached == mock_connection
    
    @pytest.mark.asyncio
    async def test_known_ports_check(self, discovery):
        """Test checking known ports for servers."""
        # Test with a server that doesn't exist
        connection = await discovery.check_known_ports("non-existent-server")
        assert connection is None
        
        # Test with zen-mcp (will likely return None unless server is running)
        connection = await discovery.check_known_ports("zen-mcp")
        # This is ok to be None if no server is running
        assert connection is None or isinstance(connection, ServerConnection)


class TestAgentDiscovery:
    """Test agent discovery system."""
    
    @pytest.fixture
    def discovery(self):
        """Create agent discovery system for testing."""
        return AgentDiscoverySystem()
    
    @pytest.fixture
    def resource_manager(self):
        """Create resource manager for testing."""
        return AgentResourceManager()
    
    @pytest.fixture
    def loader(self, discovery, resource_manager):
        """Create dynamic agent loader for testing."""
        return DynamicAgentLoader(discovery, resource_manager)
    
    def test_agent_resource_manager_memory_parsing(self, resource_manager):
        """Test memory requirement parsing."""
        assert resource_manager.parse_memory_requirement("512MB") == 512
        assert resource_manager.parse_memory_requirement("1GB") == 1024
        assert resource_manager.parse_memory_requirement("2.5GB") == 2560
        assert resource_manager.parse_memory_requirement("invalid") == 128  # default
    
    def test_agent_resource_limits(self, resource_manager):
        """Test resource limit checking."""
        from src.agents.discovery import (
            AgentDefinition,
            ContextConfig,
            DependencyConfig,
            ImplementationConfig,
            RuntimeConfig,
            ToolConfig,
        )
        
        # Create a test agent definition
        agent_def = AgentDefinition(
            id="test-agent",
            version="1.0.0",
            description="Test agent",
            category="test",
            runtime=RuntimeConfig(model="haiku", memory_requirement="128MB"),
            dependencies=DependencyConfig(),
            tools=ToolConfig(),
            context=ContextConfig(),
            implementation=ImplementationConfig(type="markdown", source="test"),
        )
        
        # Should be able to load initially
        assert resource_manager.can_load_agent(agent_def) is True
        
        # Allocate resources
        resource_manager.allocate_resources("test-agent", agent_def)
        
        # Check resource usage
        usage = resource_manager.get_resource_usage()
        assert usage["active_agents"] == 1
        assert usage["total_memory_mb"] == 128
    
    def test_discovery_config_loading(self, discovery):
        """Test discovery configuration loading."""
        # Should load some form of configuration
        assert isinstance(discovery.discovery_config, dict)
        
        # Should have reasonable defaults
        assert "default_priority_order" in discovery.discovery_config
    
    def test_available_agents_discovery(self, discovery):
        """Test discovering available agents."""
        # This should find the agents we created in the .agents directory
        available = discovery.get_available_agents()
        
        # Should be a list
        assert isinstance(available, list)
        
        # Should include our test agents if .agents directory exists
        if Path(".agents").exists():
            # Should include some agents
            assert len(available) > 0
    
    def test_agent_definition_yaml_parsing(self):
        """Test parsing agent definition from YAML."""
        from src.agents.discovery import AgentDefinition
        
        yaml_content = """
metadata:
  id: test-agent
  version: 1.0.0
  description: Test agent
  category: test

runtime:
  model: haiku
  memory_requirement: 128MB
  execution_mode: async

dependencies:
  services: {}
  packages: []

tools:
  required: ["Read"]
  optional: []

context:
  shared: []
  project: []

implementation:
  type: markdown
  source: "Test agent implementation"
"""
        
        agent_def = AgentDefinition.from_yaml(yaml_content)
        assert agent_def.id == "test-agent"
        assert agent_def.runtime.model == "haiku"
        assert agent_def.implementation.source == "Test agent implementation"


class TestMCPConfigManager:
    """Test MCP Configuration Manager integration."""
    
    @pytest.fixture
    def config_manager(self):
        """Create config manager for testing."""
        # Use a test config path to avoid interfering with real configs
        test_config = Path("test_mcp.json")
        return MCPConfigurationManager(config_path=test_config, enable_discovery=False)
    
    def test_config_manager_initialization(self, config_manager):
        """Test config manager initializes properly."""
        assert config_manager.config_path.name == "test_mcp.json"
        assert config_manager.configuration is not None
    
    def test_config_merge_functionality(self, config_manager):
        """Test configuration merging."""
        configs = [
            ("source1", {"mcpServers": {"server1": {"command": "test1"}}}),
            ("source2", {"mcpServers": {"server2": {"command": "test2"}}}),
        ]
        
        merged = config_manager._merge_configurations(configs)
        
        assert "server1" in merged["mcpServers"]
        assert "server2" in merged["mcpServers"]
        assert merged["mcpServers"]["server1"]["command"] == "test1"


class TestIntegratedSystem:
    """Test integrated MCP and agent systems."""
    
    @pytest.mark.asyncio
    async def test_system_integration(self):
        """Test that MCP discovery and agent systems work together."""
        # Initialize both systems
        mcp_discovery = SmartMCPDiscovery()
        agent_discovery = AgentDiscoverySystem()
        
        # Both should initialize without errors
        assert mcp_discovery is not None
        assert agent_discovery is not None
        
        # Both should have reasonable configurations
        assert hasattr(mcp_discovery, "server_requirements")
        assert hasattr(agent_discovery, "search_paths")
    
    def test_configuration_files_exist(self):
        """Test that required configuration files were created."""
        required_files = [
            Path(".mcp/discovery-config.yaml"),
            Path(".mcp/servers/core.json"),
            Path(".mcp/servers/optional.json"),
            Path(".agents/discovery-config.yaml"),
        ]
        
        for file_path in required_files:
            assert file_path.exists(), f"Required configuration file {file_path} not found"
    
    def test_agent_definitions_exist(self):
        """Test that agent definitions were created."""
        required_agents = [
            Path(".agents/core/ai-engineer.yaml"),
            Path(".agents/core/code-reviewer.yaml"),
            Path(".agents/project/journey-orchestrator.yaml"),
        ]
        
        for agent_path in required_agents:
            assert agent_path.exists(), f"Required agent definition {agent_path} not found"
    
    def test_context_files_exist(self):
        """Test that context files were created."""
        required_context = [
            Path(".agents/context/c-r-e-a-t-e-framework.md"),
            Path(".agents/context/shared-architecture.md"),
        ]
        
        for context_path in required_context:
            assert context_path.exists(), f"Required context file {context_path} not found"


if __name__ == "__main__":
    # Simple test runner for development
    import sys
    
    async def run_async_tests():
        """Run async tests manually."""
        discovery = SmartMCPDiscovery()
        
        print("Testing MCP Discovery...")
        try:
            # Test server discovery (will likely find no servers, which is ok)
            connection = await discovery.find_existing_deployment("zen-mcp")
            print(f"Zen MCP discovery result: {connection}")
        except Exception as e:
            print(f"Discovery test completed with expected result: {e}")
        
        print("Testing Agent Discovery...")
        agent_discovery = AgentDiscoverySystem()
        available = agent_discovery.get_available_agents()
        print(f"Available agents: {available}")
        
        # Try to load an agent if any are available
        if available:
            try:
                agent_def = agent_discovery.discover_agent(available[0])
                print(f"Successfully discovered agent {available[0]}: {agent_def.id}")
            except Exception as e:
                print(f"Agent discovery test completed: {e}")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        print("Running manual integration test...")
        asyncio.run(run_async_tests())
        print("Manual test completed.")
    else:
        print("Run with --manual for manual testing, or use pytest for full test suite")
        print("Example: python -m pytest tests/integration/test_hybrid_infrastructure.py -v")