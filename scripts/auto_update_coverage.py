#!/usr/bin/env python3
"""
Simple Auto-Update Coverage Reports

This script provides a simple way to automatically update coverage reports
after VS Code test runs. It combines the old and new systems for maximum compatibility.

Usage:
  python scripts/auto_update_coverage.py              # Auto-detect and update
  python scripts/auto_update_coverage.py --force      # Force update
  python scripts/auto_update_coverage.py --watch      # Watch for changes
"""

import argparse
import sys
import time
from pathlib import Path

def check_fresh_coverage_data():
    """Check if we have fresh coverage data from recent test run."""
    project_root = Path(__file__).parent.parent
    coverage_file = project_root / ".coverage"
    coverage_xml = project_root / "coverage.xml"
    
    if not coverage_file.exists():
        return False, "No .coverage file found"
    
    # Check if coverage file is recent (within last 10 minutes)
    coverage_age = time.time() - coverage_file.stat().st_mtime
    if coverage_age > 600:  # 10 minutes
        return False, f"Coverage data is {coverage_age/60:.1f} minutes old"
    
    return True, f"Fresh coverage data ({coverage_age:.0f}s old)"

def run_coverage_automation():
    """Run both automation systems for maximum compatibility."""
    project_root = Path(__file__).parent.parent
    
    # Try the new v2 system first
    try:
        print("🚀 Running new modular automation system...")
        result = subprocess.run([
            sys.executable, "scripts/simplified_coverage_automation_v2.py", "--force"
        ], cwd=project_root, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ New v2 system completed successfully")
            return True
    except Exception as e:
        print(f"⚠️ New v2 system failed: {e}")
    
    # Fallback to original system
    try:
        print("🔄 Running original automation system...")
        result = subprocess.run([
            sys.executable, "scripts/simplified_coverage_automation.py", "--force"
        ], cwd=project_root, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Original system completed successfully")
            return True
    except Exception as e:
        print(f"❌ Original system failed: {e}")
    
    return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Auto-update coverage reports")
    parser.add_argument("--force", action="store_true", help="Force update even if data seems stale")
    parser.add_argument("--watch", action="store_true", help="Watch for coverage file changes")
    args = parser.parse_args()
    
    print("📊 Auto Coverage Report Updater")
    print("=" * 40)
    
    if args.watch:
        print("👀 Watching for coverage file changes...")
        # Simple file watching - check every 5 seconds
        project_root = Path(__file__).parent.parent
        coverage_file = project_root / ".coverage"
        last_mtime = 0
        
        try:
            while True:
                if coverage_file.exists():
                    current_mtime = coverage_file.stat().st_mtime
                    if current_mtime > last_mtime:
                        print(f"\n🔄 Coverage file updated, generating reports...")
                        if run_coverage_automation():
                            print("✅ Reports updated successfully")
                        else:
                            print("❌ Report generation failed")
                        last_mtime = current_mtime
                
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n👋 Stopping coverage watcher")
            return
    
    # Single run mode
    if not args.force:
        fresh, message = check_fresh_coverage_data()
        print(f"📊 Coverage data status: {message}")
        
        if not fresh:
            print("ℹ️  Use --force to update anyway")
            return
    
    if run_coverage_automation():
        print("\n🎉 Coverage reports updated successfully!")
        print(f"📂 Main report: file://{Path(__file__).parent.parent}/reports/coverage/simplified_report.html")
    else:
        print("\n❌ Failed to update coverage reports")
        sys.exit(1)

if __name__ == "__main__":
    import subprocess
    main()