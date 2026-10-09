# Pre-Commit Rule

**Scope:** Before every commit.

## Gate Checklist

- [ ] `make pre-commit` (all hooks on all files) passes.
- [ ] Commit is signed (`git config user.signingkey` set).
- [ ] Commit message follows Conventional Commits; the commitizen commit-msg hook checks it.
- [ ] Test coverage stays at or above 80% line.
- [ ] No em-dashes in any text file; the `no-em-dash` hook enforces this.

## What Not To Do

- Do not bypass hooks with `--no-verify`.
- Do not suppress Semgrep, Bandit, SonarCloud, Qlty, or detect-secrets findings inline as the fix. If a finding is a
  genuine false positive, suppress it with a linked reason.
- Do not commit `.env` files or anything containing secrets.

## Deep Reference

`.pre-commit-config.yaml` and `pyproject.toml` are the sources of truth for what the gate runs.
