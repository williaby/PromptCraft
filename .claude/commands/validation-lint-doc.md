# Lint Document

Perform comprehensive document linting and compliance checking with automatic corrections for PromptCraft-Hybrid project files: $ARGUMENTS

## Analysis Required

1. **File Path and Naming Validation**: Check filename compliance with project conventions
2. **File Type Detection**: Determine document type and applicable standards
3. **YAML Front Matter Auto-Generation**: Create/fix proper metadata structure
4. **Heading Structure Auto-Correction**: Fix H1/H4+ violations automatically
5. **Markdown Linting Auto-Fix**: Apply markdownlint rules automatically
6. **Advanced Link Validation**: Fuzzy matching for broken link suggestions
7. **Content Structure Analysis**: Recommend improvements without auto-applying
8. **Cross-Reference Validation**: Verify consistency and suggest enhancements
9. **DeepSeek V3 Expert Review**: Get independent feedback on document quality and potential issues

## File Type Detection and Rules

### Knowledge Files (`knowledge/` directory)
**Auto-Corrections Applied**:
- Generate complete YAML front matter with agent_id from directory
- Fix H1 duplicates (keep only document title)
- Convert H4+ headings to H3 (preserve content)
- Apply markdownlint auto-fixes
- Fix line length and formatting issues

**Manual Review Flagged**:
- agent_id inconsistency with directory name
- Content atomicity violations (H3 sections not self-contained)
- Document scope too broad (suggest splitting)
- Missing cross-references to related agents

### Planning Documents (`docs/planning/` directory)
**Auto-Corrections Applied**:
- Generate planning-specific YAML front matter
- Fix H1/H4+ heading structure issues
- Apply markdownlint auto-fixes
- Standardize component field based on content analysis

**Manual Review Flagged**:
- Document scope mixing (planning + technical implementation)
- Missing stakeholder identification
- Content structure reorganization suggestions
- Cross-reference opportunities with related planning docs

### General Documentation (other locations)
**Auto-Corrections Applied**:
- Basic YAML front matter (if beneficial)
- Critical heading structure fixes
- Essential markdownlint violations

**Manual Review Flagged**:
- File location appropriateness
- Naming convention compliance

## Auto-Correction Capabilities

### 1. YAML Front Matter Auto-Generation
```python
# Knowledge file example
def generate_knowledge_frontmatter(file_path: str, content: str) -> dict:
    agent_id = extract_agent_from_path(file_path)  # from knowledge/agent_id/
    title = extract_h1_or_filename(content, file_path)
    tags = extract_content_keywords(content, agent_id)

    return {
        "title": title,
        "version": "1.0",
        "status": "draft",
        "agent_id": agent_id,
        "tags": tags,
        "purpose": f"To provide {detect_content_purpose(content)}."
    }

# Planning document example
def generate_planning_frontmatter(file_path: str, content: str) -> dict:
    component = classify_planning_type(content)  # Architecture|Planning|Process
    title = extract_h1_or_filename(content, file_path)

    return {
        "title": title,
        "version": "1.0",
        "status": "draft",
        "component": component,
        "tags": generate_planning_tags(content, component),
        "source": "PromptCraft-Hybrid Project",
        "purpose": f"To {detect_planning_purpose(content)}."
    }
```

### 2. Heading Structure Auto-Fixes
```markdown
# Auto-corrections applied:

## Multiple H1 → Single H1
# Original
# Document Title
# Another Title
# Third Title

# Fixed
# Document Title
## Another Title
## Third Title

## H4+ → H3 Conversion
#### Deep Section → ### Deep Section
##### Very Deep → ### Very Deep (with content note)

## Bold H1 → Clean H1
# **Bold Title** → # Bold Title
```

### 3. Markdownlint Auto-Fixes
- **MD013**: Line length violations (wrap at 120 chars)
- **MD022**: Heading spacing (add blank lines)
- **MD025**: Multiple H1 (keep only first)
- **MD032**: List spacing corrections
- **MD047**: Add trailing newlines
- **MD046**: Code block consistency

