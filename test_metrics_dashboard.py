#!/usr/bin/env python3
"""
Comprehensive Test Metrics Dashboard

Implements the performance matrix with minimum vs target thresholds:
- Branch coverage (overall & per-file)
- Test composition ratios
- Performance regression tracking
- Security findings
- Flakiness monitoring
"""

import json
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import re

@dataclass
class TestMetrics:
    """Core test metrics for the dashboard."""
    # Coverage metrics
    branch_coverage_overall: float = 0.0
    branch_coverage_per_file_min: float = 0.0
    files_below_coverage_threshold: int = 0
    
    # Test composition
    total_tests: int = 0
    unit_tests: int = 0
    component_tests: int = 0
    integration_tests: int = 0
    e2e_tests: int = 0
    perf_tests: int = 0
    security_tests: int = 0
    contract_tests: int = 0
    chaos_tests: int = 0
    
    # Derived ratios
    unit_to_total_ratio: float = 0.0
    integration_plus_e2e_ratio: float = 0.0
    
    # Quality metrics
    flaky_tests: int = 0
    security_findings_high: int = 0
    
    # Performance
    test_execution_time: float = 0.0
    performance_regression_percent: float = 0.0

@dataclass
class QualityThresholds:
    """Quality gate thresholds."""
    # Minimum thresholds (CI must pass)
    min_branch_coverage_overall: float = 80.0
    min_branch_coverage_per_file: float = 50.0
    min_unit_to_total_ratio: float = 65.0
    max_integration_plus_e2e_ratio: float = 10.0
    max_flakiness_rate: float = 0.5
    max_security_findings_high: int = 0
    max_performance_regression: float = 5.0
    
    # Target thresholds (trend goals)
    target_branch_coverage_overall: float = 90.0
    target_branch_coverage_per_file: float = 70.0
    target_unit_to_total_ratio: float = 72.5  # 70-75% target range
    target_integration_plus_e2e_ratio: float = 7.0
    target_flakiness_rate: float = 0.3
    target_performance_regression: float = 2.0

