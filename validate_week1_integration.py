#!/usr/bin/env python3
"""
Week 1 Day 5 Integration Validation Script for PromptCraft Phase 1 Issue NEW-8.

This script validates that all Week 1 deliverables are properly integrated and
meet the acceptance criteria for the <2 second response time requirement.

Key Validations:
- Performance framework setup
- QueryCounselor + HydeProcessor integration
- Response time measurement infrastructure
- Baseline performance establishment
- SLA compliance validation

Usage:
    python validate_week1_integration.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.core.hyde_processor import HydeProcessor
    from src.core.query_counselor import QueryCounselor
    from src.utils.performance_monitor import PerformanceMonitor, SLAMonitor, track_performance

    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


async def validate_basic_functionality():
    """Validate basic functionality of integrated components."""
    print("\n" + "=" * 60)
    print("WEEK 1 DAY 5 INTEGRATION VALIDATION")
    print("=" * 60)

    # Test 1: Performance Monitor Setup
    print("\n1. Testing Performance Framework Setup...")
    try:
        monitor = PerformanceMonitor()
        sla_monitor = SLAMonitor()
        assert monitor is not None
        assert sla_monitor is not None
        print("   ✓ Performance monitoring framework initialized")
    except Exception as e:
        print(f"   ✗ Performance framework error: {e}")
        return False

    # Test 2: Component Initialization
    print("\n2. Testing Component Initialization...")
    try:
        query_counselor = QueryCounselor()
        hyde_processor = HydeProcessor()
        assert query_counselor.hyde_processor is not None
        print("   ✓ QueryCounselor initialized with HydeProcessor")
        print("   ✓ Components properly integrated")
    except Exception as e:
        print(f"   ✗ Component initialization error: {e}")
        return False

    # Test 3: Basic Query Processing
    print("\n3. Testing Basic Query Processing...")
    try:
        test_query = "Create a simple prompt for code generation"

        start_time = time.time()
        intent = await query_counselor.analyze_intent(test_query)
        processing_time = time.time() - start_time

        assert intent is not None
        assert processing_time < 2.0  # Must meet <2s requirement
        print(f"   ✓ Intent analysis completed in {processing_time:.3f}s")
        print(f"   ✓ Query type: {intent.query_type}")
        print(f"   ✓ Confidence: {intent.confidence:.2f}")
    except Exception as e:
        print(f"   ✗ Query processing error: {e}")
        return False

    # Test 4: HyDE Integration
    print("\n4. Testing HyDE Integration...")
    try:
        test_complex_query = (
            "Create a comprehensive multi-step prompt for analyzing large codebases with performance optimization"
        )

        start_time = time.time()
        enhanced_query = await hyde_processor.three_tier_analysis(test_complex_query)
        processing_time = time.time() - start_time

        assert enhanced_query is not None
        assert processing_time < 2.0  # Must meet <2s requirement
        print(f"   ✓ HyDE analysis completed in {processing_time:.3f}s")
        print(f"   ✓ Processing strategy: {enhanced_query.processing_strategy}")
        print(f"   ✓ Specificity level: {enhanced_query.specificity_analysis.specificity_level}")
    except Exception as e:
        print(f"   ✗ HyDE integration error: {e}")
        return False

    # Test 5: End-to-End Integration
    print("\n5. Testing End-to-End Integration...")
    try:
        test_query = "Generate a template for CI/CD pipeline with security scanning"

        start_time = time.time()
        final_response = await query_counselor.process_query_with_hyde(test_query)
        processing_time = time.time() - start_time

        assert final_response is not None
        assert processing_time < 2.0  # Must meet <2s requirement
        assert final_response.confidence > 0.0
        print(f"   ✓ End-to-end processing completed in {processing_time:.3f}s")
        print(f"   ✓ Response confidence: {final_response.confidence:.2f}")

        # Check HyDE metadata
        hyde_meta = final_response.metadata.get("hyde_integration", {})
        print(f"   ✓ HyDE integration metadata: {hyde_meta.get('processing_strategy', 'unknown')}")

    except Exception as e:
        print(f"   ✗ End-to-end integration error: {e}")
        return False

    # Test 6: Performance Tracking
    print("\n6. Testing Performance Tracking...")
    try:
        with track_performance("integration_test") as tracker:
            # Simulate some processing
            await asyncio.sleep(0.1)

        metrics = monitor.get_all_metrics()
        assert "timers" in metrics
        assert "integration_test_duration" in metrics["timers"]
        print("   ✓ Performance tracking functional")
        print(f"   ✓ Tracked metrics: {len(metrics['timers'])} timers")
    except Exception as e:
        print(f"   ✗ Performance tracking error: {e}")
        return False

    # Test 7: SLA Compliance Check
    print("\n7. Testing SLA Compliance...")
    try:
        all_metrics = monitor.get_all_metrics()
        compliance = sla_monitor.check_sla_compliance(all_metrics)

        assert isinstance(compliance, dict)
        print("   ✓ SLA compliance checking functional")
        print(f"   ✓ Compliance checks performed: {len(compliance)}")
    except Exception as e:
        print(f"   ✗ SLA compliance error: {e}")
        return False

    # Test 8: Processing Recommendations
    print("\n8. Testing Processing Recommendations...")
    try:
        test_query = "Analyze code performance issues"
        recommendations = await query_counselor.get_processing_recommendation(test_query)

        assert "query_analysis" in recommendations
        assert "processing_strategy" in recommendations
        print("   ✓ Processing recommendations functional")
        print(f"   ✓ Recommended strategy: {recommendations['processing_strategy']}")
    except Exception as e:
        print(f"   ✗ Processing recommendations error: {e}")
        return False

    return True


async def run_performance_validation():
    """Run quick performance validation tests."""
    print("\n" + "=" * 60)
    print("PERFORMANCE VALIDATION")
    print("=" * 60)

    query_counselor = QueryCounselor()
    test_queries = [
        "Create a basic prompt",
        "Generate template for deployment",
        "Analyze code quality issues",
        "Create comprehensive documentation system",
        "Design multi-agent orchestration workflow",
    ]

    total_times = []
    sla_violations = 0

    print(f"\nTesting {len(test_queries)} queries for <2s SLA compliance...")

    for i, query in enumerate(test_queries, 1):
        start_time = time.time()
        try:
            response = await query_counselor.process_query_with_hyde(query)
            processing_time = time.time() - start_time
            total_times.append(processing_time)

            status = "✓" if processing_time < 2.0 else "✗"
            if processing_time >= 2.0:
                sla_violations += 1

            print(f"   {status} Query {i}: {processing_time:.3f}s")

        except Exception as e:
            processing_time = time.time() - start_time
            total_times.append(processing_time)
            sla_violations += 1
            print(f"   ✗ Query {i}: {processing_time:.3f}s (Error: {str(e)[:50]})")

    # Calculate statistics
    if total_times:
        avg_time = sum(total_times) / len(total_times)
        max_time = max(total_times)
        min_time = min(total_times)

        # Calculate p95
        sorted_times = sorted(total_times)
        p95_index = int(0.95 * len(sorted_times))
        p95_time = sorted_times[min(p95_index, len(sorted_times) - 1)]

        print("\nPerformance Summary:")
        print(f"   Average: {avg_time:.3f}s")
        print(f"   Min: {min_time:.3f}s")
        print(f"   Max: {max_time:.3f}s")
        print(f"   P95: {p95_time:.3f}s")
        print(f"   SLA Violations: {sla_violations}/{len(test_queries)}")

        # SLA compliance check
        sla_compliant = p95_time < 2.0 and sla_violations == 0
        status = "✓ PASS" if sla_compliant else "✗ FAIL"
        print(f"\nSLA Compliance (<2s p95): {status}")

        return sla_compliant

    return False


async def main():
    """Main validation function."""
    print("PromptCraft Phase 1 Issue NEW-8: Week 1 Day 5 Validation")
    print("Validating integration between QueryCounselor and HydeProcessor")

    # Run basic functionality validation
    basic_validation = await validate_basic_functionality()

    # Run performance validation
    performance_validation = await run_performance_validation()

    # Final summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    basic_status = "✓ PASS" if basic_validation else "✗ FAIL"
    perf_status = "✓ PASS" if performance_validation else "✗ FAIL"

    print(f"Basic Functionality: {basic_status}")
    print(f"Performance SLA (<2s): {perf_status}")

    overall_success = basic_validation and performance_validation
    overall_status = "✓ PASS" if overall_success else "✗ FAIL"

    print(f"\nOVERALL WEEK 1 VALIDATION: {overall_status}")

    if overall_success:
        print("\n🎉 Week 1 Day 5 deliverables successfully integrated!")
        print("   - Performance framework operational")
        print("   - QueryCounselor + HydeProcessor integration complete")
        print("   - <2 second response time SLA compliance validated")
        print("   - Baseline performance infrastructure established")
        print("\n✅ Ready for Week 2 real integrations!")
    else:
        print("\n❌ Week 1 integration validation failed.")
        print("   Please review the error messages above and fix issues.")
        print("   Re-run validation after fixes.")

    return overall_success


if __name__ == "__main__":
    """Run the validation script."""
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nValidation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nValidation failed with unexpected error: {e}")
        sys.exit(1)
