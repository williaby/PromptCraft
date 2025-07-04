# **PromptCraft-Hybrid Project Hub**

This document is the central index for all project documentation, strategy, and standards. Use it to find the authoritative source for any question you have about the project's vision, architecture, and execution.

## **1. Strategic Vision (The "Why" & "What")**

This section is for understanding the business goals, user value, and overall strategy.

* [**Executive Summary**](/docs/planning/exec.md): For stakeholders. The business case, ROI, and high-level vision.
* [**The Four Journeys**](/docs/planning/four_journeys.md): For product and marketing teams. Describes the user experience and progressive value proposition.
* [**Phase 1 MVP Definition**](PC_MVP.md): Clearly defines what's included in the initial release and prioritization rationale.
* [**C.R.E.A.T.E. Framework Quick Reference**](/knowledge/create/00_quick-reference.md): The core prompt engineering methodology that powers our unique value.

## **2. Project Expectations & Standards (The "How We Work")**

This section defines the quality bar and conventions all contributors must follow. Adherence to these standards is mandatory.

* [**Knowledge File Style Guide**](/docs/planning/knowledge_style_guide.md): **Required reading for all content creators.** Defines the mandatory formatting, metadata, and structure for all Markdown files in the knowledge base to ensure machine-readability for our RAG pipeline.
* [**Development Guidelines**](/docs/planning/development.md): **Required reading for all developers.** Comprehensive guide covering naming conventions, Git workflow, code review process, and quality standards.
* [**Contributing Guide**](/CONTRIBUTING.md): Initial setup instructions, development workflow, and how to submit contributions.
* [**MCP Server Reference**](/docs/planning/MCP_Servers.md): Complete list of available MCP servers, their roles, and integration patterns.

## **3. Technical Architecture (The Technical "Why" & "How")**

This section is for architects and developers to understand the system's design and the rationale behind it.