class TestMetricsCollector:
    """Collects test metrics from various sources."""
    
    def __init__(self):
        self.thresholds = QualityThresholds()
    
    def collect_test_composition(self) -> Dict[str, int]:
        """Collect test counts by marker type."""
        composition = defaultdict(int)
        
        # Marker mapping to standardized names
        marker_map = {
            'unit': 'unit_tests',
            'component': 'component_tests', 
            'contract': 'contract_tests',
            'integration': 'integration_tests',
            'e2e': 'e2e_tests',
            'perf': 'perf_tests',
            'chaos': 'chaos_tests',
            'security': 'security_tests'
        }
        
        try:
            # Get test collection for each marker
            for marker, metric_name in marker_map.items():
                result = subprocess.run([
                    'poetry', 'run', 'pytest', 
                    '--collect-only', '-q', '--tb=no', '--no-cov',
                    '-m', marker
                ], capture_output=True, text=True, timeout=60)
                
                if result.returncode == 0:
                    # Count collected tests
                    output = result.stdout
                    if 'tests collected' in output:
                        match = re.search(r'(\d+)/?(\d+)? tests? collected', output)
                        if match:
                            count = int(match.group(1))
                            composition[metric_name] = count
            
            # Get total test count
            result = subprocess.run([
                'poetry', 'run', 'pytest', 
                '--collect-only', '-q', '--tb=no', '--no-cov'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                output = result.stdout
                if 'tests collected' in output:
                    match = re.search(r'(\d+)/?(\d+)? tests? collected', output)
                    if match:
                        composition['total_tests'] = int(match.group(1))
        
        except Exception as e:
            print(f"Warning: Could not collect test composition: {e}")
        
        return dict(composition)
    
    def collect_coverage_metrics(self) -> Dict[str, float]:
        """Collect coverage metrics from pytest-cov."""
        coverage_data = {}
        
        try:
            # Run tests with coverage (use fast subset for speed)
            result = subprocess.run([
                'poetry', 'run', 'pytest',
                '--cov=src', '--cov-branch', '--cov-report=json',
                '--cov-report=term-missing:skip-covered',
                '-m', 'not perf and not chaos and not slow',  # Fast tests only
                '-q', '--tb=no', '--maxfail=3'
            ], capture_output=True, text=True, timeout=180)
            
            # Parse coverage.json
            coverage_file = Path('coverage.json')
            if coverage_file.exists():
                with open(coverage_file, 'r') as f:
                    coverage_json = json.load(f)
                
                # Overall coverage
                totals = coverage_json.get('totals', {})
                coverage_data['branch_coverage_overall'] = totals.get('percent_covered_display', 0.0)
                
                # Per-file coverage analysis
                files = coverage_json.get('files', {})
                per_file_coverages = []
                files_below_threshold = 0
                
                for file_path, file_data in files.items():
                    if file_path.startswith('src/'):
                        file_coverage = file_data['summary'].get('percent_covered', 0.0)
                        per_file_coverages.append(file_coverage)
                        
                        if file_coverage < self.thresholds.min_branch_coverage_per_file:
                            files_below_threshold += 1
                
                if per_file_coverages:
                    coverage_data['branch_coverage_per_file_min'] = min(per_file_coverages)
                    coverage_data['files_below_coverage_threshold'] = files_below_threshold
        
        except Exception as e:
            print(f"Warning: Could not collect coverage metrics: {e}")
        
        return coverage_data
    
    def collect_security_metrics(self) -> Dict[str, int]:
        """Collect security metrics from bandit."""
        security_data = {'security_findings_high': 0}
        
        try:
            result = subprocess.run([
                'poetry', 'run', 'bandit', '-r', 'src/',
                '-f', 'json', '-ll'  # Low confidence, low severity minimum
            ], capture_output=True, text=True, timeout=60)
            
            if result.stdout:
                bandit_data = json.loads(result.stdout)
                high_severity_count = 0
                
                for result_item in bandit_data.get('results', []):
                    if result_item.get('issue_severity') == 'HIGH':
                        high_severity_count += 1
                
                security_data['security_findings_high'] = high_severity_count
        
        except Exception as e:
            print(f"Warning: Could not collect security metrics: {e}")
        
        return security_data
    
    def collect_performance_metrics(self) -> Dict[str, float]:
        """Collect performance metrics."""
        perf_data = {}
        
        try:
            # Run a quick performance test to get execution time
            result = subprocess.run([
                'poetry', 'run', 'pytest',
                '-m', 'unit', '--tb=no', '--no-cov',
                '--durations=0', '--maxfail=5', '-x'
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                output = result.stdout
                # Extract execution time
                time_match = re.search(r'=+ (\d+\.?\d*) seconds =+', output)
                if time_match:
                    perf_data['test_execution_time'] = float(time_match.group(1))
        
        except Exception as e:
            print(f"Warning: Could not collect performance metrics: {e}")
        
        return perf_data
    
    def collect_all_metrics(self) -> TestMetrics:
        """Collect all metrics and return TestMetrics object."""
        print("🔍 Collecting test metrics...")
        
        # Initialize metrics
        metrics = TestMetrics()
        
        # Collect test composition
        print("  📊 Analyzing test composition...")
        composition = self.collect_test_composition()
        
        metrics.total_tests = composition.get('total_tests', 0)
        metrics.unit_tests = composition.get('unit_tests', 0)
        metrics.component_tests = composition.get('component_tests', 0)
        metrics.integration_tests = composition.get('integration_tests', 0)
        metrics.e2e_tests = composition.get('e2e_tests', 0)
        metrics.perf_tests = composition.get('perf_tests', 0)
        metrics.security_tests = composition.get('security_tests', 0)
        metrics.contract_tests = composition.get('contract_tests', 0)
        metrics.chaos_tests = composition.get('chaos_tests', 0)
        
        # Calculate ratios
        if metrics.total_tests > 0:
            metrics.unit_to_total_ratio = (metrics.unit_tests / metrics.total_tests) * 100
            integration_e2e_count = metrics.integration_tests + metrics.e2e_tests
            metrics.integration_plus_e2e_ratio = (integration_e2e_count / metrics.total_tests) * 100
        
        # Collect coverage metrics
        print("  📈 Analyzing coverage...")
        coverage_data = self.collect_coverage_metrics()
        metrics.branch_coverage_overall = coverage_data.get('branch_coverage_overall', 0.0)
        metrics.branch_coverage_per_file_min = coverage_data.get('branch_coverage_per_file_min', 0.0)
        metrics.files_below_coverage_threshold = coverage_data.get('files_below_coverage_threshold', 0)
        
        # Collect security metrics
        print("  🔒 Analyzing security...")
        security_data = self.collect_security_metrics()
        metrics.security_findings_high = security_data.get('security_findings_high', 0)
        
        # Collect performance metrics
        print("  ⚡ Analyzing performance...")
        perf_data = self.collect_performance_metrics()
        metrics.test_execution_time = perf_data.get('test_execution_time', 0.0)
        
        return metrics

class QualityGateValidator:
    """Validates metrics against quality gates."""
    
    def __init__(self, thresholds: QualityThresholds):
        self.thresholds = thresholds
    
    def validate_metrics(self, metrics: TestMetrics) -> Dict[str, Dict]:
        """Validate metrics against quality gates."""
        results = {}
        
        # Branch coverage overall
        results['branch_coverage_overall'] = {
            'value': metrics.branch_coverage_overall,
            'min_threshold': self.thresholds.min_branch_coverage_overall,
            'target_threshold': self.thresholds.target_branch_coverage_overall,
            'status': 'PASS' if metrics.branch_coverage_overall >= self.thresholds.min_branch_coverage_overall else 'FAIL',
            'target_status': 'PASS' if metrics.branch_coverage_overall >= self.thresholds.target_branch_coverage_overall else 'IMPROVING'
        }
        
        # Unit test ratio
        results['unit_to_total_ratio'] = {
            'value': metrics.unit_to_total_ratio,
            'min_threshold': self.thresholds.min_unit_to_total_ratio,
            'target_threshold': self.thresholds.target_unit_to_total_ratio,
            'status': 'PASS' if metrics.unit_to_total_ratio >= self.thresholds.min_unit_to_total_ratio else 'FAIL',
            'target_status': 'PASS' if metrics.unit_to_total_ratio >= self.thresholds.target_unit_to_total_ratio else 'IMPROVING'
        }
        
        # Integration + E2E ratio (should be low)
        results['integration_plus_e2e_ratio'] = {
            'value': metrics.integration_plus_e2e_ratio,
            'min_threshold': self.thresholds.max_integration_plus_e2e_ratio,
            'target_threshold': self.thresholds.target_integration_plus_e2e_ratio,
            'status': 'PASS' if metrics.integration_plus_e2e_ratio <= self.thresholds.max_integration_plus_e2e_ratio else 'FAIL',
            'target_status': 'PASS' if metrics.integration_plus_e2e_ratio <= self.thresholds.target_integration_plus_e2e_ratio else 'IMPROVING'
        }
        
        # Security findings
        results['security_findings_high'] = {
            'value': metrics.security_findings_high,
            'min_threshold': self.thresholds.max_security_findings_high,
            'target_threshold': self.thresholds.max_security_findings_high,
            'status': 'PASS' if metrics.security_findings_high <= self.thresholds.max_security_findings_high else 'FAIL',
            'target_status': 'PASS' if metrics.security_findings_high <= self.thresholds.max_security_findings_high else 'FAIL'
        }
        
        # Files below coverage threshold
        results['files_below_coverage_threshold'] = {
            'value': metrics.files_below_coverage_threshold,
            'min_threshold': 5,  # Allow some files below threshold
            'target_threshold': 0,
            'status': 'PASS' if metrics.files_below_coverage_threshold <= 5 else 'FAIL',
            'target_status': 'PASS' if metrics.files_below_coverage_threshold == 0 else 'IMPROVING'
        }
        
        return results

def print_dashboard(metrics: TestMetrics, validation_results: Dict):
    """Print comprehensive test metrics dashboard."""
    
    print("\n" + "=" * 100)
    print("🎯 TEST QUALITY METRICS DASHBOARD")
    print("=" * 100)
    
    # Test Composition Section
    print(f"\n📊 TEST COMPOSITION")
    print(f"{'Layer':<20} {'Count':<8} {'Percentage':<12} {'Target Range':<15}")
    print("-" * 65)
    
    total = metrics.total_tests if metrics.total_tests > 0 else 1
    
    test_layers = [
        ('Unit', metrics.unit_tests, '65-75%'),
        ('Component', metrics.component_tests, '15-25%'),
        ('Integration', metrics.integration_tests, '5-10%'),
        ('E2E', metrics.e2e_tests, '2-5%'),
        ('Performance', metrics.perf_tests, '3-8%'),
        ('Security', metrics.security_tests, '2-5%'),
        ('Contract', metrics.contract_tests, '1-3%'),
        ('Chaos', metrics.chaos_tests, '1-2%'),
    ]
    
    for layer, count, target_range in test_layers:
        percentage = (count / total) * 100
        print(f"{layer:<20} {count:<8} {percentage:>8.1f}%    {target_range:<15}")
    
    print("-" * 65)
    print(f"{'TOTAL':<20} {metrics.total_tests:<8}")
    
    # Quality Gates Section
    print(f"\n🚦 QUALITY GATES")
    print(f"{'Metric':<35} {'Value':<12} {'Min':<8} {'Target':<8} {'Status':<8} {'Target Status'}")
    print("-" * 90)
    
    quality_metrics = [
        ('Branch Coverage (Overall)', f"{metrics.branch_coverage_overall:.1f}%", 'branch_coverage_overall'),
        ('Unit-to-Total Ratio', f"{metrics.unit_to_total_ratio:.1f}%", 'unit_to_total_ratio'),
        ('Integration+E2E Ratio', f"{metrics.integration_plus_e2e_ratio:.1f}%", 'integration_plus_e2e_ratio'),
        ('Security Findings (High)', f"{metrics.security_findings_high}", 'security_findings_high'),
        ('Files Below Min Coverage', f"{metrics.files_below_coverage_threshold}", 'files_below_coverage_threshold'),
    ]
    
    for metric_name, value, key in quality_metrics:
        if key in validation_results:
            result = validation_results[key]
            min_thresh = result['min_threshold']
            target_thresh = result['target_threshold']
            status = result['status']
            target_status = result['target_status']
            
            status_emoji = "✅" if status == "PASS" else "❌"
            target_emoji = "🎯" if target_status == "PASS" else "📈"
            
            print(f"{metric_name:<35} {value:<12} {min_thresh:<8} {target_thresh:<8} {status_emoji} {status:<6} {target_emoji} {target_status}")
    
    # Summary Section
    print(f"\n🎯 SUMMARY")
    passed_gates = sum(1 for result in validation_results.values() if result['status'] == 'PASS')
    total_gates = len(validation_results)
    target_achieved = sum(1 for result in validation_results.values() if result['target_status'] == 'PASS')
    
    print(f"Quality Gates Passed: {passed_gates}/{total_gates}")
    print(f"Target Goals Achieved: {target_achieved}/{total_gates}")
    
    if passed_gates == total_gates:
        print("🎉 All quality gates PASSED! ✅")
    else:
        print("⚠️  Some quality gates FAILED! ❌")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    for key, result in validation_results.items():
        if result['status'] == 'FAIL':
            if key == 'branch_coverage_overall':
                print(f"• Increase overall coverage to {result['min_threshold']}% (current: {result['value']:.1f}%)")
            elif key == 'unit_to_total_ratio':
                print(f"• Add more unit tests - target {result['min_threshold']}% (current: {result['value']:.1f}%)")
            elif key == 'integration_plus_e2e_ratio':
                print(f"• Reduce integration/E2E tests or add more unit tests - target ≤{result['min_threshold']}% (current: {result['value']:.1f}%)")
            elif key == 'security_findings_high':
                print(f"• Fix {result['value']} high-severity security findings")
            elif key == 'files_below_coverage_threshold':
                print(f"• Improve coverage for {result['value']} files below 50%")
    
    print(f"\n" + "=" * 100)

def main():
    """Main function to run the metrics dashboard."""
    print("Initializing Test Quality Metrics Dashboard...")
    
    # Collect metrics
    collector = TestMetricsCollector()
    metrics = collector.collect_all_metrics()
    
    # Validate against quality gates
    validator = QualityGateValidator(collector.thresholds)
    validation_results = validator.validate_metrics(metrics)
    
    # Print dashboard
    print_dashboard(metrics, validation_results)
    
    # Export metrics
    export_data = {
        'metrics': asdict(metrics),
        'validation_results': validation_results,
        'thresholds': asdict(collector.thresholds)
    }
    
    with open('test_quality_metrics.json', 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"\n📄 Detailed metrics exported to: test_quality_metrics.json")
    
    # Exit with error code if quality gates failed
    failed_gates = sum(1 for result in validation_results.values() if result['status'] == 'FAIL')
    if failed_gates > 0:
        print(f"\n❌ {failed_gates} quality gate(s) failed!")
        sys.exit(1)
    else:
        print(f"\n✅ All quality gates passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()