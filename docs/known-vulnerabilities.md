# Known Vulnerabilities

> **Purpose:** Track unfixed CVEs surfaced by `pip-audit`, Semgrep, Bandit, or
> upstream advisories. Every suppression or deferred fix must have an entry
> here. Required by the global OpenSSF baseline: **no vulnerability ages past
> 60 days without reassessment**. The release gate blocks any entry whose
> `first seen` date is more than 60 days old unless maintainers reassess
> the entry and record a new `reassessed` date (see Release Gate Rule
> below for the precise mechanics).

## How to Use

1. When `pip-audit` or another scanner reports a finding we cannot resolve
   immediately, add an entry below.
2. Record absolute dates, not relative ones ("first seen: 2026-04-19", not
   "last week").
3. Review this file at the start of each quarter and before every release.
4. Remove entries once the underlying CVE is fixed and the fix is deployed.

## Active Entries

_None._ Last `pip-audit` sweep on **2026-04-20** against the Poetry venv
(Python 3.11) reported: **No known vulnerabilities found**.

When you add or update dependencies, re-run:

```bash
PIPAPI_PYTHON_LOCATION="$(poetry env info --path)/bin/python" \
  poetry run pip-audit --format=columns
```

If findings appear, add entries using the template below.

## Entry Template

```markdown
### <CVE-YYYY-NNNNN> or <scanner>-<id>

- **Package / component:** `package-name==version`
- **Severity:** low | medium | high | critical
- **First seen:** YYYY-MM-DD
- **Reassessed:** YYYY-MM-DD (must be within 60 days of "first seen")
- **Planned fix by:** YYYY-MM-DD
- **Why deferred:** One or two sentences. Upstream has no patch; a workaround
  would break X; waiting on dependency Y to release.
- **Mitigation in place:** What we are doing now to reduce exposure
  (network isolation, config hardening, disabled feature, etc.).
- **Tracking issue:** Link to GitHub issue or ticket.
```

## Release Gate Rule

Any active entry with `first seen` older than 60 days (regardless of
`reassessed`) **blocks the next release** until either:

- The vulnerability is fixed and the entry is removed, or
- The entry is explicitly accepted by project maintainers with a new
  `reassessed` date and documented mitigation.

## CI / Dependency-Resolution Conflicts

These entries track dependency-resolution conflicts that affect CI tooling but
are not CVEs. They follow the same 60-day reassessment rule as active CVE
entries above.

### cffi-cryptography-pip-compile-conflict

- **Package / component:** `cffi==1.17.1` (poetry.lock pin) vs.
  `cryptography==46.0.7` (requires `cffi>=2.0.0`)
- **Severity:** low (CI-only; no runtime vulnerability)
- **First seen:** 2026-05-23
- **Reassessed:** 2026-05-25
- **Planned fix by:** 2026-07-25 (or when a SBOM consumer is identified)
- **Why deferred:** The conflict only affects GitHub's Automatic Dependency
  Submission (`submit-pypi`) workflow. That feature has been disabled because no
  consumer of the submitted SBOMs has been identified. Runtime behaviour is
  unaffected; Poetry resolves `cffi` and `cryptography` correctly at install
  time.
- **Mitigation in place:** GitHub Automatic Dependency Submission disabled via
  repo settings. SLSA SBOM generation via `pip-audit` in
  `renovate-auto-merge.yml` is unaffected and continues to run.
- **Tracking issue:** docs/architecture/disable-automatic-dependency-submission.md

## References

- Global standard: `~/.claude/CLAUDE.md` section "Unfixed CVEs".
- Scanner config: `pyproject.toml`, `.semgrep.yml`, `.pre-commit-config.yaml`.
- Security policy: [`SECURITY.md`](../SECURITY.md).
