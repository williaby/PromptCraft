#!/usr/bin/env python3
"""Check for dependency issues and security vulnerabilities."""
import json
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def check_poetry_lock() -> bool:
    """Verify poetry.lock is up to date."""
    print("Checking poetry.lock consistency...")
    code, _, stderr = run_command(["poetry", "lock", "--check"])
    if code != 0:
        print(f"❌ poetry.lock is out of date: {stderr}")
        return False
    print("✅ poetry.lock is up to date")
    return True


def check_requirements_sync() -> bool:
    """Verify requirements.txt is in sync with poetry.lock."""
    print("\nChecking requirements.txt sync...")

    # Generate fresh requirements
    run_command(["./scripts/generate_requirements.sh"])

    # Check if files changed
    code, stdout, _ = run_command(["git", "diff", "--name-only", "requirements*.txt"])
    if stdout.strip():
        print("❌ requirements files are out of sync")
        print(f"   Changed files: {stdout.strip()}")
        return False
    print("✅ requirements files are in sync")
    return True


def check_security() -> bool:
    """Run security checks."""
    print("\nRunning security checks...")

    # Safety check
    print("  Running safety check...")
    code, stdout, _ = run_command(["poetry", "run", "safety", "check", "--json"])
    if code != 0:
        try:
            issues = json.loads(stdout)
            print(f"❌ Found {len(issues)} security vulnerabilities")
            max_issues_to_show = 5
            for issue in issues[:max_issues_to_show]:  # Show first 5
                print(f"   - {issue['package']}: {issue['vulnerability']}")
            if len(issues) > max_issues_to_show:
                print(f"   ... and {len(issues) - max_issues_to_show} more")
        except (json.JSONDecodeError, KeyError):
            print("❌ Safety check failed")
        return False
    print("  ✅ No known vulnerabilities")

    # Bandit check
    print("  Running bandit check...")
    code, _, _ = run_command(["poetry", "run", "bandit", "-r", "src", "-ll", "-q"])
    if code != 0:
        print("  ❌ Bandit found security issues")
        return False
    print("  ✅ No security issues found")

    return True


def check_pip_hash_install() -> bool:
    """Verify pip can install with hash verification."""
    print("\nChecking pip hash verification...")

    # Create a temporary venv
    import tempfile
    import venv

    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "test_venv"
        venv.create(venv_path, with_pip=True)

        pip_path = venv_path / "bin" / "pip"

        # Try to install with hashes
        code, _, stderr = run_command(
            [
                str(pip_path),
                "install",
                "--dry-run",
                "--require-hashes",
                "-r",
                "requirements.txt",
            ],
        )

        if code != 0:
            print(f"❌ Hash verification failed: {stderr[:200]}")
            return False

    print("✅ Hash verification successful")
    return True


def main() -> int:
    """Run all checks."""
    print("🔍 PromptCraft Dependency Security Check\n")

    checks = [
        check_poetry_lock(),
        check_requirements_sync(),
        check_security(),
        check_pip_hash_install(),
    ]

    if all(checks):
        print("\n✅ All checks passed!")
        return 0
    print("\n❌ Some checks failed. Please fix the issues above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
