# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |
| < 0.1   | No        |

## Reporting a Vulnerability

To report a vulnerability privately, use
[Private Vulnerability Reporting](https://github.com/williaby/PromptCraft/security/advisories/new). Do not open a
public issue.

We commit to acknowledging all vulnerability reports within 14 days of submission. Confirmed issues are fixed and
released as soon as practical, with credit to the reporter unless they ask otherwise.

Please include:

1. The type of issue and its impact.
2. The affected file, tag, branch, or commit.
3. Steps to reproduce, and proof-of-concept code if available.
4. Any configuration needed to reproduce it.

## Security Surface

| Surface | Risk | Mitigation |
| --- | --- | --- |
| User prompt text passed to the refiner | Prompt injection that changes refiner behavior | User content is passed in delimited data blocks; the golden set includes injection cases (ADR-001) |
| Engine endpoint configuration | Sending on-prem prompts to a remote service | `data_boundary: on_prem` restricts engines to loopback or allowlisted LAN hosts, pins resolved IPs, disables proxies and redirects (ADR-001) |
| Audit logs of original and refined prompts | Leaking sensitive prompt content | Logs are written to local sinks only; no telemetry |
| Dependencies | Vulnerable third-party packages | `uv.lock` pins versions; Renovate and pip-audit run continuously; see [known vulnerabilities](docs/known-vulnerabilities.md) |
| CI workflows | Supply-chain or script injection | Org reusable workflows pinned to commit SHAs; least-privilege permissions per job |

## Practices

- Dependencies are locked in `uv.lock` and updated by Renovate.
- Bandit, pip-audit, TruffleHog, and detect-secrets run in pre-commit and CI.
- basedpyright runs in strict mode.
- Unfixed vulnerabilities older than 60 days block a release; each is recorded in
  [docs/known-vulnerabilities.md](docs/known-vulnerabilities.md).
