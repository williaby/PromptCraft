#!/usr/bin/env python3
"""
Security Gate Metrics Collection and Reporting

This script collects comprehensive metrics about security gate effectiveness, including:
- Security scan pass/fail rates
- Exception usage and false positive tracking
- Admin override frequency and patterns
- PR blocking statistics and developer impact
- Performance metrics and workflow disruption analysis
- Trend analysis and recommendations
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
import yaml

# Constants for magic numbers
MINOR_DISRUPTION_HOURS = 2
MODERATE_DISRUPTION_HOURS = 24
HIGH_ADMIN_OVERRIDE_THRESHOLD = 2
HIGH_EXCEPTION_THRESHOLD = 5
EXCELLENT_PASS_RATE_THRESHOLD = 95
LOW_BYPASS_EXCEPTION_THRESHOLD = 3
HIGH_FRICTION_THRESHOLD = 20
MODERATE_FRICTION_THRESHOLD = 10
REQUEST_TIMEOUT_SECONDS = 30


class SecurityMetricsCollector:
    """Collects and analyzes security gate metrics from GitHub."""

    def __init__(self) -> None:
        self.token = os.environ.get("GITHUB_TOKEN")
        if not self.token:
            print("Error: GITHUB_TOKEN environment variable not set")
            sys.exit(1)

        self.repo = os.environ.get("GITHUB_REPOSITORY", "williaby/PromptCraft")
        self.headers = {"Authorization": f"token {self.token}", "Accept": "application/vnd.github.v3+json"}
        self.base_url = "https://api.github.com"

    def _make_request(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        """Make a request to the GitHub API."""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
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
        except (requests.RequestException, KeyError) as e:
            print(f"Warning: Failed to get check runs for {ref}: {e}")
            return []

    def _load_exceptions(self) -> list[dict[str, Any]]:
        """Load security exceptions from the exceptions file."""
        exceptions_path = Path(".github/security-exceptions.yml")
        if not exceptions_path.exists():
            return []

        with exceptions_path.open() as f:
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

    def _analyze_false_positives(self, since: datetime) -> dict[str, Any]:
        """Analyze false positive patterns from exceptions and overrides."""
        false_positive_metrics = {
            "total_false_positives": 0,
            "by_tool": defaultdict(int),
            "by_rule": defaultdict(int),
            "resolution_time": [],
            "patterns": [],
        }

        # Analyze exceptions marked as false positives
        exceptions = self._load_exceptions()
        for exception in exceptions:
            if exception.get("type") == "false-positive":
                approved_date = exception.get("approved_date")
                if approved_date and datetime.fromisoformat(approved_date) > since:
                    false_positive_metrics["total_false_positives"] += 1
                    false_positive_metrics["by_tool"][exception.get("tool", "unknown")] += 1
                    false_positive_metrics["by_rule"][exception.get("rule", "unknown")] += 1

        # Analyze override commits for false positive mentions
        page = 1

        while True:
            params = {"since": since.isoformat(), "per_page": 100, "page": page}
            commits = self._make_request(f"/repos/{self.repo}/commits", params)

            if not commits:
                break

            for commit in commits:
                message = commit.get("commit", {}).get("message", "")
                if "false positive" in message.lower() or "SECURITY_OVERRIDE" in message:
                    false_positive_metrics["total_false_positives"] += 1
                    # Extract tool and rule information from commit message if possible

            page += 1

        return false_positive_metrics

    def _analyze_developer_impact(self, prs: list[dict[str, Any]]) -> dict[str, Any]:
        """Analyze developer workflow impact from security gates."""
        impact_metrics = {
            "average_pr_duration": 0,
            "blocked_pr_duration": 0,
            "security_fix_time": [],
            "developer_friction_score": 0,
            "workflow_disruption": {"minor": 0, "moderate": 0, "severe": 0},  # <2 hours  # 2-24 hours  # >24 hours
        }

        pr_durations = []
        blocked_pr_durations = []

        for pr in prs:
            if pr.get("created_at") and pr.get("merged_at"):
                created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                duration_hours = (merged - created).total_seconds() / 3600
                pr_durations.append(duration_hours)

                # Check if PR was blocked by security gates
                if self._was_pr_blocked_by_security(pr):
                    blocked_pr_durations.append(duration_hours)

                    # Categorize disruption level
                    if duration_hours < MINOR_DISRUPTION_HOURS:
                        impact_metrics["workflow_disruption"]["minor"] += 1
                    elif duration_hours < MODERATE_DISRUPTION_HOURS:
                        impact_metrics["workflow_disruption"]["moderate"] += 1
                    else:
                        impact_metrics["workflow_disruption"]["severe"] += 1

        if pr_durations:
            impact_metrics["average_pr_duration"] = sum(pr_durations) / len(pr_durations)

        if blocked_pr_durations:
            impact_metrics["blocked_pr_duration"] = sum(blocked_pr_durations) / len(blocked_pr_durations)
            impact_metrics["developer_friction_score"] = len(blocked_pr_durations) / len(prs) * 100

        return impact_metrics

    def _was_pr_blocked_by_security(self, pr: dict[str, Any]) -> bool:
        """Check if a PR was blocked by security gates."""
        # Check for security-gate-blocked label
        labels = [label.get("name", "") for label in pr.get("labels", [])]
        if "security-gate-blocked" in labels:
            return True

        # Check comments for security gate mentions
        try:
            comments = self._make_request(f"/repos/{self.repo}/issues/{pr['number']}/comments")
            for comment in comments:
                if "Security Gate Blocked" in comment.get("body", ""):
                    return True
        except (requests.RequestException, KeyError) as e:
            print(f"Warning: Failed to check for security blocks in PR #{pr['number']}: {e}")

        return False

    def _calculate_trend_analysis(self, current_metrics: dict, historical_data: list) -> dict[str, Any]:
        """Calculate trends and provide recommendations."""
        trends = {
            "false_positive_trend": "stable",
            "override_trend": "stable",
            "developer_impact_trend": "stable",
            "recommendations": [],
        }

        if not historical_data:
            return trends

        # Compare with historical averages
        historical_avg_fp = sum(m.get("false_positives", 0) for m in historical_data) / len(historical_data)
        historical_avg_overrides = sum(m.get("admin_overrides", 0) for m in historical_data) / len(historical_data)

        current_fp = current_metrics.get("false_positive_metrics", {}).get("total_false_positives", 0)
        current_overrides = current_metrics.get("admin_overrides", 0)

        # Trend analysis
        if current_fp > historical_avg_fp * 1.2:
            trends["false_positive_trend"] = "increasing"
            trends["recommendations"].append("Consider tuning security scan rules to reduce false positives")
        elif current_fp < historical_avg_fp * 0.8:
            trends["false_positive_trend"] = "decreasing"

        if current_overrides > historical_avg_overrides * 1.5:
            trends["override_trend"] = "increasing"
            trends["recommendations"].append("Review override usage patterns and provide additional training")
        elif current_overrides < historical_avg_overrides * 0.5:
            trends["override_trend"] = "decreasing"

        return trends

    def collect_metrics(self, days: int = 7) -> dict[str, Any]:
        """Collect security metrics for the past N days."""
        since = datetime.now(UTC) - timedelta(days=days)

        metrics = {
            "period": f"Last {days} days",
            "collection_date": datetime.now(UTC).isoformat(),
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

        # Analyze false positives
        print("Analyzing false positive patterns...")
        metrics["false_positive_metrics"] = self._analyze_false_positives(since)

        # Analyze developer impact
        print("Analyzing developer workflow impact...")
        metrics["developer_impact"] = self._analyze_developer_impact(prs)

        # Load historical data for trend analysis
        print("Calculating trends and recommendations...")
        historical_data = self._load_historical_metrics()
        metrics["trend_analysis"] = self._calculate_trend_analysis(metrics, historical_data)

        return metrics

    def _load_historical_metrics(self) -> list[dict]:
        """Load historical metrics for trend analysis."""
        metrics_dir = Path("security-metrics")
        if not metrics_dir.exists():
            return []

        historical_files = sorted(metrics_dir.glob("metrics-*.json"))[-30:]  # Last 30 reports
        historical_data = []

        for file_path in historical_files:
            try:
                with file_path.open() as f:
                    data = json.load(f)
                    historical_data.append(data)
            except Exception as e:
                print(f"Warning: Failed to load historical metrics from {file_path}: {e}")
                continue

        return historical_data

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
        if metrics["admin_overrides"] > HIGH_ADMIN_OVERRIDE_THRESHOLD:
            report += (
                "⚠️ **High Admin Override Usage**: Review override justifications and consider process improvements.\n\n"
            )

        if failure_count > success_count * 0.2:
            report += "⚠️ **High Failure Rate**: Consider additional developer training or tool tuning.\n\n"

        if metrics["exceptions_used"] > HIGH_EXCEPTION_THRESHOLD:
            report += "⚠️ **High Exception Usage**: Review exceptions for patterns and consider rule adjustments.\n\n"

        if pass_rate > EXCELLENT_PASS_RATE_THRESHOLD:
            report += "✅ **Excellent Pass Rate**: Security gates are working effectively with minimal friction.\n\n"

        if metrics["admin_overrides"] == 0 and metrics["exceptions_used"] < LOW_BYPASS_EXCEPTION_THRESHOLD:
            report += "✅ **Low Bypass Rate**: Teams are successfully working within security constraints.\n\n"

        # Add new sections for enhanced metrics
        report += self._generate_false_positive_section(metrics)
        report += self._generate_developer_impact_section(metrics)
        report += self._generate_trend_analysis_section(metrics)

        report += """## Next Steps

