#!/usr/bin/env python3
"""
MyPy CI Match Script

This script runs MyPy with the exact same configuration and cache settings
as the CI environment to ensure local results match CI results.

Usage:
    python scripts/mypy_ci_match.py
    # or
    poetry run python scripts/mypy_ci_match.py
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def run_mypy_ci_match():
    """Run MyPy with CI-matching configuration."""
    print("🔍 Running MyPy with CI-matching settings...")

    # Create a temporary cache directory (like CI)
    with tempfile.TemporaryDirectory(prefix="mypy_ci_cache_") as temp_cache:
        print(f"📁 Using fresh cache directory: {temp_cache}")

        # Set environment variables to match CI
        env = os.environ.copy()
        env.update(
            {
                "CI_ENVIRONMENT": "true",
                "MYPY_CACHE_DIR": temp_cache,
            }
        )

        # Run MyPy with the exact same command as CI
        cmd = ["poetry", "run", "mypy", "src", f"--cache-dir={temp_cache}"]

        print(f"🚀 Running command: {' '.join(cmd)}")
        print("=" * 60)

        try:
            result = subprocess.run(
                cmd,
                env=env,
                cwd=Path(__file__).parent.parent,  # Project root
                check=False,  # Don't raise on non-zero exit
                capture_output=False,  # Show output in real-time
            )

            print("=" * 60)
            if result.returncode == 0:
                print("✅ MyPy CI match: SUCCESS - No errors found!")
                print("🎯 Local results now match CI expectations")
            else:
                print(f"❌ MyPy CI match: FAILED - Exit code {result.returncode}")
                print("🔧 Errors found that need to be fixed for CI compliance")

            return result.returncode == 0

        except Exception as e:
            print(f"❌ Error running MyPy CI match: {e}")
            return False


def clear_local_mypy_cache():
    """Clear local MyPy cache to start fresh."""
    cache_paths = [
        Path.home() / ".mypy_cache",
        Path.home() / ".cache" / "mypy",
        Path(".mypy_cache"),
    ]

    for cache_path in cache_paths:
        if cache_path.exists():
            print(f"🧹 Clearing MyPy cache: {cache_path}")
            try:
                import shutil

                shutil.rmtree(cache_path)
                print(f"✅ Cleared: {cache_path}")
            except Exception as e:
                print(f"⚠️  Could not clear {cache_path}: {e}")


if __name__ == "__main__":
    print("🎯 MyPy CI Match Tool")
    print("This tool runs MyPy with CI-identical settings")
    print()

    # Optional: Clear local cache first
    if "--clear-cache" in sys.argv:
        clear_local_mypy_cache()
        print()

    # Run MyPy with CI settings
    success = run_mypy_ci_match()

    if success:
        print("\n🎉 SUCCESS: Local MyPy results match CI!")
        print("💡 Your code will pass CI type checking")
    else:
        print("\n🔧 FAILED: Local MyPy results don't match CI")
        print("💡 Fix the errors above to match CI expectations")
        print("💡 Tip: Run with --clear-cache to start with fresh cache")

    sys.exit(0 if success else 1)
