#!/usr/bin/env python3
"""Simple test runner that executes the integration test."""

import os
import subprocess
import sys


def main():
    # Change to the correct directory
    os.chdir("/home/byron/dev/PromptCraft")

    # Run the test
    try:
        result = subprocess.run(
            [sys.executable, "test_hyde_vector_integration.py"],
            check=False,
            capture_output=True,
            text=True,
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        print(f"\nReturn code: {result.returncode}")

    except Exception as e:
        print(f"Error running test: {e}")


if __name__ == "__main__":
    main()
