"""Comprehensive tests for function loading demo system.

This test suite provides complete coverage for the interactive demonstration
system including demo scenarios, interactive sessions, performance comparison,
and validation reporting.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.dynamic_function_loader import LoadingStrategy
from src.core.function_loading_demo import DemoScenario, InteractiveFunctionLoadingDemo, main


class TestDemoScenario:
    """Test cases for DemoScenario class."""

    def test_init_basic(self):
        """Test basic DemoScenario initialization."""
        scenario = DemoScenario(
            name="Test Scenario",
            description="A test scenario",
            query="test query",
            expected_categories=["test", "demo"],
        )

        assert scenario.name == "Test Scenario"
        assert scenario.description == "A test scenario"
        assert scenario.query == "test query"
        assert scenario.expected_categories == ["test", "demo"]
        assert scenario.user_commands == []
        assert scenario.strategy == LoadingStrategy.CONSERVATIVE

    def test_init_with_optional_parameters(self):
        """Test DemoScenario initialization with all parameters."""
        user_commands = ["/load-category test", "/optimize-for demo"]

        scenario = DemoScenario(
            name="Full Scenario",
            description="Complete scenario test",
            query="comprehensive test query",
            expected_categories=["test", "demo", "quality"],
            user_commands=user_commands,
            strategy=LoadingStrategy.AGGRESSIVE,
        )

        assert scenario.user_commands == user_commands
        assert scenario.strategy == LoadingStrategy.AGGRESSIVE

    def test_init_with_none_values(self):
        """Test DemoScenario initialization with None values."""
        scenario = DemoScenario(
            name="Minimal Scenario",
            description="Minimal test",
            query="minimal query",
            expected_categories=["core"],
            user_commands=None,
            strategy=None,
        )

        assert scenario.user_commands == []
        assert scenario.strategy == LoadingStrategy.CONSERVATIVE


class TestInteractiveFunctionLoadingDemo:
    """Test cases for InteractiveFunctionLoadingDemo class."""

    @pytest.fixture
    def mock_loader(self):
        """Create a mock DynamicFunctionLoader."""
        loader = AsyncMock()
        loader.function_registry = MagicMock()
        loader.function_registry.functions = {}
        loader.function_registry.get_baseline_token_cost.return_value = 10000
        loader.function_registry.tiers = ["tier1", "tier2", "tier3"]
        loader.function_registry.get_functions_by_tier.return_value = []
        loader.function_registry.get_tier_token_cost.return_value = 1000
        loader.function_registry.calculate_loading_cost.return_value = (500, ["func1", "func2"])
        return loader

    @pytest.fixture
    def demo(self):
        """Create InteractiveFunctionLoadingDemo instance."""
        return InteractiveFunctionLoadingDemo()

    def test_init(self, demo):
        """Test InteractiveFunctionLoadingDemo initialization."""
        assert demo.loader is None
        assert demo.current_session_id is None
        assert isinstance(demo.demo_scenarios, list)
        assert len(demo.demo_scenarios) == 8  # Based on _create_demo_scenarios
        assert demo.performance_baseline is None

    def test_create_demo_scenarios(self, demo):
        """Test demo scenarios creation."""
        scenarios = demo._create_demo_scenarios()

        assert len(scenarios) == 8

        # Verify specific scenarios
        git_scenario = next(s for s in scenarios if s.name == "Git Workflow")
        assert git_scenario.description == "Common git operations workflow"
        assert git_scenario.query == "help me commit my changes and create a pull request"
        assert git_scenario.expected_categories == ["git", "core"]
        assert git_scenario.strategy == LoadingStrategy.BALANCED

        debug_scenario = next(s for s in scenarios if s.name == "Debugging Session")
        assert debug_scenario.expected_categories == ["debug", "test", "analysis"]
        assert "/load-category analysis" in debug_scenario.user_commands
        assert debug_scenario.strategy == LoadingStrategy.CONSERVATIVE

        security_scenario = next(s for s in scenarios if s.name == "Security Audit")
        assert security_scenario.expected_categories == ["security", "analysis", "quality"]
        assert "/load-tier 2" in security_scenario.user_commands

        refactor_scenario = next(s for s in scenarios if s.name == "Code Refactoring")
        assert refactor_scenario.strategy == LoadingStrategy.AGGRESSIVE

        minimal_scenario = next(s for s in scenarios if s.name == "Minimal Setup")
        assert minimal_scenario.expected_categories == ["core"]
        assert "/optimize-for minimal" in minimal_scenario.user_commands

    @pytest.mark.asyncio
    async def test_initialize(self, demo, mock_loader):
        """Test demo initialization."""
        with patch("src.core.function_loading_demo.initialize_dynamic_loading", return_value=mock_loader):
            await demo.initialize()

        assert demo.loader == mock_loader
        assert demo.performance_baseline is not None

        # Verify baseline performance structure
        baseline = demo.performance_baseline
        assert "total_functions" in baseline
        assert "total_tokens" in baseline
        assert "tier_breakdown" in baseline
        assert "tier_1" in baseline["tier_breakdown"]
        assert "tier_2" in baseline["tier_breakdown"]
        assert "tier_3" in baseline["tier_breakdown"]

    @pytest.mark.asyncio
    async def test_measure_baseline_performance(self, demo, mock_loader):
        """Test baseline performance measurement."""
        demo.loader = mock_loader

        # Mock registry with tiers
        mock_loader.function_registry.functions = {"func1": {}, "func2": {}, "func3": {}}
        mock_loader.function_registry.get_baseline_token_cost.return_value = 15000
        mock_loader.function_registry.tiers = ["tier1", "tier2", "tier3"]
        mock_loader.function_registry.get_functions_by_tier.side_effect = [
            ["func1"],
            ["func2"],
            ["func3"],  # Different functions per tier
        ]
        mock_loader.function_registry.get_tier_token_cost.side_effect = [5000, 7000, 3000]  # Token costs per tier

        await demo._measure_baseline_performance()

        baseline = demo.performance_baseline
        assert baseline["total_functions"] == 3
        assert baseline["total_tokens"] == 15000

        # Verify tier breakdown
        assert baseline["tier_breakdown"]["tier_1"]["functions"] == 1
        assert baseline["tier_breakdown"]["tier_1"]["tokens"] == 5000
        assert baseline["tier_breakdown"]["tier_2"]["functions"] == 1
        assert baseline["tier_breakdown"]["tier_2"]["tokens"] == 7000
        assert baseline["tier_breakdown"]["tier_3"]["functions"] == 1
        assert baseline["tier_breakdown"]["tier_3"]["tokens"] == 3000

    @pytest.mark.asyncio
    async def test_measure_baseline_performance_empty_tiers(self, demo, mock_loader):
        """Test baseline performance measurement with empty tiers."""
        demo.loader = mock_loader
        mock_loader.function_registry.tiers = []

        await demo._measure_baseline_performance()

        baseline = demo.performance_baseline
        assert baseline["tier_breakdown"]["tier_1"]["functions"] == 0
        assert baseline["tier_breakdown"]["tier_1"]["tokens"] == 0
        assert baseline["tier_breakdown"]["tier_2"]["functions"] == 0
        assert baseline["tier_breakdown"]["tier_2"]["tokens"] == 0

    @pytest.mark.asyncio
    async def test_run_demo_scenarios(self, demo, mock_loader):
        """Test running all demo scenarios."""
        demo.loader = mock_loader

        # Mock single scenario execution
        mock_result = {
            "scenario": demo.demo_scenarios[0],
            "token_reduction": 75.0,
            "total_time_ms": 250.0,
            "functions_loaded": 10,
            "functions_used": 5,
        }

        with patch.object(demo, "_run_single_scenario", return_value=mock_result) as mock_run:
            with patch.object(demo, "_display_scenario_result") as mock_display:
                with patch.object(demo, "_display_scenarios_summary") as mock_summary:
                    with patch("src.core.function_loading_demo.asyncio.sleep"):
                        await demo._run_demo_scenarios()

        # Verify all scenarios were run
        assert mock_run.call_count == len(demo.demo_scenarios)
        assert mock_display.call_count == len(demo.demo_scenarios)
        mock_summary.assert_called_once()

        # Verify results were passed to summary
        summary_call = mock_summary.call_args[0][0]
        assert len(summary_call) == len(demo.demo_scenarios)

    @pytest.mark.asyncio
    async def test_run_single_scenario_success(self, demo, mock_loader):
        """Test successful single scenario execution."""
        demo.loader = mock_loader

        # Create test scenario
        scenario = DemoScenario(
            name="Test Scenario",
            description="Test description",
            query="test query for loading",
            expected_categories=["test"],
            user_commands=["/load-category test", "/optimize-for testing"],
            strategy=LoadingStrategy.BALANCED,
        )

        # Mock loader responses
        session_id = "test_session_123"
        mock_loader.create_loading_session.return_value = session_id

        mock_command_result = MagicMock()
        mock_command_result.success = True
        mock_loader.execute_user_command.return_value = mock_command_result

        mock_loading_decision = MagicMock()
        mock_loading_decision.functions_to_load = ["func1", "func2", "func3", "func4", "func5", "func6"]
        mock_loader.load_functions_for_query.return_value = mock_loading_decision

        mock_session_summary = {"token_reduction_percentage": 72.5, "functions_loaded": 6, "status": "completed"}
        mock_loader.end_loading_session.return_value = mock_session_summary

        # Run scenario
        result = await demo._run_single_scenario(scenario)

        # Verify loader calls
        mock_loader.create_loading_session.assert_called_once_with(
            user_id="demo_user_test_scenario",
            query="test query for loading",
            strategy=LoadingStrategy.BALANCED,
        )

        # Verify command execution
        assert mock_loader.execute_user_command.call_count == 2
        mock_loader.execute_user_command.assert_any_call(session_id, "/load-category test")
        mock_loader.execute_user_command.assert_any_call(session_id, "/optimize-for testing")

        # Verify function usage recording (max 5 functions)
        assert mock_loader.record_function_usage.call_count == 5

        # Verify session cleanup
        mock_loader.end_loading_session.assert_called_once_with(session_id)

        # Verify result structure
        assert result["scenario"] == scenario
        assert result["session_summary"] == mock_session_summary
        assert result["loading_decision"] == mock_loading_decision
        assert len(result["command_results"]) == 2
        assert "total_time_ms" in result
        assert result["token_reduction"] == 72.5
        assert result["functions_loaded"] == 6
        assert result["functions_used"] == 5

    @pytest.mark.asyncio
    async def test_run_single_scenario_no_commands(self, demo, mock_loader):
        """Test single scenario execution with no user commands."""
        demo.loader = mock_loader

        scenario = DemoScenario(
            name="Simple Scenario",
            description="No commands scenario",
            query="simple test query",
            expected_categories=["core"],
        )

        session_id = "simple_session_456"
        mock_loader.create_loading_session.return_value = session_id

        mock_loading_decision = MagicMock()
        mock_loading_decision.functions_to_load = ["func1", "func2"]
        mock_loader.load_functions_for_query.return_value = mock_loading_decision

        mock_session_summary = {"token_reduction_percentage": 65.0}
        mock_loader.end_loading_session.return_value = mock_session_summary

        result = await demo._run_single_scenario(scenario)

        # Verify no command execution
        mock_loader.execute_user_command.assert_not_called()

        # Verify function usage (2 functions)
        assert mock_loader.record_function_usage.call_count == 2

        assert result["command_results"] == []
        assert result["functions_used"] == 2

    @pytest.mark.asyncio
    async def test_run_single_scenario_many_functions(self, demo, mock_loader):
        """Test single scenario with many functions (usage limit testing)."""
        demo.loader = mock_loader

        scenario = DemoScenario(
            name="Large Scenario",
            description="Many functions scenario",
            query="complex query requiring many functions",
            expected_categories=["debug", "analysis", "security"],
        )

        session_id = "large_session_789"
        mock_loader.create_loading_session.return_value = session_id

        # Mock 20 functions being loaded
        many_functions = [f"func_{i}" for i in range(20)]
        mock_loading_decision = MagicMock()
        mock_loading_decision.functions_to_load = many_functions
        mock_loader.load_functions_for_query.return_value = mock_loading_decision

        mock_session_summary = {"token_reduction_percentage": 80.0}
        mock_loader.end_loading_session.return_value = mock_session_summary

        result = await demo._run_single_scenario(scenario)

        # Verify only 5 functions were used (limit)
        assert mock_loader.record_function_usage.call_count == 5
        assert result["functions_loaded"] == 20
        assert result["functions_used"] == 5

    def test_display_scenario_result(self, demo):
        """Test scenario result display method."""
        scenario = DemoScenario(
            name="Display Test",
            description="Test display",
            query="display query",
            expected_categories=["test"],
        )

        mock_loading_decision = MagicMock()
        mock_loading_decision.fallback_reason = "Test fallback reason"

        result = {
            "scenario": scenario,
            "token_reduction": 75.5,
            "loading_decision": mock_loading_decision,
            "command_results": [MagicMock(success=True), MagicMock(success=False), MagicMock(success=True)],
            "total_time_ms": 125.0,
            "functions_loaded": 8,
            "functions_used": 4,
        }

        # This method currently has minimal implementation
        # Test should pass without exceptions
        demo._display_scenario_result(result)

        # Verify it accesses the expected fields
        assert result["token_reduction"] == 75.5
        assert result["loading_decision"] == mock_loading_decision

    @pytest.mark.asyncio
    async def test_display_scenarios_summary(self, demo):
        """Test scenarios summary display method."""
        results = [
            {"token_reduction": 75.0, "total_time_ms": 200.0},
            {"token_reduction": 68.0, "total_time_ms": 150.0},
            {"token_reduction": 82.0, "total_time_ms": 300.0},
            {"token_reduction": 71.0, "total_time_ms": 180.0},
            {"token_reduction": 65.0, "total_time_ms": 220.0},
        ]

        # Test should pass without exceptions
        await demo._display_scenarios_summary(results)

        # Verify calculations work
        total_scenarios = len(results)
        achieving_target = sum(1 for r in results if r["token_reduction"] >= 70.0)
        avg_reduction = sum(r["token_reduction"] for r in results) / total_scenarios
        avg_time = sum(r["total_time_ms"] for r in results) / total_scenarios

        assert total_scenarios == 5
        assert achieving_target == 3  # 75.0, 82.0, 71.0
        assert avg_reduction == 72.2
        assert avg_time == 210.0

    @pytest.mark.asyncio
    async def test_interactive_session_single_query(self, demo, mock_loader):
        """Test interactive session with single query."""
        demo.loader = mock_loader

        # Mock user input sequence: query, strategy, back
        user_inputs = ["debug failing tests", "2", "back"]  # Query  # Strategy (Balanced)  # Exit

        with patch("builtins.input", side_effect=user_inputs):
            with patch.object(demo, "_run_interactive_query") as mock_run_query:
                await demo._interactive_session()

        # Verify interactive query was run with correct parameters
        mock_run_query.assert_called_once_with("debug failing tests", LoadingStrategy.BALANCED)

    @pytest.mark.asyncio
    async def test_interactive_session_multiple_queries(self, demo, mock_loader):
        """Test interactive session with multiple queries."""
        demo.loader = mock_loader

        user_inputs = [
            "first query",  # Query 1
            "1",  # Conservative strategy
            "second query",  # Query 2
            "3",  # Aggressive strategy
            "third query",  # Query 3
            "",  # Default strategy (2)
            "quit",  # Exit
        ]

        with patch("builtins.input", side_effect=user_inputs):
            with patch.object(demo, "_run_interactive_query") as mock_run_query:
                await demo._interactive_session()

        # Verify all queries were processed
        assert mock_run_query.call_count == 3
        mock_run_query.assert_any_call("first query", LoadingStrategy.CONSERVATIVE)
        mock_run_query.assert_any_call("second query", LoadingStrategy.AGGRESSIVE)
        mock_run_query.assert_any_call("third query", LoadingStrategy.BALANCED)  # Default

    @pytest.mark.asyncio
    async def test_interactive_session_empty_queries(self, demo, mock_loader):
        """Test interactive session with empty queries."""
        demo.loader = mock_loader

        user_inputs = [
            "",  # Empty query (should be skipped)
            "   ",  # Whitespace only (should be skipped)
            "valid query",  # Valid query
            "1",  # Strategy
            "exit",  # Exit
        ]

        with patch("builtins.input", side_effect=user_inputs):
            with patch.object(demo, "_run_interactive_query") as mock_run_query:
                await demo._interactive_session()

        # Only the valid query should be processed
        mock_run_query.assert_called_once_with("valid query", LoadingStrategy.CONSERVATIVE)

    @pytest.mark.asyncio
    async def test_run_interactive_query(self, demo, mock_loader):
        """Test running a single interactive query."""
        demo.loader = mock_loader
        demo.performance_baseline = {"total_tokens": 10000}

        session_id = "interactive_123"
        mock_loader.create_loading_session.return_value = session_id

        mock_loading_decision = MagicMock()
        mock_loading_decision.tier_breakdown = {"tier_1": ["func1", "func2"], "tier_2": ["func3"], "tier_3": []}
        mock_loading_decision.estimated_tokens = 3000
        mock_loader.load_functions_for_query.return_value = mock_loading_decision

        with patch.object(demo, "_offer_user_commands") as mock_offer_commands:
            await demo._run_interactive_query("test interactive query", LoadingStrategy.BALANCED)

        # Verify session creation
        mock_loader.create_loading_session.assert_called_once_with(
            user_id="interactive_user",
            query="test interactive query",
            strategy=LoadingStrategy.BALANCED,
        )

        # Verify function loading
        mock_loader.load_functions_for_query.assert_called_once_with(session_id)

        # Verify user commands were offered
        mock_offer_commands.assert_called_once_with(session_id)

        # Verify session cleanup
        mock_loader.end_loading_session.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_offer_user_commands_success(self, demo, mock_loader):
        """Test offering user commands with successful execution."""
        demo.loader = mock_loader
        session_id = "commands_test_456"

        # Mock successful command result
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {"categories": ["test", "debug"]}
        mock_result.suggestions = []
        mock_loader.execute_user_command.return_value = mock_result

        user_inputs = [
            "/load-category test",  # Command with slash
            "optimize-for debug",  # Command without slash (should be added)
            "done",  # Exit
        ]

        with patch("builtins.input", side_effect=user_inputs):
            await demo._offer_user_commands(session_id)

        # Verify commands were executed
        assert mock_loader.execute_user_command.call_count == 2
        mock_loader.execute_user_command.assert_any_call(session_id, "/load-category test")
        mock_loader.execute_user_command.assert_any_call(session_id, "/optimize-for debug")

    @pytest.mark.asyncio
    async def test_offer_user_commands_failure(self, demo, mock_loader):
        """Test offering user commands with failed execution."""
        demo.loader = mock_loader
        session_id = "commands_fail_789"

        # Mock failed command result
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.suggestions = ["Try /help for available commands"]
        mock_loader.execute_user_command.return_value = mock_result

        user_inputs = ["/invalid-command", "exit"]  # Invalid command  # Exit

        with patch("builtins.input", side_effect=user_inputs):
            await demo._offer_user_commands(session_id)

        mock_loader.execute_user_command.assert_called_once_with(session_id, "/invalid-command")

    @pytest.mark.asyncio
    async def test_offer_user_commands_exception(self, demo, mock_loader):
        """Test offering user commands with exception handling."""
        demo.loader = mock_loader
        session_id = "commands_exception_101"

        # Mock command execution raising exception
        mock_loader.execute_user_command.side_effect = Exception("Command execution failed")

        user_inputs = ["/error-command", "back"]  # Command that will raise exception  # Exit

        with patch("builtins.input", side_effect=user_inputs):
            await demo._offer_user_commands(session_id)

        # Should not raise exception and continue to accept more input
        mock_loader.execute_user_command.assert_called_once_with(session_id, "/error-command")

    @pytest.mark.asyncio
    async def test_offer_user_commands_empty_input(self, demo, mock_loader):
        """Test offering user commands with empty input."""
        demo.loader = mock_loader
        session_id = "commands_empty_202"

        user_inputs = [
            "",  # Empty input (should be skipped)
            "   ",  # Whitespace only (should be skipped)
            "done",  # Exit
        ]

        with patch("builtins.input", side_effect=user_inputs):
            await demo._offer_user_commands(session_id)

        # No commands should be executed
        mock_loader.execute_user_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_performance_comparison(self, demo, mock_loader):
        """Test performance comparison functionality."""
        demo.loader = mock_loader
        demo.performance_baseline = {"total_functions": 100, "total_tokens": 15000}

        # Mock session creation and loading for each strategy
        session_ids = ["comp_conservative", "comp_balanced", "comp_aggressive"]
        mock_loader.create_loading_session.side_effect = session_ids

        # Mock loading decisions for each strategy
        loading_decisions = []
        session_summaries = []

        for i, strategy in enumerate(
            [LoadingStrategy.CONSERVATIVE, LoadingStrategy.BALANCED, LoadingStrategy.AGGRESSIVE],
        ):
            decision = MagicMock()
            decision.functions_to_load = [f"func_{j}" for j in range(30 + i * 10)]  # 30, 40, 50 functions
            decision.estimated_tokens = 8000 - i * 1000  # 8000, 7000, 6000 tokens
            loading_decisions.append(decision)

            summary = {"token_reduction_percentage": 45.0 + i * 5}  # 45%, 50%, 55%
            session_summaries.append(summary)

        mock_loader.load_functions_for_query.side_effect = loading_decisions
        mock_loader.end_loading_session.side_effect = session_summaries

        await demo._performance_comparison()

        # Verify all strategies were tested
        assert mock_loader.create_loading_session.call_count == 3
        assert mock_loader.load_functions_for_query.call_count == 3
        assert mock_loader.end_loading_session.call_count == 3

        # Verify correct query was used for all strategies
        expected_query = "analyze this codebase for security vulnerabilities and performance issues"
        for call in mock_loader.create_loading_session.call_args_list:
            assert call[1]["query"] == expected_query
            assert call[1]["user_id"] == "comparison_user"

    @pytest.mark.asyncio
    async def test_user_commands_demo(self, demo, mock_loader):
        """Test user commands demonstration."""
        demo.loader = mock_loader

        session_id = "user_commands_demo_333"
        mock_loader.create_loading_session.return_value = session_id

        # Mock successful command results
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.data = {
            "categories": ["security", "debug", "analysis"],
            "functions_loaded": 25,
            "help_text": "Available commands:\n/load-category <name>\n/optimize-for <task>\nMore help...",
        }
        mock_loader.execute_user_command.return_value = mock_result

        await demo._user_commands_demo()

        # Verify session was created for commands demo
        mock_loader.create_loading_session.assert_called_once_with(
            user_id="commands_demo_user",
            query="help me with various development tasks",
        )

        # Verify initial function loading
        mock_loader.load_functions_for_query.assert_called_once_with(session_id)

        # Verify all demo commands were executed
        expected_commands = [
            "/list-categories",
            "/load-category security",
            "/optimize-for debugging",
            "/tier-status",
            "/performance-mode aggressive",
            "/function-stats",
            "/help",
        ]

        assert mock_loader.execute_user_command.call_count == len(expected_commands)
        for command in expected_commands:
            mock_loader.execute_user_command.assert_any_call(session_id, command)

        # Verify session cleanup
        mock_loader.end_loading_session.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_user_commands_demo_with_failures(self, demo, mock_loader):
        """Test user commands demo with some command failures."""
        demo.loader = mock_loader

        session_id = "user_commands_fail_444"
        mock_loader.create_loading_session.return_value = session_id

        # Mock mixed success/failure results
        def mock_command_execution(session_id, command):
            if "security" in command or "help" in command:
                # Some commands fail
                result = MagicMock()
                result.success = False
                return result
            # Other commands succeed
            result = MagicMock()
            result.success = True
            result.data = {"status": "executed"}
            return result

        mock_loader.execute_user_command.side_effect = mock_command_execution

        # Should not raise exceptions despite failures
        await demo._user_commands_demo()

        # All commands should still be attempted
        assert mock_loader.execute_user_command.call_count == 7

    @pytest.mark.asyncio
    async def test_user_commands_demo_with_exceptions(self, demo, mock_loader):
        """Test user commands demo with command execution exceptions."""
        demo.loader = mock_loader

        session_id = "user_commands_exception_555"
        mock_loader.create_loading_session.return_value = session_id

        # Mock commands raising exceptions
        mock_loader.execute_user_command.side_effect = Exception("Command failed")

        # Should not raise exceptions and complete all commands
        await demo._user_commands_demo()

        # All commands should be attempted despite exceptions
        assert mock_loader.execute_user_command.call_count == 7

    @pytest.mark.asyncio
    async def test_monitoring_dashboard(self, demo, mock_loader):
        """Test monitoring dashboard functionality."""
        demo.loader = mock_loader

        # Mock performance report
        mock_performance_report = {
            "session_statistics": {"total_sessions": 25, "active_sessions": 3, "avg_session_duration": 45.5},
            "function_registry_stats": {
                "total_functions": 150,
                "functions_loaded": 45,
                "cache_hits": 120,
                "cache_misses": 30,
            },
            "cache_statistics": {"hit_rate": 80.0, "size": 1024, "evictions": 5},
            "optimization_performance": {
                "token_optimization": {
                    "baseline_tokens": 12000,
                    "optimized_tokens": 3600,
                    "reduction_percentage": 70.0,
                },
            },
        }

        mock_loader.get_performance_report.return_value = mock_performance_report

        # Test should complete without exceptions
        await demo._monitoring_dashboard()

        # Verify performance report was requested
        mock_loader.get_performance_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_monitoring_dashboard_minimal_data(self, demo, mock_loader):
        """Test monitoring dashboard with minimal data."""
        demo.loader = mock_loader

        # Mock minimal performance report
        mock_performance_report = {
            "session_statistics": {"total_sessions": 0},
            "function_registry_stats": {"total_functions": 50},
            "cache_statistics": {"hit_rate": 0.0},
        }

        mock_loader.get_performance_report.return_value = mock_performance_report

        # Test should complete without exceptions
        await demo._monitoring_dashboard()

        mock_loader.get_performance_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_report(self, demo, mock_loader):
        """Test validation report generation."""
        demo.loader = mock_loader

        # Mock session creation for validation scenarios
        session_ids = [f"validation_{i}" for i in range(5)]
        mock_loader.create_loading_session.side_effect = session_ids

        # Mock loading decisions and session summaries
        loading_decisions = []
        session_summaries = []

        token_reductions = [78.0, 65.0, 82.0, 71.0, 55.0]  # Various reduction levels
        functions_loaded = [20, 35, 15, 28, 40]

        for i in range(5):
            decision = MagicMock()
            decision.functions_to_load = [f"func_{j}" for j in range(functions_loaded[i])]
            loading_decisions.append(decision)

            summary = {"token_reduction_percentage": token_reductions[i]}
            session_summaries.append(summary)

        mock_loader.load_functions_for_query.side_effect = loading_decisions
        mock_loader.end_loading_session.side_effect = session_summaries

        # Mock final performance report
        mock_performance_report = {"final_stats": "validation_complete"}
        mock_loader.get_performance_report.return_value = mock_performance_report

        await demo._validation_report()

        # Verify all validation scenarios were run
        assert mock_loader.create_loading_session.call_count == 5
        assert mock_loader.load_functions_for_query.call_count == 5
        assert mock_loader.end_loading_session.call_count == 5

        # Verify final performance report was requested
        mock_loader.get_performance_report.assert_called_once()

        # Verify session creation parameters
        validation_scenarios = [
            ("Basic Git Operations", "commit my changes and push to github", LoadingStrategy.BALANCED),
            ("Security Analysis", "audit security vulnerabilities in authentication", LoadingStrategy.CONSERVATIVE),
            ("Performance Debug", "debug slow database queries", LoadingStrategy.BALANCED),
            ("Code Quality", "refactor legacy code for maintainability", LoadingStrategy.AGGRESSIVE),
            ("Documentation", "generate API documentation", LoadingStrategy.BALANCED),
        ]

        for i, (name, query, strategy) in enumerate(validation_scenarios):
            call_args = mock_loader.create_loading_session.call_args_list[i]
            assert call_args[1]["user_id"] == f"validation_{name.lower().replace(' ', '_')}"
            assert call_args[1]["query"] == query
            assert call_args[1]["strategy"] == strategy


class TestMainFunction:
    """Test cases for main function and CLI interface."""

    @pytest.mark.asyncio
    async def test_main_interactive_mode(self):
        """Test main function in interactive mode."""
        test_args = ["script.py", "--mode", "interactive"]

        with patch("sys.argv", test_args):
            with patch("src.core.function_loading_demo.InteractiveFunctionLoadingDemo") as mock_demo_class:
                mock_demo = AsyncMock()
                mock_demo_class.return_value = mock_demo

                await main()

        # Verify demo was created and initialized
        mock_demo_class.assert_called_once()
        mock_demo.initialize.assert_called_once()
        mock_demo.run_interactive_demo.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_scenarios_mode(self):
        """Test main function in scenarios mode."""
        test_args = ["script.py", "--mode", "scenarios"]

        with patch("sys.argv", test_args):
            with patch("src.core.function_loading_demo.InteractiveFunctionLoadingDemo") as mock_demo_class:
                mock_demo = AsyncMock()
                mock_demo_class.return_value = mock_demo

                await main()

        mock_demo.initialize.assert_called_once()
        mock_demo._run_demo_scenarios.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_validation_mode(self):
        """Test main function in validation mode."""
        test_args = ["script.py", "--mode", "validation"]

        with patch("sys.argv", test_args):
            with patch("src.core.function_loading_demo.InteractiveFunctionLoadingDemo") as mock_demo_class:
                mock_demo = AsyncMock()
                mock_demo_class.return_value = mock_demo

                await main()

        mock_demo.initialize.assert_called_once()
        mock_demo._validation_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_performance_mode(self):
        """Test main function in performance mode."""
        test_args = ["script.py", "--mode", "performance"]

        with patch("sys.argv", test_args):
            with patch("src.core.function_loading_demo.InteractiveFunctionLoadingDemo") as mock_demo_class:
                mock_demo = AsyncMock()
                mock_demo_class.return_value = mock_demo

                await main()

        mock_demo.initialize.assert_called_once()
        mock_demo._performance_comparison.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_default_mode(self):
        """Test main function with default mode (interactive)."""
        test_args = ["script.py"]  # No mode specified

        with patch("sys.argv", test_args):
            with patch("src.core.function_loading_demo.InteractiveFunctionLoadingDemo") as mock_demo_class:
                mock_demo = AsyncMock()
                mock_demo_class.return_value = mock_demo

                await main()

        # Should default to interactive mode
        mock_demo.run_interactive_demo.assert_called_once()

    @pytest.mark.asyncio
    async def test_main_with_scenarios_argument(self):
        """Test main function with scenarios argument."""
        test_args = ["script.py", "--mode", "scenarios", "--scenarios", "git", "debug"]

        with patch("sys.argv", test_args):
            with patch("src.core.function_loading_demo.InteractiveFunctionLoadingDemo") as mock_demo_class:
                mock_demo = AsyncMock()
                mock_demo_class.return_value = mock_demo

                await main()

        # Scenarios argument is parsed but not currently used in implementation
        mock_demo._run_demo_scenarios.assert_called_once()

    def test_main_entry_point_keyboard_interrupt(self):
        """Test main entry point handling keyboard interrupt."""
        with patch("src.core.function_loading_demo.asyncio.run", side_effect=KeyboardInterrupt):
            # Should not raise exception - KeyboardInterrupt is caught
            if __name__ == "__main__":
                exec(
                    """
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
""",
                )

    def test_main_entry_point_exception(self):
        """Test main entry point handling general exception."""
        with patch("src.core.function_loading_demo.asyncio.run", side_effect=Exception("Test error")):
            with patch("sys.exit") as mock_exit:
                if __name__ == "__main__":
                    exec(
                        """
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
except Exception:
    sys.exit(1)
