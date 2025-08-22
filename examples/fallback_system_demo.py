"""
Conservative Fallback System Demonstration

This example demonstrates the complete conservative fallback mechanism chain
in action, showing how it handles various failure scenarios while maintaining
user functionality and providing comprehensive observability.

Run this example to see:
- Normal operation with optimized function loading
- Graceful degradation through the five-tier fallback strategy
- Error recovery and circuit breaker protection
- User notifications and system health monitoring
- Performance metrics and learning capabilities
"""

import asyncio
import builtins
import contextlib
import logging
import time
import traceback
from typing import Any

from src.core.conservative_fallback_chain import create_conservative_fallback_chain
from src.core.fallback_integration import IntegrationMode, create_enhanced_task_detection
from src.core.task_detection import DetectionResult
from src.core.task_detection_config import DetectionMode, TaskDetectionConfig

# Configure logging for demo
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class DemoTaskDetectionSystem:
    """Demo task detection system with configurable failure modes"""

    def __init__(self) -> None:
        self.failure_mode = None
        self.call_count = 0
        self.response_delay = 0.05  # 50ms default response time

    def set_failure_mode(self, mode: str | None) -> None:
        """Set failure mode for demonstration"""
        self.failure_mode = mode

    def set_response_delay(self, delay: float) -> None:
        """Set response delay for demonstration"""
        self.response_delay = delay

    async def detect_categories(self, query: str, context: dict[str, Any] | None = None) -> DetectionResult:
        """Mock detection with configurable failures"""
        self.call_count += 1

        # Simulate processing time
        await asyncio.sleep(self.response_delay)

        # Simulate different failure modes
        if self.failure_mode == "timeout":
            await asyncio.sleep(10)  # Exceeds timeout
        elif self.failure_mode == "network":
            raise ConnectionError("Simulated network failure")
        elif self.failure_mode == "memory":
            raise MemoryError("Simulated memory pressure")
        elif self.failure_mode == "generic":
            raise Exception("Simulated generic error")

        # Return realistic detection result based on query
        query_lower = query.lower()

        if "git" in query_lower:
            return DetectionResult(
                categories={"git": True, "core": True, "debug": False},
                confidence_scores={"git": 0.9, "core": 0.8, "debug": 0.1},
                detection_time_ms=self.response_delay * 1000,
                signals_used={"keyword": ["git"]},
                fallback_applied=None,
            )
        if "test" in query_lower:
            return DetectionResult(
                categories={"test": True, "quality": True, "debug": True},
                confidence_scores={"test": 0.8, "quality": 0.7, "debug": 0.6},
                detection_time_ms=self.response_delay * 1000,
                signals_used={"keyword": ["test"]},
                fallback_applied=None,
            )
        if "debug" in query_lower or "error" in query_lower:
            return DetectionResult(
                categories={"debug": True, "analysis": True, "test": False},
                confidence_scores={"debug": 0.85, "analysis": 0.6, "test": 0.3},
                detection_time_ms=self.response_delay * 1000,
                signals_used={"keyword": ["debug", "error"]},
                fallback_applied=None,
            )
        # Ambiguous query - low confidence
        return DetectionResult(
            categories={"analysis": True, "core": False},
            confidence_scores={"analysis": 0.4, "core": 0.3},
            detection_time_ms=self.response_delay * 1000,
            signals_used={"keyword": []},
            fallback_applied=None,
        )


async def demonstrate_normal_operation() -> None:
    """Demonstrate normal operation with different confidence levels"""

    # Create demo system
    demo_system = DemoTaskDetectionSystem()
    config = TaskDetectionConfig()
    config.apply_mode_preset(DetectionMode.CONSERVATIVE)

    fallback_chain = create_conservative_fallback_chain(demo_system, config)

    # Test different types of queries
    test_queries = [
        ("git commit my changes", "High confidence - git operations"),
        ("run the test suite", "High confidence - testing operations"),
        ("debug this error message", "High confidence - debugging operations"),
        ("help me with something", "Low confidence - ambiguous request"),
        ("analyze code patterns", "Medium confidence - analysis request"),
    ]

    for query, _description in test_queries:

        with contextlib.suppress(Exception):
            categories, decision = await fallback_chain.get_function_categories(query)

            [cat for cat, loaded in categories.items() if loaded]


async def demonstrate_failure_scenarios() -> None:
    """Demonstrate failure scenarios and recovery"""

    demo_system = DemoTaskDetectionSystem()
    config = TaskDetectionConfig()
    config.apply_mode_preset(DetectionMode.CONSERVATIVE)

    fallback_chain = create_conservative_fallback_chain(demo_system, config)

    # Test different failure modes
    failure_scenarios = [
        ("timeout", "Timeout failure - detection takes too long"),
        ("network", "Network failure - connection issues"),
        ("memory", "Memory pressure - system overload"),
        ("generic", "Generic error - unexpected failure"),
    ]

    for failure_mode, _description in failure_scenarios:

        # Set failure mode
        demo_system.set_failure_mode(failure_mode)

        with contextlib.suppress(Exception):
            categories, decision = await fallback_chain.get_function_categories(
                "help me debug this issue",
            )

            [cat for cat, loaded in categories.items() if loaded]

        # Reset to normal
        demo_system.set_failure_mode(None)


