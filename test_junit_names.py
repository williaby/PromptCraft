#!/usr/bin/env python3
"""Test script to generate JUnit XML and check test names."""

import os
import sys

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Run the specific parametrized test
if __name__ == "__main__":
    # Run the specific parametrized test that has large strings
    pytest.main(
        [
            "tests/unit/test_edge_cases_parametrized.py::TestInputSanitizationBoundaries::test_input_sanitization_boundaries",
            "-v",
            "--junitxml=junit_test.xml",
            "--tb=short",
            "--ignore=tests/conftest.py",
        ],
    )
