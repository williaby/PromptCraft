# Pre-Commit Rule

**Scope:** Before every commit.

## Gate Checklist

- [ ] `pre-commit run --all-files` passes.
- [ ] GPG key present (`gpg --list-secret-keys`) for `.env` encryption.
- [ ] SSH signing key present (`ssh-add -l`) and
      `git config user.signingkey` set.
- [ ] Configured Python hooks clean: Ruff format, Ruff check, Ruff datetime
      check, MyPy, Bandit. The Bandit suppressions in `pyproject.toml` (B101,
      B601) are the only acceptable exceptions.
- [ ] `uv-lock` hook passes (verifies `uv.lock` is in sync with
      `pyproject.toml`).
- [ ] Markdown and YAML lint clean (`markdownlint`, `yamllint`).
- [ ] Type checker (MyPy today, BasedPyright strict once migrated) passes.
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