async def demonstrate_circuit_breaker() -> None:
    """Demonstrate circuit breaker protection"""

    demo_system = DemoTaskDetectionSystem()
    config = TaskDetectionConfig()
    config.apply_mode_preset(DetectionMode.CONSERVATIVE)

    fallback_chain = create_conservative_fallback_chain(demo_system, config)

    # Set failure mode
    demo_system.set_failure_mode("network")

    # Generate multiple failures
    for i in range(5):
        with contextlib.suppress(Exception):
            categories, decision = await fallback_chain.get_function_categories(
                f"query that will fail {i}",
            )

    # Reset and test circuit breaker behavior
    demo_system.set_failure_mode(None)

    categories, decision = await fallback_chain.get_function_categories("test with circuit breaker open")

    # Reset circuit breaker
    fallback_chain.reset_circuit_breaker()


async def demonstrate_emergency_mode() -> None:
    """Demonstrate emergency mode activation"""

    demo_system = DemoTaskDetectionSystem()
    config = TaskDetectionConfig()
    config.apply_mode_preset(DetectionMode.CONSERVATIVE)

    fallback_chain = create_conservative_fallback_chain(demo_system, config)

    # Force emergency mode
    fallback_chain.emergency_mode = True
    fallback_chain.emergency_mode_start = time.time()

    categories, decision = await fallback_chain.get_function_categories(
        "any query in emergency mode",
    )

    [cat for cat, loaded in categories.items() if loaded]

    # Exit emergency mode
    fallback_chain.exit_emergency_mode()


async def demonstrate_integration_modes() -> None:
    """Demonstrate different integration modes"""

    demo_system = DemoTaskDetectionSystem()

    integration_modes = [
        (IntegrationMode.MONITORING, "Monitoring only - no intervention"),
        (IntegrationMode.SHADOW, "Shadow mode - parallel execution"),
        (IntegrationMode.ACTIVE, "Active mode - full protection"),
    ]

    for mode, _description in integration_modes:

        enhanced_system = create_enhanced_task_detection(
            demo_system,
            integration_mode=mode,
        )

        with contextlib.suppress(Exception):
            result = await enhanced_system.detect_categories(
                "git commit changes",
                {"user_id": "demo_user"},
            )

            if result.fallback_applied:
                pass


async def demonstrate_health_monitoring() -> None:
    """Demonstrate health monitoring and metrics"""

    demo_system = DemoTaskDetectionSystem()
    config = TaskDetectionConfig()
    config.apply_mode_preset(DetectionMode.CONSERVATIVE)

    fallback_chain = create_conservative_fallback_chain(demo_system, config)

    # Generate some activity

    for i in range(10):
        if i % 3 == 0:
            # Introduce some failures
            demo_system.set_failure_mode("timeout")
        else:
            demo_system.set_failure_mode(None)

        with contextlib.suppress(builtins.BaseException):
            await fallback_chain.get_function_categories(f"query {i}")

    # Reset to normal
    demo_system.set_failure_mode(None)

    # Get health status
    health = fallback_chain.get_health_status()

    if "performance" in health:
        health["performance"]

    if "recovery" in health:
        health["recovery"]

    if "learning" in health:
        learning = health["learning"]

        if learning["insights"]:
            for _insight in learning["insights"][:3]:  # Top 3 insights
                pass


async def demonstrate_performance_impact() -> None:
    """Demonstrate performance characteristics"""

    demo_system = DemoTaskDetectionSystem()
    config = TaskDetectionConfig()
    config.apply_mode_preset(DetectionMode.CONSERVATIVE)

    # Test without fallback protection

    start_time = time.time()
    for i in range(100):
        await demo_system.detect_categories(f"query {i}")
    original_time = time.time() - start_time

    # Test with fallback protection

    fallback_chain = create_conservative_fallback_chain(demo_system, config)

    start_time = time.time()
    for i in range(100):
        await fallback_chain.get_function_categories(f"query {i}")
    protected_time = time.time() - start_time

    ((protected_time - original_time) / original_time) * 100

    # Test under failure conditions

    demo_system.set_failure_mode("timeout")
    demo_system.set_response_delay(6.0)  # Exceeds timeout

    start_time = time.time()
    for i in range(10):
        with contextlib.suppress(builtins.BaseException):
            await fallback_chain.get_function_categories(f"failing query {i}")
    time.time() - start_time


async def main() -> None:
    """Run the complete demonstration"""

    try:
        # Run all demonstrations
        await demonstrate_normal_operation()
        await demonstrate_failure_scenarios()
        await demonstrate_circuit_breaker()
        await demonstrate_emergency_mode()
        await demonstrate_integration_modes()
        await demonstrate_health_monitoring()
        await demonstrate_performance_impact()

    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())
