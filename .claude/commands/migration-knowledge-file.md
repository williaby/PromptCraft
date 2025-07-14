# Migrate Knowledge File

Move knowledge files between agents with proper metadata updates and cross-reference fixes: $ARGUMENTS

## Expected Arguments

- **Source File**: Current file path (e.g., `knowledge/create_agent/auth-guide.md`)
- **Target Agent**: Destination agent_id (e.g., `security_agent`)

## Analysis Required

1. **Source File Analysis**: Understand current file structure and content
2. **Target Agent Validation**: Ensure destination agent exists and is valid
3. **Content Relevance Assessment**: Verify content fits target agent's domain
4. **Metadata Transformation**: Update all agent-specific metadata
5. **Cross-Reference Impact**: Identify and update all references to the file
6. **Dependency Analysis**: Check for related files that should move together

## Migration Process

### 1. Pre-Migration Validation

**Source File Checks**:

- File exists and is readable
- Has proper YAML front matter
- Follows knowledge base standards
- Content is complete and published

**Target Agent Checks**:

- Agent directory exists: `/knowledge/{target_agent}/`
- Agent is registered in system
- Content domain alignment with agent expertise
- No filename conflicts in destination

**Content Relevance Assessment**:

- Does content align with target agent's domain?
- Are there overlapping capabilities?
- Will migration improve content discoverability?
- Should content be split or merged with existing files?

### 2. Metadata Transformation

**YAML Front Matter Updates**:

```yaml
# Before Migration
---
title: Authentication Best Practices
version: 1.2
status: published
agent_id: create_agent          # ← UPDATE
tags: ['auth', 'security']
purpose: Guide for secure authentication patterns.
---

# After Migration
---
title: Authentication Best Practices
version: 1.3                   # ← INCREMENT
status: published
agent_id: security_agent       # ← UPDATED
tags: ['auth', 'security', 'best-practices']  # ← ENHANCED
purpose: Guide for secure authentication patterns.
migration_from: create_agent   # ← TRACKING
migration_date: 2024-01-15     # ← TRACKING
---
```

**Required Updates**:

- `agent_id`: Change to target agent
- `version`: Increment to reflect migration
- `tags`: Enhance with target agent's taxonomy
- Add migration tracking metadata

### 3. File System Operations

**Path Changes**:

- Source: `/knowledge/{source_agent}/{filename}.md`
- Target: `/knowledge/{target_agent}/{filename}.md`

**Conflict Resolution**:

- If target file exists, propose merge or rename
- Check for similar content that could be consolidated
- Preserve version history and authorship

### 4. Cross-Reference Updates

**Internal Repository Links**:

- Find all markdown files linking to the source file
- Update relative and absolute paths
- Verify link validity after migration

**Registry Updates**:

- Update agent capability listings
- Modify knowledge base indexes
- Update any automated navigation files

**Documentation Updates**:

- Update README files in both source and target directories
- Modify any knowledge base catalogs or indexes
- Update related planning documents

### 5. Content Integration

**Target Agent Integration**:

- Review existing knowledge in target agent
- Identify potential consolidation opportunities
- Ensure content doesn't duplicate existing knowledge
- Update agent overview to reflect new capabilities

**Source Agent Cleanup**:

- Remove file from source location
- Update source agent capability listings
- Add migration note to source agent documentation
- Clean up any broken internal references

## Advanced Migration Scenarios

### Bulk File Migration

When migrating multiple related files:

```bash
# Example: Moving all authentication-related files
/project:migrate-knowledge-file knowledge/create_agent/auth-*.md security_agent
```

**Batch Operations**:

- Analyze content relationships
- Maintain logical groupings
- Update cross-references between migrated files
- Preserve content hierarchy and organization

### Content Splitting

When file contains content for multiple agents:

```markdown
# Original file: knowledge/create_agent/security-and-prompting.md

# Split into:
# knowledge/security_agent/security-patterns.md
# knowledge/create_agent/prompt-security.md
```

