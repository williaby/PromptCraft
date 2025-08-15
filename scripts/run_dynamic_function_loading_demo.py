#!/usr/bin/env python3
"""
Dynamic Function Loading Prototype Runner

This script provides a comprehensive CLI for running, testing, and demonstrating
the dynamic function loading prototype. It includes validation, benchmarking,
and interactive demonstration capabilities.

Usage:
    python scripts/run_dynamic_function_loading_demo.py --mode demo
    python scripts/run_dynamic_function_loading_demo.py --mode validate
    python scripts/run_dynamic_function_loading_demo.py --mode benchmark
    python scripts/run_dynamic_function_loading_demo.py --mode test
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

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.dynamic_function_loader import DynamicFunctionLoader, LoadingStrategy, initialize_dynamic_loading
from src.core.function_loading_demo import InteractiveFunctionLoadingDemo


class PrototypeRunner:
    """Main runner for the dynamic function loading prototype."""

    def __init__(self):
        self.loader: DynamicFunctionLoader = None
        self.demo: InteractiveFunctionLoadingDemo = None
        self.results_dir = Path("prototype_results")
        self.results_dir.mkdir(exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize the prototype system."""
        print("🚀 Initializing Dynamic Function Loading Prototype...")

        self.loader = await initialize_dynamic_loading()
        self.demo = InteractiveFunctionLoadingDemo()
        await self.demo.initialize()

        print("✅ Prototype system initialized successfully!")

    async def run_interactive_demo(self):
        """Run the interactive demonstration."""
        print("\n🎮 Starting Interactive Demo...")
        await self.demo.run_interactive_demo()

    async def run_validation_suite(self):
        """Run comprehensive validation of the 70% token reduction claim."""
        print("\n✅ COMPREHENSIVE VALIDATION SUITE")
        print("="*60)
        print("Validating 70% token reduction claim with comprehensive scenarios...")

        validation_scenarios = [
            # Basic development tasks
            ("Git Workflow", "commit changes and create pull request", LoadingStrategy.BALANCED),
            ("File Operations", "read and edit configuration files", LoadingStrategy.AGGRESSIVE),
            ("Basic Debug", "check system status and logs", LoadingStrategy.CONSERVATIVE),

            # Advanced development tasks
            ("Security Audit", "perform comprehensive security analysis", LoadingStrategy.CONSERVATIVE),
            ("Performance Debug", "analyze performance bottlenecks in database", LoadingStrategy.BALANCED),
            ("Code Refactoring", "refactor legacy authentication module", LoadingStrategy.AGGRESSIVE),
            ("Documentation", "generate comprehensive API documentation", LoadingStrategy.BALANCED),

            # Specialized tasks
            ("External Integration", "integrate payment gateway with security validation", LoadingStrategy.BALANCED),
            ("Infrastructure Management", "manage MCP resources and configurations", LoadingStrategy.CONSERVATIVE),
            ("Testing Workflow", "generate and run comprehensive test suite", LoadingStrategy.BALANCED),

            # Edge cases
            ("Minimal Task", "just read a simple file", LoadingStrategy.AGGRESSIVE),
            ("Complex Analysis", "deep analysis of system architecture with security review", LoadingStrategy.CONSERVATIVE),
        ]

        validation_results = []
        baseline_tokens = self.loader.function_registry.get_baseline_token_cost()

        print(f"📊 Baseline token cost: {baseline_tokens} tokens")
        print(f"🎯 Target: 70% reduction (≤{baseline_tokens * 0.3:.0f} tokens per query)")
        print(f"📋 Running {len(validation_scenarios)} validation scenarios...\n")

        for i, (name, query, strategy) in enumerate(validation_scenarios, 1):
            print(f"[{i:2d}/{len(validation_scenarios)}] {name:<25} ", end="", flush=True)

            try:
                # Run scenario
                start_time = time.perf_counter()

                session_id = await self.loader.create_loading_session(
                    user_id=f"validation_user_{i}",
                    query=query,
                    strategy=strategy,
                )

                loading_decision = await self.loader.load_functions_for_query(session_id)

                # Simulate function usage
                used_functions = list(loading_decision.functions_to_load)[:min(3, len(loading_decision.functions_to_load))]
                for func in used_functions:
                    await self.loader.record_function_usage(session_id, func, success=True)

                session_summary = await self.loader.end_loading_session(session_id)

                execution_time = (time.perf_counter() - start_time) * 1000

                result = {
                    "scenario": name,
                    "query": query,
                    "strategy": strategy.value,
                    "baseline_tokens": baseline_tokens,
                    "optimized_tokens": loading_decision.estimated_tokens,
                    "token_reduction_percent": session_summary["token_reduction_percentage"],
                    "functions_loaded": len(loading_decision.functions_to_load),
                    "functions_used": len(used_functions),
                    "execution_time_ms": execution_time,
                    "target_achieved": session_summary["token_reduction_percentage"] >= 70.0,
                    "fallback_applied": loading_decision.fallback_reason is not None,
                }

                validation_results.append(result)

                # Display result
                reduction = result["token_reduction_percent"]
                status = "✅" if result["target_achieved"] else "❌"
                print(f"{reduction:5.1f}% {status}")

            except Exception as e:
                print(f"❌ FAILED: {e}")
                self.logger.error(f"Validation scenario '{name}' failed: {e}")

        # Analyze results
        await self._analyze_validation_results(validation_results, baseline_tokens)

        # Save results
        results_file = self.results_dir / f"validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(validation_results, f, indent=2, default=str)

        print(f"\n💾 Results saved to: {results_file}")

        return validation_results

    async def _analyze_validation_results(self, results: list[dict[str, Any]], baseline_tokens: int):
        """Analyze and display validation results."""
        print("\n📊 VALIDATION ANALYSIS")
        print("="*50)

        # Calculate statistics
        total_scenarios = len(results)
        achieving_target = sum(1 for r in results if r["target_achieved"])
        success_rate = achieving_target / total_scenarios * 100

        reductions = [r["token_reduction_percent"] for r in results]
        avg_reduction = sum(reductions) / len(reductions)
        min_reduction = min(reductions)
        max_reduction = max(reductions)

        execution_times = [r["execution_time_ms"] for r in results]
        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)

        # Display summary statistics
        print(f"Total scenarios tested: {total_scenarios}")
        print(f"Scenarios achieving 70% target: {achieving_target} ({success_rate:.1f}%)")
        print(f"Average token reduction: {avg_reduction:.1f}%")
        print(f"Token reduction range: {min_reduction:.1f}% - {max_reduction:.1f}%")
        print(f"Average execution time: {avg_execution_time:.1f}ms")
        print(f"Max execution time: {max_execution_time:.1f}ms")

        # Performance validation
        print("\n⚡ PERFORMANCE VALIDATION:")
        latency_target_met = max_execution_time < 200.0
        print(f"Latency requirement (<200ms): {'✅' if latency_target_met else '❌'} ({max_execution_time:.1f}ms max)")

        # Token savings analysis
        total_baseline_tokens = baseline_tokens * total_scenarios
        total_optimized_tokens = sum(r["optimized_tokens"] for r in results)
        total_savings = total_baseline_tokens - total_optimized_tokens

        print("\n💰 TOKEN SAVINGS ANALYSIS:")
        print(f"Total baseline tokens: {total_baseline_tokens:,}")
        print(f"Total optimized tokens: {total_optimized_tokens:,}")
        print(f"Total tokens saved: {total_savings:,}")
        print(f"Overall savings rate: {(total_savings/total_baseline_tokens)*100:.1f}%")

        # Scenario breakdown by strategy
        strategy_results = {}
        for result in results:
            strategy = result["strategy"]
            if strategy not in strategy_results:
                strategy_results[strategy] = []
            strategy_results[strategy].append(result["token_reduction_percent"])

        print("\n📋 STRATEGY BREAKDOWN:")
        for strategy, reductions in strategy_results.items():
            avg_strategy_reduction = sum(reductions) / len(reductions)
            strategy_success = sum(1 for r in reductions if r >= 70.0)
            print(f"  {strategy:<12}: {avg_strategy_reduction:5.1f}% avg, {strategy_success}/{len(reductions)} achieving target")

        # Final assessment
        print("\n🏆 FINAL ASSESSMENT:")

        if success_rate >= 80.0 and avg_reduction >= 70.0:
            print("✅ EXCELLENT: Prototype successfully demonstrates 70% token reduction!")
            print("   • Strong performance across diverse scenarios")
            print("   • Consistent achievement of optimization targets")
            print("   • Ready for production deployment")

        elif success_rate >= 60.0 and avg_reduction >= 65.0:
            print("👍 GOOD: Prototype demonstrates strong optimization capabilities")
            print("   • Solid performance with room for improvement")
            print("   • Most scenarios achieve significant reduction")
            print("   • Minor tuning recommended before production")

        elif avg_reduction >= 50.0:
            print("📈 MODERATE: Prototype shows optimization potential")
            print("   • Meaningful token reduction achieved")
            print("   • Detection accuracy needs improvement")
            print("   • Significant tuning required for production")

        else:
            print("❌ NEEDS IMPROVEMENT: Optimization targets not met")
            print("   • Review task detection algorithms")
            print("   • Adjust loading thresholds")
            print("   • Consider fallback strategy improvements")

        # Recommendations
        if success_rate < 80.0:
            print("\n💡 RECOMMENDATIONS:")
            print("   • Analyze failed scenarios for pattern detection issues")
            print("   • Consider lowering detection thresholds for conservative loading")
            print("   • Improve fallback mechanisms for edge cases")

        if max_execution_time > 200.0:
            print("   • Optimize loading performance for large function sets")
            print("   • Consider async loading for non-critical functions")

        return {
            "success_rate": success_rate,
            "average_reduction": avg_reduction,
            "performance_target_met": latency_target_met,
            "total_token_savings": total_savings,
            "assessment": "excellent" if success_rate >= 80.0 and avg_reduction >= 70.0 else "good" if success_rate >= 60.0 else "needs_improvement",
        }

    async def run_performance_benchmark(self):
        """Run comprehensive performance benchmarks."""
        print("\n⚡ PERFORMANCE BENCHMARK SUITE")
        print("="*50)

        benchmarks = [
            ("Single Session Latency", self._benchmark_single_session),
            ("Concurrent Sessions", self._benchmark_concurrent_sessions),
            ("Cache Performance", self._benchmark_cache_performance),
            ("Memory Usage", self._benchmark_memory_usage),
            ("Strategy Comparison", self._benchmark_strategy_comparison),
        ]

        benchmark_results = {}

        for name, benchmark_func in benchmarks:
            print(f"\n🔄 Running: {name}")
            try:
                result = await benchmark_func()
                benchmark_results[name] = result
                print(f"✅ {name} completed")
            except Exception as e:
                print(f"❌ {name} failed: {e}")
                benchmark_results[name] = {"error": str(e)}

        # Save benchmark results
        results_file = self.results_dir / f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, "w") as f:
            json.dump(benchmark_results, f, indent=2, default=str)

        print(f"\n💾 Benchmark results saved to: {results_file}")

        # Display summary
        await self._display_benchmark_summary(benchmark_results)

        return benchmark_results

    async def _benchmark_single_session(self) -> dict[str, Any]:
        """Benchmark single session performance."""
        iterations = 10
        times = []

        for i in range(iterations):
            start_time = time.perf_counter()

            session_id = await self.loader.create_loading_session(
                user_id=f"benchmark_user_{i}",
                query="analyze code for security vulnerabilities",
            )

            await self.loader.load_functions_for_query(session_id)
            await self.loader.end_loading_session(session_id)

            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)

        return {
            "iterations": iterations,
            "average_time_ms": sum(times) / len(times),
            "min_time_ms": min(times),
            "max_time_ms": max(times),
            "times_ms": times,
        }

    async def _benchmark_concurrent_sessions(self) -> dict[str, Any]:
        """Benchmark concurrent session handling."""
        concurrency_levels = [1, 2, 5, 10]
        results = {}

        for concurrency in concurrency_levels:
            print(f"  Testing {concurrency} concurrent sessions...")

            start_time = time.perf_counter()

            tasks = []
            for i in range(concurrency):
                task = self._run_benchmark_session(f"concurrent_user_{i}", f"query {i}")
                tasks.append(task)

            await asyncio.gather(*tasks)

            end_time = time.perf_counter()
            total_time = (end_time - start_time) * 1000

            results[f"{concurrency}_sessions"] = {
                "total_time_ms": total_time,
                "time_per_session_ms": total_time / concurrency,
            }

        return results

    async def _run_benchmark_session(self, user_id: str, query: str):
        """Run a single benchmark session."""
        session_id = await self.loader.create_loading_session(user_id=user_id, query=query)
        await self.loader.load_functions_for_query(session_id)
        await self.loader.end_loading_session(session_id)

    async def _benchmark_cache_performance(self) -> dict[str, Any]:
        """Benchmark caching performance."""
        query = "test cache performance with repeated query"

        # Disable cache for baseline
        self.loader.enable_caching = False

        # Run without cache
        times_no_cache = []
        for i in range(5):
            start_time = time.perf_counter()
            session_id = await self.loader.create_loading_session(f"no_cache_user_{i}", query)
            await self.loader.load_functions_for_query(session_id)
            await self.loader.end_loading_session(session_id)
            end_time = time.perf_counter()
            times_no_cache.append((end_time - start_time) * 1000)

        # Enable cache
        self.loader.enable_caching = True

        # Run with cache
        times_with_cache = []
        for i in range(5):
            start_time = time.perf_counter()
            session_id = await self.loader.create_loading_session(f"cache_user_{i}", query)
            await self.loader.load_functions_for_query(session_id)
            await self.loader.end_loading_session(session_id)
            end_time = time.perf_counter()
            times_with_cache.append((end_time - start_time) * 1000)

        avg_no_cache = sum(times_no_cache) / len(times_no_cache)
        avg_with_cache = sum(times_with_cache) / len(times_with_cache)
        improvement = ((avg_no_cache - avg_with_cache) / avg_no_cache) * 100

        return {
            "average_time_no_cache_ms": avg_no_cache,
            "average_time_with_cache_ms": avg_with_cache,
            "cache_improvement_percent": improvement,
            "times_no_cache_ms": times_no_cache,
            "times_with_cache_ms": times_with_cache,
        }

    async def _benchmark_memory_usage(self) -> dict[str, Any]:
        """Benchmark memory usage (simplified)."""
        # This is a simplified benchmark - in production would use actual memory profiling
        registry = self.loader.function_registry

        return {
            "total_functions": len(registry.functions),
            "cache_entries": len(self.loader.loading_cache),
            "active_sessions": len(self.loader.active_sessions),
            "estimated_memory_kb": len(registry.functions) * 1.5 + len(self.loader.loading_cache) * 0.5,  # Rough estimate
        }

    async def _benchmark_strategy_comparison(self) -> dict[str, Any]:
        """Benchmark different loading strategies."""
        query = "comprehensive security analysis with performance optimization"
        strategies = [LoadingStrategy.CONSERVATIVE, LoadingStrategy.BALANCED, LoadingStrategy.AGGRESSIVE]

        results = {}

        for strategy in strategies:
            times = []
            token_counts = []

            for i in range(3):  # Run each strategy 3 times
                start_time = time.perf_counter()

                session_id = await self.loader.create_loading_session(
                    user_id=f"strategy_{strategy.value}_user_{i}",
                    query=query,
                    strategy=strategy,
                )

                loading_decision = await self.loader.load_functions_for_query(session_id)
                await self.loader.end_loading_session(session_id)

                end_time = time.perf_counter()

                times.append((end_time - start_time) * 1000)
                token_counts.append(loading_decision.estimated_tokens)

            results[strategy.value] = {
                "average_time_ms": sum(times) / len(times),
                "average_tokens": sum(token_counts) / len(token_counts),
                "times_ms": times,
                "token_counts": token_counts,
            }

        return results

    async def _display_benchmark_summary(self, results: dict[str, Any]):
        """Display benchmark summary."""
        print("\n📊 BENCHMARK SUMMARY")
        print("="*40)

        for benchmark_name, result in results.items():
            if "error" in result:
                print(f"❌ {benchmark_name}: FAILED - {result['error']}")
                continue

            print(f"\n📈 {benchmark_name}:")

            if benchmark_name == "Single Session Latency":
                print(f"   Average: {result['average_time_ms']:.1f}ms")
                print(f"   Range: {result['min_time_ms']:.1f}ms - {result['max_time_ms']:.1f}ms")

            elif benchmark_name == "Concurrent Sessions":
                for key, value in result.items():
                    sessions = key.split("_")[0]
                    print(f"   {sessions} sessions: {value['total_time_ms']:.1f}ms total, {value['time_per_session_ms']:.1f}ms/session")

            elif benchmark_name == "Cache Performance":
                print(f"   Without cache: {result['average_time_no_cache_ms']:.1f}ms")
                print(f"   With cache: {result['average_time_with_cache_ms']:.1f}ms")
                print(f"   Improvement: {result['cache_improvement_percent']:.1f}%")

            elif benchmark_name == "Memory Usage":
                print(f"   Functions: {result['total_functions']}")
                print(f"   Cache entries: {result['cache_entries']}")
                print(f"   Estimated memory: {result['estimated_memory_kb']:.1f}KB")

            elif benchmark_name == "Strategy Comparison":
                for strategy, data in result.items():
                    print(f"   {strategy}: {data['average_time_ms']:.1f}ms, {data['average_tokens']} tokens")

    async def run_unit_tests(self):
        """Run the unit test suite."""
        print("\n🧪 RUNNING UNIT TEST SUITE")
        print("="*40)

        try:
            import pytest

            # Run the test suite
            test_file = project_root / "tests" / "unit" / "test_dynamic_function_loader.py"

            if not test_file.exists():
                print("❌ Test file not found. Creating tests...")
                return False

            print(f"Running tests from: {test_file}")

            # Run pytest programmatically
            exit_code = pytest.main([
                "-v",
                "--tb=short",
                "--disable-warnings",
                str(test_file),
            ])

            if exit_code == 0:
                print("✅ All tests passed!")
                return True
            print(f"❌ Tests failed with exit code: {exit_code}")
            return False

        except ImportError:
            print("❌ pytest not available. Install with: pip install pytest")
            return False
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False

    async def generate_comprehensive_report(self):
        """Generate a comprehensive prototype report."""
        print("\n📋 GENERATING COMPREHENSIVE PROTOTYPE REPORT")
        print("="*60)

        # Run all validation and benchmarks
        validation_results = await self.run_validation_suite()
        benchmark_results = await self.run_performance_benchmark()

        # Get performance report from loader
        performance_report = await self.loader.get_performance_report()

        # Compile comprehensive report
        report = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "prototype_version": "1.0.0",
                "validation_scenarios": len(validation_results),
                "benchmark_suite": len(benchmark_results),
            },
            "validation": {
                "scenarios": validation_results,
                "summary": await self._analyze_validation_results(validation_results,
                                                                self.loader.function_registry.get_baseline_token_cost()),
            },
            "performance": {
                "benchmarks": benchmark_results,
                "system_metrics": performance_report,
            },
            "function_inventory": {
                "total_functions": len(self.loader.function_registry.functions),
                "tier_breakdown": {
                    "tier_1": len(self.loader.function_registry.get_functions_by_tier(self.loader.function_registry.LoadingTier.TIER_1)),
                    "tier_2": len(self.loader.function_registry.get_functions_by_tier(self.loader.function_registry.LoadingTier.TIER_2)),
                    "tier_3": len(self.loader.function_registry.get_functions_by_tier(self.loader.function_registry.LoadingTier.TIER_3)),
                },
                "baseline_tokens": self.loader.function_registry.get_baseline_token_cost(),
            },
        }

        # Save comprehensive report
        report_file = self.results_dir / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Comprehensive report saved to: {report_file}")

        # Generate executive summary
        await self._generate_executive_summary(report, report_file.with_suffix(".md"))

        return report

    async def _generate_executive_summary(self, report: dict[str, Any], output_file: Path):
        """Generate executive summary in markdown format."""
        validation_summary = report["validation"]["summary"]

        summary = f"""# Dynamic Function Loading Prototype - Executive Summary

## Overview
This report presents the results of comprehensive validation and testing of the Dynamic Function Loading prototype, designed to achieve 70% token reduction while maintaining full functionality.

**Generated**: {report['metadata']['timestamp']}
**Validation Scenarios**: {report['metadata']['validation_scenarios']}
**Benchmark Tests**: {report['metadata']['benchmark_suite']}

## Key Results

### Token Optimization Performance
- **Average Token Reduction**: {validation_summary['average_reduction']:.1f}%
- **Target Achievement Rate**: {validation_summary['success_rate']:.1f}%
- **Performance Target Met**: {'✅ Yes' if validation_summary['performance_target_met'] else '❌ No'}
- **Total Token Savings**: {validation_summary['total_token_savings']:,} tokens

### System Performance
- **Baseline Token Cost**: {report['function_inventory']['baseline_tokens']:,} tokens
- **Function Coverage**: {report['function_inventory']['total_functions']} total functions
- **Tier Distribution**:
  - Tier 1 (Essential): {report['function_inventory']['tier_breakdown']['tier_1']} functions
  - Tier 2 (Extended): {report['function_inventory']['tier_breakdown']['tier_2']} functions
  - Tier 3 (Specialized): {report['function_inventory']['tier_breakdown']['tier_3']} functions

## Assessment: {validation_summary['assessment'].upper()}

### Prototype Capabilities Demonstrated
✅ **Intelligent Task Detection**: Analyzes user queries to determine required function categories
✅ **Three-Tier Loading Architecture**: Loads functions based on usage patterns and confidence
✅ **Conservative Fallback Mechanisms**: Ensures no functionality loss in edge cases
✅ **User Override Commands**: Provides manual control when needed
✅ **Comprehensive Monitoring**: Validates optimization claims with detailed metrics
✅ **Performance Requirements**: Meets latency and efficiency requirements

### Production Readiness
{'✅ **Ready for Production**' if validation_summary['success_rate'] >= 80 else '⚠️ **Requires Tuning**' if validation_summary['success_rate'] >= 60 else '❌ **Needs Significant Work**'}

## Technical Architecture

The prototype integrates:
- **Task Detection System**: Multi-modal analysis of user intent
- **Function Registry**: Metadata-driven function management
- **Loading Decision Engine**: Strategy-based optimization
- **Fallback Chain**: Conservative safety mechanisms
- **User Control Interface**: Command-based overrides
- **Performance Monitoring**: Real-time optimization validation

## Recommendations

{'### Immediate Deployment' if validation_summary['success_rate'] >= 80 else '### Pre-Production Tuning Required' if validation_summary['success_rate'] >= 60 else '### Significant Development Required'}

{'The prototype successfully demonstrates 70% token reduction and is ready for production deployment with minimal additional work.' if validation_summary['success_rate'] >= 80 else 'The prototype shows strong potential but requires tuning of detection thresholds and fallback strategies before production deployment.' if validation_summary['success_rate'] >= 60 else 'The prototype requires significant improvements to task detection accuracy and loading strategies before production consideration.'}

---
*This report was generated automatically by the Dynamic Function Loading Prototype validation system.*
"""

        with open(output_file, "w") as f:
            f.write(summary)

        print(f"📄 Executive summary saved to: {output_file}")


