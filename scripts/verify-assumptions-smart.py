#!/usr/bin/env python3
"""
Response-Aware Development (RAD) Verification Tool

Systematically verify code assumptions using tiered AI model routing:
- #CRITICAL: Premium models (Gemini 2.5 Pro, O3-Mini)
- #ASSUME: Dynamic free model selection (DeepSeek-R1, Qwen-Coder)
- #EDGE: Fast batch processing (Gemini Flash Lite)
"""

import argparse
from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Optional


@dataclass
class Assumption:
    """Represents a code assumption with metadata"""

    file_path: str
    line_number: int
    category: str  # CRITICAL, ASSUME, EDGE
    text: str


@dataclass
class AIVerificationResult:
    """Result from AI model verification"""

    assumption_id: str
    model_used: str
    status: str  # BLOCKING, REVIEW, NOTE
    confidence: float
    issues_found: list[str]
    suggested_fixes: list[str]
    defensive_patterns: list[str]
    verification_time: float
    cost_estimate: float
    context_lines: list[str]
    risk_level: str


@dataclass
class VerificationResult:
    """Results from AI model verification"""

    assumption: Assumption
    model_used: str
    status: str  # BLOCKING, REVIEW, NOTE
    issues_found: list[str]
    suggested_fixes: list[str]
    cost_estimate: float


class ArgumentParser:
    """Parse and validate command line arguments"""

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Verify code assumptions using tiered AI models",
        )
        self._setup_arguments()

    def _setup_arguments(self):
        self.parser.add_argument(
            "--strategy",
            choices=["tiered", "uniform", "critical-only"],
            default="tiered",
            help="Verification strategy (default: tiered)",
        )

        self.parser.add_argument(
            "--budget",
            choices=["premium", "balanced", "free-only"],
            default="balanced",
            help="Budget preference for model usage (default: balanced)",
        )

        self.parser.add_argument(
            "--scope",
            choices=["current-file", "changed-files", "all-files"],
            default="changed-files",
            help="Scope of files to analyze (default: changed-files)",
        )

        self.parser.add_argument(
            "--explain",
            action="store_true",
            help="Show model selection reasoning",
        )

        self.parser.add_argument(
            "--apply-fixes",
            choices=["auto", "review", "none"],
            default="review",
            help="How to handle suggested fixes (default: review)",
        )

        self.parser.add_argument(
            "--output-format",
            choices=["markdown", "json", "text"],
            default="markdown",
            help="Output format (default: markdown)",
        )


class FileCollector:
    """Collect files based on scope parameter"""

    def __init__(self, scope: str):
        self.scope = scope
        self.project_root = self._find_project_root()

    def _find_project_root(self) -> Path:
        """Find project root by looking for pyproject.toml or .git"""
        current = Path.cwd()
        while current != current.parent:
            if (current / "pyproject.toml").exists() or (current / ".git").exists():
                return current
            current = current.parent
        return Path.cwd()

    def collect_files(self) -> list[Path]:
        """Collect files based on scope"""
        if self.scope == "current-file":
            return self._get_current_file()
        if self.scope == "changed-files":
            return self._get_changed_files()
        if self.scope == "all-files":
            return self._get_all_source_files()
        raise ValueError(f"Unknown scope: {self.scope}")

    def _get_current_file(self) -> list[Path]:
        """Get current file from context or working directory"""
        # #ASSUME: current-file: Current context contains file information
        # #VERIFY: Add fallback to detect file from git or working directory
        current_file = os.environ.get("CURRENT_FILE")
        if current_file and Path(current_file).exists():
            return [Path(current_file)]
        return []

    def _get_changed_files(self) -> list[Path]:
        """Get files from git diff with robust fallback to full scan"""
        try:
            # Consolidated git command for efficiency and atomic failure
            git_command = ["git", "diff", "--name-only", "--cached", "HEAD"]

            result = subprocess.run(
                git_command,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                check=True,  # Raises CalledProcessError on non-zero exit codes
                encoding="utf-8",
            )

            # Process the output
            changed_paths = result.stdout.strip().split("\n")
            files = {path for path in changed_paths if path}  # Filter empty strings

            # Filter to existing source files
            source_files = []
            for file in files:
                file_path = self.project_root / file
                if file_path.exists() and self._is_source_file(file_path):
                    source_files.append(file_path)

            return source_files

        except FileNotFoundError:
            # Git command not found in PATH
            print("⚠️ Warning: 'git' command not found, falling back to full file scan", file=sys.stderr)
            return self._get_all_source_files()

        except subprocess.CalledProcessError as e:
            # Git command failed (not in repo, corrupted repo, etc.)
            print(
                f"⚠️ Warning: Git operation failed (exit code {e.returncode}), falling back to full scan",
                file=sys.stderr,
            )
            return self._get_all_source_files()

        except Exception as e:
            # Any other unexpected errors
            print(f"⚠️ Warning: Unexpected error during git processing: {e}, falling back to full scan", file=sys.stderr)
            return self._get_all_source_files()

    def _get_all_source_files(self) -> list[Path]:
        """Get all source files in project"""
        source_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cpp", ".c", ".h"}

        source_files = []
        for ext in source_extensions:
            source_files.extend(self.project_root.rglob(f"*{ext}"))

        # Filter out common ignored directories
        ignored_dirs = {"node_modules", "__pycache__", ".git", "dist", "build", ".pytest_cache"}

        return [f for f in source_files if not any(part in ignored_dirs for part in f.parts)]

    def _is_source_file(self, file_path: Path) -> bool:
        """Check if file is a source code file"""
        source_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".cpp", ".c", ".h"}
        return file_path.suffix in source_extensions


