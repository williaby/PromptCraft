# PromptCraft

An enterprise-grade AI assistant built on Microsoft Azure that transforms simple user queries into
standardized, high-quality, and structured prompts using a Retrieval-Augmented Generation (RAG)
architecture.

## Overview

The goal of PromptCraft is to solve the problem of inconsistent and ineffective Large Language Model
(LLM) prompts. By guiding users through the C.R.E.A.T.E. framework and enriching their requests with
verified information from a custom knowledge base, PromptCraft produces outputs that are more accurate,
reliable, and auditable.

This system is designed from the ground up to be secure, scalable, and fully automated, leveraging
best-in-class Azure services and modern DevOps practices.

## Core Features

- **Retrieval-Augmented Generation (RAG)**: Grounds the AI's responses in a secure, version-controlled
knowledge base, dramatically reducing hallucinations and improving factual accuracy.
- **Structured Prompt Engineering**: Implements the C.R.E.A.T.E. framework to systematically deconstruct
and rebuild user requests into detailed, effective prompts.
- **Secure by Design**: Utilizes Azure Key Vault for secrets management, Private Endpoints for network
isolation, and Azure Active Directory (AAD) for authentication.
- **Fully Automated Infrastructure**: All Azure resources are defined using Infrastructure as Code (Bicep)
and deployed via GitHub Actions, ensuring a repeatable and auditable environment.
- **CI/CD for Knowledge and Code**: The knowledge base and application code are automatically synchronized
and deployed via GitHub Actions, enabling seamless updates.

## Architecture

The system is built on a decoupled, serverless architecture using Microsoft Azure services:

- **User Interface**: A static web page built with HTML/CSS/JavaScript, hosted on Azure Static Web Apps,
providing the chat interface.
- **Bot and Assistant Layer**:
  - Azure Bot Service manages the user session and channel communication.
  - Azure OpenAI Assistants API hosts the core PromptCraft Pro assistant, which handles
  conversation flow and function calling.
- **Business Logic**: An Azure Function (Node.js) serves two key purposes:
  - GenerateDirectLineToken: Acts as a secure token broker, authenticating users via AAD before allowing
  them to connect to the bot.
  - GetAnchor: Retrieves specific content from the knowledge base on behalf of the assistant.
- **Data and Knowledge Layer (RAG)**:
  - Azure Blob Storage securely stores the version-controlled Markdown knowledge files.
  - Azure Cognitive Search indexes the knowledge files, using its vector search capabilities
  to find the most relevant information for the assistant.
- **Security and Identity**:
  - Azure Key Vault stores all application secrets (API keys, connection strings).
  - Azure Active Directory (AAD) secures the token-generation function.
  - Azure Private Endpoints and VNet ensure backend services are not exposed to the public internet.

## Getting Started

### Prerequisites

- Node.js (LTS version)
- Azure CLI
- pre-commit

### Installation and Setup

Clone the repository:

```bash
git clone https://github.com/williaby/PromptCraft.git
```

cd PromptCraft

Install dependencies:
The core application logic resides in an Azure Function.

### Navigate to the function's source directory

cd src/functions
npm install

Activate pre-commit hooks:
This will ensure your commits adhere to the project's quality standards.
pre-commit install

For full details on the development workflow and submitting changes, please see our Contributing
Guidelines.

## Contributing

Contributions are welcome! Whether it's a bug report, a new feature, or improvements to documentation,
we value your input. Please read our CONTRIBUTING.md to get started.

This project is governed by our Code of Conduct.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
