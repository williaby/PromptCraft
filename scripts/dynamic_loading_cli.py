#!/usr/bin/env python3
"""
Dynamic Function Loading CLI

Command-line interface for interacting with the dynamic function loading prototype.
Provides easy access to demonstration, testing, and validation capabilities.

Usage Examples:
    # Run comprehensive demonstration
    python scripts/dynamic_loading_cli.py demo --comprehensive

    # Test specific query optimization
    python scripts/dynamic_loading_cli.py optimize "analyze code security" --strategy aggressive

    # Run performance validation
    python scripts/dynamic_loading_cli.py validate --performance

    # Interactive session
    python scripts/dynamic_loading_cli.py interactive

    # Generate performance report
    python scripts/dynamic_loading_cli.py report --export results.json

This CLI serves as both a demonstration tool and a practical interface for
testing and validating the dynamic function loading system.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.comprehensive_prototype_demo import (
    ComprehensivePrototypeDemo,
    DemoScenarioType,
)
from src.core.dynamic_function_loader import LoadingStrategy
from src.core.dynamic_loading_integration import (
    DynamicLoadingIntegration,
    IntegrationMode,
    ProcessingResult,
    get_integration_instance,
)


class DynamicLoadingCLI:
    """Command-line interface for the dynamic function loading system."""

    def __init__(self):
        self.integration: DynamicLoadingIntegration | None = None
        self.logger = logging.getLogger(__name__)

    async def initialize(self, mode: IntegrationMode = IntegrationMode.PRODUCTION):
        """Initialize the CLI with the integration system."""
        try:
            print("🚀 Initializing Dynamic Function Loading CLI...")
            self.integration = await get_integration_instance(mode=mode)
            print("✅ CLI initialized successfully!")
            return True
        except Exception as e:
            print(f"❌ CLI initialization failed: {e}")
            return False

    async def run_demo(self, comprehensive: bool = False, scenario_types: list[str] | None = None):
        """Run demonstration scenarios."""
        print("🎬 RUNNING DYNAMIC FUNCTION LOADING DEMONSTRATION")
        print("=" * 60)

        demo = ComprehensivePrototypeDemo(mode=IntegrationMode.DEMO)

        if not await demo.initialize():
            print("❌ Failed to initialize demonstration system")
            return False

        if comprehensive:
            # Run full comprehensive demonstration
            results = await demo.run_comprehensive_demo()

            # Display key results
            self._display_demo_summary(results)
            return results["production_readiness"]["readiness_level"] in ["PRODUCTION_READY", "MOSTLY_READY"]

        # Run selected scenario types or basic demo
        if scenario_types:
            selected_scenarios = [s for s in demo.demo_scenarios if s.scenario_type.value in scenario_types]
        else:
            # Run basic scenarios
            selected_scenarios = [
                s
                for s in demo.demo_scenarios
                if s.scenario_type in [DemoScenarioType.BASIC_OPTIMIZATION, DemoScenarioType.USER_INTERACTION]
            ][:3]

        print(f"Running {len(selected_scenarios)} selected scenarios...")

        for scenario in selected_scenarios:
            print(f"\n🔄 {scenario.name}")
            print(f"   {scenario.description}")

            result = await demo._run_single_scenario(scenario)
            self._display_scenario_result(scenario, result)

        return True

    async def optimize_query(
        self,
        query: str,
        strategy: str = "balanced",
        user_commands: list[str] | None = None,
        user_id: str = "cli_user",
    ) -> ProcessingResult:
        """Optimize a single query and display results."""
        print("🔍 OPTIMIZING QUERY")
        print(f"Query: {query}")
        print(f"Strategy: {strategy}")
        print("-" * 50)

        # Convert strategy string to enum
        strategy_map = {
            "conservative": LoadingStrategy.CONSERVATIVE,
            "balanced": LoadingStrategy.BALANCED,
            "aggressive": LoadingStrategy.AGGRESSIVE,
        }

        if strategy not in strategy_map:
            print(f"❌ Invalid strategy: {strategy}. Valid options: {list(strategy_map.keys())}")
            return None

        strategy_enum = strategy_map[strategy]

        # Process the query
        start_time = time.perf_counter()
        result = await self.integration.process_query(
            query=query,
            user_id=user_id,
            strategy=strategy_enum,
            user_commands=user_commands,
        )
        total_time = (time.perf_counter() - start_time) * 1000

        # Display results
        self._display_optimization_result(result, total_time)

        return result

    async def run_validation(
        self,
        performance: bool = False,
        stress_test: bool = False,
        production_readiness: bool = False,
    ):
        """Run various validation tests."""
        print("✅ RUNNING VALIDATION TESTS")
        print("=" * 50)

        validation_results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": [],
            "overall_success": True,
        }

        if performance:
            print("\n📊 Performance Validation")
            print("-" * 30)
            perf_result = await self._validate_performance()
            validation_results["tests_run"].append(("performance", perf_result))
            if not perf_result["success"]:
                validation_results["overall_success"] = False

        if stress_test:
            print("\n🔥 Stress Test Validation")
            print("-" * 30)
            stress_result = await self._validate_stress_test()
            validation_results["tests_run"].append(("stress_test", stress_result))
            if not stress_result["success"]:
                validation_results["overall_success"] = False

        if production_readiness:
            print("\n🚀 Production Readiness Validation")
            print("-" * 40)
            prod_result = await self._validate_production_readiness()
            validation_results["tests_run"].append(("production_readiness", prod_result))
            if not prod_result["success"]:
                validation_results["overall_success"] = False

        # Default validation if no specific tests requested
        if not any([performance, stress_test, production_readiness]):
            basic_result = await self._validate_basic_functionality()
            validation_results["tests_run"].append(("basic_functionality", basic_result))
            if not basic_result["success"]:
                validation_results["overall_success"] = False

        # Display overall results
        print("\n🏆 VALIDATION SUMMARY")
        print("-" * 30)
        for test_name, result in validation_results["tests_run"]:
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{test_name}: {status}")

        overall_status = "✅ ALL TESTS PASSED" if validation_results["overall_success"] else "❌ SOME TESTS FAILED"
        print(f"\nOverall: {overall_status}")

        return validation_results

    async def run_interactive(self):
        """Run interactive session for testing queries."""
        print("💬 INTERACTIVE DYNAMIC LOADING SESSION")
        print("=" * 50)
        print("Enter queries to see optimization in action!")
        print("Commands:")
        print("  /help                    - Show available commands")
        print("  /strategy <strategy>     - Change loading strategy")
        print("  /commands <command>      - Add user command")
        print("  /clear                   - Clear user commands")
        print("  /status                  - Show system status")
        print("  /quit                    - Exit interactive mode")
        print()

        current_strategy = LoadingStrategy.BALANCED
        user_commands = []

        while True:
            try:
                user_input = input("🔍 Query: ").strip()

                if not user_input:
                    continue

                if user_input.startswith("/"):
                    # Handle commands
                    if user_input == "/quit":
                        print("👋 Goodbye!")
                        break
                    if user_input == "/help":
                        self._show_interactive_help()
                    elif user_input.startswith("/strategy "):
                        strategy_name = user_input[10:].strip()
                        if strategy_name in ["conservative", "balanced", "aggressive"]:
                            strategy_map = {
                                "conservative": LoadingStrategy.CONSERVATIVE,
                                "balanced": LoadingStrategy.BALANCED,
                                "aggressive": LoadingStrategy.AGGRESSIVE,
                            }
                            current_strategy = strategy_map[strategy_name]
                            print(f"✅ Strategy changed to: {strategy_name}")
                        else:
                            print("❌ Invalid strategy. Use: conservative, balanced, or aggressive")
                    elif user_input.startswith("/commands "):
                        command = user_input[10:].strip()
                        if command.startswith("/"):
                            user_commands.append(command)
                            print(f"✅ Added command: {command}")
                        else:
                            print("❌ Commands must start with '/'")
                    elif user_input == "/clear":
                        user_commands.clear()
                        print("✅ User commands cleared")
                    elif user_input == "/status":
                        await self._show_system_status()
                    else:
                        print("❌ Unknown command. Type /help for available commands.")
                    continue

                # Process query
                result = await self.optimize_query(
                    query=user_input,
                    strategy=current_strategy.value,
                    user_commands=user_commands.copy() if user_commands else None,
                )

                # Show brief summary
                if result:
                    print("💡 Quick Summary:")
                    print(f"   Reduction: {result.reduction_percentage:.1f}%")
                    print(f"   Time: {result.total_time_ms:.1f}ms")
                    print(f"   Success: {'Yes' if result.success else 'No'}")
                print()

            except KeyboardInterrupt:
                print("\n👋 Interactive session ended")
                break
            except Exception as e:
                print(f"❌ Error processing query: {e}")

    async def generate_report(self, export_path: str | None = None):
        """Generate comprehensive performance report."""
        print("📊 GENERATING PERFORMANCE REPORT")
        print("=" * 40)

        report = await self.integration.get_performance_report()
        status = await self.integration.get_system_status()

        # Create comprehensive report
        comprehensive_report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "cli_version": "1.0.0",
                "mode": self.integration.mode.value,
            },
            "system_status": status,
            "performance_report": report,
            "summary": {
                "integration_health": status["integration_health"],
                "total_queries_processed": status["metrics"]["total_queries_processed"],
                "success_rate": status["metrics"]["success_rate"],
                "average_reduction": status["metrics"]["average_reduction_percentage"],
                "target_achievement_rate": status["metrics"]["target_achievement_rate"],
                "uptime_hours": status["metrics"]["uptime_hours"],
            },
        }

        # Display summary
        summary = comprehensive_report["summary"]
        print(f"System Health: {summary['integration_health']}")
        print(f"Queries Processed: {summary['total_queries_processed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Average Reduction: {summary['average_reduction']:.1f}%")
        print(f"Target Achievement: {summary['target_achievement_rate']:.1f}%")
        print(f"Uptime: {summary['uptime_hours']:.1f} hours")

        # Export if requested
        if export_path:
            output_path = Path(export_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w") as f:
                json.dump(comprehensive_report, f, indent=2, default=str)

            print(f"\n💾 Report exported to: {output_path}")

        return comprehensive_report

    def _display_demo_summary(self, results: dict[str, Any]):
        """Display summary of comprehensive demo results."""
        print("\n🏆 DEMONSTRATION SUMMARY")
        print("=" * 50)

        perf_summary = results["performance_summary"]
        readiness = results["production_readiness"]

        print(f"Scenarios Tested: {perf_summary['total_scenarios']}")
        print(f"Success Rate: {perf_summary['success_rate']:.1f}%")
        print(f"Average Token Reduction: {perf_summary['token_optimization']['average_reduction']:.1f}%")
        print(f"70% Target Achievement: {perf_summary['token_optimization']['target_achievement_rate']:.1f}%")
        print(f"Average Processing Time: {perf_summary['performance_metrics']['average_processing_time_ms']:.1f}ms")

        print(f"\n{readiness['readiness_color']} Production Readiness: {readiness['readiness_level']}")
        print(f"Overall Score: {readiness['overall_score']:.1f}/100")

        print("\n🎯 Key Achievements:")
        for achievement in readiness["key_achievements"]:
            print(f"  {achievement}")

        print("\n📋 Deployment Recommendation:")
        print(readiness["deployment_recommendation"])

    def _display_scenario_result(self, scenario, result: dict[str, Any]):
        """Display results of a single scenario."""
        processing = result.get("processing_result", {})

        if processing.get("success", False):
            reduction = processing.get("reduction_percentage", 0.0)
            time_ms = processing.get("total_time_ms", 0.0)
            target_met = "✅" if reduction >= scenario.target_reduction else "❌"

            print(f"   Results: {reduction:.1f}% reduction in {time_ms:.1f}ms {target_met}")
        else:
            error = processing.get("error_message", "Unknown error")
            print(f"   ❌ Failed: {error}")

    def _display_optimization_result(self, result: ProcessingResult, total_time_ms: float):
        """Display detailed optimization result."""
        if result.success:
            print("✅ OPTIMIZATION SUCCESSFUL")
            print("📊 Results:")
            print(f"   Session ID: {result.session_id}")
            print(f"   Baseline Tokens: {result.baseline_tokens:,}")
            print(f"   Optimized Tokens: {result.optimized_tokens:,}")
            print(f"   Reduction: {result.reduction_percentage:.1f}%")
            print(f"   Target (70%) Achieved: {'✅ Yes' if result.target_achieved else '❌ No'}")

            print("\n⏱️  Performance:")
            print(f"   Detection Time: {result.detection_time_ms:.1f}ms")
            print(f"   Loading Time: {result.loading_time_ms:.1f}ms")
            print(f"   Total Time: {total_time_ms:.1f}ms")

            print("\n🎯 Detection Results:")
            categories = [cat.value for cat in result.detection_result.categories]
            print(f"   Categories: {', '.join(categories)}")
            print(f"   Confidence: {result.detection_result.confidence:.2f}")
            print(f"   Reasoning: {result.detection_result.reasoning}")

            if result.user_commands:
                successful_commands = sum(1 for cmd in result.user_commands if cmd.success)
                print(f"\n🎛️  User Commands: {successful_commands}/{len(result.user_commands)} successful")

            if result.fallback_used:
                print(f"\n🔄 Fallback Used: {result.optimization_report.fallback_reason}")

            if result.cache_hit:
                print("\n💾 Cache Hit: Yes")
        else:
            print("❌ OPTIMIZATION FAILED")
            print(f"Error: {result.error_message}")

    def _show_interactive_help(self):
        """Show help for interactive mode."""
        print("\n📖 INTERACTIVE MODE HELP")
        print("-" * 30)
        print("Available Commands:")
        print("  /strategy <name>         - Set loading strategy (conservative/balanced/aggressive)")
        print("  /commands <command>      - Add user command (e.g., /commands /load-category debug)")
        print("  /clear                   - Clear all user commands")
        print("  /status                  - Show current system status")
        print("  /help                    - Show this help")
        print("  /quit                    - Exit interactive mode")
        print("\nUser Commands (use with /commands):")
        print("  /load-category <cat>     - Force load specific category")
        print("  /unload-category <cat>   - Unload specific category")
        print("  /optimize-for <task>     - Optimize for specific task type")
        print("  /performance-mode <mode> - Set performance mode")
        print("  /tier-status             - Show tier loading status")
        print("  /function-stats          - Show function statistics")
        print()

    async def _show_system_status(self):
        """Show current system status."""
        status = await self.integration.get_system_status()

        print("\n📊 SYSTEM STATUS")
        print("-" * 20)
        print(f"Health: {status['integration_health']}")
        print(f"Mode: {status['mode']}")
        print(f"Uptime: {status['metrics']['uptime_hours']:.1f} hours")
        print(f"Queries Processed: {status['metrics']['total_queries_processed']}")
        print(f"Success Rate: {status['metrics']['success_rate']:.1f}%")
        print(f"Average Reduction: {status['metrics']['average_reduction_percentage']:.1f}%")
        print()

    async def _validate_performance(self) -> dict[str, Any]:
        """Validate performance requirements."""
        test_queries = [
            ("Simple git operation", "git status", LoadingStrategy.AGGRESSIVE, 80.0, 100.0),
            ("Code analysis", "analyze code quality", LoadingStrategy.BALANCED, 60.0, 200.0),
            ("Security audit", "security vulnerability scan", LoadingStrategy.CONSERVATIVE, 50.0, 300.0),
        ]

        results = []
        for name, query, strategy, min_reduction, max_time in test_queries:
            start_time = time.perf_counter()
            result = await self.integration.process_query(
                query=query,
                user_id="perf_test_user",
                strategy=strategy,
            )
            total_time = (time.perf_counter() - start_time) * 1000

            meets_reduction = result.reduction_percentage >= min_reduction
            meets_time = total_time <= max_time

            test_result = {
                "name": name,
                "reduction": result.reduction_percentage,
                "time_ms": total_time,
                "meets_reduction": meets_reduction,
                "meets_time": meets_time,
                "success": result.success and meets_reduction and meets_time,
            }
            results.append(test_result)

            status = "✅" if test_result["success"] else "❌"
            print(f"{status} {name}: {result.reduction_percentage:.1f}% in {total_time:.1f}ms")

        overall_success = all(r["success"] for r in results)
        return {"success": overall_success, "results": results}

    async def _validate_stress_test(self) -> dict[str, Any]:
        """Validate system under stress."""
        print("Running 20 concurrent queries...")

        queries = ["test query " + str(i) for i in range(20)]

        start_time = time.perf_counter()
        tasks = [
            self.integration.process_query(
                query=query,
                user_id=f"stress_user_{i}",
                strategy=LoadingStrategy.BALANCED,
            )
            for i, query in enumerate(queries)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = (time.perf_counter() - start_time) * 1000

        successful_results = [r for r in results if isinstance(r, ProcessingResult) and r.success]
        success_rate = len(successful_results) / len(queries)

        if successful_results:
            avg_reduction = sum(r.reduction_percentage for r in successful_results) / len(successful_results)
            avg_time = sum(r.total_time_ms for r in successful_results) / len(successful_results)
        else:
            avg_reduction = 0.0
            avg_time = 0.0

        stress_success = success_rate >= 0.9 and avg_reduction >= 40.0

        print(f"Success Rate: {success_rate:.1%}")
        print(f"Average Reduction: {avg_reduction:.1f}%")
        print(f"Average Time: {avg_time:.1f}ms")
        print(f"Total Time: {total_time:.1f}ms")

        return {
            "success": stress_success,
            "success_rate": success_rate,
            "avg_reduction": avg_reduction,
            "avg_time": avg_time,
            "total_time": total_time,
        }

    async def _validate_production_readiness(self) -> dict[str, Any]:
        """Validate production readiness criteria."""
        # Run comprehensive demo for production readiness assessment
        demo = ComprehensivePrototypeDemo(mode=IntegrationMode.TESTING)

        if not await demo.initialize():
            return {"success": False, "error": "Failed to initialize demo"}

        results = await demo.run_comprehensive_demo()
        readiness = results["production_readiness"]

        prod_ready = readiness["readiness_level"] in ["PRODUCTION_READY", "MOSTLY_READY"]

        print(f"Production Readiness: {readiness['readiness_level']}")
        print(f"Overall Score: {readiness['overall_score']:.1f}/100")

        return {
            "success": prod_ready,
            "readiness_level": readiness["readiness_level"],
            "score": readiness["overall_score"],
            "detailed_results": results,
        }

    async def _validate_basic_functionality(self) -> dict[str, Any]:
        """Validate basic functionality."""
        test_query = "help me with git operations"

        result = await self.integration.process_query(
            query=test_query,
            user_id="basic_test_user",
            strategy=LoadingStrategy.BALANCED,
        )

        basic_success = result.success and result.reduction_percentage > 0 and result.total_time_ms <= 1000.0

        status = "✅" if basic_success else "❌"
        print(
            f"{status} Basic functionality: {result.reduction_percentage:.1f}% reduction in {result.total_time_ms:.1f}ms",
        )

        return {
            "success": basic_success,
            "reduction": result.reduction_percentage,
            "time_ms": result.total_time_ms,
        }


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Dynamic Function Loading CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s demo --comprehensive
  %(prog)s optimize "analyze security vulnerabilities" --strategy aggressive
  %(prog)s validate --performance --stress-test
  %(prog)s interactive
  %(prog)s report --export results.json
        """,
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Demo command
    demo_parser = subparsers.add_parser("demo", help="Run demonstration scenarios")
    demo_parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive demo")
    demo_parser.add_argument("--scenario-types", nargs="+", help="Specific scenario types to run")

    # Optimize command
    optimize_parser = subparsers.add_parser("optimize", help="Optimize a specific query")
    optimize_parser.add_argument("query", help="Query to optimize")
    optimize_parser.add_argument(
        "--strategy",
        choices=["conservative", "balanced", "aggressive"],
        default="balanced",
        help="Loading strategy",
    )
    optimize_parser.add_argument("--user-commands", nargs="*", help="User commands to execute")
    optimize_parser.add_argument("--user-id", default="cli_user", help="User identifier")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Run validation tests")
    validate_parser.add_argument("--performance", action="store_true", help="Run performance validation")
    validate_parser.add_argument("--stress-test", action="store_true", help="Run stress test validation")
    validate_parser.add_argument(
        "--production-readiness",
        action="store_true",
        help="Run production readiness validation",
    )

    # Interactive command
    subparsers.add_parser("interactive", help="Run interactive session")

    # Report command
    report_parser = subparsers.add_parser("report", help="Generate performance report")
    report_parser.add_argument("--export", help="Export report to JSON file")

    # Global options
    parser.add_argument(
        "--mode",
        choices=["production", "development", "testing", "demo"],
        default="production",
        help="Integration mode",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    # Initialize CLI
    cli = DynamicLoadingCLI()
    mode = IntegrationMode(args.mode)

    if not await cli.initialize(mode=mode):
        sys.exit(1)

    try:
        # Execute command
        if args.command == "demo":
            success = await cli.run_demo(
                comprehensive=args.comprehensive,
                scenario_types=args.scenario_types,
            )
            sys.exit(0 if success else 1)

        elif args.command == "optimize":
            result = await cli.optimize_query(
                query=args.query,
                strategy=args.strategy,
                user_commands=args.user_commands,
                user_id=args.user_id,
            )
            sys.exit(0 if result and result.success else 1)

        elif args.command == "validate":
            validation_results = await cli.run_validation(
                performance=args.performance,
                stress_test=args.stress_test,
                production_readiness=args.production_readiness,
            )
            sys.exit(0 if validation_results["overall_success"] else 1)

        elif args.command == "interactive":
            await cli.run_interactive()
            sys.exit(0)

        elif args.command == "report":
            await cli.generate_report(export_path=args.export)
            sys.exit(0)

        else:
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
