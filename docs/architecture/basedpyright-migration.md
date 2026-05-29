# BasedPyright Migration Plan

> **Status:** Planned | **Owner:** Unassigned | **Target window:** TBD
>
> The global standard at `~/.claude/CLAUDE.md` prescribes BasedPyright strict
> as the Python type checker. This project still uses MyPy via pre-commit.
> This doc plans the migration; it is not the migration itself.

## Current State

- Pre-commit runs MyPy with `--config-file=pyproject.toml`, excluding
  `tests/`, `scripts/`, `examples/`, `noxfile.py`.
- MyPy settings in `pyproject.toml` under `[tool.mypy]` include:
  `disallow_untyped_defs`, `disallow_incomplete_defs`, `warn_return_any`,
  `warn_unused_configs`, `namespace_packages`, `explicit_package_bases`.
- BasedPyright is not a project dependency.
- Line length override: project runs at 120 chars, not the global 88.

## Target State

- BasedPyright strict replaces MyPy as the pre-commit type checker.
- `pyproject.toml` gains a `[tool.basedpyright]` section with strict mode.
- MyPy hook removed once BasedPyright is clean across `src/`.

## Phases

### Phase 1: Install and baseline (no enforcement)

1. `uv add --group dev basedpyright`
2. Add `[tool.basedpyright]` section to `pyproject.toml`:

   ```toml
   [tool.basedpyright]
   include = ["src"]
   pythonVersion = "3.11"
   typeCheckingMode = "standard"  # not strict yet
   reportMissingTypeStubs = false
   ```

3. Run `uv run basedpyright src/` and redirect to
   `docs/architecture/basedpyright-baseline.txt`. Commit the baseline.
   (`docs/planning/` is gitignored; use a tracked location so the baseline
   can actually be reviewed.)

### Phase 2: Fix `standard` mode errors

1. Work through the baseline module by module.
2. Keep MyPy pre-commit hook active throughout; it is the gate until
   Phase 4.
3. Add a scheduled check (e.g., CI job running weekly) that runs
   BasedPyright against the codebase and posts the diff vs. baseline.

### Phase 3: Flip to strict mode

1. Change `typeCheckingMode = "strict"` in `pyproject.toml`.
2. Regenerate baseline; expect new findings from stricter rules
   (`reportUnknownMemberType`, `reportUnknownVariableType`,
   `reportMissingParameterType`, etc.).
3. Work through strict-mode findings. Triage aggressively: suppress with
   `# pyright: ignore[ruleName]` only when the finding is a known false
   positive tied to a third-party library gap; pair each suppression with
   an issue reference.

### Phase 4: Swap in pre-commit

1. Add BasedPyright hook to `.pre-commit-config.yaml`:

   ```yaml
   - id: basedpyright
     name: basedpyright
     entry: uv run basedpyright
     language: system
     types: [python]
     files: ^src/
     pass_filenames: false
   ```

2. Remove the MyPy hook in the same commit.
3. Update `.claude/rules/python.md` to state that BasedPyright strict is
   the canonical type checker.

## Risks and Mitigations

- **Large initial error count.** Start with `standard` mode, not `strict`.
- **Third-party libraries without types.** Use `reportMissingTypeStubs =
  false` and `reportMissingModuleSource = false` pragmatically; do not
  suppress errors on project code to work around third-party gaps.
- **CI cost.** BasedPyright is fast; additional CI time should be
  negligible. If it matters, scope to changed files in PR runs.

## Exit Criteria

- BasedPyright strict runs clean on `src/` in pre-commit.
- MyPy hook removed from `.pre-commit-config.yaml`.
- `[tool.mypy]` section removed from `pyproject.toml`.
- `.claude/rules/python.md` updated to reflect final state.

## References

- Global standard: `~/.claude/CLAUDE.md` "Core development standards".
- Project current config: `pyproject.toml`, `.pre-commit-config.yaml`.
- BasedPyright docs: <https://docs.basedpyright.com/>
