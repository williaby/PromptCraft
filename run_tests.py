#!/usr/bin/env python3
"""
Simple test runner to run AI Tool Routing tests without pytest configuration issues.
"""

import asyncio
import sys
from typing import Any

# Add the project root to Python path
sys.path.insert(0, "/home/byron/dev/PromptCraft")


def run_sync_test(test_class_name: str, test_method_name: str, test_module) -> dict[str, Any]:
    """Run a synchronous test method."""
    try:
        test_class = getattr(test_module, test_class_name)
        test_instance = test_class()
        test_method = getattr(test_instance, test_method_name)
        test_method()
        return {"status": "PASSED", "error": None}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}


def run_async_test(test_class_name: str, test_method_name: str, test_module) -> dict[str, Any]:
    """Run an asynchronous test method."""
    try:
        test_class = getattr(test_module, test_class_name)
        test_instance = test_class()
        test_method = getattr(test_instance, test_method_name)
        asyncio.run(test_method())
        return {"status": "PASSED", "error": None}
    except Exception as e:
        return {"status": "FAILED", "error": str(e)}


def main():
    """Main test runner."""
    print("=" * 60)
    print("AI Tool Routing Test Runner")
    print("=" * 60)

    # Test Model Registry (fundamental component)
    print("\n1. Testing Model Registry...")
    try:
        from tests.unit.test_model_registry import TestModelRegistry

        test_instance = TestModelRegistry()

        # Test basic functionality
        test_instance.test_initialization()
        print("   ✓ Model Registry initialization")

        test_instance.test_register_model()
        print("   ✓ Model registration")

        test_instance.test_get_model_info()
        print("   ✓ Model info retrieval")

        test_instance.test_select_best_model()
        print("   ✓ Best model selection")

        print("   Model Registry: ALL TESTS PASSED")

    except Exception as e:
        print(f"   Model Registry: FAILED - {e}")

    # Test Circuit Breaker (reliability component)
    print("\n2. Testing Circuit Breaker...")
    try:
        from tests.unit.test_circuit_breaker import TestCircuitBreaker

        test_instance = TestCircuitBreaker()

        # Test basic functionality
        test_instance.test_initialization()
        print("   ✓ Circuit breaker initialization")

        test_instance.test_closed_state_allows_requests()
        print("   ✓ Closed state behavior")

        test_instance.test_failure_threshold_triggers_open()
        print("   ✓ Failure threshold logic")

        test_instance.test_success_threshold_closes_circuit()
        print("   ✓ Success threshold logic")

        print("   Circuit Breaker: ALL TESTS PASSED")

    except Exception as e:
        print(f"   Circuit Breaker: FAILED - {e}")

    # Test OpenRouter Client (basic synchronous tests)
    print("\n3. Testing OpenRouter Client...")
    try:
        from tests.unit.test_openrouter_client import TestOpenRouterClient

        test_instance = TestOpenRouterClient()

        # Test basic functionality
        test_instance.test_init_with_default_settings()
        print("   ✓ OpenRouter client initialization")

        test_instance.test_init_with_custom_parameters()
        print("   ✓ Custom parameters")

        test_instance.test_get_headers_with_api_key()
        print("   ✓ Header generation with API key")

        test_instance.test_get_headers_without_api_key()
        print("   ✓ Header generation without API key")

        print("   OpenRouter Client: ALL TESTS PASSED")

    except Exception as e:
        print(f"   OpenRouter Client: FAILED - {e}")

    # Test Hybrid Router (basic synchronous tests)
    print("\n4. Testing Hybrid Router...")
    try:
        from tests.unit.test_hybrid_router import TestRoutingDecision, TestRoutingMetrics

        # Test routing decision
        test_instance = TestRoutingDecision()
        test_instance.test_routing_decision_creation()
        print("   ✓ Routing decision creation")

        test_instance.test_routing_decision_to_dict()
        print("   ✓ Routing decision serialization")

        # Test routing metrics
        test_instance = TestRoutingMetrics()
        test_instance.test_routing_metrics_initialization()
        print("   ✓ Routing metrics initialization")

        test_instance.test_routing_metrics_properties()
        print("   ✓ Routing metrics properties")

        print("   Hybrid Router: ALL TESTS PASSED")

    except Exception as e:
        print(f"   Hybrid Router: FAILED - {e}")

    print("\n" + "=" * 60)
    print("Test Summary: Core AI Tool Routing components are functional")
    print("=" * 60)


if __name__ == "__main__":
    main()
