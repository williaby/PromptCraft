"""Nox sessions for local development.

CI runs through the ByronWilliamsCPA/.github reusable workflows, which call
uv directly. These sessions mirror those checks for local use.
"""

import nox


nox.options.default_venv_backend = "uv"
nox.options.sessions = ["lint", "typecheck", "tests", "security"]

PYTHON_VERSIONS = ["3.11", "3.12", "3.13"]


def _sync(session: nox.Session, *groups: str) -> None:
    """Install the project and the given dependency groups from uv.lock."""
    args = ["uv", "sync", "--frozen", "--active"]
    for group in groups:
        args += ["--group", group]
    session.run_install(*args, env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location})


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite with coverage."""
    _sync(session, "dev")
    session.run("pytest", "--cov", "--cov-report=term-missing", "--cov-report=xml", *session.posargs)


@nox.session
def lint(session: nox.Session) -> None:
    """Check formatting and lint rules."""
    _sync(session, "dev")
    session.run("ruff", "format", "--check", ".")
    session.run("ruff", "check", ".")


@nox.session
def typecheck(session: nox.Session) -> None:
    """Run basedpyright in strict mode."""
    _sync(session, "dev")
    session.run("basedpyright")


@nox.session
def security(session: nox.Session) -> None:
    """Run bandit and pip-audit."""
    _sync(session, "dev")
    session.run("bandit", "-c", "pyproject.toml", "-lll", "-r", "src")
    session.run("pip-audit", "--skip-editable")


@nox.session
def docs(session: nox.Session) -> None:
    """Build the documentation site in strict mode."""
    _sync(session, "dev", "docs")
    session.run("mkdocs", "build", "--strict")


@nox.session(name="format")
def format_code(session: nox.Session) -> None:
    """Apply formatting and autofixable lint rules."""
    _sync(session, "dev")
    session.run("ruff", "format", ".")
    session.run("ruff", "check", "--fix", ".")
