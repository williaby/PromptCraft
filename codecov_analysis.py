#!/usr/bin/env python3
"""
Codecov-enhanced coverage analysis by test type.
Leverages Codecov's flag system for comprehensive coverage insights.
"""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

class CodecovAnalyzer:
    """Enhanced coverage analysis using Codecov flags and local execution."""
    
    def __init__(self):
        self.codecov_token = os.getenv('CODECOV_TOKEN')
        self.project_root = Path.cwd()
        
    def run_flagged_tests(self, flag: str, description: str) -> Dict:
        """Run tests for specific flag and generate flagged coverage."""
        print(f"🔍 Running {description} tests with Codecov flag: {flag}")
        
        # Map flags to pytest markers
        flag_to_marker = {
            'unit': 'unit',
            'integration': 'integration', 
            'security': 'security',
            'fast': 'not slow',
            'performance': 'perf or performance',
            'stress': 'perf and stress',
            'contract': 'contract'
        }
        
        marker = flag_to_marker.get(flag, flag)
        
        try:
            # Run tests with coverage for this flag
            cmd = [
                'poetry', 'run', 'pytest',
                '-m', marker,
                '--cov=src',
                '--cov-branch',
                f'--cov-report=xml:coverage-{flag}.xml',
                '--cov-report=json',
                '--cov-report=term',
                '-q', '--tb=no',
                '--maxfail=5'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            
            # Parse results
            coverage_data = self._parse_coverage_json()
            test_count = self._extract_test_count(result.stdout + result.stderr)
            
            # Upload to Codecov if token available
            if self.codecov_token and Path(f'coverage-{flag}.xml').exists():
                self._upload_to_codecov(flag)
            
            return {
                'flag': flag,
                'description': description,
                'tests_run': test_count,
                'coverage_percentage': coverage_data.get('overall_coverage', 0.0),
                'statements_covered': coverage_data.get('statements_covered', 0),
                'total_statements': coverage_data.get('total_statements', 0),
                'files_analyzed': coverage_data.get('files_analyzed', 0),
                'coverage_file': f'coverage-{flag}.xml'
            }
            
        except Exception as e:
            print(f"    ⚠️ Error running {description}: {e}")
            return {
                'flag': flag,
                'description': description,
                'tests_run': 0,
                'coverage_percentage': 0.0,
                'statements_covered': 0,
                'total_statements': 0,
                'files_analyzed': 0,
                'error': str(e)
            }
    
    def _parse_coverage_json(self) -> Dict:
        """Parse coverage.json if it exists."""
        coverage_file = Path('coverage.json')
        if not coverage_file.exists():
            return {}
            
        try:
            with open(coverage_file, 'r') as f:
                data = json.load(f)
            
            totals = data.get('totals', {})
            return {
                'overall_coverage': totals.get('percent_covered_display', 0.0),
                'statements_covered': totals.get('covered_lines', 0),
                'total_statements': totals.get('num_statements', 0),
                'files_analyzed': len(data.get('files', {}))
            }
        except Exception as e:
            print(f"Error parsing coverage.json: {e}")
            return {}
    
    def _extract_test_count(self, output: str) -> int:
        """Extract test count from pytest output."""
        import re
        patterns = [
            r'(\d+) passed',
            r'= (\d+) passed',
            r'(\d+)/\d+ tests collected'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                return int(match.group(1))
        return 0
    
    def _upload_to_codecov(self, flag: str) -> None:
        """Upload coverage report to Codecov with flag."""
        try:
            cmd = [
                'codecov',
                '-f', f'coverage-{flag}.xml',
                '-F', flag,
                '-n', f'{flag}-coverage'
            ]
            
            if self.codecov_token:
                cmd.extend(['-t', self.codecov_token])
            
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"    ✅ Uploaded {flag} coverage to Codecov")
            
        except subprocess.CalledProcessError as e:
            print(f"    ⚠️ Failed to upload {flag} to Codecov: {e}")
        except Exception as e:
            print(f"    ⚠️ Error uploading {flag}: {e}")

def analyze_test_pyramid_with_codecov():
    """Comprehensive test pyramid analysis using Codecov flags."""
    
    print("📊 CODECOV-ENHANCED TEST ANALYSIS")
    print("=" * 80)
    
    analyzer = CodecovAnalyzer()
    
    # Test flags to analyze (matching codecov.yaml configuration)
    test_flags = [
        ('unit', 'Unit Tests (isolated, fast)'),
        ('integration', 'Integration Tests (cross-service)'),
        ('security', 'Security Tests (auth, validation)'),
        ('fast', 'Fast Development Cycle'),
        ('performance', 'Performance Tests'),
        ('contract', 'Contract Tests (MCP)'),
    ]
    
    results = {}
    
    # Run analysis for each flag
    for flag, description in test_flags:
        result = analyzer.run_flagged_tests(flag, description)
        results[flag] = result
        print()
    
    return results

def print_codecov_analysis(results: Dict):
    """Print comprehensive Codecov-based analysis."""
    
    print(f"\n📈 CODECOV FLAG ANALYSIS")
    print("-" * 90)
    print(f"{'Flag':<15} {'Tests':<8} {'Coverage':<10} {'Statements':<12} {'Files':<6} {'Efficiency'}")
    print("-" * 90)
    
    for flag, data in results.items():
        if 'error' in data:
            print(f"{flag:<15} {'ERROR':<8} {'N/A':<10} {'N/A':<12} {'N/A':<6} {'N/A'}")
            continue
            
        tests = data.get('tests_run', 0)
        coverage = data.get('coverage_percentage', 0.0)
        statements = data.get('statements_covered', 0)
        total_statements = data.get('total_statements', 0)
        files = data.get('files_analyzed', 0)
        
        # Coverage efficiency: coverage points per test
        efficiency = coverage / tests if tests > 0 else 0
        
        print(f"{flag:<15} {tests:<8} {coverage:>6.1f}%    {statements:>4}/{total_statements:<4}   {files:<6} {efficiency:>6.2f}")

def generate_codecov_insights(results: Dict):
    """Generate insights using Codecov data."""
    
    print(f"\n🎯 CODECOV INSIGHTS")
    print("-" * 60)
    
    unit_data = results.get('unit', {})
    integration_data = results.get('integration', {})
    fast_data = results.get('fast', {})
    
    # Test composition analysis
    unit_tests = unit_data.get('tests_run', 0)
    integration_tests = integration_data.get('tests_run', 0)
    total_fast = fast_data.get('tests_run', 0)
    
    if total_fast > 0:
        unit_ratio = (unit_tests / total_fast) * 100
        integration_ratio = (integration_tests / total_fast) * 100
        
        print(f"Test Composition (Fast Cycle):")
        print(f"  Unit Tests:       {unit_tests:4} ({unit_ratio:5.1f}%) [Target: 65-75%]")
        print(f"  Integration:      {integration_tests:4} ({integration_ratio:5.1f}%) [Target: 5-10%]")
        print(f"  Total Fast:       {total_fast:4}")
        
        # Health assessment
        if unit_ratio < 65:
            print(f"  ❌ INVERTED PYRAMID: Need ~{int((total_fast * 0.65) - unit_tests)} more unit tests")
        else:
            print(f"  ✅ HEALTHY PYRAMID: Good unit test ratio")
    
    # Coverage efficiency analysis
    print(f"\nCoverage Efficiency:")
    for flag, data in results.items():
        if 'error' not in data:
            tests = data.get('tests_run', 0)
            coverage = data.get('coverage_percentage', 0.0)
            if tests > 0:
                efficiency = coverage / tests
                status = "🎯" if efficiency > 5 else "⚠️" if efficiency > 2 else "❌"
                print(f"  {flag:12}: {efficiency:6.2f} coverage/test {status}")

def suggest_codecov_improvements(results: Dict):
    """Suggest improvements based on Codecov analysis."""
    
    print(f"\n💡 CODECOV-BASED RECOMMENDATIONS")
    print("-" * 60)
    
    unit_data = results.get('unit', {})
    integration_data = results.get('integration', {})
    
    unit_coverage = unit_data.get('coverage_percentage', 0)
    integration_coverage = integration_data.get('coverage_percentage', 0)
    
    print(f"Coverage Strategy:")
    if unit_coverage < 75:
        print(f"1. 🎯 Boost unit coverage from {unit_coverage:.1f}% to 75%+")
        print(f"   → Focus on src/core/, src/auth/, src/utils/")
    
    if integration_coverage < 60:
        print(f"2. 🔗 Improve integration coverage from {integration_coverage:.1f}% to 60%+")
        print(f"   → Focus on src/mcp_integration/, src/ui/")
    
    print(f"\nCodecov Workflow:")
    print(f"1. Use flags in CI: codecov -F unit -f coverage-unit.xml")
    print(f"2. Monitor component coverage in Codecov dashboard") 
    print(f"3. Set up branch protection rules based on flag coverage")
    print(f"4. Use Codecov's PR comments for flag-specific feedback")
    
    if results.get('unit', {}).get('coverage_file'):
        print(f"\n📁 Generated Coverage Files:")
        for flag, data in results.items():
            if data.get('coverage_file'):
                print(f"   {data['coverage_file']} (flag: {flag})")

def main():
    """Main function."""
    print("🚀 Starting Codecov-enhanced test analysis...")
    print("This leverages your existing codecov.yaml configuration.\n")
    
    results = analyze_test_pyramid_with_codecov()
    print_codecov_analysis(results)
    generate_codecov_insights(results)
    suggest_codecov_improvements(results)
    
    print(f"\n" + "=" * 90)
    print("📊 TIP: View detailed flag coverage at https://codecov.io/gh/YOUR_REPO")
    print("🔧 TIP: Use 'nox -s unit' for unit flag, 'nox -s integration' for integration flag")

if __name__ == "__main__":
    main()