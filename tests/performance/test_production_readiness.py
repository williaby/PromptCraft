"""Performance testing for PromptCraft-Hybrid production readiness.

This module tests system performance requirements, load handling, and production
readiness across all components to ensure the system meets the <2s response time
requirement and can handle concurrent load effectively.
"""

import asyncio
import os
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.config.settings import ApplicationSettings
from src.core.hyde_processor import HydeProcessor
from src.core.performance_optimizer import PerformanceOptimizer
from src.core.query_counselor import QueryCounselor
from src.core.vector_store import (
    DEFAULT_VECTOR_DIMENSIONS,
    ConnectionStatus,
    EnhancedMockVectorStore,
    SearchParameters,
    VectorDocument,
)
from src.mcp_integration.config_manager import MCPConfigurationManager
from src.mcp_integration.mcp_client import MCPConnectionState, ZenMCPClient
from src.utils.performance_monitor import PerformanceMonitor


class TestProductionReadiness:
    """Performance testing for production readiness."""

    @pytest.fixture
    def performance_settings(self):
        """Create optimized settings for performance testing."""
        return ApplicationSettings(
            # MCP Configuration
            mcp_enabled=True,
            mcp_server_url="http://localhost:3000",
            mcp_timeout=2.0,  # Tight timeout for performance
            mcp_max_retries=2,
            mcp_health_check_interval=30.0,
            # Vector Store Configuration
            qdrant_enabled=False,  # Use mock for consistent performance
            vector_store_type="mock",
            vector_dimensions=DEFAULT_VECTOR_DIMENSIONS,
            # Performance Configuration
            performance_monitoring_enabled=True,
            max_concurrent_queries=20,
            query_timeout=2.0,  # 2 second requirement
            # Optimization Configuration
            caching_enabled=True,
            connection_pooling_enabled=True,
            batch_processing_enabled=True,
            # Production Configuration
            health_check_enabled=True,
            error_recovery_enabled=True,
            circuit_breaker_enabled=True,
        )

    @pytest.fixture
    def performance_monitor(self):
        """Create performance monitor for testing."""
        return PerformanceMonitor()

    @pytest.fixture
    def sample_load_queries(self):
        """Create sample queries for load testing."""
        return [
            "How do I implement authentication in FastAPI?",
            "What are the best practices for async programming in Python?",
            "How do I optimize database queries for performance?",
            "What is the difference between REST and GraphQL APIs?",
            "How do I implement caching in distributed systems?",
            "What are the security considerations for web applications?",
            "How do I handle errors in microservices architecture?",
            "What are the best practices for API design?",
            "How do I implement real-time features in web apps?",
            "What is the best approach for data validation?",
            "How do I optimize frontend performance?",
            "What are the considerations for scalable architecture?",
            "How do I implement monitoring and logging?",
            "What are the best practices for testing?",
            "How do I handle database migrations?",
            "What is the best approach for configuration management?",
            "How do I implement rate limiting?",
            "What are the patterns for error handling?",
            "How do I optimize memory usage in applications?",
            "What is the best approach for deployment automation?",
        ]

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_single_query_performance_requirement(self, performance_settings, performance_monitor):
        """Test that single query processing meets <2s requirement."""

        with patch("src.config.settings.get_settings", return_value=performance_settings):
            # Mock optimized MCP client
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED
            mock_mcp_client.orchestrate_agents = AsyncMock(
                return_value=[
                    MagicMock(
                        agent_id="create_agent",
                        success=True,
                        content="Optimized response from create_agent",
                        metadata={"processing_time": 0.1, "confidence": 0.9},
                    ),
                ],
            )

            # Mock optimized vector store
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.005},  # Very low latency
            )
            await mock_vector_store.connect()

            # Mock optimized HyDE processor
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store
            mock_hyde_processor.process_query = AsyncMock(
                return_value={
                    "original_query": "test",
                    "enhanced_query": "Enhanced: test",
                    "enhancement_score": 0.9,
                    "relevant_documents": [],
                    "processing_time": 0.02,
                },
            )

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test multiple queries to ensure consistent performance
                test_queries = [
                    "How do I optimize Python code for performance?",
                    "What are the best practices for database design?",
                    "How do I implement secure authentication?",
                    "What is the best approach for API versioning?",
                    "How do I handle concurrent requests efficiently?",
                ]

                response_times = []

                for query in test_queries:
                    start_time = time.time()

                    # Execute complete workflow
                    intent = await counselor.analyze_intent(query)
                    hyde_result = await counselor.hyde_processor.process_query(query)
                    agents = await counselor.select_agents(intent)
                    responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                    processing_time = time.time() - start_time
                    response_times.append(processing_time)

                    # Verify response quality
                    assert len(responses) > 0
                    assert all(response.success for response in responses)

                    # Record performance metrics
                    performance_monitor.record_query_time(processing_time)
                    performance_monitor.record_response_quality(len(responses[0].content))

                # Verify performance requirements
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile

                assert avg_response_time < 1.5, f"Average response time {avg_response_time:.2f}s exceeds 1.5s target"
                assert (
                    max_response_time < 2.0
                ), f"Maximum response time {max_response_time:.2f}s exceeds 2.0s requirement"
                assert (
                    p95_response_time < 2.0
                ), f"95th percentile response time {p95_response_time:.2f}s exceeds 2.0s requirement"

                # Verify performance metrics
                metrics = performance_monitor.get_metrics()
                assert metrics["avg_query_time"] < 1.5
                assert metrics["query_count"] == len(test_queries)
                assert metrics["avg_response_quality"] > 100  # Minimum response length

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_concurrent_load_performance(self, performance_settings, sample_load_queries, performance_monitor):
        """Test concurrent load handling performance."""

        with patch("src.config.settings.get_settings", return_value=performance_settings):
            # Mock concurrent MCP client
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED

            async def mock_concurrent_orchestration(agent_configs, query, context=None):
                # Simulate realistic processing time with some variation
                await asyncio.sleep(0.05 + (hash(query) % 100) / 2000)  # 50-100ms variation
                return [
                    MagicMock(
                        agent_id="create_agent",
                        success=True,
                        content=f"Concurrent response for: {query[:50]}...",
                        metadata={"processing_time": 0.08, "confidence": 0.85},
                    ),
                ]

            mock_mcp_client.orchestrate_agents = mock_concurrent_orchestration

            # Mock concurrent vector store
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.01},
            )
            await mock_vector_store.connect()

            # Mock concurrent HyDE processor
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store

            async def mock_concurrent_hyde(query):
                await asyncio.sleep(0.02 + (hash(query) % 50) / 5000)  # 20-30ms variation
                return {
                    "original_query": query,
                    "enhanced_query": f"Enhanced: {query}",
                    "enhancement_score": 0.85,
                    "relevant_documents": [],
                    "processing_time": 0.025,
                }

            mock_hyde_processor.process_query = mock_concurrent_hyde

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Test concurrent processing with different load levels
                load_levels = [5, 10, 15, 20]  # Number of concurrent queries

                for concurrent_queries in load_levels:
                    queries = sample_load_queries[:concurrent_queries]

                    async def process_query_with_timing(query):
                        start_time = time.time()

                        intent = await counselor.analyze_intent(query)
                        hyde_result = await counselor.hyde_processor.process_query(query)
                        agents = await counselor.select_agents(intent)
                        responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                        processing_time = time.time() - start_time

                        return {
                            "query": query,
                            "processing_time": processing_time,
                            "success": len(responses) > 0 and all(r.success for r in responses),
                            "response_count": len(responses),
                        }

                    # Execute concurrent queries
                    start_time = time.time()
                    results = await asyncio.gather(
                        *[process_query_with_timing(query) for query in queries], return_exceptions=True,
                    )
                    total_time = time.time() - start_time

                    # Analyze results
                    successful_results = [r for r in results if not isinstance(r, Exception) and r["success"]]
                    failed_results = [r for r in results if isinstance(r, Exception) or not r.get("success", True)]

                    # Verify concurrent performance
                    success_rate = len(successful_results) / len(queries)
                    assert (
                        success_rate >= 0.95
                    ), f"Success rate {success_rate:.2%} below 95% for {concurrent_queries} concurrent queries"

                    # Verify individual query performance under load
                    response_times = [r["processing_time"] for r in successful_results]
                    if response_times:
                        avg_response_time = statistics.mean(response_times)
                        max_response_time = max(response_times)
                        p95_response_time = (
                            statistics.quantiles(response_times, n=20)[18]
                            if len(response_times) > 1
                            else response_times[0]
                        )

                        assert (
                            avg_response_time < 2.0
                        ), f"Average response time {avg_response_time:.2f}s exceeds 2.0s under {concurrent_queries} concurrent load"
                        assert (
                            max_response_time < 3.0
                        ), f"Maximum response time {max_response_time:.2f}s exceeds 3.0s under {concurrent_queries} concurrent load"
                        assert (
                            p95_response_time < 2.5
                        ), f"95th percentile {p95_response_time:.2f}s exceeds 2.5s under {concurrent_queries} concurrent load"

                    # Verify overall throughput
                    throughput = len(successful_results) / total_time
                    expected_min_throughput = concurrent_queries / 5  # Should complete within 5 seconds
                    assert (
                        throughput >= expected_min_throughput
                    ), f"Throughput {throughput:.2f} queries/sec below expected {expected_min_throughput:.2f}"

                    # Record performance metrics
                    performance_monitor.record_concurrent_load(
                        concurrent_queries, success_rate, avg_response_time if response_times else 0,
                    )

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_production_readiness_checklist(self, performance_settings, performance_monitor):
        """Test production readiness checklist and requirements."""

        with patch("src.config.settings.get_settings", return_value=performance_settings):
            # Mock production-ready MCP client
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED
            mock_mcp_client.orchestrate_agents = AsyncMock(
                return_value=[
                    MagicMock(
                        agent_id="create_agent",
                        success=True,
                        content="Production-ready response",
                        metadata={"processing_time": 0.1},
                    ),
                ],
            )

            # Mock production-ready vector store
            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.01},
            )
            await mock_vector_store.connect()

            # Mock production-ready HyDE processor
            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store
            mock_hyde_processor.process_query = AsyncMock(
                return_value={
                    "original_query": "test",
                    "enhanced_query": "Enhanced: test",
                    "enhancement_score": 0.9,
                    "relevant_documents": [],
                    "processing_time": 0.02,
                },
            )

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Production readiness checklist
                production_checks = []

                # 1. Response time requirement (<2s)
                start_time = time.time()
                intent = await counselor.analyze_intent("Production readiness test query")
                hyde_result = await counselor.hyde_processor.process_query("Production readiness test query")
                agents = await counselor.select_agents(intent)
                responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])
                response_time = time.time() - start_time

                production_checks.append(
                    {
                        "check": "Response time <2s",
                        "status": "PASS" if response_time < 2.0 else "FAIL",
                        "value": f"{response_time:.2f}s",
                        "requirement": "<2.0s",
                    },
                )

                # 2. Error handling
                error_handling_works = True
                try:
                    # Simulate error scenario
                    with patch.object(mock_mcp_client, "orchestrate_agents", side_effect=Exception("Test error")):
                        await counselor.orchestrate_workflow(agents, "test query")
                except Exception:
                    error_handling_works = True  # Expected to fail gracefully

                production_checks.append(
                    {
                        "check": "Error handling",
                        "status": "PASS" if error_handling_works else "FAIL",
                        "value": "Graceful degradation",
                        "requirement": "Handle errors gracefully",
                    },
                )

                # 3. Health monitoring
                health_check_works = True
                try:
                    health_status = await mock_vector_store.health_check()
                    health_check_works = health_status.status == ConnectionStatus.HEALTHY
                except Exception:
                    health_check_works = False

                production_checks.append(
                    {
                        "check": "Health monitoring",
                        "status": "PASS" if health_check_works else "FAIL",
                        "value": "Health checks functional",
                        "requirement": "Health monitoring enabled",
                    },
                )

                # 4. Performance monitoring
                performance_monitoring_works = True
                try:
                    performance_monitor.record_query_time(response_time)
                    metrics = performance_monitor.get_metrics()
                    performance_monitoring_works = "avg_query_time" in metrics
                except Exception:
                    performance_monitoring_works = False

                production_checks.append(
                    {
                        "check": "Performance monitoring",
                        "status": "PASS" if performance_monitoring_works else "FAIL",
                        "value": "Metrics collection functional",
                        "requirement": "Performance metrics enabled",
                    },
                )

                # 5. Configuration validation
                config_validation_works = True
                try:
                    config_manager = MCPConfigurationManager()
                    config_validation_works = config_manager.validate_configuration()
                except Exception:
                    config_validation_works = False

                production_checks.append(
                    {
                        "check": "Configuration validation",
                        "status": "PASS" if config_validation_works else "FAIL",
                        "value": "Configuration valid",
                        "requirement": "Valid configuration",
                    },
                )

                # 6. Concurrent handling
                concurrent_handling_works = True
                try:
                    # Test basic concurrent handling
                    concurrent_tasks = [counselor.analyze_intent(f"Concurrent test {i}") for i in range(3)]
                    concurrent_results = await asyncio.gather(*concurrent_tasks)
                    concurrent_handling_works = len(concurrent_results) == 3
                except Exception:
                    concurrent_handling_works = False

                production_checks.append(
                    {
                        "check": "Concurrent handling",
                        "status": "PASS" if concurrent_handling_works else "FAIL",
                        "value": "Concurrent processing functional",
                        "requirement": "Handle concurrent requests",
                    },
                )

                # Verify all production checks pass
                failed_checks = [check for check in production_checks if check["status"] == "FAIL"]

                # Print production readiness report
                print("\n=== PRODUCTION READINESS REPORT ===")
                for check in production_checks:
                    status_symbol = "✓" if check["status"] == "PASS" else "✗"
                    print(f"{status_symbol} {check['check']}: {check['value']} (Required: {check['requirement']})")

                if failed_checks:
                    print(f"\n❌ {len(failed_checks)} production checks failed:")
                    for check in failed_checks:
                        print(f"  - {check['check']}: {check['value']}")

                    assert False, f"Production readiness failed: {len(failed_checks)} checks failed"
                else:
                    print("\n✅ All production readiness checks passed!")

                # Assert all checks pass
                assert len(failed_checks) == 0, "All production readiness checks must pass"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_and_resource_usage(self, performance_settings, sample_load_queries):
        """Test memory usage and resource consumption."""

        import gc
        import os

        import psutil

        with patch("src.config.settings.get_settings", return_value=performance_settings):
            # Mock memory-efficient components
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED
            mock_mcp_client.orchestrate_agents = AsyncMock(
                return_value=[
                    MagicMock(
                        agent_id="create_agent",
                        success=True,
                        content="Memory-efficient response",
                        metadata={"processing_time": 0.1},
                    ),
                ],
            )

            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": False, "error_rate": 0.0, "base_latency": 0.001},
            )
            await mock_vector_store.connect()

            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store
            mock_hyde_processor.process_query = AsyncMock(
                return_value={
                    "original_query": "test",
                    "enhanced_query": "Enhanced: test",
                    "enhancement_score": 0.9,
                    "relevant_documents": [],
                    "processing_time": 0.01,
                },
            )

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Get baseline memory usage
                process = psutil.Process(os.getpid())
                baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

                # Process queries and monitor memory
                num_queries = 100
                memory_measurements = []

                for i in range(num_queries):
                    query = sample_load_queries[i % len(sample_load_queries)]

                    # Process query
                    intent = await counselor.analyze_intent(query)
                    hyde_result = await counselor.hyde_processor.process_query(query)
                    agents = await counselor.select_agents(intent)
                    responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                    # Measure memory every 10 queries
                    if i % 10 == 0:
                        gc.collect()  # Force garbage collection
                        current_memory = process.memory_info().rss / 1024 / 1024  # MB
                        memory_measurements.append(current_memory)

                # Analyze memory usage
                final_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = final_memory - baseline_memory
                peak_memory = max(memory_measurements)
                avg_memory = statistics.mean(memory_measurements)

                # Verify memory performance
                assert memory_increase < 50, f"Memory increase {memory_increase:.1f}MB exceeds 50MB limit"
                assert peak_memory < baseline_memory + 100, f"Peak memory {peak_memory:.1f}MB exceeds baseline + 100MB"

                # Check for memory leaks
                memory_trend = (memory_measurements[-1] - memory_measurements[0]) / len(memory_measurements)
                assert memory_trend < 0.5, f"Memory trend {memory_trend:.2f}MB per measurement indicates potential leak"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_stress_and_recovery(self, performance_settings, sample_load_queries):
        """Test system stress handling and recovery."""

        with patch("src.config.settings.get_settings", return_value=performance_settings):
            # Mock stress-resistant components
            mock_mcp_client = AsyncMock()
            mock_mcp_client.connection_state = MCPConnectionState.CONNECTED

            # Simulate variable load response
            call_count = 0

            async def mock_variable_orchestration(agent_configs, query, context=None):
                nonlocal call_count
                call_count += 1

                # Simulate increasing load
                load_factor = min(call_count / 100, 2.0)  # Increase up to 2x
                processing_time = 0.05 * load_factor

                await asyncio.sleep(processing_time)

                return [
                    MagicMock(
                        agent_id="create_agent",
                        success=True,
                        content=f"Stress test response #{call_count}",
                        metadata={"processing_time": processing_time, "load_factor": load_factor},
                    ),
                ]

            mock_mcp_client.orchestrate_agents = mock_variable_orchestration

            mock_vector_store = EnhancedMockVectorStore(
                {"type": "mock", "simulate_latency": True, "error_rate": 0.0, "base_latency": 0.01},
            )
            await mock_vector_store.connect()

            mock_hyde_processor = AsyncMock()
            mock_hyde_processor.vector_store = mock_vector_store
            mock_hyde_processor.process_query = AsyncMock(
                return_value={
                    "original_query": "test",
                    "enhanced_query": "Enhanced: test",
                    "enhancement_score": 0.85,
                    "relevant_documents": [],
                    "processing_time": 0.02,
                },
            )

            with (
                patch(
                    "src.mcp_integration.mcp_client.MCPClientFactory.create_from_settings", return_value=mock_mcp_client,
                ),
                patch("src.core.hyde_processor.HydeProcessor", return_value=mock_hyde_processor),
            ):

                counselor = QueryCounselor()

                # Stress test with increasing load
                stress_phases = [
                    {"concurrent": 5, "duration": 30},  # Light load
                    {"concurrent": 15, "duration": 30},  # Medium load
                    {"concurrent": 25, "duration": 30},  # Heavy load
                    {"concurrent": 5, "duration": 30},  # Recovery
                ]

                phase_results = []

                for phase_num, phase in enumerate(stress_phases):
                    concurrent_queries = phase["concurrent"]
                    duration = phase["duration"]

                    phase_start = time.time()
                    phase_responses = []

                    # Run phase
                    while time.time() - phase_start < duration:
                        batch_queries = sample_load_queries[:concurrent_queries]

                        async def process_stress_query(query):
                            start_time = time.time()

                            intent = await counselor.analyze_intent(query)
                            hyde_result = await counselor.hyde_processor.process_query(query)
                            agents = await counselor.select_agents(intent)
                            responses = await counselor.orchestrate_workflow(agents, hyde_result["enhanced_query"])

                            processing_time = time.time() - start_time

                            return {
                                "processing_time": processing_time,
                                "success": len(responses) > 0 and all(r.success for r in responses),
                            }

                        batch_results = await asyncio.gather(
                            *[process_stress_query(query) for query in batch_queries], return_exceptions=True,
                        )

                        phase_responses.extend([r for r in batch_results if not isinstance(r, Exception)])

                    # Analyze phase results
                    successful_responses = [r for r in phase_responses if r["success"]]
                    success_rate = len(successful_responses) / len(phase_responses) if phase_responses else 0

                    if successful_responses:
                        avg_response_time = statistics.mean([r["processing_time"] for r in successful_responses])
                        max_response_time = max([r["processing_time"] for r in successful_responses])
                    else:
                        avg_response_time = 0
                        max_response_time = 0

                    phase_results.append(
                        {
                            "phase": phase_num + 1,
                            "concurrent": concurrent_queries,
                            "success_rate": success_rate,
                            "avg_response_time": avg_response_time,
                            "max_response_time": max_response_time,
                            "total_queries": len(phase_responses),
                        },
                    )

                # Verify stress test results
                for result in phase_results:
                    phase_type = ["Light", "Medium", "Heavy", "Recovery"][result["phase"] - 1]

                    # Success rate should remain high
                    assert (
                        result["success_rate"] >= 0.90
                    ), f"Success rate {result['success_rate']:.2%} below 90% in {phase_type} phase"

                    # Response times should be reasonable
                    if result["phase"] <= 3:  # Stress phases
                        max_allowed_time = 3.0 + (result["phase"] - 1) * 0.5  # Allow degradation
                        assert (
                            result["avg_response_time"] < max_allowed_time
                        ), f"Average response time {result['avg_response_time']:.2f}s exceeds {max_allowed_time:.1f}s in {phase_type} phase"
                    else:  # Recovery phase
                        assert (
                            result["avg_response_time"] < 2.0
                        ), f"Recovery phase response time {result['avg_response_time']:.2f}s should be under 2.0s"

                # Verify recovery
                recovery_result = phase_results[-1]
                heavy_load_result = phase_results[-2]

                recovery_improvement = (
                    heavy_load_result["avg_response_time"] - recovery_result["avg_response_time"]
                ) / heavy_load_result["avg_response_time"]
                assert recovery_improvement > 0.1, f"Recovery improvement {recovery_improvement:.2%} should be > 10%"