1. Review any admin overrides for compliance
2. Update expired security exceptions
3. Address high-failure security tools
4. Schedule security training if needed
5. Monitor false positive trends for rule tuning opportunities
6. Review developer impact metrics for workflow optimization

---
*This report was automatically generated by the enhanced security metrics collection system.*
"""

        return report

    def _generate_false_positive_section(self, metrics: dict[str, Any]) -> str:
        """Generate false positive analysis section."""
        fp_metrics = metrics.get("false_positive_metrics", {})

        section = f"""
## False Positive Analysis

### Summary
- **Total False Positives**: {fp_metrics.get('total_false_positives', 0)}
- **False Positive Rate**: {(fp_metrics.get('total_false_positives', 0) / max(metrics.get('total_prs', 1), 1) * 100):.1f}% of PRs affected

### By Security Tool
"""

        by_tool = fp_metrics.get("by_tool", {})
        if by_tool:
            for tool, count in sorted(by_tool.items(), key=lambda x: x[1], reverse=True):
                section += f"- **{tool}**: {count} false positives\n"
        else:
            section += "- No false positives detected in this period\n"

        section += """
### Recommendations
"""

        if fp_metrics.get("total_false_positives", 0) > metrics.get("total_prs", 0) * 0.1:
            section += "⚠️ **High False Positive Rate**: Consider tuning security scan rules\n"
        else:
            section += "✅ **Acceptable False Positive Rate**: Security tools are well-tuned\n"

        return section

    def _generate_developer_impact_section(self, metrics: dict[str, Any]) -> str:
        """Generate developer impact analysis section."""
        impact = metrics.get("developer_impact", {})

        section = f"""
