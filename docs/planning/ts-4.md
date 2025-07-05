# PromptCraft-Hybrid: Technical Specification - Phase 4

Version: 2.0
Status: Updated for v7.0 Architecture
Audience: Senior Developers, Architects, DevOps, Product Management

## 1. Introduction

### 1.1. Purpose

This document provides the complete technical specification for **Phase 4** of the PromptCraft-Hybrid platform.
Phase 4 represents the continuous expansion and maturation phase, focusing on scalability, observability, automated
agent creation, and enterprise-grade features while maintaining the 7-week delivery constraint.

### 1.2. Scope

Phase 4 implements **Continuous Enhancement and Enterprise Readiness**. This involves:

* **Automated Agent Creation** - CLI tools and templates for rapid agent deployment
* **Advanced Analytics** - Comprehensive usage analytics and performance insights
* **Enterprise Security** - SSO integration, audit logging, compliance reporting
* **Workflow Optimization** - ML-based workflow improvement suggestions
* **Custom Integrations** - Plugin system for organization-specific MCP servers
* **Production Monitoring** - Advanced observability with Grafana and alerting

### 1.3. Key Architectural Evolution (Phase 4)

Phase 4 transforms the platform into an enterprise-ready, self-improving system:

```mermaid
graph TD
    subgraph "Phase 3: Execution Platform"
        P3A[Direct Execution]
        P3B[API Security]
        P3C[State Management]
    end

    subgraph "Phase 4: Enterprise & Intelligence"
        P4A[Automated Agent Factory]
        P4B[Analytics Engine]
        P4C[Enterprise SSO]
        P4D[Workflow Optimizer]
        P4E[Custom MCP Registry]
        P4F[Advanced Monitoring]
        P4G[Compliance Engine]
    end

    P3A --> P4A & P4D
    P3B --> P4C & P4G
    P3C --> P4B & P4F

    P4A --> P4E
    P4B --> P4D
    P4C --> P4G
```

**Key Principle**: Phase 4 focuses on automation, intelligence, and enterprise needs while maintaining the rapid
delivery approach established in previous phases.

## 2. Core Technologies & Dependencies (Phase 4 Additions)

| Technology/Service | Role | Target Version | Source/Justification |
|:-------------------|:-----|:---------------|:---------------------|
| **PostgreSQL** | Analytics Database | 15-alpine | Structured data for analytics and audit logs |
| **Grafana** | Monitoring Dashboard | Latest | Visual monitoring and alerting |
| **Prometheus** | Metrics Collection | Latest | Time-series metrics for observability |
| **Keycloak** | Enterprise SSO | Latest | SAML/OAuth2 identity provider integration |
| **MLflow** | ML Model Management | Latest | Workflow optimization model tracking |
| **Typer** | CLI Framework | Latest | Agent creation and management CLI |
| **Alembic** | Database Migrations | Latest | Schema evolution for analytics DB |
| **Celery** | Background Tasks | Latest | Async processing for analytics |
| **Nginx** | Load Balancer | Latest | Production load balancing and SSL termination |

## 3. Deployment Architecture (Phase 4)

Phase 4 adds enterprise infrastructure while maintaining performance and security.

```mermaid
graph TD
    subgraph "Production Infrastructure"
        subgraph "Load Balancing Layer"
            LB[Nginx Load Balancer<br/>(SSL Termination)]
            CF[Cloudflare CDN/Security]
        end

        subgraph "Application Layer"
            API[FastAPI Gateway<br/>(Multi-Instance)]
            UI[Gradio UI<br/>(Multi-Instance)]
            Z[Zen MCP Server<br/>(Multi-Instance)]
        end

        subgraph "MCP Ecosystem"
            H[Heimdall MCP]
            GH[GitHub MCP]
            CI[Code Interpreter MCP]
            HITL[Human-in-Loop MCP]
            CUSTOM[Custom MCP Registry]
        end

        subgraph "Data Layer"
            Q[Qdrant Vector DB]
            R[Redis Cluster]
            PG[PostgreSQL<br/>(Analytics)]
        end

        subgraph "Enterprise Services"
            KC[Keycloak SSO]
            GRAF[Grafana Dashboard]
            PROM[Prometheus Metrics]
            AF[Agent Factory]
        end

        subgraph "Background Processing"
            CEL[Celery Workers]
            ML[MLflow Model Server]
            AE[Analytics Engine]
        end
    end

    subgraph "External Services"
        USERS[Enterprise Users]
        SAML[SAML/OIDC Identity Provider]
        SLACK[Slack/Teams Integration]
        AUDIT[External Audit Systems]
    end

    USERS --> CF
    CF --> LB
    LB --> API & UI

    API --> Z
    Z --> H & GH & CI & HITL & CUSTOM

    API --> Q & R & PG
    UI --> KC
    KC --> SAML

    GRAF --> PROM
    PROM --> API & Z & Q

    CEL --> PG & ML
    AE --> PG
    AF --> CUSTOM

    SLACK --> HITL
    AUDIT --> PG

    style AF fill:#e8f5e8
    style AE fill:#e3f2fd
    style KC fill:#fff3e0
    style CUSTOM fill:#f3e5f5
    style GRAF fill:#fce4ec
```

**Enterprise Enhancements:**

* **High Availability**: Multi-instance deployment with load balancing
* **Enterprise SSO**: Keycloak integration with SAML/OIDC
* **Advanced Monitoring**: Prometheus + Grafana observability stack
* **Audit Compliance**: Comprehensive audit logging and reporting
* **Scalable Processing**: Celery workers for background analytics

## 4. Data Flow Diagrams

### 4.1. Automated Agent Creation Flow

```mermaid
sequenceDiagram
    participant Admin as Platform Admin
    participant CLI as PC CLI Tool
    participant AF as Agent Factory
    participant Template as Agent Template
    participant Registry as MCP Registry
    participant Git as Git Repository
    participant CI as CI/CD Pipeline
    participant Zen as Zen MCP Server

    Admin->>CLI: pc-hybrid create-agent --domain="finance" --name="tax_advisor"
    CLI->>AF: Request agent creation with specifications
    AF->>Template: Load base agent template
    Template-->>AF: Return template structure

    AF->>AF: Generate agent-specific code
    Note over AF: - Knowledge schema<br/>- Agent class<br/>- Configuration<br/>- Tests

    AF->>Git: Create new repository with agent code
    Git-->>AF: Repository created

    AF->>Registry: Register new MCP server
    Registry-->>AF: MCP registered with metadata

    AF->>CI: Trigger build and deployment pipeline
    CI->>CI: Build Docker image
    CI->>CI: Run security scans
    CI->>CI: Deploy to development environment

    CI->>Zen: Register new agent with orchestrator
    Zen-->>CI: Agent integration confirmed

    CI-->>CLI: Deployment successful
    CLI-->>Admin: Agent "tax_advisor" ready for use

    Note over Admin,Zen: Total time: ~15 minutes for simple agents
```

### 4.2. Advanced Analytics & Learning Flow

```mermaid
sequenceDiagram
    participant User
    participant API as API Gateway
    participant Analytics as Analytics Engine
    participant ML as MLflow Model
    participant DB as PostgreSQL
    participant Grafana as Grafana Dashboard
    participant Alert as Alert Manager

    User->>API: Execute workflow
    API->>Analytics: Log execution metrics

    par Data Collection
        Analytics->>DB: Store execution data
        and
        Analytics->>DB: Store user interaction data
        and
        Analytics->>DB: Store performance metrics
    end

    Note over Analytics: Hourly batch processing

    Analytics->>ML: Analyze workflow patterns
    ML->>ML: Train optimization models
    ML-->>Analytics: Return insights and predictions

    Analytics->>DB: Store optimization recommendations

    par Monitoring & Alerting
        Grafana->>DB: Query performance metrics
        Grafana->>Grafana: Update dashboards
        and
        Alert->>DB: Check SLA violations
        Alert->>Slack: Send alert if thresholds exceeded
    end

    User->>Grafana: View analytics dashboard
    Grafana-->>User: Display insights and trends

    Note over Analytics,ML: Weekly model retraining<br/>Monthly trend analysis
```

### 4.3. Enterprise SSO Integration Flow

```mermaid
sequenceDiagram
    participant User as Enterprise User
    participant UI as Gradio UI
    participant API as API Gateway
    participant KC as Keycloak
    participant SAML as Corporate SAML IdP
    participant Audit as Audit Logger

    User->>UI: Access PromptCraft application
    UI->>KC: Redirect to SSO login
    KC->>SAML: SAML authentication request
    SAML-->>User: Corporate login page

    User->>SAML: Enter corporate credentials
    SAML->>SAML: Validate credentials
    SAML-->>KC: SAML assertion with user claims

    KC->>KC: Process SAML response
    KC->>KC: Generate JWT with enterprise claims
    KC-->>UI: Redirect with JWT token

    UI->>API: API request with JWT
    API->>KC: Validate JWT signature
    KC-->>API: Token valid + user permissions

    API->>Audit: Log authenticated access
    Audit->>DB: Store audit entry

    API-->>UI: Authorized response
    UI-->>User: Access granted to application

    Note over User,Audit: All API calls logged for compliance
```

### 4.4. Custom MCP Integration Flow

```mermaid
sequenceDiagram
    participant Dev as Organization Developer
    participant Reg as MCP Registry
    participant Val as Validation Service
    participant Deploy as Deployment Engine
    participant Zen as Zen MCP Server
    participant Monitor as Monitoring

    Dev->>Reg: Submit custom MCP specification
    Note over Dev: Includes: manifest.json<br/>Docker image<br/>API documentation

    Reg->>Val: Validate MCP specification
    Val->>Val: Check security requirements
    Val->>Val: Validate API contract
    Val->>Val: Test integration compatibility
    Val-->>Reg: Validation results

    alt Validation Passed
        Reg->>Deploy: Deploy MCP to sandbox environment
        Deploy->>Deploy: Create isolated container
        Deploy->>Deploy: Configure networking
        Deploy-->>Reg: Deployment successful

        Reg->>Zen: Register new MCP server
        Zen->>Zen: Update routing configuration
        Zen-->>Reg: Integration confirmed

        Reg->>Monitor: Add MCP to monitoring
        Monitor-->>Reg: Monitoring configured

        Reg-->>Dev: MCP deployed and available

    else Validation Failed
        Reg-->>Dev: Validation errors and requirements
    end

    Note over Dev,Monitor: Custom MCPs run in isolated environment<br/>Full monitoring and audit logging
```

## 5. API Contracts & Data Schemas

### 5.1. Agent Factory API

**Endpoint:** `POST /api/v4/admin/agents/create`

**Authentication:** Admin JWT token + SSO claims required

**Request Body:**

```json
{
  "agent_spec": {
    "name": "string (snake_case)",
    "display_name": "string",
    "description": "string",
    "domain": "string",
    "keywords": ["string"],
    "capabilities": ["string"],
    "knowledge_sources": [
      {
        "type": "markdown|json|api|database",
        "source": "string",
        "update_frequency": "daily|weekly|monthly"
      }
    ]
  },
  "deployment_config": {
    "environment": "development|staging|production",
    "resource_limits": {
      "memory": "string (e.g., '512M')",
      "cpu": "string (e.g., '0.5')"
    },
    "auto_deploy": "boolean (default: false)"
  },
  "integration_config": {
    "required_tools": ["string"],
    "optional_tools": ["string"],
    "custom_endpoints": ["string"]
  }
}
```

