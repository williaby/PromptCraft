#!/usr/bin/env python3
"""
Quick test composition analysis without running tests.
Analyzes markers and provides test pyramid metrics.
"""

import subprocess
import re
from collections import defaultdict, Counter

def analyze_marker_composition():
    """Quickly analyze test composition by marker."""
    
    print("🔍 Analyzing test composition by marker...")
    
    # Marker mapping for analysis
    markers = ['unit', 'component', 'contract', 'integration', 'e2e', 'perf', 'chaos', 'security', 'slow']
    
    composition = {}
    
    for marker in markers:
        try:
            result = subprocess.run([
                'poetry', 'run', 'pytest', 
                '--collect-only', '-q', '--tb=no', '--no-cov',
                '-m', marker
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout
                if 'tests collected' in output:
                    match = re.search(r'(\d+)/?(\d+)? tests? collected', output)
                    if match:
                        count = int(match.group(1))
                        composition[marker] = count
                        print(f"  {marker:12}: {count:4} tests")
                    else:
                        composition[marker] = 0
                        print(f"  {marker:12}: {0:4} tests")
                else:
                    composition[marker] = 0
                    print(f"  {marker:12}: {0:4} tests")
        except Exception as e:
            print(f"  {marker:12}: Error - {e}")
            composition[marker] = 0
    
    # Get total without slow marker
    try:
        result = subprocess.run([
            'poetry', 'run', 'pytest', 
            '--collect-only', '-q', '--tb=no', '--no-cov',
            '-m', 'not slow'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = result.stdout
            if 'tests collected' in output:
                match = re.search(r'(\d+)/?(\d+)? tests? collected', output)
                if match:
                    total_fast = int(match.group(1))
                    composition['total_fast'] = total_fast
                    print(f"  {'total_fast':12}: {total_fast:4} tests")
    except Exception as e:
        print(f"  total_fast: Error - {e}")
    
    return composition

def print_test_pyramid_analysis(composition):
    """Print test pyramid analysis."""
    
    print("\n" + "=" * 80)
    print("🏗️ TEST PYRAMID ANALYSIS")
    print("=" * 80)
    
    total_fast = composition.get('total_fast', 1)
    
    # Calculate percentages
    layers = [
        ('Unit', composition.get('unit', 0), '65-75%'),
        ('Component', composition.get('component', 0), '15-25%'),
        ('Integration', composition.get('integration', 0), '5-10%'),
        ('E2E', composition.get('e2e', 0), '2-5%'),
        ('Performance', composition.get('perf', 0), '3-8%'),
        ('Security', composition.get('security', 0), '2-5%'),
        ('Contract', composition.get('contract', 0), '1-3%'),
        ('Chaos', composition.get('chaos', 0), '1-2%'),
    ]
    
    print(f"\n📊 TEST DISTRIBUTION (excluding slow tests)")
    print(f"{'Layer':<15} {'Count':<8} {'Percentage':<12} {'Target Range':<15} {'Status'}")
    print("-" * 75)
    
    for layer, count, target_range in layers:
        percentage = (count / total_fast) * 100 if total_fast > 0 else 0
        
        # Determine status
        if layer == 'Unit':
            status = "✅" if percentage >= 65 else "❌"
        elif layer in ['Integration', 'E2E']:
            status = "✅" if percentage <= 10 else "❌"
        else:
            status = "📊"  # Neutral for other layers
        
        print(f"{layer:<15} {count:<8} {percentage:>8.1f}%    {target_range:<15} {status}")
    
    print("-" * 75)
    print(f"{'TOTAL (Fast)':<15} {total_fast:<8}")
    print(f"{'Slow Tests':<15} {composition.get('slow', 0):<8}")
    
    # Quality metrics
    print(f"\n🎯 QUALITY METRICS")
    unit_ratio = (composition.get('unit', 0) / total_fast) * 100 if total_fast > 0 else 0
    integration_e2e_ratio = ((composition.get('integration', 0) + composition.get('e2e', 0)) / total_fast) * 100 if total_fast > 0 else 0
    
    print(f"Unit-to-Total Ratio:     {unit_ratio:6.1f}% (target: ≥65%)")
    print(f"Integration+E2E Ratio:   {integration_e2e_ratio:6.1f}% (target: ≤10%)")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    if unit_ratio < 65:
        needed_unit_tests = int((total_fast * 0.65) - composition.get('unit', 0))
        print(f"• Add ~{needed_unit_tests} more unit tests to reach 65% ratio")
    
    if integration_e2e_ratio > 10:
        excess_tests = int((integration_e2e_ratio - 10) * total_fast / 100)
        print(f"• Consider converting {excess_tests} integration/E2E tests to unit tests")
    
    if composition.get('security', 0) < 5:
        print(f"• Add more security tests (current: {composition.get('security', 0)}, recommended: 5+)")
    
    if composition.get('perf', 0) < 5:
        print(f"• Add more performance tests (current: {composition.get('perf', 0)}, recommended: 5+)")

def suggest_nox_usage():
    """Suggest nox session usage for different scenarios."""
    
    print(f"\n🔧 NOX SESSION USAGE")
    print("-" * 40)
    print("Development Workflow:")
    print("  nox -s fast           # Fast development cycle (exclude slow tests)")
    print("  nox -s unit           # Unit tests only") 
    print("  nox -s component      # Component tests with mocks")
    print("  nox -s metrics        # Generate this analysis")
    print()
    print("CI/CD Pipeline:")
    print("  nox -s unit           # PR validation")
    print("  nox -s integration    # Scheduled/main branch")
    print("  nox -s perf           # Performance validation")
    print("  nox -s security_tests # Security validation")
    print("  nox -s chaos_tests    # Resilience testing")
    print()
    print("Full Testing:")
    print("  nox -s tests          # All tests (including slow)")

def main():
    """Main function."""
    composition = analyze_marker_composition()
    print_test_pyramid_analysis(composition)
    suggest_nox_usage()
    
    print(f"\n" + "=" * 80)

if __name__ == "__main__":
    main()