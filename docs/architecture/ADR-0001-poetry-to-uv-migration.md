# ADR-0001: Migrate Python Package Manager from Poetry to uv

- **Status**: Accepted
- **Date**: 2026-05-25
- **Deciders**: PromptCraft maintainers
- **Tags**: build, dependencies, ci, tooling

## Context

PromptCraft used Poetry as its Python package manager from project inception
through early 2026. The toolchain combined `poetry-core` as the build backend,
`poetry.lock` for reproducible installs, and a generated set of
`requirements*.txt` files (with hashes) consumed by Docker builds and external
scanners. CI installed Poetry on every job via `snok/install-poetry@v1` plus
`poetry-plugin-export`, then ran `poetry install --sync` against the lockfile.

Three pressures pushed the project off this stack:

1. **Bulk dependency hygiene.** A Snyk audit surfaced roughly 92 transitive
   CVEs that required coordinated upgrades across `cryptography`, `aiohttp`,
   `mako`, `orjson`, `python-multipart`, and their dependents. Poetry's
   resolver and its plugin-export step were slow enough that the retry-loop
   machinery in `.github/workflows/pr-validation.yml` had become permanent
   infrastructure, masking real failures and adding 4-7 minutes per cold CI
   run.
2. **Standards drift.** Poetry predates PEP 621 (`[project]` metadata) and
   PEP 735 (`[dependency-groups]`). New tooling (Renovate's group rules,
   pip-audit, `uv`, modern setup-action caching) targets the standard layout
   first; `[tool.poetry]` and `[tool.poetry.group.X.dependencies]` were
   becoming the awkward path.
3. **Plugin install fragility.** Every CI job paid the cost of installing
   Poetry plus `poetry-plugin-export` from PyPI. Outages and version skew on
   either side produced transient failures unrelated to the change under
   test.

`uv` (Astral) resolves and installs the same dependency set deterministically
in seconds, ships with PEP 621/735 support, integrates with
`astral-sh/setup-uv@v4` (which provides built-in caching keyed on `uv.lock`),
and removes the need for both `poetry-plugin-export` and the
`requirements*.txt` artifacts the project carried for Docker and scanning.

## Decision

Migrate the project's Python toolchain to uv in a single coordinated change:

- Replace the build backend `poetry-core` with `hatchling`.
- Adopt `uv` version `0.9.26` (pinned in `setup-uv` and in
  `.pre-commit-config.yaml`) as the package manager for local development,
  CI, Docker, and the devcontainer.
- Convert `pyproject.toml` from `[tool.poetry]` and
  `[tool.poetry.group.X.dependencies]` to PEP 621 `[project]` plus PEP 735
  `[dependency-groups]`.
- Make `uv.lock` the single authoritative lockfile. Delete `poetry.lock` and
  all tracked `requirements*.txt` snapshots. Generate `requirements.txt` on
  demand with `uv export --frozen --format requirements-txt` only when an
  external consumer needs one; do not commit the output.
- Wire pre-commit to `astral-sh/uv-pre-commit` (`uv-lock`) so the lockfile is
  verified in sync with `pyproject.toml` on every commit.
- Ship the migration as a single mega-PR (#327) rather than a phased
  rollout. The dependency graph and CI workflow set are too interlinked to
  cut over piecewise without leaving the repo in a half-built state.

## Consequences

### Positive

- **Deterministic installs.** `uv sync --frozen --all-groups` matches the
  resolved lockfile exactly; CI no longer needs retry loops to absorb
  resolver flakiness.
- **Faster cold CI.** `astral-sh/setup-uv@v4` provides a built-in cache keyed
  on `uv.lock`. Cold installs typically drop from minutes to seconds, and
  warm caches hit instantly.
- **Smaller CI surface.** No more `snok/install-poetry` step, no
  `poetry-plugin-export` install, no `requirements*.txt` regeneration step,
  no PR-validation retry block. The workflow files shrink and become easier
  to reason about.
- **Standardized metadata.** Project metadata now follows PEP 621 / 735, so
  Renovate group rules, IDE introspection, and external tooling read the
  project without Poetry-specific shims.
- **Consolidated configuration.** Build backend, dependency groups, lint
  config, and tooling versions all live in `pyproject.toml` alongside the
  authoritative `uv.lock`.

### Negative

- **Contributor onboarding cost.** Existing contributors need uv installed
  locally (a one-time `curl` install or `pipx install uv`). Documentation and
  the devcontainer have been updated to reflect this.
- **Open Renovate PRs need rebase.** Branches opened against the Poetry
  layout will not merge cleanly. Each open dependency PR must be rebased or
  regenerated against the new `pyproject.toml` and `uv.lock`.
- **First post-migration CI run is cold.** The setup-uv cache key changes
  (the lockfile filename and hash both change), so the first run after merge
  rebuilds the cache from scratch. Subsequent runs return to fast warm-cache
  behavior.
- **Supply-chain gating moves to pip-audit + OSV.** The AssuredOSS index
  used by the previous workflow is decommissioned in the same change.
  Supply-chain security now relies on `pip-audit`, the OSV scanner, and
  Renovate's vulnerability alerts. The `docs/known-vulnerabilities.md`
  60-day OpenSSF gate remains the backstop.

## Rollback Plan

If the migration produces a blocking regression in production, revert to the
Poetry baseline:

```bash
# Tag captured before the migration commits landed
git checkout legacy/pre-uv-migration   # signed tag at SHA 6533dbc

# Restore the Poetry environment
poetry install --sync
```

The `legacy/pre-uv-migration` tag is signed and retained for 90 days from
the merge date. After 90 days the tag is no longer guaranteed; reverting
beyond that window requires resurrecting `poetry.lock` and the
`requirements*.txt` artifacts from git history.

## References

- PR #327: poetry to uv mega-PR (this migration)
- Issue #316: uv migration tracking issue
- Issue #320: phantom file cleanup (cleared during stabilization)
- Issue #321: Python compatibility audit (3.11 / 3.12 matrix)
- Issue #322: FIPS workflow removal (no FIPS components in repo)
- Plan: `docs/superpowers/plans/review-temp-cleanup-ci-stabilization-tea-temporal-harp.md`
- PEP 621: Storing project metadata in `pyproject.toml`
- PEP 735: Dependency Groups in `pyproject.toml`
- uv documentation: <https://docs.astral.sh/uv/>
- Hatchling: <https://hatch.pypa.io/latest/>
