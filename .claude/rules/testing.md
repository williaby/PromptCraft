# Testing Rule

**Scope:** `tests/**`

## Structure

Tests are organized by type under `tests/`:

```text
tests/unit/            # Pure unit tests, no I/O
tests/integration/     # Component-to-component
tests/e2e/             # End-to-end journeys
tests/contract/        # API contract validation
tests/security/        # Security-focused tests
tests/performance/     # Perf and load
tests/auth/            # Auth-specific flows
tests/smoke/           # Fast pre-release checks
tests/base/, tests/core/  # Shared fixtures and core coverage
```

## Coverage Targets

- Line coverage **>= 80%** overall.
- Branch coverage **>= 70%**.
- Critical paths (auth, encryption, payment, external API boundaries)
  **>= 90%**.
- Patch coverage (new code in a PR) **>= 90%**.

## Required Practices

- Golden files in tests are source of truth; do not regenerate them to make a
  failing test pass without understanding why they drifted.
- Do not mock the real database in integration tests; use the configured test
  database fixture.
- New assertions must trace to a specific behavior or requirement, not "make
  the test pass."
- Prefer `pytest.mark.integration`, `pytest.mark.e2e`, etc. over ad-hoc
  `skipif` gating.

## Deep References

- `tests/conftest.py` - shared fixtures.
- `docs/standards/development-commands.md` - tiered test commands
  (`make test-fast`, `test-pr`, `test`).
