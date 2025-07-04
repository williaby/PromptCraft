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
