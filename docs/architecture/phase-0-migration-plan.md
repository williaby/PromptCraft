# Phase 0 Migration Plan: Archive, Tooling, and Standards Alignment

> **Status:** Proposed | **Date:** 2026-10-09 | **Parent:** `adr-001-portable-prompt-refiner.md`
>
> **Supersedes:** `docs/architecture/v1.4.0-alignment-backlog.md` (its "convert commands to skills" item and its Phase 2
> kickoff, which assume the legacy workbench), `docs/architecture/basedpyright-migration.md` (Phase 0 moves directly to
> basedpyright strict), and `docs/architecture/dynamic_loading_recommendations.md` (the dynamic function loading
> prototype is removed). The Phase 0 PR deletes these three files.

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
- **Python versions:** at v11.0.1 `python-ci.yml` defaults to primary 3.12, PR tier (`python-versions-pr`) 3.11 and
  3.12, and comprehensive tier (`python-versions-comprehensive`) 3.10 to 3.13. 3.14 is the maximum in the global Python
  standard (`requires-python = ">=3.10,<3.15"`), not a workflow default, so it comes from the caller input. Pull
  requests run only `python-versions-pr`: 3.13 and 3.14 run on push and schedule unless `ci.yml` also passes
  `python-versions-pr` including 3.13 and 3.14 (the Phase 0 CI change sets it). Set `requires-python` to match whatever
  matrix is enabled (current `>=3.11,<3.13` excludes 3.13).
- **Other files:** `.pre-commit-config.yaml`, `REUSE.toml` with `LICENSES/MIT.txt`, `mkdocs.yml` if docs are built,
  `qlty.toml` (Qlty is required), and a SonarCloud project (required).
- **nox:** no org workflow invokes nox. It is local developer tooling only.

## Steps

### Step 1: Tag the legacy code

Tag `main` as `legacy-hybrid-v0` and push the tag. All history and the working legacy tree stay reachable.

**Done (2026-10-09):** the session's git proxy rejected tag pushes (HTTP 403), so commit `fccc4eb` is preserved as
branch `archive/legacy-hybrid-v0`. Add the tag from a maintainer machine:
`git tag -a legacy-hybrid-v0 fccc4eb && git push origin legacy-hybrid-v0`.

The repo already has the annotated tag `legacy/pre-uv-migration` (commit `6533dbc`, 2026-05-25). Keep it:
`legacy-hybrid-v0` is a separate marker for the last tree before the strip.

### Step 2: Compliance audit, report only

Run the `repo-compliance` skill in scheduled (report-only) mode. Record findings in this file's appendix. Triage each
finding as: fixed by the strip, fixed by Steps 4 to 5, or remediate in Step 6.

### Step 3: Strip legacy code

Remove:

- `src/` legacy modules (all current modules; the new package starts empty in Phase 1).
- `tests/` (145k lines; nearly all cover removed code) and `pytest_plugins/`.
- Gradio, Playwright, and UI assets: `playwright.config*.ts`, `playwright-report/`, `test-results/`, `package.json`.
- Tracked artifacts that `.gitignore` already excludes (`*.db`, `temp*/`): `ab_testing.db`, `analytics.db`,
  `metrics.db`, `temp_cleanup/`.
- Tracked files with no ignore rule: `lint_env/` and the stray `src/core/vector_store.py\r` file. Delete both and add
  `lint_env/` to `.gitignore`.
- Deployment for the legacy app: `Dockerfile`, `docker-compose*.yml`/`.yaml`, `deployment/`,
  `requirements*.txt`.
- `.claude/commands/` and `.agents/` entries that target removed subsystems (Qdrant schema, function loading, agent
  skeletons). Delete them rather than convert them to skills, because the subsystems they serve are removed; this
  overrides the "convert, not delete" item in `v1.4.0-alignment-backlog.md`. Keep knowledge-file validation commands.
- Stale docs that describe removed subsystems. Keep OpenSSF root files, `docs/standards/`, `docs/architecture/`, and
  `docs/known-vulnerabilities.md`.
- `docs/planning/` references: `README.md` and `CONTRIBUTING.md` link the removed `docs/planning/ADR.md`; rewrite
  those links to point at `docs/architecture/`.

Keep `knowledge/create_agent/` (input to the Phase 1 spec).

Update `CLAUDE.md` to describe the new scope, uv commands, and the removal of Poetry, Qdrant, Gradio, Prefect, and
Azure AI references. Update `README.md`, `CONTRIBUTING.md`, and `.github/PULL_REQUEST_TEMPLATE.md` to the new scope and
uv commands.

