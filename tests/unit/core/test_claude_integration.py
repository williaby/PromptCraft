"""
Comprehensive test suite for claude_integration.py

Tests the Claude Code integration layer including command registration,
execution, analytics tracking, and health monitoring functionality.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.claude_integration import (
    ClaudeCodeCommandFactory,
    ClaudeCommandIntegration,
    CommandMetadata,
    CommandRegistry,
    IntegrationStatus,
)
from src.core.user_control_system import CommandResult


class TestCommandMetadata:
    """Test CommandMetadata dataclass functionality."""

    def test_command_metadata_creation(self):
        """Test CommandMetadata creation with all fields."""
        metadata = CommandMetadata(
            name="test-command",
            category="test",
            complexity="medium",
            estimated_time="< 2 minutes",
            dependencies=["dep1", "dep2"],
            sub_commands=["sub1", "sub2"],
            version="2.0",
            tags=["tag1", "tag2"],
        )

        assert metadata.name == "test-command"
        assert metadata.category == "test"
        assert metadata.complexity == "medium"
        assert metadata.estimated_time == "< 2 minutes"
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.sub_commands == ["sub1", "sub2"]
        assert metadata.version == "2.0"
        assert metadata.tags == ["tag1", "tag2"]

    def test_command_metadata_defaults(self):
        """Test CommandMetadata with default values."""
        metadata = CommandMetadata(
            name="simple-command", category="basic", complexity="low", estimated_time="< 1 minute",
        )

        assert metadata.dependencies == []
        assert metadata.sub_commands == []
        assert metadata.version == "1.0"
        assert metadata.tags == []


class TestIntegrationStatus:
    """Test IntegrationStatus dataclass functionality."""

    def test_integration_status_defaults(self):
        """Test IntegrationStatus default values."""
        status = IntegrationStatus()

        assert not status.user_control_active
        assert not status.help_system_active
        assert not status.analytics_active
        assert not status.detection_system_active
        assert status.command_count == 0
        assert status.last_health_check is None
        assert status.error_count == 0

    def test_integration_status_with_values(self):
        """Test IntegrationStatus with explicit values."""
        now = datetime.now()
        status = IntegrationStatus(
            user_control_active=True,
            help_system_active=True,
            analytics_active=True,
            detection_system_active=True,
            command_count=10,
            last_health_check=now,
            error_count=2,
        )

        assert status.user_control_active
        assert status.help_system_active
        assert status.analytics_active
        assert status.detection_system_active
        assert status.command_count == 10
        assert status.last_health_check == now
        assert status.error_count == 2


class TestCommandRegistry:
    """Test CommandRegistry functionality."""

    def test_command_registry_initialization(self):
        """Test CommandRegistry initialization."""
        registry = CommandRegistry()

        assert registry.commands == {}
        assert "meta" in registry.categories
        assert "workflow" in registry.categories
        assert "function_control" in registry.categories
        assert registry.aliases == {}

    def test_register_command_basic(self):
        """Test basic command registration."""
        registry = CommandRegistry()
        handler = MagicMock()
        metadata = CommandMetadata(name="test-cmd", category="meta", complexity="low", estimated_time="< 1 minute")

        registry.register_command("test-cmd", handler, metadata)

        assert "test-cmd" in registry.commands
        assert registry.commands["test-cmd"]["handler"] == handler
        assert registry.commands["test-cmd"]["metadata"] == metadata
        assert isinstance(registry.commands["test-cmd"]["registered_at"], datetime)
        assert "test-cmd" in registry.categories["meta"]

    def test_register_command_with_aliases(self):
        """Test command registration with aliases."""
        registry = CommandRegistry()
        handler = MagicMock()
        metadata = CommandMetadata(
            name="long-command-name", category="workflow", complexity="medium", estimated_time="< 2 minutes",
        )
        aliases = ["short", "lcn"]

        registry.register_command("long-command-name", handler, metadata, aliases)

        assert registry.aliases["short"] == "long-command-name"
        assert registry.aliases["lcn"] == "long-command-name"

    def test_get_command_by_name(self):
        """Test getting command by direct name."""
        registry = CommandRegistry()
        handler = MagicMock()
        metadata = CommandMetadata(
            name="direct-cmd", category="validation", complexity="low", estimated_time="< 1 minute",
        )

        registry.register_command("direct-cmd", handler, metadata)
        result = registry.get_command("direct-cmd")

        assert result is not None
        assert result["handler"] == handler
        assert result["metadata"] == metadata

    def test_get_command_by_alias(self):
        """Test getting command by alias."""
        registry = CommandRegistry()
        handler = MagicMock()
        metadata = CommandMetadata(
            name="aliased-command", category="creation", complexity="high", estimated_time="< 5 minutes",
        )

        registry.register_command("aliased-command", handler, metadata, ["alias"])
        result = registry.get_command("alias")

        assert result is not None
        assert result["handler"] == handler
        assert result["metadata"] == metadata

    def test_get_command_not_found(self):
        """Test getting non-existent command."""
        registry = CommandRegistry()

        result = registry.get_command("nonexistent")
        assert result is None

    def test_list_commands_by_category(self):
        """Test listing commands by category."""
        registry = CommandRegistry()
        handler1 = MagicMock()
        handler2 = MagicMock()

        metadata1 = CommandMetadata("cmd1", "test_category", "low", "< 1 minute")
        metadata2 = CommandMetadata("cmd2", "test_category", "medium", "< 2 minutes")

        registry.register_command("cmd1", handler1, metadata1)
        registry.register_command("cmd2", handler2, metadata2)

        # Add test_category to registry categories
        registry.categories["test_category"] = []
        registry.register_command("cmd1", handler1, metadata1)
        registry.register_command("cmd2", handler2, metadata2)

        commands = registry.list_commands_by_category("test_category")
        assert "cmd1" in commands
        assert "cmd2" in commands

    def test_search_commands_by_name(self):
        """Test searching commands by name."""
        registry = CommandRegistry()
        handler = MagicMock()
        metadata = CommandMetadata(
            name="searchable-command", category="meta", complexity="low", estimated_time="< 1 minute",
        )

        registry.register_command("searchable-command", handler, metadata)

        results = registry.search_commands("search")
        assert "searchable-command" in results

    def test_search_commands_by_tags(self):
        """Test searching commands by tags."""
        registry = CommandRegistry()
        handler = MagicMock()
        metadata = CommandMetadata(
            name="tagged-command",
            category="workflow",
            complexity="medium",
            estimated_time="< 2 minutes",
            tags=["special-tag", "useful"],
        )

        registry.register_command("tagged-command", handler, metadata)

        results = registry.search_commands("special")
        assert "tagged-command" in results

    def test_search_commands_no_results(self):
        """Test searching with no matching commands."""
        registry = CommandRegistry()

        results = registry.search_commands("nonexistent-term")
        assert results == []


class TestClaudeCommandIntegration:
    """Test ClaudeCommandIntegration functionality."""

    @pytest.fixture
    def mock_systems(self):
        """Create mock system dependencies."""
        control_system = MagicMock()
        help_system = MagicMock()
        analytics = MagicMock()

        # Setup return values for system initialization
        analytics.track_user_action = MagicMock()
        analytics.get_user_analytics = MagicMock(
            return_value={
                "user_id": "test_user",
                "analysis_period_days": 30,
                "total_events": 25,
                "error_rate": 0.1,
                "patterns_detected": 3,
                "recommendations": ["rec1", "rec2", "rec3"],
                "optimization_insights": ["insight1", "insight2"],
            },
        )
        analytics.get_system_analytics = MagicMock(return_value={"total_events": 100, "active_users": 5})

        help_system.get_help = MagicMock(
            return_value=CommandResult(success=True, message="Help content", data={"help_content": "Test help"}),
        )
        help_system.content_generator = MagicMock()
        help_system.content_generator.help_topics = {"topic1": "content1"}
        help_system.content_generator.learning_paths = {"path1": "learning1"}

        return control_system, help_system, analytics

    @pytest.fixture
    def integration(self, mock_systems):
        """Create ClaudeCommandIntegration instance with mocked dependencies."""
        control_system, help_system, analytics = mock_systems
        return ClaudeCommandIntegration(control_system, help_system, analytics)

    def test_integration_initialization(self, integration, mock_systems):
        """Test ClaudeCommandIntegration initialization."""
        control_system, help_system, analytics = mock_systems

        assert integration.control_system == control_system
        assert integration.help_system == help_system
        assert integration.analytics == analytics
        assert isinstance(integration.command_registry, CommandRegistry)
        assert isinstance(integration.integration_status, IntegrationStatus)
        assert integration.active_session_id is None
        assert integration.command_history == []
        assert integration.performance_metrics == {}

    def test_initialization_registers_commands(self, integration):
        """Test that initialization registers all user control commands."""
        assert integration.integration_status.command_count > 0
        assert integration.integration_status.user_control_active

        # Check some specific commands are registered
        assert integration.command_registry.get_command("function-loading:load-category") is not None
        assert integration.command_registry.get_command("function-loading:help") is not None
        assert integration.command_registry.get_command("function-loading:analytics") is not None

    def test_parse_command_line_project_format(self, integration):
        """Test parsing /project: command format."""
        result = integration._parse_command_line("/project:test-command arg1 arg2")

        assert result["command"] == "test-command"
        assert result["arguments"] == ["arg1", "arg2"]

    def test_parse_command_line_slash_format(self, integration):
        """Test parsing / command format."""
        result = integration._parse_command_line("/user-command param1 param2")

        assert result["command"] == "user-command"
        assert result["arguments"] == ["param1", "param2"]

    def test_parse_command_line_colon_format(self, integration):
        """Test parsing command:subcommand format."""
        result = integration._parse_command_line("module:action param1")

        assert result["command"] == "module:action"
        assert result["arguments"] == ["param1"]

    def test_parse_command_line_simple_format(self, integration):
        """Test parsing simple command format."""
        result = integration._parse_command_line("simple param1 param2")

        assert result["command"] == "simple"
        assert result["arguments"] == ["param1", "param2"]

    def test_parse_command_line_empty(self, integration):
        """Test parsing empty command line."""
        result = integration._parse_command_line("")

        assert result["command"] == ""
        assert result["arguments"] == []

    @pytest.mark.asyncio
    async def test_execute_command_success(self, integration, mock_systems):
        """Test successful command execution."""
        control_system, _, _ = mock_systems

        # Mock a registered command
        mock_handler = AsyncMock(
            return_value=CommandResult(success=True, message="Command executed successfully", data={"result": "test"}),
        )

        metadata = CommandMetadata("test-cmd", "meta", "low", "< 1 minute")
        integration.command_registry.register_command("test-cmd", mock_handler, metadata)

        result = await integration.execute_command("test-cmd arg1")

        assert result.success
        assert result.message == "Command executed successfully"
        mock_handler.assert_called_once_with(["arg1"], {})

    @pytest.mark.asyncio
    async def test_execute_command_unknown_command(self, integration, mock_systems):
        """Test execution of unknown command."""
        control_system, _, _ = mock_systems
        control_system.execute_command = AsyncMock(return_value=CommandResult(success=False, message="Unknown command"))

        result = await integration.execute_command("/unknown-command")

        assert not result.success
        control_system.execute_command.assert_called_once_with("/unknown-command")

    @pytest.mark.asyncio
    async def test_execute_command_fallback_to_control_system(self, integration, mock_systems):
        """Test fallback to control system for unknown commands."""
        control_system, _, _ = mock_systems
        control_system.execute_command = AsyncMock(
            return_value=CommandResult(success=True, message="Handled by control system"),
        )

        result = await integration.execute_command("/control-system-command")

        assert result.success
        control_system.execute_command.assert_called_once_with("/control-system-command")

    @pytest.mark.asyncio
    async def test_execute_command_with_context(self, integration, mock_systems):
        """Test command execution with context."""
        mock_handler = AsyncMock(return_value=CommandResult(success=True, message="OK"))
        metadata = CommandMetadata("context-cmd", "meta", "low", "< 1 minute")
        integration.command_registry.register_command("context-cmd", mock_handler, metadata)

        context = {"user_id": "test_user", "session": "test_session"}
        result = await integration.execute_command("context-cmd", context)

        assert result.success
        mock_handler.assert_called_once_with([], context)

    @pytest.mark.asyncio
    async def test_execute_command_error_handling(self, integration):
        """Test command execution error handling."""
        # Register a command that raises an exception
        mock_handler = AsyncMock(side_effect=Exception("Test error"))
        metadata = CommandMetadata("error-cmd", "meta", "low", "< 1 minute")
        integration.command_registry.register_command("error-cmd", mock_handler, metadata)

        result = await integration.execute_command("error-cmd")

        assert not result.success
        assert "Command execution error" in result.message
        assert "Test error" in result.message

    def test_track_command_start(self, integration, mock_systems):
        """Test command execution tracking start."""
        _, _, analytics = mock_systems

        context = {"user_id": "test_user"}
        integration._track_command_start("test-command", context)

        assert integration.active_session_id is not None
        analytics.track_user_action.assert_called_once()

    def test_track_command_end(self, integration, mock_systems):
        """Test command execution tracking end."""
        _, _, analytics = mock_systems

        integration.active_session_id = "test_session"
        result = CommandResult(success=True, message="Test")

        integration._track_command_end("test-command", result)

        analytics.track_user_action.assert_called_once()
        assert len(integration.command_history) == 1
        assert integration.command_history[0]["command"] == "test-command"
        assert integration.command_history[0]["success"]

    def test_track_command_end_no_session(self, integration, mock_systems):
        """Test command end tracking without active session."""
        _, _, analytics = mock_systems

        result = CommandResult(success=True, message="Test")
        integration._track_command_end("test-command", result)

        # Should not call analytics without active session
        analytics.track_user_action.assert_not_called()

    def test_command_history_management(self, integration):
        """Test command history size management."""
        integration.active_session_id = "test_session"

        # Add more than 100 commands to trigger history management
        for i in range(105):
            entry = {"timestamp": datetime.now(), "command": f"command-{i}", "success": True, "message": f"Message {i}"}
            integration.command_history.append(entry)

        # Trigger history management by calling _track_command_end
        result = CommandResult(success=True, message="Final command")
        integration._track_command_end("final-command", result)

        # Should keep only last 50 + 1 new command = 51
        assert len(integration.command_history) == 51

    def test_suggest_similar_commands(self, integration):
        """Test similar command suggestions."""
        # Test with function loading related terms
        suggestions = integration._suggest_similar_commands("load")

        assert len(suggestions) <= 5
        assert any("load-category" in cmd for cmd in suggestions)

    def test_suggest_similar_commands_empty(self, integration):
        """Test similar command suggestions with no matches."""
        suggestions = integration._suggest_similar_commands("xyz123")

        # Should return empty list or at most function loading commands
        assert len(suggestions) <= 5

    @pytest.mark.asyncio
    async def test_handle_load_category_success(self, integration, mock_systems):
        """Test successful load-category command handling."""
        control_system, _, analytics = mock_systems
        control_system.execute_command = AsyncMock(
            return_value=CommandResult(success=True, message="Category loaded", data={"token_cost": 1000}),
        )

        result = await integration._handle_load_category(["security"], {"user_id": "test"})

        assert result.success
        control_system.execute_command.assert_called_once_with("/load-category security")
        analytics.track_user_action.assert_called()

    @pytest.mark.asyncio
    async def test_handle_load_category_no_args(self, integration, mock_systems):
        """Test load-category command with missing arguments."""
        result = await integration._handle_load_category([], {})

        assert not result.success
        assert "Category name required" in result.message
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_handle_unload_category_success(self, integration, mock_systems):
        """Test successful unload-category command handling."""
        control_system, _, analytics = mock_systems
        control_system.execute_command = AsyncMock(
            return_value=CommandResult(success=True, message="Category unloaded", data={"tokens_saved": 500}),
        )

        result = await integration._handle_unload_category(["external"], {"user_id": "test"})

        assert result.success
        control_system.execute_command.assert_called_once_with("/unload-category external")
        analytics.track_user_action.assert_called()

    @pytest.mark.asyncio
    async def test_handle_list_categories_basic(self, integration, mock_systems):
        """Test basic list-categories command handling."""
        control_system, _, _ = mock_systems
        control_system.execute_command = AsyncMock(
            return_value=CommandResult(success=True, message="Categories listed"),
        )

        result = await integration._handle_list_categories([], {})

        assert result.success
        control_system.execute_command.assert_called_once_with("/list-categories")

    @pytest.mark.asyncio
    async def test_handle_list_categories_with_filters(self, integration, mock_systems):
        """Test list-categories command with filters."""
        control_system, _, _ = mock_systems
        control_system.execute_command = AsyncMock(
            return_value=CommandResult(success=True, message="Filtered categories listed"),
        )

        result = await integration._handle_list_categories(["tier:2", "loaded-only"], {})

        assert result.success
        control_system.execute_command.assert_called_once_with("/list-categories tier:2 loaded-only")

    @pytest.mark.asyncio
    async def test_handle_optimize_for_success(self, integration, mock_systems):
        """Test successful optimize-for command handling."""
        control_system, _, analytics = mock_systems
        control_system.execute_command = AsyncMock(
            return_value=CommandResult(success=True, message="Optimization applied", data={"loaded_tiers": [1, 2]}),
        )

        result = await integration._handle_optimize_for(["debugging"], {"user_id": "test"})

        assert result.success
        control_system.execute_command.assert_called_once_with("/optimize-for debugging")
        analytics.track_user_action.assert_called()

    @pytest.mark.asyncio
    async def test_handle_optimize_for_no_args(self, integration, mock_systems):
        """Test optimize-for command with missing arguments."""
        result = await integration._handle_optimize_for([], {})

        assert not result.success
        assert "Task type required" in result.message
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_handle_tier_status(self, integration, mock_systems):
        """Test tier-status command handling."""
        control_system, _, _ = mock_systems
        control_system.execute_command = AsyncMock(
            return_value=CommandResult(success=True, message="Tier status retrieved"),
        )

        result = await integration._handle_tier_status([], {})

        assert result.success
        control_system.execute_command.assert_called_once_with("/tier-status")

    @pytest.mark.asyncio
    async def test_handle_save_profile_success(self, integration, mock_systems):
        """Test successful save-profile command handling."""
        control_system, _, analytics = mock_systems
        control_system.execute_command = AsyncMock(return_value=CommandResult(success=True, message="Profile saved"))

        result = await integration._handle_save_profile(["test-profile", "description"], {"user_id": "test"})

        assert result.success
        control_system.execute_command.assert_called_once()
        analytics.track_user_action.assert_called()

    @pytest.mark.asyncio
    async def test_handle_save_profile_no_args(self, integration, mock_systems):
        """Test save-profile command with missing arguments."""
        result = await integration._handle_save_profile([], {})

        assert not result.success
        assert "Profile name required" in result.message

    @pytest.mark.asyncio
    async def test_handle_load_profile_success(self, integration, mock_systems):
        """Test successful load-profile command handling."""
        control_system, _, analytics = mock_systems
        control_system.execute_command = AsyncMock(
            return_value=CommandResult(success=True, message="Profile loaded", data={"categories": {"security": True}}),
        )

        result = await integration._handle_load_profile(["test-profile"], {"user_id": "test"})

        assert result.success
        control_system.execute_command.assert_called_once_with("/load-session-profile test-profile")
        analytics.track_user_action.assert_called()

    @pytest.mark.asyncio
    async def test_handle_performance_stats(self, integration, mock_systems):
        """Test performance-stats command handling."""
        control_system, _, _ = mock_systems
        control_system.execute_command = AsyncMock(
            return_value=CommandResult(success=True, message="Stats retrieved", data={"stats": "test"}),
        )

        # Add some command history for integration metrics
        integration.command_history = [
            {"command": "cmd1", "success": True},
            {"command": "cmd2", "success": False},
            {"command": "cmd1", "success": True},
        ]

        result = await integration._handle_performance_stats([], {})

        assert result.success
        assert "integration_metrics" in result.data
        assert result.data["integration_metrics"]["commands_executed"] == 3

    @pytest.mark.asyncio
    async def test_handle_function_loading_help(self, integration, mock_systems):
        """Test function-loading help command handling."""
        _, help_system, analytics = mock_systems

        result = await integration._handle_function_loading_help(["basic"], {"user_id": "test"})

        assert result.success
        help_system.get_help.assert_called_once()
        analytics.track_user_action.assert_called()

    @pytest.mark.asyncio
    async def test_handle_analytics(self, integration, mock_systems):
        """Test analytics command handling."""
        _, _, analytics = mock_systems

        result = await integration._handle_analytics([], {"user_id": "test_user"})

        assert result.success
        assert result.message == "Usage analytics and insights"
        assert "summary" in result.data
        assert "full_analytics" in result.data
        assert "insights" in result.data
        analytics.get_user_analytics.assert_called_once_with("test_user")

    def test_get_command_usage_stats(self, integration):
        """Test command usage statistics calculation."""
        integration.command_history = [
            {"command": "cmd1 arg", "success": True},
            {"command": "cmd1 arg2", "success": True},
            {"command": "cmd2", "success": True},
            {"command": "cmd1 arg3", "success": False},
        ]

        stats = integration._get_command_usage_stats()

        assert stats["cmd1"] == 3
        assert stats["cmd2"] == 1

    def test_categorize_activity_level(self, integration):
        """Test activity level categorization."""
        assert integration._categorize_activity_level(5) == "low"
        assert integration._categorize_activity_level(25) == "moderate"
        assert integration._categorize_activity_level(75) == "high"
        assert integration._categorize_activity_level(150) == "very_high"

    def test_calculate_efficiency_score(self, integration):
        """Test efficiency score calculation."""
        analytics_data = {"error_rate": 0.05, "patterns_detected": 3, "optimization_insights": ["insight1", "insight2"]}

        score = integration._calculate_efficiency_score(analytics_data)

        assert 0 <= score <= 100
        assert score > 50  # Should be above base with good metrics

    def test_calculate_efficiency_score_poor_metrics(self, integration):
        """Test efficiency score with poor metrics."""
        analytics_data = {"error_rate": 0.4, "patterns_detected": 0, "optimization_insights": []}

        score = integration._calculate_efficiency_score(analytics_data)

        assert 0 <= score <= 100
        assert score < 50  # Should be below base with poor metrics

    def test_get_integration_status(self, integration):
        """Test integration status retrieval."""
        integration.active_session_id = "test_session"
        integration.command_history = [{"test": "command"}]

        status = integration.get_integration_status()

        assert "status" in status
        assert "active_session" in status
        assert "command_history_length" in status
        assert "registered_commands" in status
        assert "categories" in status
        assert "recent_activity" in status

        assert status["active_session"] == "test_session"
        assert status["command_history_length"] == 1

    def test_health_check_all_healthy(self, integration):
        """Test health check with all systems healthy."""
        integration.command_history = [
            {"command": "cmd1", "success": True, "timestamp": datetime.now()},
            {"command": "cmd2", "success": True, "timestamp": datetime.now()},
        ]

        health = integration.health_check()

        assert health["overall"] in ["healthy", "warning", "error"]
        assert "components" in health
        assert "metrics" in health
        assert "timestamp" in health

    def test_health_check_with_errors(self, integration, mock_systems):
        """Test health check with component errors."""
        _, help_system, _ = mock_systems
        help_system.get_help.side_effect = Exception("Help system error")

        health = integration.health_check()

        # Should handle errors gracefully
        assert "overall" in health
        assert "components" in health

    def test_calculate_error_rate_no_history(self, integration):
        """Test error rate calculation with no command history."""
        error_rate = integration._calculate_error_rate()
        assert error_rate == 0.0

    def test_calculate_error_rate_with_errors(self, integration):
        """Test error rate calculation with errors in history."""
        integration.command_history = [
            {"command": "cmd1", "success": True},
            {"command": "cmd2", "success": False},
            {"command": "cmd3", "success": True},
            {"command": "cmd4", "success": False},
        ]

        error_rate = integration._calculate_error_rate()
        assert error_rate == 0.5  # 2 errors out of 4 commands


class TestClaudeCodeCommandFactory:
    """Test ClaudeCodeCommandFactory functionality."""

    def test_create_function_loading_commands(self):
        """Test factory creates all expected commands."""
        commands = ClaudeCodeCommandFactory.create_function_loading_commands()

        assert isinstance(commands, dict)
        assert len(commands) > 0

        # Check specific commands exist
        assert "function-loading-help" in commands
        assert "function-loading-categories" in commands
        assert "function-loading-optimize" in commands

        # Check command structure
        for cmd_name, cmd_info in commands.items():
            assert "category" in cmd_info
            assert "complexity" in cmd_info
            assert "estimated_time" in cmd_info
            assert "content" in cmd_info
            assert isinstance(cmd_info["dependencies"], list)
            assert isinstance(cmd_info["sub_commands"], list)

    def test_command_content_format(self):
        """Test that command content follows expected format."""
        commands = ClaudeCodeCommandFactory.create_function_loading_commands()

        for cmd_name, cmd_info in commands.items():
            content = cmd_info["content"]

            # Should contain markdown headers
            assert "#" in content

            # Should contain usage examples for most commands
            if "help" not in cmd_name.lower():
                assert "```bash" in content or "```" in content


# Integration test scenarios
class TestIntegrationScenarios:
    """Test complete integration scenarios."""

    @pytest.fixture
    def full_integration(self):
        """Create a fully configured integration for scenario testing."""
        control_system = MagicMock()
        help_system = MagicMock()
        analytics = MagicMock()

        # Setup comprehensive mock returns
        control_system.execute_command = AsyncMock(return_value=CommandResult(success=True, message="Mock success"))

        help_system.get_help = MagicMock(return_value=CommandResult(success=True, message="Help content"))
        help_system.content_generator = MagicMock()
        help_system.content_generator.help_topics = {}
        help_system.content_generator.learning_paths = {}

        analytics.track_user_action = MagicMock()
        analytics.get_user_analytics = MagicMock(
            return_value={
                "user_id": "test",
                "analysis_period_days": 30,
                "total_events": 10,
                "error_rate": 0.1,
                "patterns_detected": 2,
                "recommendations": [],
                "optimization_insights": [],
            },
        )
        analytics.get_system_analytics = MagicMock(return_value={"total_events": 50, "active_users": 3})

        return ClaudeCommandIntegration(control_system, help_system, analytics)

    @pytest.mark.asyncio
    async def test_complete_workflow_scenario(self, full_integration):
        """Test a complete workflow scenario."""
        # Execute a sequence of commands
        commands = [
            "function-loading:list-categories",
            "function-loading:load-category security",
            "function-loading:optimize-for debugging",
            "function-loading:save-profile debug-session",
            "function-loading:performance-stats",
        ]

        for command in commands:
            result = await full_integration.execute_command(command)
            assert result.success

        # Verify state changes
        assert len(full_integration.command_history) == len(commands)
        assert full_integration.active_session_id is not None

    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self, full_integration):
        """Test error recovery and suggestions."""
        # Execute unknown command
        result = await full_integration.execute_command("unknown-command")

        # Should provide suggestions
        assert not result.success
        assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    async def test_analytics_tracking_scenario(self, full_integration):
        """Test comprehensive analytics tracking."""
        context = {"user_id": "analytics_test"}

        # Execute several commands
        await full_integration.execute_command("function-loading:load-category test", context)
        await full_integration.execute_command("function-loading:analytics", context)

        # Verify analytics calls
        assert full_integration.analytics.track_user_action.call_count >= 2


if __name__ == "__main__":
    pytest.main([__file__])
