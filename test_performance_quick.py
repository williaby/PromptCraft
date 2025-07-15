#!/usr/bin/env python3
"""
Quick Performance Test for PromptCraft-Hybrid Performance Optimizations

This script performs a quick validation that our performance optimizations
are working correctly and can handle typical queries within 2 seconds.
"""

import asyncio
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def print_status(message: str, success: bool = True):
    """Print status with appropriate symbol."""
    symbol = "✅" if success else "❌"
    print(f"{symbol} {message}")


def print_header(title: str):
    """Print formatted header."""
    print(f"\n{'='*50}")
    print(f"{title:^50}")
    print(f"{'='*50}")


async def test_performance_optimizations():
    """Test performance optimizations are working."""
    print_header("Performance Optimization Test")

    success_count = 0
    total_tests = 0

    # Test 1: Import Performance Modules
    print("\n1. Testing module imports...")
    total_tests += 1

    try:
        from src.core.performance_optimizer import (
            clear_all_caches,
            get_performance_stats,
        )

        print_status("Performance optimizer modules imported successfully")
        success_count += 1
    except Exception as e:
        print_status(f"Failed to import performance modules: {e}", False)

    # Test 2: Test LRU Cache
    print("\n2. Testing LRU Cache...")
    total_tests += 1

    try:
        from src.core.performance_optimizer import LRUCache

        cache = LRUCache(max_size=5, ttl_seconds=60)

        # Test basic operations
        cache.put("key1", "value1")
        cache.put("key2", "value2")

        # Test retrieval
        value1 = cache.get("key1")
        value2 = cache.get("key2")

        # Test cache miss
        value3 = cache.get("nonexistent")

        # Test stats
        stats = cache.get_stats()

        cache_working = (
            value1 == "value1" and value2 == "value2" and value3 is None and stats["hits"] == 2 and stats["misses"] == 1
        )

        print_status(
            f"LRU Cache: hits={stats['hits']}, misses={stats['misses']}, hit_rate={stats['hit_rate']:.2f}",
            cache_working,
        )
        if cache_working:
            success_count += 1
    except Exception as e:
        print_status(f"LRU Cache test failed: {e}", False)

    # Test 3: Test Performance Monitor
    print("\n3. Testing Performance Monitor...")
    total_tests += 1

    try:
        from src.core.performance_optimizer import PerformanceMonitor

        monitor = PerformanceMonitor()

        # Test operation tracking
        metric = monitor.start_operation("test_operation")
        time.sleep(0.01)  # 10ms simulation
        monitor.complete_operation(metric)

        # Get summary
        summary = monitor.get_performance_summary()

        monitor_working = summary["total_operations"] == 1 and summary["avg_duration_ms"] > 0

        print_status(
            f"Performance Monitor: ops={summary['total_operations']}, avg={summary['avg_duration_ms']:.1f}ms",
            monitor_working,
        )
        if monitor_working:
            success_count += 1
    except Exception as e:
        print_status(f"Performance Monitor test failed: {e}", False)

    # Test 4: Test Query Counselor Performance
    print("\n4. Testing Query Counselor Performance...")
    total_tests += 1

    try:
        from src.core.query_counselor import QueryCounselor

        counselor = QueryCounselor()

        # Test with a simple query
        test_query = "How to implement authentication in Python?"

        start_time = time.time()
        intent = await counselor.analyze_intent(test_query)
        response_time = time.time() - start_time

        counselor_working = (
            response_time < 2.0
            and hasattr(intent, "query_type")
            and hasattr(intent, "confidence")
            and intent.confidence > 0.5
        )

        print_status(f"Query Counselor: {response_time:.3f}s, confidence={intent.confidence:.2f}", counselor_working)
        if counselor_working:
            success_count += 1
    except Exception as e:
        print_status(f"Query Counselor test failed: {e}", False)

    # Test 5: Test HyDE Processor Performance
    print("\n5. Testing HyDE Processor Performance...")
    total_tests += 1

    try:
        from src.core.hyde_processor import HydeProcessor
        from src.core.vector_store import VectorStoreFactory, VectorStoreType

        # Create mock vector store
        vector_config = {"type": VectorStoreType.MOCK, "simulate_latency": False, "error_rate": 0.0}
        vector_store = VectorStoreFactory.create_vector_store(vector_config)
        hyde_processor = HydeProcessor(vector_store=vector_store)

        # Test three-tier analysis
        test_query = "What are the best practices for API design?"

        start_time = time.time()
        enhanced_query = await hyde_processor.three_tier_analysis(test_query)
        response_time = time.time() - start_time

        hyde_working = (
            response_time < 2.0
            and hasattr(enhanced_query, "original_query")
            and hasattr(enhanced_query, "processing_strategy")
            and enhanced_query.original_query == test_query
        )

        print_status(
            f"HyDE Processor: {response_time:.3f}s, strategy={enhanced_query.processing_strategy}", hyde_working,
        )
        if hyde_working:
            success_count += 1
    except Exception as e:
        print_status(f"HyDE Processor test failed: {e}", False)

    # Test 6: Test Vector Store Performance
    print("\n6. Testing Vector Store Performance...")
    total_tests += 1

    try:
        from src.core.vector_store import SearchParameters, VectorStoreFactory, VectorStoreType

        # Create optimized mock vector store
        vector_config = {"type": VectorStoreType.MOCK, "simulate_latency": False, "error_rate": 0.0}
        vector_store = VectorStoreFactory.create_vector_store(vector_config)

        # Test search operation
        search_params = SearchParameters(
            embeddings=[[0.1] * 384], limit=10, collection="test_collection",  # Mock embedding
        )

        start_time = time.time()
        results = await vector_store.search(search_params)
        response_time = time.time() - start_time

        vector_working = response_time < 1.0 and hasattr(results, "results")

        print_status(
            f"Vector Store: {response_time:.3f}s, results={len(results.results) if hasattr(results, 'results') else 0}",
            vector_working,
        )
        if vector_working:
            success_count += 1
    except Exception as e:
        print_status(f"Vector Store test failed: {e}", False)

    # Test 7: Test End-to-End Performance
    print("\n7. Testing End-to-End Performance...")
    total_tests += 1

    try:
        from src.core.performance_optimizer import clear_all_caches
        from src.core.query_counselor import QueryCounselor

        # Clear caches for clean test
        clear_all_caches()

        counselor = QueryCounselor()

        # Test complete processing
        test_query = "How to implement caching in web applications?"

        start_time = time.time()
        response = await counselor.process_query_with_hyde(test_query)
        response_time = time.time() - start_time

        e2e_working = (
            response_time < 2.0
            and hasattr(response, "content")
            and hasattr(response, "confidence")
            and len(response.content) > 0
        )

        print_status(f"End-to-End: {response_time:.3f}s, confidence={response.confidence:.2f}", e2e_working)
        if e2e_working:
            success_count += 1
    except Exception as e:
        print_status(f"End-to-End test failed: {e}", False)

    # Test 8: Test Performance Statistics
    print("\n8. Testing Performance Statistics...")
    total_tests += 1

    try:
        from src.core.performance_optimizer import get_performance_stats

        stats = get_performance_stats()

        stats_working = (
            stats is not None
            and "query_cache" in stats
            and "hyde_cache" in stats
            and "vector_cache" in stats
            and "performance_monitor" in stats
        )

        print_status(f"Performance Stats: {len(stats)} categories available", stats_working)
        if stats_working:
            success_count += 1
    except Exception as e:
        print_status(f"Performance Stats test failed: {e}", False)

    # Print Final Results
    print_header("Performance Test Results")

    print(f"\n📊 Tests Passed: {success_count}/{total_tests}")

    if success_count == total_tests:
        print("🎉 ALL PERFORMANCE OPTIMIZATIONS WORKING!")
        print("✅ System meets <2s response time requirement")
        print("✅ Caching optimizations are functional")
        print("✅ Performance monitoring is active")
        print("✅ Vector store optimizations are effective")
        print("✅ End-to-end performance is satisfactory")
        return True
    print("❌ SOME PERFORMANCE OPTIMIZATIONS FAILED")
    print(f"⚠️  {total_tests - success_count} tests need attention")
    return False


if __name__ == "__main__":
    try:
        result = asyncio.run(test_performance_optimizations())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)