**Success Response (202 Accepted):**

```json
{
  "status": "accepted",
  "data": {
    "creation_id": "uuid",
    "estimated_duration_minutes": "number",
    "agent_name": "string",
    "repository_url": "string",
    "progress_endpoint": "/api/v4/admin/agents/creation/{creation_id}/status"
  },
  "next_steps": [
    "Generate agent code from template",
    "Create knowledge base schema",
    "Build and test Docker image",
    "Deploy to target environment",
    "Register with Zen orchestrator"
  ]
}
```

### 5.2. Analytics & Insights API

**Endpoint:** `GET /api/v4/analytics/insights`

**Authentication:** JWT token with analytics permissions

**Query Parameters:**

```text
?time_range=7d|30d|90d|1y
&metrics=usage,performance,costs,quality
&granularity=hour|day|week|month
&agent_filter=agent_id1,agent_id2
&user_filter=user_id1,user_id2
```

**Success Response (200 OK):**

```json
{
  "status": "success",
  "data": {
    "summary": {
      "total_queries": "number",
      "avg_response_time_ms": "number",
      "total_cost": "number",
      "user_satisfaction": "number (1-5)",
      "agent_accuracy": "number (0-1)"
    },
    "trends": {
      "query_volume": [
        {"date": "ISO8601", "count": "number"}
      ],
      "response_times": [
        {"date": "ISO8601", "p50": "number", "p95": "number", "p99": "number"}
      ],
      "cost_breakdown": [
        {"date": "ISO8601", "model_cost": "number", "infrastructure_cost": "number"}
      ]
    },
    "agent_performance": [
      {
        "agent_id": "string",
        "query_count": "number",
        "avg_response_time": "number",
        "success_rate": "number",
        "user_rating": "number",
        "cost_per_query": "number"
      }
    ],
    "optimization_recommendations": [
      {
        "type": "cost|performance|accuracy",
        "priority": "high|medium|low",
        "description": "string",
        "estimated_impact": "string",
        "implementation_effort": "low|medium|high"
      }
    ]
  },
  "metadata": {
    "generated_at": "ISO8601",
    "data_freshness": "string",
    "query_duration_ms": "number"
  }
}
```

### 5.3. Custom MCP Registry Schema

**Endpoint:** `POST /api/v4/admin/mcp/register`

**Request Body:**

```json
{
  "mcp_spec": {
    "name": "string",
    "version": "string",
    "description": "string",
    "organization": "string",
    "contact_email": "string",
    "docker_image": "string",
    "capabilities": [
      {
        "name": "string",
        "description": "string",
        "input_schema": "object",
        "output_schema": "object"
      }
    ],
    "resource_requirements": {
      "memory": "string",
      "cpu": "string",
      "storage": "string",
      "network_access": "none|internal|external"
    }
  },
  "security_config": {
    "sandbox_level": "strict|standard|permissive",
    "allowed_endpoints": ["string"],
    "data_classification": "public|internal|confidential|restricted",
    "compliance_requirements": ["SOC2", "HIPAA", "GDPR"]
  },
  "deployment_config": {
    "environment": "development|staging|production",
    "replicas": "number",
    "health_check_endpoint": "string",
    "startup_timeout_seconds": "number"
  }
}
```

**MCP Manifest Schema:**

```json
{
  "apiVersion": "mcp.promptcraft.io/v1",
  "kind": "MCPServer",
  "metadata": {
    "name": "string",
    "version": "string",
    "created_at": "ISO8601",
    "organization": "string"
  },
  "spec": {
    "image": "string",
    "port": "number",
    "resources": {
      "limits": {"memory": "string", "cpu": "string"},
      "requests": {"memory": "string", "cpu": "string"}
    },
    "capabilities": [
      {
        "name": "string",
        "endpoint": "string",
        "method": "GET|POST|PUT|DELETE",
        "parameters": "object",
        "response": "object"
      }
    ],
    "healthCheck": {
      "path": "string",
      "intervalSeconds": "number",
      "timeoutSeconds": "number"
    }
  },
  "status": {
    "phase": "pending|running|succeeded|failed",
    "conditions": [
      {
        "type": "string",
        "status": "True|False|Unknown",
        "lastTransitionTime": "ISO8601",
        "reason": "string",
        "message": "string"
      }
    ]
  }
}
```

### 5.4. Enterprise Audit Schema

**Audit Event Structure:**

```json
{
  "event_id": "uuid",
  "timestamp": "ISO8601",
  "user_id": "string",
  "organization_id": "string",
  "session_id": "string",
  "event_type": "authentication|authorization|data_access|configuration_change|execution|error",
  "event_category": "security|compliance|operational|performance",
  "severity": "info|warning|error|critical",
  "source": {
    "component": "api_gateway|zen_mcp|agent|mcp_server",
    "version": "string",
    "host": "string",
    "ip_address": "string"
  },
  "action": {
    "operation": "string",
    "resource": "string",
    "resource_id": "string",
    "method": "string",
    "endpoint": "string"
  },
  "context": {
    "user_agent": "string",
    "request_id": "string",
    "correlation_id": "string",
    "workflow_id": "string (optional)",
    "agent_id": "string (optional)"
  },
  "outcome": {
    "status": "success|failure|partial",
    "status_code": "number",
    "error_message": "string (optional)",
    "response_time_ms": "number"
  },
  "data": {
    "request_size_bytes": "number",
    "response_size_bytes": "number",
    "cost": "number (optional)",
    "sensitive_data_accessed": "boolean",
    "compliance_flags": ["string"]
  }
}
```

## 6. Component Implementation Details

### 6.1. Automated Agent Factory

