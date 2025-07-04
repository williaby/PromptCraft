# Validate Agent Structure

Comprehensive validation of agent directory structure, naming consistency, and integration compliance: $ARGUMENTS

## Expected Arguments

- **Agent Path**: Path to agent directory (e.g., `knowledge/security_agent/` or just `security_agent`)

## Analysis Required

1. **Directory Structure Validation**: Check for required files and proper organization
2. **Naming Convention Compliance**: Verify snake_case/kebab-case consistency
3. **Agent ID Consistency**: Ensure agent_id matches across all files and configurations
4. **Knowledge File Validation**: Check YAML front matter and content structure
5. **Registry Integration**: Verify agent is properly registered
6. **Qdrant Collection**: Validate collection configuration and naming
7. **Python Implementation**: Check class definition and inheritance
8. **Cross-Reference Validation**: Ensure all references between files are correct

## Directory Structure Requirements

### Required Knowledge Base Files
```
knowledge/{agent_id}/
├── README.md                    # Agent overview (required)
├── agent-overview.md            # Core description (required)
├── core-capabilities.md         # Technical capabilities (required)
├── [additional-knowledge].md    # Domain-specific files
```

### Required Implementation Files
```
src/agents/
├── {agent_id}.py               # Python implementation (required)
├── __init__.py                 # Must import agent class

tests/
├── unit/
│   └── test_{agent_id}.py      # Unit tests (required)
└── integration/
    └── test_{agent_id}_integration.py  # Integration tests (optional)
```

## Validation Checks

### 1. Naming Convention Validation

**Agent ID Format**: `{agent_id}` must be snake_case
- ✅ Valid: `security_agent`, `tax_preparation_agent`, `web_dev_agent`
- ❌ Invalid: `SecurityAgent`, `security-agent`, `securityAgent`

**Directory Names**: Must match agent_id exactly
- Knowledge directory: `/knowledge/{agent_id}/`
- Python file: `src/agents/{agent_id}.py`
- Test file: `test_{agent_id}.py`

**File Names**: Must be kebab-case.md
- ✅ Valid: `auth-best-practices.md`, `core-capabilities.md`
- ❌ Invalid: `Auth_Best_Practices.md`, `coreCapabilities.md`

### 2. YAML Front Matter Validation

Each knowledge file must have:
```yaml
---
title: [Human readable title]
version: [X.Y format]
status: [draft|in-review|published]
agent_id: {exact_match_to_directory}
tags: [lowercase_array]
purpose: [Single sentence with period.]
---
```

**Critical Checks**:
- `agent_id` field matches directory name exactly
- `title` matches H1 heading in file
- `status` is one of approved values
- `tags` are lowercase strings
- `purpose` ends with period

### 3. Agent Class Validation

**Python Class Requirements**:
```python
class {AgentId}Agent(BaseAgent):  # PascalCase + "Agent" suffix
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.agent_id = "{agent_id}"  # Must match directory
```

**Required Methods**:
- `__init__(self, config)` - Proper initialization
- `process_query(self, query, context)` - Core processing
- `get_capabilities(self)` - Capability listing

### 4. Registry Integration Validation

Check `src/agents/registry.py` contains:
```python
"{agent_id}": {
    "class": "{AgentId}Agent",
    "module": "src.agents.{agent_id}",
    "name": "{Human Name}",
    "description": "Agent description",
    "capabilities": ["list", "of", "capabilities"],
    "knowledge_base": "knowledge/{agent_id}/",
    "qdrant_collection": "{agent_id}",
    "status": "development|active|deprecated"
}
```

### 5. Content Structure Validation

**Heading Hierarchy**: All knowledge files must follow:
- H1 (`#`): Document title only
- H2 (`##`): Major sections
- H3 (`###`): Atomic knowledge chunks
- H4+ (`####`): **PROHIBITED** - breaks RAG chunking

**Atomic Chunk Requirements**:
- Each H3 section must be self-contained
- No forward references to other sections
- Complete context within the chunk
- Includes relevant examples or implementation details

### 6. Cross-Reference Validation

**Internal Links**: Check all markdown links
- Knowledge files linking to other knowledge files
- README references to knowledge files
- Agent overview cross-references

**Registry References**: Verify
- Python class matches registry entry
- Module path is correct
- Qdrant collection name matches
- Knowledge base path is accurate

## Required Output Format

### Validation Report Structure

```markdown
# Agent Structure Validation Report

## Agent: {agent_id}

### ✅ PASSED CHECKS
- Directory structure: Complete
- Naming conventions: Compliant
- YAML front matter: Valid
- [Additional passed checks...]

### ❌ FAILED CHECKS
- Missing file: knowledge/{agent_id}/core-capabilities.md
- Invalid agent_id in: knowledge/{agent_id}/auth-guide.md (found: security_agent, expected: {agent_id})
- [Additional failed checks...]

### ⚠️ WARNINGS
- Heading structure: knowledge/{agent_id}/overview.md has H4 headings (breaks RAG chunking)
- Status inconsistency: Multiple files with status: draft (consider publishing)
- [Additional warnings...]

### 📋 RECOMMENDATIONS
1. Create missing core-capabilities.md file
2. Fix agent_id inconsistency in auth-guide.md
3. Restructure heading hierarchy in overview.md
4. [Additional recommendations...]

### 📊 COMPLIANCE SCORE
Overall: 75% (15/20 checks passed)
- Structure: 100% (5/5)
- Naming: 80% (4/5)
- Content: 60% (6/10)
```

## Specific Validation Rules

### Knowledge Base Rules
1. **Minimum Files**: agent-overview.md and core-capabilities.md required
2. **YAML Consistency**: agent_id must match directory in ALL files
3. **Heading Depth**: No H4 or deeper headings allowed
4. **Status Tracking**: Mix of draft/published is acceptable, all draft is concerning
5. **Self-Containment**: Each H3 section must be understandable alone

### Implementation Rules
1. **Class Naming**: Must be {AgentId}Agent in PascalCase
2. **Inheritance**: Must inherit from BaseAgent
3. **Agent ID**: self.agent_id must match directory name
4. **Registry Entry**: Must exist and be complete
5. **Test Coverage**: Basic test file must exist

### Integration Rules
1. **Import Path**: Agent must be importable via registry module path
2. **Qdrant Collection**: Collection name must match agent_id
3. **Knowledge Path**: Registry knowledge_base path must be valid
4. **Status Alignment**: Implementation status should align with knowledge status

## Important Notes

- This validation enforces docs/planning/development.md standards
- All checks reference CLAUDE.md requirements
- Validation supports both existing and newly created agents
- Provides actionable recommendations for fixing issues
- Compliance scoring helps prioritize remediation efforts
- Validation can be run on individual agents or entire agent directory
