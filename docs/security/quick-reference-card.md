# Security Gates Quick Reference Card

## 🚦 When Your PR is Blocked

### 1. Identify the Issue
```bash
# Check which security scan failed
gh pr checks [PR-NUMBER]

# Look for failed checks:
# - CodeQL Analysis
# - dependency-review  
# - PR Validation
```

### 2. Fix or Request Exception

#### Option A: Fix the Security Issue (Preferred)
```bash
# Address the security finding
# Update dependencies: poetry update
# Fix code issues: Follow CodeQL suggestions
# Run tests: poetry run pytest
```

#### Option B: Request Exception (False Positives)
```yaml
# Add to .github/security-exceptions.yml
- id: "EX-[INCREMENT]"
  type: "false-positive"
  tool: "[SCAN_TOOL]"
  rule: "[RULE_NAME]"
  file: "[FILE_PATH]"
  line: [LINE_NUMBER]
  justification: "[WHY_FALSE_POSITIVE]"
  expires: "[YYYY-MM-DD]"
  approved_by: "@security-team"
  pr_reference: "#[PR_NUMBER]"
```

#### Option C: Emergency Override (Production Only)
```bash
# Use only for true emergencies
git commit -m "EMERGENCY_OVERRIDE: [BRIEF_REASON]

EXPIRES: $(date -d '+2 hours' -Iseconds)
APPROVER: @[MANAGER]
JUSTIFICATION: [DETAILED_REASON]"
```

### 3. Get Help
- **Slack**: #security-help
- **Email**: security-team@company.com
- **Emergency**: +1-800-SEC-HELP

---

## 🛠️ Common Security Issues & Fixes

### CodeQL Issues
| Issue | Quick Fix |
|-------|-----------|
| SQL Injection | Use parameterized queries |
| XSS | Escape user input properly |
| Path Traversal | Validate file paths |
| Hardcoded Secrets | Use environment variables |

### Dependency Issues
| Issue | Quick Fix |
|-------|-----------|
| Vulnerable Package | `poetry update [package]` |
| High-Risk CVE | Check for security patches |
| Outdated Dependencies | `poetry update` |

### Example Fixes
```python
# ❌ SQL Injection Risk
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ Safe Parameterized Query  
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))

# ❌ XSS Risk
return f"<div>Hello {user_name}</div>"

# ✅ Escaped Output
return f"<div>Hello {html.escape(user_name)}</div>"
```

---

## 📋 Exception Request Template

```yaml
# Copy this template to .github/security-exceptions.yml
- id: "EX-XXX"  # Increment number
  type: "false-positive"  # or "accepted-risk" | "pending-fix"
  tool: "codeql"  # or "dependency-review" | "pr-validation"
  rule: "py/sql-injection"  # Specific rule that triggered
  file: "src/models/user.py"  # Full file path
  line: 45  # Line number (if applicable)
  justification: "This query uses safe ORM methods with no user input"
  risk_accepted: false  # true for accepted-risk type
  expires: "2024-03-15"  # YYYY-MM-DD format
  approved_by: "@security-team"  # GitHub username
  approved_date: "2024-01-15"  # When approved
  pr_reference: "#456"  # Link to PR
  # mitigation: "Additional context for accepted risks"
```

---

## 🚨 Emergency Override Decision Tree

```
Is this a true emergency?
├─ NO → Use exception process
└─ YES → Is production affected?
    ├─ YES → EMERGENCY_OVERRIDE (2h max)
    └─ NO → Is revenue at risk?
        ├─ YES → Revenue override (6h max)  
        └─ NO → Standard override (48h max)
```

### Emergency Override Types
| Type | Duration | Approver | Use Case |
|------|----------|----------|----------|
| Production Down | 2 hours | Engineering Manager | System outage |
| Security Fix | 4 hours | Security Lead | Critical patch |
| Revenue Blocking | 6 hours | Director | Customer impact |

---

## 📞 Quick Contacts

### During Business Hours
- **Security Help**: #security-help
- **General Questions**: security-team@company.com
- **Office Hours**: Thursdays 2-3 PM

### After Hours/Emergency
- **Emergency Phone**: +1-800-SEC-HELP
- **Urgent Slack**: #emergency-engineering  
- **Email**: engineering-emergency@company.com

### Key People
- **Security Lead**: @jane-security
- **DevOps Lead**: @devops-lead
- **Engineering Manager**: @eng-manager

---

## 📊 Useful Commands

```bash
# Check PR status
gh pr status

# View specific PR checks
gh pr checks [PR-NUMBER]

# Create exception PR
gh pr create --title "Security Exception: [DESCRIPTION]" \
  --body "Adding exception for false positive in [FILE]"

# Emergency merge (admin only)
gh pr merge [PR-NUMBER] --admin --merge

# View security metrics
python scripts/security-metrics-simple.py

# Configure branch protection
./scripts/configure-branch-protection.sh --branch [BRANCH]
```

---

## 💡 Pro Tips

### Prevent Issues Early
1. **Run security checks locally** before pushing
2. **Keep dependencies updated** regularly  
3. **Follow secure coding standards**
4. **Use IDE security plugins** for real-time feedback

### Speed Up Resolution
1. **Read the error message** carefully
2. **Check if it's a known false positive** in exceptions file
3. **Ask in #security-help** before guessing
4. **Include context** when requesting help

### Best Practices
1. **Fix real issues** rather than requesting exceptions
2. **Be specific** in exception justifications
3. **Set reasonable expiry dates** for exceptions
4. **Follow up** on pending fixes

---

*Keep this reference handy! Bookmark this page or print for quick access during development.*

**Remember**: Security gates are here to help, not hinder. When in doubt, ask for help! 🤝