---
title: Pre-flight Validation Guide
version: v1.0
status: draft
source: "AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework v2.1"
approx_tokens: 30k
purpose: >
  Provides comprehensive pre-generation validation procedures for PromptCraft Pro
  to identify and resolve potential issues before prompt generation, reducing
  downstream errors and improving output quality.
---

# Pre-flight Validation Guide

## Table of Contents

1. [Introduction to Pre-flight Validation](#introduction-to-pre-flight-validation)
2. [Core Validation Categories](#core-validation-categories)
3. [Validation Decision Tree](#validation-decision-tree)
4. [Common Conflict Patterns](#common-conflict-patterns)
5. [Domain-Specific Validation Rules](#domain-specific-validation-rules)
6. [Interactive Resolution Workflows](#interactive-resolution-workflows)
7. [Validation Severity Levels](#validation-severity-levels)
8. [Implementation Guidelines](#implementation-guidelines)

## Introduction to Pre-flight Validation

Pre-flight validation is the systematic process of analyzing a user's request BEFORE generating the full C.R.E.A.T.E.
prompt. This proactive approach catches potential issues early, reducing downstream LLM errors, preventing
hallucinations, and ensuring output quality matches user expectations.

The validation system operates on three principles:

1. **Fail Fast**: Identify problems before expensive LLM generation
2. **Guide Users**: Provide actionable feedback for resolution
3. **Learn Continuously**: Update rules based on success/failure patterns

## Core Validation Categories

### 1. Internal Consistency Validation

**Purpose**: Detect contradictions within the request that would confuse the downstream LLM.

**Key Checks**:

- **Tone Conflicts**: "Be formal but conversational" → Flag: Choose primary tone
- **Length Impossibilities**: "50-word comprehensive analysis" → Flag: Adjust expectations
- **Framework Mismatches**: "SWOT analysis in IRAC format" → Flag: Clarify structure
- **Role-Task Misalignment**: "As a comedian, write a legal brief" → Flag: Reconcile

**Resolution Strategy**:

```text
IF conflict_detected:
    severity = assess_conflict_impact()
    IF severity == "blocking":
        require_user_choice(option_a, option_b)
    ELIF severity == "warning":
        suggest_primary_mode()
        allow_override()
    ELSE:
        auto_resolve_with_note()
```text

### 2. Feasibility Validation

**Purpose**: Ensure requested outputs are achievable within constraints.

**Key Checks**:

- **Depth-Content Ratio**: Can the requested content fit in the tier?
- **Token Budget**: Will evaluation + content exceed limits?
- **Complexity-Time**: Is the task achievable in reasonable time?
- **Data Availability**: Are required sources accessible?

**Feasibility Matrix**:

| Content Elements     | Tier 1-3 | Tier 4-6 | Tier 7-10 |
| -------------------- | -------- | -------- | --------- |
| Distinct Topics      | 1-2      | 3-5      | 6+        |
| Analysis Depth       | Surface  | Moderate | Deep      |
| Source Integration   | 0-2      | 3-5      | 6+        |
| Framework Complexity | Simple   | Standard | Advanced  |

### 3. Ambiguity Detection

**Purpose**: Identify undefined terms or unclear requirements.

**Common Ambiguities**:

- **Temporal**: "recent" → Clarify: Last 30/90/365 days?
- **Scope**: "comprehensive" → Clarify: Which aspects?
- **Audience**: "technical" → Clarify: What expertise level?
- **Format**: "report" → Clarify: Academic? Business? Technical?

**Resolution Flow**:

1. Detect ambiguous terms via pattern matching
2. Check context for implicit definitions
3. If unresolved, generate clarification questions
4. Provide smart defaults with override option

### 4. Requirement Completeness

**Purpose**: Ensure all necessary components are specified.

**Component Checklist by Tier**:

**Tiers 1-3 (Minimal)**:

- [x] Core task defined
- [x] Approximate length specified
- [ ] Sources (optional)

**Tiers 4-6 (Standard)**:

- [x] Clear deliverable type
- [x] Target audience identified
- [x] Success criteria implied
- [x] Source types indicated (if factual)

**Tiers 7-10 (Full)**:

- [x] Detailed requirements
- [x] Explicit success criteria
- [x] Source list or search strategy
- [x] Framework selection justified

## Validation Decision Tree

```text
START
│
├─ Parse Request Components
│  └─ Extract C.R.E.A.T.E. elements
│
├─ Check Internal Consistency
│  ├─ PASS → Continue
│  └─ FAIL → Resolve Conflicts
│     ├─ Auto-resolvable → Apply fix + note
│     └─ User input needed → Interactive resolution
│
├─ Verify Feasibility
│  ├─ PASS → Continue
│  └─ FAIL → Adjust or Reject
│     ├─ Minor adjustment → Suggest modification
│     └─ Impossible → Explain + alternatives
│
├─ Detect Ambiguities
│  ├─ NONE → Continue
│  └─ FOUND → Clarify
│     ├─ Smart default available → Apply + confirm
│     └─ Critical ambiguity → Request clarification
│
├─ Assess Completeness
│  ├─ COMPLETE → Generate prompt
│  └─ INCOMPLETE → Fill gaps
│     ├─ Defaults sufficient → Apply defaults
│     └─ Critical missing → Request information
│
└─ VALIDATION COMPLETE
```text

## Common Conflict Patterns

### Pattern 1: Style Contradictions

**Example**: "Write a formal yet friendly and casual analysis"
**Detection**: Multiple tone descriptors with opposing meanings
**Resolution**:

- Primary: "Formal analysis"
- Modifier: "with approachable explanations"
- Note: "Friendly elements in examples only"

### Pattern 2: Length-Depth Mismatch

**Example**: "100-word comprehensive literature review"
**Detection**: Tier 2 length + Tier 8 depth requirement
**Resolution**:

- Option A: "100-word executive summary of literature"
- Option B: "2000-word literature review (Tier 5)"
- Default: Option A with offer to expand

### Pattern 3: Framework Confusion

**Example**: "SWOT analysis using IRAC method"
**Detection**: Multiple framework keywords
**Resolution**:

- Clarify primary framework: "SWOT is the structure"
- Clarify secondary: "IRAC-style reasoning within each quadrant"
- Alternative: "Choose one framework"

### Pattern 4: Source-Claim Mismatch

**Example**: "Analyze 2024 Supreme Court decision" (no source provided)
**Detection**: Specific factual claim + no source
**Resolution**:

- Add to A-block: "web.search_query for case name"
- Flag: "Will search for recent decision"
- Require: Case name or search terms

## Domain-Specific Validation Rules

### Legal Domain

```text
IF domain == "legal":
    REQUIRE:
        - Citation style specified (default: Bluebook)
        - Jurisdiction identified (if relevant)
        - Legal framework selected (IRAC, CREAC, etc.)
    WARN IF:
        - No primary sources mentioned
        - Informal tone selected
        - Tier < 4 for memo/brief
```text

### Financial Domain

```text
IF domain == "financial":
    REQUIRE:
        - Time period specified
        - Currency/units clarified
        - Calculation methodology stated
    VALIDATE:
        - Precision Mode for quantitative analysis
        - Source data availability
        - Regulatory framework (if applicable)
```text

### Technical Domain

```text
IF domain == "technical":
    REQUIRE:
        - Technical level specified
        - Platform/language identified
        - Version requirements stated
    CHECK:
        - Code output format
        - Documentation style
        - Security considerations flag
```text

### Policy Domain

```text
IF domain == "policy":
    REQUIRE:
        - Stakeholder identification
        - Geographic scope
        - Time horizon
    RECOMMEND:
        - Evidence hierarchy
        - Bias mitigation emphasis
        - Multiple perspective flag
```text

## Interactive Resolution Workflows

### Workflow 1: Ambiguity Resolution

```text
1. DETECT: "Analyze the recent policy changes"
2. PROMPT: "To ensure accuracy, please clarify 'recent':"
   - [ ] Last 30 days
   - [ ] Last 90 days
   - [ ] Since January 2025
   - [ ] Custom range: ___
3. DEFAULT: "Will search last 90 days unless specified"
4. PROCEED: With clarified parameter
```text

### Workflow 2: Conflict Resolution

```text
1. DETECT: Conflicting instructions
2. PRESENT: "I notice these requirements may conflict:"
   - Requirement A: "Brief summary"
   - Requirement B: "Comprehensive analysis"
3. OPTIONS:
   - [ ] Brief summary (300 words)
   - [ ] Comprehensive analysis (3000 words)
   - [ ] Executive summary + detailed appendix
4. APPLY: User selection to prompt
```text

### Workflow 3: Missing Requirements

```text
1. DETECT: Critical component missing
2. ASSESS: Can defaults work?
3. IF NO:
   PROMPT: "For optimal results, please provide:"
   - Specific sources [optional/required]
   - Success criteria [recommended]
   - Target audience [required for tone]
4. ALLOW: "Proceed with defaults" option
```text

## Validation Severity Levels

### Level 1: Auto-Correct (Green)

**Characteristics**: Minor issues with obvious fixes
**Examples**:

- Missing punctuation in tier specification
- Common typos in framework names
- Implied but unstated audience
**Action**: Fix silently, log correction

### Level 2: Warning (Yellow)

**Characteristics**: Potential issues that may affect quality
**Examples**:

- Ambitious depth for tier
- Multiple tone descriptors
- Unspecified time ranges
**Action**: Highlight issue, suggest fix, allow override

### Level 3: Blocking (Red)

**Characteristics**: Issues that will cause failure
**Examples**:

- Impossible length-content combination
- Contradictory core requirements
- Missing critical data for factual analysis
**Action**: Require resolution before proceeding

## Implementation Guidelines

### Performance Considerations

- Run validations in parallel where possible
- Cache validation results for similar requests
- Timeout after 2 seconds, proceed with warnings

### Learning Integration

- Log validation outcomes with final output quality
- Update rules based on failure patterns
- A/B test validation strictness

### User Experience

- Show validation progress indicator
- Provide clear, actionable messages
- Offer "Why?" explanations for rules
- Remember user preferences

### Integration Points

```python
def preflight_validation(request):
    results = {
        'status': 'pending',
        'errors': [],
        'warnings': [],
        'suggestions': []
    }

    # Parallel validation
    consistency = check_consistency(request)
    feasibility = check_feasibility(request)
    ambiguity = check_ambiguity(request)
    completeness = check_completeness(request)

    # Domain-specific rules
    if domain := detect_domain(request):
        domain_check = validate_domain_rules(request, domain)

    # Compile results
    return compile_validation_results(
        consistency, feasibility,
        ambiguity, completeness,
        domain_check
    )
```text

### Validation Report Format

```json
{
  "validation_status": "warning",
  "quality_score": 7.5,
  "issues": [
    {
      "type": "ambiguity",
      "severity": "warning",
      "component": "request",
      "issue": "Temporal term 'recent' undefined",
      "suggestion": "Specify timeframe: last 30/90/365 days",
      "auto_fix": "Default: last 90 days"
    }
  ],
  "ready_to_generate": true,
  "estimated_tokens": 2400
}
```text
