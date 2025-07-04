# PromptCraft-Hybrid: Knowledge Base Style Guide

**Version:** 3.0
**Status:** Published
**Audience:** All Content Contributors, AI Agent Developers, Technical Writers

---

## 1. Overview

This guide establishes the official style, formatting, and structural rules for all Markdown-based knowledge files within the PromptCraft-Hybrid project. Adherence to this guide is mandatory, as it ensures two critical outcomes:

1. **Machine-Readability:** Our RAG ingestion pipelines, agent routing algorithms, and automated quality checks depend on a consistent and predictable document structure. Structure is not decoration; it is the foundation of our AI's performance.
2. **Human Clarity & Maintainability:** Following a single standard makes the knowledge base easier to read, review, and maintain over time, reducing errors and improving collaboration.

Our approach is inspired by Google's developer documentation principles, prioritizing clarity, consistency, and a structure that serves both human readers and automated systems.

---

## 2. Guiding Principles

- **Atomicity:** Each knowledge chunk (H3 section) should be as small as possible while remaining self-contained and understandable. This enables precise retrieval by agents.
- **Discoverability:** Metadata is not an afterthought; it is the primary mechanism through which agents discover and retrieve knowledge. The `agent_id` must match the agent's identifier exactly.
- **Enforceability:** These rules are designed to be validated by automated tooling (e.g., markdownlint, pre-commit hooks) to maintain quality at scale.
- **Consistency:** All naming conventions must align with the project's Development Guidelines for seamless integration.

---

## 3. Document Structure

Every knowledge file MUST follow this structure precisely.

### 3.1. File Naming and Location

All knowledge files must be stored in a directory corresponding to their `agent_id`:

```
/knowledge/{agent_id}/{kebab-case-filename}.md
```

**Naming Rules:**
- Directory name: MUST be snake_case and match the agent_id exactly
- Filename: MUST be kebab-case (lowercase with hyphens)
- Extension: MUST be `.md`

**Examples:**
- **Correct:** `/knowledge/security_agent/auth-best-practices.md`
- **Correct:** `/knowledge/irs_8867/due-diligence-checklist.md`
- **Correct:** `/knowledge/create_agent/prompt-engineering-basics.md`
- **Incorrect:** `/knowledge/SecurityAgent/Auth_Best_Practices.md`
- **Incorrect:** `/knowledge/security/auth.md` (mismatched agent_id)

### 3.2. YAML Front Matter

Every file MUST begin with a YAML front matter block. This metadata is critical for agent routing, content filtering, and the ingestion pipeline.

**Mandatory Fields:**

| Key        | Description                                      | Format                                  | Example                                      |
| ---------- | ------------------------------------------------ | --------------------------------------- | -------------------------------------------- |
| `title`    | Human-readable title of the document             | String                                  | `Security Best Practices`                    |
| `version`  | Semantic version of the document                 | String (X.Y or X.Y.Z)                   | `1.0`, `2.1.3`                               |
| `status`   | Content lifecycle stage                          | Enum: `draft`, `in-review`, `published` | `published`                                  |
| `agent_id` | ID of the primary agent (MUST match folder name) | snake_case                              | `security_agent`                             |
| `tags`     | Keywords for fine-grained retrieval              | Array of lowercase strings              | `['security', 'authentication', 'oauth2']`   |
| `purpose`  | Single sentence describing the document's goal   | String ending with period               | `To provide OAuth2 implementation patterns.` |

**Example:**

```yaml
---
title: OAuth2 Implementation Guide
version: 2.1
status: published
agent_id: security_agent
tags: ['security', 'authentication', 'oauth2', 'best_practices']
purpose: To provide secure OAuth2 implementation patterns for web applications.
---
```

### 3.3. Headings & Atomic Knowledge Chunks

The heading structure is strictly enforced to ensure a consistent chunking strategy for our RAG pipeline:

```text
# (H1): Document Title - Exactly one per file, MUST match the 'title' in front matter
## (H2): Major Section - Groups related topics
### (H3): Atomic Knowledge Chunk - Self-contained unit of knowledge
#### (H4) and below: STRICTLY PROHIBITED - Breaks chunking and retrieval accuracy
```

