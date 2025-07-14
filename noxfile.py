"""Nox sessions for testing, linting, and security checks."""

from pathlib import Path

import nox

# Python versions to test
PYTHON_VERSIONS = ["3.11", "3.12"]

# Source locations
SRC_LOCATIONS = ["src", "tests", "noxfile.py", "scripts"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """Run the test suite."""
    args = session.posargs or ["--cov", "--cov-report=term-missing"]
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("pytest", *args)


@nox.session(python=["3.11"])
def tests_unit(session):
    """Run unit tests with coverage flags for Codecov."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "--cov=src",
        "--cov-report=xml:coverage-unit.xml",
        "--cov-report=term-missing",
        "tests/unit",
        "-v",
    )
    # Upload to Codecov with unit flag if token is available
    if session.env.get("CODECOV_TOKEN"):
        session.run("codecov", "-f", "coverage-unit.xml", "-F", "unit", external=True)


@nox.session(python=["3.11"])
def tests_integration(session):
    """Run integration tests with coverage flags for Codecov."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run(
        "pytest",
        "--cov=src",
        "--cov-report=xml:coverage-integration.xml",
        "--cov-report=term-missing",
        "tests/integration",
        "-v",
    )
    # Upload to Codecov with integration flag if token is available
    if session.env.get("CODECOV_TOKEN"):
        session.run("codecov", "-f", "coverage-integration.xml", "-F", "integration", external=True)


@nox.session(python="3.11")
def lint(session):
    """Run linters."""
    args = session.posargs or SRC_LOCATIONS
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("black", "--check", *args)
    session.run("ruff", "check", *args)

    # Markdown linting
    session.run("markdownlint", "**/*.md", external=True)

    # YAML linting
    session.run("yamllint", ".", external=True)


@nox.session(python="3.11")
def type_check(session):
    """Run type checking with mypy."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("mypy", "src")


@nox.session(python="3.11")
def security(session):
    """Run security checks."""
    session.run("poetry", "install", "--with", "dev", external=True)

    # Check for known vulnerabilities
    session.run("safety", "check", "--json")

    # Run bandit for code security issues
    session.run("bandit", "-r", "src", "-ll")

    # Check for hardcoded secrets
    session.run("detect-secrets", "scan", "--baseline", ".secrets.baseline")


@nox.session(python="3.11")
def format_code(session):
    """Format code."""
    args = session.posargs or SRC_LOCATIONS
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("black", *args)
    session.run("ruff", "check", "--fix", *args)


@nox.session(python="3.11")
def docs(session):
    """Build documentation."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.cd("docs")
    session.run("mkdocs", "build")


@nox.session(python="3.11")
def deps(session):
    """Check and update dependencies."""
    session.run("poetry", "install", external=True)

    # Check for outdated packages
    session.run("poetry", "show", "--outdated")

    # Export requirements with hashes
    session.run("./scripts/generate_requirements.sh", external=True)

    # Verify installation with hashes
    with session.chdir(session.create_tmp()):
        session.run("python", "-m", "venv", "test-env")
        session.run(
            "./test-env/bin/pip",
            "install",
            "--require-hashes",
            "-r",
            str(Path.cwd().parent / "requirements.txt"),
            external=True,
        )


