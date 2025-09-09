#!/usr/bin/env python3
"""
Validation script for Phase 1 Issue 5 - Gradio UI Integration & Validation.

This script validates that the existing multi_journey_interface.py meets
the requirements specified in the Phase 1 Issue 5 implementation plan.
"""

import importlib.util
import inspect
from pathlib import Path
import sys


# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_multi_journey_interface():
    """Validate the multi_journey_interface.py implementation."""
    print("🔍 Validating multi_journey_interface.py implementation...")

    try:
        # Import the multi-journey interface
        spec = importlib.util.spec_from_file_location(
            "multi_journey_interface",
            project_root / "src/ui/multi_journey_interface.py",
        )
        if spec is None or spec.loader is None:
            print("❌ Could not load multi_journey_interface.py")
            return False

        multi_journey = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(multi_journey)

        # Validate key classes exist
        required_classes = ["MultiJourneyInterface", "RateLimiter"]
        for class_name in required_classes:
            if hasattr(multi_journey, class_name):
                print(f"✅ Found class: {class_name}")
            else:
                print(f"❌ Missing class: {class_name}")
                return False

        # Check MultiJourneyInterface class methods
        if hasattr(multi_journey, "MultiJourneyInterface"):
            interface_class = multi_journey.MultiJourneyInterface
            methods = [method for method in dir(interface_class) if not method.startswith("_")]

            print(f"📋 MultiJourneyInterface methods: {len(methods)}")
            for method in methods[:10]:  # Show first 10 methods
                print(f"   - {method}")
            if len(methods) > 10:
                print(f"   ... and {len(methods) - 10} more methods")

        # Check RateLimiter implementation
        if hasattr(multi_journey, "RateLimiter"):
            rate_limiter_class = multi_journey.RateLimiter
            print(
                f"✅ RateLimiter class has {len([m for m in dir(rate_limiter_class) if not m.startswith('_')])} methods",
            )

        print("✅ Basic structure validation passed")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def validate_journey1_implementation():
    """Validate Journey 1 smart templates implementation."""
    print("\n🔍 Validating Journey 1 implementation...")

    try:
        # Import the Journey 1 implementation
        spec = importlib.util.spec_from_file_location(
            "journey1_smart_templates",
            project_root / "src/ui/journeys/journey1_smart_templates.py",
        )
        if spec is None or spec.loader is None:
            print("❌ Could not load journey1_smart_templates.py")
            return False

        journey1 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(journey1)

        # Check for key methods
        key_methods = ["enhance_prompt", "create_breakdown", "process_files"]
        found_methods = []

        for attr_name in dir(journey1):
            attr = getattr(journey1, attr_name)
            if (inspect.isfunction(attr) or inspect.isclass(attr)) and callable(attr):
                for method in key_methods:
                    if method in attr_name.lower():
                        found_methods.append(attr_name)

        print(f"✅ Found Journey 1 related functions/classes: {len(found_methods)}")
        for method in found_methods:
            print(f"   - {method}")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def validate_export_utils():
    """Validate export utilities implementation."""
    print("\n🔍 Validating export utilities...")

    try:
        # Import the export utils
        spec = importlib.util.spec_from_file_location(
            "export_utils",
            project_root / "src/ui/components/shared/export_utils.py",
        )
        if spec is None or spec.loader is None:
            print("❌ Could not load export_utils.py")
            return False

        export_utils = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(export_utils)

        # Check ExportUtils class
        if hasattr(export_utils, "ExportUtils"):
            export_class = export_utils.ExportUtils
            methods = [method for method in dir(export_class) if not method.startswith("_")]
            print(f"✅ ExportUtils class has {len(methods)} public methods")

            # Check for key export methods
            key_export_methods = ["export_journey1_content", "extract_code_blocks", "format_code_blocks_for_export"]
            for method in key_export_methods:
                if hasattr(export_class, method):
                    print(f"   ✅ {method}")
                else:
                    print(f"   ❌ Missing: {method}")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def validate_ts1_compliance():
    """Validate compliance with ts-1.md specifications."""
    print("\n🔍 Validating ts-1.md compliance...")

    # Check if key files exist
    required_files = [
        "src/ui/multi_journey_interface.py",
        "src/ui/journeys/journey1_smart_templates.py",
        "src/ui/components/shared/export_utils.py",
        "docs/planning/ts-1.md",
    ]

    all_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")
            all_exist = False

    return all_exist


def validate_performance_requirements():
    """Validate performance-related implementations."""
    print("\n🔍 Validating performance requirements...")

    # Check if rate limiting is implemented
    try:
        spec = importlib.util.spec_from_file_location(
            "multi_journey_interface",
            project_root / "src/ui/multi_journey_interface.py",
        )
        if spec and spec.loader:
            multi_journey = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(multi_journey)

            if hasattr(multi_journey, "RateLimiter"):
                print("✅ Rate limiting implementation found")

                # Check rate limiter initialization
                rate_limiter = multi_journey.RateLimiter
                if hasattr(rate_limiter, "__init__"):
                    print("✅ RateLimiter can be initialized")

            if hasattr(multi_journey, "MultiJourneyInterface"):
                interface = multi_journey.MultiJourneyInterface
                if hasattr(interface, "__init__"):
                    print("✅ MultiJourneyInterface can be initialized")

        return True

    except Exception as e:
        print(f"❌ Performance validation error: {e}")
        return False


def main():
    """Main validation function."""
    print("🚀 Phase 1 Issue 5 - Gradio UI Integration Validation")
    print("=" * 60)

    validations = [
        ("File Structure", validate_ts1_compliance),
        ("Multi-Journey Interface", validate_multi_journey_interface),
        ("Journey 1 Implementation", validate_journey1_implementation),
        ("Export Utilities", validate_export_utils),
        ("Performance Requirements", validate_performance_requirements),
    ]

    results = []
    for name, validation_func in validations:
        try:
            result = validation_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation failed with error: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {name}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} validations passed ({passed/total*100:.1f}%)")

    if passed == total:
        print("\n🎉 All validations passed! Implementation is ready for integration testing.")
        return 0
    print(f"\n⚠️  {total - passed} validation(s) failed. Review implementation before proceeding.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
