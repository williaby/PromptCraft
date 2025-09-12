#!/usr/bin/env python3
"""Check for dependency issues and security vulnerabilities."""

import json
from pathlib import Path
import subprocess
import sys


def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    # Security: cmd list is validated by callers, no shell=True used
    result = subprocess.run(  # noqa: S603
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def check_poetry_lock() -> bool:
    """Verify poetry.lock is up to date."""
    print("Checking poetry.lock consistency...")
    code, _, stderr = run_command(["poetry", "check", "--lock"])
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
    max_display = 5  # Maximum vulnerabilities to display

    # Safety check using new scan command
    print("  Running safety scan...")
    code, stdout, stderr = run_command(
        ["poetry", "run", "safety", "scan", "--output", "json"],
    )

    # Parse JSON output (safety outputs to stdout for JSON format)
    vulnerability_details: list[dict[str, str]] = []
    try:
        if stdout.strip():
            safety_data = json.loads(stdout)
            # Extract vulnerabilities from Safety scan results
            _extract_vulnerabilities(safety_data, vulnerability_details)

        if vulnerability_details:
            print(f"  ❌ Found {len(vulnerability_details)} security vulnerabilities:")
            for vuln in vulnerability_details[:max_display]:
                print(
                    f"     - {vuln['package']}: ID {vuln['id']} "
                    f"(vulnerable: {vuln['vulnerable_spec']}, "
                    f"recommended: {vuln['recommended']})",
                )
            if len(vulnerability_details) > max_display:
                print(f"     ... and {len(vulnerability_details) - max_display} more")
            return False
    except (json.JSONDecodeError, KeyError):
        if code != 0:
            print(f"  ❌ Safety scan failed with code {code}: {stderr}")
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


def _extract_vulnerabilities(
    safety_data: dict,
    vulnerability_details: list[dict[str, str]],
) -> None:
    """Extract vulnerability details from Safety scan data."""
    for project in safety_data.get("scan_results", {}).get("projects", []):
        for file in project.get("files", []):
            for dep in file.get("results", {}).get("dependencies", []):
                dep_name = dep.get("name", "unknown")
                for spec in dep.get("specifications", []):
                    vulns = spec.get("vulnerabilities", {}).get(
                        "known_vulnerabilities",
                        [],
                    )
                    if vulns:
                        remediation = spec.get("vulnerabilities", {}).get(
                            "remediation",
                            {},
                        )
                        recommended = remediation.get("recommended", "unknown")
                        for vuln in vulns:
                            vulnerability_details.append(
                                {
                                    "package": dep_name,
                                    "id": vuln.get("id", "unknown"),
                                    "vulnerable_spec": vuln.get(
                                        "vulnerable_spec",
                                        "unknown",
                                    ),
                                    "recommended": recommended,
                                },
                            )


def check_pip_hash_install() -> bool:
    """Verify pip can install with hash verification (simplified check)."""
    print("\nChecking requirements file integrity...")

    # Just verify the requirements file has hashes
    try:
        requirements_file = Path("requirements.txt")
        content = requirements_file.read_text()
        if "--hash=sha256:" in content:
            print("✅ Requirements file contains SHA256 hashes")
            return True
        print("❌ Requirements file missing SHA256 hashes")
        return False
    except FileNotFoundError:
        print("❌ Requirements file not found")
        return False


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