```python
# src/enterprise/agent_factory.py
import os
import asyncio
import git
import docker
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from jinja2 import Environment, FileSystemLoader
import subprocess
from dataclasses import dataclass

@dataclass
class AgentSpec:
    name: str
    display_name: str
    description: str
    domain: str
    keywords: List[str]
    capabilities: List[str]
    knowledge_sources: List[Dict]

class AgentFactory:
    """Automated agent creation and deployment system"""

    def __init__(self, config: Dict):
        self.config = config
        self.template_env = Environment(
            loader=FileSystemLoader('templates/agent'),
            trim_blocks=True,
            lstrip_blocks=True
        )
        self.docker_client = docker.from_env()
        self.git_base_url = config.get('git_base_url', 'https://github.com/your-org')
        self.registry_url = config.get('registry_url', 'localhost:5000')

    async def create_agent(self, agent_spec: AgentSpec, deployment_config: Dict) -> str:
        """Create complete agent from specification"""
        creation_id = f"agent_creation_{agent_spec.name}_{int(time.time())}"

        try:
            # Step 1: Generate agent code
            agent_code = await self._generate_agent_code(agent_spec)

            # Step 2: Create repository
            repo_url = await self._create_repository(agent_spec, agent_code)

            # Step 3: Generate knowledge schema
            await self._generate_knowledge_schema(agent_spec, repo_url)

            # Step 4: Create Docker configuration
            await self._create_docker_config(agent_spec, repo_url)

            # Step 5: Generate tests
            await self._generate_tests(agent_spec, repo_url)

            # Step 6: Build and deploy
            if deployment_config.get('auto_deploy', False):
                await self._build_and_deploy(agent_spec, repo_url, deployment_config)

            # Step 7: Register with MCP registry
            await self._register_mcp(agent_spec, repo_url)

            return creation_id

        except Exception as e:
            await self._cleanup_failed_creation(creation_id)
            raise AgentCreationError(f"Failed to create agent {agent_spec.name}: {str(e)}")

    async def _generate_agent_code(self, spec: AgentSpec) -> Dict[str, str]:
        """Generate agent code from templates"""

        # Generate main agent class
        agent_template = self.template_env.get_template('agent_class.py.j2')
        agent_code = agent_template.render(
            agent_name=spec.name,
            display_name=spec.display_name,
            description=spec.description,
            keywords=spec.keywords,
            capabilities=spec.capabilities,
            class_name=self._to_pascal_case(spec.name)
        )

        # Generate configuration
        config_template = self.template_env.get_template('agent_config.yaml.j2')
        config_code = config_template.render(
            agent_id=spec.name,
            display_name=spec.display_name,
            description=spec.description,
            domain=spec.domain,
            keywords=spec.keywords,
            capabilities=spec.capabilities
        )

        # Generate README
        readme_template = self.template_env.get_template('README.md.j2')
        readme_code = readme_template.render(
            agent_name=spec.display_name,
            description=spec.description,
            domain=spec.domain,
            keywords=spec.keywords
        )

        # Generate requirements.txt
        requirements = [
            "promptcraft-sdk>=1.0.0",
            "qdrant-client>=1.9.0",
            "sentence-transformers>=2.2.0",
            "pydantic>=2.0.0",
            "asyncio>=3.4.0"
        ]

        # Add domain-specific dependencies
        if spec.domain == "security":
            requirements.extend(["bandit>=1.7.0", "safety>=2.0.0"])
        elif spec.domain == "web_development":
            requirements.extend(["requests>=2.28.0", "beautifulsoup4>=4.11.0"])

        return {
            "src/agent.py": agent_code,
            "config/config.yaml": config_code,
            "README.md": readme_code,
            "requirements.txt": "\n".join(requirements),
            "pyproject.toml": self._generate_pyproject(spec),
            "Dockerfile": self._generate_dockerfile(spec)
        }

    async def _create_repository(self, spec: AgentSpec, agent_code: Dict[str, str]) -> str:
        """Create Git repository with agent code"""
        repo_name = f"agent-{spec.name}"
        repo_path = Path(f"/tmp/{repo_name}")

        # Initialize repository
        repo = git.Repo.init(repo_path)

        # Create directory structure
        (repo_path / "src").mkdir(exist_ok=True)
        (repo_path / "config").mkdir(exist_ok=True)
        (repo_path / "knowledge").mkdir(exist_ok=True)
        (repo_path / "tests").mkdir(exist_ok=True)

        # Write generated files
        for file_path, content in agent_code.items():
            full_path = repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)

        # Add and commit files
        repo.index.add([str(p.relative_to(repo_path)) for p in repo_path.rglob("*") if p.is_file()])
        repo.index.commit(f"Initial commit for {spec.display_name} agent")

        # Push to remote (if configured)
        if self.config.get('git_auto_push', False):
            remote_url = f"{self.git_base_url}/{repo_name}.git"
            origin = repo.create_remote('origin', remote_url)
            origin.push(refspec='main:main')
            return remote_url

        return str(repo_path)

    async def _generate_knowledge_schema(self, spec: AgentSpec, repo_url: str) -> None:
        """Generate knowledge base schema and sample files"""

        schema_template = self.template_env.get_template('knowledge_schema.json.j2')
        schema = schema_template.render(
            agent_id=spec.name,
            domain=spec.domain,
            knowledge_sources=spec.knowledge_sources
        )

        # Create sample knowledge file
        sample_template = self.template_env.get_template('sample_knowledge.md.j2')
        sample_knowledge = sample_template.render(
            agent_name=spec.display_name,
            domain=spec.domain,
            agent_id=spec.name
        )

        # Write to repository
        repo_path = Path(repo_url) if repo_url.startswith('/') else Path(f"/tmp/agent-{spec.name}")

        (repo_path / "knowledge" / "schema.json").write_text(schema)
        (repo_path / "knowledge" / "getting-started.md").write_text(sample_knowledge)

        # Create ingestion script
        ingestion_template = self.template_env.get_template('ingestion_script.py.j2')
        ingestion_script = ingestion_template.render(agent_id=spec.name)
        (repo_path / "scripts" / "ingest_knowledge.py").write_text(ingestion_script)

    async def _build_and_deploy(self, spec: AgentSpec, repo_url: str, deployment_config: Dict):
        """Build Docker image and deploy agent"""

        repo_path = Path(repo_url) if repo_url.startswith('/') else Path(f"/tmp/agent-{spec.name}")
        image_tag = f"{self.registry_url}/agent-{spec.name}:latest"

        # Build Docker image
        try:
            self.docker_client.images.build(
                path=str(repo_path),
                tag=image_tag,
                dockerfile="Dockerfile",
                rm=True
            )

            # Push to registry if configured
            if self.config.get('docker_auto_push', False):
                self.docker_client.images.push(image_tag)

            # Deploy using deployment config
            await self._deploy_agent_container(spec, image_tag, deployment_config)

        except docker.errors.BuildError as e:
            raise AgentCreationError(f"Docker build failed: {str(e)}")

    async def _deploy_agent_container(self, spec: AgentSpec, image_tag: str, deployment_config: Dict):
        """Deploy agent container to target environment"""

        container_config = {
            'image': image_tag,
            'name': f"agent-{spec.name}",
            'environment': {
                'AGENT_ID': spec.name,
                'QDRANT_HOST': os.getenv('QDRANT_HOST', 'localhost'),
                'LOG_LEVEL': 'INFO'
            },
            'labels': {
                'promptcraft.agent': spec.name,
                'promptcraft.domain': spec.domain,
                'promptcraft.auto-created': 'true'
            },
            'restart_policy': {'Name': 'unless-stopped'},
            'detach': True
        }

        # Apply resource limits
        if 'resource_limits' in deployment_config:
            limits = deployment_config['resource_limits']
            container_config['mem_limit'] = limits.get('memory', '512m')
            container_config['cpu_period'] = 100000
            container_config['cpu_quota'] = int(float(limits.get('cpu', '0.5')) * 100000)

        # Deploy container
        try:
            container = self.docker_client.containers.run(**container_config)

            # Wait for container to be healthy
            await self._wait_for_container_health(container, timeout=120)

            return container.id

        except docker.errors.ContainerError as e:
            raise AgentCreationError(f"Container deployment failed: {str(e)}")

    async def _register_mcp(self, spec: AgentSpec, repo_url: str):
        """Register agent as MCP server with Zen orchestrator"""

        mcp_manifest = {
            'apiVersion': 'mcp.promptcraft.io/v1',
            'kind': 'MCPServer',
            'metadata': {
                'name': f"agent-{spec.name}",
                'version': '1.0.0',
                'organization': 'auto-generated',
                'created_at': datetime.now().isoformat()
            },
            'spec': {
                'image': f"{self.registry_url}/agent-{spec.name}:latest",
                'port': 8000,
                'capabilities': [
                    {
                        'name': cap,
                        'endpoint': f'/api/v1/{cap.replace(" ", "_").lower()}',
                        'method': 'POST'
                    } for cap in spec.capabilities
                ],
                'healthCheck': {
                    'path': '/health',
                    'intervalSeconds': 30,
                    'timeoutSeconds': 5
                }
            }
        }

        # Register with MCP registry
        registry_client = MCPRegistryClient(self.config['mcp_registry_url'])
        await registry_client.register_mcp(mcp_manifest)

        # Update Zen orchestrator configuration
        zen_client = ZenOrchestratorClient(self.config['zen_mcp_url'])
        await zen_client.add_agent_config({
            'agent_id': spec.name,
            'class_path': f'agents.{spec.name}.{self._to_pascal_case(spec.name)}Agent',
            'description': spec.description,
            'keywords': spec.keywords,
            'mcp_server': f"agent-{spec.name}"
        })

    def _to_pascal_case(self, snake_str: str) -> str:
        """Generate pyproject.toml for the agent"""
        return f"""[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "promptcraft-agent-{spec.name}"
version = "1.0.0"
description = "{spec.description}"
authors = [
    {{name = "PromptCraft Agent Factory", email = "agents@promptcraft.io"}}
]
dependencies = [
    "promptcraft-sdk>=1.0.0",
    "qdrant-client>=1.9.0",
    "sentence-transformers>=2.2.0",
    "pydantic>=2.0.0",
    "asyncio>=3.4.0"
]

[project.optional-dependencies]
dev = ["pytest>=7.0.0", "black>=22.0.0", "ruff>=0.1.0"]

[tool.black]
line-length = 88
target-version = ['py311']

[tool.ruff]
target-version = "py311"
line-length = 88
"""

    def _generate_dockerfile(self, spec: AgentSpec) -> str:
        """Generate Dockerfile for the agent"""
        return f"""FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    git \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy agent code
COPY src/ ./src/
COPY config/ ./config/
COPY knowledge/ ./knowledge/

# Create non-root user
RUN useradd --create-home --shell /bin/bash agent
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start agent
CMD ["python", "-m", "src.agent"]
"""

class AgentCreationError(Exception):
    """Custom exception for agent creation failures"""
    pass
```

### 6.2. Advanced Analytics Engine

