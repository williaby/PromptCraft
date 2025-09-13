#!/usr/bin/env python3
"""
Launcher script for AI Tools validation slash command.
This script provides a clean interface for the Claude Code slash command.
"""

import argparse
from pathlib import Path
import subprocess
import sys


def main() -> None:
    """Main launcher function."""
    parser = argparse.ArgumentParser(description="AI Tools Validator Launcher")
    parser.add_argument("--quiet", action="store_true", help="Quiet output")
    parser.add_argument("--setup", action="store_true", help="Setup project")
    parser.add_argument("--install", action="store_true", help="Install missing tools")

    args = parser.parse_args()

    # Build arguments for the main script
    script_args = []

    if args.quiet:
        script_args.append("--quiet")

    if args.setup:
        script_args.append("--setup-project")

    if args.install:
        script_args.append("--install-missing")

    # Path to the main validation script
    script_path = Path.home() / ".claude" / "scripts" / "ai_tools_validator.py"

    try:
        # Execute the main validation script
        result = subprocess.run(
            ["python", str(script_path), *script_args],
            check=False,
            cwd=Path.cwd(),
        )

        sys.exit(result.returncode)

    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()
