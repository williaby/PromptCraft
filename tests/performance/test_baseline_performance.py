"""
Baseline performance testing framework for PromptCraft Phase 1 NEW-8.

This module implements comprehensive baseline performance testing for the QueryCounselor
and HydeProcessor components, establishing performance benchmarks and SLA validation
for the <2 second response time requirement.

Key Features:
- Baseline performance measurement for all core components
- Integration testing between QueryCounselor and HydeProcessor
- SLA compliance validation (<2s p95 response time)
- Memory usage monitoring and validation
- Concurrent processing capability testing
- Performance regression detection
- Comprehensive reporting and analytics

Architecture:
    The baseline testing framework establishes initial performance benchmarks
    for Week 1 components before real integration in Week 2. It validates
    that the foundation components meet performance requirements under
    various load conditions.

Dependencies:
    - src.core.query_counselor: QueryCounselor implementation
    - src.core.hyde_processor: HydeProcessor implementation
    - src.utils.performance_monitor: Performance measurement infrastructure
    - tests.performance.performance_config: Test configuration and validation

Test Categories:
    - Unit performance tests for individual components
    - Integration performance tests for component workflows
    - Concurrent processing tests for scalability validation
    - Memory usage tests for resource constraint validation
    - End-to-end workflow performance tests

Complexity: O(n*m) where n is number of test scenarios and m is component complexity
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from src.core.hyde_processor import EnhancedQuery, HydeProcessor, RankedResults, SpecificityLevel
from src.core.query_counselor import FinalResponse, QueryCounselor, QueryIntent, QueryType
from src.utils.performance_monitor import (
    MetricData,
    MetricType,
    PerformanceMonitor,
    PerformanceTracker,
    SLAMonitor,
    track_performance,
)
from tests.performance.performance_config import (
    DEFAULT_THRESHOLDS,
    PerformanceThresholds,
    PerformanceValidator,
)

# Configure logging for performance tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test constants aligned with Week 1 requirements
BASELINE_SLA_RESPONSE_TIME = 2.0  # <2 second p95 requirement
MAX_MEMORY_USAGE_MB = 2048.0  # 2GB memory limit
MIN_CONCURRENT_REQUESTS = 10  # Minimum concurrent processing capability
PERFORMANCE_TEST_ITERATIONS = 50  # Number of iterations for stable baselines

# Test query samples for different complexity levels
SIMPLE_QUERIES = [
    "Create a basic prompt",
    "Help with documentation",
    "Generate a template",
    "Analyze code quality",
    "Simple task automation",
]

MEDIUM_QUERIES = [
    "Create a comprehensive prompt for code generation with error handling",
    "Analyze the performance characteristics of this Python implementation",
    "Generate a template for CI/CD pipeline configuration with testing stages",
    "Document the API endpoints with authentication and rate limiting details",
    "Enhance this prompt with better context and examples for LLM processing",
]

COMPLEX_QUERIES = [
    "Create a detailed multi-agent orchestration prompt for analyzing large codebases, including performance optimization strategies, security vulnerability detection, and architectural improvement recommendations with specific implementation guidelines",
    "Generate a comprehensive template system for enterprise-grade CI/CD pipelines that includes automated testing, security scanning, deployment strategies, rollback mechanisms, monitoring integration, and compliance validation across multiple environments",
    "Analyze and document the complete architecture of a distributed system including microservices communication patterns, data flow optimization, scalability considerations, fault tolerance mechanisms, and performance monitoring with detailed implementation examples",
]

ALL_TEST_QUERIES = SIMPLE_QUERIES + MEDIUM_QUERIES + COMPLEX_QUERIES


class BaselinePerformanceTestSuite:
    """
    Comprehensive baseline performance testing suite for Phase 1 components.

    Establishes performance benchmarks and validates SLA compliance for
    QueryCounselor and HydeProcessor integration before Week 2 real integrations.
    """

    def __init__(self) -> None:
        """Initialize baseline performance test suite."""
        self.performance_monitor = PerformanceMonitor(max_samples=10000)
        self.sla_monitor = SLAMonitor(
            {
                "response_time_p95": BASELINE_SLA_RESPONSE_TIME,
                "response_time_p99": 5.0,
                "success_rate": 0.99,
                "memory_usage_mb": MAX_MEMORY_USAGE_MB,
            },
        )
        self.validator = PerformanceValidator(DEFAULT_THRESHOLDS)
        self.query_counselor = QueryCounselor()
        self.hyde_processor = HydeProcessor()
        self.logger = logger

    async def test_query_counselor_baseline_performance(self) -> dict[str, Any]:
        """
        Test baseline performance of QueryCounselor component.

        Returns:
            Dict containing performance metrics and validation results
        """
        self.logger.info("Starting QueryCounselor baseline performance test")

        results = {
            "component": "QueryCounselor",
            "test_iterations": PERFORMANCE_TEST_ITERATIONS,
            "metrics": {},
            "sla_compliance": {},
            "memory_usage": {},
        }

        # Test intent analysis performance
        intent_analysis_times = []
        for i in range(PERFORMANCE_TEST_ITERATIONS):
            query = ALL_TEST_QUERIES[i % len(ALL_TEST_QUERIES)]

            with track_performance("query_counselor_intent_analysis") as tracker:
                intent = await self.query_counselor.analyze_intent(query)
                intent_analysis_times.append(tracker.start_time - time.time() if tracker.start_time else 0.0)

        # Test agent selection performance
        agent_selection_times = []
        for i in range(PERFORMANCE_TEST_ITERATIONS):
            # Create mock intent for testing
            intent = QueryIntent(
                query_type=QueryType.CREATE_ENHANCEMENT,
                confidence=0.8,
                complexity="medium",
                requires_agents=["create_agent"],
            )

            with track_performance("query_counselor_agent_selection") as tracker:
                agents = await self.query_counselor.select_agents(intent)
                agent_selection_times.append(tracker.start_time - time.time() if tracker.start_time else 0.0)

        # Test workflow orchestration performance
        orchestration_times = []
        for i in range(PERFORMANCE_TEST_ITERATIONS):
            query = ALL_TEST_QUERIES[i % len(ALL_TEST_QUERIES)]
            agents = await self.query_counselor.select_agents(
                QueryIntent(
                    query_type=QueryType.GENERAL_QUERY,
                    confidence=0.7,
                    complexity="simple",
                    requires_agents=["general_agent"],
                ),
            )

            with track_performance("query_counselor_orchestration") as tracker:
                responses = await self.query_counselor.orchestrate_workflow(agents, query)
                orchestration_times.append(tracker.start_time - time.time() if tracker.start_time else 0.0)

        # Calculate performance metrics
        results["metrics"] = {
            "intent_analysis": self._calculate_performance_stats(intent_analysis_times),
            "agent_selection": self._calculate_performance_stats(agent_selection_times),
            "workflow_orchestration": self._calculate_performance_stats(orchestration_times),
        }

        # Validate SLA compliance
        all_metrics = self.performance_monitor.get_all_metrics()
        results["sla_compliance"] = self.sla_monitor.check_sla_compliance(all_metrics)

        self.logger.info("QueryCounselor baseline performance test completed")
        return results

    async def test_hyde_processor_baseline_performance(self) -> dict[str, Any]:
        """
        Test baseline performance of HydeProcessor component.

        Returns:
            Dict containing performance metrics and validation results
        """
        self.logger.info("Starting HydeProcessor baseline performance test")

        results = {
            "component": "HydeProcessor",
            "test_iterations": PERFORMANCE_TEST_ITERATIONS,
            "metrics": {},
            "sla_compliance": {},
            "specificity_analysis": {},
        }

        # Test three-tier analysis performance
        analysis_times = []
        specificity_distribution = {"high": 0, "medium": 0, "low": 0}

        for i in range(PERFORMANCE_TEST_ITERATIONS):
            query = ALL_TEST_QUERIES[i % len(ALL_TEST_QUERIES)]

            with track_performance("hyde_processor_analysis") as tracker:
                enhanced_query = await self.hyde_processor.three_tier_analysis(query)
                analysis_times.append(tracker.start_time - time.time() if tracker.start_time else 0.0)

                # Track specificity distribution
                specificity_distribution[enhanced_query.specificity_analysis.specificity_level.value] += 1

        # Test hypothetical document generation performance
        doc_generation_times = []
        for i in range(PERFORMANCE_TEST_ITERATIONS // 2):  # Fewer iterations for doc generation
            query = MEDIUM_QUERIES[i % len(MEDIUM_QUERIES)]  # Use medium complexity queries

            with track_performance("hyde_processor_doc_generation") as tracker:
                docs = await self.hyde_processor.generate_hypothetical_docs(query)
                doc_generation_times.append(tracker.start_time - time.time() if tracker.start_time else 0.0)

        # Test full query processing pipeline
        processing_times = []
        for i in range(PERFORMANCE_TEST_ITERATIONS):
            query = ALL_TEST_QUERIES[i % len(ALL_TEST_QUERIES)]

            with track_performance("hyde_processor_full_pipeline") as tracker:
                ranked_results = await self.hyde_processor.process_query(query)
                processing_times.append(tracker.start_time - time.time() if tracker.start_time else 0.0)

        # Calculate performance metrics
        results["metrics"] = {
            "three_tier_analysis": self._calculate_performance_stats(analysis_times),
            "doc_generation": self._calculate_performance_stats(doc_generation_times),
            "full_pipeline": self._calculate_performance_stats(processing_times),
        }

        results["specificity_analysis"] = specificity_distribution

        # Validate SLA compliance
        all_metrics = self.performance_monitor.get_all_metrics()
        results["sla_compliance"] = self.sla_monitor.check_sla_compliance(all_metrics)

        self.logger.info("HydeProcessor baseline performance test completed")
        return results

    async def test_integrated_workflow_performance(self) -> dict[str, Any]:
        """
        Test baseline performance of integrated QueryCounselor + HydeProcessor workflow.

        Returns:
            Dict containing integrated workflow performance metrics
        """
        self.logger.info("Starting integrated workflow baseline performance test")

        results = {
            "component": "IntegratedWorkflow",
            "test_iterations": PERFORMANCE_TEST_ITERATIONS,
            "metrics": {},
            "workflow_analysis": {},
            "sla_compliance": {},
        }

        workflow_times = []
        hyde_usage_count = 0
        workflow_success_count = 0

        for i in range(PERFORMANCE_TEST_ITERATIONS):
            query = ALL_TEST_QUERIES[i % len(ALL_TEST_QUERIES)]

            with track_performance("integrated_workflow") as tracker:
                # Step 1: Query counselor analyzes intent
                intent = await self.query_counselor.analyze_intent(query)

                # Step 2: HyDE processing if recommended
                enhanced_query = None
                if intent.hyde_recommended:
                    enhanced_query = await self.hyde_processor.three_tier_analysis(query)
                    hyde_usage_count += 1

                # Step 3: Agent selection and orchestration
                agents = await self.query_counselor.select_agents(intent)
                responses = await self.query_counselor.orchestrate_workflow(agents, query)

                # Step 4: Response synthesis
                final_response = await self.query_counselor.synthesize_response(responses)

                workflow_times.append(tracker.start_time - time.time() if tracker.start_time else 0.0)

                # Track success rate
                if final_response.confidence > 0.5:  # Consider successful if confidence > 0.5
                    workflow_success_count += 1

        # Calculate performance metrics
        results["metrics"] = {
            "end_to_end_workflow": self._calculate_performance_stats(workflow_times),
        }

        results["workflow_analysis"] = {
            "hyde_usage_rate": (hyde_usage_count / PERFORMANCE_TEST_ITERATIONS) * 100,
            "workflow_success_rate": (workflow_success_count / PERFORMANCE_TEST_ITERATIONS) * 100,
            "average_workflow_time": sum(workflow_times) / len(workflow_times),
        }

        # Validate SLA compliance
        all_metrics = self.performance_monitor.get_all_metrics()
        results["sla_compliance"] = self.sla_monitor.check_sla_compliance(all_metrics)

        self.logger.info("Integrated workflow baseline performance test completed")
        return results

    async def test_concurrent_processing_performance(self) -> dict[str, Any]:
        """
        Test concurrent processing capabilities of the system.

        Returns:
            Dict containing concurrent processing performance metrics
        """
        self.logger.info("Starting concurrent processing performance test")

        results = {
            "component": "ConcurrentProcessing",
            "concurrent_requests": MIN_CONCURRENT_REQUESTS,
            "metrics": {},
            "scalability_analysis": {},
        }

        async def process_single_query(query: str, request_id: int) -> dict[str, Any]:
            """Process a single query and return performance data."""
            start_time = time.time()

            try:
                # Full integrated workflow
                intent = await self.query_counselor.analyze_intent(query)

                if intent.hyde_recommended:
                    enhanced_query = await self.hyde_processor.three_tier_analysis(query)

                agents = await self.query_counselor.select_agents(intent)
                responses = await self.query_counselor.orchestrate_workflow(agents, query)
                final_response = await self.query_counselor.synthesize_response(responses)

                processing_time = time.time() - start_time

                return {
                    "request_id": request_id,
                    "processing_time": processing_time,
                    "success": True,
                    "confidence": final_response.confidence,
                }

            except Exception as e:
                processing_time = time.time() - start_time
                return {
                    "request_id": request_id,
                    "processing_time": processing_time,
                    "success": False,
                    "error": str(e),
                }

        # Test with different concurrency levels
        concurrency_levels = [1, 5, 10, 15, 20]
        concurrency_results = {}

        for concurrency in concurrency_levels:
            self.logger.info("Testing concurrency level: %s", concurrency)

            # Create concurrent tasks
            tasks = []
            for i in range(concurrency):
                query = ALL_TEST_QUERIES[i % len(ALL_TEST_QUERIES)]
                task = process_single_query(query, i)
                tasks.append(task)

            # Execute concurrent requests
            start_time = time.time()
            concurrent_results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            # Analyze results
            successful_requests = sum(1 for r in concurrent_results if isinstance(r, dict) and r.get("success", False))
            processing_times = [r["processing_time"] for r in concurrent_results if isinstance(r, dict)]

            concurrency_results[concurrency] = {
                "total_requests": concurrency,
                "successful_requests": successful_requests,
                "success_rate": (successful_requests / concurrency) * 100,
                "total_time": total_time,
                "throughput_rps": concurrency / total_time,
                "avg_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
                "p95_processing_time": self._calculate_percentile(processing_times, 95) if processing_times else 0,
            }

        results["metrics"] = concurrency_results

        # Analyze scalability characteristics
        results["scalability_analysis"] = {
            "max_concurrent_capacity": max(
                level
                for level, data in concurrency_results.items()
                if data["success_rate"] >= 95 and data["p95_processing_time"] <= BASELINE_SLA_RESPONSE_TIME
            ),
            "throughput_scaling": {level: data["throughput_rps"] for level, data in concurrency_results.items()},
            "performance_degradation": self._analyze_performance_degradation(concurrency_results),
        }

        self.logger.info("Concurrent processing performance test completed")
        return results

    async def test_memory_usage_performance(self) -> dict[str, Any]:
        """
        Test memory usage characteristics under various load conditions.

        Returns:
            Dict containing memory usage analysis
        """
        self.logger.info("Starting memory usage performance test")

        results = {
            "component": "MemoryUsage",
            "test_duration_seconds": 60,
            "metrics": {},
            "memory_analysis": {},
        }

        import gc

        import psutil

        # Monitor memory usage during sustained load
        memory_samples = []
        gc_collections = {"before": gc.get_count(), "after": None}

        start_time = time.time()
        process = psutil.Process()

        # Initial memory baseline
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run sustained load for 60 seconds
        iteration_count = 0
        while time.time() - start_time < 60:
            query = ALL_TEST_QUERIES[iteration_count % len(ALL_TEST_QUERIES)]

            # Process query through full pipeline
            intent = await self.query_counselor.analyze_intent(query)

            if intent.hyde_recommended:
                enhanced_query = await self.hyde_processor.three_tier_analysis(query)

            agents = await self.query_counselor.select_agents(intent)
            responses = await self.query_counselor.orchestrate_workflow(agents, query)
            final_response = await self.query_counselor.synthesize_response(responses)

            # Sample memory usage every 10 iterations
            if iteration_count % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_samples.append(
                    {
                        "iteration": iteration_count,
                        "memory_mb": current_memory,
                        "memory_growth_mb": current_memory - initial_memory,
                        "timestamp": time.time() - start_time,
                    },
                )

            iteration_count += 1

            # Small delay to prevent overwhelming the system
            await asyncio.sleep(0.1)

        # Final memory measurement
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        gc_collections["after"] = gc.get_count()

        # Analyze memory usage patterns
        memory_values = [sample["memory_mb"] for sample in memory_samples]
        memory_growth_values = [sample["memory_growth_mb"] for sample in memory_samples]

        results["metrics"] = {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "peak_memory_mb": max(memory_values) if memory_values else initial_memory,
            "total_memory_growth_mb": final_memory - initial_memory,
            "avg_memory_mb": sum(memory_values) / len(memory_values) if memory_values else initial_memory,
            "memory_samples": memory_samples,
            "total_iterations": iteration_count,
        }

        results["memory_analysis"] = {
            "memory_stable": abs(final_memory - initial_memory) < 100,  # Less than 100MB growth
            "memory_within_limits": final_memory <= MAX_MEMORY_USAGE_MB,
            "gc_collections": gc_collections,
            "memory_efficiency": {
                "mb_per_request": (final_memory - initial_memory) / iteration_count if iteration_count > 0 else 0,
                "peak_vs_average_ratio": (
                    max(memory_values) / (sum(memory_values) / len(memory_values)) if memory_values else 1.0
                ),
            },
        }

        self.logger.info("Memory usage performance test completed")
        return results

    def _calculate_performance_stats(self, times: list[float]) -> dict[str, float]:
        """Calculate comprehensive performance statistics from timing data."""
        if not times:
            return {"count": 0, "avg": 0, "min": 0, "max": 0, "p95": 0, "p99": 0}

        sorted_times = sorted(times)
        return {
            "count": len(times),
            "avg": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "p95": self._calculate_percentile(sorted_times, 95),
            "p99": self._calculate_percentile(sorted_times, 99),
        }

    def _calculate_percentile(self, sorted_values: list[float], percentile: float) -> float:
        """Calculate percentile from sorted values."""
        if not sorted_values:
            return 0.0

        index = int((percentile / 100) * (len(sorted_values) - 1))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _analyze_performance_degradation(self, concurrency_results: dict[int, dict[str, Any]]) -> dict[str, Any]:
        """Analyze performance degradation patterns across concurrency levels."""
        levels = sorted(concurrency_results.keys())

        if len(levels) < 2:
            return {"analysis": "insufficient_data"}

        # Calculate performance ratios
        baseline_throughput = concurrency_results[levels[0]]["throughput_rps"]
        baseline_response_time = concurrency_results[levels[0]]["avg_processing_time"]

        degradation_analysis = {
            "throughput_scaling_efficiency": {},
            "response_time_degradation": {},
            "scalability_threshold": None,
        }

        for level in levels[1:]:
            data = concurrency_results[level]

            # Throughput scaling efficiency (ideal would be linear)
            expected_throughput = baseline_throughput * level
            actual_throughput = data["throughput_rps"]
            efficiency = (actual_throughput / expected_throughput) * 100 if expected_throughput > 0 else 0

            degradation_analysis["throughput_scaling_efficiency"][level] = efficiency

            # Response time degradation
            response_time_ratio = (
                data["avg_processing_time"] / baseline_response_time if baseline_response_time > 0 else 1
            )
            degradation_analysis["response_time_degradation"][level] = response_time_ratio

            # Identify scalability threshold (where performance degrades significantly)
            if (efficiency < 70 or response_time_ratio > 2.0) and degradation_analysis["scalability_threshold"] is None:
                degradation_analysis["scalability_threshold"] = level

        return degradation_analysis


# Pytest test functions using the baseline performance test suite


@pytest.fixture
async def performance_test_suite():
    """Create and return baseline performance test suite."""
    return BaselinePerformanceTestSuite()


@pytest.mark.asyncio
@pytest.mark.performance
async def test_query_counselor_baseline_performance(performance_test_suite):
    """Test QueryCounselor baseline performance meets Week 1 requirements."""
    results = await performance_test_suite.test_query_counselor_baseline_performance()

    # Validate critical performance metrics
    assert (
        results["metrics"]["intent_analysis"]["p95"] < BASELINE_SLA_RESPONSE_TIME
    ), f"Intent analysis P95 ({results['metrics']['intent_analysis']['p95']:.3f}s) exceeds SLA ({BASELINE_SLA_RESPONSE_TIME}s)"

    assert (
        results["metrics"]["agent_selection"]["p95"] < 0.5
    ), f"Agent selection P95 ({results['metrics']['agent_selection']['p95']:.3f}s) too slow"

    assert (
        results["metrics"]["workflow_orchestration"]["p95"] < BASELINE_SLA_RESPONSE_TIME
    ), f"Workflow orchestration P95 ({results['metrics']['workflow_orchestration']['p95']:.3f}s) exceeds SLA"

    # Log performance summary
    logger.info("QueryCounselor Performance Summary:")
    logger.info("  Intent Analysis P95: %.3fs", results["metrics"]["intent_analysis"]["p95"])
    logger.info("  Agent Selection P95: %.3fs", results["metrics"]["agent_selection"]["p95"])
    logger.info("  Workflow Orchestration P95: %.3fs", results["metrics"]["workflow_orchestration"]["p95"])


@pytest.mark.asyncio
@pytest.mark.performance
async def test_hyde_processor_baseline_performance(performance_test_suite):
    """Test HydeProcessor baseline performance meets Week 1 requirements."""
    results = await performance_test_suite.test_hyde_processor_baseline_performance()

    # Validate critical performance metrics
    assert (
        results["metrics"]["three_tier_analysis"]["p95"] < BASELINE_SLA_RESPONSE_TIME
    ), f"Three-tier analysis P95 ({results['metrics']['three_tier_analysis']['p95']:.3f}s) exceeds SLA"

    assert (
        results["metrics"]["full_pipeline"]["p95"] < BASELINE_SLA_RESPONSE_TIME
    ), f"Full pipeline P95 ({results['metrics']['full_pipeline']['p95']:.3f}s) exceeds SLA"

    # Validate specificity distribution is reasonable
    specificity = results["specificity_analysis"]
    total_queries = sum(specificity.values())
    assert total_queries == PERFORMANCE_TEST_ITERATIONS, "Specificity analysis incomplete"

    # Log performance summary
    logger.info("HydeProcessor Performance Summary:")
    logger.info("  Three-tier Analysis P95: %.3fs", results["metrics"]["three_tier_analysis"]["p95"])
    logger.info("  Document Generation P95: %.3fs", results["metrics"]["doc_generation"]["p95"])
    logger.info("  Full Pipeline P95: %.3fs", results["metrics"]["full_pipeline"]["p95"])
    logger.info("  Specificity Distribution: %s", specificity)


@pytest.mark.asyncio
@pytest.mark.performance
async def test_integrated_workflow_baseline_performance(performance_test_suite):
    """Test integrated QueryCounselor + HydeProcessor workflow performance."""
    results = await performance_test_suite.test_integrated_workflow_performance()

    # Validate end-to-end performance meets SLA
    assert (
        results["metrics"]["end_to_end_workflow"]["p95"] < BASELINE_SLA_RESPONSE_TIME
    ), f"End-to-end workflow P95 ({results['metrics']['end_to_end_workflow']['p95']:.3f}s) exceeds SLA"

    # Validate workflow success rate
    assert (
        results["workflow_analysis"]["workflow_success_rate"] >= 95.0
    ), f"Workflow success rate ({results['workflow_analysis']['workflow_success_rate']:.1f}%) below threshold"

    # Log integration performance summary
    logger.info("Integrated Workflow Performance Summary:")
    logger.info("  End-to-End P95: %.3fs", results["metrics"]["end_to_end_workflow"]["p95"])
    logger.info("  HyDE Usage Rate: %.1f%%", results["workflow_analysis"]["hyde_usage_rate"])
    logger.info("  Workflow Success Rate: %.1f%%", results["workflow_analysis"]["workflow_success_rate"])


@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_processing_performance(performance_test_suite):
    """Test concurrent processing capabilities meet scalability requirements."""
    results = await performance_test_suite.test_concurrent_processing_performance()

    # Validate minimum concurrent processing capability
    max_capacity = results["scalability_analysis"]["max_concurrent_capacity"]
    assert (
        max_capacity >= MIN_CONCURRENT_REQUESTS
    ), f"Max concurrent capacity ({max_capacity}) below minimum requirement ({MIN_CONCURRENT_REQUESTS})"

    # Validate performance at minimum concurrency level
    min_concurrency_data = results["metrics"][MIN_CONCURRENT_REQUESTS]
    assert (
        min_concurrency_data["p95_processing_time"] < BASELINE_SLA_RESPONSE_TIME
    ), f"P95 processing time at {MIN_CONCURRENT_REQUESTS} concurrent requests exceeds SLA"

    assert (
        min_concurrency_data["success_rate"] >= 95.0
    ), f"Success rate at {MIN_CONCURRENT_REQUESTS} concurrent requests below threshold"

    # Log concurrent processing summary
    logger.info("Concurrent Processing Performance Summary:")
    logger.info("  Max Concurrent Capacity: %s requests", max_capacity)
    logger.info(
        "  Throughput at %s concurrent: %.2f RPS",
        MIN_CONCURRENT_REQUESTS,
        min_concurrency_data["throughput_rps"],
    )
    logger.info(
        "  P95 Response Time at %s concurrent: %.3fs",
        MIN_CONCURRENT_REQUESTS,
        min_concurrency_data["p95_processing_time"],
    )


@pytest.mark.asyncio
@pytest.mark.performance
async def test_memory_usage_performance(performance_test_suite):
    """Test memory usage characteristics meet resource constraints."""
    results = await performance_test_suite.test_memory_usage_performance()

    # Validate memory usage within limits
    assert (
        results["metrics"]["peak_memory_mb"] <= MAX_MEMORY_USAGE_MB
    ), f"Peak memory usage ({results['metrics']['peak_memory_mb']:.1f} MB) exceeds limit ({MAX_MEMORY_USAGE_MB} MB)"

    # Validate memory stability (no significant leaks)
    assert results["memory_analysis"][
        "memory_stable"
    ], f"Memory growth ({results['metrics']['total_memory_growth_mb']:.1f} MB) indicates potential memory leak"

    # Validate memory efficiency
    efficiency = results["memory_analysis"]["memory_efficiency"]
    assert (
        efficiency["mb_per_request"] < 1.0
    ), f"Memory usage per request ({efficiency['mb_per_request']:.3f} MB) too high"

    # Log memory usage summary
    logger.info("Memory Usage Performance Summary:")
    logger.info("  Initial Memory: %.1f MB", results["metrics"]["initial_memory_mb"])
    logger.info("  Peak Memory: %.1f MB", results["metrics"]["peak_memory_mb"])
    logger.info("  Total Growth: %.1f MB", results["metrics"]["total_memory_growth_mb"])
    logger.info("  Memory Per Request: %.3f MB", efficiency["mb_per_request"])


@pytest.mark.asyncio
@pytest.mark.performance
async def test_week1_acceptance_criteria_validation(performance_test_suite):
    """
    Comprehensive validation that Week 1 deliverables meet all acceptance criteria.

    This test validates the complete Week 1 implementation against all specified
    acceptance criteria for Phase 1 Issue NEW-8.
    """
    logger.info("Starting Week 1 acceptance criteria validation")

    # Execute all baseline performance tests
    qc_results = await performance_test_suite.test_query_counselor_baseline_performance()
    hyde_results = await performance_test_suite.test_hyde_processor_baseline_performance()
    integrated_results = await performance_test_suite.test_integrated_workflow_performance()
    concurrent_results = await performance_test_suite.test_concurrent_processing_performance()
    memory_results = await performance_test_suite.test_memory_usage_performance()

    # Comprehensive acceptance criteria validation
    acceptance_criteria = {
        "performance_framework_setup": True,  # Performance monitor exists and functional
        "response_time_infrastructure": True,  # Response time measurement in place
        "baseline_establishment": True,  # Baseline performance tests implemented
        "integration_coordination": True,  # QueryCounselor + HydeProcessor integration
        "sla_compliance": True,  # <2 second response time requirement
        "concurrent_processing": True,  # Concurrent processing capability
        "memory_constraints": True,  # Memory usage within limits
        "component_integration": True,  # Components work together
    }

    # Validate each criterion
    validation_results = {}

    # 1. Performance framework setup
    try:
        monitor = performance_test_suite.performance_monitor
        assert monitor is not None, "Performance monitor not initialized"
        metrics = monitor.get_all_metrics()
        assert isinstance(metrics, dict), "Performance monitor not functional"
        validation_results["performance_framework_setup"] = {
            "status": "PASS",
            "details": "Performance monitoring framework operational",
        }
    except Exception as e:
        validation_results["performance_framework_setup"] = {"status": "FAIL", "details": str(e)}
        acceptance_criteria["performance_framework_setup"] = False

    # 2. Response time infrastructure
    try:
        # Verify response time measurement is working
        assert "timers" in monitor.get_all_metrics(), "Timer metrics not available"
        validation_results["response_time_infrastructure"] = {
            "status": "PASS",
            "details": "Response time measurement infrastructure operational",
        }
    except Exception as e:
        validation_results["response_time_infrastructure"] = {"status": "FAIL", "details": str(e)}
        acceptance_criteria["response_time_infrastructure"] = False

    # 3. Baseline establishment
    try:
        # Verify baseline tests executed successfully
        assert qc_results["metrics"]["intent_analysis"]["count"] == PERFORMANCE_TEST_ITERATIONS
        assert hyde_results["metrics"]["three_tier_analysis"]["count"] == PERFORMANCE_TEST_ITERATIONS
        validation_results["baseline_establishment"] = {
            "status": "PASS",
            "details": "Baseline performance metrics established",
        }
    except Exception as e:
        validation_results["baseline_establishment"] = {"status": "FAIL", "details": str(e)}
        acceptance_criteria["baseline_establishment"] = False

    # 4. Integration coordination
    try:
        # Verify QueryCounselor and HydeProcessor integration
        assert integrated_results["workflow_analysis"]["hyde_usage_rate"] > 0, "HyDE integration not working"
        assert (
            integrated_results["workflow_analysis"]["workflow_success_rate"] >= 95.0
        ), "Integration success rate too low"
        validation_results["integration_coordination"] = {
            "status": "PASS",
            "details": "QueryCounselor + HydeProcessor integration functional",
        }
    except Exception as e:
        validation_results["integration_coordination"] = {"status": "FAIL", "details": str(e)}
        acceptance_criteria["integration_coordination"] = False

    # 5. SLA compliance (<2 second response time)
    try:
        # Verify all critical paths meet <2s p95 requirement
        assert qc_results["metrics"]["intent_analysis"]["p95"] < BASELINE_SLA_RESPONSE_TIME
        assert hyde_results["metrics"]["three_tier_analysis"]["p95"] < BASELINE_SLA_RESPONSE_TIME
        assert integrated_results["metrics"]["end_to_end_workflow"]["p95"] < BASELINE_SLA_RESPONSE_TIME
        validation_results["sla_compliance"] = {
            "status": "PASS",
            "details": f"All components meet <{BASELINE_SLA_RESPONSE_TIME}s p95 requirement",
        }
    except Exception as e:
        validation_results["sla_compliance"] = {"status": "FAIL", "details": str(e)}
        acceptance_criteria["sla_compliance"] = False

    # 6. Concurrent processing capability
    try:
        # Verify minimum concurrent processing capability
        max_capacity = concurrent_results["scalability_analysis"]["max_concurrent_capacity"]
        assert (
            max_capacity >= MIN_CONCURRENT_REQUESTS
        ), f"Concurrent capacity {max_capacity} below minimum {MIN_CONCURRENT_REQUESTS}"
        validation_results["concurrent_processing"] = {
            "status": "PASS",
            "details": f"Concurrent processing capability: {max_capacity} requests",
        }
    except Exception as e:
        validation_results["concurrent_processing"] = {"status": "FAIL", "details": str(e)}
        acceptance_criteria["concurrent_processing"] = False

    # 7. Memory constraints
    try:
        # Verify memory usage within limits
        peak_memory = memory_results["metrics"]["peak_memory_mb"]
        assert (
            peak_memory <= MAX_MEMORY_USAGE_MB
        ), f"Peak memory {peak_memory} MB exceeds limit {MAX_MEMORY_USAGE_MB} MB"
        assert memory_results["memory_analysis"]["memory_stable"], "Memory usage not stable"
        validation_results["memory_constraints"] = {
            "status": "PASS",
            "details": f"Memory usage within limits: {peak_memory:.1f} MB peak",
        }
    except Exception as e:
        validation_results["memory_constraints"] = {"status": "FAIL", "details": str(e)}
        acceptance_criteria["memory_constraints"] = False

    # 8. Component integration
    try:
        # Verify all components work together end-to-end
        assert all(
            [
                qc_results["metrics"]["workflow_orchestration"]["count"] > 0,
                hyde_results["metrics"]["full_pipeline"]["count"] > 0,
                integrated_results["workflow_analysis"]["workflow_success_rate"] >= 95.0,
            ],
        ), "Component integration incomplete"
        validation_results["component_integration"] = {
            "status": "PASS",
            "details": "All components integrated and functional",
        }
    except Exception as e:
        validation_results["component_integration"] = {"status": "FAIL", "details": str(e)}
        acceptance_criteria["component_integration"] = False

    # Final validation
    all_criteria_met = all(acceptance_criteria.values())

    # Generate comprehensive report
    logger.info("=" * 80)
    logger.info("WEEK 1 ACCEPTANCE CRITERIA VALIDATION REPORT")
    logger.info("=" * 80)

    for criterion, status in acceptance_criteria.items():
        result = validation_results.get(criterion, {"status": "UNKNOWN", "details": "No validation data"})
        logger.info("%s: %s - %s", criterion.upper(), result["status"], result["details"])

    logger.info("=" * 80)
    logger.info("OVERALL STATUS: %s", "PASS" if all_criteria_met else "FAIL")
    logger.info("CRITERIA MET: %s/%s", sum(acceptance_criteria.values()), len(acceptance_criteria))
    logger.info("=" * 80)

    # Assert overall success
    assert (
        all_criteria_met
    ), f"Week 1 acceptance criteria not fully met. Failed criteria: {[k for k, v in acceptance_criteria.items() if not v]}"

    logger.info("Week 1 acceptance criteria validation completed successfully")


if __name__ == "__main__":
    """
    Example usage of baseline performance testing framework.

    This can be run directly for development testing or through pytest
    for automated validation.
    """

    async def main():
        """Run baseline performance tests."""
        suite = BaselinePerformanceTestSuite()

        print("PromptCraft Phase 1 NEW-8 Baseline Performance Testing")
        print("=" * 60)

        # Run all baseline tests
        qc_results = await suite.test_query_counselor_baseline_performance()
        hyde_results = await suite.test_hyde_processor_baseline_performance()
        integrated_results = await suite.test_integrated_workflow_performance()
        concurrent_results = await suite.test_concurrent_processing_performance()
        memory_results = await suite.test_memory_usage_performance()

        # Print summary
        print("\nBASELINE PERFORMANCE SUMMARY:")
        print(f"QueryCounselor Intent Analysis P95: {qc_results['metrics']['intent_analysis']['p95']:.3f}s")
        print(f"HydeProcessor Three-Tier Analysis P95: {hyde_results['metrics']['three_tier_analysis']['p95']:.3f}s")
        print(f"Integrated Workflow P95: {integrated_results['metrics']['end_to_end_workflow']['p95']:.3f}s")
        print(
            f"Max Concurrent Capacity: {concurrent_results['scalability_analysis']['max_concurrent_capacity']} requests",
        )
        print(f"Peak Memory Usage: {memory_results['metrics']['peak_memory_mb']:.1f} MB")

        print(
            f"\nSLA COMPLIANCE: {'PASS' if integrated_results['metrics']['end_to_end_workflow']['p95'] < BASELINE_SLA_RESPONSE_TIME else 'FAIL'}",
        )
        print("Baseline performance testing completed.")

    asyncio.run(main())