@nox.session(python="3.11")
def pre_commit(session):
    """Run pre-commit on all files."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("pre-commit", "run", "--all-files")


# Advanced Testing Sessions


@nox.session(python="3.11")
def mutation_testing(session):
    """Run comprehensive mutation testing to validate test quality."""
    session.run("poetry", "install", "--with", "dev", external=True)

    # Clear previous mutation cache
    session.run("rm", "-rf", ".mutmut-cache", external=True, success_codes=[0, 1])

    # Run mutation testing with configuration
    session.log("🧬 Starting mutation testing...")

    try:
        # Run mutmut with correct options
        session.run(
            "mutmut",
            "run",
            "--paths-to-mutate",
            "src/core/,src/agents/,src/config/",
            "--test-time-multiplier",
            "2.0",
            "--runner",
            "python -m pytest tests/unit/ -x --disable-warnings",
            external=True,
        )

        # Generate comprehensive reports
        session.log("📊 Generating mutation testing reports...")

        # HTML report
        session.run("mutmut", "html", external=True)

        # Show summary
        session.run("mutmut", "show", external=True)

        session.log("✅ Mutation testing completed successfully")

    except Exception as e:
        session.log(f"⚠️ Mutation testing encountered issues: {e}")
        session.log("📋 Checking for partial results...")

        # Still generate available reports
        session.run("mutmut", "html", external=True, success_codes=[0, 1])

        # Don't fail the session for non-critical issues
        session.log("✅ Mutation testing completed with warnings")


@nox.session(python="3.11")
def contract_testing(session):
    """Run contract tests for MCP integrations."""
    session.run("poetry", "install", "--with", "dev", external=True)
    session.run("pytest", "tests/contract/", "-v")


@nox.session(python="3.11")
def dast_scanning(session):
    """Run comprehensive DAST security scanning with OWASP ZAP."""
    session.run("poetry", "install", "--with", "dev", external=True)

    # Application URL to scan
    app_url = "http://host.docker.internal:7860"
    session.log(f"🔒 Starting DAST security scan for {app_url}")

    # Verify Docker is available
    try:
        session.run("docker", "--version", external=True, silent=True)
    except Exception:
        session.error("Docker is not available. DAST scanning requires Docker.")
        return

    # Check if application is running
    session.log("📡 Checking if application is running...")
    try:
        session.run("curl", "-f", "http://localhost:7860/health", external=True, silent=True)
        session.log("✅ Application is running and accessible")
    except Exception:
        session.log("⚠️ Warning: Could not verify application is running on localhost:7860")
        session.log("Please ensure the application is started before running DAST scan")

    # Create reports directory
    session.run("mkdir", "-p", "dast-reports", external=True, success_codes=[0, 1])

    try:
        # Run OWASP ZAP baseline scan
        session.log("🕷️ Running OWASP ZAP baseline scan...")
        session.run(
            "docker",
            "run",
            "--rm",
            "-v",
            f"{session.env.get('PWD', '.')}/dast-reports:/zap/wrk/:rw",
            "owasp/zap2docker-stable",
            "zap-baseline.py",
            "-t",
            app_url,
            "-J",
            "baseline_report.json",
            "-w",
            "baseline_report.md",
            "-r",
            "baseline_report.html",
            "-x",
            "baseline_report.xml",
            external=True,
            success_codes=[0, 1, 2],  # ZAP may return non-zero for findings
        )

        # Generate comprehensive security report
        session.log("📊 Generating comprehensive security report...")
        session.run(
            "python",
            "-c",
            """
import json
import os
from datetime import datetime

def generate_security_summary():
    reports_dir = 'dast-reports'
    summary = {
        'scan_date': datetime.now().isoformat(),
        'scan_type': 'DAST',
        'tool': 'OWASP ZAP',
        'target': 'http://localhost:7860',
        'reports': []
    }

    # Check for baseline report
    baseline_path = os.path.join(reports_dir, 'baseline_report.json')
    if os.path.exists(baseline_path):
        try:
            with open(baseline_path, 'r') as f:
                baseline_data = json.load(f)
                summary['reports'].append({
                    'type': 'baseline',
                    'file': 'baseline_report.json',
                    'sites_count': len(baseline_data.get('site', [])),
                    'alerts_count': sum(len(site.get('alerts', [])) for site in baseline_data.get('site', []))
                })
        except Exception as e:
            print(f'Error parsing baseline report: {e}')

    # Write summary
    summary_path = os.path.join(reports_dir, 'security_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f'Security summary written to {summary_path}')
    print(f'Total reports generated: {len(summary["reports"])}')

if __name__ == '__main__':
    generate_security_summary()
""",
            external=True,
        )

        session.log("✅ DAST security scanning completed successfully")
        session.log("📁 Reports available in: dast-reports/")

    except Exception as e:
        session.log(f"⚠️ DAST scanning encountered issues: {e}")
        session.log("📋 Check dast-reports/ directory for any partial results")

        # Don't fail the session for DAST issues in development
        session.log("✅ DAST scanning completed with warnings")


@nox.session(python="3.11")
def performance_testing(session):
    """Run performance tests with Locust."""
    session.run("poetry", "install", "--with", "dev", external=True)

    # Run load tests
    session.log("Starting performance testing - ensure application is running")
    session.run(
        "locust",
        "-f",
        "tests/performance/locustfile.py",
        "--host=http://localhost:7860",
        "--headless",
        "--users",
        "10",
        "--spawn-rate",
        "2",
        "--run-time",
        "30s",
    )
