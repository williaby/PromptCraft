# PromptCraft Usage Guide

## Overview

PromptCraft-Hybrid is a Zen-powered AI workbench that transforms user queries into accurate,
context-aware outputs through intelligent orchestration and multi-agent collaboration.
This guide covers the four progressive journeys and how to use the platform effectively.

## Quick Start

### Getting Started with PromptCraft

1. **Access the Interface**: Navigate to <http://192.168.1.205:7860> to access the Gradio UI
2. **Choose Your Journey**: Select from four progressive levels of AI assistance
3. **Enter Your Query**: Start with a simple prompt or complex requirement
4. **Review Results**: Get enhanced, structured outputs tailored to your needs

### Basic Usage Pattern

```python
# Example: Using PromptCraft for prompt enhancement
from src.core.query_counselor import QueryCounselor

counselor = QueryCounselor()
enhanced_prompt = counselor.enhance_query("Help me write a Python function")
```

## Four Progressive Journeys

PromptCraft offers four levels of AI assistance to match your needs:

### Journey 1: Quick Enhancement

- **Purpose**: Basic prompt improvement and clarification
- **Use Case**: Transform simple requests into better-structured prompts
- **Example**: "Help with Python" → "Generate a Python function with error handling and documentation"

### Journey 2: Power Templates

- **Purpose**: Template-based prompt generation with frameworks
- **Use Case**: Apply proven prompt engineering patterns
- **Example**: Use C.R.E.A.T.E. Framework for comprehensive prompt generation

### Journey 3: Light IDE Integration

- **Purpose**: Local development integration and context-aware assistance
- **Use Case**: Code analysis, documentation generation, and development workflows
- **Example**: Analyze codebase patterns and generate appropriate tests

### Journey 4: Full Automation

- **Purpose**: Complete multi-agent workflow execution
- **Use Case**: End-to-end task automation with specialized AI agents
- **Example**: Full project analysis, implementation, and documentation generation

## Core Features

### HyDE Query Enhancement

```python
# The system automatically enhances ambiguous queries
original_query = "help with authentication"
# Becomes: "Implement secure user authentication with JWT tokens, password hashing, and session management"
```

### Agent-First Design

- **Security Agent**: Handles authentication, authorization, and security best practices
- **CREATE Agent**: Implements C.R.E.A.T.E. Framework for prompt engineering
- **Documentation Agent**: Generates comprehensive technical documentation
- **Testing Agent**: Creates test suites and validation frameworks