class AssumptionDetector:
    """Detect and categorize assumption tags in code"""

    def __init__(self):
        # Patterns for different assumption types
        self.patterns = {
            "CRITICAL": re.compile(r"#\s*CRITICAL:\s*([^:]+):\s*(.+)", re.IGNORECASE),
            "ASSUME": re.compile(r"#\s*ASSUME:\s*([^:]+):\s*(.+)", re.IGNORECASE),
            "EDGE": re.compile(r"#\s*EDGE:\s*([^:]+):\s*(.+)", re.IGNORECASE),
        }

        # Risk categorization
        self.risk_categories = {
            # Critical categories - production blockers
            "payment": "critical",
            "financial": "critical",
            "security": "critical",
            "auth": "critical",
            "authentication": "critical",
            "authorization": "critical",
            "concurrency": "critical",
            "race": "critical",
            "transaction": "critical",
            "database": "high",
            "timing": "high",
            # Standard categories
            "api": "medium",
            "state": "medium",
            "validation": "medium",
            "error": "medium",
            "network": "medium",
            # Edge categories
            "browser": "low",
            "performance": "low",
            "ui": "low",
            "display": "low",
        }

    def detect_assumptions(self, files: list[Path]) -> list[Assumption]:
        """Detect all assumption tags in provided files"""
        assumptions = []

        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    lines = f.readlines()

                for line_num, line in enumerate(lines, 1):
                    for category, pattern in self.patterns.items():
                        match = pattern.search(line)
                        if match:
                            subcategory = match.group(1).strip().lower()
                            assumption_text = match.group(2).strip()

                            # Get context lines
                            context = self._get_context_lines(lines, line_num - 1, 3)

                            # Determine risk level
                            risk_level = self._determine_risk_level(category, subcategory)

                            assumption = Assumption(
                                file_path=str(file_path),
                                line_number=line_num,
                                category=category,
                                text=f"{subcategory}: {assumption_text}",
                                context_lines=context,
                                risk_level=risk_level,
                            )
                            assumptions.append(assumption)

            except (OSError, UnicodeDecodeError) as e:
                print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
                continue

        return assumptions

    def _get_context_lines(self, lines: list[str], center_line: int, context_size: int = 3) -> list[str]:
        """Get surrounding context lines for an assumption"""
        start = max(0, center_line - context_size)
        end = min(len(lines), center_line + context_size + 1)
        return lines[start:end]

    def _determine_risk_level(self, category: str, subcategory: str) -> str:
        """Determine risk level based on category and subcategory"""
        if category == "CRITICAL":
            return "critical"
        if category == "EDGE":
            return "low"
        # ASSUME
        return self.risk_categories.get(subcategory, "medium")