```python
# src/enterprise/analytics_engine.py
import asyncio
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import mlflow
import mlflow.sklearn
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedAnalyticsEngine:
    """Enterprise analytics and insights engine"""

    def __init__(self, config: Dict):
        self.config = config
        self.db_engine = create_engine(config['analytics_db_url'])
        self.Session = sessionmaker(bind=self.db_engine)
        self.mlflow_client = mlflow.tracking.MlflowClient(config.get('mlflow_url'))

        # Initialize ML models
        self.usage_predictor = None
        self.anomaly_detector = None
        self.cost_optimizer = None

        # Analytics cache
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)

    async def generate_usage_insights(self, time_range: str = "30d",
                                    filters: Optional[Dict] = None) -> Dict:
        """Generate comprehensive usage insights"""

        cache_key = f"usage_insights_{time_range}_{hash(str(filters))}"
        if self._is_cached(cache_key):
            return self.cache[cache_key]

        # Calculate time boundaries
        end_date = datetime.now()
        days = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}[time_range]
        start_date = end_date - timedelta(days=days)

        with self.Session() as session:
            # Query execution data
            query = text("""
                SELECT
                    DATE(created_at) as date,
                    agent_id,
                    user_id,
                    status,
                    processing_time_ms,
                    total_cost,
                    steps_completed,
                    security_issues_found,
                    test_success_rate
                FROM workflow_executions
                WHERE created_at >= :start_date
                AND created_at <= :end_date
            """)

            if filters:
                query = self._apply_filters(query, filters)

            df = pd.read_sql(query, session.bind, params={
                'start_date': start_date,
                'end_date': end_date
            })

        if df.empty:
            return {"error": "No data available for the specified time range"}

        # Calculate insights
        insights = {
            "summary": self._calculate_summary_metrics(df),
            "trends": self._calculate_trends(df),
            "agent_performance": self._analyze_agent_performance(df),
            "user_behavior": self._analyze_user_behavior(df),
            "cost_analysis": self._analyze_costs(df),
            "quality_metrics": self._analyze_quality_metrics(df),
            "optimization_recommendations": await self._generate_optimization_recommendations(df)
        }

        self.cache[cache_key] = insights
        return insights

    def _calculate_summary_metrics(self, df: pd.DataFrame) -> Dict:
        """Calculate high-level summary metrics"""
        return {
            "total_queries": len(df),
            "unique_users": df['user_id'].nunique(),
            "avg_response_time_ms": df['processing_time_ms'].mean(),
            "median_response_time_ms": df['processing_time_ms'].median(),
            "p95_response_time_ms": df['processing_time_ms'].quantile(0.95),
            "success_rate": (df['status'] == 'completed').mean(),
            "total_cost": df['total_cost'].sum(),
            "avg_cost_per_query": df['total_cost'].mean(),
            "avg_steps_per_workflow": df['steps_completed'].mean(),
            "avg_test_success_rate": df['test_success_rate'].mean()
        }

    def _calculate_trends(self, df: pd.DataFrame) -> Dict:
        """Calculate trend data for visualization"""
        daily_stats = df.groupby('date').agg({
            'user_id': 'count',
            'processing_time_ms': ['mean', 'median', lambda x: x.quantile(0.95)],
            'total_cost': 'sum',
            'status': lambda x: (x == 'completed').mean()
        }).round(2)

        return {
            "query_volume": daily_stats['user_id'].to_dict(),
            "response_times": {
                "mean": daily_stats[('processing_time_ms', 'mean')].to_dict(),
                "median": daily_stats[('processing_time_ms', 'median')].to_dict(),
                "p95": daily_stats[('processing_time_ms', '<lambda>')].to_dict()
            },
            "daily_costs": daily_stats[('total_cost', 'sum')].to_dict(),
            "success_rates": daily_stats[('status', '<lambda>')].to_dict()
        }

    def _analyze_agent_performance(self, df: pd.DataFrame) -> List[Dict]:
        """Analyze performance by agent"""
        agent_stats = df.groupby('agent_id').agg({
            'user_id': 'count',
            'processing_time_ms': 'mean',
            'status': lambda x: (x == 'completed').mean(),
            'total_cost': ['sum', 'mean'],
            'test_success_rate': 'mean',
            'security_issues_found': 'sum'
        }).round(2)

        agent_performance = []
        for agent_id in agent_stats.index:
            agent_performance.append({
                "agent_id": agent_id,
                "query_count": agent_stats.loc[agent_id, ('user_id', 'count')],
                "avg_response_time": agent_stats.loc[agent_id, ('processing_time_ms', 'mean')],
                "success_rate": agent_stats.loc[agent_id, ('status', '<lambda>')],
                "total_cost": agent_stats.loc[agent_id, ('total_cost', 'sum')],
                "cost_per_query": agent_stats.loc[agent_id, ('total_cost', 'mean')],
                "avg_test_success": agent_stats.loc[agent_id, ('test_success_rate', 'mean')],
                "security_issues": agent_stats.loc[agent_id, ('security_issues_found', 'sum')]
            })

        return sorted(agent_performance, key=lambda x: x['query_count'], reverse=True)

    def _analyze_user_behavior(self, df: pd.DataFrame) -> Dict:
        """Analyze user behavior patterns"""
        user_stats = df.groupby('user_id').agg({
            'agent_id': ['count', 'nunique'],
            'processing_time_ms': 'mean',
            'total_cost': 'sum',
            'status': lambda x: (x == 'completed').mean()
        })

        # User segmentation using clustering
        user_features = user_stats[['agent_id', 'processing_time_ms', 'total_cost']].copy()
        user_features.columns = ['query_count', 'avg_response_time', 'total_cost']

        # Normalize features for clustering
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(user_features.fillna(0))

        # Perform clustering
        kmeans = KMeans(n_clusters=3, random_state=42)
        user_clusters = kmeans.fit_predict(features_scaled)

        # Analyze clusters
        cluster_analysis = []
        for cluster_id in range(3):
            cluster_users = user_features[user_clusters == cluster_id]
            cluster_analysis.append({
                "cluster_id": cluster_id,
                "user_count": len(cluster_users),
                "avg_queries_per_user": cluster_users['query_count'].mean(),
                "avg_cost_per_user": cluster_users['total_cost'].mean(),
                "avg_response_time": cluster_users['avg_response_time'].mean(),
                "characteristics": self._describe_cluster(cluster_users)
            })

        return {
            "total_users": len(user_stats),
            "power_users": len(user_stats[user_stats[('agent_id', 'count')] > 50]),
            "occasional_users": len(user_stats[user_stats[('agent_id', 'count')] <= 5]),
            "user_segments": cluster_analysis,
            "top_users_by_volume": user_stats.nlargest(10, ('agent_id', 'count')).to_dict('index')
        }

    def _analyze_costs(self, df: pd.DataFrame) -> Dict:
        """Analyze cost patterns and efficiency"""
        cost_by_agent = df.groupby('agent_id')['total_cost'].agg(['sum', 'mean', 'count'])
        cost_by_agent['cost_efficiency'] = cost_by_agent['count'] / cost_by_agent['sum']

        # Identify cost outliers
        cost_outliers = df[df['total_cost'] > df['total_cost'].quantile(0.95)]

        return {
            "total_cost": df['total_cost'].sum(),
            "cost_trend": df.groupby('date')['total_cost'].sum().to_dict(),
            "cost_by_agent": cost_by_agent.to_dict('index'),
            "cost_outliers": {
                "count": len(cost_outliers),
                "total_cost": cost_outliers['total_cost'].sum(),
                "avg_cost": cost_outliers['total_cost'].mean()
            },
            "cost_efficiency_ranking": cost_by_agent.sort_values('cost_efficiency', ascending=False).to_dict('index')
        }

    def _analyze_quality_metrics(self, df: pd.DataFrame) -> Dict:
        """Analyze quality and success metrics"""
        quality_by_agent = df.groupby('agent_id').agg({
            'status': lambda x: (x == 'completed').mean(),
            'test_success_rate': 'mean',
            'security_issues_found': 'mean',
            'steps_completed': 'mean'
        })

        return {
            "overall_success_rate": (df['status'] == 'completed').mean(),
            "avg_test_success_rate": df['test_success_rate'].mean(),
            "total_security_issues": df['security_issues_found'].sum(),
            "avg_workflow_complexity": df['steps_completed'].mean(),
            "quality_by_agent": quality_by_agent.to_dict('index'),
            "quality_trends": df.groupby('date').agg({
                'status': lambda x: (x == 'completed').mean(),
                'test_success_rate': 'mean'
            }).to_dict('index')
        }

    async def _generate_optimization_recommendations(self, df: pd.DataFrame) -> List[Dict]:
        """Generate ML-powered optimization recommendations"""
        recommendations = []

        # Performance optimization recommendations
        slow_agents = df.groupby('agent_id')['processing_time_ms'].mean()
        slow_agents = slow_agents[slow_agents > slow_agents.quantile(0.8)]

        for agent_id in slow_agents.index:
            recommendations.append({
                "type": "performance",
                "priority": "high" if slow_agents[agent_id] > slow_agents.quantile(0.95) else "medium",
                "description": f"Agent '{agent_id}' has high response times (avg: {slow_agents[agent_id]:.0f}ms)",
                "estimated_impact": f"Could reduce response time by 20-40%",
                "implementation_effort": "medium",
                "suggested_actions": [
                    "Review agent logic for optimization opportunities",
                    "Consider caching frequently requested data",
                    "Optimize model inference if applicable"
                ]
            })

        # Cost optimization recommendations
        expensive_agents = df.groupby('agent_id')['total_cost'].mean()
        expensive_agents = expensive_agents[expensive_agents > expensive_agents.quantile(0.8)]

        for agent_id in expensive_agents.index:
            recommendations.append({
                "type": "cost",
                "priority": "medium",
                "description": f"Agent '{agent_id}' has high per-query costs (avg: ${expensive_agents[agent_id]:.3f})",
                "estimated_impact": f"Could reduce costs by 15-30%",
                "implementation_effort": "low",
                "suggested_actions": [
                    "Review model usage patterns",
                    "Consider using tiered search strategies",
                    "Implement query result caching"
                ]
            })

        # Quality improvement recommendations
        error_prone_agents = df.groupby('agent_id')['status'].apply(lambda x: (x == 'failed').mean())
        error_prone_agents = error_prone_agents[error_prone_agents > 0.1]  # >10% failure rate

        for agent_id in error_prone_agents.index:
            recommendations.append({
                "type": "accuracy",
                "priority": "high",
                "description": f"Agent '{agent_id}' has high failure rate ({error_prone_agents[agent_id]*100:.1f}%)",
                "estimated_impact": f"Could improve success rate by 20-50%",
                "implementation_effort": "high",
                "suggested_actions": [
                    "Review error logs and failure patterns",
                    "Improve error handling and recovery",
                    "Add additional validation steps"
                ]
            })

        return sorted(recommendations, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True)

    async def predict_usage_patterns(self, horizon_days: int = 30) -> Dict:
        """Predict future usage patterns using ML models"""

        if not self.usage_predictor:
            await self._train_usage_predictor()

        # Generate predictions
        future_dates = pd.date_range(
            start=datetime.now(),
            periods=horizon_days,
            freq='D'
        )

        # Create feature matrix for predictions
        features = self._create_prediction_features(future_dates)

        # Make predictions
        predicted_volume = self.usage_predictor.predict(features)
        predicted_costs = predicted_volume * self._estimate_cost_per_query()

        return {
            "prediction_horizon_days": horizon_days,
            "predicted_daily_volume": dict(zip(future_dates.strftime('%Y-%m-%d'), predicted_volume)),
            "predicted_daily_costs": dict(zip(future_dates.strftime('%Y-%m-%d'), predicted_costs)),
            "total_predicted_volume": predicted_volume.sum(),
            "total_predicted_cost": predicted_costs.sum(),
            "confidence_interval": "85%",  # Model-dependent
            "model_accuracy": self._get_model_accuracy()
        }

    async def detect_anomalies(self, time_range: str = "7d") -> List[Dict]:
        """Detect usage and performance anomalies"""

        if not self.anomaly_detector:
            await self._train_anomaly_detector()

        # Get recent data
        end_date = datetime.now()
        days = {"1d": 1, "7d": 7, "30d": 30}[time_range]
        start_date = end_date - timedelta(days=days)

        with self.Session() as session:
            query = text("""
                SELECT
                    DATE(created_at) as date,
                    EXTRACT(hour FROM created_at) as hour,
                    COUNT(*) as query_count,
                    AVG(processing_time_ms) as avg_response_time,
                    SUM(total_cost) as total_cost,
                    AVG(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as success_rate
                FROM workflow_executions
                WHERE created_at >= :start_date
                GROUP BY DATE(created_at), EXTRACT(hour FROM created_at)
                ORDER BY date, hour
            """)

            df = pd.read_sql(query, session.bind, params={'start_date': start_date})

        if df.empty:
            return []

        # Detect anomalies
        features = df[['query_count', 'avg_response_time', 'total_cost', 'success_rate']].fillna(0)
        anomaly_scores = self.anomaly_detector.decision_function(features)
        anomalies = df[anomaly_scores < -0.5]  # Threshold for anomaly detection

        anomaly_list = []
        for _, row in anomalies.iterrows():
            anomaly_list.append({
                "timestamp": f"{row['date']} {int(row['hour']):02d}:00",
                "type": self._classify_anomaly_type(row),
                "severity": self._calculate_anomaly_severity(anomaly_scores[row.name]),
                "metrics": {
                    "query_count": row['query_count'],
                    "avg_response_time": row['avg_response_time'],
                    "total_cost": row['total_cost'],
                    "success_rate": row['success_rate']
                },
                "description": self._describe_anomaly(row),
                "suggested_investigation": self._suggest_anomaly_investigation(row)
            })

        return sorted(anomaly_list, key=lambda x: x['severity'], reverse=True)

    def _classify_anomaly_type(self, row: pd.Series) -> str:
        """Classify the type of anomaly"""
        if row['query_count'] > row['query_count'] * 2:
            return "volume_spike"
        elif row['avg_response_time'] > 5000:  # >5 seconds
            return "performance_degradation"
        elif row['success_rate'] < 0.8:
            return "quality_issues"
        elif row['total_cost'] > row['total_cost'] * 1.5:
            return "cost_spike"
        else:
            return "general_anomaly"

    def _calculate_anomaly_severity(self, score: float) -> str:
        """Calculate anomaly severity based on score"""
        if score < -1.5:
            return "critical"
        elif score < -1.0:
            return "high"
        elif score < -0.75:
            return "medium"
        else:
            return "low"

    def _is_cached(self, key: str) -> bool:
        """Check if result is cached and still valid"""
        if key not in self.cache:
            return False

        # For simplicity, assume all cache entries have timestamp
        # In production, implement proper cache invalidation
        return True  # Simplified for this example

    async def _train_usage_predictor(self):
        """Train ML model for usage prediction"""
        # Implementation would load historical data and train a time series model
        # For now, return a mock model
        logger.info("Training usage prediction model...")
        self.usage_predictor = MockUsagePredictor()

    async def _train_anomaly_detector(self):
        """Train ML model for anomaly detection"""
        logger.info("Training anomaly detection model...")
        self.anomaly_detector = MockAnomalyDetector()

class MockUsagePredictor:
    """Mock usage predictor for demonstration"""
    def predict(self, features):
        return np.random.normal(100, 20, len(features))

class MockAnomalyDetector:
    """Mock anomaly detector for demonstration"""
    def decision_function(self, features):
        return np.random.normal(0, 0.5, len(features))
```

### 6.3. Enterprise SSO Integration