Rebuild the `mkdocs.yml` nav against the docs that survive the strip, and add the ADR and this plan to it. The current
nav points at files that no longer exist (`planning/four-journeys.md`, `planning/ADR.md`, `planning/project_hub.md`,
`zen/README.md`, `CHANGELOG.md` under `docs/`), and `python-docs.yml` runs `mkdocs build --strict`, so a stale nav
fails the docs build. Verify with a local strict build before the PR.

### Step 4: Poetry to uv, nox, pre-commit

- **`pyproject.toml`:** PEP 621 static `[project]` dependencies, hatchling build backend, `[dependency-groups]` for dev
  tools, extras for optional features. Remove every `[tool.poetry...]` table and the Poetry source. Add the pytest,
  bandit, coverage, and basedpyright sections from the consumer contract. Drop mypy config.
- **Lockfile:** delete `poetry.lock`; generate and commit `uv.lock`.
- **`noxfile.py`:** replace the 26 Poetry sessions with a small set on uv (`tests`, `lint`, `typecheck`, `security`,
  `docs` if kept), using nox's uv backend or `uv sync` / `uv run`.
- **`Makefile`:** remove `POETRY := poetry`; targets call `uv run` or `nox`.
- **`.pre-commit-config.yaml`:** replace `poetry run` hooks with `uv run`; drop black (ruff format replaces it), the
  `poetry-check` and `poetry-lock` hooks, and mypy; add basedpyright and `uv-lock`.
- **`renovate.json`:** remove the Poetry manager; enable uv lock maintenance; copy the org rule (org `renovate.json`
  around line 70) that advances `ByronWilliamsCPA/.github` workflow pins. Set `automerge` and `platformAutomerge` to
  true for vulnerability alerts (keep the org severity ladder) and for `lockFileMaintenance`. Leave every other update
  manual.
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
| `reuse.yml` | Replace with caller of `python-reuse.yml` plus `Check REUSE Compliance` wrapper | Bespoke; ruleset needs the bare name |
| `scorecard.yml` | Replace with caller of `python-scorecard.yml` | Bespoke, unpinned harden-runner |
| `docs.yml` | Replace with caller of `python-docs.yml` | Docs site is kept |
| `deploy-docs.yml`, `deploy-docs-production.yml` | Delete | Poetry; duplicates docs |
| `codeql.yml`, `dependency-review.yml` | Delete | Removed org-wide |
| `fips-compatibility.yml` | Delete | Not needed for this library |
| `renovate-auto-merge.yml` | Delete | Poetry; Renovate automerge replaces merging; `sbom.yml` replaces its SBOM step |
| `security-scan-summary.yml` | Delete | Depends on removed workflows |
| `setup-assured-oss.yml` | Delete | Poetry plus GCP Assured OSS, unused |
| `codespaces-prebuild.yml` | Delete | Poetry devcontainer |
| `ui-testing-pipeline.yml` | Delete | Playwright for removed UI |

#### Target caller set

| Caller | Calls | Check names produced |
| --- | --- | --- |
| `ci.yml` (`name: CI`) | `python-ci.yml` with `python-version: '3.12'`, `enable-matrix-testing: true`, `python-versions-comprehensive` 3.11 to 3.14, `python-versions-pr` (include 3.13 and 3.14 for PR-time coverage), `no-build: false`, `coverage-threshold` | `ci / CI Gate`, plus wrapper job **`CI Gate`** |
| `pr-validation.yml` | Copied from org | **`Dependency & Standards Validation`** (a PR title and body gate only), `PR Title Format`, `PR Body Non-Empty`, `PR Validation Gate` |
| `security-analysis.yml` | `python-security-analysis.yml` | `security / Security Gate Validation`, wrapper `Security Gate Validation` |
| `pre-commit.yml` | `python-precommit.yml` | `<job> / Pre-Commit Hooks` |
| `reuse.yml` | `python-reuse.yml`, job id `reuse` | `reuse / REUSE Compliance Check`, plus wrapper job **`Check REUSE Compliance`** |
| `scorecard.yml` | `python-scorecard.yml` | Scorecard |
| `codecov.yml` | `python-codecov.yml` (on `workflow_run` of `CI`) | Codecov upload |
| `sonarcloud.yml` (required) | `python-sonarcloud.yml` | SonarCloud analysis |
| `qlty.yml` (required) | `python-qlty-gate.yml`, job id `qlty-gate` | `qlty-gate / Qlty Gate` |
| `coverage.yml` | `python-qlty-coverage.yml` with `coverage-artifact-name: coverage-reports` | Qlty coverage upload |
| `docs.yml` | `python-docs.yml` | Docs build and Pages deploy |
| `sbom.yml` | `python-sbom.yml` | CycloneDX SBOM, Grype and OSV scan, license check (artifacts) |

