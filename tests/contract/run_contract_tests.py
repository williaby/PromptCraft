#!/usr/bin/env python3
"""
Contract Test Runner

Script to run MCP contract tests with local servers.
"""

import os
from pathlib import Path
import subprocess
import sys


def install_dependencies():
    """Install pact-python and other dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.run(["poetry", "install"], check=True, cwd=Path(__file__).parent)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)


def check_pact_binary():
    """Check if pact-mock-service binary is available."""
    import shutil
    
    if shutil.which("pact-mock-service"):
        print("✅ pact-mock-service binary found")
        return True
    
    print("⚠️  pact-mock-service binary not found")
    print("Install with: gem install pact-mock_service")
    print("Or install pact-ruby-standalone")
    return False


def run_contract_tests():
    """Run the contract tests."""
    print("🧪 Running contract tests...")
    
    # Set test environment variables
    env = os.environ.copy()
    env.update({
        "PACT_TEST_MODE": "consumer",
        "CONTRACT_TEST": "true",
        "LOG_LEVEL": "INFO",
    })
    
    try:
        # Run contract tests specifically
        result = subprocess.run([
            "poetry", "run", "pytest", 
            "tests/contract/test_mcp_contracts.py",
            "-v",
            "-m", "contract",
            "--tb=short",
        ], 
        check=False, env=env,
        cwd=Path(__file__).parent,
        )
        
        if result.returncode == 0:
            print("✅ Contract tests passed!")
        else:
            print("❌ Contract tests failed")
            
        return result.returncode == 0
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run contract tests: {e}")
        return False


def main():
    """Main test runner."""
    print("🚀 MCP Contract Test Runner")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("pyproject.toml").exists():
        print("❌ Must be run from project root (where pyproject.toml exists)")
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Check for pact binary (optional - tests can run without it)
    pact_available = check_pact_binary()
    if not pact_available:
        print("Note: Some Pact features may be limited without pact-mock-service binary")
    
    # Run tests
    success = run_contract_tests()
    
    if success:
        print("\n🎉 All contract tests completed successfully!")
        print("\nPact files generated in: ./pacts/")
        print("Test servers used:")
        print("  - zen-mcp-server on localhost:8080")
        print("  - heimdall-stub on localhost:8081")
    else:
        print("\n💥 Contract tests failed - check output above")
        sys.exit(1)


if __name__ == "__main__":
    main()