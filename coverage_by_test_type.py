#!/usr/bin/env python3
"""
Coverage analysis by test type - shows both test count distribution 
and actual code coverage achieved by each test layer.
"""

import subprocess
import json
import re
from pathlib import Path
from collections import defaultdict

def run_coverage_by_marker(marker, description):
    """Run coverage analysis for specific test marker."""
    print(f"  🔍 Running {description}...")
    
    try:
        result = subprocess.run([
            'poetry', 'run', 'pytest',
            '-m', marker,
            '--cov=src', '--cov-branch', '--cov-report=json',
            '--cov-report=term-missing:skip-covered',
            '-q', '--tb=no', '--maxfail=3'
        ], capture_output=True, text=True, timeout=120)
        
        # Parse coverage.json
        coverage_file = Path('coverage.json')
        coverage_data = {}
        
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                coverage_json = json.load(f)
            
            totals = coverage_json.get('totals', {})
            coverage_data = {
                'overall_coverage': totals.get('percent_covered_display', 0.0),
                'statements_covered': totals.get('covered_lines', 0),
                'total_statements': totals.get('num_statements', 0),
                'branches_covered': totals.get('covered_branches', 0),
                'total_branches': totals.get('num_branches', 0),
                'files_analyzed': len(coverage_json.get('files', {}))
            }
            
            # Count tests run
            output = result.stdout + result.stderr
            test_match = re.search(r'(\d+) passed', output)
            if test_match:
                coverage_data['tests_run'] = int(test_match.group(1))
            else:
                coverage_data['tests_run'] = 0
        
        return coverage_data
    
    except Exception as e:
        print(f"    ⚠️ Error running {description}: {e}")
        return {
            'overall_coverage': 0.0,
            'statements_covered': 0,
            'total_statements': 0,
            'tests_run': 0,
            'files_analyzed': 0
        }

def analyze_coverage_by_test_type():
    """Analyze coverage achieved by each test type."""
    
    print("📊 ANALYZING COVERAGE BY TEST TYPE")
    print("=" * 60)
    
    # Test layers to analyze
    test_layers = [
        ('unit', 'Unit tests only'),
        ('integration', 'Integration tests only'), 
        ('security', 'Security tests only'),
        ('contract', 'Contract tests only'),
        ('not slow', 'All fast tests (current dev cycle)'),
        ('', 'All tests (including slow)')  # Empty marker = all tests
    ]
    
    results = {}
    
    for marker, description in test_layers:
        if marker:
            coverage_data = run_coverage_by_marker(marker, description)
        else:
            # Run all tests
            coverage_data = run_coverage_by_marker('not xyz_nonexistent_marker', description)
        
        results[marker or 'all'] = coverage_data
    
    return results

