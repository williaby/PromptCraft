# Contributing to PromptCraft

Thanks for helping. This file covers setup, the quality gates, and how changes get merged.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).

## Setup

1. Install [uv](https://docs.astral.sh/uv/).
2. Clone the repo and run:

   ```bash
   make setup
   ```

   This syncs the environment from `uv.lock` and installs the `pre-commit` and `commit-msg` git hooks.

## Quality Gates

Every change must pass the same gates CI runs:

| Gate | Command |
| --- | --- |
| Format and lint | `make lint` (ruff, 120-character lines) |
| Types | `make typecheck` (basedpyright strict) |
| Tests | `make test` (pytest, 80% line coverage minimum) |
| Security | `make security` (bandit, pip-audit) |
| Docs | `make docs` (mkdocs strict build) |
| All hooks | `make pre-commit` |

Do not bypass hooks with `--no-verify`, and do not add `# noqa`, `# type: ignore`, or skip markers to get past a real
failure. If a suppression is genuinely needed, add a comment that explains why.

## Dependencies

- Add runtime dependencies with `uv add <package>` and dev tools with `uv add --group dev <package>`.
- Commit the updated `uv.lock` in the same change.
- Renovate maintains versions afterward; do not hand-edit `uv.lock`.

## Branches and Commits

- Branch from `main` using a prefix: `feature/`, `fix/`, `docs/`, `refactor/`, `hotfix/`, `release/`.
- Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat`, `fix`, `docs`, `test`, `chore`,
  `refactor`, `security`, `build`, `ci`, `style`). The commit-msg hook checks this.
- Sign commits.
- Do not use em-dashes in any text; a pre-commit hook enforces this.

## Pull Requests

- Fill in the pull request template.
- CI must pass: the `CI Gate` and `Dependency & Standards Validation` checks are required, along with Qlty and
  SonarCloud.
- Keep each PR focused on one change.

## Security

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md). Do not open public issues for them.