**Critical Rules:**
- Each H3 section MUST be completely self-contained and understandable in isolation
- H3 sections are the unit of retrieval - agents will receive individual H3 chunks
- Never assume context from other sections when writing an H3 chunk
- If information requires deeper nesting, restructure into multiple H3 sections

**Good Example:**

```markdown
# OAuth2 Implementation Guide

## Client Authentication Methods

### Client Credentials Flow

The Client Credentials flow is used for machine-to-machine authentication where no user context is required. This flow involves the client authenticating directly with the authorization server using its client ID and secret.

Implementation steps:
1. Register your application to obtain client credentials
2. Exchange credentials for an access token
3. Use the access token for API requests

### Authorization Code Flow with PKCE

The Authorization Code flow with PKCE (Proof Key for Code Exchange) is the recommended flow for public clients like SPAs and mobile apps. It provides enhanced security by eliminating the need to store client secrets.

Key components:
- Code verifier: Random string generated by client
- Code challenge: SHA256 hash of the verifier
- Authorization endpoint: Where users authenticate
```

---

## 4. Content Authoring Rules

### 4.1. Handling Complex Content

Vector databases do not reliably interpret the structure of complex visual elements. Therefore:

**Mandatory Rule:** All tables, Mermaid diagrams, images, code blocks over 20 lines, and other complex visual elements MUST be immediately preceded by a descriptive paragraph that summarizes the content.

**Table Example:**

```markdown
The following table compares three OAuth2 flows, showing their use cases, security levels, and implementation complexity:

| Flow                      | Use Case                    | Security | Complexity |
| ------------------------- | --------------------------- | -------- | ---------- |
| Client Credentials        | Machine-to-machine          | High     | Low        |
| Authorization Code + PKCE | Public clients (SPA/Mobile) | High     | Medium     |
| Implicit                  | Legacy SPAs                 | Low      | Low        |
```

**Code Example:**