def print_coverage_analysis(results):
    """Print comprehensive coverage analysis."""
    
    print(f"\n📈 COVERAGE BY TEST TYPE")
    print("-" * 90)
    print(f"{'Test Type':<25} {'Tests':<8} {'Coverage':<10} {'Statements':<12} {'Files':<6} {'Efficiency'}")
    print("-" * 90)
    
    # Calculate efficiency (coverage per test)
    for test_type, data in results.items():
        tests_run = data.get('tests_run', 0)
        coverage = data.get('overall_coverage', 0.0)
        statements = data.get('statements_covered', 0)
        total_statements = data.get('total_statements', 0)
        files = data.get('files_analyzed', 0)
        
        # Efficiency: coverage points per test
        efficiency = coverage / tests_run if tests_run > 0 else 0
        
        # Format display name
        display_name = {
            'unit': 'Unit Tests',
            'integration': 'Integration Tests',
            'security': 'Security Tests', 
            'contract': 'Contract Tests',
            'not slow': 'Fast Tests (Dev Cycle)',
            'all': 'All Tests'
        }.get(test_type, test_type)
        
        print(f"{display_name:<25} {tests_run:<8} {coverage:>6.1f}%    {statements:>4}/{total_statements:<4}   {files:<6} {efficiency:>6.2f}")
    
    # Gap analysis
    print(f"\n🔍 COVERAGE GAP ANALYSIS")
    print("-" * 50)
    
    unit_coverage = results.get('unit', {}).get('overall_coverage', 0)
    all_coverage = results.get('all', {}).get('overall_coverage', 0)
    integration_coverage = results.get('integration', {}).get('overall_coverage', 0)
    
    print(f"Unit Test Coverage:        {unit_coverage:6.1f}%")
    print(f"Integration Test Coverage: {integration_coverage:6.1f}%")
    print(f"Total Coverage:            {all_coverage:6.1f}%")
    
    # Calculate incremental value
    if unit_coverage > 0 and all_coverage > 0:
        integration_incremental = all_coverage - unit_coverage
        print(f"Integration Incremental:   {integration_incremental:+6.1f}%")
        
        if integration_incremental < 5:
            print("⚠️  Integration tests provide minimal additional coverage")
        elif integration_incremental > 15:
            print("✅ Integration tests provide significant additional coverage")
    
    # Test pyramid health check
    print(f"\n🏗️ TEST PYRAMID HEALTH")
    print("-" * 40)
    
    unit_tests = results.get('unit', {}).get('tests_run', 0)
    integration_tests = results.get('integration', {}).get('tests_run', 0)
    total_fast_tests = results.get('not slow', {}).get('tests_run', 0)
    
    if total_fast_tests > 0:
        unit_percentage = (unit_tests / total_fast_tests) * 100
        integration_percentage = (integration_tests / total_fast_tests) * 100
        
        print(f"Unit Tests:       {unit_tests:4} ({unit_percentage:5.1f}%) [Target: 65-75%]")
        print(f"Integration:      {integration_tests:4} ({integration_percentage:5.1f}%) [Target: 5-10%]")
        
        # Health indicators
        if unit_percentage < 65:
            print("❌ INVERTED PYRAMID: Too few unit tests")
        elif unit_percentage > 75:
            print("⚠️  OVER-UNIT: Consider adding integration tests")
        else:
            print("✅ HEALTHY PYRAMID: Good unit test ratio")
        
        if integration_percentage > 10:
            print("❌ INTEGRATION HEAVY: Too many slow integration tests")
        else:
            print("✅ INTEGRATION BALANCED: Good integration test ratio")

def suggest_improvements(results):
    """Suggest specific improvements based on analysis."""
    
    print(f"\n💡 IMPROVEMENT RECOMMENDATIONS")
    print("-" * 50)
    
    unit_coverage = results.get('unit', {}).get('overall_coverage', 0)
    unit_tests = results.get('unit', {}).get('tests_run', 0)
    integration_tests = results.get('integration', {}).get('tests_run', 0)
    total_coverage = results.get('all', {}).get('overall_coverage', 0)
    
    # Coverage recommendations
    if unit_coverage < 70:
        print(f"1. 🎯 UNIT COVERAGE: Increase from {unit_coverage:.1f}% to 70%+")
        print("   → Focus on core business logic, utils, and model classes")
    
    if total_coverage < 80:
        gap = 80 - total_coverage
        print(f"2. 📈 TOTAL COVERAGE: Increase by {gap:.1f}% to reach 80% minimum")
    
    # Test composition recommendations  
    total_fast = unit_tests + integration_tests
    if total_fast > 0:
        unit_ratio = (unit_tests / total_fast) * 100
        if unit_ratio < 65:
            needed_units = int((total_fast * 0.65) - unit_tests)
            print(f"3. 🔺 UNIT TESTS: Add ~{needed_units} unit tests for healthy pyramid")
    
    # Specific areas that likely need unit tests
    print(f"\n🎯 FOCUS AREAS FOR UNIT TESTS:")
    print("   → src/auth/ (JWT validation, middleware)")
    print("   → src/ui/ (component functions, export utils)")  
    print("   → src/core/ (business logic, processors)")
    print("   → src/utils/ (utility functions)")
    print("   → src/config/ (configuration validation)")
    
    print(f"\n🔧 DEVELOPMENT WORKFLOW:")
    print("   → Use 'nox -s unit' to run only unit tests during development")
    print("   → Use 'nox -s fast' to exclude slow tests (current setup)")
    print("   → Use 'python coverage_by_test_type.py' to monitor progress")

def main():
    """Main function."""
    print("🔍 Starting comprehensive coverage analysis by test type...")
    print("This will run different test combinations to measure coverage contribution.\n")
    
    results = analyze_coverage_by_test_type()
    print_coverage_analysis(results)
    suggest_improvements(results)
    
    print(f"\n" + "=" * 90)
    print("💾 TIP: Run this regularly to track test quality improvements")

if __name__ == "__main__":
    main()