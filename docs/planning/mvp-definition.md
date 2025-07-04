# Phase 1 Minimum Viable Product (MVP) Definition

**Version:** 1.0
**Status:** Defined
**Audience:** Project Stakeholders, Development Team, Product Management

---

## 1. MVP Goal & Core Value Proposition

The primary goal of Phase 1 MVP is to **deliver immediate, tangible value** to two distinct user groups by launching two separate but connected journeys. This validates our core architecture and proves the platform’s value from day one.

1. **General User (Journey 1):** A standalone tool that dramatically improves interaction quality with external LLMs.
2. **Developer (Journey 3 Light):** An IDE integration that enhances workflows with tool-based assistance, proving the core MCP connection.

---

## 2. What’s in the MVP: Key Components & Deliverables

### A. User‑Facing Application (Journey 1: Quick Enhancement)

* **Web UI (Gradio):** Simple interface for query input.
* **HyDE Query Counselor:** Implements “Simple Query Counselor” from HyDE Deep Dive v2.0 to analyze query specificity.
* **C.R.E.A.T.E. Agent:** Logic and knowledge base for generating structured prompts.
* **Copy‑to‑Clipboard:** Button to copy generated prompts easily.

### B. Developer‑Facing Integration (Journey 3 Light)

* **Local Zen MCP Server:** Self‑hosted Zen MCP instance for local development.
* **Claude Code CLI Integration:** Documentation to point Claude Code CLI at local Zen MCP endpoint.
* **Public MCP Tool Routing:** Preconfigured routing to at least one public tool (e.g., Google Search).

### C. Core Backend Infrastructure

* **Qdrant Vector Database:** Stores C.R.E.A.T.E. agent knowledge.
* **Prefect Ingestion Pipeline:** Triggerable Prefect flow to load knowledge files (.md) into Qdrant.
* **Core Agent Framework:** Initial BaseAgent class and Agent Router/Registry system (one agent registered).

---

## 3. Feature Prioritization: Must‑Have vs. Nice‑to‑Have

|         Priority | Feature                     | Description                                                             | Rationale                                    |
| ---------------: | :-------------------------- | :---------------------------------------------------------------------- | :------------------------------------------- |
|    **Must‑Have** | Journey 1 UI                | Functional Gradio interface for query submission and prompt generation. | Core value for general users.                |
|    **Must‑Have** | HyDE Query Counselor        | LLM‑based analysis of every query to determine specificity.             | Essential for handling ambiguity.            |
|    **Must‑Have** | C.R.E.A.T.E. Agent Logic    | Retrieve knowledge and apply C.R.E.A.T.E. framework.                    | The “engine” of Journey 1.                   |
|    **Must‑Have** | Prefect Knowledge Ingestion | Pipeline to ingest C.R.E.A.T.E. knowledge into Qdrant.                  | Required for agent functionality.            |
|    **Must‑Have** | Local Zen MCP Setup         | Easy local run of Zen MCP server.                                       | Core requirement for Journey 3 Light.        |
|    **Must‑Have** | CLI Integration & Docs      | Clear instructions for connecting Claude Code CLI to local Zen MCP.     | Enables developer journey.                   |
|    **Must‑Have** | Google Search MCP           | Route `/tool:google` commands successfully.                             | Proves tool orchestration concept.           |
| **Nice‑to‑Have** | Advanced UI Features        | Conversation history, user accounts, or prompt saving.                  | Improves UX; Phase 2 candidate.              |
| **Nice‑to‑Have** | HyDE Caching                | Cache common query patterns to reduce LLM calls.                        | Performance optimization.                    |
| **Nice‑to‑Have** | Multiple Public MCPs        | Integrate additional public tools (e.g., DuckDuckGo, URL Reader).       | Extends routing; Phase 2 addition.           |
| **Nice‑to‑Have** | Automated Agent Scaffolding | CLI tool to generate new agent files.                                   | Simplifies agent creation; deferred Phase 2. |

---

## 4. User Stories for MVP Journeys

### Journey 1: Quick Enhancement (Persona: Business Analyst)

* **As a** Business Analyst, **I want to** enter a vague request like “I need slides for the Q3 results,” **so that** I receive a detailed C.R.E.A.T.E. prompt for a high‑quality presentation draft.
* **As a** new user, **I want** clarifying questions when I submit a generic query like “help with marketing,” **so that** I can provide necessary context.
* **As a** user in a hurry, **I want to** copy the final prompt with one click, **so that** I can paste it into another AI tool efficiently.

### Journey 3 Light: IDE Integration (Persona: Developer)

* **As a** Developer, **I want to** point my Claude Code CLI to a local Zen MCP endpoint, **so that** I can verify my orchestrator is running.
* **As a** Developer working on code, **I want to** use `/tool:google "error message"` directly in my IDE terminal, **so that** I get search results without switching contexts.
* **As a** Developer, **I want to** see search output in my terminal, **so that** I can act on information or links immediately.