class ModelSelector:
    """Select appropriate AI model based on assumption risk and budget"""

    def __init__(self, budget: str, strategy: str):
        self.budget = budget
        self.strategy = strategy

        # Model mappings by capability and cost
        self.models = {
            "critical": {
                "premium": ["gemini-2.5-pro", "openai/o3-mini"],
                "balanced": ["gemini-2.5-pro", "deepseek/deepseek-r1"],
                "free-only": ["deepseek/deepseek-r1", "qwen/qwen3-coder"],
            },
            "high": {
                "premium": ["gemini-2.5-pro"],
                "balanced": ["deepseek/deepseek-r1", "qwen/qwen-2.5-coder-32b-instruct:free"],
                "free-only": ["deepseek/deepseek-r1", "qwen/qwen-2.5-coder-32b-instruct:free"],
            },
            "medium": {
                "premium": ["gemini-2.5-flash"],
                "balanced": ["gemini-2.5-flash", "deepseek/deepseek-chat:free"],
                "free-only": ["deepseek/deepseek-chat:free", "qwen/qwen3-14b:free"],
            },
            "low": {
                "premium": ["gemini-2.0-flash-lite"],
                "balanced": ["gemini-2.0-flash-lite"],
                "free-only": ["gemini-2.0-flash-lite", "qwen/qwen3-14b:free"],
            },
        }

        # Specialized models for specific categories
        self.specialized = {
            "payment": "openai/o3-mini",
            "financial": "openai/o3-mini",
            "security": "gemini-2.5-pro",
            "auth": "gemini-2.5-pro",
            "concurrency": "deepseek/deepseek-r1",
            "database": "deepseek/deepseek-r1",
        }

    def select_model(self, assumption: Assumption) -> str:
        """Select best model for assumption verification"""
        # Check for specialized model first
        subcategory = assumption.text.split(":")[0].lower()
        if self.budget != "free-only" and subcategory in self.specialized:
            return self.specialized[subcategory]

        # Use risk-based selection
        risk_models = self.models.get(assumption.risk_level, self.models["medium"])
        available_models = risk_models.get(self.budget, risk_models["free-only"])

        # Return first available model (could be enhanced with load balancing)
        return available_models[0] if available_models else "gemini-2.0-flash-lite"


