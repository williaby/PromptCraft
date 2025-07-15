#!/usr/bin/env python3
"""
Quick import validation for performance modules.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_import(module_name, items):
    """Test importing specific items from a module."""
    print(f"Testing {module_name}...")
    try:
        module = __import__(module_name, fromlist=items)
        for item in items:
            if hasattr(module, item):
                print(f"  ✅ {item}")
            else:
                print(f"  ❌ {item} not found")
        print(f"  ✅ {module_name} imported successfully")
        return True
    except Exception as e:
        print(f"  ❌ {module_name} import failed: {e}")
        return False


def main():
    print("=== Performance Module Import Validation ===\n")

    # Test imports
    modules_to_test = [
        (
            "src.core.performance_optimizer",
            [
                "cache_query_analysis",
                "cache_hyde_processing",
                "cache_vector_search",
                "monitor_performance",
                "get_performance_stats",
                "clear_all_caches",
                "PerformanceOptimizer",
                "LRUCache",
                "PerformanceMonitor",
            ],
        ),
        ("src.core.query_counselor", ["QueryCounselor", "QueryIntent", "QueryType"]),
        ("src.core.hyde_processor", ["HydeProcessor", "QueryAnalysis", "SpecificityLevel"]),
        ("src.core.vector_store", ["VectorStoreFactory", "VectorStoreType", "SearchParameters"]),
        (
            "src.config.performance_config",
            ["get_performance_config", "validate_performance_requirements", "OPERATION_THRESHOLDS"],
        ),
    ]

    success_count = 0
    for module_name, items in modules_to_test:
        if test_import(module_name, items):
            success_count += 1
        print()

    print(f"Import validation: {success_count}/{len(modules_to_test)} modules successful")

    if success_count == len(modules_to_test):
        print("🎉 All performance modules imported successfully!")
        return True
    print("❌ Some modules failed to import")
    return False


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)
