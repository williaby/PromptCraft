# Pre-Commit Rule

**Scope:** Before every commit.

## Gate Checklist

- [ ] `pre-commit run --all-files` passes.
- [ ] GPG key present (`gpg --list-secret-keys`) for `.env` encryption.
- [ ] SSH signing key present (`ssh-add -l`) and
      `git config user.signingkey` set.
- [ ] Ruff format and lint clean.
- [ ] Type checker (MyPy today, BasedPyright strict once migrated) passes.
- [ ] Bandit clean except the documented project-excluded rules.
- [ ] Test coverage at or above 80% line.
- [ ] No em-dashes introduced in any text file.
- [ ] No new `mcp__zen__*` tool references in project-owned files.

## What Not To Do

- Do not bypass hooks with `--no-verify`.
- Do not suppress Semgrep, Bandit, or SonarQube findings with inline
  ignores as the fix. Address the finding. If genuinely false-positive,
  suppress with a linked reason.
- Do not commit `.env` files or any file containing secrets.

## Deep Reference

`pyproject.toml` and `.pre-commit-config.yaml` are the sources of truth for
what the gate actually runs.
