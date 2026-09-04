# Decision: Disable GitHub Automatic Dependency Submission (submit-pypi)

**Date:** 2026-05-25
**Status:** Active
**Context:** CI stabilization Stage 5

## Background

GitHub provides a built-in "Automatic Dependency Submission" feature for Python
repositories (Settings → Code security & analysis → Dependency graph → Automatic
dependency submission). When enabled, GitHub runs a system-managed workflow named
`submit-pypi` (path: `dynamic/dependency-graph/auto-submission`, triggered by
`github-advanced-security[bot]`) on every pull request. This workflow submits
dependency metadata to the GitHub Dependency Graph.

This workflow is not a YAML file in the repository; it cannot be disabled or
modified by adding or removing a file from `.github/workflows/`.

## Problem

The `submit-pypi` workflow was failing on every Renovate dependency PR with a
pip-compile resolution conflict:

- `poetry.lock` pins `cffi==1.17.1`
- `cryptography==46.0.7` requires `cffi>=2.0.0`
- pip-compile (used by submit-pypi) cannot resolve these constraints simultaneously
- Conclusion: `failure` on every PR from Renovate

Example failure: PR #315, run `26340020698`, job `77540266232`.

## Decision

Disable automatic dependency submission because:

1. **No identified consumer.** No downstream tool, compliance requirement, or
   integration consumes the GitHub Dependency Graph data submitted by this
   workflow.
2. **Persistent failures block PR review.** A failing required check on every
   Renovate PR degrades CI signal and increases manual triage overhead.
3. **Separate SBOM pipeline exists.** The `renovate-auto-merge.yml` workflow
   generates a CycloneDX SBOM via `pip-audit` for SLSA provenance attestation.
   This separate pipeline is unaffected by this decision.

## Actions Taken

### Required manual steps (repo owner only — cannot be done via code)

1. **GitHub UI:** Settings → Code security & analysis → Dependency graph →
   Automatic dependency submission → **Disable**
2. **GitHub UI:** Branch protection rules → remove `submit-pypi` from the
   required-status-checks list for `main`

### Repository code changes (this PR)

- No workflow YAML files were added or removed (the feature is GitHub-managed).
- Documented the cffi/cryptography pin conflict in `docs/known-vulnerabilities.md`
  under a "CI / Dependency-Resolution Conflicts" section for future tracking.
- This decision record created.

## Revisit Criteria

Re-enable automatic dependency submission and address the cffi conflict if any
of the following emerge:

- A documented SBOM consumer (downstream integration, compliance requirement,
  external auditor requesting GitHub Dependency Graph evidence).
- When re-enabling, bump the cffi pin in `pyproject.toml` to `^2.0.0` and
  validate compatibility with cryptography ≥46.0.7.

## References

- Failing job: <https://github.com/williaby/PromptCraft/actions/runs/26340020698>
- GitHub docs: Automatic dependency submission for Python repositories
- CI stabilization plan: docs/superpowers/plans/review-temp-cleanup-ci-stabilization-tea-temporal-harp.md
- Tracking issue: referenced in Stage 5 of CI stabilization plan
