#!/usr/bin/env python3
"""Test script to inject CSS into standard coverage reports."""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the automation class
from scripts.simplified_coverage_automation import SimplifiedCoverageAutomation


def main() -> None:
    """Test CSS injection functionality."""
    automation = SimplifiedCoverageAutomation()

    automation._inject_css_into_standard_reports()


if __name__ == "__main__":
    main()
