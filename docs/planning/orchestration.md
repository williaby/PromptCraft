# Orchestration Architecture Deep Dive: Zen & Prefect

**Version:** 1.3
**Status:** Draft
**Audience:** Developers, AI Engineers, Architects

---

## 1. Introduction: The Dual-Orchestration Philosophy

The PromptCraft-Hybrid architecture is built on a **dual-orchestration** model, a deliberate design choice to ensure performance, reliability, and maintainability. We use two specialized engines—**Zen MCP Server** and **Prefect**—each assigned to the type of task it excels at:

* **Zen MCP Server (Real-Time Orchestration):** Manages all **online**, synchronous, user-facing tasks. Its primary concern is low-latency, intelligent coordination of AI agents to fulfill live user requests.
* **Prefect (Background Orchestration):** Manages all **offline**, asynchronous, heavy-lifting tasks. Its primary concern is the reliable, observable execution of data pipelines that prepare the knowledge environment.

This document provides a technical breakdown of each orchestrator’s function and a clear blueprint of the key components a developer needs to build.

---

## 2. Prefect: The “Writer” Implementation

Prefect’s primary role is to act as the **Writer** to our vector store. It runs a scheduled data pipeline that processes knowledge files and populates Qdrant. A developer building this component is responsible for creating a robust, configurable, and observable ingestion pipeline.

### 2.1. Core Logic (Python Pseudocode)

```python
# src/pipelines/ingestion_pipeline.py

from prefect import task, flow
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer
import yaml
import os
import uuid

# Initialize clients (global for efficiency)
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
qdrant_client = QdrantClient(host=QDRANT_HOST, port=6333)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

@task(retries=3, retry_delay_seconds=10)
def process_and_ingest_document(filepath: str) -> int:
    """
    Reads a markdown file, chunks it, creates embeddings,
    and upserts the data into Qdrant. Returns number of chunks.
    """
    with open(filepath, 'r') as f:
        content = f.read()

    # Separate YAML front matter from markdown content
    parts = content.split('---', 2)
    if len(parts) < 3:
        raise ValueError(f"File {filepath} is missing front matter.")

    metadata = yaml.safe_load(parts[1])
    markdown_content = parts[2]

    # Chunk the document based on headings
    chunks = markdown_content.split('\n## ')
    points_to_upsert = []

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # Generate embedding for the text chunk
        vector = embedding_model.encode(chunk).tolist()

        # Create the Qdrant Point object
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text_chunk": chunk,
                "metadata": metadata
            }
        )
        points_to_upsert.append(point)

    # Perform a batch upsert to the target collection
    if points_to_upsert:
        collection_name = metadata.get("agent_id")
        if not collection_name:
            raise ValueError(f"agent_id missing in {filepath}")

        qdrant_client.upsert(
            collection_name=collection_name,
            points=points_to_upsert,
            wait=True
        )

    return len(points_to_upsert)

@flow(name="Knowledge Base Ingestion")
def knowledge_ingestion_flow():
    """
    Entry point for the background orchestration.
    Finds all markdown files and processes them.
    """
    # TODO: Recursively scan the /knowledge directory for .md files
    knowledge_files = [
        "/knowledge/security_agent/auth.md",
        # ... add other paths
    ]

    total_chunks = 0
    for file in knowledge_files:
        future = process_and_ingest_document.submit(file)
        # total_chunks += future.result()

    # TODO: Add logging to report the flow outcome
    # print(f"Ingestion complete. Processed {total_chunks} chunks.")
```

### 2.2. Key Functionality & Objectives

A developer implementing the Prefect pipeline must ensure:

* **Triggering:** `knowledge_ingestion_flow` runs on a schedule (e.g., nightly) and via webhook (e.g., on Git commit).
* **File Discovery:** Recursively scan a target directory for all `.md` files.
* **Error Handling:** `process_and_ingest_document` should retry on transient errors and handle missing front matter gracefully.
* **Configuration:** Host, embedding model name, and directory path configurable via environment variables.

---

## 3. Zen MCP Server: The “Reader” Implementation

Zen’s AI agents act as the **Reader** from the vector store. A developer building an agent must implement logic to retrieve relevant knowledge from Qdrant and use it to fulfill user requests.

