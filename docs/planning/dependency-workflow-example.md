# Dependency Management Workflow Example

This document demonstrates the complete workflow for adding dependencies to PromptCraft-Hybrid, following our secure dependency management strategy (ADR-009).

## Example: Adding a New HTTP Client Library

### Scenario
Developer needs to add the `httpx` library for asynchronous HTTP requests in a new agent.

### Step-by-Step Process

#### 1. Check AssuredOSS Availability

```bash
# Search for httpx in AssuredOSS
poetry search httpx --source assured-oss

# Result: Package found in AssuredOSS with version 0.27.0
```

#### 2. Add the Dependency

```bash
# Add httpx with appropriate version constraint
poetry add "httpx>=0.27.0,<1.0.0"

# Poetry updates pyproject.toml and poetry.lock automatically
```

#### 3. Update Requirements Files

```bash
# Regenerate requirements files with hash verification
./scripts/generate_requirements.sh

# Output:
# 🔐 Generating requirements files WITH hashes (secure mode)
# 📦 Exporting requirements.txt using poetry export...
# 🔍 Validating main requirements...
# ✅ Hash validation passed for requirements.txt
# ✅ requirements.txt updated and validated.
# 📦 Exporting requirements-dev.txt using poetry export...
# 🔍 Validating dev requirements...
# ✅ Hash validation passed for requirements-dev.txt
# ✅ requirements-dev.txt updated and validated.
# 📦 Generating requirements-docker.txt (production only)...
# 🔍 Validating Docker requirements...
# ✅ Hash validation passed for requirements-docker.txt
# ✅ requirements-docker.txt updated and validated.
```

#### 4. Verify Changes

```bash
# Check what files were modified
git status

# Result:
# modified:   pyproject.toml
# modified:   poetry.lock
# modified:   requirements.txt
# modified:   requirements-dev.txt
# modified:   requirements-docker.txt
```

#### 5. Review Generated Requirements

```bash
# Check that httpx has hash verification
grep -A 2 "httpx==" requirements.txt

# Result:
# httpx==0.27.0 ; python_version >= "3.11" and python_version < "4.0" \
#     --hash=sha256:abc123... \
#     --hash=sha256:def456...
```

#### 6. Commit Changes

```bash
git add pyproject.toml poetry.lock requirements*.txt
git commit -m "feat(deps): add httpx for async HTTP client functionality

- Add httpx>=0.27.0,<1.0.0 for asynchronous HTTP requests
- Updated requirements files with hash verification
- Verified AssuredOSS compatibility
- Package classified as security-critical (HTTP library)

Closes #123"
```

### Renovate Bot Behavior

Since `httpx` is classified as a security-critical package, future updates will:

1. **Individual PRs**: Each httpx update gets its own PR (not batched)
2. **Immediate Processing**: Updates processed at any time (not monthly)
3. **Auto-merge Ready**: Labeled for automatic merging after CI passes
4. **High Priority**: Priority level 10 for fastest processing

### Security Implications

- **Hash Verification**: All httpx versions include SHA256 hashes
- **AssuredOSS Source**: Package comes from Google-vetted repository
- **Supply Chain Protection**: Hashes prevent tampering during download
- **Automatic Updates**: Security patches applied immediately via Renovate

## Example: Renovate PR for httpx Update

When a new version of httpx is released, Renovate will automatically:

### 1. Create Individual PR

```yaml
# Generated PR details
title: "chore(deps): update httpx to 0.27.1"
labels: ["security-critical", "automerge", "priority:high"]
body: |
  This PR updates httpx from 0.27.0 to 0.27.1
  
  ### Security Impact
  - Package classified as security-critical
  - Immediate processing (not batched)
  - Hash verification included
  
  ### Changes
  - pyproject.toml: httpx constraint remains ^0.27.0
  - poetry.lock: exact version updated to 0.27.1
  - requirements*.txt: regenerated with new hashes
```

### 2. Automated CI Processing

The renovate-auto-merge.yml workflow will:

1. **Authenticate to AssuredOSS** using Google Cloud service account
2. **Install dependencies** with Poetry
3. **Regenerate requirements** using our script with hash verification
4. **Run security scans** (pip-audit, OSV-scanner, Safety, Bandit)
5. **Execute tests** with minimum 80% coverage requirement
6. **Generate SLSA provenance** for supply chain verification
7. **Auto-approve and merge** if all checks pass

### 3. Hash Verification Process

```bash
# Old requirements.txt
httpx==0.27.0 \
    --hash=sha256:old123... \
    --hash=sha256:old456...

# New requirements.txt (auto-generated)
httpx==0.27.1 \
    --hash=sha256:new789... \
    --hash=sha256:new012...
```

## Troubleshooting Examples

### Issue: Package Not in AssuredOSS

```bash
# If special-package is not in AssuredOSS
poetry search special-package --source assured-oss
# Result: No packages found

# Solution: Use PyPI with extra caution
poetry add "special-package>=1.0.0,<2.0.0"
# Note: Document why AssuredOSS alternative wasn't available
```

### Issue: Hash Verification Failure

```bash
# Error during installation
pip install --require-hashes -r requirements.txt
# Error: Hash mismatch for package-name

# Solution: Regenerate requirements
./scripts/generate_requirements.sh
git add requirements*.txt
git commit -m "fix(deps): regenerate requirements with correct hashes"
```

### Issue: Dependency Conflict

```bash
# Poetry shows conflict
poetry add new-package
# Error: Conflicting dependencies

# Debug the conflict
poetry show --tree

# Solution: Update constraints
poetry add "conflicting-package>=compatible-version"
./scripts/generate_requirements.sh
```

## Best Practices Summary

1. **Always check AssuredOSS first** before adding any dependency
2. **Use appropriate version ranges** (not exact pins in pyproject.toml)
3. **Regenerate requirements immediately** after poetry changes
4. **Commit all related files together** (pyproject.toml, poetry.lock, requirements*.txt)
5. **Classify security implications** and document in commit message
6. **Test locally** before pushing changes
7. **Monitor Renovate PRs** for security-critical packages

This workflow ensures supply chain security while maintaining developer productivity and automation efficiency.