**Splitting Process**:

1. Identify content boundaries by domain
2. Create new files for each domain
3. Update cross-references between split files
4. Maintain content relationships and flow

### Content Merging

When migrating into existing related content:

```markdown
# Merge auth-guide.md into existing security-best-practices.md
# Preserve both content streams while eliminating duplication
```

**Merging Strategy**:

1. Analyze content overlap and gaps
2. Integrate unique content from source
3. Resolve conflicting recommendations
4. Maintain atomic H3 chunk structure

## Required Output Format

### Migration Report

```markdown
# Knowledge File Migration Report

## Migration Summary
- **Source**: knowledge/create_agent/auth-guide.md
- **Target**: knowledge/security_agent/auth-guide.md
- **Status**: ✅ Completed Successfully
- **Migration Date**: 2024-01-15

## Changes Made

### Metadata Updates
- agent_id: create_agent → security_agent
- version: 1.2 → 1.3
- tags: Enhanced with security-specific taxonomy
- Added migration tracking metadata

### File Operations
- ✅ File moved to target location
- ✅ Source file removed
- ✅ No filename conflicts
- ✅ Permissions preserved

### Cross-Reference Updates
- Updated 3 internal links in planning documents
- Fixed 2 relative links in security_agent README
- Updated knowledge base index in docs/

### Content Integration
- ✅ No content conflicts with existing files
- ✅ Enhanced security_agent capabilities
- ✅ Updated agent overview documentation

## Validation Results
- [ ] Target file exists and is readable
- [ ] YAML front matter is valid
- [ ] All cross-references resolve correctly
- [ ] No broken links remain
- [ ] Agent registry updated
- [ ] Content fits target agent domain

## Post-Migration Actions
1. ✅ Update Qdrant collection mappings
2. ✅ Refresh knowledge base embeddings
3. ⏳ Run regression tests on affected agents
4. ⏳ Update deployment configurations

## Rollback Information
**Rollback Commands** (if needed):
```bash
# Restore original file location
mv knowledge/security_agent/auth-guide.md knowledge/create_agent/auth-guide.md
# Restore original metadata (automated backup available)
```

**Backup Location**: `.migration-backups/2024-01-15/auth-guide.md.backup`

```text

### Conflict Resolution
When conflicts occur, provide resolution options:
```markdown
## ⚠️ Migration Conflicts Detected

### Filename Conflict
Target file `knowledge/security_agent/auth-guide.md` already exists.

**Resolution Options**:
1. **Merge Content**: Combine files and consolidate information
2. **Rename Source**: Migrate as `auth-guide-advanced.md`
3. **Replace Target**: Backup existing and replace with source
4. **Cancel Migration**: Resolve conflicts manually first

**Recommended**: Option 1 (Merge Content) - preserves all information

### Content Overlap
Both files cover OAuth2 implementation patterns.

**Merge Strategy**:
- Preserve unique content from both sources
- Eliminate duplicate sections
- Maintain atomic H3 chunk structure
- Cross-reference related concepts
```

## Validation Checklist

### Pre-Migration

- [ ] Source file exists and is valid
- [ ] Target agent directory exists
- [ ] Content relevance confirmed
- [ ] No critical dependencies prevent migration
- [ ] Backup strategy in place

### During Migration

- [ ] Metadata properly updated
- [ ] File operations successful
- [ ] Cross-references identified and updated
- [ ] Content conflicts resolved
- [ ] Version tracking maintained

### Post-Migration

- [ ] Target file is valid and accessible
- [ ] All links resolve correctly
- [ ] No broken references remain
- [ ] Agent capabilities updated
- [ ] Knowledge base indexes refreshed

## Important Notes

- Migration preserves full version history and authorship
- Automatic backup creation before any destructive operations
- Cross-reference updates use fuzzy matching for robustness
- Content domain validation prevents inappropriate migrations
- Support for rollback operations with detailed restoration steps
- Integration with existing knowledge base management workflows
- Compliance with all naming conventions and metadata standards
