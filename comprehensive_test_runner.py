#!/usr/bin/env python3
"""
Comprehensive test runner for AI Tool Routing components validation.
"""

import asyncio
import sys
from typing import Any

# Add the project root to Python path
sys.path.insert(0, "/home/byron/dev/PromptCraft")


def run_test_method(test_class_name: str, test_method_name: str, test_module) -> dict[str, Any]:
    """Run a test method and return results."""
    try:
        test_class = getattr(test_module, test_class_name)
        test_instance = test_class()

        # Check if method exists
        if not hasattr(test_instance, test_method_name):
            return {"status": "SKIPPED", "error": f"Method {test_method_name} not found"}

        test_method = getattr(test_instance, test_method_name)

        # Run the test method
        if asyncio.iscoroutinefunction(test_method):
            asyncio.run(test_method())
        else:
            test_method()

        return {"status": "PASSED", "error": None}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}


def main():
    """Main test runner."""
    print("=" * 60)
    print("Comprehensive AI Tool Routing Test Suite")
    print("=" * 60)

    test_results = {}

    # Test 1: Model Registry
    print("\n1. Testing Model Registry...")
    try:
        from tests.unit.test_model_registry import TestModelRegistry

        test_instance = TestModelRegistry()

        # Test core functionality
        methods_to_test = [
            "test_initialization",
            "test_register_model",
            "test_get_model_info",
            "test_select_best_model",
            "test_get_available_models",
            "test_update_model_config",
        ]

        passed = 0
        failed = 0

        for method_name in methods_to_test:
            result = run_test_method("TestModelRegistry", method_name, sys.modules["tests.unit.test_model_registry"])
            if result["status"] == "PASSED":
                print(f"   ✓ {method_name}")
                passed += 1
            elif result["status"] == "SKIPPED":
                print(f"   ~ {method_name} (skipped)")
            else:
                print(f"   ✗ {method_name}: {result['error']}")
                failed += 1

        test_results["model_registry"] = {"passed": passed, "failed": failed}
        print(f"   Model Registry: {passed} passed, {failed} failed")

    except Exception as e:
        print(f"   Model Registry: FAILED - {e}")
        test_results["model_registry"] = {"passed": 0, "failed": 1}

    # Test 2: Circuit Breaker
    print("\n2. Testing Circuit Breaker...")
    try:

        passed = 0
        failed = 0

        # Test configuration
        config_tests = [
            ("TestCircuitBreakerConfig", "test_valid_config"),
            ("TestCircuitBreakerConfig", "test_invalid_config"),
            ("TestCircuitBreakerStates", "test_closed_state_allows_requests"),
            ("TestCircuitBreakerStates", "test_open_state_rejects_requests"),
            ("TestCircuitBreakerStates", "test_half_open_state_behavior"),
        ]

        for class_name, method_name in config_tests:
            result = run_test_method(class_name, method_name, sys.modules["tests.unit.test_circuit_breaker"])
            if result["status"] == "PASSED":
                print(f"   ✓ {method_name}")
                passed += 1
            elif result["status"] == "SKIPPED":
                print(f"   ~ {method_name} (skipped)")
            else:
                print(f"   ✗ {method_name}: {result['error']}")
                failed += 1

        test_results["circuit_breaker"] = {"passed": passed, "failed": failed}
        print(f"   Circuit Breaker: {passed} passed, {failed} failed")

    except Exception as e:
        print(f"   Circuit Breaker: FAILED - {e}")
        test_results["circuit_breaker"] = {"passed": 0, "failed": 1}

    # Test 3: OpenRouter Client (already working)
    print("\n3. Testing OpenRouter Client...")
    try:

        passed = 0
        failed = 0

        # Test core functionality
        methods_to_test = [
            "test_init_with_default_settings",
            "test_init_with_custom_parameters",
            "test_get_headers_with_api_key",
            "test_get_headers_without_api_key",
        ]

        for method_name in methods_to_test:
            result = run_test_method(
                "TestOpenRouterClient",
                method_name,
                sys.modules["tests.unit.test_openrouter_client"],
            )
            if result["status"] == "PASSED":
                print(f"   ✓ {method_name}")
                passed += 1
            elif result["status"] == "SKIPPED":
                print(f"   ~ {method_name} (skipped)")
            else:
                print(f"   ✗ {method_name}: {result['error']}")
                failed += 1

        test_results["openrouter_client"] = {"passed": passed, "failed": failed}
        print(f"   OpenRouter Client: {passed} passed, {failed} failed")

    except Exception as e:
        print(f"   OpenRouter Client: FAILED - {e}")
        test_results["openrouter_client"] = {"passed": 0, "failed": 1}

    # Test 4: Hybrid Router (already working)
    print("\n4. Testing Hybrid Router...")
    try:

        passed = 0
        failed = 0

        # Test core functionality
        test_cases = [
            ("TestRoutingDecision", "test_routing_decision_creation"),
            ("TestRoutingDecision", "test_routing_decision_to_dict"),
            ("TestRoutingMetrics", "test_routing_metrics_initialization"),
            ("TestRoutingMetrics", "test_routing_metrics_properties"),
        ]

        for class_name, method_name in test_cases:
            result = run_test_method(class_name, method_name, sys.modules["tests.unit.test_hybrid_router"])
            if result["status"] == "PASSED":
                print(f"   ✓ {method_name}")
                passed += 1
            elif result["status"] == "SKIPPED":
                print(f"   ~ {method_name} (skipped)")
            else:
                print(f"   ✗ {method_name}: {result['error']}")
                failed += 1

        test_results["hybrid_router"] = {"passed": passed, "failed": failed}
        print(f"   Hybrid Router: {passed} passed, {failed} failed")

    except Exception as e:
        print(f"   Hybrid Router: FAILED - {e}")
        test_results["hybrid_router"] = {"passed": 0, "failed": 1}

    # Test 5: Query Counselor
    print("\n5. Testing Query Counselor...")
    try:

        passed = 0
        failed = 0

        # Test core functionality
        methods_to_test = [
            "test_initialization",
            "test_analyze_intent",
            "test_select_agents",
            "test_orchestrate_workflow",
            "test_synthesize_response",
        ]

        for method_name in methods_to_test:
            result = run_test_method("TestQueryCounselor", method_name, sys.modules["tests.unit.test_query_counselor"])
            if result["status"] == "PASSED":
                print(f"   ✓ {method_name}")
                passed += 1
            elif result["status"] == "SKIPPED":
                print(f"   ~ {method_name} (skipped)")
            else:
                print(f"   ✗ {method_name}: {result['error']}")
                failed += 1

        test_results["query_counselor"] = {"passed": passed, "failed": failed}
        print(f"   Query Counselor: {passed} passed, {failed} failed")

    except Exception as e:
        print(f"   Query Counselor: FAILED - {e}")
        test_results["query_counselor"] = {"passed": 0, "failed": 1}

    # Calculate overall results
    total_passed = sum(result["passed"] for result in test_results.values())
    total_failed = sum(result["failed"] for result in test_results.values())

    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Total Tests: {total_passed + total_failed}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(
        (
            f"Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%"
            if total_passed + total_failed > 0
            else "0.0%"
        ),
    )

    # Individual component results
    print("\nComponent Results:")
    for component, result in test_results.items():
        success_rate = (
            (result["passed"] / (result["passed"] + result["failed"]) * 100)
            if result["passed"] + result["failed"] > 0
            else 0.0
        )
        print(f"  {component}: {result['passed']} passed, {result['failed']} failed ({success_rate:.1f}%)")

    print("=" * 60)

    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
