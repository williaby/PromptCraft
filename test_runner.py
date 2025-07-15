#!/usr/bin/env python3
"""Simple test runner to check performance tests."""

import os
import subprocess
import sys


def main():
    print("Starting performance test runner...")

    # Change to the correct directory
    os.chdir("/home/byron/dev/PromptCraft")

    print(f"Current directory: {os.getcwd()}")
    print(f"Python version: {sys.version}")

    # Try to run the performance tests
    try:
        print("Running production readiness tests...")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/performance/test_production_readiness.py",
                "-v",
                "-x",
                "--tb=short",
            ],
            check=False, capture_output=True,
            text=True,
            timeout=300,
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        print(f"\nReturn code: {result.returncode}")

    except Exception as e:
        print(f"Error running pytest: {e}")

        # Try the quick performance test instead
        try:
            print("\nTrying quick performance test...")
            result = subprocess.run(
                [sys.executable, "test_performance_quick.py"], check=False, capture_output=True, text=True, timeout=300,
            )

            print("STDOUT:")
            print(result.stdout)

            if result.stderr:
                print("\nSTDERR:")
                print(result.stderr)

            print(f"\nReturn code: {result.returncode}")

        except Exception as e2:
            print(f"Error running quick test: {e2}")


if __name__ == "__main__":
    main()
