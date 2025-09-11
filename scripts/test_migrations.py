#!/usr/bin/env python3
"""
Test script for database migrations.

This script validates that Alembic migrations can be run successfully
in a test environment.
"""

import os
from pathlib import Path
import subprocess
import sys


# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_migration_syntax():
    """Test that all migration files have valid Python syntax."""
    print("🔍 Testing migration file syntax...")

    versions_dir = project_root / "alembic" / "versions"
    migration_files = list(versions_dir.glob("*.py"))

    if not migration_files:
        print("❌ No migration files found!")
        return False

    for migration_file in migration_files:
        try:
            # Compile the Python file to check syntax
            with open(migration_file) as f:
                compile(f.read(), str(migration_file), "exec")
            print(f"✅ {migration_file.name} - syntax OK")
        except SyntaxError as e:
            print(f"❌ {migration_file.name} - syntax error: {e}")
            return False
        except Exception as e:
            print(f"⚠️  {migration_file.name} - warning: {e}")

    return True


def test_alembic_config():
    """Test that Alembic configuration is valid."""
    print("\n🔍 Testing Alembic configuration...")

    try:
        # Test that alembic can load the configuration
        result = subprocess.run(
            ["poetry", "run", "alembic", "history"], check=False, cwd=project_root, capture_output=True, text=True, timeout=30,
        )

        if result.returncode == 0:
            print("✅ Alembic configuration is valid")
            print(f"📋 Migration history:\n{result.stdout}")
            return True
        print(f"❌ Alembic configuration error: {result.stderr}")
        return False

    except subprocess.TimeoutExpired:
        print("❌ Alembic command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing Alembic config: {e}")
        return False


def test_offline_migration():
    """Test offline migration generation."""
    print("\n🔍 Testing offline migration...")

    # Set up environment for offline mode
    env = os.environ.copy()
    env["PROMPTCRAFT_DATABASE_URL"] = "postgresql+psycopg2://test:test@localhost:5432/test_db"

    try:
        # Test offline migration (SQL generation without database connection)
        result = subprocess.run(
            ["poetry", "run", "alembic", "upgrade", "001", "--sql"],
            check=False, cwd=project_root,
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )

        if result.returncode == 0 and "CREATE TABLE" in result.stdout:
            print("✅ Offline migration generates valid SQL")
            return True
        print(f"❌ Offline migration failed: {result.stderr}")
        return False

    except subprocess.TimeoutExpired:
        print("❌ Offline migration command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing offline migration: {e}")
        return False


def main():
    """Run all migration tests."""
    print("🚀 Starting database migration tests...\n")

    tests = [
        ("Migration Syntax", test_migration_syntax),
        ("Alembic Configuration", test_alembic_config),
        ("Offline Migration", test_offline_migration),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Migration Test Results:")
    print("=" * 50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1

    print(f"\n🎯 Tests passed: {passed}/{len(results)}")

    if passed == len(results):
        print("🎉 All migration tests passed! Database migrations are ready for production.")
        return 0
    print("⚠️  Some migration tests failed. Please review and fix issues before production deployment.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
