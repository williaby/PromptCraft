---
title: Validation Rules and Real-time Feedback
version: v1.0
status: draft
source: "AI Prompt Engineering Guide: The C.R.E.A.T.E. Framework v2.1"
approx_tokens: 35k
purpose: >
  Defines the complete set of validation rules for real-time prompt quality assessment,
  enabling immediate feedback during prompt construction and preventing common errors
  before generation begins.
---

# Validation Rules and Real-time Feedback

## Table of Contents

1. [Introduction to Real-time Validation](#introduction-to-real-time-validation)
2. [Validation Rule Structure](#validation-rule-structure)
3. [Component-Specific Rules](#component-specific-rules)
4. [Cross-Component Validation](#cross-component-validation)
5. [Quality Scoring Algorithm](#quality-scoring-algorithm)
6. [Real-time Feedback UI Patterns](#real-time-feedback-ui-patterns)
7. [Custom Rule Development](#custom-rule-development)
8. [Performance Optimization](#performance-optimization)
9. [Rule Precedence and Conflicts](#rule-precedence-and-conflicts)

## Introduction to Real-time Validation

Real-time validation provides immediate feedback as users construct their prompts, catching errors before they propagate to the downstream LLM. This system operates continuously, validating each component as it's modified and checking cross-component consistency.

The validation system uses a three-tier feedback model:
- **Immediate** (< 100ms): Syntax and format checks
- **Quick** (< 500ms): Semantic and consistency checks  
- **Deep** (< 2000ms): Complex cross-component analysis

## Validation Rule Structure

Each validation rule follows this standardized format:

```yaml
rule_id: "CR001"
name: "Context Role Token Length"
component: "context"
field: "role"
severity: "warning"
trigger:
  condition: "token_count(role) > 5"
  real_time: true
validation:
  type: "token_count"
  parameters:
    min: 3
    max: 5
    count_method: "whitespace_split"
feedback:
  user_message: "Role should be 3-5 words for clarity"
  suggestion: "Consider: 'veteran policy analyst' instead"
  documentation_link: "#context-role-guidelines"
auto_fix:
  available: true
  method: "truncate_to_max"
  requires_confirmation: true
metrics:
  false_positive_rate: 0.02
  user_override_rate: 0.15
  performance_impact: "low"
```

## Component-Specific Rules

### Context (C) Validation Rules

#### CR001: Role Token Length
```yaml
trigger: "token_count(role) > 5 OR token_count(role) < 3"
severity: "warning"
message: "Role should be 3-5 tokens (e.g., 'senior tax attorney')"
auto_fix: "suggest_truncation"
```

#### CR002: Persona Clause Length
```yaml
trigger: "word_count(persona_clause) > 12"
severity: "warning"
message: "Persona clause should be ≤12 words for impact"
suggestion: "Focus on one key trait or background element"
```

#### CR003: AI/LLM Self-Reference
```yaml
trigger: "contains_any(role, ['AI', 'LLM', 'chatbot', 'assistant'])"
severity: "error"
message: "Avoid AI self-references in role definition"
auto_fix: "remove_terms"
```

#### CR004: Background Completeness
```yaml
trigger: "tier >= 4 AND missing_all(background, ['objective', 'scope', 'constraints'])"
severity: "warning"
message: "Background should include objective, scope, or constraints for Tier 4+"
checklist:
  - "Primary objective defined?"
  - "Scope boundaries stated?"
  - "Key constraints mentioned?"
```

#### CR005: Goal Clarity
```yaml
trigger: "contains_vague_terms(goal, ['help', 'assist', 'support']) AND no_specific_outcome"
severity: "warning"
message: "Goal should specify concrete outcome"
examples:
  bad: "Help with analysis"
  good: "Produce actionable recommendations for board approval"
```

### Request (R) Validation Rules

#### RR001: Deliverable Specificity
```yaml
trigger: "missing(deliverable_type) OR too_generic(deliverable)"
severity: "error"
message: "Specify exact deliverable (memo, analysis, script, etc.)"
suggestions: 
  - "Legal: memo, brief, contract review"
  - "Technical: script, architecture doc, API spec"
  - "Business: executive summary, SWOT, proposal"
```

#### RR002: Tier-Length Alignment
```yaml
trigger: "selected_tier != appropriate_tier_for_length(word_count)"
severity: "warning"
calculation: |
  if word_count <= 60: expected_tier = 1
  elif word_count <= 400: expected_tier = 2-3
  elif word_count <= 2000: expected_tier = 4-5
  ...
message: "Word count suggests Tier {expected}, but Tier {selected} chosen"
```

#### RR003: Action Verb Strength
```yaml
trigger: "starts_with_weak_verb(request, ['discuss', 'talk about', 'cover'])"
severity: "warning"
message: "Use strong action verbs for clarity"
suggestions:
  weak: "Discuss the policy"
  strong: "Analyze policy impact" | "Compare policy options" | "Evaluate policy effectiveness"
```

#### RR004: Framework-Request Compatibility
```yaml
trigger: "framework_mismatch(selected_framework, request_type)"
severity: "error"
examples:
  - incompatible: "SWOT analysis for legal statute interpretation"
  - compatible: "IRAC analysis for legal statute interpretation"
message: "Framework '{framework}' unsuitable for {request_type}"
```

### Examples (E) Validation Rules

#### ER001: Example-Request Alignment
```yaml
trigger: "example_format != expected_output_format"
severity: "error"
message: "Example format doesn't match requested output"
check: "structural_similarity(example_output, expected_format) < 0.7"
```

#### ER002: Example Quality
```yaml
trigger: "example_contains_errors OR example_too_simple"
severity: "warning"
checks:
  - "Grammar and spelling correct?"
  - "Format matches exactly?"
  - "Appropriate complexity?"
message: "Example may be too simple or contains errors"
```

#### ER003: Example Sufficiency
```yaml
trigger: "complex_format AND example_count < 2"
severity: "warning"
message: "Complex formats benefit from 2-3 examples"
recommendation: "Add {2 - current_count} more examples"
```

### Augmentations (A) Validation Rules

#### AR001: Source Availability
```yaml
trigger: "requires_factual_accuracy AND no_sources_specified"
severity: "warning"
message: "Factual analysis benefits from specified sources"
suggestion: "Add source documents or enable web search"
```

#### AR002: Framework Selection
```yaml
trigger: "no_framework AND request_implies_framework"
severity: "warning"
detection: |
  if contains(request, ['compare', 'contrast']): suggest 'Comparative Analysis'
  if contains(request, ['strengths', 'weaknesses']): suggest 'SWOT'
  if contains(request, ['legal', 'statute']): suggest 'IRAC'
message: "Consider using {suggested_framework} framework"
```

#### AR003: Evidence-Claim Balance
```yaml
trigger: "word_count > 2000 AND no_evidence_directives"
severity: "warning"
message: "Long-form content should specify evidence requirements"
add_to_prompt: "Tag unsourced claims with [ExpertJudgment]"
```

#### AR004: Mode-Task Alignment
```yaml
trigger: "selected_mode != optimal_mode_for_task"
severity: "warning"
rules:
  - "numerical_analysis → Precision Mode"
  - "strategic_planning → Analysis Mode"  
  - "creative_writing → Creative Mode"
message: "Consider {optimal_mode} for {task_type}"
```

### Tone & Format (T) Validation Rules

#### TR001: Tone Consistency
```yaml
trigger: "multiple_conflicting_tones"
severity: "error"
conflicts:
  - ["formal", "casual"]
  - ["academic", "conversational"]
  - ["technical", "lay-person"]
message: "Conflicting tones: {tone1} vs {tone2}"
resolution: "Choose primary tone, note exceptions"
```

#### TR002: Citation Style Specification
```yaml
trigger: "academic_output AND no_citation_style"
severity: "warning"
message: "Academic content needs citation style"
defaults:
  - "Legal → Bluebook"
  - "Academic → Chicago"
  - "Scientific → APA"
```

#### TR003: Format-Content Feasibility
```yaml
trigger: "complex_format AND tier < 4"
severity: "warning"
examples:
  - "Full academic paper in Tier 2"
  - "Detailed technical spec in 200 words"
message: "Format complexity exceeds tier capacity"
```

### Evaluation (E) Validation Rules

#### EV001: Evaluation-Tier Mismatch
```yaml
trigger: "evaluation_mode != tier_default"
severity: "info"
message: "Using {mode} evaluation for Tier {tier}"
note: "Override detected - ensure intentional"
```

#### EV002: Missing Critical Checks
```yaml
trigger: "high_stakes_domain AND missing_critical_evaluations"
severity: "error"
required_checks:
  legal: ["citation_verification", "precedent_check"]
  financial: ["calculation_verification", "assumption_validation"]
  medical: ["source_authority", "disclaimer_presence"]
message: "Critical evaluation missing for {domain}"
```

## Cross-Component Validation

### XC001: Role-Tone Alignment
```yaml
components: ["context.role", "tone.style"]
trigger: "role_tone_mismatch"
examples:
  - mismatch: "Role: 'technical expert' + Tone: 'casual lay-person'"
  - aligned: "Role: 'technical expert' + Tone: 'technical practitioner'"
severity: "warning"
message: "Role '{role}' typically uses {expected_tone} tone"
```

### XC002: Length-Depth Feasibility
```yaml
components: ["request.tier", "request.depth", "augmentations.framework"]
trigger: "impossible_depth_for_length"
calculation: |
  required_words = estimate_framework_words(framework) + 
                  estimate_depth_words(depth)
  if required_words > tier_max_words * 1.2: trigger
severity: "error"
message: "Cannot fit {framework} + {depth} analysis in Tier {tier}"
```

### XC003: Source-Claim Requirements
```yaml
components: ["request.type", "augmentations.sources", "evaluation.mode"]
trigger: "factual_claims AND insufficient_sourcing"
severity: "warning"
rules:
  - "Legal analysis → Primary sources required"
  - "Statistical claims → Data sources required"
  - "Historical facts → Date-verified sources required"
message: "Factual {type} requires source specification"
```

### XC004: Evaluation Completeness
```yaml
components: ["request.tier", "augmentations.mode", "evaluation.checks"]
trigger: "missing_required_evaluation_elements"
severity: "error"
requirements:
  tier_7_plus:
    - "Multi-path reasoning"
    - "Confidence scoring"
    - "Adversarial testing"
message: "Tier {tier} requires: {missing_elements}"
```

## Quality Scoring Algorithm

### Overall Quality Score (0-10)

```python
def calculate_quality_score(prompt_components):
    """Calculate overall prompt quality score"""
    
    # Component scores (0-2 each)
    scores = {
        'context': score_context(prompt_components.context),
        'request': score_request(prompt_components.request),
        'examples': score_examples(prompt_components.examples),
        'augmentations': score_augmentations(prompt_components.augmentations),
        'tone_format': score_tone_format(prompt_components.tone_format)
    }
    
    # Weighted sum
    weights = {
        'context': 0.20,
        'request': 0.30,  # Most critical
        'examples': 0.15,
        'augmentations': 0.20,
        'tone_format': 0.15
    }
    
    base_score = sum(scores[k] * weights[k] * 5 for k in scores)
    
    # Penalty factors
    penalties = {
        'internal_conflicts': -1.0 * count_conflicts(prompt_components),
        'missing_required': -0.5 * count_missing_required(prompt_components),
        'ambiguity': -0.3 * ambiguity_score(prompt_components)
    }
    
    # Bonus factors
    bonuses = {
        'completeness': 0.5 if all_recommended_present() else 0,
        'clarity': 0.5 if clarity_score() > 0.8 else 0,
        'framework_fit': 0.5 if perfect_framework_match() else 0
    }
    
    final_score = base_score + sum(penalties.values()) + sum(bonuses.values())
    return max(0, min(10, final_score))

def score_context(context):
    """Score context component (0-2)"""
    score = 2.0
    
    if not context.role:
        score -= 1.0
    elif len(context.role.split()) not in range(3, 6):
        score -= 0.3
        
    if context.persona_clause and len(context.persona_clause.split()) > 12:
        score -= 0.2
        
    if not context.goal or is_vague(context.goal):
        score -= 0.5
        
    return max(0, score)
```

### Component Status Indicators

```python
def get_component_status(component, validation_results):
    """Return status indicator for component"""
    
    errors = [r for r in validation_results if r.severity == 'error']
    warnings = [r for r in validation_results if r.severity == 'warning']
    
    if errors:
        return {
            'status': 'red',
            'symbol': '✗',
            'message': f"{len(errors)} error(s) must be fixed",
            'details': [e.message for e in errors[:2]]  # Show first 2
        }
    elif warnings:
        return {
            'status': 'yellow', 
            'symbol': '⚠️',
            'message': f"{len(warnings)} warning(s) to review",
            'details': [w.message for w in warnings[:2]]
        }
    else:
        return {
            'status': 'green',
            'symbol': '✓',
            'message': "Component valid",
            'details': []
        }
```

## Real-time Feedback UI Patterns

### Progressive Disclosure Pattern
```javascript
// Show feedback at appropriate detail level
const feedbackLevels = {
    minimal: {
        show: ['status_icon'],
        hide: ['details', 'suggestions', 'examples']
    },
    standard: {
        show: ['status_icon', 'primary_message'],
        hide: ['examples', 'documentation']
    },
    detailed: {
        show: ['status_icon', 'primary_message', 'suggestions', 'examples'],
        hide: ['documentation']
    },
    full: {
        show: ['all']
    }
};

// Escalate detail on hover/focus
element.addEventListener('focus', () => {
    showFeedbackLevel('detailed');
});
```

### Inline Validation Display
```html
<div class="prompt-component context-block">
    <div class="validation-status">
        <span class="status-icon yellow">⚠️</span>
        <span class="status-text">2 warnings</span>
    </div>
    
    <div class="component-content">
        <div class="field-group validated-field">
            <label>Role</label>
            <input type="text" 
                   value="experienced machine learning engineer and data scientist"
                   class="warning" />
            <div class="validation-feedback">
                <p class="message">Role should be 3-5 words</p>
                <p class="suggestion">Try: "senior ML engineer"</p>
            </div>
        </div>
    </div>
</div>
```

### Validation Summary Panel
```html
<div class="validation-summary">
    <h3>Prompt Quality: 7.5/10</h3>
    
    <div class="component-scores">
        <div class="score-item">
            <span class="component">Context</span>
            <span class="score">✓ Valid</span>
        </div>
        <div class="score-item">
            <span class="component">Request</span>
            <span class="score">⚠️ 1 warning</span>
        </div>
        <!-- ... other components ... -->
    </div>
    
    <div class="actions">
        <button class="fix-all">Auto-fix All Issues</button>
        <button class="generate">Generate Prompt</button>
    </div>
    
    <details class="issues-list">
        <summary>View All Issues (3)</summary>
        <!-- Detailed issue list -->
    </details>
</div>
```

## Custom Rule Development

### Rule Template
```yaml
rule_id: "CUSTOM_{org}_{number}"
name: "Organization-Specific Rule Name"
component: "target_component"
enabled: true
override_core_rule: null  # or ID of rule to override

# Rule definition
trigger:
  condition: "custom_validation_logic"
  custom_function: "validateCustomRule"  # Optional JS/Python function
  
validation:
  type: "custom"
  implementation: |
    function validateCustomRule(value, context) {
      // Custom logic
      return {
        valid: boolean,
        message: string,
        severity: 'error' | 'warning' | 'info',
        suggestions: string[]
      };
    }

# Integration
integration:
  load_order: 1000  # Higher numbers load later
  conflicts_with: []  # Rule IDs that conflict
  requires: []  # Rule IDs that must be active
```

### Organization-Specific Rules Example
```yaml
# Legal firm specific rules
rule_id: "CUSTOM_LAWFIRM_001"
name: "Privileged Information Check"
component: "context"
trigger:
  condition: "contains_any(background, ['client', 'case', 'matter'])"
validation:
  type: "custom"
  message: "Ensure no privileged information in prompt"
  checklist:
    - "Client names replaced with '[Client]'?"
    - "Case numbers replaced with '[Matter #]'?"
    - "Confidential facts generalized?"
    
# Financial firm specific rules  
rule_id: "CUSTOM_FINFIRM_001"
name: "Compliance Disclaimer Check"
component: "augmentations"
trigger:
  condition: "domain == 'financial' AND public_facing == true"
validation:
  type: "required_element"
  element: "compliance_disclaimer"
  message: "Public financial content requires disclaimer"
```

## Performance Optimization

### Validation Debouncing
```javascript
class ValidationDebouncer {
    constructor(delay = 300) {
        this.delay = delay;
        this.timers = new Map();
    }
    
    debounce(componentId, validationFn) {
        // Clear existing timer
        if (this.timers.has(componentId)) {
            clearTimeout(this.timers.get(componentId));
        }
        
        // Set new timer
        const timer = setTimeout(() => {
            validationFn();
            this.timers.delete(componentId);
        }, this.delay);
        
        this.timers.set(componentId, timer);
    }
}
```

### Validation Caching
from functools import lru_cache
import hashlib

class ValidationCache:
    def __init__(self, max_size=1000):
        self.max_size = max_size
        self._cache = {}
    
    def get_cache_key(self, component_data):
        """Generate stable cache key for component data"""
        # Serialize component data deterministically
        data_str = json.dumps(component_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    @lru_cache(maxsize=128)
    def validate_with_cache(self, component_type, component_data_hash):
        """Cached validation execution"""
        # Expensive validation logic here
        return self._execute_validation(component_type, component_data_hash)
    
    def validate(self, component_type, component_data):
        """Main validation entry point with caching"""
        cache_key = self.get_cache_key(component_data)
        
        # Check if we've validated this exact data before
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Perform validation
        result = self.validate_with_cache(component_type, cache_key)
        
        # Store in cache with size limit
        if len(self._cache) >= self.max_size:
            # Remove oldest entry (simple FIFO)
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        
        self._cache[cache_key] = result
        return result
```

### Parallel Validation Strategy
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelValidator:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def validate_all_components(self, prompt_data):
        """Validate all components in parallel"""
        tasks = []
        
        # Create validation tasks for each component
        for component in ['context', 'request', 'examples', 'augmentations', 'tone']:
            if component in prompt_data:
                task = asyncio.create_task(
                    self.validate_component(component, prompt_data[component])
                )
                tasks.append((component, task))
        
        # Wait for all validations to complete
        results = {}
        for component, task in tasks:
            try:
                results[component] = await asyncio.wait_for(task, timeout=2.0)
            except asyncio.TimeoutError:
                results[component] = {
                    'status': 'timeout',
                    'message': f'{component} validation timed out'
                }
        
        # Run cross-component validations after individual ones
        cross_results = await self.validate_cross_components(prompt_data, results)
        results['cross_component'] = cross_results
        
        return results
```

### Performance Monitoring
```javascript
class ValidationPerformanceMonitor {
    constructor() {
        this.metrics = {
            validationTimes: [],
            cacheHits: 0,
            cacheMisses: 0,
            timeouts: 0
        };
    }
    
    recordValidation(componentType, duration, cacheHit = false) {
        this.metrics.validationTimes.push({
            component: componentType,
            duration: duration,
            timestamp: Date.now(),
            cacheHit: cacheHit
        });
        
        if (cacheHit) {
            this.metrics.cacheHits++;
        } else {
            this.metrics.cacheMisses++;
        }
        
        // Alert if validation is consistently slow
        const recentTimes = this.metrics.validationTimes
            .filter(m => m.component === componentType)
            .slice(-10);
            
        const avgTime = recentTimes.reduce((sum, m) => sum + m.duration, 0) / recentTimes.length;
        
        if (avgTime > 500) {
            console.warn(`Slow validation detected for ${componentType}: ${avgTime}ms avg`);
        }
    }
    
    getPerformanceReport() {
        const totalValidations = this.metrics.validationTimes.length;
        const avgDuration = this.metrics.validationTimes
            .reduce((sum, m) => sum + m.duration, 0) / totalValidations;
        
        return {
            totalValidations,
            averageDuration: avgDuration,
            cacheHitRate: this.metrics.cacheHits / 
                         (this.metrics.cacheHits + this.metrics.cacheMisses),
            timeoutRate: this.metrics.timeouts / totalValidations,
            slowestComponent: this.findSlowestComponent()
        };
    }
}
```

## Rule Precedence and Conflicts

### Precedence Hierarchy
```yaml
precedence_levels:
  1_critical_safety:
    - "No PII validation"
    - "No harmful content"
    - "Legal compliance checks"
    priority: 1000
    override: "none"
    
  2_blocking_errors:
    - "Component requirement violations"
    - "Impossible constraints"
    - "Framework incompatibilities"
    priority: 900
    override: "safety_only"
    
  3_quality_warnings:
    - "Best practice violations"
    - "Optimization suggestions"
    - "Style recommendations"
    priority: 500
    override: "errors_and_above"
    
  4_info_suggestions:
    - "Alternative approaches"
    - "Enhancement ideas"
    - "Template recommendations"
    priority: 100
    override: "all"
```

### Conflict Resolution Matrix
```python
class ConflictResolver:
    def __init__(self):
        self.conflict_rules = {
            ('formal_tone', 'casual_tone'): self.resolve_tone_conflict,
            ('brief_length', 'comprehensive_depth'): self.resolve_length_depth,
            ('speed_priority', 'accuracy_priority'): self.resolve_priority_conflict
        }
    
    def resolve_conflicts(self, validation_results):
        """Resolve conflicts between validation rules"""
        conflicts = self.detect_conflicts(validation_results)
        
        for conflict in conflicts:
            rule1, rule2 = conflict['rules']
            
            # Check if we have a specific resolver
            key = (rule1.type, rule2.type)
            if key in self.conflict_rules:
                resolution = self.conflict_rules[key](rule1, rule2)
            else:
                # Generic resolution based on precedence
                resolution = self.resolve_by_precedence(rule1, rule2)
            
            # Apply resolution
            self.apply_resolution(resolution, validation_results)
        
        return validation_results
    
    def resolve_tone_conflict(self, rule1, rule2):
        """Specific resolver for tone conflicts"""
        return {
            'action': 'merge',
            'primary': rule1 if rule1.precedence > rule2.precedence else rule2,
            'modifier': 'with elements of',
            'secondary': rule2 if rule1.precedence > rule2.precedence else rule1,
            'message': f"Primary: {primary.value}, with {secondary.value} elements where appropriate"
        }
```

### Rule Learning and Adaptation
```python
class AdaptiveRuleEngine:
    def __init__(self):
        self.rule_performance = {}
        self.user_overrides = {}
        self.false_positive_threshold = 0.3
    
    def track_rule_outcome(self, rule_id, outcome):
        """Track whether a rule's warning was helpful"""
        if rule_id not in self.rule_performance:
            self.rule_performance[rule_id] = {
                'triggered': 0,
                'heeded': 0,
                'overridden': 0,
                'false_positives': 0
            }
        
        stats = self.rule_performance[rule_id]
        stats['triggered'] += 1
        
        if outcome == 'heeded':
            stats['heeded'] += 1
        elif outcome == 'overridden':
            stats['overridden'] += 1
        elif outcome == 'false_positive':
            stats['false_positives'] += 1
    
    def should_suppress_rule(self, rule_id, user_context):
        """Determine if a rule should be suppressed based on history"""
        if rule_id not in self.rule_performance:
            return False
        
        stats = self.rule_performance[rule_id]
        
        # Calculate false positive rate
        if stats['triggered'] > 10:  # Minimum sample size
            fp_rate = stats['false_positives'] / stats['triggered']
            override_rate = stats['overridden'] / stats['triggered']
            
            # Suppress if consistently overridden or false positive
            if fp_rate > self.false_positive_threshold:
                return True
            
            # Check user-specific overrides
            user_key = f"{user_context.user_id}:{rule_id}"
            if user_key in self.user_overrides:
                if self.user_overrides[user_key]['count'] > 3:
                    return True
        
        return False
    
    def get_rule_confidence(self, rule_id):
        """Return confidence level for a rule based on performance"""
        if rule_id not in self.rule_performance:
            return 1.0  # Default confidence for new rules
        
        stats = self.rule_performance[rule_id]
        if stats['triggered'] < 5:
            return 1.0  # Not enough data
        
        # Calculate confidence based on how often the rule is heeded
        heed_rate = stats['heeded'] / stats['triggered']
        fp_rate = stats['false_positives'] / stats['triggered']
        
        confidence = heed_rate * (1 - fp_rate)
        return max(0.1, min(1.0, confidence))
```

### Integration Testing for Rules
```python
import pytest

class RuleIntegrationTests:
    @pytest.fixture
    def validator(self):
        return ValidationEngine()
    
    def test_conflicting_tone_rules(self, validator):
        """Test that tone conflicts are properly detected and resolved"""
        prompt = {
            'context': {'role': 'academic researcher'},
            'tone': {'style': ['formal', 'casual', 'technical']}
        }
        
        results = validator.validate(prompt)
        
        # Should detect conflict
        assert any(r.rule_id == 'TR001' for r in results)
        
        # Should suggest resolution
        conflict_result = next(r for r in results if r.rule_id == 'TR001')
        assert 'Choose primary tone' in conflict_result.message
        assert conflict_result.severity == 'error'
    
    def test_cascade_validation(self, validator):
        """Test that fixing one issue resolves dependent issues"""
        prompt = {
            'request': {
                'tier': 1,
                'depth': 'comprehensive',
                'framework': 'detailed_analysis'
            }
        }
        
        results = validator.validate(prompt)
        
        # Should detect multiple related issues
        tier_issue = next(r for r in results if 'tier' in r.message)
        framework_issue = next(r for r in results if 'framework' in r.message)
        
        # Fix tier issue
        prompt['request']['tier'] = 7
        results2 = validator.validate(prompt)
        
        # Framework issue should be resolved
        assert not any('framework' in r.message for r in results2)
```

## Validation Analytics Dashboard

```sql
-- Track validation rule effectiveness
CREATE VIEW rule_effectiveness AS
SELECT 
    rule_id,
    COUNT(*) as total_triggers,
    SUM(CASE WHEN outcome = 'heeded' THEN 1 ELSE 0 END) as heeded_count,
    SUM(CASE WHEN outcome = 'overridden' THEN 1 ELSE 0 END) as override_count,
    SUM(CASE WHEN outcome = 'false_positive' THEN 1 ELSE 0 END) as fp_count,
    AVG(CASE WHEN outcome = 'heeded' THEN 1 ELSE 0 END) as heed_rate,
    AVG(user_satisfaction_score) as avg_satisfaction
FROM validation_events
WHERE timestamp > NOW() - INTERVAL '30 days'
GROUP BY rule_id
ORDER BY total_triggers DESC;

-- Identify problematic rule combinations
CREATE VIEW conflict_patterns AS
SELECT 
    r1.rule_id as rule_1,
    r2.rule_id as rule_2,
    COUNT(*) as co_occurrence_count,
    AVG(resolution_time) as avg_resolution_time,
    MODE() WITHIN GROUP (ORDER BY resolution_type) as common_resolution
FROM validation_conflicts
JOIN validation_events r1 ON conflicts.rule_1_id = r1.id
JOIN validation_events r2 ON conflicts.rule_2_id = r2.id
WHERE r1.timestamp > NOW() - INTERVAL '7 days'
GROUP BY r1.rule_id, r2.rule_id
HAVING COUNT(*) > 10
ORDER BY co_occurrence_count DESC;
```