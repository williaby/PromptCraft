# Create Planning Doc

Create new planning documents with proper structure, front matter, and cross-references: $ARGUMENTS

## Expected Arguments

- **Document Title**: Name of the planning document (e.g., "API Gateway Strategy", "Security Implementation Plan")
- **Document Type**: Type of planning document (e.g., "architecture", "process", "runbook", "technical-spec")

## Analysis Required

1. **Document Type Classification**: Determine appropriate template and structure
2. **Front Matter Generation**: Create proper YAML metadata based on type
3. **Content Structure**: Generate appropriate sections and headings
4. **Cross-Reference Integration**: Identify related documents for linking
5. **File Naming**: Generate proper kebab-case filename
6. **Location Determination**: Place in appropriate docs/planning/ subdirectory

## Document Types and Templates

### Architecture Documents (ADR, Technical Specifications)
**Purpose**: Technical decisions, system design, architectural patterns
**Template Sections**:
- Problem Statement / Context
- Decision Drivers / Requirements
- Considered Options
- Decision Outcome
- Consequences (Positive/Negative)
- Implementation Notes

### Process Documents (Workflows, Procedures)
**Purpose**: Operational procedures, development workflows, team processes
**Template Sections**:
- Process Overview
- Prerequisites / Requirements
- Step-by-Step Procedures
- Validation / Quality Gates
- Troubleshooting
- Related Processes

### Runbook Documents (Operational Guides)
**Purpose**: Deployment guides, maintenance procedures, incident response
**Template Sections**:
- Overview / Purpose
- Prerequisites
- Detailed Procedures
- Verification Steps
- Rollback Procedures
- Monitoring / Alerting

### Planning Documents (Project Plans, Roadmaps)
**Purpose**: Project planning, timelines, resource allocation, roadmaps
**Template Sections**:
- Executive Summary
- Objectives / Goals
- Scope / Deliverables
- Timeline / Milestones
- Resources / Dependencies
- Risk Assessment

## Front Matter Templates

### Architecture Document Front Matter
```yaml
---
title: {Document Title}
version: 1.0
status: draft
component: Architecture
tags: ["architecture", "adr", "{relevant-tech}", "{domain}"]
source: "PromptCraft-Hybrid Project"
purpose: {Single sentence describing the architectural decision or specification.}
decision_date: {YYYY-MM-DD if applicable}
stakeholders: ["{role1}", "{role2}"]
---
```

### Process Document Front Matter
```yaml
---
title: {Document Title}
version: 1.0
status: draft
component: Process
tags: ["process", "workflow", "{area}", "{team}"]
source: "PromptCraft-Hybrid Project"
purpose: {Single sentence describing the process or workflow.}
process_owner: "{Role or Team}"
review_frequency: "{monthly|quarterly|annually}"
---
```

### Runbook Document Front Matter
```yaml
---
title: {Document Title}
version: 1.0
status: draft
component: Operations
tags: ["runbook", "operations", "{system}", "{procedure}"]
source: "PromptCraft-Hybrid Project"
purpose: {Single sentence describing the operational procedure.}
execution_frequency: "{on-demand|daily|weekly|monthly}"
required_access: ["{system1}", "{system2}"]
---
```

### Planning Document Front Matter
```yaml
---
title: {Document Title}
version: 1.0
status: draft
component: Planning
tags: ["planning", "roadmap", "{area}", "{timeline}"]
source: "PromptCraft-Hybrid Project"
purpose: {Single sentence describing the planning objective.}
planning_horizon: "{short-term|medium-term|long-term}"
stakeholders: ["{role1}", "{role2}"]
---
```

## Content Templates

