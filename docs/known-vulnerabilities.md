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

### SNYK-INTEGRATION-UV-LOCK-PARSER

- **Package / component:** Snyk GitHub App integration (not a dependency CVE)
- **Severity:** low (integration error, not a vulnerability finding)
- **First seen:** 2026-05-25
- **Reassessed:** 2026-05-25
- **Planned fix by:** 2026-07-24
- **Why deferred:** Snyk's `snyk-python-plugin` does not yet fully parse
  `uv.lock` format. The project migrated from `poetry.lock` plus
  `requirements.txt` to `uv.lock` in PR #327. Snyk reports `state: error`
  (not a vulnerability `failure`) on the `security/snyk (williaby)` commit
  status with description "1 test has failed". This is a Snyk-side parser
  compatibility gap, not a real CVE finding. Snyk has publicly acknowledged
  uv support is in progress.
- **Mitigation in place:** All other dependency scanners pass: `pip-audit`
  via `uv run pip-audit` finds no vulnerabilities, Socket Security
  passes, CodeQL passes, GitGuardian passes, and the GitHub
  `dependency-review` action passes. The dependency surface is fully
  audited through these parallel tools.
- **Tracking issue:** Snyk dashboard PR check:
  <https://app.snyk.io/org/williaby/pr-checks/f2917475-de7b-429c-9860-23f2decd5f7e>.
  Human action required: file a Snyk support ticket or find the upstream
  snyk-python-plugin issue tracking uv.lock support, then add the link here.

## pip-audit Command (updated for uv)

When you add or update dependencies, re-run:

```bash
uv run pip-audit
```

Last `pip-audit` sweep on **2026-05-25** against the uv venv
(Python 3.11) reported: **No known vulnerabilities found**.

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

## References

- Global standard: `~/.claude/CLAUDE.md` section "Unfixed CVEs".
- Scanner config: `pyproject.toml`, `.semgrep.yml`, `.pre-commit-config.yaml`.
- Security policy: [`SECURITY.md`](../SECURITY.md).