```markdown
This Python function demonstrates secure password hashing using bcrypt with a cost factor of 12:

```python
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
```

### 4.2. Agent Directives

To provide explicit instructions to AI agents or the Zen MCP orchestrator, use blockquotes with defined directive types:

**Syntax:** `> **DIRECTIVE_TYPE:** Instruction content`

**Defined Directives:**

| Directive            | Purpose                                  | Example                                                           |
| -------------------- | ---------------------------------------- | ----------------------------------------------------------------- |
| `AGENT-DIRECTIVE`    | Mandatory instruction for the AI agent   | `> **AGENT-DIRECTIVE:** Always validate input before processing.` |
| `TOOL_CALL`          | Hint to execute a specific MCP tool      | `> **TOOL_CALL:** heimdall.analyze_code(file_path)`               |
| `VERBATIM-INJECTION` | Copy the following code block exactly    | `> **VERBATIM-INJECTION:** Use this configuration as-is.`         |
| `HUMAN-NOTE`         | Information for human readers only       | `> **HUMAN-NOTE:** This section is under active development.`     |
| `EXAMPLE`            | Marks content as an illustrative example | `> **EXAMPLE:** Sample implementation below.`                     |

### 4.3. Cross-References

When referencing other knowledge files or agents:

- Use the full path: `See /knowledge/web_dev_agent/react-patterns.md`
- Never use relative links that might break during chunking
- When referencing another agent's expertise: `For React-specific patterns, consult the web_dev_agent`

---

## 5. Quality Standards

### 5.1. Content Lifecycle

All content follows a defined lifecycle tracked by the `status` field:

| Status      | Description                        | Can be Ingested? | Review Required? |
| ----------- | ---------------------------------- | ---------------- | ---------------- |
| `draft`     | Initial creation, work in progress | No               | No               |
| `in-review` | Ready for peer review, PR created  | No               | Yes              |
| `published` | Approved and merged to main        | Yes              | Complete         |

### 5.2. Version Management

- Use semantic versioning in the `version` field
- Major version (X.0): Significant content changes or restructuring
- Minor version (X.Y): New sections or substantial updates
- Patch version (X.Y.Z): Typo fixes or minor clarifications

### 5.3. Automated Validation

The following checks are enforced by pre-commit hooks:

- **Structure Validation:** Correct YAML front matter with all required fields
- **Heading Hierarchy:** No H4 or deeper headings
- **File Location:** File is in correct `/knowledge/{agent_id}/` directory
- **Naming Convention:** Directory and filenames follow conventions
- **Status Check:** Only `published` content is ingested

---

## 6. Integration with Development Workflow

### 6.1. Git Workflow

Knowledge files follow the same Git workflow as code:

1. Create feature branch: `feature/<issue-number>-<description>`
2. Add/update knowledge files with `status: draft`
3. When ready, update to `status: in-review`
4. Create PR following Conventional Commits format
5. After approval, update to `status: published` before merge

### 6.2. Ingestion Pipeline

The knowledge ingestion pipeline (triggered by GitHub webhook on push to main):

1. Scans `/knowledge/` directory for all `.md` files
2. Validates YAML front matter
3. Only processes files with `status: published`
4. Chunks content by H2/H3 sections
5. Generates embeddings using SentenceTransformers
6. Upserts to Qdrant collection matching `agent_id`

### 6.3. Blue-Green Deployment

Knowledge updates follow a blue-green deployment strategy:

- Two collections per agent: `{agent_id}_blue` and `{agent_id}_green`
- Production alias: `{agent_id}_production`
- Zero-downtime updates with automatic rollback capability

---

## 7. Agent-Specific Guidelines

### 7.1. C.R.E.A.T.E. Agent (`create_agent`)

Focus on prompt engineering patterns and the C.R.E.A.T.E. framework:
- Each H3 should explain one aspect of the framework
- Include examples of good vs. bad prompts
- Provide templates for common use cases

### 7.2. Security Agent (`security_agent`)

Emphasize best practices and vulnerability prevention:
- Each H3 should address a specific security concern
- Include code examples in multiple languages
- Reference relevant compliance standards (OWASP, SOC2)

### 7.3. Domain-Specific Agents

For specialized agents (e.g., `irs_8867_agent`):
- Use domain-appropriate terminology
- Include regulatory references
- Provide step-by-step compliance checklists

---

## 8. Knowledge File Template

Use this template to create any new knowledge file:

```yaml
---
title: [Descriptive Title - Match H1]
version: 1.0
status: draft
agent_id: [snake_case_agent_id]
tags: ['tag1', 'tag2', 'tag3']
purpose: [Single sentence ending with period describing the document's goal.]
---

# [Descriptive Title - Must Match Front Matter Title]

Brief introduction paragraph explaining what this document covers and why it's important.

## [Major Topic Area]

### [Specific Atomic Concept]

> **AGENT-DIRECTIVE:** [Optional instruction for the agent when using this chunk.]

Complete, self-contained explanation of this specific concept. Remember that this H3 section may be retrieved and used in isolation, so it must make sense without context from other sections.

### [Another Atomic Concept]

Another self-contained knowledge chunk. Include examples, best practices, or implementation details as appropriate.

## [Second Major Topic Area]

### [Specific Implementation Pattern]

> **EXAMPLE:** The following demonstrates the recommended approach.

Detailed explanation with code examples or step-by-step instructions.
```

---

## 9. Common Pitfalls to Avoid

1. **Deep Nesting:** Never use H4 or deeper headings
2. **Context Dependencies:** Each H3 must stand alone
3. **Inconsistent Naming:** agent_id must match exactly across folder, file, and metadata
4. **Missing Descriptions:** Tables and code blocks without explanatory text
5. **Wrong Status:** Forgetting to update status to `published` before merge
6. **Relative References:** Using relative links that break during chunking
7. **Incorrect Tags:** Using uppercase or special characters in tags

---

## 10. References

- [Development Guidelines](/docs/planning/development.md) - For naming conventions and Git workflow
- [Architecture Decision Record](PC_ADR.md) - For technical context
- [Contributing Guide](PC_Contributing.md) - For contribution process
- [Runbook](PC_Runbook.md) - For blue-green deployment details

---

*Remember: Every knowledge chunk should be a valuable, self-contained unit that helps our agents provide accurate, contextual assistance.*
