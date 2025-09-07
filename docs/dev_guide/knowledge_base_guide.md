# Knowledge Base Guide

This guide explains how to create and manage knowledge bases for agents in the PromptCraft Hybrid System.

## 1. Knowledge Base Structure

A knowledge base is a collection of documents that an agent can use to answer queries. Each document is a text file that contains information about a specific topic.

## 2. Creating a Knowledge Base

To create a new knowledge base, create a new directory in the `knowledge` directory. The name of the directory should be the name of the knowledge base.

Inside the knowledge base directory, create a new text file for each document in the knowledge base. The name of the file should be the name of the document.

## 3. Adding Documents to a Knowledge Base

To add a new document to a knowledge base, simply create a new text file in the knowledge base directory. The document will be automatically indexed and made available to the agents.

## 4. Using a Knowledge Base in an Agent

To use a knowledge base in an agent, you can use the `KnowledgeBase` class. The `KnowledgeBase` class provides methods for searching the knowledge base and retrieving documents.

Here is an example of how to use a knowledge base in an agent:

```python
from src.core.agent import Agent
from src.core.knowledge_base import KnowledgeBase

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            name="MyAgent",
            description="A simple agent that uses a knowledge base."
        )
        self.kb = KnowledgeBase("my_knowledge_base")

    def process(self, query):
        results = self.kb.search(query)
        return results[0] if results else "I don't know."
```

In this example, the agent uses the `my_knowledge_base` knowledge base to answer queries. The agent searches the knowledge base for the query and returns the first result.