### 4. Advanced Link Validation
```python
def validate_and_suggest_links(content: str, file_path: str) -> dict:
    broken_links = find_broken_links(content)
    suggestions = {}

    for link in broken_links:
        # Fuzzy match against repository files
        candidates = fuzzy_match_files(link.target, similarity_threshold=0.7)

        # Check common path corrections
        path_fixes = suggest_path_corrections(link.target, file_path)

        suggestions[link.original] = {
            "fuzzy_matches": candidates[:3],  # Top 3 suggestions
            "path_corrections": path_fixes,
            "likely_fix": get_best_suggestion(candidates, path_fixes)
        }

    return suggestions
```

## Content Analysis and Recommendations

### Document Scope Analysis (docs/ and knowledge/ only)
```python
def analyze_document_scope(content: str, file_type: str) -> dict:
    analysis = {
        "scope_violations": [],
        "splitting_suggestions": [],
        "restructuring_recommendations": []
    }

    if file_type == "planning":
        # Check for technical implementation mixed with planning
        if detect_implementation_details(content):
            analysis["scope_violations"].append({
                "issue": "Planning document contains implementation details",
                "recommendation": "Split technical sections into separate architecture document",
                "suggested_files": ["technical-architecture.md", "implementation-guide.md"]
            })

    if file_type == "knowledge":
        # Check for non-atomic H3 sections
        non_atomic_sections = find_non_atomic_sections(content)
        for section in non_atomic_sections:
            analysis["restructuring_recommendations"].append({
                "section": section.heading,
                "issue": "H3 section is not self-contained",
                "suggestion": "Break into smaller atomic chunks or add missing context"
            })

    return analysis
```

### File Naming Convention Validation
```python
def validate_file_naming(file_path: str) -> dict:
    issues = []

    # Extract filename and check patterns
    filename = os.path.basename(file_path)
    directory = os.path.dirname(file_path)

    if "/knowledge/" in file_path:
        # Should be kebab-case.md in agent directory
        expected_pattern = r"^[a-z][a-z0-9-]*\.md$"
        if not re.match(expected_pattern, filename):
            issues.append({
                "type": "naming_violation",
                "current": filename,
                "expected": "kebab-case.md format",
                "example": "auth-best-practices.md"
            })

    elif "/docs/planning/" in file_path:
        # Should be kebab-case.md
        expected_pattern = r"^[a-z][a-z0-9-]*\.md$"
        if not re.match(expected_pattern, filename):
            issues.append({
                "type": "naming_violation",
                "current": filename,
                "expected": "kebab-case.md format",
                "example": "four-journeys.md"
            })

    return {"naming_issues": issues}
```

## DeepSeek V3 Expert Review Process

After completing all auto-corrections and analysis, request an independent review from DeepSeek Chat V3:

```markdown
**Expert Review Request**:
Please review this document for potential issues, improvements, and compliance with the PromptCraft-Hybrid standards. Focus on:

1. **Content Quality**: Clarity, accuracy, completeness
2. **Technical Accuracy**: Correct use of terminology and concepts
3. **Structure & Organization**: Logical flow and information architecture
4. **Missing Elements**: What critical information might be missing
5. **Potential Confusion**: Areas that could be misunderstood
6. **Best Practice Compliance**: Alignment with documentation standards

**Document Type**: [knowledge/planning/general]
**File Path**: [file_path]
**Purpose**: [extracted from front matter or inferred]

**Document Content**:
[full document content after auto-corrections]

**Current Analysis Results**:
[summary of auto-corrections applied and manual review flags]

Please provide constructive feedback and recommendations for improvement. Do not rewrite the content - only provide analysis and suggestions.
```

**Model Configuration**: Use `deepseek-v3` (DeepSeek Chat V3 free model) for this review to leverage its 685B parameter expertise and large context window (163K tokens).

