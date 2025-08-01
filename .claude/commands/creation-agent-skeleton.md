# Create Agent Skeleton

Create complete agent directory structure with proper naming conventions, base files, and registry integration: $ARGUMENTS

## Expected Arguments

- **Agent ID**: snake_case identifier (e.g., `security_agent`, `tax_preparation_agent`)
- **Description**: Brief description of agent purpose and capabilities

## Required Analysis

1. **Naming Convention Validation**: Ensure agent_id follows snake_case pattern
2. **Directory Structure Creation**: Create proper knowledge base directory
3. **Base File Generation**: Create essential files with proper templates
4. **Registry Integration**: Add agent to registry with correct metadata
5. **Qdrant Configuration**: Generate collection schema and configuration
6. **Development Integration**: Create corresponding Python class skeleton

## Directory Structure to Create

```
knowledge/{agent_id}/
├── README.md                    # Agent overview and capabilities
├── agent-overview.md            # Main agent description
├── core-capabilities.md         # Primary functions and skills
├── examples-gallery.md          # Usage examples and demonstrations
├── best-practices.md            # Implementation guidelines
└── troubleshooting.md           # Common issues and solutions

src/agents/
├── {agent_id}.py               # Python agent implementation
└── __init__.py                 # Updated with new agent import

tests/
└── unit/
    └── test_{agent_id}.py      # Unit tests for agent
```

## File Templates

### Knowledge Base README Template

```markdown
# {Agent Name} Knowledge Base

**Agent ID**: {agent_id}
**Version**: 1.0
**Status**: Development

## Overview

This directory contains the knowledge base for the {Agent Name}, responsible for {description}.

## Knowledge Files

- `agent-overview.md` - Core agent description and capabilities
- `core-capabilities.md` - Detailed technical capabilities
- `examples-gallery.md` - Usage examples and demonstrations
- `best-practices.md` - Implementation guidelines
- `troubleshooting.md` - Common issues and solutions

## Integration

This agent integrates with:
- Zen MCP Server for orchestration
- Qdrant collection: `{agent_id}`
- Python class: `{AgentClass}`
```

### Agent Overview Template

```yaml
---
title: {Agent Name} Overview
version: 1.0
status: draft
agent_id: {agent_id}
tags: ["{category}", "agent", "overview"]
purpose: To provide comprehensive overview of {agent_id} capabilities and usage.
---

# {Agent Name} Overview

## Agent Purpose

{Description of what this agent does}

## Core Capabilities

### Primary Functions

- Function 1: Description
- Function 2: Description
- Function 3: Description

### Integration Points

> **AGENT-DIRECTIVE:** This agent integrates with Zen MCP Server for orchestration.

## Usage Patterns

### Common Workflows

Describe typical usage scenarios and workflows.

### Best Practices

Provide guidelines for optimal agent usage.
```

### Python Agent Class Template

```python
"""
{Agent Name} implementation.

This module provides the {AgentClass} class for {description}.
"""

from typing import Dict, List, Any, Optional
from src.agents.base_agent import BaseAgent
from src.core.query_counselor import QueryCounselor


class {AgentClass}(BaseAgent):
    """
    {Agent Name} for {description}.

    This agent specializes in:
    - Primary capability 1
    - Primary capability 2
    - Primary capability 3
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the {Agent Name}."""
        super().__init__(config)
        self.agent_id = "{agent_id}"
        self.name = "{Agent Name}"
        self.description = "{description}"

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a query using {agent_id} capabilities.

        Args:
            query: The user's query or request
            context: Optional context information

        Returns:
            Processed response with agent-specific insights
        """
        # Implementation placeholder
        return {
            "agent_id": self.agent_id,
            "response": "Agent implementation pending",
            "capabilities": self.get_capabilities()
        }

    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities."""
        return [
            "Capability 1",
            "Capability 2",
            "Capability 3"
        ]
```

## Registry Integration

Update `src/agents/registry.py` to include:

```python
"{agent_id}": {
    "class": "{AgentClass}",
    "module": "src.agents.{agent_id}",
    "name": "{Agent Name}",
    "description": "{description}",
    "capabilities": [
        "Primary capability 1",
        "Primary capability 2",
        "Primary capability 3"
    ],
    "knowledge_base": "knowledge/{agent_id}/",
    "qdrant_collection": "{agent_id}",
    "status": "development"
}
```

## Qdrant Collection Schema

Generate collection configuration:

```python
# config/qdrant_collections.py
"{agent_id}": {
    "vector_size": 384,  # SentenceTransformers default
    "distance": "Cosine",
    "on_disk_payload": True,
    "hnsw_config": {
        "m": 16,
        "ef_construct": 100,
        "full_scan_threshold": 10000
    },
    "optimizers_config": {
        "default_segment_number": 2,
        "max_segment_size": 200000
    }
}
```

## Required Output

1. **Directory Structure**: Create all required directories and files
2. **Base Files**: Generate all template files with proper content
3. **Registry Updates**: Add agent to registry with correct metadata
4. **Configuration**: Create Qdrant collection configuration
5. **Development Integration**: Create Python class skeleton and tests
6. **Documentation**: Generate comprehensive README and overview files

## Validation Checklist

- [ ] Agent ID follows snake_case convention
- [ ] All file names follow kebab-case convention
- [ ] YAML front matter includes all required fields
- [ ] Python class follows PascalCase with "Agent" suffix
- [ ] Knowledge files have proper agent_id consistency
- [ ] Registry entry includes all required metadata
- [ ] Qdrant collection name matches agent_id
- [ ] Test file follows naming convention

## Important Notes

- Follow all naming conventions from docs/planning/development.md
- Ensure agent_id consistency across all files and configurations
- Reference CLAUDE.md for development standards
- All knowledge files start with status: draft
- Python class must inherit from BaseAgent
- Include proper imports and type hints
- Generate meaningful placeholder content for development
