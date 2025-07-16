#!/usr/bin/env python3
"""
Run the integration test and capture output.
"""

import os
import subprocess
import sys


def run_integration_test():
    """Run the integration test script."""
    print("Running HyDE Processor and Vector Store Integration Test...")
    print("=" * 70)

    # Change to the correct directory
    os.chdir("/home/byron/dev/PromptCraft")

    try:
        # Run the integration test
        result = subprocess.run(
            [sys.executable, "integration_test_summary.py"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        print("INTEGRATION TEST OUTPUT:")
        print("-" * 40)
        print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print("-" * 40)
            print(result.stderr)

        print(f"\nReturn code: {result.returncode}")

        if result.returncode == 0:
            print("\n🎉 Integration test PASSED!")
            return True
        print("\n❌ Integration test FAILED!")
        return False

    except subprocess.TimeoutExpired:
        print("❌ Integration test timed out!")
        return False
    except Exception as e:
        print(f"❌ Error running integration test: {e}")
        return False


if __name__ == "__main__":
    success = run_integration_test()
    print("\n" + "=" * 70)
    print("Integration test runner complete.")
    print("=" * 70)
    sys.exit(0 if success else 1)