### Architecture Document Template
```markdown
# {Document Title}

## Problem Statement

### Context
Describe the current situation and why a decision is needed.

### Decision Drivers
- Driver 1: Explanation
- Driver 2: Explanation
- Driver 3: Explanation

## Considered Options

### Option 1: {Option Name}
- **Pros**: Benefits and advantages
- **Cons**: Drawbacks and limitations
- **Implementation**: High-level approach

### Option 2: {Option Name}
- **Pros**: Benefits and advantages
- **Cons**: Drawbacks and limitations
- **Implementation**: High-level approach

## Decision Outcome

### Chosen Option: {Selected Option}

**Rationale**: Explanation of why this option was selected.

## Consequences

### Positive Consequences
- Benefit 1: Description
- Benefit 2: Description

### Negative Consequences
- Risk 1: Description and mitigation
- Risk 2: Description and mitigation

## Implementation

### Implementation Steps
1. Step 1: Description
2. Step 2: Description
3. Step 3: Description

### Success Criteria
- Criteria 1: Measurable outcome
- Criteria 2: Measurable outcome

## References

- [Related Document](./related-doc.md)
- [External Reference](https://example.com)
```

### Process Document Template
```markdown
# {Document Title}

## Process Overview

### Purpose
Describe what this process accomplishes and why it's important.

### Scope
Define what is and isn't covered by this process.

### Roles and Responsibilities
- **Role 1**: Responsibilities
- **Role 2**: Responsibilities

## Prerequisites

### Required Access
- System 1: Access level
- System 2: Access level

### Required Knowledge
- Skill 1: Proficiency level
- Skill 2: Proficiency level

## Procedures

### Step 1: {Procedure Name}
1. Action 1: Detailed description
2. Action 2: Detailed description
3. Validation: How to verify completion

### Step 2: {Procedure Name}
1. Action 1: Detailed description
2. Action 2: Detailed description
3. Validation: How to verify completion

## Quality Gates

### Validation Checkpoints
- [ ] Checkpoint 1: Description
- [ ] Checkpoint 2: Description

### Approval Requirements
- Approver 1: Criteria
- Approver 2: Criteria

## Troubleshooting

### Common Issues
- **Issue 1**: Description and resolution
- **Issue 2**: Description and resolution

## Related Processes

- [Related Process](./related-process.md)
- [Upstream Process](./upstream-process.md)
```

## File Naming Convention

Generate filename from document title:
1. Convert to lowercase
2. Replace spaces with hyphens
3. Remove special characters
4. Add .md extension

**Examples**:
- "API Gateway Strategy" → `api-gateway-strategy.md`
- "Security Implementation Plan" → `security-implementation-plan.md`
- "Database Migration Runbook" → `database-migration-runbook.md`

## Cross-Reference Integration

### Automatic Cross-References
Based on document type and content, suggest links to:
- **Architecture docs**: Link to related ADRs and technical specs
- **Process docs**: Link to upstream/downstream processes
- **Runbooks**: Link to related procedures and monitoring
- **Planning docs**: Link to implementation documents and dependencies

### Standard References
All planning documents should reference:
- [Project Hub](./project-hub.md) - Main project navigation
- [Development Guidelines](./development.md) - Standards and conventions
- [Architecture Overview](./ADR.md) - Technical context

## Required Output

Generate complete document with:

1. **Proper Front Matter**: Type-appropriate YAML metadata
2. **Structured Content**: Template-based sections with placeholders
3. **Cross-References**: Links to related documents
4. **File Location**: Proper path in docs/planning/
5. **Naming Convention**: Kebab-case filename
6. **Status Tracking**: Initial status as "draft"

## Validation Checklist

- [ ] Front matter includes all required fields
- [ ] Document title matches H1 and front matter
- [ ] Filename follows kebab-case convention
- [ ] Content structure matches document type
- [ ] Cross-references use valid paths
- [ ] Tags are relevant and lowercase
- [ ] Purpose statement ends with period
- [ ] Stakeholders/owners are identified

## Important Notes

- Follow docs/planning/development.md standards
- Reference CLAUDE.md for development guidelines
- All new documents start with status: draft
- Include placeholder content that guides completion
- Generate meaningful cross-references based on project structure
- Ensure front matter component field matches document purpose
- Create documents that integrate with existing planning workflow