## Required Output Format

### 1. Auto-Corrected File Content
```markdown
---
[Generated/corrected YAML front matter]
---

# [Corrected document title]

[Content with auto-fixes applied:
- Fixed heading structure
- Resolved markdownlint issues
- Corrected formatting
- All automatic corrections noted]
```

### 2. Manual Review Report
```markdown
# Document Linting Report

## File: [file_path]

### ✅ AUTO-CORRECTIONS APPLIED
- Generated YAML front matter with [details]
- Fixed [X] heading structure violations
- Resolved [Y] markdownlint issues
- Applied formatting corrections

### 🔗 LINK VALIDATION RESULTS
#### Broken Links Found: [count]
- **Link**: `./docs/quickstart.md`
  - **Status**: ❌ File not found
  - **Suggestions**:
    - `../README.md#quick-start-for-developers` (95% match)
    - `./PC_Setup.md` (78% match)
  - **Recommended Fix**: `../README.md#quick-start-for-developers`

### 📂 FILE NAMING VALIDATION
- **Current**: `four_jeurneys.md`
- **Issue**: Typo in filename + underscore usage
- **Expected**: `four-journeys.md` (kebab-case)
- **Action**: Manual rename required

### 📋 CONTENT STRUCTURE RECOMMENDATIONS
#### Document Scope Analysis
- **Issue**: Planning document contains detailed technical implementation
- **Impact**: Reduces focus and maintainability
- **Suggestion**: Split into focused documents:
  - `four-journeys.md` - User journey strategy and progression
  - `zen-mcp-architecture.md` - Technical orchestration details
  - `qdrant-architecture.md` - Database and memory architecture

#### Content Organization
- **H3 Atomicity**: 3 sections need better self-containment
- **Cross-References**: Missing links to related planning documents
- **Stakeholder Info**: Consider adding stakeholder matrix

### 🤖 DEEPSEEK V3 EXPERT REVIEW
#### Content Quality Assessment
[DeepSeek's analysis of clarity, accuracy, and completeness]

#### Technical Accuracy Review
[DeepSeek's feedback on terminology and concept usage]

#### Structure & Organization Feedback
[DeepSeek's recommendations for logical flow improvements]

#### Identified Missing Elements
[DeepSeek's suggestions for missing critical information]

#### Potential Confusion Points
[DeepSeek's identification of areas that could be misunderstood]

#### Best Practice Recommendations
[DeepSeek's assessment of alignment with documentation standards]

#### Overall Expert Assessment
[DeepSeek's summary and priority recommendations]

### 📊 COMPLIANCE SUMMARY
- **Auto-Fixed**: 8/12 issues resolved
- **Manual Review**: 4 items requiring attention
- **Expert Review**: [X] recommendations from DeepSeek V3
- **Overall Score**: 85% compliance (up from 60%)
```

## Validation Scope Restrictions

### Auto-Correction Scope
- **docs/**: Full auto-correction capabilities
- **knowledge/**: Full auto-correction capabilities
- **Other locations**: Limited to critical fixes only

### Content Analysis Scope
- **Document splitting suggestions**: docs/ and knowledge/ only
- **Content structure analysis**: docs/ and knowledge/ only
- **File naming validation**: All locations (flagged, not corrected)
- **Link validation**: All locations with fuzzy matching

## Important Notes

- All auto-corrections preserve original content meaning and intent
- File naming issues are flagged for manual correction (no auto-rename)
- Content restructuring is recommended, never automatically applied
- Link suggestions use repository-wide fuzzy matching for accuracy
- Front matter generation uses intelligent content analysis
- DeepSeek V3 review provides independent expert analysis without making changes
- Uses free DeepSeek Chat V3 model (685B parameters, 163K context) for comprehensive review
- Expert review focuses on quality, accuracy, and compliance rather than automated fixes
- Follows all CLAUDE.md and project development standards
- Provides clear before/after indication of all changes made
