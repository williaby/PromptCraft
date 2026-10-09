# Phase 0 Migration Plan: Archive, Tooling, and Standards Alignment

> **Status:** Proposed | **Date:** 2026-10-09 | **Parent:** `adr-001-portable-prompt-refiner.md`

Phase 0 turns the legacy repo into a clean, standards-compliant base for the new refiner. No new product code is
written in this phase.

## Reference: Org Reusable Workflows

- Source: `ByronWilliamsCPA/.github`, tag `v11.0.1`, commit `74cfc8e9d1ea1f6babc40bea102b3071af620942`.
- Pin form: `@<commit-sha> # vX.Y.Z`. Never `@main`. Pin the commit SHA, not the annotated tag object
  (`0c247cea...`). Renovate advances pins.
- The org docs lag the tags. README, `USAGE_EXAMPLES.md`, and `docs/workflows/*.md` still show `v7.0.1` and
  `workflow-templates/` shows `v10.1.9`. Some examples pass a `CODECOV_TOKEN` secret and `run-mypy` inputs that
  `python-ci.yml` no longer declares, which fails at startup. Copy inputs from the workflow file, not the docs.
- `CHANGELOG.md` `[Unreleased]` lists breaking changes (SARIF upload, CodeQL and dependency-review removal, FIPS
  `--pqc-mode`). Re-check before pinning a later tag.

## Consumer Contract (what the org workflows expect)

- **uv only.** The Python workflows that install the project (`python-ci.yml`, `python-precommit.yml`,
  `python-docs.yml`, `python-security-analysis.yml`, `python-sonarcloud.yml`) fail if `poetry.lock` or a
  `[tool.poetry...]` table exists (`python-ci.yml` around line 196). `python-reuse.yml` only checks licensing.
- **`uv.lock` committed.** `python-ci.yml` and `python-docs.yml` run `uv sync --all-extras --frozen`;
  `python-precommit.yml` runs `uv sync --frozen`. Dev tools must therefore install through the default dependency
  groups, which both commands include.
- **`pyproject.toml`**, PEP 621 `[project]`, plus:
  - `[tool.pytest.ini_options]` with `testpaths` and markers `unit`, `integration`, `security`, `slow`. CI selects
    `-m "unit or not (integration or security or slow)"`, then `-m integration` and `-m security` (exit code 5, no
    tests collected, is tolerated).
  - `[tool.bandit]` (run as `bandit -c pyproject.toml -lll`).
  - Optional `[tool.pip-audit] ignore-vuln`.
- **Dev tools reachable via uv:** ruff, basedpyright (not mypy), pytest, pytest-cov, coverage, bandit, pip-audit,
  pre-commit; mkdocs and interrogate if docs are built.
- **Layout:** `src/` and `tests/`.
- **`no-build`** defaults to `true`. An installable library needs `no-build: false`.
- **Python versions:** org supports 3.10 to 3.14, primary 3.12, PR tier 3.11 and 3.12. Set `requires-python` to match
  whatever matrix is enabled (current `>=3.11,<3.13` excludes 3.13).
- **Other files:** `.pre-commit-config.yaml`, `REUSE.toml` with `LICENSES/MIT.txt`, `mkdocs.yml` if docs are built,
  `qlty.toml` (Qlty is required), and a SonarCloud project (required).
- **nox:** no org workflow invokes nox. It is local developer tooling only.

## Steps

### Step 1: Tag the legacy code

Tag `main` as `legacy-hybrid-v0` and push the tag. All history and the working legacy tree stay reachable.

### Step 2: Compliance audit, report only

Run the `repo-compliance` skill in scheduled (report-only) mode. Record findings in this file's appendix. Triage each
finding as: fixed by the strip, fixed by Steps 4 to 5, or remediate in Step 6.

### Step 3: Strip legacy code

Remove:

- `src/` legacy modules (all current modules; the new package starts empty in Phase 1).
- `tests/` (145k lines; nearly all cover removed code) and `pytest_plugins/`.
- Gradio, Playwright, and UI assets: `playwright.config*.ts`, `playwright-report/`, `test-results/`, `package.json`.
- Tracked artifacts that `.gitignore` already excludes: `ab_testing.db`, `analytics.db`, `metrics.db`, `lint_env/`,
  `temp_cleanup/`, and the stray `src/core/vector_store.py\r` file.