Ruleset `williaby-default-branch-baseline` (verified with `gh api repos/williaby/PromptCraft/rulesets`) requires four
bare contexts: `Security Gate Validation`, `Dependency & Standards Validation`, `Check REUSE Compliance`, and
`CI Gate`. Reusable workflow checks are named `<caller-job> / <job>`, so `ci.yml` adds a wrapper job named `CI Gate`
(`needs: [ci]`, `if: always()`, fails unless `needs.ci.result == 'success'`), following the org's own
"Security Gate Validation" wrapper pattern. `reuse.yml` adds the same kind of wrapper named `Check REUSE Compliance`
(`needs: [reuse]`, `if: always()`, fails unless `needs.reuse.result == 'success'`); without it the caller emits only
`reuse / REUSE Compliance Check` and the required context stays pending. The copied `pr-validation.yml` emits
`Dependency & Standards Validation` natively, but that job only aggregates the PR title and body checks; it validates
no dependencies or standards.

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
- All four ruleset-required contexts (`Security Gate Validation`, `Dependency & Standards Validation`,
  `Check REUSE Compliance`, `CI Gate`) produced by real jobs; stubs deleted.
- `mkdocs build --strict` passes against the rebuilt nav.
- `repo-compliance` audit clean or with documented exceptions.
- No Poetry artifacts remain in build, config, CI, and the files Step 3 updates (`poetry.lock`, `[tool.poetry...]`,
  `poetry run` in `Makefile`, `noxfile.py`, pre-commit, workflows, `CLAUDE.md`, `README.md`, `CONTRIBUTING.md`, the PR
  template). `docs/standards/*`, `.claude/rules/*`, and the kept architecture docs still mention Poetry commands; update
  them as follow-up work.

## Decisions

- **Org placement:** the repo stays under `williaby`. Both `williaby` and `ByronWilliamsCPA` repos can call the
  org reusable workflows; `williaby` does not enforce org-level rulesets. SonarCloud org and key stay as configured.
- **Required quality services:** Qlty and SonarCloud.
- **SonarCloud CI analysis returns.** Commit `00a0967` (2026-05-04) removed `sonarcloud.yml` in favor of Automatic
  Analysis. This plan reverses that decision: `sonarcloud.yml` calls `python-sonarcloud.yml`, and the owner disables
  Automatic Analysis for `williaby_PromptCraft` so the two do not double-report.
- **CodeQL and dependency-review are dropped deliberately.** The org removed them org-wide, citing paid GitHub Advanced
  Security, but the repo is public, so that rationale does not apply here. The drop is an owner decision.
  Dependency vulnerability coverage comes from Renovate alerts, `pip-audit`, OSV, Grype (via `sbom.yml`), and Snyk.
- **Renovate automerge:** enabled for vulnerability alerts (org severity ladder) and `lockFileMaintenance`; everything
  else stays manual.
- **SBOM:** `renovate-auto-merge.yml` was the only SBOM generator (CycloneDX via `pip-audit`, plus SLSA provenance)
  after `sbom.yml` was retired in `e3adbe1` (#290). Add an `sbom.yml` caller of `python-sbom.yml` pinned to
  `74cfc8e9d1ea1f6babc40bea102b3071af620942 # v11.0.1`. SLSA provenance is dropped with that workflow.
- **Scorecard override:** the org `python-scorecard.yml` publishes results as a workflow artifact only and ignores
  `publish-results`. Publishing to the public Scorecard API is not restored, so the public score stops updating. This is
  an explicit override of the Scorecard publishing the legacy `scorecard.yml` did.
- **Azure AI is dropped.** The engine is llama.cpp for the portal; hosted backends are deferred (see ADR-001 scope
  table). `CLAUDE.md` no longer lists Azure AI.
- **Docs site:** kept, built and deployed by `python-docs.yml`.
- **Releases:** no semantic-release. Adopt `python-release.yml` only if another system needs guaranteed versioning;
  the portal pins git tags, which are created manually.

## Risks and Open Items

- **Ruleset contexts verified.** `williaby-default-branch-baseline` requires four bare contexts:
  `Security Gate Validation`, `Dependency & Standards Validation`, `Check REUSE Compliance`, `CI Gate`. Qlty and
  SonarCloud are not ruleset-required, so their callers are not wrapped. Re-run
  `gh api repos/williaby/PromptCraft/rulesets` before deleting the stubs in case the ruleset changed.
- **No org migration guide** exists for Poetry to uv or bespoke CI to the org stack; this plan serves as one and could
  be upstreamed.
- **Old pin** `c22009cc...` in current callers is an untagged commit from 2026-04-14 and an ancestor of v11.0.1.

## Appendix: Compliance Audit Findings

To be filled in Step 2.