## Developer Workflow Impact

### PR Processing Times
- **Average PR Duration**: {impact.get('average_pr_duration', 0):.1f} hours
- **Security-Blocked PR Duration**: {impact.get('blocked_pr_duration', 0):.1f} hours
- **Developer Friction Score**: {impact.get('developer_friction_score', 0):.1f}%

### Workflow Disruption Analysis
"""

        disruption = impact.get("workflow_disruption", {})
        total_disruptions = sum(disruption.values())

        if total_disruptions > 0:
            section += f"- **Minor Disruptions** (<2h): {disruption.get('minor', 0)} ({disruption.get('minor', 0)/total_disruptions*100:.1f}%)\n"
            section += f"- **Moderate Disruptions** (2-24h): {disruption.get('moderate', 0)} ({disruption.get('moderate', 0)/total_disruptions*100:.1f}%)\n"
            section += f"- **Severe Disruptions** (>24h): {disruption.get('severe', 0)} ({disruption.get('severe', 0)/total_disruptions*100:.1f}%)\n"
        else:
            section += "- No significant workflow disruptions detected\n"

        section += """
### Impact Assessment
"""

        if impact.get("developer_friction_score", 0) > HIGH_FRICTION_THRESHOLD:
            section += "⚠️ **High Developer Friction**: Consider process improvements\n"
        elif impact.get("developer_friction_score", 0) > MODERATE_FRICTION_THRESHOLD:
            section += "🔸 **Moderate Developer Friction**: Monitor for trends\n"
        else:
            section += "✅ **Low Developer Friction**: Security gates integrate well with workflow\n"

        return section

    def _generate_trend_analysis_section(self, metrics: dict[str, Any]) -> str:
        """Generate trend analysis and recommendations section."""
        trends = metrics.get("trend_analysis", {})

        section = f"""
## Trend Analysis & Strategic Recommendations

### Trend Summary
- **False Positive Trend**: {trends.get('false_positive_trend', 'unknown').title()}
- **Override Usage Trend**: {trends.get('override_trend', 'unknown').title()}
- **Developer Impact Trend**: {trends.get('developer_impact_trend', 'unknown').title()}

### Strategic Recommendations
"""

        recommendations = trends.get("recommendations", [])
        if recommendations:
            for rec in recommendations:
                section += f"- {rec}\n"
        else:
            section += "- Current security gate configuration appears optimal\n"
            section += "- Continue monitoring for emerging patterns\n"

        return section

    def save_metrics(self, metrics: dict[str, Any], output_dir: str = "security-metrics") -> None:
        """Save metrics data for historical tracking."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Save raw metrics as JSON
        timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
        metrics_file = f"{output_dir}/metrics-{timestamp}.json"

        with Path(metrics_file).open("w") as f:
            json.dump(metrics, f, indent=2, default=str)

        print(f"Metrics saved to: {metrics_file}")


def main() -> None:
    """Main entry point for the security metrics script."""

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
        with Path(args.output).open("w") as f:
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
