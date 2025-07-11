# Security Gate Override Process

## Overview

This document outlines the process for overriding security gates in emergency situations. Admin overrides should be used sparingly and only when absolutely necessary.

## When to Use Admin Override

Admin override should **only** be used in the following emergency situations:

1. **Critical Production Hotfix**: When a critical bug in production needs immediate patching
2. **False Positive Blocking**: When a confirmed false positive cannot be resolved through the exception process in time
3. **Business Continuity Risk**: When delay would cause significant business impact
4. **Security Tool Malfunction**: When the security scanning tools themselves are broken

## Override Process

### Step 1: Document Justification

Before overriding, you **MUST** document the justification in your commit message:

```bash
git commit -m "SECURITY_OVERRIDE: [Brief reason]

Justification: [Detailed explanation of why override is necessary]
Risk Assessment: [What risks are we accepting by overriding]
Mitigation: [How will we address the security concern after merge]
Approver: @[admin-username]
Ticket: [Link to tracking issue]
Expires: [Date by which the security issue must be resolved]"
```

### Step 2: Create Tracking Issue

Create a GitHub issue to track the security debt:

```markdown
Title: Security Override: [Brief description]

## Override Details
- PR: #[PR number]
- Date: [Override date]
- Approver: @[admin-username]
- Security Tool: [Which check was overridden]

## Justification
[Copy from commit message]

## Resolution Plan
- [ ] Fix the underlying security issue
- [ ] Remove any temporary workarounds
- [ ] Verify security scans pass
- [ ] Update security exceptions if needed

## Deadline
Must be resolved by: [Date]
```

### Step 3: Execute Override

Use GitHub CLI with admin privileges:

```bash
# First, ensure you have admin rights
gh auth status

# Override and merge the PR
gh pr merge [PR-NUMBER] --admin --merge \
  --body "SECURITY_OVERRIDE: See commit message for justification"
```

### Step 4: Post-Override Actions

1. **Immediate Actions**:
   - Notify the security team via email
   - Post in #security-alerts channel
   - Add `security-override` label to the PR

2. **Within 24 Hours**:
   - Security team reviews the override
   - Risk assessment documented
   - Remediation plan approved

3. **Follow-up**:
   - Weekly check-ins until resolved
   - Escalation if deadline approaches

## Override Audit Trail

All overrides are tracked in multiple locations:

1. **GitHub Audit Log**: Permanent record of admin actions
2. **Commit History**: Override commits are specially marked
3. **Issue Tracker**: All overrides have tracking issues
4. **Security Metrics**: Weekly reports include override statistics

## Approval Matrix

| Scenario | Required Approver | Maximum Duration |
|----------|------------------|------------------|
| Critical hotfix | Engineering Manager | 48 hours |
| False positive | Security Team Lead | 1 week |
| Tool malfunction | DevOps Lead | Until fixed |
| Business continuity | Director level | 72 hours |

## Consequences of Misuse

Inappropriate use of security overrides may result in:

1. Revocation of admin privileges
2. Required security training
3. Incident review with leadership
4. Additional approval requirements for future PRs

## Best Practices

1. **Try Alternatives First**:
   - Can you fix the security issue quickly?
   - Can you use the exception process?
   - Can you split the PR to merge safe parts?

2. **Minimize Scope**:
   - Override only the specific security check
   - Keep the override window as short as possible
   - Fix the issue in the next PR

3. **Communicate Transparently**:
   - Over-communicate the reasons
   - Keep stakeholders informed
   - Document everything

## Examples

### Example 1: Critical Production Fix

```bash
git commit -m "SECURITY_OVERRIDE: Critical payment processing fix

Justification: Payment gateway integration is failing for 30% of transactions
Risk Assessment: CodeQL detected potential SQL injection in logging statement
Mitigation: Logging statement will be removed in follow-up PR today
Approver: @jane-doe
Ticket: https://github.com/org/repo/issues/501
Expires: 2024-01-11 (24 hours)"
```

### Example 2: False Positive

```bash
git commit -m "SECURITY_OVERRIDE: False positive in dependency scan

Justification: CVE-2023-12345 flagged in test dependency not used in production
Risk Assessment: No production risk as this is a dev-only dependency
Mitigation: Exception will be added to security-exceptions.yml
Approver: @security-lead
Ticket: https://github.com/org/repo/issues/502
Expires: 2024-01-17 (1 week)"
```

## Questions or Concerns

If you have questions about the override process:

1. Contact the security team: security@company.com
2. Slack: #security-help
3. Office hours: Thursdays 2-3 PM

Remember: **Security overrides are a last resort.** Always try to fix the underlying issue first.
