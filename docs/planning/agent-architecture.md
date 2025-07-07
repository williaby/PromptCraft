# Agent Architecture Deep Dive

**Version:** 3.0
**Status:** Draft
**Audience:** Developers, AI Engineers, Architects

---

## 1. Introduction: The Agent Philosophy

In the PromptCraft-Hybrid ecosystem, an **Agent** is an encapsulated expert with a defined interface. Rather than hard‑coding individual behaviors, we build a **reusable agent framework** that accelerates development and deployment of new experts with minimal boilerplate.

This document covers:

1. **Shared Agent Framework:** Core infrastructure built once and used across all agents.
2. **Agent Anatomy:** Agent‑specific components required to plug new experts into the framework.

Agents fall into two categories:

* **Knowledge Experts:** Reason over unstructured text (markdown, JSON).
* **Data Experts:** Query and interpret structured data sources.

---

## 2. Shared Agent Framework: Reusable Infrastructure

The shared framework lives under `src/agents/` and provides common logic for search, filtering, and execution.

### 2.1. BaseAgent Abstract Class (`src/agents/base_agent.py`)

```python
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import abc

class BaseAgent(abc.ABC):
    """
    Abstract base class for all agents.
    Provides reusable methods for semantic and structured search.
    """
    def __init__(self, agent_id: str, fallback_strategy: str = "clarify"):
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.agent_id = agent_id
        self.fallback_strategy = fallback_strategy

    def get_relevant_knowledge(
        self, query: str, limit: int = 5
    ) -> list[dict]:
        """
        Performs semantic search over text chunks.
        """
        vector = self.embedding_model.encode(query).tolist()
        results = self.qdrant_client.search(
            collection_name=self.agent_id,
            query_vector=vector,
            limit=limit,
            with_payload=True
        )
        return [{"chunk": hit.payload["text_chunk"], "score": hit.score} for hit in results]

    def get_structured_data(
        self, filters: dict, limit: int = 25
    ) -> list[dict]:
        """
        Performs filtered search on structured metadata.
        """
        # Example: use scroll or filter API based on `filters` dict
        ...

    @abc.abstractmethod
    def execute(self, query: str, **kwargs) -> str:
        """
        Entry point for each agent. Must be implemented.
        """
        pass
```

### 2.2. Agent Router (`src/routing/agent_router.py`)

* Reads `config/agents.yaml` registry.
* Scores and selects the appropriate agent for each query.
* Dispatches execution to the chosen agent.

### 2.3. Agent Registry (`config/agents.yaml`)

A YAML file listing each agent’s ID, class path, and capabilities. Example:

```yaml
- id: mtg_agent
  class: agents.mtg_agent.MTGAgent
  type: knowledge
- id: security_agent
  class: agents.security_agent.SecurityAgent
  type: knowledge
```

---

## 3. Anatomy of a Specific Agent

To add a new expert, create two components:

1. **Knowledge Component:** Files under `/knowledge/<agent_id>/` (e.g., markdown, JSON).
2. **Logic Component:** A Python class in `src/agents/` inheriting from `BaseAgent`.

### 3.1. Example: MTGAgent Plug‑in (`src/agents/mtg_agent.py`)

```python
from agents.base_agent import BaseAgent

class MTGAgent(BaseAgent):
    """
    A Magic: The Gathering expert agent.
    """
    def __init__(self):
        super().__init__(agent_id="mtg_agent", fallback_strategy="clarify")

    def execute(self, query: str, **kwargs) -> str:
        # 1. Convert query to structured filters
        filters = self._parse_query_to_filters(query)
        # 2. Retrieve data
        cards = self.get_structured_data(filters)
        if not cards:
            return "No cards match your criteria."
        # 3. Format response
        names = [c['metadata']['card_details']['name'] for c in cards]
        return f"Found {len(names)} cards: {', '.join(names)}"

    def _parse_query_to_filters(self, query: str) -> dict:
        # TODO: NLP or regex logic
        return {"colors": ["R"], "type": "Creature", "keywords": ["Haste"]}
```

---

## 4. Implementation Verification Checklist

A developer can consider the architecture complete when they can verify the following:

**Shared Framework:**

* [ ] The BaseAgent abstract class is created in `src/agents/base_agent.py` and provides reusable search methods.
* [ ] The **Agent Router** is implemented and can dynamically select an agent from the registry.
* [ ] The `config/agents.yaml` registry is implemented and used by the router.
* [ ] A mechanism for inter-agent communication is available to be passed to agents.

**Specific Agent Plug‑in:**

* [ ] A new agent can be created by adding a knowledge folder, a Python class file, and a YAML entry, without modifying the core framework.
* [ ] The new agent class successfully inherits from `BaseAgent`.
* [ ] The new agent can call the inherited `get_relevant_knowledge` and/or `get_structured_data` methods.
* [ ] The Agent Router correctly identifies and selects the new agent for relevant queries.

---