```python
# src/enterprise/sso_integration.py
import jwt
import httpx
import xml.etree.ElementTree as ET
from typing import Dict, Optional, List
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class EnterpriseSSO:
    """Enterprise Single Sign-On integration"""

    def __init__(self, config: Dict):
        self.config = config
        self.keycloak_url = config['keycloak_url']
        self.realm = config['realm']
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.saml_idp_url = config.get('saml_idp_url')
        self.jwt_secret = config['jwt_secret']
        self.audit_logger = AuditLogger(config.get('audit_config', {}))

    async def authenticate_saml(self, saml_response: str, request: Request) -> Dict:
        """Authenticate user via SAML response"""
        try:
            # Parse SAML response
            saml_data = self._parse_saml_response(saml_response)

            # Validate SAML assertion
            if not self._validate_saml_assertion(saml_data):
                await self.audit_logger.log_security_event(
                    event_type="authentication_failure",
                    user_id=saml_data.get('user_id', 'unknown'),
                    details={"reason": "invalid_saml_assertion"},
                    request=request
                )
                raise HTTPException(status_code=401, detail="Invalid SAML assertion")

            # Extract user information
            user_info = self._extract_user_claims(saml_data)

            # Create JWT token with enterprise claims
            jwt_token = self._create_enterprise_jwt(user_info)

            # Log successful authentication
            await self.audit_logger.log_security_event(
                event_type="authentication_success",
                user_id=user_info['user_id'],
                details={
                    "authentication_method": "saml",
                    "organization": user_info.get('organization'),
                    "roles": user_info.get('roles', [])
                },
                request=request
            )

            return {
                "access_token": jwt_token,
                "token_type": "bearer",
                "expires_in": 86400,  # 24 hours
                "user_info": user_info
            }

        except Exception as e:
            await self.audit_logger.log_security_event(
                event_type="authentication_error",
                user_id="unknown",
                details={"error": str(e)},
                request=request
            )
            raise HTTPException(status_code=500, detail="Authentication failed")

    async def authenticate_oidc(self, authorization_code: str, request: Request) -> Dict:
        """Authenticate user via OpenID Connect"""
        try:
            # Exchange authorization code for tokens
            token_response = await self._exchange_oidc_code(authorization_code)

            # Validate and decode ID token
            id_token = token_response['id_token']
            user_claims = self._validate_oidc_token(id_token)

            # Get additional user info if needed
            if 'access_token' in token_response:
                additional_info = await self._get_oidc_userinfo(token_response['access_token'])
                user_claims.update(additional_info)

            # Create internal JWT
            jwt_token = self._create_enterprise_jwt(user_claims)

            # Log authentication
            await self.audit_logger.log_security_event(
                event_type="authentication_success",
                user_id=user_claims['user_id'],
                details={
                    "authentication_method": "oidc",
                    "organization": user_claims.get('organization'),
                    "roles": user_claims.get('roles', [])
                },
                request=request
            )

            return {
                "access_token": jwt_token,
                "token_type": "bearer",
                "expires_in": 86400,
                "user_info": user_claims
            }

        except Exception as e:
            await self.audit_logger.log_security_event(
                event_type="authentication_error",
                user_id="unknown",
                details={"error": str(e)},
                request=request
            )
            raise HTTPException(status_code=500, detail="OIDC authentication failed")

    def validate_enterprise_jwt(self, token: str, request: Request) -> Dict:
        """Validate enterprise JWT token"""
        try:
            # Decode and validate JWT
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256'],
                options={"verify_exp": True}
            )

            # Validate enterprise-specific claims
            if not self._validate_enterprise_claims(payload):
                raise HTTPException(status_code=403, detail="Invalid enterprise claims")

            # Log API access
            asyncio.create_task(self.audit_logger.log_api_access(
                user_id=payload['user_id'],
                endpoint=request.url.path,
                method=request.method,
                request=request
            ))

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    async def refresh_token(self, refresh_token: str, request: Request) -> Dict:
        """Refresh authentication token"""
        try:
            # Validate refresh token
            refresh_payload = jwt.decode(
                refresh_token,
                self.jwt_secret,
                algorithms=['HS256']
            )

            if refresh_payload.get('token_type') != 'refresh':
                raise HTTPException(status_code=401, detail="Invalid refresh token")

            # Check if user still has access
            user_id = refresh_payload['user_id']
            if not await self._validate_user_access(user_id):
                raise HTTPException(status_code=401, detail="User access revoked")

            # Create new access token
            user_info = await self._get_current_user_info(user_id)
            new_token = self._create_enterprise_jwt(user_info)

            # Log token refresh
            await self.audit_logger.log_security_event(
                event_type="token_refresh",
                user_id=user_id,
                details={"refresh_successful": True},
                request=request
            )

            return {
                "access_token": new_token,
                "token_type": "bearer",
                "expires_in": 86400
            }

        except Exception as e:
            await self.audit_logger.log_security_event(
                event_type="token_refresh_failure",
                user_id="unknown",
                details={"error": str(e)},
                request=request
            )
            raise HTTPException(status_code=401, detail="Token refresh failed")

    def _parse_saml_response(self, saml_response: str) -> Dict:
        """Parse SAML response XML"""
        try:
            root = ET.fromstring(saml_response)

            # Extract assertion
            assertion = root.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Assertion')
            if assertion is None:
                raise ValueError("No assertion found in SAML response")

            # Extract subject
            subject = assertion.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Subject')
            name_id = subject.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}NameID')

            # Extract attributes
            attributes = {}
            attr_statements = assertion.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement')
            for attr_statement in attr_statements:
                for attr in attr_statement.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}Attribute'):
                    attr_name = attr.get('Name')
                    attr_values = [val.text for val in attr.findall('.//{urn:oasis:names:tc:SAML:2.0:assertion}AttributeValue')]
                    attributes[attr_name] = attr_values[0] if len(attr_values) == 1 else attr_values

            return {
                "user_id": name_id.text if name_id is not None else None,
                "attributes": attributes,
                "assertion": assertion
            }

        except ET.ParseError as e:
            raise ValueError(f"Invalid SAML XML: {str(e)}")

    def _validate_saml_assertion(self, saml_data: Dict) -> bool:
        """Validate SAML assertion"""
        # In production, implement proper SAML signature validation
        # For now, perform basic checks

        if not saml_data.get('user_id'):
            return False

        # Check assertion validity period
        assertion = saml_data['assertion']
        conditions = assertion.find('.//{urn:oasis:names:tc:SAML:2.0:assertion}Conditions')

        if conditions is not None:
            not_before = conditions.get('NotBefore')
            not_on_or_after = conditions.get('NotOnOrAfter')

            if not_before or not_on_or_after:
                current_time = datetime.utcnow()

                if not_before:
                    not_before_time = datetime.fromisoformat(not_before.replace('Z', '+00:00'))
                    if current_time < not_before_time:
                        return False

                if not_on_or_after:
                    not_after_time = datetime.fromisoformat(not_on_or_after.replace('Z', '+00:00'))
                    if current_time >= not_after_time:
                        return False

        return True

    def _extract_user_claims(self, saml_data: Dict) -> Dict:
        """Extract user claims from SAML data"""
        attributes = saml_data.get('attributes', {})

        # Map SAML attributes to internal user claims
        user_claims = {
            "user_id": saml_data['user_id'],
            "email": attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress'),
            "name": attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name'),
            "given_name": attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname'),
            "family_name": attributes.get('http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname'),
            "organization": attributes.get('organization'),
            "department": attributes.get('department'),
            "roles": self._parse_roles(attributes.get('roles', [])),
            "groups": self._parse_groups(attributes.get('groups', [])),
            "authentication_method": "saml",
            "authentication_time": datetime.utcnow().isoformat()
        }

        return {k: v for k, v in user_claims.items() if v is not None}

    async def _exchange_oidc_code(self, authorization_code: str) -> Dict:
        """Exchange authorization code for OIDC tokens"""
        token_endpoint = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/token"

        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": authorization_code,
            "redirect_uri": self.config.get('redirect_uri')
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_endpoint, data=data)

            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

            return response.json()

    def _validate_oidc_token(self, id_token: str) -> Dict:
        """Validate and decode OIDC ID token"""
        try:
            # In production, fetch and validate with Keycloak's public keys
            # For now, decode without verification (for development only)
            payload = jwt.decode(
                id_token,
                options={"verify_signature": False, "verify_exp": True}
            )

            # Map OIDC claims to internal format
            user_claims = {
                "user_id": payload.get('sub'),
                "email": payload.get('email'),
                "name": payload.get('name'),
                "given_name": payload.get('given_name'),
                "family_name": payload.get('family_name'),
                "organization": payload.get('organization'),
                "roles": payload.get('realm_access', {}).get('roles', []),
                "groups": payload.get('groups', []),
                "authentication_method": "oidc",
                "authentication_time": datetime.utcnow().isoformat()
            }

            return {k: v for k, v in user_claims.items() if v is not None}

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="ID token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid ID token")

    async def _get_oidc_userinfo(self, access_token: str) -> Dict:
        """Get additional user info from OIDC userinfo endpoint"""
        userinfo_endpoint = f"{self.keycloak_url}/realms/{self.realm}/protocol/openid-connect/userinfo"

        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_endpoint, headers=headers)

            if response.status_code == 200:
                return response.json()

            return {}

    def _create_enterprise_jwt(self, user_info: Dict) -> str:
        """Create enterprise JWT with custom claims"""
        now = datetime.utcnow()

        payload = {
            "iss": "promptcraft-hybrid",
            "sub": user_info['user_id'],
            "aud": "promptcraft-api",
            "exp": now + timedelta(hours=24),
            "iat": now,
            "nbf": now,
            "user_id": user_info['user_id'],
            "email": user_info.get('email'),
            "name": user_info.get('name'),
            "organization": user_info.get('organization'),
            "roles": user_info.get('roles', []),
            "groups": user_info.get('groups', []),
            "permissions": self._calculate_permissions(user_info),
            "authentication_method": user_info.get('authentication_method'),
            "token_type": "access"
        }

        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')

    def _calculate_permissions(self, user_info: Dict) -> List[str]:
        """Calculate user permissions based on roles and groups"""
        permissions = set()
        roles = user_info.get('roles', [])
        groups = user_info.get('groups', [])

        # Role-based permissions
        role_permissions = {
            'admin': ['read', 'write', 'execute', 'admin', 'create_agents', 'manage_users'],
            'developer': ['read', 'write', 'execute', 'create_agents'],
            'analyst': ['read', 'execute'],
            'viewer': ['read']
        }

        for role in roles:
            if role in role_permissions:
                permissions.update(role_permissions[role])

        # Group-based permissions
        group_permissions = {
            'security-team': ['security_analysis', 'compliance_reports'],
            'data-team': ['analytics', 'cost_management'],
            'engineering': ['agent_management', 'infrastructure']
        }

        for group in groups:
            if group in group_permissions:
                permissions.update(group_permissions[group])

        return list(permissions)

    def _validate_enterprise_claims(self, payload: Dict) -> bool:
        """Validate enterprise-specific JWT claims"""
        required_claims = ['user_id', 'organization']

        for claim in required_claims:
            if claim not in payload:
                return False

        # Validate organization access
        allowed_organizations = self.config.get('allowed_organizations', [])
        if allowed_organizations and payload.get('organization') not in allowed_organizations:
            return False

        return True

    async def _validate_user_access(self, user_id: str) -> bool:
        """Validate if user still has access to the system"""
        # In production, check against user management system
        # For now, always return True
        return True

    async def _get_current_user_info(self, user_id: str) -> Dict:
        """Get current user information for token refresh"""
        # In production, fetch from user management system
        # For now, return minimal info
        return {
            "user_id": user_id,
            "authentication_method": "refresh"
        }

    def _parse_roles(self, roles_data) -> List[str]:
        """Parse roles from SAML/OIDC data"""
        if isinstance(roles_data, str):
            return [r.strip() for r in roles_data.split(',')]
        elif isinstance(roles_data, list):
            return roles_data
        return []

    def _parse_groups(self, groups_data) -> List[str]:
        """Parse groups from SAML/OIDC data"""
        if isinstance(groups_data, str):
            return [g.strip() for g in groups_data.split(',')]
        elif isinstance(groups_data, list):
            return groups_data
        return []

class AuditLogger:
    """Enterprise audit logging"""

    def __init__(self, config: Dict):
        self.config = config
        self.db_engine = create_engine(config.get('audit_db_url'))
        self.external_siem_url = config.get('external_siem_url')

    async def log_security_event(self, event_type: str, user_id: str,
                                details: Dict, request: Request):
        """Log security-related events"""
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "event_category": "security",
            "user_id": user_id,
            "source": {
                "component": "sso_integration",
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent")
            },
            "details": details,
            "severity": self._determine_severity(event_type)
        }

        await self._store_audit_event(event)

        # Send to external SIEM if configured
        if self.external_siem_url:
            await self._send_to_siem(event)

    async def log_api_access(self, user_id: str, endpoint: str,
                           method: str, request: Request):
        """Log API access events"""
        event = {
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": "api_access",
            "event_category": "operational",
            "user_id": user_id,
            "action": {
                "operation": f"{method} {endpoint}",
                "resource": endpoint,
                "method": method
            },
            "source": {
                "component": "api_gateway",
                "ip_address": request.client.host,
                "user_agent": request.headers.get("user-agent")
            },
            "severity": "info"
        }

        await self._store_audit_event(event)

    async def _store_audit_event(self, event: Dict):
        """Store audit event in database"""
        # Implementation would insert into audit_events table
        logger.info(f"Audit event: {event['event_type']} for user {event.get('user_id')}")

    async def _send_to_siem(self, event: Dict):
        """Send audit event to external SIEM system"""
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    self.external_siem_url,
                    json=event,
                    headers={"Content-Type": "application/json"}
                )
        except Exception as e:
            logger.error(f"Failed to send audit event to SIEM: {str(e)}")

    def _determine_severity(self, event_type: str) -> str:
        """Determine event severity"""
        severity_map = {
            "authentication_failure": "warning",
            "authentication_error": "error",
            "token_refresh_failure": "warning",
            "authentication_success": "info",
            "token_refresh": "info"
        }
        return severity_map.get(event_type, "info")
```

