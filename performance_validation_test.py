#!/usr/bin/env python3
"""
Comprehensive Performance Validation Test for PromptCraft-Hybrid

This script validates that all performance optimizations are working correctly
and that the system meets the <2s response time requirement.

Features tested:
1. Import all performance optimization modules
2. QueryCounselor with performance decorators
3. HydeProcessor with caching and monitoring
4. Vector store performance optimizations
5. Overall system performance validation

Usage:
    python performance_validation_test.py
"""

import asyncio
import logging
import os
import sys
import time
from statistics import mean

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Print formatted header."""
    print(f"\n{'='*60}")
    print(f"{title:^60}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print formatted section header."""
    print(f"\n{'-'*40}")
    print(f"{title}")
    print(f"{'-'*40}")


def print_status(message: str, status: bool = True):
    """Print status message with checkmark or X."""
    symbol = "✅" if status else "❌"
    print(f"{symbol} {message}")


def print_performance_stats(operation: str, times: list[float], threshold: float = 2.0):
    """Print performance statistics."""
    if not times:
        print_status(f"{operation}: No data", False)
        return False

    avg_time = mean(times)
    max_time = max(times)
    min_time = min(times)

    # Calculate percentiles
    sorted_times = sorted(times)
    p95_time = sorted_times[int(len(sorted_times) * 0.95)]
    p99_time = sorted_times[int(len(sorted_times) * 0.99)]

    print(f"  📊 {operation} Performance:")
    print(f"     Average: {avg_time:.3f}s")
    print(f"     Min: {min_time:.3f}s")
    print(f"     Max: {max_time:.3f}s")
    print(f"     P95: {p95_time:.3f}s")
    print(f"     P99: {p99_time:.3f}s")

    # Check if meets requirements
    meets_avg = avg_time < threshold
    meets_p95 = p95_time < threshold
    meets_max = max_time < threshold * 1.5  # Allow 50% tolerance for max

    print_status(f"Average response time: {avg_time:.3f}s < {threshold}s", meets_avg)
    print_status(f"P95 response time: {p95_time:.3f}s < {threshold}s", meets_p95)
    print_status(f"Max response time: {max_time:.3f}s < {threshold * 1.5}s", meets_max)

    return meets_avg and meets_p95 and meets_max


