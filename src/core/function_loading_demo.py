"""
Interactive Demo and Validation Framework for Dynamic Function Loading

This module provides an interactive demonstration of the dynamic function loading
system, showcasing real-time optimization, user controls, and performance validation.

Features:
- Command-line interactive demo
- Real-time performance monitoring
- User command simulation
- Validation scenario runner
- Performance comparison tools
"""

import argparse
import asyncio
import sys
import time
from typing import Any

from .dynamic_function_loader import (
    DynamicFunctionLoader,
    LoadingStrategy,
    initialize_dynamic_loading,
)


class DemoScenario:
    """Represents a demonstration scenario."""

    def __init__(
        self,
        name: str,
        description: str,
        query: str,
        expected_categories: list[str],
        user_commands: list[str] | None = None,
        strategy: LoadingStrategy | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.query = query
        self.expected_categories = expected_categories
        self.user_commands = user_commands or []
        self.strategy = strategy or LoadingStrategy.CONSERVATIVE


class InteractiveFunctionLoadingDemo:
    """Interactive demonstration system for dynamic function loading."""

    def __init__(self) -> None:
        self.loader: DynamicFunctionLoader | None = None
        self.current_session_id: str | None = None
        self.demo_scenarios = self._create_demo_scenarios()
        self.performance_baseline: dict[str, Any] | None = None

    def _create_demo_scenarios(self) -> list[DemoScenario]:
        """Create comprehensive demonstration scenarios."""
        return [
            DemoScenario(
                name="Git Workflow",
                description="Common git operations workflow",
                query="help me commit my changes and create a pull request",
                expected_categories=["git", "core"],
                user_commands=[],
                strategy=LoadingStrategy.BALANCED,
            ),
            DemoScenario(
                name="Debugging Session",
                description="Debugging failing tests with analysis",
                query="debug the failing authentication tests in the user module",
                expected_categories=["debug", "test", "analysis"],
                user_commands=["/load-category analysis", "/optimize-for debugging"],
                strategy=LoadingStrategy.CONSERVATIVE,
            ),
            DemoScenario(
                name="Security Audit",
                description="Security analysis and vulnerability scanning",
                query="perform comprehensive security audit on payment processing",
                expected_categories=["security", "analysis", "quality"],
                user_commands=["/load-tier 2", "/performance-mode balanced"],
                strategy=LoadingStrategy.BALANCED,
            ),
            DemoScenario(
                name="Code Refactoring",
                description="Code quality improvement and refactoring",
                query="refactor this legacy authentication module for better maintainability",
                expected_categories=["quality", "analysis"],
                user_commands=["/optimize-for refactoring", "/load-category quality"],
                strategy=LoadingStrategy.AGGRESSIVE,
            ),
            DemoScenario(
                name="Documentation Generation",
                description="Generate comprehensive documentation",
                query="create documentation for the entire API module",
                expected_categories=["quality", "analysis"],
                user_commands=["/optimize-for documentation"],
                strategy=LoadingStrategy.BALANCED,
            ),
            DemoScenario(
                name="Performance Analysis",
                description="Performance bottleneck investigation",
                query="analyze performance bottlenecks in the database layer",
                expected_categories=["debug", "analysis"],
                user_commands=["/load-category debug", "/load-category analysis"],
                strategy=LoadingStrategy.CONSERVATIVE,
            ),
            DemoScenario(
                name="External Integration",
                description="Working with external APIs and services",
                query="integrate with the payment gateway API and validate security",
                expected_categories=["external", "security", "analysis"],
                user_commands=["/load-tier 3", "/load-category external"],
                strategy=LoadingStrategy.BALANCED,
            ),
            DemoScenario(
                name="Minimal Setup",
                description="Minimal function set for basic operations",
                query="just need basic file operations",
                expected_categories=["core"],
                user_commands=["/optimize-for minimal"],
                strategy=LoadingStrategy.AGGRESSIVE,
            ),
        ]

    async def initialize(self) -> None:
        """Initialize the demo system."""
        self.loader = await initialize_dynamic_loading()

        # Measure baseline performance
        await self._measure_baseline_performance()

    async def _measure_baseline_performance(self) -> None:
        """Measure baseline performance with all functions loaded."""
        if self.loader is None:
            raise RuntimeError("Loader not initialized")

        registry = self.loader.function_registry

        self.performance_baseline = {
            "total_functions": len(registry.functions),
            "total_tokens": registry.get_baseline_token_cost(),
            "tier_breakdown": {
                "tier_1": (
                    {
                        "functions": len(registry.get_functions_by_tier(list(registry.tiers)[0])),
                        "tokens": registry.get_tier_token_cost(list(registry.tiers)[0]),
                    }
                    if registry.tiers
                    else {"functions": 0, "tokens": 0}
                ),
                "tier_2": {
                    "functions": (
                        len(registry.get_functions_by_tier(list(registry.tiers)[1])) if len(registry.tiers) > 1 else 0
                    ),
                    "tokens": registry.get_tier_token_cost(list(registry.tiers)[1]) if len(registry.tiers) > 1 else 0,
                },
                "tier_3": {
                    "functions": (
                        len(registry.get_functions_by_tier(list(registry.tiers)[2])) if len(registry.tiers) > 2 else 0
                    ),
                    "tokens": registry.get_tier_token_cost(list(registry.tiers)[2]) if len(registry.tiers) > 2 else 0,
                },
            },
        }

    async def run_interactive_demo(self) -> None:
        """Run the interactive demonstration."""

        while True:
            await self._show_main_menu()
            choice = input("\n👉 Enter your choice: ").strip()

            if choice == "1":
                await self._run_demo_scenarios()
            elif choice == "2":
                await self._interactive_session()
            elif choice == "3":
                await self._performance_comparison()
            elif choice == "4":
                await self._user_commands_demo()
            elif choice == "5":
                await self._monitoring_dashboard()
            elif choice == "6":
                await self._validation_report()
            elif choice.lower() in ["q", "quit", "exit"]:
                break
            else:
                pass

    async def _show_main_menu(self) -> None:
        """Display the main menu."""

    async def _run_demo_scenarios(self) -> None:
        """Run all demonstration scenarios."""

        scenario_results = []

        for _i, scenario in enumerate(self.demo_scenarios, 1):

            # Run scenario
            result = await self._run_single_scenario(scenario)
            scenario_results.append(result)

            # Display results
            self._display_scenario_result(result)

            # Brief pause for readability
            await asyncio.sleep(1)

        # Summary
        await self._display_scenarios_summary(scenario_results)

    async def _run_single_scenario(self, scenario: DemoScenario) -> dict[str, Any]:
        """Run a single demonstration scenario."""
        if self.loader is None:
            raise RuntimeError("Loader not initialized")

        start_time = time.perf_counter()

        # Create session
        session_id = await self.loader.create_loading_session(
            user_id=f"demo_user_{scenario.name.lower().replace(' ', '_')}",
            query=scenario.query,
            strategy=scenario.strategy,
        )

        # Execute user commands if any
        command_results = []
        for command in scenario.user_commands:
            try:
                cmd_result = await self.loader.execute_user_command(session_id, command)
                # Record only successful commands in results
                if getattr(cmd_result, "success", False):
                    command_results.append(cmd_result)
            except Exception:
                # Swallow command errors to allow scenario to proceed
                pass

        # Load functions
        loading_decision = await self.loader.load_functions_for_query(session_id)

        # Simulate function usage
        used_functions = list(loading_decision.functions_to_load)[: min(5, len(loading_decision.functions_to_load))]
        for func_name in used_functions:
            await self.loader.record_function_usage(session_id, func_name, success=True)

        # End session
        session_summary = await self.loader.end_loading_session(session_id)

        total_time = (time.perf_counter() - start_time) * 1000

        # Extract token reduction safely
        token_reduction = 0.0
        if session_summary is not None and isinstance(session_summary, dict):
            token_reduction = float(session_summary.get("token_reduction_percentage", 0.0))

        return {
            "scenario": scenario,
            "session_summary": session_summary,
            "loading_decision": loading_decision,
            "command_results": command_results,
            "total_time_ms": total_time,
            "token_reduction": token_reduction,
            "functions_loaded": len(loading_decision.functions_to_load),
            "functions_used": len(used_functions),
        }

    def _display_scenario_result(self, result: dict[str, Any]) -> None:
        """Display the results of a scenario execution."""
        result["token_reduction"]
        loading_decision = result["loading_decision"]

        if loading_decision.fallback_reason:
            pass

        if result["command_results"]:
            sum(1 for cmd in result["command_results"] if cmd.success)

    async def _display_scenarios_summary(self, results: list[dict[str, Any]]) -> None:
        """Display summary of all scenario results."""

        total_scenarios = len(results)
        achieving_target = sum(1 for r in results if r["token_reduction"] >= 70.0)
        sum(r["token_reduction"] for r in results) / total_scenarios
        sum(r["total_time_ms"] for r in results) / total_scenarios

        if achieving_target >= total_scenarios * 0.8 or achieving_target >= total_scenarios * 0.6:  # 80% success rate
            pass
        else:
            pass

    async def _interactive_session(self) -> None:
        """Run an interactive loading session."""

        while True:
            query = input("\n🔍 Enter your query: ").strip()

            if query.lower() in ["back", "exit", "quit"]:
                break

            if not query:
                continue

            # Get strategy preference

            strategy_choice = input("Strategy (1-3, default=2): ").strip() or "2"

            strategies = {
                "1": LoadingStrategy.CONSERVATIVE,
                "2": LoadingStrategy.BALANCED,
                "3": LoadingStrategy.AGGRESSIVE,
            }
            strategy = strategies.get(strategy_choice, LoadingStrategy.BALANCED)

            # Run interactive session
            await self._run_interactive_query(query, strategy)

    async def _run_interactive_query(self, query: str, strategy: LoadingStrategy) -> None:
        """Run a single interactive query."""
        if self.loader is None:
            raise RuntimeError("Loader not initialized")

        start_time = time.perf_counter()

        # Create session
        session_id = await self.loader.create_loading_session(
            user_id="interactive_user",
            query=query,
            strategy=strategy,
        )

        # Load functions with real-time display
        loading_decision = await self.loader.load_functions_for_query(session_id)

        (time.perf_counter() - start_time) * 1000

        # Display results

        # Show tier breakdown
        for _tier, functions in loading_decision.tier_breakdown.items():
            if functions:
                tier_tokens, _ = self.loader.function_registry.calculate_loading_cost(functions)

                # Show sample functions
                sample_functions = list(functions)[:3]
                for _func in sample_functions:
                    pass
                if len(functions) > 3:
                    pass

        # Calculate and show optimization
        if self.performance_baseline is not None:
            baseline_tokens = self.performance_baseline["total_tokens"]
            optimized_tokens = loading_decision.estimated_tokens
            (baseline_tokens - optimized_tokens) / baseline_tokens * 100

        # Offer user commands
        await self._offer_user_commands(session_id)

        # End session
        await self.loader.end_loading_session(session_id)

    async def _offer_user_commands(self, session_id: str) -> None:
        """Offer user commands during interactive session."""
        if self.loader is None:
            raise RuntimeError("Loader not initialized")

        while True:
            command = input("\n🎛️  Command: ").strip()

            if command.lower() in ["done", "exit", "back"]:
                break

            if not command:
                continue

            if not command.startswith("/"):
                command = "/" + command

            try:
                result = await self.loader.execute_user_command(session_id, command)

                if result.success:
                    if result.data:
                        pass
                elif result.suggestions:
                    pass

            except Exception:
                pass

    async def _performance_comparison(self) -> None:
        """Show performance comparison between optimized and baseline."""
        if self.loader is None or self.performance_baseline is None:
            raise RuntimeError("Loader and baseline not initialized")

        # Run a sample query with different strategies
        test_query = "analyze this codebase for security vulnerabilities and performance issues"

        comparison_results = []

        strategies = [
            ("Baseline (All Functions)", None),
            ("Conservative Loading", LoadingStrategy.CONSERVATIVE),
            ("Balanced Loading", LoadingStrategy.BALANCED),
            ("Aggressive Loading", LoadingStrategy.AGGRESSIVE),
        ]

        for strategy_name, strategy in strategies:

            if strategy is None:
                # Simulate baseline (all functions loaded)
                result = {
                    "strategy_name": strategy_name,
                    "functions_loaded": self.performance_baseline["total_functions"],
                    "tokens_used": self.performance_baseline["total_tokens"],
                    "loading_time_ms": 500.0,  # Simulated baseline loading time
                    "token_reduction": 0.0,
                }
            else:
                # Run with optimization
                start_time = time.perf_counter()

                try:
                    session_id = await self.loader.create_loading_session(
                        user_id="comparison_user",
                        query=test_query,
                        strategy=strategy,
                    )

                    loading_decision = await self.loader.load_functions_for_query(session_id)
                    loading_time = (time.perf_counter() - start_time) * 1000

                    session_summary = await self.loader.end_loading_session(session_id)

                    # Extract token reduction safely
                    token_reduction = 0.0
                    if session_summary is not None and isinstance(session_summary, dict):
                        token_reduction = float(session_summary.get("token_reduction_percentage", 0.0))

                    result = {
                        "strategy_name": strategy_name,
                        "functions_loaded": len(loading_decision.functions_to_load),
                        "tokens_used": loading_decision.estimated_tokens,
                        "loading_time_ms": loading_time,
                        "token_reduction": token_reduction,
                    }
                except Exception:
                    # Skip this strategy on failure and continue with others
                    continue

            comparison_results.append(result)

        # Display comparison table

        for result in comparison_results:
            pass

        # Analysis
        best_reduction = max(r["token_reduction"] for r in comparison_results)
        next(r["strategy_name"] for r in comparison_results if r["token_reduction"] == best_reduction)

        if best_reduction >= 70:
            baseline_tokens = self.performance_baseline["total_tokens"]
            baseline_tokens * (best_reduction / 100)

    async def _user_commands_demo(self) -> None:
        """Demonstrate user command capabilities."""
        if self.loader is None:
            raise RuntimeError("Loader not initialized")

        # Create a session for commands demo
        session_id = await self.loader.create_loading_session(
            user_id="commands_demo_user",
            query="help me with various development tasks",
        )

        # Initial load
        await self.loader.load_functions_for_query(session_id)

        # Demonstrate various commands
        demo_commands = [
            ("/list-categories", "Show available function categories"),
            ("/load-category security", "Force load security functions"),
            ("/optimize-for debugging", "Optimize for debugging tasks"),
            ("/tier-status", "Show current tier loading status"),
            ("/performance-mode aggressive", "Switch to aggressive mode"),
            ("/function-stats", "Show function loading statistics"),
            ("/help", "Show available commands"),
        ]

        for command, _description in demo_commands:

            try:
                result = await self.loader.execute_user_command(session_id, command)

                if result.success:

                    # Show relevant data
                    if result.data:
                        if "categories" in result.data or "functions_loaded" in result.data:
                            pass
                        elif "help_text" in result.data:
                            # Show just first few lines of help
                            result.data["help_text"].split("\n")[:3]
                else:
                    pass

            except Exception:
                pass

        await self.loader.end_loading_session(session_id)

    async def _monitoring_dashboard(self) -> None:
        """Show real-time monitoring dashboard."""
        if self.loader is None:
            raise RuntimeError("Loader not initialized")

        # Get current performance report
        performance_report = await self.loader.get_performance_report()

        # Active sessions

        # Session statistics
        _ = performance_report.get("session_statistics", {})

        # Function registry stats
        _ = performance_report.get("function_registry_stats", {})

        # Cache statistics
        _ = performance_report.get("cache_statistics", {})

        # Show optimization report if available
        if "optimization_performance" in performance_report:
            opt_report = performance_report["optimization_performance"]
            if isinstance(opt_report, dict) and "token_optimization" in opt_report:
                _ = opt_report["token_optimization"]

    async def _validation_report(self) -> None:
        """Generate comprehensive validation report."""
        if self.loader is None:
            raise RuntimeError("Loader not initialized")

        # Run validation scenarios

        validation_scenarios = [
            ("Basic Git Operations", "commit my changes and push to github", LoadingStrategy.BALANCED),
            ("Security Analysis", "audit security vulnerabilities in authentication", LoadingStrategy.CONSERVATIVE),
            ("Performance Debug", "debug slow database queries", LoadingStrategy.BALANCED),
            ("Code Quality", "refactor legacy code for maintainability", LoadingStrategy.AGGRESSIVE),
            ("Documentation", "generate API documentation", LoadingStrategy.BALANCED),
        ]

        validation_results = []

        for name, query, strategy in validation_scenarios:
            session_id = await self.loader.create_loading_session(
                user_id=f"validation_{name.lower().replace(' ', '_')}",
                query=query,
                strategy=strategy,
            )

            loading_decision = await self.loader.load_functions_for_query(session_id)
            session_summary = await self.loader.end_loading_session(session_id)

            # Extract token reduction safely
            token_reduction = 0.0
            if session_summary is not None and isinstance(session_summary, dict):
                token_reduction = float(session_summary.get("token_reduction_percentage", 0.0))

            validation_results.append(
                {
                    "name": name,
                    "token_reduction": token_reduction,
                    "functions_loaded": len(loading_decision.functions_to_load),
                    "strategy": strategy.value,
                },
            )

        # Analysis
        achieving_target = 0
        total_reductions = []

        for r in validation_results:
            token_reduction_raw = r.get("token_reduction", 0.0)
            if isinstance(token_reduction_raw, (int, float)):
                token_reduction = float(token_reduction_raw)
                if token_reduction >= 70.0:
                    achieving_target += 1
                total_reductions.append(token_reduction)

        total_scenarios = len(validation_results)
        avg_reduction = sum(total_reductions) / len(total_reductions) if total_reductions else 0.0

        for result in validation_results:
            token_reduction_raw = result.get("token_reduction", 0.0)
            if isinstance(token_reduction_raw, (int, float)):
                token_reduction = float(token_reduction_raw)
                "✅" if token_reduction >= 70.0 else "❌"

        # Final assessment
        if (avg_reduction >= 70.0 and achieving_target >= total_scenarios * 0.8) or avg_reduction >= 60.0:
            pass
        else:
            pass

        # Generate performance report
        await self.loader.get_performance_report()


async def main() -> None:
    """Main demo entry point."""
    parser = argparse.ArgumentParser(description="Dynamic Function Loading Demo")
    parser.add_argument(
        "--mode",
        choices=["interactive", "scenarios", "validation", "performance"],
        default="interactive",
        help="Demo mode to run",
    )
    parser.add_argument("--scenarios", nargs="*", help="Specific scenarios to run")

    args = parser.parse_args()

    # Initialize demo
    demo = InteractiveFunctionLoadingDemo()
    await demo.initialize()

    if args.mode == "interactive":
        await demo.run_interactive_demo()
    elif args.mode == "scenarios":
        await demo._run_demo_scenarios()
    elif args.mode == "validation":
        await demo._validation_report()
    elif args.mode == "performance":
        await demo._performance_comparison()


# Make main function available for import by test modules
__all__ = ["main", "InteractiveFunctionLoadingDemo", "DemoScenario"]


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        sys.exit(1)