### 6.4. CLI Tools for Agent Management

```python
# src/enterprise/cli.py
import typer
import asyncio
import yaml
import json
import os
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from rich.prompt import Prompt, Confirm
import httpx

console = Console()
app = typer.Typer(name="pc-hybrid", help="PromptCraft-Hybrid Enterprise CLI")

# Configuration
CONFIG_FILE = Path.home() / ".promptcraft" / "config.yaml"

class CLIConfig:
    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> dict:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return yaml.safe_load(f)
        return {}

    def save_config(self):
        CONFIG_FILE.parent.mkdir(exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(self.config, f)

    def get_api_url(self) -> str:
        return self.config.get('api_url', 'http://localhost:8000')

    def get_auth_token(self) -> Optional[str]:
        return self.config.get('auth_token')

    def set_auth_token(self, token: str):
        self.config['auth_token'] = token
        self.save_config()

config = CLIConfig()

@app.command()
def configure(
    api_url: str = typer.Option("http://localhost:8000", help="API base URL"),
    username: Optional[str] = typer.Option(None, help="Username for authentication"),
    password: Optional[str] = typer.Option(None, help="Password for authentication")
):
    """Configure CLI settings and authentication"""

    config.config['api_url'] = api_url

    if username and password:
        # Authenticate and store token
        auth_url = f"{api_url}/auth/token"

        try:
            response = httpx.post(
                auth_url,
                json={"username": username, "password": password}
            )

            if response.status_code == 200:
                token_data = response.json()
                config.set_auth_token(token_data['access_token'])
                console.print("✅ Authentication successful!", style="green")
            else:
                console.print("❌ Authentication failed!", style="red")
                return

        except Exception as e:
            console.print(f"❌ Connection error: {str(e)}", style="red")
            return

    config.save_config()
    console.print("🔧 Configuration saved!", style="blue")

@app.group()
def agent():
    """Agent management commands"""
    pass

@agent.command("create")
def create_agent(
    name: str = typer.Argument(..., help="Agent name (snake_case)"),
    domain: str = typer.Option(..., help="Domain expertise (e.g., security, finance)"),
    description: str = typer.Option(..., help="Agent description"),
    keywords: str = typer.Option(..., help="Comma-separated keywords"),
    auto_deploy: bool = typer.Option(False, help="Automatically deploy after creation"),
    interactive: bool = typer.Option(True, help="Interactive mode for additional options")
):
    """Create a new agent"""

    if not config.get_auth_token():
        console.print("❌ Not authenticated. Run 'pc-hybrid configure' first.", style="red")
        return

    # Validate name format
    if not name.replace('_', '').islower():
        console.print("❌ Agent name must be in snake_case format", style="red")
        return

    # Parse keywords
    keyword_list = [k.strip() for k in keywords.split(',')]

    # Interactive mode for additional configuration
    capabilities = []
    knowledge_sources = []

    if interactive:
        console.print("\n🤖 Creating new agent...", style="blue")

        # Collect capabilities
        console.print("\n📋 Define agent capabilities:")
        while True:
            capability = Prompt.ask("Add capability (or press Enter to finish)")
            if not capability:
                break
            capabilities.append(capability)

        # Collect knowledge sources
        console.print("\n📚 Define knowledge sources:")
        while True:
            if not Confirm.ask("Add knowledge source?"):
                break

            source_type = Prompt.ask(
                "Source type",
                choices=["markdown", "json", "api", "database"],
                default="markdown"
            )
            source_location = Prompt.ask("Source location/URL")
            update_freq = Prompt.ask(
                "Update frequency",
                choices=["daily", "weekly", "monthly"],
                default="weekly"
            )

            knowledge_sources.append({
                "type": source_type,
                "source": source_location,
                "update_frequency": update_freq
            })

    # Build agent specification
    agent_spec = {
        "agent_spec": {
            "name": name,
            "display_name": name.replace('_', ' ').title(),
            "description": description,
            "domain": domain,
            "keywords": keyword_list,
            "capabilities": capabilities,
            "knowledge_sources": knowledge_sources
        },
        "deployment_config": {
            "environment": "development",
            "auto_deploy": auto_deploy,
            "resource_limits": {
                "memory": "512M",
                "cpu": "0.5"
            }
        },
        "integration_config": {
            "required_tools": [],
            "optional_tools": ["heimdall", "github_mcp"]
        }
    }

    # Create agent via API
    with console.status("Creating agent..."):
        try:
            response = httpx.post(
                f"{config.get_api_url()}/api/v4/admin/agents/create",
                json=agent_spec,
                headers={"Authorization": f"Bearer {config.get_auth_token()}"}
            )

            if response.status_code == 202:
                result = response.json()
                creation_id = result['data']['creation_id']
                estimated_duration = result['data']['estimated_duration_minutes']

                console.print(f"🚀 Agent creation started!", style="green")
                console.print(f"📊 Creation ID: {creation_id}")
                console.print(f"⏱️  Estimated duration: {estimated_duration} minutes")
                console.print(f"🔗 Repository: {result['data']['repository_url']}")

                # Monitor progress if requested
                if Confirm.ask("Monitor creation progress?"):
                    asyncio.run(_monitor_agent_creation(creation_id))

            else:
                error_detail = response.json().get('detail', 'Unknown error')
                console.print(f"❌ Agent creation failed: {error_detail}", style="red")

        except Exception as e:
            console.print(f"❌ Connection error: {str(e)}", style="red")

@agent.command("list")
def list_agents(
    status: Optional[str] = typer.Option(None, help="Filter by status"),
    domain: Optional[str] = typer.Option(None, help="Filter by domain")
):
    """List all agents"""

    if not config.get_auth_token():
        console.print("❌ Not authenticated. Run 'pc-hybrid configure' first.", style="red")
        return

    try:
        params = {}
        if status:
            params['status'] = status
        if domain:
            params['domain'] = domain

        response = httpx.get(
            f"{config.get_api_url()}/api/v4/admin/agents",
            params=params,
            headers={"Authorization": f"Bearer {config.get_auth_token()}"}
        )

        if response.status_code == 200:
            agents = response.json()['data']

            if not agents:
                console.print("No agents found.", style="yellow")
                return

            # Create table
            table = Table(title="PromptCraft Agents")
            table.add_column("Name", style="cyan")
            table.add_column("Domain", style="magenta")
            table.add_column("Status", style="green")
            table.add_column("Version", style="blue")
            table.add_column("Created", style="dim")

            for agent in agents:
                table.add_row(
                    agent['name'],
                    agent['domain'],
                    agent['status'],
                    agent['version'],
                    agent['created_at'][:10]  # Just the date
                )

            console.print(table)

        else:
            console.print("❌ Failed to fetch agents", style="red")

    except Exception as e:
        console.print(f"❌ Connection error: {str(e)}", style="red")

@agent.command("deploy")
def deploy_agent(
    name: str = typer.Argument(..., help="Agent name to deploy"),
    environment: str = typer.Option("development", help="Target environment"),
    wait: bool = typer.Option(True, help="Wait for deployment to complete")
):
    """Deploy an agent to specified environment"""

    if not config.get_auth_token():
        console.print("❌ Not authenticated. Run 'pc-hybrid configure' first.", style="red")
        return

    deployment_config = {
        "agent_name": name,
        "environment": environment,
        "restart_policy": "unless-stopped"
    }

    with console.status(f"Deploying {name} to {environment}..."):
        try:
            response = httpx.post(
                f"{config.get_api_url()}/api/v4/admin/agents/{name}/deploy",
                json=deployment_config,
                headers={"Authorization": f"Bearer {config.get_auth_token()}"}
            )

            if response.status_code == 202:
                result = response.json()
                deployment_id = result['data']['deployment_id']

                console.print(f"🚀 Deployment started!", style="green")
                console.print(f"📊 Deployment ID: {deployment_id}")

                if wait:
                    asyncio.run(_monitor_deployment(deployment_id))

            else:
                console.print("❌ Deployment failed", style="red")

        except Exception as e:
            console.print(f"❌ Connection error: {str(e)}", style="red")

@app.group()
def analytics():
    """Analytics and monitoring commands"""
    pass

@analytics.command("usage")
def usage_report(
    time_range: str = typer.Option("30d", help="Time range (7d, 30d, 90d, 1y)"),
    format: str = typer.Option("table", help="Output format (table, json, csv)"),
    output: Optional[str] = typer.Option(None, help="Output file path")
):
    """Generate usage analytics report"""

    if not config.get_auth_token():
        console.print("❌ Not authenticated. Run 'pc-hybrid configure' first.", style="red")
        return

    with console.status("Generating usage report..."):
        try:
            response = httpx.get(
                f"{config.get_api_url()}/api/v4/analytics/insights",
                params={"time_range": time_range, "metrics": "usage,performance,costs"},
                headers={"Authorization": f"Bearer {config.get_auth_token()}"}
            )

            if response.status_code == 200:
                data = response.json()['data']

                if format == "json":
                    output_data = json.dumps(data, indent=2)
                elif format == "csv":
                    output_data = _convert_to_csv(data)
                else:  # table format
                    _display_usage_table(data)
                    return

                if output:
                    with open(output, 'w') as f:
                        f.write(output_data)
                    console.print(f"📄 Report saved to {output}", style="green")
                else:
                    console.print(output_data)

            else:
                console.print("❌ Failed to generate report", style="red")

        except Exception as e:
            console.print(f"❌ Connection error: {str(e)}", style="red")

@analytics.command("performance")
def performance_dashboard():
    """Display real-time performance dashboard"""

    if not config.get_auth_token():
        console.print("❌ Not authenticated. Run 'pc-hybrid configure' first.", style="red")
        return

    console.print("📊 Performance Dashboard", style="bold blue")
    console.print("Press Ctrl+C to exit\n")

    try:
        while True:
            response = httpx.get(
                f"{config.get_api_url()}/api/v4/analytics/realtime",
                headers={"Authorization": f"Bearer {config.get_auth_token()}"}
            )

            if response.status_code == 200:
                metrics = response.json()['data']

                # Clear screen and display metrics
                console.clear()
                _display_performance_metrics(metrics)

            time.sleep(5)  # Update every 5 seconds

    except KeyboardInterrupt:
        console.print("\n👋 Dashboard closed", style="yellow")

async def _monitor_agent_creation(creation_id: str):
    """Monitor agent creation progress"""

    with Progress() as progress:
        task = progress.add_task("Creating agent...", total=100)

        while not progress.finished:
            try:
                response = httpx.get(
                    f"{config.get_api_url()}/api/v4/admin/agents/creation/{creation_id}/status",
                    headers={"Authorization": f"Bearer {config.get_auth_token()}"}
                )

                if response.status_code == 200:
                    status_data = response.json()['data']
                    progress_percent = status_data.get('progress_percentage', 0)
                    status = status_data.get('status')

                    progress.update(task, completed=progress_percent)

                    if status == 'completed':
                        progress.update(task, completed=100)
                        console.print("✅ Agent created successfully!", style="green")
                        break
                    elif status == 'failed':
                        console.print("❌ Agent creation failed!", style="red")
                        break

            except Exception as e:
                console.print(f"❌ Monitoring error: {str(e)}", style="red")
                break

            await asyncio.sleep(2)

def _display_usage_table(data: dict):
    """Display usage data in table format"""

    summary = data['summary']

    # Summary table
    summary_table = Table(title="Usage Summary")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total Queries", f"{summary['total_queries']:,}")
    summary_table.add_row("Unique Users", f"{summary['unique_users']:,}")
    summary_table.add_row("Avg Response Time", f"{summary['avg_response_time_ms']:.0f}ms")
    summary_table.add_row("Success Rate", f"{summary['success_rate']*100:.1f}%")
    summary_table.add_row("Total Cost", f"${summary['total_cost']:.2f}")

    console.print(summary_table)

    # Agent performance table
    if 'agent_performance' in data:
        agent_table = Table(title="Agent Performance")
        agent_table.add_column("Agent", style="cyan")
        agent_table.add_column("Queries", style="green")
        agent_table.add_column("Avg Time", style="blue")
        agent_table.add_column("Success Rate", style="magenta")
        agent_table.add_column("Cost/Query", style="yellow")

        for agent in data['agent_performance'][:10]:  # Top 10
            agent_table.add_row(
                agent['agent_id'],
                f"{agent['query_count']:,}",
                f"{agent['avg_response_time']:.0f}ms",
                f"{agent['success_rate']*100:.1f}%",
                f"${agent['cost_per_query']:.3f}"
            )

        console.print(agent_table)

def _display_performance_metrics(metrics: dict):
    """Display real-time performance metrics"""

    # Current metrics
    current_table = Table(title="Current Performance")
    current_table.add_column("Metric", style="cyan")
    current_table.add_column("Value", style="green")
    current_table.add_column("Status", style="yellow")

    # Add metrics with status indicators
    response_time = metrics.get('avg_response_time_ms', 0)
    response_status = "🟢" if response_time < 3000 else "🟡" if response_time < 5000 else "🔴"

    success_rate = metrics.get('success_rate', 0)
    success_status = "🟢" if success_rate > 0.95 else "🟡" if success_rate > 0.9 else "🔴"

    current_table.add_row("Response Time", f"{response_time:.0f}ms", response_status)
    current_table.add_row("Success Rate", f"{success_rate*100:.1f}%", success_status)
    current_table.add_row("Active Workflows", f"{metrics.get('active_workflows', 0)}", "🟢")
    current_table.add_row("Queue Length", f"{metrics.get('queue_length', 0)}", "🟢")

    console.print(current_table)

if __name__ == "__main__":
    app()
```

