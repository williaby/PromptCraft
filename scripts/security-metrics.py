#!/usr/bin/env python3
"""
Security Gate Metrics Collection and Reporting

This script collects metrics about security gate effectiveness, including:
- Security scan pass/fail rates
- Exception usage
- Admin override frequency
- PR blocking statistics
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests
import yaml


class SecurityMetricsCollector:
    """Collects and analyzes security gate metrics from GitHub."""

    def __init__(self):
        self.token = os.environ.get("GITHUB_TOKEN")
        if not self.token:
            print("Error: GITHUB_TOKEN environment variable not set")
            sys.exit(1)

        self.repo = os.environ.get("GITHUB_REPOSITORY", "promptcraft-hybrid/PromptCraft")
        self.headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
        self.base_url = "https://api.github.com"

    def _make_request(self, endpoint: str, params: dict[str, Any] = None) -> Any:
        """Make a request to the GitHub API."""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def _get_pull_requests(self, since: datetime) -> list[dict[str, Any]]:
        """Get all pull requests since a given date."""
        prs = []
        page = 1

        while True:
            params = {"state": "all", "sort": "created", "direction": "desc", "per_page": 100, "page": page}

            batch = self._make_request(f"/repos/{self.repo}/pulls", params)

            if not batch:
                break

            for pr in batch:
                created_at = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                if created_at < since:
                    return prs
                prs.append(pr)

            page += 1

        return prs

    def _get_check_runs(self, ref: str) -> list[dict[str, Any]]:
        """Get check runs for a specific ref."""
        try:
            response = self._make_request(f"/repos/{self.repo}/commits/{ref}/check-runs")
            return response.get("check_runs", [])
        except:
            return []

    def _load_exceptions(self) -> list[dict[str, Any]]:
        """Load security exceptions from the exceptions file."""
        exceptions_path = Path(".github/security-exceptions.yml")
        if not exceptions_path.exists():
            return []

        with open(exceptions_path) as f:
            data = yaml.safe_load(f)

        return data.get("exceptions", [])

    def _count_admin_overrides(self, since: datetime) -> int:
        """Count admin overrides by searching for SECURITY_OVERRIDE commits."""
        override_count = 0
        page = 1

        while True:
            params = {"since": since.isoformat(), "per_page": 100, "page": page}

            commits = self._make_request(f"/repos/{self.repo}/commits", params)

            if not commits:
                break

            for commit in commits:
                if commit.get("commit", {}).get("message", "").startswith("SECURITY_OVERRIDE:"):
                    override_count += 1

            page += 1

        return override_count

    def collect_metrics(self, days: int = 7) -> dict[str, Any]:
        """Collect security metrics for the past N days."""
        since = datetime.now() - timedelta(days=days)

        metrics = {
            "period": f"Last {days} days",
            "collection_date": datetime.now().isoformat(),
            "repository": self.repo,
            "scan_results": defaultdict(lambda: defaultdict(int)),
            "exceptions_used": 0,
            "admin_overrides": 0,
            "blocked_prs": 0,
            "total_prs": 0,
            "security_tools": defaultdict(lambda: {"pass": 0, "fail": 0, "pending": 0}),
        }

        # Security check names we're tracking
        security_checks = ["CodeQL Analysis", "dependency-review", "PR Validation"]

        # Collect PR data
        print(f"Collecting PR data for the last {days} days...")
        prs = self._get_pull_requests(since)
        metrics["total_prs"] = len(prs)

        for pr in prs:
            if pr.get("head", {}).get("sha"):
                checks = self._get_check_runs(pr["head"]["sha"])

                pr_blocked = False
                for check in checks:
                    if check["name"] in security_checks:
                        status = check["conclusion"] or "pending"

                        # Map GitHub statuses to our categories
                        if status in ["success", "skipped"]:
                            metrics["security_tools"][check["name"]]["pass"] += 1
                            metrics["scan_results"]["all"]["success"] += 1
                        elif status in ["failure", "cancelled", "timed_out"]:
                            metrics["security_tools"][check["name"]]["fail"] += 1
                            metrics["scan_results"]["all"]["failure"] += 1
                            pr_blocked = True
                        else:
                            metrics["security_tools"][check["name"]]["pending"] += 1
                            metrics["scan_results"]["all"]["pending"] += 1

                if pr_blocked:
                    metrics["blocked_prs"] += 1

        # Check for exceptions used in the time period
        print("Checking security exceptions...")
        exceptions = self._load_exceptions()
        recent_exceptions = [
            e for e in exceptions if e.get("approved_date") and datetime.fromisoformat(e["approved_date"]) > since
        ]
        metrics["exceptions_used"] = len(recent_exceptions)

        # Count admin overrides
        print("Counting admin overrides...")
        metrics["admin_overrides"] = self._count_admin_overrides(since)

        return metrics

    def generate_report(self, metrics: dict[str, Any]) -> str:
        """Generate a markdown report from collected metrics."""
        total_scans = sum(metrics["scan_results"]["all"].values())
        success_count = metrics["scan_results"]["all"].get("success", 0)
        failure_count = metrics["scan_results"]["all"].get("failure", 0)
        pending_count = metrics["scan_results"]["all"].get("pending", 0)

        pass_rate = (success_count / total_scans * 100) if total_scans > 0 else 0
        block_rate = (metrics["blocked_prs"] / metrics["total_prs"] * 100) if metrics["total_prs"] > 0 else 0

        report = f"""# Security Gate Metrics Report