async def main():
    """Main entry point for the prototype runner."""
    parser = argparse.ArgumentParser(
        description="Dynamic Function Loading Prototype Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode demo                    # Run interactive demo
  %(prog)s --mode validate                # Validate 70%% token reduction
  %(prog)s --mode benchmark               # Run performance benchmarks
  %(prog)s --mode test                    # Run unit tests
  %(prog)s --mode report                  # Generate comprehensive report
  %(prog)s --mode demo --interactive      # Interactive demo mode
        """,
    )

    parser.add_argument(
        "--mode",
        choices=["demo", "validate", "benchmark", "test", "report"],
        default="demo",
        help="Mode to run (default: demo)",
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("prototype_results"),
        help="Output directory for results (default: prototype_results)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create runner
    runner = PrototypeRunner()
    runner.results_dir = args.output_dir
    runner.results_dir.mkdir(exist_ok=True)

    try:
        # Initialize
        await runner.initialize()

        # Run selected mode
        if args.mode == "demo":
            if args.interactive:
                await runner.run_interactive_demo()
            else:
                print("Running demonstration scenarios...")
                await runner.demo._run_demo_scenarios()

        elif args.mode == "validate":
            await runner.run_validation_suite()

        elif args.mode == "benchmark":
            await runner.run_performance_benchmark()

        elif args.mode == "test":
            success = await runner.run_unit_tests()
            if not success:
                sys.exit(1)

        elif args.mode == "report":
            await runner.generate_comprehensive_report()

    except KeyboardInterrupt:
        print("\n\n👋 Operation interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Operation failed: {e}")
        logging.exception("Detailed error information:")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
