---
title: "What The Diff (WTD) Cost Monitoring Guide"
version: "1.0"
status: "published"
component: "Implementation-Guide"
tags: ["wtd", "cost-monitoring", "openai", "ci-cd"]
purpose: "Provide guidance for monitoring and optimizing WTD OpenAI API costs"
---

# What The Diff (WTD) Cost Monitoring Guide

## Overview

This document provides guidance for monitoring and optimizing costs associated with the What The Diff (WTD)
AI-powered PR summary integration implemented in Phase 1 Issue 38.

## Cost Optimization Features

### Built-in Cost Controls

- **GPT-3.5-Turbo Model**: Uses cost-efficient model (~$0.002/1K tokens)
- **File Filtering**: Excludes generated files reducing token usage by 60-80%
- **Draft Exclusion**: Skips draft PRs until ready for review
- **Bot Exclusion**: Prevents processing of automated PRs
- **Single Comment Mode**: Updates one comment instead of creating multiple

### File Exclusion Patterns

The following patterns are automatically excluded from analysis:

```yaml
Excluded Paths:
  - dist/**
  - build/**
  - vendor/**
  - *.lock files (package-lock.json, poetry.lock)
  - Binary files (*.png, *.jpg, *.gif, etc.)
```

## Monitoring Approach

### Initial Baseline Collection

**Week 1 Post-Deployment**:
1. Monitor OpenAI API usage in organization dashboard
2. Track costs per PR analysis
3. Document average tokens per PR type
4. Establish baseline cost metrics

### Ongoing Monitoring

**Weekly Reviews**:
- Check OpenAI API usage dashboard
- Review cost per PR summary
- Monitor for usage spikes or anomalies
- Assess file filtering effectiveness

**Monthly Analysis**:
- Calculate ROI based on review time savings
- Analyze cost trends and optimization opportunities
- Review file exclusion patterns for effectiveness

## Cost Thresholds and Alerts

### Recommended Thresholds

- **Daily Limit**: $50/day (triggers investigation)
- **Monthly Budget**: $200/month (typical for active development)
- **Per-PR Average**: $0.10-$0.50 (depending on PR size)

### Alert Setup

Consider setting up OpenAI usage alerts:
1. Go to OpenAI platform organization settings
2. Set up usage notifications at 80% of monthly budget
3. Configure daily usage alerts for unusual spikes

## Cost Optimization Strategies

### If Costs Exceed Budget

1. **Review File Filtering**:
   - Add more patterns to WTD_IGNORE_PATHS
   - Update .gitattributes for better exclusion

2. **Adjust Trigger Conditions**:
   - Skip PRs with >100 files changed
   - Exclude PRs with only documentation changes

3. **Model Optimization**:
   - Consider using GPT-3.5-Turbo-Instruct for simpler summaries
   - Implement custom prompt optimization

### Example Enhanced Exclusions

```bash
# Add to workflow if costs are high
export WTD_IGNORE_PATHS="dist/**,build/**,vendor/**,*.lock,*.png,*.jpg,*.gif,*.svg,*.ico,docs/**/*.md,*.json,*.yml,*.yaml"
```

## Rollback Procedures

### Immediate Cost Rollback

If costs exceed $50/day:

1. **Temporary Disable**: Comment out WTD workflow triggers
2. **Investigation**: Review recent PR analysis for unusual usage
3. **Adjustment**: Implement additional filtering before re-enabling

### Complete Rollback

If WTD provides insufficient value:

1. **Remove Workflow**: Delete `.github/workflows/wtd.yml`
2. **Clean Secrets**: Remove WTD_OPENAI_API_KEY from repository secrets
3. **Update Documentation**: Remove WTD references from CONTRIBUTING.md

## Cost-Benefit Analysis

### Expected Savings

- **Review Time**: 5-10 minutes saved per PR for reviewers
- **Context Switching**: Faster initial understanding of changes
- **Onboarding**: New reviewers get better context

### Break-Even Analysis

If average PR costs $0.25 and saves 7 minutes of developer time:
- Developer rate: $50/hour = $0.83/minute
- Time savings value: 7 minutes × $0.83 = $5.81
- ROI: ($5.81 - $0.25) / $0.25 = 2,224% return

## Reporting Template

### Weekly Cost Report

```markdown
## WTD Cost Report - Week of [Date]

**Usage Metrics**:
- Total PRs Analyzed: X
- Total API Calls: X
- Total Tokens Used: X
- Total Cost: $X.XX

**Cost per PR**:
- Average: $X.XX
- Median: $X.XX
- Range: $X.XX - $X.XX

**Optimization Opportunities**:
- Large PRs (>50 files): X PRs, $X.XX cost
- Documentation-only PRs: X PRs, $X.XX cost

**Action Items**:
- [ ] Review file filtering effectiveness
- [ ] Assess cost threshold compliance
- [ ] Document any optimization changes
```

## Contact Information

For WTD cost monitoring questions or issues:
- **Technical Implementation**: Phase 1 Issue 38 documentation
- **Cost Optimization**: Review file exclusion patterns
- **Budget Concerns**: Consider rollback procedures outlined above
