# Python Rule

**Scope:** `src/**/*.py`, `tests/**/*.py`

## Overrides of Global

- **Line length: 120** (global default is 88). Set in `pyproject.toml`; `.markdownlint.json` and `.yamllint.yml`
  mirror it.
- **Package manager:** uv. Run tools with `uv run --frozen <tool>`; add dependencies with `uv add`. Never edit
  `uv.lock` by hand.
- **Formatter and linter:** ruff (`ruff format`, `ruff check`).
- **Type checker:** basedpyright in strict mode.

## Required Practices

- All Python files pass `ruff format --check`, `ruff check`, and `basedpyright` before commit.
- Bandit findings B101 and B601 are excluded in `pyproject.toml`; fix any other Bandit finding.
- Do not add `# noqa`, `# type: ignore`, or `pytest.mark.skip` to get past a real failure. A genuinely needed
  suppression carries an explanation comment or issue link.

## Deep References

- `pyproject.toml`: tool configuration.
- `docs/architecture/adr-001-portable-prompt-refiner.md`: design constraints for library code.
