# Testing Rule

**Scope:** `tests/**`

## Structure

Tests live under `tests/`. Mark each test with one of the pytest markers defined in `pyproject.toml`: `unit`,
`integration`, `security`, `slow`. CI selects tests by marker.

## Coverage Targets

- Line coverage **>= 80%** overall (enforced by `fail_under` and the CI coverage threshold).
- Branch coverage **>= 70%**.
- Critical paths (on-prem data boundary guard, engine network calls) **>= 90%**.
- Patch coverage (new code in a PR) **>= 90%**.

## Required Practices

- Golden-set fixtures are the source of truth for refinement evaluation; do not regenerate them to make a failing
  test pass without understanding why they drifted.
- Tests never send real prompts to a remote model. Engine tests use a local stub server or recorded responses.
- New assertions trace to a specific behavior or requirement.
- Prefer markers over ad-hoc `skipif` gating.
