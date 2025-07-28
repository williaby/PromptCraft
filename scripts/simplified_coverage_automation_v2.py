#!/usr/bin/env python3
"""
PromptCraft Coverage Automation v2.0 - Refactored Entry Point

This script provides the new modular coverage automation system while maintaining
backward compatibility with the original simplified_coverage_automation.py.

Key Improvements:
- ✅ Modular architecture (watcher, classifier, renderer, cli)
- ✅ Enhanced error handling with structured logging
- ✅ Security hardening with proper path validation and HTML sanitization
- ✅ Codecov flag mapping for unified local/remote views
- ✅ Performance improvements with caching and optimization

Usage:
    # After running "Run Tests with Coverage" in VS Code:
    python scripts/simplified_coverage_automation_v2.py

    # Force generation:
    python scripts/simplified_coverage_automation_v2.py --force

    # Validate environment:
    python scripts/simplified_coverage_automation_v2.py --validate

Migration Guide:
    The new system maintains full API compatibility while providing enhanced
    features. Replace calls to simplified_coverage_automation.py with this script.
"""

import sys
from pathlib import Path

# Add the coverage_automation package to the path
sys.path.insert(0, str(Path(__file__).parent))

from coverage_automation.cli import main

if __name__ == "__main__":
    sys.exit(main())
