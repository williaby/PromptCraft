# Deployment Guide

This guide provides a comprehensive guide for deploying and configuring the PromptCraft Hybrid System.

## 1. Prerequisites

Before you begin, ensure you have the following prerequisites installed:

* Docker
* Docker Compose
* Python 3.11+
* Poetry

## 2. Configuration

1. **Clone the repository:**

    ```bash
    git clone https://github.com/williaby/PromptCraft.git
    cd PromptCraft
    ```

2. **Create a `.env` file:**

    Create a `.env` file in the root of the project and add the following environment variables:

    ```
    QDRANT_URL=<your_qdrant_url>
    QDRANT_API_KEY=<your_qdrant_api_key>
    ```

3. **Install dependencies:**

    ```bash
    make setup
    ```

## 3. Deployment

To deploy the system, run the following command:

```bash
make dev
```

This command will start all the services using Docker Compose.

## 4. Services

The following services will be started:

* **Gradio UI:** `http://192.168.1.205:7860`
* **Zen MCP Server:** `http://192.168.1.205:3000`
* **External Qdrant Dashboard:** `http://192.168.1.16:6333/dashboard`