## 7. Environment Configuration (Phase 4)

```bash
# .env.example - Phase 4 Enterprise Configuration

# === Core Services (From Previous Phases) ===
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# === AI Models ===
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# === Phase 4 Enterprise Services ===

# PostgreSQL Analytics Database
ANALYTICS_DB_HOST=localhost
ANALYTICS_DB_PORT=5432
ANALYTICS_DB_NAME=promptcraft_analytics
ANALYTICS_DB_USER=promptcraft
ANALYTICS_DB_PASSWORD=your-postgres-password
ANALYTICS_DB_URL=postgresql://promptcraft:your-postgres-password@localhost:5432/promptcraft_analytics

# Keycloak SSO
KEYCLOAK_URL=http://localhost:8080/auth
KEYCLOAK_REALM=promptcraft
KEYCLOAK_CLIENT_ID=promptcraft-hybrid
KEYCLOAK_CLIENT_SECRET=your-keycloak-secret
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=your-keycloak-admin-password

# SAML Configuration
SAML_IDP_URL=https://your-idp.com/saml
SAML_ENTITY_ID=promptcraft-hybrid
SAML_ACS_URL=https://your-domain.com/auth/saml/acs
SAML_CERTIFICATE_PATH=/app/certs/saml.crt
SAML_PRIVATE_KEY_PATH=/app/certs/saml.key

# Enterprise Security
JWT_SECRET=your-super-secret-jwt-key-256-bits-minimum
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
ALLOWED_ORGANIZATIONS=org1,org2,org3
REQUIRE_MFA=false

# Audit & Compliance
AUDIT_DB_URL=postgresql://audit_user:audit_password@localhost:5432/audit_logs
EXTERNAL_SIEM_URL=https://your-siem.com/api/events
COMPLIANCE_LEVEL=SOC2
ENABLE_GDPR_COMPLIANCE=true
DATA_RETENTION_DAYS=2555  # 7 years

# Analytics & ML
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_ARTIFACT_ROOT=s3://your-bucket/mlflow-artifacts
ANALYTICS_CACHE_TTL_MINUTES=15
ENABLE_PREDICTIVE_ANALYTICS=true
MODEL_RETRAINING_SCHEDULE=weekly

# Monitoring & Observability
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3001
GRAFANA_ADMIN_PASSWORD=your-grafana-password
ALERTMANAGER_URL=http://localhost:9093
ENABLE_DISTRIBUTED_TRACING=true
JAEGER_ENDPOINT=http://localhost:14268/api/traces

# Agent Factory
AGENT_FACTORY_GIT_URL=https://github.com/your-org
AGENT_FACTORY_REGISTRY_URL=localhost:5000
AGENT_FACTORY_AUTO_PUSH=true
AGENT_TEMPLATE_REPO=https://github.com/your-org/agent-templates

# Custom MCP Registry
MCP_REGISTRY_URL=http://localhost:8100
MCP_VALIDATION_STRICT=true
MCP_SANDBOX_NETWORK=172.21.0.0/16
MCP_RESOURCE_LIMITS_MEMORY=1G
MCP_RESOURCE_LIMITS_CPU=1.0

# Load Balancing & Scaling
NGINX_UPSTREAM_SERVERS=zen-mcp-1:3000,zen-mcp-2:3000
ENABLE_AUTO_SCALING=true
MIN_REPLICAS=2
MAX_REPLICAS=10
CPU_THRESHOLD_PERCENT=70
MEMORY_THRESHOLD_PERCENT=80

# Backup & Disaster Recovery
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
QDRANT_BACKUP_PATH=/backups/qdrant
POSTGRES_BACKUP_PATH=/backups/postgres
S3_BACKUP_BUCKET=your-backup-bucket

# Enterprise Features
ENABLE_COST_CENTER_TRACKING=true
ENABLE_DEPARTMENT_QUOTAS=true
ENABLE_API_RATE_LIMITING=true
ENABLE_ADVANCED_REPORTING=true
ENABLE_CUSTOM_BRANDING=true

# Development & Debug
DEBUG_MODE=false
ENABLE_SWAGGER_UI=false
LOG_LEVEL=INFO
ENABLE_PERFORMANCE_PROFILING=false
```

## 8. Docker Compose Configuration (Phase 4)