### 3.1. Core Logic (Python Pseudocode)

```python
# src/agents/base_agent.py & src/agents/security_agent.py

from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

class BaseAgent:
    """
    Abstract base class for all agents.
    Provides common retrieval logic.
    """
    def __init__(self, agent_id: str):
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.agent_id = agent_id

    def get_relevant_knowledge(
        self, query: str, tags: list[str] = None, limit: int = 5
    ) -> list[dict]:
        """
        Performs a hybrid search to find relevant knowledge chunks.
        """
        query_vector = self.embedding_model.encode(query).tolist()
        filter_conditions = [
            models.FieldCondition(
                key="metadata.agent_id",
                match=models.MatchValue(value=self.agent_id)
            )
        ]
        if tags:
            filter_conditions.append(
                models.FieldCondition(
                    key="metadata.tags",
                    match=models.MatchAny(any=tags)
                )
            )

        search_result = self.qdrant_client.search(
            collection_name=self.agent_id,
            query_vector=query_vector,
            query_filter=models.Filter(must=filter_conditions),
            limit=limit,
            with_payload=True
        )
        return [
            {"chunk": hit.payload["text_chunk"], "score": hit.score}
            for hit in search_result
        ]

    def execute(self, query: str, **kwargs) -> str:
        """Each agent MUST implement an execute method."""
        raise NotImplementedError

class SecurityAgent(BaseAgent):
    """Specialized agent for security topics."""
    def __init__(self):
        super().__init__(agent_id="security_agent")

    def execute(self, query: str, **kwargs) -> str:
        # 1. Retrieve relevant knowledge
        context_chunks = self.get_relevant_knowledge(query, tags=kwargs.get("tags"))

        # 2. Formulate a prompt
        prompt = f"Context: {context_chunks}\n\nQuestion: {query}\n\nAnswer:"

        # 3. Call an LLM (placeholder)
        # llm_response = call_llm(prompt)
        # return llm_response
        return "LLM response based on retrieved security context."
```

### 3.2. Key Functionality & Objectives

A developer implementing the agent architecture must ensure:

* **Agent Registry:** Mechanism to discover and register all agent classes.
* **Standard Interface:** All agents inherit from `BaseAgent`, enforce `execute` method.
* **Encapsulation:** Each agent manages its own retrieval logic.

---

## 4. The Qdrant Data Contract

The decoupling of Prefect (Writer) and Zen (Reader) relies on a strict data contract in Qdrant:

* **Collection Naming:** Each agent has a dedicated collection named after its `agent_id`.
* **Vector Size:** All vectors use the same dimension (e.g., 384 for all-MiniLM-L6-v2).
* **Payload Schema:** Each point’s payload must include:

  ```json
  {
    "text_chunk": "The actual text content...",
    "metadata": {
      "title": "Form 8867 Due Diligence Checklist",
      "version": "1.0",
      "status": "published",
      "agent_id": "irs_8867",
      "tags": ["compliance", "tax", "form 8867"],
      "purpose": "To provide a detailed checklist..."
    }
  }
  ```

---

## 5. Implementation Verification Checklist

### Prefect ("Writer")

* [ ] The `knowledge_ingestion_flow` is triggerable on a **schedule** and via **webhook**.
* [ ] All `.md` files in the knowledge directory are discovered and processed.
* [ ] YAML front matter is parsed correctly; missing metadata is handled.
* [ ] Embeddings are generated for each text chunk.
* [ ] Points are upserted into Qdrant following the **Payload Schema**.
* [ ] Logging reports success and failures per file.

### Zen MCP ("Reader")

* [ ] An **agent registry** loads and manages agent instances.
* [ ] `BaseAgent` provides knowledge retrieval logic.
* [ ] `get_relevant_knowledge` filters by `agent_id` and optional tags.
* [ ] Agents retrieve and utilize `text_chunk` from search payloads.

---

*Expert Judgment: This document outlines the core components and best practices for implementing a dual-orchestration system with Prefect and Zen MCP Server. Ensure alignment with organizational standards for configuration management, observability, and security.*
