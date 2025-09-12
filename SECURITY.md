# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches
depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

Please report (suspected) security vulnerabilities to **<security@promptcraft.io>**. You will receive a response
from us within 48 hours. If the issue is confirmed, we will release a patch as soon as possible depending on
complexity but historically within a few days.

Please include the following in your report:

1. Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
2. Full paths of source file(s) related to the manifestation of the issue
3. The location of the affected source code (tag/branch/commit or direct URL)
4. Any special configuration required to reproduce the issue
5. Step-by-step instructions to reproduce the issue
6. Proof-of-concept or exploit code (if possible)
7. Impact of the issue, including how an attacker might exploit the issue

## Known Security Vulnerabilities

### PyTorch Dependencies (via sentence-transformers)

⚠️ **Critical Security Notice**: This project may include PyTorch 2.8.0 as a transitive dependency through
`sentence-transformers` when the ML features are enabled.

**Known Vulnerabilities (as of September 2025):**

1. **CVE-2025-2998** - Buffer Overflow (CVSS 8.2 - High)
   - **Component**: torch.nn.utils.rnn.pad_packed_sequence
   - **Impact**: Memory corruption through function state manipulation
   - **Status**: No fixed version available
   - **Exploit Maturity**: No known exploit

2. **CVE-2025-4287** - Improper Resource Shutdown (CVSS 6.8 - Medium)
   - **Component**: torch.cuda.nccl.reduce in torch/cuda/nccl.py
   - **Impact**: Application crash via local host manipulation
   - **Status**: Fix available in master branch, not yet published
   - **Exploit Maturity**: Proof of Concept available

3. **Additional CVEs**: CVE-2025-2999, CVE-2025-3000, CVE-2025-3001, CVE-2025-3121, CVE-2025-3136
   - **Severity**: Medium (CVSS 4.8-6.8)
   - **Impact**: Memory management issues, out-of-bounds writes
   - **Status**: No fixed versions available

### Mitigation Strategies

#### Option 1: Disable ML Features (Recommended for Production)

```bash
# Install without ML dependencies (no PyTorch)
poetry install

# ML features will gracefully fail with clear error messages
```

#### Option 2: Use ML Features with Accepted Risk

```bash
# Install with ML dependencies (includes PyTorch with known vulnerabilities)
poetry install --with ml

# Consider additional isolation measures:
# - Run in sandboxed containers
# - Limit network access for ML operations
# - Monitor for PyTorch security updates
```

### Risk Assessment

**Current Risk Level**: Medium-High for ML-enabled deployments, Low for standard deployments

**Attack Vectors**:
- Most vulnerabilities require local access
- No remote code execution (RCE) vulnerabilities identified
- Primarily denial-of-service and memory corruption issues

**Business Impact**:
- Standard deployments (without ML features): **No impact**
- ML-enabled deployments: **Service disruption possible**

### Monitoring and Updates

1. **Security Monitoring**: Track PyTorch security advisories at:
   - [PyTorch Security](https://pytorch.org/blog/tag/security/)
   - [CVE Database](https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=pytorch)

2. **Update Schedule**:
   - Check for PyTorch security updates monthly
   - Evaluate sentence-transformers alternatives quarterly
   - Re-assess risk tolerance bi-annually

3. **Alternative Libraries**: Consider migration to:
   - Hugging Face Transformers (with TensorFlow backend)
   - ONNX Runtime for inference
   - OpenAI embeddings API

## Security Best Practices

### Dependencies

- All dependencies are locked with specific versions in `poetry.lock`
- Requirements are exported with cryptographic hashes for pip verification
- Automated dependency updates via Renovate bot
- Daily security scanning in CI/CD pipeline
- **PyTorch vulnerabilities are temporarily accepted with documented risk**

### Code Security

- All code is scanned with Bandit for common security issues
- Secrets detection prevents accidental credential commits
- Type checking with mypy reduces runtime errors
- Comprehensive test coverage (>80%) for all critical paths

### Infrastructure

- All containers run as non-root users
- Minimal base images to reduce attack surface
- Network isolation between services
- Secrets managed via environment variables (never in code)

## Security Checklist for Contributors

Before submitting a PR:

- [ ] Run `nox -s security` to check for vulnerabilities
- [ ] Ensure no secrets are exposed in code or configuration
- [ ] Verify all user inputs are validated and sanitized
- [ ] Check that error messages don't leak sensitive information
- [ ] Confirm logging doesn't include PII or credentials
- [ ] Test with `pip install --require-hashes` to verify dependency integrity