**Period**: {metrics['period']}
**Generated**: {datetime.fromisoformat(metrics['collection_date']).strftime('%Y-%m-%d %H:%M:%S')}
**Repository**: {metrics['repository']}

## Executive Summary

- **Total Pull Requests**: {metrics['total_prs']}
- **Security Scan Pass Rate**: {pass_rate:.1f}%
- **PRs Blocked by Security Gates**: {metrics['blocked_prs']} ({block_rate:.1f}%)
- **Security Exceptions Used**: {metrics['exceptions_used']}
- **Admin Overrides**: {metrics['admin_overrides']}

## Security Scan Results

### Overall Statistics

| Metric | Count | Percentage |
|--------|-------|------------|
| Total Security Scans | {total_scans} | 100.0% |
| Passed | {success_count} | {(success_count/total_scans*100) if total_scans > 0 else 0:.1f}% |
| Failed | {failure_count} | {(failure_count/total_scans*100) if total_scans > 0 else 0:.1f}% |
| Pending | {pending_count} | {(pending_count/total_scans*100) if total_scans > 0 else 0:.1f}% |

### Results by Security Tool

| Tool | Passed | Failed | Pending | Pass Rate |
|------|--------|--------|---------|-----------|
"""

        for tool, results in metrics["security_tools"].items():
            tool_total = sum(results.values())
            tool_pass_rate = (results["pass"] / tool_total * 100) if tool_total > 0 else 0
            report += (
                f"| {tool} | {results['pass']} | {results['fail']} | {results['pending']} | {tool_pass_rate:.1f}% |\n"
            )

        report += f"""
## Security Gate Effectiveness

- **PRs Reviewed**: {metrics['total_prs']}
- **PRs Blocked**: {metrics['blocked_prs']} ({block_rate:.1f}%)
- **Average Scans per PR**: {total_scans / metrics['total_prs'] if metrics['total_prs'] > 0 else 0:.1f}

## Exception and Override Usage

- **Security Exceptions Applied**: {metrics['exceptions_used']}
- **Admin Overrides Used**: {metrics['admin_overrides']}
- **Total Bypasses**: {metrics['exceptions_used'] + metrics['admin_overrides']}

## Recommendations

"""

        # Add recommendations based on metrics
        if metrics["admin_overrides"] > 2:
            report += (
                "⚠️ **High Admin Override Usage**: Review override justifications and consider process improvements.\n\n"
            )

        if failure_count > success_count * 0.2:
            report += "⚠️ **High Failure Rate**: Consider additional developer training or tool tuning.\n\n"

        if metrics["exceptions_used"] > 5:
            report += "⚠️ **High Exception Usage**: Review exceptions for patterns and consider rule adjustments.\n\n"

        if pass_rate > 95:
            report += "✅ **Excellent Pass Rate**: Security gates are working effectively with minimal friction.\n\n"

        if metrics["admin_overrides"] == 0 and metrics["exceptions_used"] < 3:
            report += "✅ **Low Bypass Rate**: Teams are successfully working within security constraints.\n\n"

        report += """## Next Steps

1. Review any admin overrides for compliance
2. Update expired security exceptions
3. Address high-failure security tools
4. Schedule security training if needed

---
*This report was automatically generated by the security metrics collection system.*
"""

        return report

    def save_metrics(self, metrics: dict[str, Any], output_dir: str = "security-metrics"):
        """Save metrics data for historical tracking."""
        os.makedirs(output_dir, exist_ok=True)

        # Save raw metrics as JSON
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        metrics_file = f"{output_dir}/metrics-{timestamp}.json"

        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2, default=str)

        print(f"Metrics saved to: {metrics_file}")


def main():
    """Main entry point for the security metrics script."""
    import argparse

    parser = argparse.ArgumentParser(description="Collect and report security gate metrics")
    parser.add_argument("--days", type=int, default=7, help="Number of days to analyze (default: 7)")
    parser.add_argument("--output", default="security-metrics-report.md", help="Output file for the report")
    parser.add_argument("--save-metrics", action="store_true", help="Save raw metrics data")

    args = parser.parse_args()

    # Collect metrics
    collector = SecurityMetricsCollector()
    print(f"Collecting security metrics for the last {args.days} days...")

    try:
        metrics = collector.collect_metrics(args.days)

        # Generate report
        report = collector.generate_report(metrics)

        # Save report
        with open(args.output, "w") as f:
            f.write(report)

        print(f"\nReport generated: {args.output}")

        # Optionally save raw metrics
        if args.save_metrics:
            collector.save_metrics(metrics)

        # Print summary
        print("\nSummary:")
        print(f"- Total PRs analyzed: {metrics['total_prs']}")
        print(f"- PRs blocked by security: {metrics['blocked_prs']}")
        print(f"- Admin overrides: {metrics['admin_overrides']}")
        print(f"- Exceptions used: {metrics['exceptions_used']}")

    except Exception as e:
        print(f"Error collecting metrics: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
