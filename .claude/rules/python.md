# Python Rule

**Scope:** `src/**/*.py`, `tests/**/*.py`

## Overrides of Global

- **Line length: 120** (global default is 88). The project sets 120 in
  `pyproject.toml`; `.markdownlint.json` and `.yamllint.yml` mirror this.
- **Formatter:** Ruff format (replacing Black over time). Do not revert files
  to Black output when Ruff has already formatted them.
- **Type checker:** MyPy is currently wired into pre-commit. Migration to
  BasedPyright strict is planned per
  `docs/architecture/basedpyright-migration.md`; write new code in a way
  that passes both MyPy today and BasedPyright strict tomorrow.

## Required Practices

- All Python source and test files must pass `ruff check` and `ruff format
  --check` before commit.
- Bandit findings B101 and B601 are project-excluded (see `pyproject.toml`);
  any other Bandit finding must be fixed, not suppressed.
- Do not add `# noqa`, `# type: ignore`, or `pytest.mark.skip` as a shortcut
  past a real failure. If a suppression is genuinely needed, pair it with an
  issue link or explanation comment.

## Deep References

- `pyproject.toml` - primary configuration source.
- `docs/standards/linting.md` - full linting spec.