* [**Repository Structure**](docs/planning/repomix-output.xml): XML formatted summary information regarding repository structure for LLM usage.
* [**Architecture Decision Record (ADR)**](PC_ADR.md): Documents key technical decisions and their justifications. The authoritative source for *why* the system is built the way it is.
* [**Dependency Management**](/docs/planning/development.md#8-secure-dependency-management): Section 8 details the proper way to include dependencies in the pyproject.toml file.
* [**Context7 Dependency Mapping**](docs/context7-package-reference.md): This file maps all dependencies in pyproject.toml to their corresponding context7 id for use with the context7 mcp server.

### **Phase-Based Implementation Guide**

Each phase includes comprehensive documentation divided into three focused areas: strategic overview, technical implementation, and quality assurance.

#### **Phase 1: Foundation & MVP**
* **Planning & Issues**: [Phase 1 Issues](/docs/planning/phase-1-issues.md) - GitHub issues and work breakdown
* **Strategic Overview**: [Phase 1 Overview](/docs/planning/ts-1-overview.md) - Executive summary and architectural decisions
* **Technical Implementation**: [Phase 1 Implementation](/docs/planning/ts-1-implementation.md) - Code examples and configurations
* **Quality Assurance**: [Phase 1 Testing](/docs/planning/ts-1-testing.md) - Testing strategy and validation

#### **Phase 2: Multi-Agent Orchestration**
* **Planning & Issues**: [Phase 2 Issues](/docs/planning/phase-2-issues.md) - GitHub issues and work breakdown
* **Strategic Overview**: [Phase 2 Overview](/docs/planning/ts-2-overview.md) - Executive summary and architectural decisions
* **Technical Implementation**: [Phase 2 Implementation](/docs/planning/ts-2-implementation.md) - Code examples and configurations
* **Quality Assurance**: [Phase 2 Testing](/docs/planning/ts-2-testing.md) - Testing strategy and validation

#### **Phase 3: Direct Execution**
* **Planning & Issues**: [Phase 3 Issues](/docs/planning/phase-3-issues.md) - GitHub issues and work breakdown
* **Strategic Overview**: [Phase 3 Overview](/docs/planning/ts-3-overview.md) - Executive summary and architectural decisions
* **Technical Implementation**: [Phase 3 Implementation](/docs/planning/ts-3-implementation.md) - Code examples and configurations
* **Quality Assurance**: [Phase 3 Testing](/docs/planning/ts-3-testing.md) - Testing strategy and validation

#### **Phase 4: Enterprise Features & Scaling**
* **Planning & Issues**: [Phase 4 Issues](/docs/planning/phase-4-issues.md) - GitHub issues and work breakdown
* **Strategic Overview**: [Phase 4 Overview](/docs/planning/ts-4-overview.md) - Executive summary and architectural decisions
* **Technical Implementation**: [Phase 4 Implementation](/docs/planning/ts-4-implementation.md) - Code examples and configurations
* **Quality Assurance**: [Phase 4 Testing](/docs/planning/ts-4-testing.md) - Testing strategy and validation

### **Cross-Phase Architecture Deep Dives**

* [**Orchestration Architecture**](PC_orchestration.md): Zen MCP Server integration details
* [**HyDE Query Enhancement**](PC_HYDE.md): Three-tier query analysis system
* [**Agent Architecture**](PC_agent.md): BaseAgent framework and implementation patterns
* [**Journey 3 Light Setup**](/docs/planning/journey_3_light.md): Local Claude Code integration guide

## **4. Operations & Deployment (The "How to Run It")**

This section provides practical guides for deploying and operating the system.

* [**Server Setup & Onboarding Guide**](PC_Setup.md): Step-by-step server provisioning and application deployment.
* [**Operations Runbook**](PC_Runbook.md): Standard operating procedures for knowledge base management, blue-green deployments, and emergency procedures.
* [**Deployment Automation**]: Infrastructure as Code templates and CI/CD configurations (coming from ledgerbase).

## **5. Execution & Delivery (The "What We're Doing")**

This section contains the tactical artifacts for tracking progress and work items.

* [**Project Timeline**](PC_Timeline.md): 16-week phased delivery schedule with Gantt visualization.
* [**Critical Path Dependencies**]: Visual dependency map showing blocking items across phases (see Technical Architecture section above).

### **Phase-Based Work Breakdown**

Detailed GitHub issues and milestones organized by development phase:

* [**Overall Milestones & Issues**](pc_milestones_issues.md): Complete work breakdown with 44 issues across 12 milestones
* [**Phase 1 Issues**](/docs/planning/phase-1-issues.md): Foundation and MVP implementation tasks
* [**Phase 2 Issues**](/docs/planning/phase-2-issues.md): Multi-agent orchestration tasks
* [**Phase 3 Issues**](/docs/planning/phase-3-issues.md): Direct execution capability tasks
* [**Phase 4 Issues**](/docs/planning/phase-4-issues.md): Enterprise features and scaling tasks

### **Resource Planning**

* [**Resource Allocation**]: Team structure and skill requirements by phase (TBD)

## **6. Risk Management & Quality Assurance**

This section addresses risk mitigation and quality control.

* [**Risk Register**]: Identified risks with mitigation strategies (TBD).
* [**Quality Gates**]: Phase transition criteria and approval process (TBD).
* [**Performance Benchmarks**]: Target metrics and testing procedures (TBD).
* [**Security Compliance**]: AssuredOSS usage and security audit procedures.

## **7. Communication & Stakeholder Management**

This section defines how we communicate progress and decisions.

* [**Communication Plan**]: Stakeholder updates, meeting cadences, and reporting structure (TBD).
* [**Decision Log**]: Record of major project decisions and rationales.
* [**Feedback Integration Process**]: How user feedback is collected and incorporated between phases.

---

**Quick Links for New Team Members:**
1. Start with the [Executive Summary](/docs/planning/exec.md) for context
2. Read the [Development Guidelines](/docs/planning/development.md) for standards
3. Review the [Phase 1 MVP](PC_MVP.md) to understand immediate goals
4. Check the [Project Timeline](PC_Timeline.md) to see where we are
5. Dive into the relevant phase documentation:
   - **Executives/PMs**: Review phase overview documents (e.g., [Phase 1 Overview](/docs/planning/ts-1-overview.md))
   - **Developers**: Focus on implementation documents (e.g., [Phase 1 Implementation](/docs/planning/ts-1-implementation.md))
   - **QA/Testing**: Start with testing documents (e.g., [Phase 1 Testing](/docs/planning/ts-1-testing.md))
   - **Project Management**: Check phase issues (e.g., [Phase 1 Issues](/docs/planning/phase-1-issues.md))
```

---
