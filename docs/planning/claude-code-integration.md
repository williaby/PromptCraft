# **Reference Document: Claude Code**

**Version:** 2.0
**Status:** Published
**Audience:** All Project Members, New Developers, and Stakeholders

## **1. Overview**

**Claude Code** is the official and required IDE integration for the PromptCraft-Hybrid project. It is a powerful AI assistant that embeds directly into **Visual Studio Code (VS Code)**, our project's standard IDE. Its core purpose is to bridge the developer's local workflow with the project's central orchestration engine, the **Zen MCP Server**, eliminating context switching and providing highly relevant, AI-powered assistance.

By intercepting commands and sending them with project context to the Zen MCP, Claude Code enables developers to leverage the full power of the PromptCraft-Hybrid platform—from simple tool execution to complex, multi-agent code generation and analysis—all from within their editor.

## **2. Installation & Setup**

1.  **Installation:** Install the "Claude Code" extension directly from the VS Code Marketplace.
2.  **Configuration:** The critical setup step is configuring the extension to point to the correct Zen MCP Server endpoint. For initial setup and local development, this will be a locally hosted Zen MCP instance. For full capabilities, it will be the production server endpoint.

## **3. Core Concepts**

### **The `claude.md` Context File**

To ensure Claude Code has the necessary project-specific context, a `claude.md` file must be created at the root of the repository. This file acts as a permanent set of instructions that Claude Code automatically reads at the start of every session.

The project's `claude.md` file should include:
* **Key Files:** Pointers to core architectural components, such as `src/agents/base_agent.py` and `src/pipelines/ingestion_pipeline.py`.
* **Style Guides:** A reference to our project's development standards, including Python Black, Ruff, and the naming conventions outlined in `PC_Development.md`.
* **Testing Procedures:** Instructions on how to run the `pytest` suite.
* **Project Etiquette:** Guidelines for branch naming (e.g., `feature/add-security-agent`) and commit message formats.

### **Slash Commands and MCP Integration**

Slash commands are the primary method for interacting with the Zen MCP orchestration layer. When a developer types a command like `/tool:heimdall`, the Claude Code extension sends this request to the Zen MCP, which then routes it to the appropriate registered tool or agent.

## **4. Common Workflows & Examples**

### **Example: Security Analysis Workflow**

A developer has just written a new function that handles user input and wants to check it for common security flaws before committing.

1.  **Action:** In the relevant code file, the developer highlights the function.
2.  **Command:** They open the Claude Code input and type the following command:
    > `/tool:heimdall "Scan the highlighted function for potential SQL injection or XSS vulnerabilities based on our security agent's knowledge base."`
3.  **Process:**
    * Claude Code sends the command, the highlighted code, and the file context to the Zen MCP.
    * Zen MCP routes the request to the **Heimdall MCP** and the **Security Agent**.
    * The Security Agent retrieves relevant vulnerability patterns from its knowledge in Qdrant.
    * Heimdall analyzes the code, informed by the Security Agent's context.
4.  **Result:** A detailed security analysis is returned directly in the IDE, flagging potential issues and suggesting secure coding alternatives.

## **5. Best Practices**

To maximize the effectiveness of Claude Code, all developers should adhere to the following best practices:

* **Be Specific:** Vague prompts lead to vague results. Instead of "fix this code," provide specific instructions like, "Refactor this function to use the `get_relevant_knowledge` method from `BaseAgent` and handle potential `KeyError` exceptions."
* **Provide Full Context:** Use tab-completion to reference specific files and folders. For tasks requiring external information, paste in URLs to documentation or relevant articles.
* **Plan Complex Tasks:** For multi-step changes, first ask Claude Code to create a plan.
    > *"I need to create a new 'LegalAgent'. First, create a plan detailing the necessary files, class structure, and registration steps."*
* **Course Correct Early:** Claude Code is a collaborator. If its output starts to diverge from the goal, interrupt it, provide feedback, and guide it back on track.
* **Manage Context Window:** Use the `/clear` command between distinct tasks to reset the context window. This prevents unrelated information from previous tasks from impacting performance on a new task.

## **6. Role in the Four Journeys**

* **Journey 3 Light (Phase 1):** Provides immediate developer utility by enabling direct access to public tools (e.g., Google Search, URL Reader) and validating the core connection to the local Zen MCP.
* **Journey 3 Full Integration (Phase 3):** Unlocks the full potential of the platform by providing developers with seamless access to the entire multi-agent orchestration ecosystem, enabling context-aware, secure, and highly efficient AI-assisted development.

## **7. External Reference Links**

For further reading and official information, developers should refer to the following resources:

1.  **[VS Code Marketplace Listing](https://marketplace.visualstudio.com/items?itemName=anthropic.claude-code):** The official installation page for the VS Code extension. Use this for installation and to see version updates and reviews.
2.  **[Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices):** The authoritative guide on how to use Claude Code effectively. It covers advanced prompting, context management, and workflow optimization techniques.
3.  **[Official Overview Documentation](https://docs.anthropic.com/en/docs/claude-code/overview):** The main documentation hub for a high-level understanding of Claude Code's features and core capabilities.
