# Security Gate Override Process

## Overview

This document outlines the process for overriding security gates in emergency situations. Admin overrides should be used sparingly and only when absolutely necessary.

> **IMPORTANT**: All overrides are time-boxed and require automatic expiration. No override should remain in effect indefinitely.

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

## Emergency Override Types & Time Limits

### Break Glass Procedures

For immediate emergency situations requiring instant action:

| Emergency Type | Required Approver | Maximum Duration | Auto-Expiry | Follow-up Required |
|----------------|------------------|------------------|-------------|-------------------|
| **Production Down** | Engineering Manager | 2 hours | ✅ Automatic | Within 4 hours |
| **Critical Security Fix** | Security Team Lead | 4 hours | ✅ Automatic | Within 8 hours |
| **Revenue Blocking** | Director level | 6 hours | ✅ Automatic | Within 12 hours |

### Standard Override Procedures

For planned overrides with justification:

| Scenario | Required Approver | Maximum Duration | Review Cycle | Extensions |
|----------|------------------|------------------|--------------|------------|
| Critical hotfix | Engineering Manager | 48 hours | Daily | 1x (24 hours) |
| False positive | Security Team Lead | 1 week | Every 2 days | 1x (3 days) |
| Tool malfunction | DevOps Lead | Until fixed | Weekly | Unlimited with justification |
| Business continuity | Director level | 72 hours | Every 12 hours | 1x (48 hours) |

### Time-Boxed Override Implementation

All overrides must include automatic expiration:

```bash
# Emergency override with 2-hour auto-expiry
git commit -m "EMERGENCY_OVERRIDE: Production payment system down

EXPIRES: $(date -d '+2 hours' -Iseconds)
APPROVER: @engineering-manager
AUTO_REVERT: true
TRACKING: #EMERGENCY-$(date +%Y%m%d-%H%M)"
```

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

## Escalation Paths & Emergency Contacts

### 24/7 Emergency Escalation

For production-critical situations requiring immediate override:

1. **Primary**: Engineering Manager on-call rotation
2. **Secondary**: Director of Engineering
3. **Executive**: CTO (for revenue-blocking issues)

### Contact Methods

| Urgency | Contact Method | Response SLA |
|---------|---------------|--------------|
| **EMERGENCY** | Phone + Slack + Email | 15 minutes |
| **URGENT** | Slack + Email | 30 minutes |
| **STANDARD** | Email + GitHub mention | 2 hours |

### Emergency Contact Information

```bash
# On-call rotation (updated weekly)
curl -s https://company.pagerduty.com/api/oncalls/engineering

# Emergency contacts
Emergency Phone: +1-800-ENG-HELP
Slack: #emergency-engineering
Email: engineering-emergency@company.com
```

### Override Monitoring & Alerts

#### Automatic Monitoring

- **Expiry Alerts**: 30-minute warning before override expires
- **Usage Tracking**: Daily override count reports
- **Pattern Detection**: Alerts for unusual override patterns
- **Compliance Monitoring**: Weekly audit reports

#### Manual Review Process

1. **Daily Stand-ups**: Review active overrides
2. **Weekly Security Review**: Override patterns and trends
3. **Monthly Audit**: Complete override compliance review
4. **Quarterly Training**: Override best practices refresh

## Override Automation Scripts

### Emergency Override Helper

```bash
#!/bin/bash
# scripts/emergency-override.sh - Guided emergency override process

OVERRIDE_TYPE="$1"
DURATION="$2"
JUSTIFICATION="$3"

case "$OVERRIDE_TYPE" in
  "production-down")
    MAX_DURATION="2h"
    REQUIRED_APPROVER="engineering-manager"
    ;;
  "security-fix")
    MAX_DURATION="4h"
    REQUIRED_APPROVER="security-lead"
    ;;
  "revenue-blocking")
    MAX_DURATION="6h"
    REQUIRED_APPROVER="director"
    ;;
  *)
    echo "Invalid override type. Use: production-down, security-fix, revenue-blocking"
    exit 1
    ;;
esac

# Validate duration doesn't exceed maximum
# Generate tracking issue
# Create override commit with auto-expiry
# Send notifications
```

### Override Expiry Monitor

```bash
#!/bin/bash
# scripts/monitor-overrides.sh - Check for expiring overrides

# Find commits with EMERGENCY_OVERRIDE or SECURITY_OVERRIDE
# Parse expiry dates
# Send alerts for approaching expiries
# Auto-create follow-up issues
# Generate compliance reports
```

## Questions or Concerns

### During Business Hours
1. Contact the security team: security@company.com
2. Slack: #security-help
3. Office hours: Thursdays 2-3 PM

### After Hours Emergency
1. **EMERGENCY**: Call +1-800-ENG-HELP
2. **URGENT**: Slack #emergency-engineering
3. **STANDARD**: Create GitHub issue with `urgent-security` label

Remember: **Security overrides are a last resort.** Always try to fix the underlying issue first.

### Override Decision Tree

```
Is this a true emergency? 
├─ NO → Use standard exception process (.github/security-exceptions.yml)
├─ YES → Is production affected?
    ├─ YES → Use EMERGENCY_OVERRIDE (2-hour max)
    ├─ NO → Is revenue at risk?
        ├─ YES → Use revenue-blocking override (6-hour max)
        ├─ NO → Use standard override process (48-hour max)
```