- Deployment for the legacy app: `Dockerfile`, `docker-compose*.yml`/`.yaml`, `deployment/`,
  `requirements*.txt`.
- `.claude/commands/` and `.agents/` entries that target removed subsystems (Qdrant schema, function loading, agent
  skeletons). Keep knowledge-file validation commands.
- Stale docs that describe removed subsystems. Keep OpenSSF root files, `docs/standards/`, `docs/architecture/`, and
  `docs/known-vulnerabilities.md`.

Keep `knowledge/create_agent/` (input to the Phase 1 spec).

Update `CLAUDE.md` to describe the new scope, uv commands, and the removal of Poetry, Qdrant, Gradio, and Prefect
references.

### Step 4: Poetry to uv, nox, pre-commit

- **`pyproject.toml`:** PEP 621 static `[project]` dependencies, hatchling build backend, `[dependency-groups]` for dev
  tools, extras for optional features. Remove every `[tool.poetry...]` table and the Poetry source. Add the pytest,
  bandit, coverage, and basedpyright sections from the consumer contract. Drop mypy config.
- **Lockfile:** delete `poetry.lock`; generate and commit `uv.lock`.
- **`noxfile.py`:** replace the 21 Poetry sessions with a small set on uv (`tests`, `lint`, `typecheck`, `security`,
  `docs` if kept), using nox's uv backend or `uv sync` / `uv run`.
- **`Makefile`:** remove `POETRY := poetry`; targets call `uv run` or `nox`.
- **`.pre-commit-config.yaml`:** replace `poetry run` hooks with `uv run`; drop black (ruff format replaces it), the
  `poetry-check` and `poetry-lock` hooks, and mypy; add basedpyright and `uv-lock`.
- **`renovate.json`:** remove the Poetry manager; enable uv lock maintenance; copy the org rule (org `renovate.json`
  around line 70) that advances `ByronWilliamsCPA/.github` workflow pins.
- **`codecov.yaml`:** `after_n_builds: 2` assumes two uploads; set it to match the single `coverage-reports` upload.

### Step 5: CI on org reusable workflows

All callers pin `@74cfc8e9d1ea1f6babc40bea102b3071af620942 # v11.0.1`, set workflow-level `permissions: {}`, grant
per-job permissions, and include `merge_group:` if the merge queue is enabled.

#### Workflow map

| Current file | Action | Reason |
| --- | --- | --- |
| `ci.yml` | Replace with caller of `python-ci.yml` | Bespoke Poetry CI |
| `ci-gate.yml` | Delete after `CI Gate` is emitted by real job | Stub |
| `dependency-standards-validation.yml` | Delete after real check exists | Stub |
| `pr-validation.yml` | Replace with a copy of org `pr-validation.yml` | Poetry-based; org version is not `workflow_call`, so copy it |
| `security-analysis.yml` | Keep, re-pin to v11, re-enable bandit and osv, drop removed inputs | Pinned to an old SHA labeled `main` |
| `coverage.yml` | Replace with caller of `python-qlty-coverage.yml`, pinned | Uses `@main`; Qlty is required |
| `python-compatibility.yml` | Delete | `ci.yml` sets `enable-matrix-testing: true` with 3.11 to 3.14 |
| `container-security.yml` | Delete | Calls `williaby/.github@main`; no container after strip |
| `reuse.yml` | Replace with caller of `python-reuse.yml` | Bespoke |
| `scorecard.yml` | Replace with caller of `python-scorecard.yml` | Bespoke, unpinned harden-runner |
| `docs.yml` | Replace with caller of `python-docs.yml` | Docs site is kept |
| `deploy-docs.yml`, `deploy-docs-production.yml` | Delete | Poetry; duplicates docs |
| `codeql.yml`, `dependency-review.yml` | Delete | Removed org-wide |
| `fips-compatibility.yml` | Delete | Not needed for this library |
| `renovate-auto-merge.yml` | Delete | Poetry; use Renovate automerge |
| `security-scan-summary.yml` | Delete | Depends on removed workflows |
| `setup-assured-oss.yml` | Delete | Poetry plus GCP Assured OSS, unused |
| `codespaces-prebuild.yml` | Delete | Poetry devcontainer |
| `ui-testing-pipeline.yml` | Delete | Playwright for removed UI |

