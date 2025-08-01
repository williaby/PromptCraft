# Convert Legacy Knowledge

Migrate old knowledge files to new format with modern front matter, heading structure, and conventions: $ARGUMENTS

## Expected Arguments

- **Source File**: Path to legacy knowledge file (e.g., `knowledge/old-format/security-guide.md`)
- **Target Agent** (optional): Destination agent_id if migrating between agents

## Analysis Required

1. **Legacy Format Detection**: Identify current format and conversion requirements
2. **Content Structure Analysis**: Understand existing heading hierarchy and organization
3. **Metadata Extraction**: Extract or generate proper YAML front matter
4. **Link Modernization**: Update old reference formats and broken links
5. **Content Optimization**: Restructure for RAG chunking and atomic sections
6. **Agent Assignment**: Determine appropriate agent ownership

## Legacy Format Patterns

### Legacy ANCHOR System (Pre-2024)

```markdown
# Old Format
### ANCHOR-QR-1: Quick Reference Overview
### ANCHOR-QR-2: Implementation Details
### ANCHOR-QR-3: Best Practices

# New Format
### Quick Reference Overview
### Implementation Details
### Best Practices
```

### Legacy Front Matter (Incomplete)

```yaml
# Old Format
---
title: Security Guide
status: draft
---

# New Format
---
title: Security Implementation Guide
version: 1.0
status: published
agent_id: security_agent
tags: ['security', 'implementation', 'best-practices']
purpose: To provide comprehensive security implementation patterns.
---
```

### Legacy Link Formats

```markdown
# Old Format
See [ANCHOR-QR-2](#anchor-qr-2)
Reference: ./legacy-docs/security.md

# New Format
See [Implementation Details](#implementation-details)
Reference: knowledge/security_agent/security-patterns.md
```

## Conversion Rules

### 1. Heading Structure Modernization

**ANCHOR Reference Removal**:

```markdown
# Convert ANCHOR-XX-# format
### ANCHOR-QR-1: Topic Name → ### Topic Name
### ANCHOR-SEC-5: Security Pattern → ### Security Pattern
```

**Heading Hierarchy Validation**:

- Ensure single H1 document title
- Convert deep nesting (H4+) to H3 atomic chunks
- Group related H3 sections under appropriate H2 headings

### 2. Front Matter Generation

**Analyze Content for Metadata**:

```python
def extract_legacy_metadata(content: str) -> dict:
    """Extract metadata from legacy content."""
    metadata = {}

    # Extract title from H1 or filename
    metadata['title'] = extract_document_title(content)

    # Determine agent_id from content domain
    metadata['agent_id'] = classify_content_domain(content)

    # Generate tags from content analysis
    metadata['tags'] = extract_content_keywords(content)

    # Set initial version and status
    metadata['version'] = '1.0'
    metadata['status'] = 'draft'  # For review

    return metadata
```

**Content Domain Classification**:

```python
DOMAIN_PATTERNS = {
    'security_agent': [
        'authentication', 'authorization', 'encryption',
        'security', 'oauth', 'jwt', 'vulnerability'
    ],
    'create_agent': [
        'prompt', 'create', 'framework', 'template',
        'example', 'pattern', 'best-practice'
    ],
    'web_dev_agent': [
        'react', 'javascript', 'frontend', 'api',
        'web', 'html', 'css', 'component'
    ]
}
```

### 3. Link Modernization

**Internal Link Updates**:

```markdown
# Legacy anchor links
[See Section 2](#anchor-qr-2) → [See Implementation](#implementation)

# Legacy relative paths
./docs/security.md → knowledge/security_agent/security-patterns.md

# Legacy absolute paths
/knowledge/old/guide.md → knowledge/security_agent/guide.md
```

**Cross-Reference Resolution**:

- Identify broken links and suggest modern equivalents
- Update cross-agent references to use proper paths
- Convert legacy documentation links to current structure

### 4. Content Restructuring

**Atomic Chunk Creation**:

```markdown
# Legacy: Long sections with sub-sections
## Security Implementation
### Basic Setup
#### Step 1: Install Dependencies
#### Step 2: Configure Settings
#### Step 3: Test Connection
### Advanced Configuration
#### Custom Authentication
#### Error Handling

# Modern: Atomic H3 chunks
## Security Implementation

### Security Library Installation and Setup
Complete setup process including dependency installation,
basic configuration, and connection testing...

### Custom Authentication Configuration
Advanced authentication patterns including custom providers,
token management, and session handling...

### Security Error Handling Patterns
Comprehensive error handling for authentication failures,
authorization issues, and security exceptions...
```

## Conversion Process

### 1. Content Analysis Phase

**Structure Assessment**:

- Count heading levels and identify deep nesting
- Locate ANCHOR references and legacy patterns
- Analyze content organization and flow
- Identify agent domain alignment

**Link Inventory**:

- Catalog all internal and external links
- Identify broken or outdated references
- Map legacy paths to modern equivalents
- Check cross-reference validity

### 2. Metadata Generation Phase

**YAML Front Matter Creation**:

```yaml
---
title: {extracted_or_generated_title}
version: 1.0
status: draft
agent_id: {classified_agent_domain}
tags: {generated_from_content_analysis}
purpose: {generated_purpose_statement}
legacy_source: {original_file_path}
conversion_date: {current_date}
---
```

**Agent Classification Logic**:

1. Analyze content keywords and terminology
2. Check existing agent domain expertise
3. Consider content complexity and scope
4. Default to most relevant agent or create_agent

### 3. Content Restructuring Phase

**Heading Modernization**:

- Remove ANCHOR-XX-# prefixes
- Restructure deep nesting into atomic H3 chunks
- Ensure each H3 section is self-contained
- Group related concepts under H2 sections

**Content Optimization**:

- Break up large sections into atomic chunks
- Add missing context to isolated procedures
- Include examples and implementation details
- Ensure RAG-friendly content structure

### 4. Link Resolution Phase

**Reference Updates**:

- Convert ANCHOR links to modern heading links
- Update file paths to current knowledge base structure
- Fix broken external links where possible
- Add TODO comments for unresolvable references

## Required Output Format

### Conversion Report

```markdown
# Legacy Knowledge Conversion Report

## Source File: {legacy_file_path}

### Conversion Summary
- **Target Agent**: {agent_id}
- **Target Path**: knowledge/{agent_id}/{new_filename}.md
- **Conversion Date**: {date}
- **Status**: ✅ Successfully Converted

### Changes Made

#### Heading Structure
- ✅ Removed 8 ANCHOR-XX-# prefixes
- ✅ Converted 3 H4 sections to atomic H3 chunks
- ✅ Restructured content into 12 self-contained sections
- ⚠️ Manual review needed for section "Advanced Configuration"

#### Front Matter Generation
```yaml
# Generated YAML front matter
---
title: Security Implementation Guide
version: 1.0
status: draft
agent_id: security_agent
tags: ['security', 'authentication', 'implementation', 'oauth']
purpose: To provide comprehensive security implementation patterns and best practices.
legacy_source: knowledge/old-format/security-guide.md
conversion_date: 2024-01-15
---
```

#### Link Modernization

- ✅ Updated 12 internal ANCHOR links
- ✅ Fixed 3 broken relative path links
- ✅ Converted 2 legacy documentation references
- ⚠️ 1 external link requires validation: <https://old-domain.com/guide>

#### Content Restructuring

- ✅ Split "Security Setup" into 3 atomic chunks
- ✅ Enhanced "Error Handling" with complete context
- ✅ Added implementation examples to abstract concepts
- ✅ Ensured all H3 sections are self-contained

### Validation Results

- [ ] YAML front matter is valid
- [ ] All heading levels appropriate (H1-H3 only)
- [ ] Internal links resolve correctly
- [ ] Content chunks are atomic and complete
- [ ] Agent domain alignment confirmed

### Post-Conversion Actions Required

1. **Manual Review**: Advanced Configuration section needs domain expert review
2. **Link Validation**: Verify external link: <https://old-domain.com/guide>
3. **Content Enhancement**: Consider adding more examples to OAuth section
4. **Agent Integration**: Update security_agent knowledge index

### Quality Metrics

- **Heading Compliance**: 100% (12/12 sections follow H3 atomic pattern)
- **Link Health**: 94% (15/16 links functional)
- **Content Completeness**: 85% (most sections self-contained)
- **Agent Alignment**: 95% (strong security domain fit)

### Backup Information

**Original File Backup**: `.conversion-backups/2024-01-15/security-guide.md.backup`
**Rollback Available**: Yes, full restoration possible

```

### Content Quality Assessment
```markdown
## Content Quality Analysis

### ✅ Successful Conversions
- **OAuth Implementation**: Perfect atomic chunk with complete context
- **Error Handling Patterns**: Self-contained with examples
- **Security Best Practices**: Comprehensive coverage

### ⚠️ Needs Review
- **Advanced Configuration**: Complex section may need domain expert input
- **Integration Examples**: Could benefit from more concrete examples
- **Cross-References**: Some references to deprecated systems

### 📋 Recommendations
1. **Priority 1**: Review Advanced Configuration section with security expert
2. **Priority 2**: Add more implementation examples throughout
3. **Priority 3**: Update references to deprecated authentication systems
```

## Batch Conversion Support

### Directory-Level Conversion

```bash
# Convert entire legacy directory
/project:convert-legacy-knowledge knowledge/legacy-docs/ security_agent
```

**Batch Processing**:

- Analyze content relationships between files
- Maintain cross-references during conversion
- Generate consistent agent assignments
- Preserve content organization and flow

## Important Notes

- Conversion preserves original content meaning and intent
- Automatic backup creation before any modifications
- Agent domain classification uses content analysis and keyword matching
- Manual review recommended for complex or technical content
- Support for both individual file and batch directory conversion
- Generated front matter follows current knowledge base standards
- Link resolution uses fuzzy matching for robustness
- Content restructuring optimizes for RAG chunking and retrieval
