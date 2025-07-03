# PromptCraft-Hybrid Project Overview

## Purpose
PromptCraft-Hybrid is a Zen-powered AI workbench that transforms queries into accurate, context-aware outputs through intelligent orchestration and multi-agent collaboration. It implements a hybrid architecture with on-premise compute, external Qdrant vector database on Unraid, and Ubuntu VM deployment.

## Core Architecture Concepts
- **Dual-Orchestration Model**: Zen MCP Server for real-time user interactions, Prefect for background workflows
- **Four Progressive Journeys**: From simple prompt enhancement to full multi-agent automation
- **HyDE Query Enhancement**: Three-tier query analysis system for improved retrieval accuracy
- **Agent-First Design**: Specialized AI agents with dedicated knowledge bases
- **C.R.E.A.T.E. Framework**: Core prompt engineering methodology (Context, Request, Examples, Augmentations, Tone & Format, Evaluation)

## Infrastructure
- **External Qdrant Database**: 192.168.1.16:6333 (hosted on Unraid)
- **Ubuntu VM Deployment**: 192.168.1.205 (application services)
- **External Dependencies**: Qdrant runs separately on Unraid infrastructure
- **Cost-Effective Model**: Leverages external vector search with minimal cloud dependencies

## Key Features
- Four Progressive User Journeys (simple to full automation)
- Free Mode toggle for cost-conscious usage (1000 requests/day)
- Transparent pricing with real-time cost visibility
- Smart routing for best available free models
- Hybrid infrastructure balancing performance and cost