#!/usr/bin/env python3
"""Check for dependency issues and security vulnerabilities."""
import subprocess
import sys
import json
from pathlib import Path

def run_command(cmd: list[str]) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def check_poetry_lock():
    """Verify poetry.lock is up to date."""
    print("Checking poetry.lock consistency...")
    code, _, stderr = run_command(["poetry", "lock", "--check"])
    if code != 0:
        print(f"❌ poetry.lock is out of date: {stderr}")
        return False
    print("✅ poetry.lock is up to date")
    return True

def check_requirements_sync():
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

def check_security():
    """Run security checks."""
    print("\nRunning security checks...")
    
    # Safety check
    print("  Running safety check...")
    code, stdout, _ = run_command(["poetry", "run", "safety", "check", "--json"])
    if code != 0:
        try:
            issues = json.loads(stdout)
            print(f"❌ Found {len(issues)} security vulnerabilities")
            for issue in issues[:5]:  # Show first 5
                print(f"   - {issue['package']}: {issue['vulnerability']}")
            if len(issues) > 5:
                print(f"   ... and {len(issues) - 5} more")
        except:
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

def check_pip_hash_install():
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
        code, _, stderr = run_command([
            str(pip_path), "install", "--dry-run", 
            "--require-hashes", "-r", "requirements.txt"
        ])
        
        if code != 0:
            print(f"❌ Hash verification failed: {stderr[:200]}")
            return False
    
    print("✅ Hash verification successful")
    return True

def main():
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
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