class VerificationReporter:
    """Generate comprehensive verification reports with actionable insights"""

    def __init__(self, format_type: str = "markdown"):
        self.format_type = format_type

    def generate_report(
        self,
        assumptions: list[Assumption],
        verification_results: list["AIVerificationResult"] | None = None,
        args: argparse.Namespace = None,
    ) -> str:
        """Generate comprehensive verification report"""

        if self.format_type == "markdown":
            return self._generate_markdown_report(assumptions, verification_results, args)
        if self.format_type == "json":
            return self._generate_json_report(assumptions, verification_results, args)
        return self._generate_text_report(assumptions, verification_results, args)

    def _generate_markdown_report(
        self,
        assumptions: list[Assumption],
        verification_results: list["AIVerificationResult"] | None,
        args: argparse.Namespace,
    ) -> str:
        """Generate detailed markdown report"""

        # Categorize assumptions
        critical = [a for a in assumptions if a.risk_level == "critical"]
        high = [a for a in assumptions if a.risk_level == "high"]
        medium = [a for a in assumptions if a.risk_level == "medium"]
        low = [a for a in assumptions if a.risk_level == "low"]

        # Calculate summary statistics
        total_files = len({a.file_path for a in assumptions})
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        report_lines = []

        # Header
        report_lines.extend(
            [
                "# Response-Aware Development (RAD) Verification Report",
                "",
                f"**Generated**: {timestamp}",
                f"**Files analyzed**: {total_files}",
                f"**Scope**: {args.scope if args else 'unknown'}",
                f"**Strategy**: {args.strategy if args else 'tiered'}",
                f"**Budget**: {args.budget if args else 'balanced'}",
                "",
            ],
        )

        # Executive Summary
        if assumptions:
            blocking_count = len([r for r in (verification_results or []) if r.status == "BLOCKING"])
            review_count = len([r for r in (verification_results or []) if r.status == "REVIEW"])

            report_lines.extend(
                [
                    "## Executive Summary",
                    "",
                    f"- **Total Assumptions Found**: {len(assumptions)}",
                    f"- **Critical Issues** (❌ Must fix): {len(critical)}",
                    f"- **High Priority** (⚠️ Should fix): {len(high)}",
                    f"- **Medium Priority** (💭 Review): {len(medium)}",
                    f"- **Edge Cases** (💡 Note): {len(low)}",
                    "",
                ],
            )

            if verification_results:
                report_lines.extend(
                    [
                        f"- **AI Verified**: {len(verification_results)} assumptions",
                        f"- **Blocking Issues**: {blocking_count}",
                        f"- **Review Required**: {review_count}",
                        "",
                    ],
                )
        else:
            report_lines.extend(
                [
                    "## No Assumptions Found",
                    "",
                    "Consider adding assumption tags to critical code paths:",
                    "",
                    "```javascript",
                    "// #ASSUME: api: Server response timeout handled gracefully",
                    "// #ASSUME: state: User session data assumed valid",
                    "// #EDGE: browser: Modern ES6+ features assumed available",
                    "```",
                    "",
                    "See: `/docs/response-aware-development.md` for complete guidance.",
                    "",
                ],
            )
            return "\n".join(report_lines)

        # Critical Issues Section
        if critical:
            report_lines.extend(
                [
                    "## ❌ Critical Issues (Must Fix Before Deploy)",
                    "",
                ],
            )

            for assumption in critical:
                file_name = Path(assumption.file_path).name
                report_lines.extend(
                    [
                        f"### {file_name}:{assumption.line_number}",
                        f"**Category**: {assumption.text}",
                        f"**Risk Level**: {assumption.risk_level}",
                        "",
                    ],
                )

                # Add AI verification results if available
                ai_result = self._find_ai_result(assumption, verification_results)
                if ai_result:
                    report_lines.extend(
                        [
                            f"**AI Analysis** ({ai_result.model_used}, confidence: {ai_result.confidence:.1%}):",
                            "",
                        ],
                    )

                    if ai_result.issues_found:
                        report_lines.append("**Issues Identified**:")
                        for issue in ai_result.issues_found:
                            report_lines.append(f"- {issue}")
                        report_lines.append("")

                    if ai_result.suggested_fixes:
                        report_lines.append("**Suggested Fixes**:")
                        for fix in ai_result.suggested_fixes:
                            report_lines.append(f"- {fix}")
                        report_lines.append("")

                # Show context
                report_lines.extend(
                    [
                        "**Code Context**:",
                        "```python",
                        *assumption.context_lines,
                        "```",
                        "",
                    ],
                )

        # High Priority Section (show top 5)
        if high:
            report_lines.extend(
                [
                    "## ⚠️ High Priority Issues (Should Fix Before PR)",
                    "",
                ],
            )

            for assumption in high[:5]:
                file_name = Path(assumption.file_path).name
                report_lines.extend(
                    [
                        f"**{file_name}:{assumption.line_number}** - {assumption.text}",
                        "",
                    ],
                )

                ai_result = self._find_ai_result(assumption, verification_results)
                if ai_result and ai_result.suggested_fixes:
                    report_lines.extend(
                        [
                            "**Quick Fixes**:",
                            f"- {ai_result.suggested_fixes[0] if ai_result.suggested_fixes else 'Add proper error handling'}",
                            "",
                        ],
                    )

            if len(high) > 5:
                report_lines.append(f"... and {len(high) - 5} more high priority issues\n")

        # Summary sections for medium and low
        if medium:
            report_lines.extend(
                [
                    f"## 💭 Medium Priority Issues: {len(medium)}",
                    "",
                    "Run with `--scope=all-files --strategy=tiered` for detailed analysis.",
                    "",
                ],
            )

        if low:
            report_lines.extend(
                [
                    f"## 💡 Edge Cases: {len(low)}",
                    "",
                    "These can be deferred to backlog for future improvement.",
                    "",
                ],
            )

        # Model Usage Section
        if verification_results and args and args.explain:
            report_lines.extend(
                [
                    "## 🤖 AI Model Usage",
                    "",
                ],
            )

            model_usage = {}
            total_cost = 0.0

            for result in verification_results:
                model = result.model_used
                model_usage[model] = model_usage.get(model, 0) + 1
                total_cost += result.cost_estimate

            for model, count in model_usage.items():
                report_lines.append(f"- **{model}**: {count} assumptions verified")

            report_lines.extend(
                [
                    f"- **Total Estimated Cost**: ${total_cost:.3f}",
                    "",
                ],
            )

        # Next Steps
        report_lines.extend(
            [
                "## Next Steps",
                "",
            ],
        )

        if critical:
            report_lines.append("1. **❌ URGENT**: Fix all critical assumptions immediately")

        if high:
            report_lines.append("2. **⚠️ HIGH**: Address high priority issues before PR")

        if args and args.apply_fixes != "none":
            report_lines.extend(
                [
                    "3. **🔧 AI VERIFICATION**: Get specific fixes from AI models:",
                    "   ```bash",
                    "   ./scripts/verify-assumptions-smart.sh --strategy=critical-only --budget=premium",
                    "   ```",
                ],
            )

        if args and args.scope != "all-files" and (medium or low):
            report_lines.extend(
                [
                    "4. **📊 FULL SCAN**: Analyze entire project:",
                    "   ```bash",
                    "   ./scripts/verify-assumptions-smart.sh --scope=all-files --budget=balanced",
                    "   ```",
                ],
            )

        report_lines.extend(
            [
                "5. **📚 LEARN**: See `/docs/response-aware-development.md` for RAD methodology",
                "",
            ],
        )

        # Footer
        report_lines.extend(
            [
                "---",
                "",
                "*Generated by Response-Aware Development (RAD) verification system*",
                "*Helping prevent production failures through systematic assumption analysis*",
            ],
        )

        return "\n".join(report_lines)

    def _generate_json_report(
        self,
        assumptions: list[Assumption],
        verification_results: list["AIVerificationResult"] | None,
        args: argparse.Namespace,
    ) -> str:
        """Generate JSON format report for programmatic processing"""

        report_data = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "scope": args.scope if args else None,
                "strategy": args.strategy if args else None,
                "budget": args.budget if args else None,
            },
            "summary": {
                "total_assumptions": len(assumptions),
                "critical_count": len([a for a in assumptions if a.risk_level == "critical"]),
                "high_count": len([a for a in assumptions if a.risk_level == "high"]),
                "medium_count": len([a for a in assumptions if a.risk_level == "medium"]),
                "low_count": len([a for a in assumptions if a.risk_level == "low"]),
            },
            "assumptions": [
                {
                    "file_path": a.file_path,
                    "line_number": a.line_number,
                    "category": a.category,
                    "text": a.text,
                    "risk_level": a.risk_level,
                }
                for a in assumptions
            ],
        }

        if verification_results:
            report_data["verification_results"] = [
                {
                    "assumption_id": r.assumption_id,
                    "model_used": r.model_used,
                    "status": r.status,
                    "confidence": r.confidence,
                    "issues_found": r.issues_found,
                    "suggested_fixes": r.suggested_fixes,
                    "cost_estimate": r.cost_estimate,
                }
                for r in verification_results
            ]

            report_data["summary"]["verified_count"] = len(verification_results)
            report_data["summary"]["blocking_count"] = len([r for r in verification_results if r.status == "BLOCKING"])

        return json.dumps(report_data, indent=2)

    def _generate_text_report(
        self,
        assumptions: list[Assumption],
        verification_results: list["AIVerificationResult"] | None,
        args: argparse.Namespace,
    ) -> str:
        """Generate simple text report for console output"""

        lines = []
        lines.append("RAD Verification Report")
        lines.append("=" * 50)
        lines.append("")

        if not assumptions:
            lines.append("No assumptions found.")
            return "\n".join(lines)

        critical = len([a for a in assumptions if a.risk_level == "critical"])
        high = len([a for a in assumptions if a.risk_level == "high"])
        medium = len([a for a in assumptions if a.risk_level == "medium"])
        low = len([a for a in assumptions if a.risk_level == "low"])

        lines.extend(
            [
                f"Total assumptions: {len(assumptions)}",
                f"Critical: {critical}, High: {high}, Medium: {medium}, Low: {low}",
                "",
            ],
        )

        if verification_results:
            blocking = len([r for r in verification_results if r.status == "BLOCKING"])
            review = len([r for r in verification_results if r.status == "REVIEW"])
            lines.extend(
                [
                    f"AI Verified: {len(verification_results)}",
                    f"Blocking: {blocking}, Review Required: {review}",
                    "",
                ],
            )

        return "\n".join(lines)

    def _find_ai_result(
        self,
        assumption: Assumption,
        verification_results: list["AIVerificationResult"] | None,
    ) -> Optional["AIVerificationResult"]:
        """Find AI verification result for a specific assumption"""
        if not verification_results:
            return None

        assumption_id = f"{assumption.file_path}:{assumption.line_number}"
        for result in verification_results:
            if result.assumption_id == assumption_id:
                return result
        return None


def main():
    """Main verification workflow"""
    # Parse arguments
    arg_parser = ArgumentParser()
    args = arg_parser.parser.parse_args()

    try:
        # Collect files
        collector = FileCollector(args.scope)
        files = collector.collect_files()

        # Detect assumptions
        detector = AssumptionDetector()
        assumptions = detector.detect_assumptions(files)

        # Generate and display report
        reporter = VerificationReporter(args.output_format if hasattr(args, "output_format") else "markdown")
        report = reporter.generate_report(assumptions, None, args)
        print(report)

        # Return appropriate exit code
        critical_count = len([a for a in assumptions if a.risk_level == "critical"])
        return 1 if critical_count > 0 else 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