#### Target caller set

| Caller | Calls | Check names produced |
| --- | --- | --- |
| `ci.yml` (`name: CI`) | `python-ci.yml` with `python-version: '3.12'`, `enable-matrix-testing: true`, `python-versions-comprehensive` 3.11 to 3.14, `no-build: false`, `coverage-threshold` | `ci / CI Gate`, plus wrapper job **`CI Gate`** |
| `pr-validation.yml` | Copied from org | **`Dependency & Standards Validation`**, `PR Title Format`, `PR Body Non-Empty`, `PR Validation Gate` |
| `security-analysis.yml` | `python-security-analysis.yml` | `security / Security Gate Validation`, wrapper `Security Gate Validation` |
| `pre-commit.yml` | `python-precommit.yml` | `<job> / Pre-Commit Hooks` |
| `reuse.yml` | `python-reuse.yml` | `reuse / REUSE Compliance Check` |
| `scorecard.yml` | `python-scorecard.yml` | Scorecard |
| `codecov.yml` | `python-codecov.yml` (on `workflow_run` of `CI`) | Codecov upload |
| `sonarcloud.yml` (required) | `python-sonarcloud.yml` | SonarCloud analysis |
| `qlty.yml` (required) | `python-qlty-gate.yml`, job id `qlty-gate` | `qlty-gate / Qlty Gate` |
| `coverage.yml` | `python-qlty-coverage.yml` with `coverage-artifact-name: coverage-reports` | Qlty coverage upload |
| `docs.yml` | `python-docs.yml` | Docs build and Pages deploy |

The ruleset requires bare check names. Reusable workflow checks are named `<caller-job> / <job>`, so `ci.yml` adds a
wrapper job named `CI Gate` (`needs: [ci]`, `if: always()`, fails unless `needs.ci.result == 'success'`), following
the org's own "Security Gate Validation" wrapper pattern. The copied `pr-validation.yml` emits
`Dependency & Standards Validation` natively.

Starting a library with no tests trips the 80% coverage gate. Phase 0 sets `run-integration-tests: false` and
`run-security-tests: false` and lands a minimal package with a smoke test so the gate has something to measure.

#### Baselines and secrets

- Reset Codecov and SonarCloud baselines after the strip; the first PR will otherwise fail project-coverage deltas.
- Confirm secrets on `williaby/PromptCraft`: `CODECOV_TOKEN` (required for codecov), and as adopted `SONAR_TOKEN`,
  `QLTY_COVERAGE_TOKEN`, `SCORECARD_TOKEN`, `SNYK_TOKEN`, `ANTHROPIC_API_KEY`.

### Step 6: Compliance audit, remediate

Run the `repo-compliance` skill in interactive mode on the slim tree. Approve and apply remediations. Record accepted
exceptions in this file.

## Exit Criteria

- Org reusable workflows green on a PR.
- `CI Gate` and `Dependency & Standards Validation` produced by real jobs; stubs deleted.
- `repo-compliance` audit clean or with documented exceptions.
- No Poetry artifacts remain (`poetry.lock`, `[tool.poetry...]`, `poetry run`).

## Decisions

- **Org placement:** the repo stays under `williaby`. Both `williaby` and `ByronWilliamsCPA` repos can call the
  org reusable workflows; `williaby` does not enforce org-level rulesets. SonarCloud org and key stay as configured.
- **Required quality services:** Qlty and SonarCloud.
- **Docs site:** kept, built and deployed by `python-docs.yml`.
- **Releases:** no semantic-release. Adopt `python-release.yml` only if another system needs guaranteed versioning;
  the portal pins git tags, which are created manually.

## Risks and Open Items

- **Ruleset contexts unverified.** `williaby-default-branch-baseline` is not documented in the org repo. Confirm the
  exact required contexts (bare names or `ci / CI Gate`, and any others such as `Security Gate Validation` or
  `qlty-gate / Qlty Gate`) with `gh api repos/williaby/PromptCraft/rulesets` before deleting the stubs.
- **No org migration guide** exists for Poetry to uv or bespoke CI to the org stack; this plan serves as one and could
  be upstreamed.
- **Old pin** `c22009cc...` in current callers could not be verified against a release.

## Appendix: Compliance Audit Findings

To be filled in Step 2.
