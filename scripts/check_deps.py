#!/usr/bin/env python3
"""Check for dependency issues and security vulnerabilities."""

import json
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


def check_uv_lock() -> bool:
    """Verify uv.lock is up to date."""
    print("Checking uv.lock consistency...")
    code, _, stderr = run_command(["uv", "lock", "--check"])
    if code != 0:
        print(f"❌ uv.lock is out of date: {stderr}")
        return False
    print("✅ uv.lock is up to date")
    return True


def check_security() -> bool:
    """Run security checks."""
    print("\nRunning security checks...")
    max_display = 5  # Maximum vulnerabilities to display

    # pip-audit dependency vulnerability scan
    print("  Running pip-audit scan...")
    code, stdout, stderr = run_command(
        ["uv", "run", "--frozen", "pip-audit", "--format=json"],
    )

    # Parse JSON output from pip-audit
    vulnerability_details: list[dict[str, str]] = []
    try:
        if stdout.strip():
            audit_data = json.loads(stdout)
            _extract_vulnerabilities(audit_data, vulnerability_details)

        if vulnerability_details:
            print(f"  ❌ Found {len(vulnerability_details)} security vulnerabilities:")
            for vuln in vulnerability_details[:max_display]:
                print(
                    f"     - {vuln['package']}: ID {vuln['id']} "
                    f"(installed: {vuln['installed_version']}, "
                    f"fix: {vuln['fix_versions']})",
                )
            if len(vulnerability_details) > max_display:
                print(f"     ... and {len(vulnerability_details) - max_display} more")
            return False
    except (json.JSONDecodeError, KeyError):
        if code != 0:
            print(f"  ❌ pip-audit scan failed with code {code}: {stderr}")
            return False

    print("  ✅ No known vulnerabilities")

    # Bandit check
    print("  Running bandit check...")
    code, _, _ = run_command(["uv", "run", "--frozen", "bandit", "-r", "src", "-ll", "-q"])
    if code != 0:
        print("  ❌ Bandit found security issues")
        return False
    print("  ✅ No security issues found")

    return True


def _extract_vulnerabilities(
    audit_data: dict,
    vulnerability_details: list[dict[str, str]],
) -> None:
    """Extract vulnerability details from pip-audit JSON output.

    pip-audit emits: {"dependencies": [{"name": ..., "version": ..., "vulns": [
        {"id": ..., "fix_versions": [...], "description": ...},
    ]}, ...]}
    """
    for dep in audit_data.get("dependencies", []):
        name = dep.get("name", "unknown")
        installed_version = dep.get("version", "unknown")
        for vuln in dep.get("vulns", []):
            fix_versions = vuln.get("fix_versions", []) or []
            vulnerability_details.append(
                {
                    "package": name,
                    "id": vuln.get("id", "unknown"),
                    "installed_version": installed_version,
                    "fix_versions": ", ".join(fix_versions) if fix_versions else "none",
                },
            )


def main() -> int:
    """Run all checks."""
    print("🔍 PromptCraft Dependency Security Check\n")

    checks = [
        check_uv_lock(),
        check_security(),
    ]

    if all(checks):
        print("\n✅ All checks passed!")
        return 0
    print("\n❌ Some checks failed. Please fix the issues above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