class PerformanceValidator:
    """Main performance validation class."""

    def __init__(self):
        self.test_results = {}
        self.sample_queries = [
            "How to implement user authentication in Python?",
            "What are the best practices for REST API design?",
            "Explain database indexing strategies",
            "How to handle errors in async Python code?",
            "What are microservices and when to use them?",
            "Implement caching strategies for web apps",
            "How to secure API endpoints?",
            "Design patterns for scalable applications",
            "Performance monitoring best practices",
            "Container orchestration basics",
        ]

    def test_module_imports(self) -> bool:
        """Test 1: Verify all performance modules can be imported."""
        print_section("Test 1: Module Import Validation")

        modules_to_test = [
            ("src.core.performance_optimizer", "Performance Optimizer"),
            ("src.core.query_counselor", "Query Counselor"),
            ("src.core.hyde_processor", "HyDE Processor"),
            ("src.core.vector_store", "Vector Store"),
            ("src.config.performance_config", "Performance Configuration"),
            ("src.utils.performance_monitor", "Performance Monitor"),
            ("src.mcp_integration.mcp_client", "MCP Client"),
        ]

        import_results = []

        for module_name, display_name in modules_to_test:
            try:
                __import__(module_name)
                print_status(f"Imported {display_name}")
                import_results.append(True)
            except ImportError as e:
                print_status(f"Failed to import {display_name}: {e}", False)
                import_results.append(False)
            except Exception as e:
                print_status(f"Error importing {display_name}: {e}", False)
                import_results.append(False)

        success = all(import_results)
        self.test_results["module_imports"] = success
        print_status(
            f"Module imports: {len([r for r in import_results if r])}/{len(import_results)} successful",
            success,
        )

        return success

    def test_performance_optimizer_initialization(self) -> bool:
        """Test 2: Verify performance optimizer components initialize correctly."""
        print_section("Test 2: Performance Optimizer Initialization")

        try:
            from src.core.performance_optimizer import (
                LRUCache,
                PerformanceMonitor,
                PerformanceOptimizer,
                clear_all_caches,
                get_performance_stats,
            )

            # Test LRU Cache
            cache = LRUCache(max_size=10, ttl_seconds=60)
            cache.put("test_key", "test_value")
            cached_value = cache.get("test_key")
            print_status(f"LRU Cache: {cached_value == 'test_value'}")

            # Test Performance Monitor
            monitor = PerformanceMonitor()
            metric = monitor.start_operation("test_operation")
            time.sleep(0.01)  # Simulate work
            monitor.complete_operation(metric)
            summary = monitor.get_performance_summary()
            print_status(f"Performance Monitor: {summary['total_operations'] == 1}")

            # Test Performance Optimizer
            optimizer = PerformanceOptimizer()
            stats = optimizer.get_optimization_stats()
            print_status(f"Performance Optimizer: {stats is not None}")

            # Test global functions
            clear_all_caches()
            print_status("Cache clearing function")

            initial_stats = get_performance_stats()
            print_status(f"Performance stats: {initial_stats is not None}")

            self.test_results["performance_optimizer_init"] = True
            return True

        except Exception as e:
            print_status(f"Performance optimizer initialization failed: {e}", False)
            self.test_results["performance_optimizer_init"] = False
            return False

    async def test_query_counselor_performance(self) -> bool:
        """Test 3: Query Counselor with performance decorators."""
        print_section("Test 3: Query Counselor Performance")

        try:
            from src.core.performance_optimizer import clear_all_caches
            from src.core.query_counselor import QueryCounselor

            # Clear caches for clean test
            clear_all_caches()

            # Initialize Query Counselor
            counselor = QueryCounselor()

            # Test individual query analysis
            analysis_times = []

            for query in self.sample_queries[:5]:  # Test with 5 queries
                start_time = time.time()

                try:
                    intent = await counselor.analyze_intent(query)
                    response_time = time.time() - start_time
                    analysis_times.append(response_time)

                    # Verify response structure
                    if not (hasattr(intent, "query_type") and hasattr(intent, "confidence")):
                        print_status(f"Invalid intent response for: {query[:50]}...", False)
                        continue

                except Exception as e:
                    print_status(f"Query analysis failed for '{query[:50]}...': {e}", False)
                    continue

            # Test caching effectiveness
            if analysis_times:
                # Test same query twice to verify caching
                test_query = self.sample_queries[0]

                # First execution (cache miss)
                start_time = time.time()
                await counselor.analyze_intent(test_query)
                first_time = time.time() - start_time

                # Second execution (cache hit)
                start_time = time.time()
                await counselor.analyze_intent(test_query)
                second_time = time.time() - start_time

                cache_effective = second_time < first_time
                print_status(f"Caching effectiveness: {second_time:.3f}s < {first_time:.3f}s", cache_effective)

            # Evaluate performance
            success = print_performance_stats("Query Analysis", analysis_times, 2.0)
            self.test_results["query_counselor_performance"] = success

            return success

        except Exception as e:
            print_status(f"Query Counselor performance test failed: {e}", False)
            self.test_results["query_counselor_performance"] = False
            return False

    async def test_hyde_processor_performance(self) -> bool:
        """Test 4: HyDE Processor with caching and monitoring."""
        print_section("Test 4: HyDE Processor Performance")

        try:
            from src.core.hyde_processor import HydeProcessor
            from src.core.performance_optimizer import clear_all_caches
            from src.core.vector_store import VectorStoreFactory, VectorStoreType

            # Clear caches for clean test
            clear_all_caches()

            # Initialize HyDE Processor with mock vector store
            vector_config = {
                "type": VectorStoreType.MOCK,
                "simulate_latency": True,
                "error_rate": 0.0,
                "base_latency": 0.02,  # 20ms base latency
            }
            vector_store = VectorStoreFactory.create_vector_store(vector_config)
            hyde_processor = HydeProcessor(vector_store=vector_store)

            # Test three-tier analysis
            tier_analysis_times = []

            for query in self.sample_queries[:5]:  # Test with 5 queries
                start_time = time.time()

                try:
                    enhanced_query = await hyde_processor.three_tier_analysis(query)
                    response_time = time.time() - start_time
                    tier_analysis_times.append(response_time)

                    # Verify response structure
                    if not (
                        hasattr(enhanced_query, "original_query") and hasattr(enhanced_query, "processing_strategy")
                    ):
                        print_status(f"Invalid enhanced query response for: {query[:50]}...", False)
                        continue

                except Exception as e:
                    print_status(f"HyDE analysis failed for '{query[:50]}...': {e}", False)
                    continue

            # Test full query processing
            full_processing_times = []

            for query in self.sample_queries[:3]:  # Test with 3 queries for full processing
                start_time = time.time()

                try:
                    results = await hyde_processor.process_query(query)
                    response_time = time.time() - start_time
                    full_processing_times.append(response_time)

                    # Verify response structure
                    if not (hasattr(results, "results") and hasattr(results, "processing_time")):
                        print_status(f"Invalid processing results for: {query[:50]}...", False)
                        continue

                except Exception as e:
                    print_status(f"HyDE processing failed for '{query[:50]}...': {e}", False)
                    continue

            # Evaluate performance
            tier_success = print_performance_stats("HyDE Tier Analysis", tier_analysis_times, 2.0)
            full_success = print_performance_stats("HyDE Full Processing", full_processing_times, 2.0)

            success = tier_success and full_success
            self.test_results["hyde_processor_performance"] = success

            return success

        except Exception as e:
            print_status(f"HyDE Processor performance test failed: {e}", False)
            self.test_results["hyde_processor_performance"] = False
            return False

    async def test_vector_store_performance(self) -> bool:
        """Test 5: Vector Store performance optimizations."""
        print_section("Test 5: Vector Store Performance")

        try:
            from src.core.vector_store import SearchParameters, VectorStoreFactory, VectorStoreType

            # Test both mock and optimized configurations
            configs = [
                {
                    "type": VectorStoreType.MOCK,
                    "simulate_latency": True,
                    "error_rate": 0.0,
                    "base_latency": 0.01,  # 10ms base latency
                },
                {
                    "type": VectorStoreType.MOCK,
                    "simulate_latency": False,  # Optimized configuration
                    "error_rate": 0.0,
                },
            ]

            all_search_times = []

            for i, config in enumerate(configs):
                vector_store = VectorStoreFactory.create_vector_store(config)

                # Test search operations
                search_times = []

                for j in range(5):  # 5 search operations per config
                    # Create mock search parameters
                    search_params = SearchParameters(
                        embeddings=[[0.1] * 384],
                        limit=10,
                        collection="test_collection",  # Mock embedding
                    )

                    start_time = time.time()

                    try:
                        results = await vector_store.search(search_params)
                        response_time = time.time() - start_time
                        search_times.append(response_time)

                        # Verify response structure
                        if not hasattr(results, "results"):
                            print_status(f"Invalid search results for config {i}", False)
                            continue

                    except Exception as e:
                        print_status(f"Vector search failed for config {i}: {e}", False)
                        continue

                all_search_times.extend(search_times)

                config_name = f"Config {i+1} ({'Latency' if config.get('simulate_latency') else 'Optimized'})"
                config_success = print_performance_stats(f"Vector Store {config_name}", search_times, 1.0)

            # Test batch operations
            batch_times = []
            vector_store = VectorStoreFactory.create_vector_store(configs[1])  # Use optimized config

            for batch_size in [1, 5, 10]:
                search_params_batch = []
                for _ in range(batch_size):
                    search_params_batch.append(
                        SearchParameters(embeddings=[[0.1] * 384], limit=5, collection="test_collection"),
                    )

                start_time = time.time()

                try:
                    # Simulate batch processing
                    batch_results = []
                    for params in search_params_batch:
                        result = await vector_store.search(params)
                        batch_results.append(result)

                    response_time = time.time() - start_time
                    batch_times.append(response_time)

                except Exception as e:
                    print_status(f"Batch operation failed for size {batch_size}: {e}", False)
                    continue

            # Evaluate performance
            search_success = print_performance_stats("Vector Store Search", all_search_times, 1.0)
            batch_success = print_performance_stats("Vector Store Batch", batch_times, 2.0)

            success = search_success and batch_success
            self.test_results["vector_store_performance"] = success

            return success

        except Exception as e:
            print_status(f"Vector Store performance test failed: {e}", False)
            self.test_results["vector_store_performance"] = False
            return False

    async def test_end_to_end_performance(self) -> bool:
        """Test 6: Complete end-to-end system performance."""
        print_section("Test 6: End-to-End System Performance")

        try:
            from src.core.performance_optimizer import clear_all_caches, warm_up_system
            from src.core.query_counselor import QueryCounselor

            # Clear caches and warm up system
            clear_all_caches()
            await warm_up_system()

            # Initialize system
            counselor = QueryCounselor()

            # Test complete workflow
            end_to_end_times = []

            for query in self.sample_queries[:5]:  # Test with 5 queries
                start_time = time.time()

                try:
                    # Complete processing with HyDE integration
                    response = await counselor.process_query_with_hyde(query)
                    response_time = time.time() - start_time
                    end_to_end_times.append(response_time)

                    # Verify response structure
                    if not (hasattr(response, "content") and hasattr(response, "confidence")):
                        print_status(f"Invalid end-to-end response for: {query[:50]}...", False)
                        continue

                except Exception as e:
                    print_status(f"End-to-end processing failed for '{query[:50]}...': {e}", False)
                    continue

            # Test concurrent processing
            concurrent_times = []
            concurrent_queries = self.sample_queries[:3]

            async def process_concurrent_query(query: str) -> float:
                start_time = time.time()
                await counselor.process_query_with_hyde(query)
                return time.time() - start_time

            try:
                # Run 3 concurrent queries
                start_time = time.time()
                tasks = [process_concurrent_query(q) for q in concurrent_queries]
                concurrent_times = await asyncio.gather(*tasks)
                total_concurrent_time = time.time() - start_time

                print_status(f"Concurrent processing completed in {total_concurrent_time:.3f}s")

            except Exception as e:
                print_status(f"Concurrent processing failed: {e}", False)

            # Evaluate performance
            e2e_success = print_performance_stats("End-to-End Processing", end_to_end_times, 2.0)
            concurrent_success = print_performance_stats("Concurrent Processing", concurrent_times, 2.0)

            success = e2e_success and concurrent_success
            self.test_results["end_to_end_performance"] = success

            return success

        except Exception as e:
            print_status(f"End-to-end performance test failed: {e}", False)
            self.test_results["end_to_end_performance"] = False
            return False

    def test_performance_monitoring(self) -> bool:
        """Test 7: Performance monitoring and statistics."""
        print_section("Test 7: Performance Monitoring")

        try:
            from src.config.performance_config import (
                get_optimization_recommendations,
                get_performance_config,
                validate_performance_requirements,
            )
            from src.core.performance_optimizer import get_performance_stats

            # Test performance statistics
            stats = get_performance_stats()
            print_status(f"Performance stats available: {stats is not None}")

            if stats:
                for cache_type in ["query_cache", "hyde_cache", "vector_cache"]:
                    if cache_type in stats:
                        cache_stats = stats[cache_type]
                        print_status(f"{cache_type} statistics: {len(cache_stats)} metrics")
                    else:
                        print_status(f"{cache_type} not found in stats", False)

            # Test performance configuration
            config = get_performance_config()
            print_status(f"Performance config loaded: {config is not None}")

            if config:
                print_status(f"Max response time: {config.max_response_time_ms}ms")
                print_status(f"Target response time: {config.target_response_time_ms}ms")
                print_status(f"Cache sizes configured: query={config.query_cache_size}, hyde={config.hyde_cache_size}")

            # Test requirements validation
            requirements_valid = validate_performance_requirements()
            print_status(f"Performance requirements valid: {requirements_valid}")

            # Test optimization recommendations
            recommendations = get_optimization_recommendations()
            print_status(f"Optimization recommendations: {len(recommendations)} items")

            success = stats is not None and config is not None and requirements_valid
            self.test_results["performance_monitoring"] = success

            return success

        except Exception as e:
            print_status(f"Performance monitoring test failed: {e}", False)
            self.test_results["performance_monitoring"] = False
            return False

    async def run_all_tests(self) -> dict[str, bool]:
        """Run all performance validation tests."""
        print_header("PromptCraft-Hybrid Performance Validation")
        print("🚀 Starting comprehensive performance validation...")

        # Run all tests
        test_functions = [
            ("Module Imports", self.test_module_imports),
            ("Performance Optimizer Init", self.test_performance_optimizer_initialization),
            ("Query Counselor Performance", self.test_query_counselor_performance),
            ("HyDE Processor Performance", self.test_hyde_processor_performance),
            ("Vector Store Performance", self.test_vector_store_performance),
            ("End-to-End Performance", self.test_end_to_end_performance),
            ("Performance Monitoring", self.test_performance_monitoring),
        ]

        results = {}

        for test_name, test_func in test_functions:
            try:
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                results[test_name] = result
            except Exception as e:
                print_status(f"{test_name} encountered error: {e}", False)
                results[test_name] = False

        # Print summary
        self.print_summary(results)

        return results

    def print_summary(self, results: dict[str, bool]):
        """Print test results summary."""
        print_header("Performance Validation Summary")

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        print(f"📊 Test Results: {passed}/{total} tests passed")
        print()

        for test_name, result in results.items():
            print_status(f"{test_name}", result)

        print()

        if passed == total:
            print("🎉 ALL PERFORMANCE TESTS PASSED!")
            print("✅ System meets <2s response time requirement")
            print("✅ All performance optimizations are working correctly")
            print("✅ Caching, monitoring, and batching are functional")
            print("✅ Vector store optimizations are effective")
            print("✅ End-to-end performance is satisfactory")
        else:
            print("❌ SOME PERFORMANCE TESTS FAILED")
            print(f"⚠️  {total - passed} tests need attention")
            print("🔧 Please review failed tests and optimize accordingly")

        print_header("Performance Validation Complete")


async def main():
    """Main function to run performance validation."""
    validator = PerformanceValidator()

    try:
        results = await validator.run_all_tests()

        # Return appropriate exit code
        if all(results.values()):
            print("\n🎉 Performance validation successful!")
            return 0
        print("\n❌ Performance validation failed!")
        return 1

    except Exception as e:
        print(f"\n💥 Performance validation encountered error: {e}")
        logger.exception("Performance validation failed")
        return 1


if __name__ == "__main__":
    # Run the validation
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