```yaml
# docker-compose.yml - Phase 4 Enterprise Production
version: '3.8'

services:
  # === Load Balancer & SSL Termination ===
  nginx:
    image: nginx:alpine
    container_name: nginx-lb
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - api-gateway-1
      - api-gateway-2
      - gradio-ui-1
      - gradio-ui-2
    restart: unless-stopped
    networks:
      - promptcraft-frontend
      - promptcraft-backend

  # === API Gateway (Multiple Instances) ===
  api-gateway-1:
    build:
      context: ./src/api
      dockerfile: Dockerfile
    container_name: api-gateway-1
    environment:
      - API_PORT=8000
      - INSTANCE_ID=1
      - ZEN_ENDPOINT=http://zen-mcp-1:3000,http://zen-mcp-2:3000
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - KEYCLOAK_URL=${KEYCLOAK_URL}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - redis
      - keycloak
    restart: unless-stopped
    networks:
      - promptcraft-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  api-gateway-2:
    build:
      context: ./src/api
      dockerfile: Dockerfile
    container_name: api-gateway-2
    environment:
      - API_PORT=8000
      - INSTANCE_ID=2
      - ZEN_ENDPOINT=http://zen-mcp-1:3000,http://zen-mcp-2:3000
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - KEYCLOAK_URL=${KEYCLOAK_URL}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - redis
      - keycloak
    restart: unless-stopped
    networks:
      - promptcraft-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === Zen MCP Orchestrators (Multiple Instances) ===
  zen-mcp-1:
    build:
      context: ./zen-mcp-server
      dockerfile: Dockerfile
    container_name: zen-mcp-1
    environment:
      - NODE_ENV=production
      - INSTANCE_ID=1
      - QDRANT_HOST=qdrant
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
    volumes:
      - ./config:/app/config:ro
      - ./knowledge:/app/knowledge:ro
    depends_on:
      - qdrant
      - redis
      - postgres
    restart: unless-stopped
    networks:
      - promptcraft-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  zen-mcp-2:
    build:
      context: ./zen-mcp-server
      dockerfile: Dockerfile
    container_name: zen-mcp-2
    environment:
      - NODE_ENV=production
      - INSTANCE_ID=2
      - QDRANT_HOST=qdrant
      - REDIS_HOST=redis
      - POSTGRES_HOST=postgres
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
    volumes:
      - ./config:/app/config:ro
      - ./knowledge:/app/knowledge:ro
    depends_on:
      - qdrant
      - redis
      - postgres
    restart: unless-stopped
    networks:
      - promptcraft-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === Enterprise Identity & Access ===
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    container_name: keycloak
    ports:
      - "8080:8080"
    environment:
      - KEYCLOAK_ADMIN=${KEYCLOAK_ADMIN_USER}
      - KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}
      - KC_DB=postgres
      - KC_DB_URL=jdbc:postgresql://postgres:5432/keycloak
      - KC_DB_USERNAME=${ANALYTICS_DB_USER}
      - KC_DB_PASSWORD=${ANALYTICS_DB_PASSWORD}
      - KC_HOSTNAME_STRICT=false
      - KC_HTTP_ENABLED=true
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - promptcraft-backend
    command: start-dev
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 60s

  # === Data Layer ===
  postgres:
    image: postgres:15-alpine
    container_name: postgres
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=${ANALYTICS_DB_NAME}
      - POSTGRES_USER=${ANALYTICS_DB_USER}
      - POSTGRES_PASSWORD=${ANALYTICS_DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --locale=C
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./sql/init:/docker-entrypoint-initdb.d:ro
    restart: unless-stopped
    networks:
      - promptcraft-backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${ANALYTICS_DB_USER} -d ${ANALYTICS_DB_NAME}"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    command: redis-server /usr/local/etc/redis/redis.conf
    restart: unless-stopped
    networks:
      - promptcraft-backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  qdrant:
    image: qdrant/qdrant:v1.9.0
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
      - ./qdrant/config.yaml:/qdrant/config/production.yaml:ro
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=INFO
    restart: unless-stopped
    networks:
      - promptcraft-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === Analytics & ML Platform ===
  analytics-engine:
    build:
      context: ./src/enterprise
      dockerfile: Dockerfile.analytics
    container_name: analytics-engine
    environment:
      - ANALYTICS_DB_URL=${ANALYTICS_DB_URL}
      - MLFLOW_TRACKING_URI=${MLFLOW_TRACKING_URI}
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
      - mlflow
    restart: unless-stopped
    networks:
      - promptcraft-backend

  mlflow:
    image: python:3.11-slim
    container_name: mlflow
    ports:
      - "5000:5000"
    environment:
      - MLFLOW_BACKEND_STORE_URI=${ANALYTICS_DB_URL}
      - MLFLOW_ARTIFACT_ROOT=${MLFLOW_ARTIFACT_ROOT}
    volumes:
      - mlflow_artifacts:/mlflow/artifacts
    command: >
      bash -c "pip install mlflow psycopg2-binary &&
               mlflow server --host 0.0.0.0 --port 5000
               --backend-store-uri ${ANALYTICS_DB_URL}
               --default-artifact-root ${MLFLOW_ARTIFACT_ROOT}"
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - promptcraft-backend

  # === Agent Factory ===
  agent-factory:
    build:
      context: ./src/enterprise
      dockerfile: Dockerfile.agent-factory
    container_name: agent-factory
    environment:
      - GIT_BASE_URL=${AGENT_FACTORY_GIT_URL}
      - REGISTRY_URL=${AGENT_FACTORY_REGISTRY_URL}
      - AUTO_PUSH=${AGENT_FACTORY_AUTO_PUSH}
      - POSTGRES_URL=${ANALYTICS_DB_URL}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./templates:/app/templates:ro
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - promptcraft-backend

  # === Custom MCP Registry ===
  mcp-registry:
    build:
      context: ./src/mcp-registry
      dockerfile: Dockerfile
    container_name: mcp-registry
    ports:
      - "8100:8100"
    environment:
      - REGISTRY_PORT=8100
      - POSTGRES_URL=${ANALYTICS_DB_URL}
      - VALIDATION_STRICT=${MCP_VALIDATION_STRICT}
      - SANDBOX_NETWORK=${MCP_SANDBOX_NETWORK}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - postgres
    restart: unless-stopped
    networks:
      - promptcraft-backend
      - mcp-sandbox

  # === Monitoring Stack ===
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    restart: unless-stopped
    networks:
      - promptcraft-backend

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_DATABASE_TYPE=postgres
      - GF_DATABASE_HOST=postgres:5432
      - GF_DATABASE_NAME=grafana
      - GF_DATABASE_USER=${ANALYTICS_DB_USER}
      - GF_DATABASE_PASSWORD=${ANALYTICS_DB_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning:ro
    depends_on:
      - postgres
      - prometheus
    restart: unless-stopped
    networks:
      - promptcraft-backend

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
      - '--web.external-url=http://localhost:9093'
    restart: unless-stopped
    networks:
      - promptcraft-backend

  # === Background Processing ===
  celery-worker:
    build:
      context: ./src/enterprise
      dockerfile: Dockerfile.celery
    container_name: celery-worker
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
      - POSTGRES_URL=${ANALYTICS_DB_URL}
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    networks:
      - promptcraft-backend
    command: celery -A src.enterprise.tasks worker --loglevel=info

  celery-beat:
    build:
      context: ./src/enterprise
      dockerfile: Dockerfile.celery
    container_name: celery-beat
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - POSTGRES_URL=${ANALYTICS_DB_URL}
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    networks:
      - promptcraft-backend
    command: celery -A src.enterprise.tasks beat --loglevel=info

  # === UI Layer (Multiple Instances) ===
  gradio-ui-1:
    build:
      context: ./src/ui
      dockerfile: Dockerfile
    container_name: gradio-ui-1
    environment:
      - INSTANCE_ID=1
      - API_ENDPOINT=http://nginx/api
      - KEYCLOAK_URL=${KEYCLOAK_URL}
      - ENABLE_SSO=true
    depends_on:
      - api-gateway-1
      - api-gateway-2
    restart: unless-stopped
    networks:
      - promptcraft-backend

  gradio-ui-2:
    build:
      context: ./src/ui
      dockerfile: Dockerfile
    container_name: gradio-ui-2
    environment:
      - INSTANCE_ID=2
      - API_ENDPOINT=http://nginx/api
      - KEYCLOAK_URL=${KEYCLOAK_URL}
      - ENABLE_SSO=true
    depends_on:
      - api-gateway-1
      - api-gateway-2
    restart: unless-stopped
    networks:
      - promptcraft-backend

  # === Existing MCP Services (Phase 2-3) ===
  heimdall-mcp:
    image: lcbcfoo/heimdall-mcp-server:latest
    container_name: heimdall-mcp
    restart: unless-stopped
    networks:
      - promptcraft-backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  github-mcp:
    image: github/github-mcp-server:latest
    container_name: github-mcp
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
    restart: unless-stopped
    networks:
      - promptcraft-backend

  code-interpreter-mcp:
    image: executeautomation/mcp-code-runner:latest
    container_name: code-interpreter-mcp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    networks:
      - mcp-sandbox
    restart: unless-stopped

  hitl-mcp:
    image: gotohuman/gotohuman-mcp-server:latest
    container_name: hitl-mcp
    environment:
      - NOTIFICATION_WEBHOOK=${HITL_NOTIFICATION_WEBHOOK}
    restart: unless-stopped
    networks:
      - promptcraft-backend

  # === Backup & Maintenance ===
  backup-service:
    build:
      context: ./src/backup
      dockerfile: Dockerfile
    container_name: backup-service
    environment:
      - BACKUP_SCHEDULE=${BACKUP_SCHEDULE}
      - BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS}
      - POSTGRES_URL=${ANALYTICS_DB_URL}
      - S3_BACKUP_BUCKET=${S3_BACKUP_BUCKET}
    volumes:
      - qdrant_data:/source/qdrant:ro
      - backup_data:/backups
    depends_on:
      - postgres
      - qdrant
    restart: unless-stopped
    networks:
      - promptcraft-backend

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/promptcraft/postgres_data

  redis_data:
    driver: local

  qdrant_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/promptcraft/qdrant_data

  grafana_data:
    driver: local

  prometheus_data:
    driver: local

  alertmanager_data:
    driver: local

  mlflow_artifacts:
    driver: local

  backup_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/promptcraft/backups

networks:
  promptcraft-frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.18.0.0/16

  promptcraft-backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.19.0.0/16

  mcp-sandbox:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.21.0.0/16
```

## 9. Success Criteria & Metrics (Phase 4)

### 9.1. Phase 4 Success Metrics

| Category | Metric | Target | Measurement Method |
|:---------|:-------|:-------|:------------------|
| **Enterprise Adoption** | SSO Integration Success | >99% | Login success rate via SAML/OIDC |
| **Automation Efficiency** | Agent Creation Time | <15 min | Agent Factory CLI measurements |
| **Analytics Value** | Dashboard Usage | >80% daily active users | Grafana access logs |
| **Compliance Readiness** | Audit Log Completeness | 100% | All events logged with proper metadata |
| **Platform Scalability** | Multi-Instance Performance | Linear scaling | Load testing with 2-10 instances |
| **Self-Service Capability** | CLI Tool Adoption | >70% admin tasks via CLI | CLI usage analytics |

### 9.2. Enterprise Quality Gates

**Security & Compliance Gate:**

* [ ] All authentication flows work with external SAML/OIDC
* [ ] Complete audit trail for all user actions
* [ ] Data retention policies enforced
* [ ] GDPR compliance features functional
* [ ] Role-based access controls working

**Operational Excellence Gate:**

* [ ] Multi-instance deployment stable under load
* [ ] Automated backup and recovery tested
* [ ] Monitoring alerts properly configured
* [ ] Performance metrics within SLA targets
* [ ] Cost tracking and optimization recommendations working

**Developer Experience Gate:**

* [ ] Agent creation via CLI completes in <15 minutes
* [ ] Custom MCP integration process documented and tested
* [ ] Analytics API provides actionable insights
* [ ] Documentation complete and accessible
* [ ] Error handling and recovery mechanisms proven

## 10. Timeline & Milestones (Phase 4)

### Week 12: Enterprise Infrastructure

* [ ] Deploy PostgreSQL analytics database
* [ ] Implement Keycloak SSO integration
* [ ] Set up multi-instance load balancing
* [ ] Configure enterprise monitoring stack

### Week 13: Analytics & Intelligence

* [ ] Deploy MLflow and analytics engine
* [ ] Implement usage prediction models
* [ ] Create Grafana dashboards and alerts
* [ ] Build cost optimization recommendations

### Week 14: Automation Tools

* [ ] Complete Agent Factory implementation
* [ ] Deploy Custom MCP Registry
* [ ] Build CLI tools for administration
* [ ] Implement automated backup systems

### Week 15: Enterprise Features

* [ ] Complete audit logging and compliance
* [ ] Implement role-based access controls
* [ ] Deploy background processing with Celery
* [ ] Finalize enterprise security hardening

### Week 16: Production Readiness

* [ ] Complete load testing and optimization
* [ ] Finalize documentation and training materials
* [ ] Conduct security audit and penetration testing
* [ ] Prepare for enterprise customer deployments

This Phase 4 specification completes the transformation of PromptCraft-Hybrid into a comprehensive, enterprise-ready
AI automation platform while maintaining the rapid delivery principles established throughout the project's development
phases.