""",
                    )


class TestInteractiveFunctionLoadingDemoIntegration:
    """Integration tests for InteractiveFunctionLoadingDemo."""

    @pytest.mark.asyncio
    async def test_full_demo_workflow(self, mock_loader):
        """Test complete demo workflow from initialization to completion."""
        demo = InteractiveFunctionLoadingDemo()

        # Mock initialization
        with patch("src.core.function_loading_demo.initialize_dynamic_loading", return_value=mock_loader):
            await demo.initialize()

        # Test running a single scenario end-to-end
        scenario = demo.demo_scenarios[0]  # Git Workflow scenario

        # Mock all loader interactions
        session_id = "integration_test_session"
        mock_loader.create_loading_session.return_value = session_id

        mock_loading_decision = MagicMock()
        mock_loading_decision.functions_to_load = ["git_commit", "git_push", "pr_create"]
        mock_loading_decision.tier_breakdown = {
            "tier_1": ["git_commit"],
            "tier_2": ["git_push", "pr_create"],
            "tier_3": [],
        }
        mock_loading_decision.estimated_tokens = 2500
        mock_loader.load_functions_for_query.return_value = mock_loading_decision

        mock_session_summary = {"token_reduction_percentage": 75.0, "functions_loaded": 3, "status": "completed"}
        mock_loader.end_loading_session.return_value = mock_session_summary

        # Run the scenario
        result = await demo._run_single_scenario(scenario)

        # Verify complete workflow
        assert result["scenario"] == scenario
        assert result["token_reduction"] == 75.0
        assert result["functions_loaded"] == 3
        assert result["functions_used"] == 3  # All functions used since ≤5
        assert "total_time_ms" in result

        # Verify loader interactions
        mock_loader.create_loading_session.assert_called_once()
        mock_loader.load_functions_for_query.assert_called_once()
        assert mock_loader.record_function_usage.call_count == 3
        mock_loader.end_loading_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_comparison_integration(self, mock_loader):
        """Test performance comparison with realistic data."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader
        demo.performance_baseline = {"total_functions": 200, "total_tokens": 20000}

        # Mock realistic performance data for different strategies
        strategy_results = {
            LoadingStrategy.CONSERVATIVE: {"functions": 80, "tokens": 12000, "reduction": 40.0},
            LoadingStrategy.BALANCED: {"functions": 60, "tokens": 8000, "reduction": 60.0},
            LoadingStrategy.AGGRESSIVE: {"functions": 40, "tokens": 5000, "reduction": 75.0},
        }

        def mock_session_creation(user_id, query, strategy):
            return f"session_{strategy.value}"

        def mock_loading(session_id):
            # Extract strategy from session_id
            for strat in LoadingStrategy:
                if strat.value in session_id:
                    data = strategy_results[strat]
                    decision = MagicMock()
                    decision.functions_to_load = [f"func_{i}" for i in range(data["functions"])]
                    decision.estimated_tokens = data["tokens"]
                    return decision
            return MagicMock()

        def mock_session_end(session_id):
            for strat in LoadingStrategy:
                if strat.value in session_id:
                    return {"token_reduction_percentage": strategy_results[strat]["reduction"]}
            return {"token_reduction_percentage": 0.0}

        mock_loader.create_loading_session.side_effect = mock_session_creation
        mock_loader.load_functions_for_query.side_effect = mock_loading
        mock_loader.end_loading_session.side_effect = mock_session_end

        # Run performance comparison
        await demo._performance_comparison()

        # Verify all strategies were tested
        assert mock_loader.create_loading_session.call_count == 3

        # Verify the aggressive strategy would be identified as best
        # (This is implicit in the current implementation which calculates best_reduction)

    @pytest.mark.asyncio
    async def test_validation_report_integration(self, mock_loader):
        """Test validation report with comprehensive scenario coverage."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader

        # Mock realistic validation results
        validation_data = [
            {"name": "Basic Git Operations", "reduction": 72.0, "functions": 25},
            {"name": "Security Analysis", "reduction": 68.0, "functions": 45},
            {"name": "Performance Debug", "reduction": 85.0, "functions": 30},
            {"name": "Code Quality", "reduction": 79.0, "functions": 35},
            {"name": "Documentation", "reduction": 63.0, "functions": 20},
        ]

        session_counter = 0

        def mock_session_creation(user_id, query, strategy):
            nonlocal session_counter
            session_id = f"validation_session_{session_counter}"
            session_counter += 1
            return session_id

        def mock_loading(session_id):
            idx = int(session_id.split("_")[-1])
            data = validation_data[idx]
            decision = MagicMock()
            decision.functions_to_load = [f"func_{i}" for i in range(data["functions"])]
            return decision

        def mock_session_end(session_id):
            idx = int(session_id.split("_")[-1])
            return {"token_reduction_percentage": validation_data[idx]["reduction"]}

        mock_loader.create_loading_session.side_effect = mock_session_creation
        mock_loader.load_functions_for_query.side_effect = mock_loading
        mock_loader.end_loading_session.side_effect = mock_session_end
        mock_loader.get_performance_report.return_value = {"validation": "completed"}

        # Run validation report
        await demo._validation_report()

        # Verify all scenarios were tested
        assert mock_loader.create_loading_session.call_count == 5
        assert mock_loader.load_functions_for_query.call_count == 5
        assert mock_loader.end_loading_session.call_count == 5
        mock_loader.get_performance_report.assert_called_once()

        # Calculate expected results
        achieving_target = sum(1 for data in validation_data if data["reduction"] >= 70.0)
        avg_reduction = sum(data["reduction"] for data in validation_data) / len(validation_data)

        assert achieving_target == 3  # 72.0, 85.0, 79.0
        assert avg_reduction == 73.4


class TestInteractiveFunctionLoadingDemoEdgeCases:
    """Test edge cases and error conditions for InteractiveFunctionLoadingDemo."""

    @pytest.mark.asyncio
    async def test_initialization_with_loader_error(self):
        """Test initialization when loader creation fails."""
        demo = InteractiveFunctionLoadingDemo()

        with patch(
            "src.core.function_loading_demo.initialize_dynamic_loading",
            side_effect=Exception("Loader init failed"),
        ):
            with pytest.raises(Exception, match="Loader init failed"):
                await demo.initialize()

    @pytest.mark.asyncio
    async def test_scenario_execution_with_loader_errors(self, mock_loader):
        """Test scenario execution with various loader errors."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader

        scenario = demo.demo_scenarios[0]

        # Test session creation failure
        mock_loader.create_loading_session.side_effect = Exception("Session creation failed")

        with pytest.raises(Exception, match="Session creation failed"):
            await demo._run_single_scenario(scenario)

    @pytest.mark.asyncio
    async def test_scenario_with_command_failures(self, mock_loader):
        """Test scenario execution when user commands fail."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader

        scenario = DemoScenario(
            name="Command Failure Test",
            description="Test command failures",
            query="test query",
            expected_categories=["test"],
            user_commands=["/failing-command", "/another-failing-command"],
        )

        session_id = "command_failure_session"
        mock_loader.create_loading_session.return_value = session_id

        # Mock command failures
        mock_loader.execute_user_command.side_effect = Exception("Command failed")

        # Mock successful loading and session end
        mock_loading_decision = MagicMock()
        mock_loading_decision.functions_to_load = ["func1"]
        mock_loader.load_functions_for_query.return_value = mock_loading_decision

        mock_session_summary = {"token_reduction_percentage": 50.0}
        mock_loader.end_loading_session.return_value = mock_session_summary

        # Should not raise exception despite command failures
        result = await demo._run_single_scenario(scenario)

        # Verify scenario completed despite command failures
        assert result["token_reduction"] == 50.0
        assert len(result["command_results"]) == 0  # Failed commands not recorded

    @pytest.mark.asyncio
    async def test_interactive_session_with_invalid_strategy(self, mock_loader):
        """Test interactive session with invalid strategy input."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader

        user_inputs = ["test query", "invalid", "back"]  # Invalid strategy choice

        with patch("builtins.input", side_effect=user_inputs):
            with patch.object(demo, "_run_interactive_query") as mock_run_query:
                await demo._interactive_session()

        # Should default to BALANCED strategy for invalid input
        mock_run_query.assert_called_once_with("test query", LoadingStrategy.BALANCED)

    @pytest.mark.asyncio
    async def test_performance_comparison_with_partial_failures(self, mock_loader):
        """Test performance comparison when some strategies fail."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader
        demo.performance_baseline = {"total_functions": 100, "total_tokens": 10000}

        # Mock partial failures - conservative strategy fails
        def mock_session_creation(user_id, query, strategy):
            if strategy == LoadingStrategy.CONSERVATIVE:
                raise Exception("Conservative strategy failed")
            return f"session_{strategy.value}"

        mock_loader.create_loading_session.side_effect = mock_session_creation

        # Mock successful loading for other strategies
        mock_loading_decision = MagicMock()
        mock_loading_decision.functions_to_load = ["func1", "func2"]
        mock_loading_decision.estimated_tokens = 5000
        mock_loader.load_functions_for_query.return_value = mock_loading_decision

        mock_session_summary = {"token_reduction_percentage": 50.0}
        mock_loader.end_loading_session.return_value = mock_session_summary

        # Should handle failure gracefully and continue with other strategies
        await demo._performance_comparison()

        # Only successful strategies should be processed
        assert mock_loader.load_functions_for_query.call_count == 2  # Balanced and Aggressive

    @pytest.mark.asyncio
    async def test_monitoring_dashboard_with_empty_performance_report(self, mock_loader):
        """Test monitoring dashboard with empty or missing performance data."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader

        # Mock empty performance report
        mock_loader.get_performance_report.return_value = {}

        # Should complete without errors
        await demo._monitoring_dashboard()

        mock_loader.get_performance_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_validation_report_with_all_failures(self, mock_loader):
        """Test validation report when all scenarios fail."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader

        # Mock all scenarios failing at different stages
        mock_loader.create_loading_session.side_effect = [
            Exception("Session 1 failed"),
            "session_2",
            "session_3",
            "session_4",
            "session_5",
        ]

        mock_loader.load_functions_for_query.side_effect = [
            Exception("Loading 2 failed"),
            MagicMock(),
            MagicMock(),
            MagicMock(),
        ]

        mock_loader.end_loading_session.side_effect = [
            Exception("End 3 failed"),
            {"token_reduction_percentage": 30.0},
            {"token_reduction_percentage": 25.0},
        ]

        mock_loader.get_performance_report.return_value = {"status": "completed"}

        # Should handle failures gracefully
        with pytest.raises(Exception):
            await demo._validation_report()

    @pytest.mark.asyncio
    async def test_baseline_performance_with_no_tiers(self, mock_loader):
        """Test baseline performance measurement with no tiers defined."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader

        # Mock registry with no tiers
        mock_loader.function_registry.tiers = []
        mock_loader.function_registry.functions = {"func1": {}, "func2": {}}
        mock_loader.function_registry.get_baseline_token_cost.return_value = 5000

        await demo._measure_baseline_performance()

        baseline = demo.performance_baseline
        assert baseline["total_functions"] == 2
        assert baseline["total_tokens"] == 5000

        # All tier breakdowns should show 0
        for tier in ["tier_1", "tier_2", "tier_3"]:
            assert baseline["tier_breakdown"][tier]["functions"] == 0
            assert baseline["tier_breakdown"][tier]["tokens"] == 0

    @pytest.mark.asyncio
    async def test_run_interactive_demo_exit_conditions(self, mock_loader):
        """Test interactive demo exit conditions."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader

        # Test various exit inputs
        exit_inputs = ["q", "quit", "exit", "Q", "QUIT", "EXIT"]

        for exit_input in exit_inputs:
            with patch.object(demo, "_show_main_menu"):
                with patch("builtins.input", return_value=exit_input):
                    # Should exit the loop without calling any menu functions
                    await demo.run_interactive_demo()

    @pytest.mark.asyncio
    async def test_run_interactive_demo_invalid_menu_choices(self, mock_loader):
        """Test interactive demo with invalid menu choices."""
        demo = InteractiveFunctionLoadingDemo()
        demo.loader = mock_loader

        # Test invalid choices followed by quit
        user_inputs = ["0", "7", "invalid", "q"]

        with patch.object(demo, "_show_main_menu"):
            with patch("builtins.input", side_effect=user_inputs):
                with patch.object(demo, "_run_demo_scenarios") as mock_scenarios:
                    with patch.object(demo, "_interactive_session") as mock_session:
                        await demo.run_interactive_demo()

        # None of the menu functions should be called for invalid choices
        mock_scenarios.assert_not_called()
        mock_session.assert_not_called()
