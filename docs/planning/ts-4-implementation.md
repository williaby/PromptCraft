---
title: PromptCraft-Hybrid Phase 4 Implementation
version: 2.0
status: published
component: Architecture
tags: ['phase-4', 'enterprise', 'implementation', 'code-examples']
source: PromptCraft-Hybrid Project
purpose: To provide detailed technical implementation guide with complete code examples and configurations for Phase 4 enterprise features.
---

# PromptCraft-Hybrid: Phase 4 Implementation

Version: 2.0
Status: Updated for v7.0 Architecture
Audience: Development Team, DevOps Engineers

## 1. Data Flow Diagrams

### 1.1. Automated Agent Creation Flow

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

### 1.2. Advanced Analytics & Learning Flow

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

### 1.3. Enterprise SSO Integration Flow

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

### 1.4. Custom MCP Integration Flow

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

## 2. API Contracts & Data Schemas

### 2.1. Agent Factory API

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

### 2.2. Analytics & Insights API

**Endpoint:** `GET /api/v4/analytics/insights`

**Authentication:** JWT token with analytics permissions

**Query Parameters:**
```
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

### 2.3. Custom MCP Registry Schema

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

### 2.4. Enterprise Audit Schema

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

## 3. Component Implementation Details

### 3.1. Automated Agent Factory

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

### 3.2. Advanced Analytics Engine

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
```

### 3.3. Enterprise SSO Integration

```python
# src/enterprise/sso_integration.py
import jwt
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from fastapi import HTTPException, Request, Depends
from keycloak import KeycloakOpenID
import aioredis
import hashlib
import logging

logger = logging.getLogger(__name__)

class EnterpriseSSOManager:
    """Enterprise SSO integration with Keycloak and audit logging"""

    def __init__(self, config: Dict):
        self.config = config
        self.keycloak_client = KeycloakOpenID(
            server_url=config['keycloak_server_url'],
            client_id=config['keycloak_client_id'],
            realm_name=config['keycloak_realm'],
            client_secret_key=config['keycloak_client_secret']
        )
        self.redis_client = None
        self.audit_logger = AuditLogger(config)

    async def initialize(self):
        """Initialize Redis connection for session management"""
        self.redis_client = await aioredis.from_url(
            self.config['redis_url'],
            encoding="utf-8",
            decode_responses=True
        )

    async def authenticate_user(self, token: str, request: Request) -> Dict:
        """Authenticate user with JWT token and log audit event"""
        try:
            # Verify token with Keycloak
            token_info = self.keycloak_client.introspect(token)
            if not token_info.get('active', False):
                raise HTTPException(status_code=401, detail="Invalid or expired token")

            # Extract user information
            user_info = {
                'user_id': token_info.get('sub'),
                'username': token_info.get('preferred_username'),
                'email': token_info.get('email'),
                'organization': token_info.get('organization'),
                'roles': token_info.get('realm_access', {}).get('roles', []),
                'permissions': token_info.get('resource_access', {})
            }

            # Create session
            session_id = await self._create_user_session(user_info, token)

            # Log authentication event
            await self.audit_logger.log_authentication(
                user_id=user_info['user_id'],
                session_id=session_id,
                request=request,
                status='success'
            )

            return {
                'user': user_info,
                'session_id': session_id,
                'expires_at': datetime.now() + timedelta(hours=8)
            }

        except Exception as e:
            # Log failed authentication
            await self.audit_logger.log_authentication(
                user_id=None,
                session_id=None,
                request=request,
                status='failure',
                error=str(e)
            )
            raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

    async def _create_user_session(self, user_info: Dict, token: str) -> str:
        """Create and store user session in Redis"""
        session_id = hashlib.sha256(f"{user_info['user_id']}{datetime.now().isoformat()}".encode()).hexdigest()

        session_data = {
            'user_id': user_info['user_id'],
            'username': user_info['username'],
            'organization': user_info['organization'],
            'roles': ','.join(user_info['roles']),
            'token': token,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }

        # Store session with 8-hour expiry
        await self.redis_client.hset(f"session:{session_id}", mapping=session_data)
        await self.redis_client.expire(f"session:{session_id}", 28800)  # 8 hours

        return session_id

class AuditLogger:
    """Comprehensive audit logging for compliance"""

    def __init__(self, config: Dict):
        self.config = config
        self.db_engine = create_engine(config['analytics_db_url'])

    async def log_authentication(self, user_id: Optional[str], session_id: Optional[str],
                                request: Request, status: str, error: Optional[str] = None):
        """Log authentication events"""
        event = {
            'event_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'session_id': session_id,
            'event_type': 'authentication',
            'event_category': 'security',
            'severity': 'error' if status == 'failure' else 'info',
            'source': {
                'component': 'api_gateway',
                'host': request.client.host,
                'ip_address': request.client.host
            },
            'action': {
                'operation': 'sso_login',
                'method': request.method,
                'endpoint': str(request.url.path)
            },
            'context': {
                'user_agent': request.headers.get('user-agent'),
                'request_id': request.headers.get('x-request-id')
            },
            'outcome': {
                'status': status,
                'error_message': error
            }
        }

        await self._store_audit_event(event)

    async def _store_audit_event(self, event: Dict):
        """Store audit event in database"""
        with self.db_engine.connect() as conn:
            conn.execute(text("""
                INSERT INTO audit_events (
                    event_id, timestamp, user_id, session_id, event_type,
                    event_category, severity, source, action, context, outcome
                ) VALUES (
                    :event_id, :timestamp, :user_id, :session_id, :event_type,
                    :event_category, :severity, :source, :action, :context, :outcome
                )
            """), {
                'event_id': event['event_id'],
                'timestamp': event['timestamp'],
                'user_id': event['user_id'],
                'session_id': event['session_id'],
                'event_type': event['event_type'],
                'event_category': event['event_category'],
                'severity': event['severity'],
                'source': json.dumps(event['source']),
                'action': json.dumps(event['action']),
                'context': json.dumps(event['context']),
                'outcome': json.dumps(event['outcome'])
            })
            conn.commit()
```

### 3.4. CLI Tools for Agent Management

```python
# src/enterprise/cli.py
import typer
import asyncio
import yaml
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import track
import questionary

app = typer.Typer(name="pc-hybrid")
console = Console()

@app.command()
def create_agent(
    name: str = typer.Option(..., help="Agent name (snake_case)"),
    domain: str = typer.Option(..., help="Domain area (e.g., security, finance)"),
    description: str = typer.Option(..., help="Agent description"),
    capabilities: List[str] = typer.Option(None, help="Agent capabilities"),
    auto_deploy: bool = typer.Option(False, help="Auto-deploy after creation"),
    interactive: bool = typer.Option(False, help="Interactive configuration mode")
):
    """Create a new specialized agent"""
    if interactive:
        name, domain, description, capabilities = _interactive_agent_config()

    console.print(f"Creating agent: {name}", style="bold green")

    agent_spec = {
        "name": name,
        "display_name": name.replace('_', ' ').title(),
        "description": description,
        "domain": domain,
        "keywords": [domain, name],
        "capabilities": capabilities or ["general_assistance"],
        "knowledge_sources": []
    }

    deployment_config = {
        "environment": "development",
        "auto_deploy": auto_deploy,
        "resource_limits": {
            "memory": "512M",
            "cpu": "0.5"
        }
    }

    # Create agent using factory
    try:
        factory = AgentFactory(load_config())
        creation_id = asyncio.run(factory.create_agent(agent_spec, deployment_config))
        console.print(f"Agent creation started: {creation_id}", style="bold blue")
        console.print("Use 'pc-hybrid status <creation_id>' to check progress")
    except Exception as e:
        console.print(f"Failed to create agent: {str(e)}", style="bold red")
        raise typer.Exit(1)

@app.command()
def list_agents():
    """List all available agents"""
    agents = asyncio.run(_get_agent_list())

    table = Table(title="Available Agents")
    table.add_column("Agent ID", style="cyan")
    table.add_column("Display Name", style="magenta")
    table.add_column("Domain", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Created", style="blue")

    for agent in agents:
        table.add_row(
            agent['id'],
            agent['display_name'],
            agent['domain'],
            agent['status'],
            agent['created_at']
        )

    console.print(table)

@app.command()
def deploy_agent(
    agent_name: str = typer.Argument(..., help="Agent name to deploy"),
    environment: str = typer.Option("development", help="Target environment"),
    replicas: int = typer.Option(1, help="Number of replicas")
):
    """Deploy an agent to specified environment"""
    console.print(f"Deploying {agent_name} to {environment}...", style="bold yellow")

    deployment_result = asyncio.run(_deploy_agent(agent_name, environment, replicas))

    if deployment_result['success']:
        console.print(f"Agent {agent_name} deployed successfully!", style="bold green")
        console.print(f"Endpoint: {deployment_result['endpoint']}")
    else:
        console.print(f"Deployment failed: {deployment_result['error']}", style="bold red")
        raise typer.Exit(1)

def _interactive_agent_config():
    """Interactive agent configuration wizard"""
    console.print("Agent Configuration Wizard", style="bold blue")

    name = questionary.text("Agent name (snake_case):").ask()
    domain = questionary.select(
        "Domain area:",
        choices=["security", "web_development", "finance", "data_analysis", "other"]
    ).ask()
    description = questionary.text("Agent description:").ask()

    capabilities = questionary.checkbox(
        "Select capabilities:",
        choices=[
            "code_analysis",
            "security_scanning",
            "test_generation",
            "documentation",
            "api_integration",
            "data_processing"
        ]
    ).ask()

    return name, domain, description, capabilities

# Configuration
def load_config() -> Dict:
    """Load CLI configuration"""
    config_path = Path.home() / ".promptcraft" / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f)
    else:
        return {
            'agent_factory_url': 'http://localhost:8000',
            'git_base_url': 'https://github.com/your-org',
            'registry_url': 'localhost:5000'
        }

if __name__ == "__main__":
    app()
```

## 4. Environment Configuration (Phase 4)

```bash
# .env.example - Phase 4 Enterprise Configuration

# === Core Services (From Previous Phases) ===
QDRANT_HOST=192.168.1.16
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379
API_BASE_URL=http://192.168.1.205:8000

# === AI Models ===
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key

# === Phase 4 Enterprise Services ===

# PostgreSQL Analytics Database
ANALYTICS_DB_HOST=localhost
ANALYTICS_DB_PORT=5432
ANALYTICS_DB_NAME=promptcraft_analytics
ANALYTICS_DB_USER=analytics_user
ANALYTICS_DB_PASSWORD=secure_password
ANALYTICS_DB_URL=postgresql://analytics_user:secure_password@localhost:5432/promptcraft_analytics

# Keycloak SSO
KEYCLOAK_SERVER_URL=http://localhost:8080/auth
KEYCLOAK_REALM=promptcraft
KEYCLOAK_CLIENT_ID=promptcraft-app
KEYCLOAK_CLIENT_SECRET=your-client-secret

# SAML Configuration
SAML_SP_ENTITY_ID=promptcraft-app
SAML_SP_ACS_URL=http://localhost:7860/auth/saml/acs
SAML_IDP_METADATA_URL=https://your-idp.com/metadata

# Enterprise Security
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=your-vault-token
JWT_SECRET_KEY=your-jwt-secret
ENCRYPTION_KEY=your-encryption-key

# Audit & Compliance
AUDIT_LOG_LEVEL=INFO
AUDIT_RETENTION_DAYS=2555  # 7 years
COMPLIANCE_MODE=SOC2
DATA_CLASSIFICATION_ENABLED=true

# Analytics & ML
MLFLOW_TRACKING_URI=http://localhost:5000
MLFLOW_EXPERIMENT_NAME=promptcraft-optimization
ANALYTICS_CACHE_TTL_MINUTES=15
BATCH_PROCESSING_SCHEDULE="0 */1 * * *"  # Hourly

# Monitoring & Observability
PROMETHEUS_HOST=localhost
PROMETHEUS_PORT=9090
GRAFANA_HOST=localhost
GRAFANA_PORT=3000
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831

# Agent Factory
AGENT_FACTORY_GIT_BASE_URL=https://github.com/your-org
AGENT_FACTORY_REGISTRY_URL=localhost:5000
AGENT_FACTORY_AUTO_PUSH=true
AGENT_FACTORY_AUTO_DEPLOY=false

# Custom MCP Registry
MCP_REGISTRY_URL=http://localhost:8001
MCP_VALIDATION_ENABLED=true
MCP_SANDBOX_LEVEL=strict
MCP_TIMEOUT_SECONDS=30

# Load Balancing & Scaling
NGINX_HOST=192.168.1.205
NGINX_PORT=80
API_REPLICAS=3
UI_REPLICAS=2
ZEN_MCP_REPLICAS=2

# Backup & Disaster Recovery
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
DISASTER_RECOVERY_RTO_HOURS=4
DISASTER_RECOVERY_RPO_HOURS=1

# Enterprise Features
ENTERPRISE_MODE=true
MULTI_TENANT_ENABLED=true
USAGE_BILLING_ENABLED=true
ADVANCED_ANALYTICS_ENABLED=true

# Development & Debug
DEBUG=false
LOG_LEVEL=INFO
PROFILE_PERFORMANCE=false
ENABLE_DEBUG_ENDPOINTS=false
```

## 5. Docker Compose Configuration (Phase 4)

```yaml
# docker-compose.yml - Phase 4 Enterprise Production
version: '3.8'

networks:
  promptcraft-enterprise:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  postgres_data:
  redis_data:
  grafana_data:
  prometheus_data:
  mlflow_data:
  vault_data:

services:
  # === Load Balancer ===
  nginx:
    image: nginx:latest
    container_name: promptcraft-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf
      - ./config/ssl:/etc/nginx/ssl
    networks:
      - promptcraft-enterprise
    depends_on:
      - api-gateway-1
      - api-gateway-2
      - api-gateway-3
      - gradio-ui-1
      - gradio-ui-2
    restart: unless-stopped

  # === Application Layer (Multiple Instances) ===
  api-gateway-1:
    build: .
    container_name: promptcraft-api-1
    environment:
      - INSTANCE_ID=api-1
      - REDIS_URL=redis://redis:6379
      - ANALYTICS_DB_URL=postgresql://analytics_user:${ANALYTICS_DB_PASSWORD}@postgres:5432/promptcraft_analytics
    networks:
      - promptcraft-enterprise
    depends_on:
      - postgres
      - redis
      - keycloak
    restart: unless-stopped

  api-gateway-2:
    build: .
    container_name: promptcraft-api-2
    environment:
      - INSTANCE_ID=api-2
      - REDIS_URL=redis://redis:6379
      - ANALYTICS_DB_URL=postgresql://analytics_user:${ANALYTICS_DB_PASSWORD}@postgres:5432/promptcraft_analytics
    networks:
      - promptcraft-enterprise
    depends_on:
      - postgres
      - redis
      - keycloak
    restart: unless-stopped

  api-gateway-3:
    build: .
    container_name: promptcraft-api-3
    environment:
      - INSTANCE_ID=api-3
      - REDIS_URL=redis://redis:6379
      - ANALYTICS_DB_URL=postgresql://analytics_user:${ANALYTICS_DB_PASSWORD}@postgres:5432/promptcraft_analytics
    networks:
      - promptcraft-enterprise
    depends_on:
      - postgres
      - redis
      - keycloak
    restart: unless-stopped

  gradio-ui-1:
    build:
      context: .
      dockerfile: Dockerfile.ui
    container_name: promptcraft-ui-1
    environment:
      - API_BASE_URL=http://nginx/api
      - INSTANCE_ID=ui-1
    networks:
      - promptcraft-enterprise
    restart: unless-stopped

  gradio-ui-2:
    build:
      context: .
      dockerfile: Dockerfile.ui
    container_name: promptcraft-ui-2
    environment:
      - API_BASE_URL=http://nginx/api
      - INSTANCE_ID=ui-2
    networks:
      - promptcraft-enterprise
    restart: unless-stopped

  # === Zen MCP Server (Multiple Instances) ===
  zen-mcp-1:
    image: zen-mcp-server:latest
    container_name: zen-mcp-1
    environment:
      - INSTANCE_ID=zen-1
      - REDIS_URL=redis://redis:6379
    networks:
      - promptcraft-enterprise
    depends_on:
      - redis
    restart: unless-stopped

  zen-mcp-2:
    image: zen-mcp-server:latest
    container_name: zen-mcp-2
    environment:
      - INSTANCE_ID=zen-2
      - REDIS_URL=redis://redis:6379
    networks:
      - promptcraft-enterprise
    depends_on:
      - redis
    restart: unless-stopped

  # === Data Layer ===
  postgres:
    image: postgres:15-alpine
    container_name: promptcraft-postgres
    environment:
      - POSTGRES_DB=promptcraft_analytics
      - POSTGRES_USER=analytics_user
      - POSTGRES_PASSWORD=${ANALYTICS_DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./config/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - promptcraft-enterprise
    ports:
      - "5432:5432"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U analytics_user -d promptcraft_analytics"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    container_name: promptcraft-redis
    volumes:
      - redis_data:/data
      - ./config/redis.conf:/usr/local/etc/redis/redis.conf
    networks:
      - promptcraft-enterprise
    ports:
      - "6379:6379"
    restart: unless-stopped
    command: redis-server /usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === Security & Auth ===
  keycloak:
    image: quay.io/keycloak/keycloak:latest
    container_name: promptcraft-keycloak
    environment:
      - KEYCLOAK_ADMIN=admin
      - KEYCLOAK_ADMIN_PASSWORD=${KEYCLOAK_ADMIN_PASSWORD}
      - KC_DB=postgres
      - KC_DB_URL=jdbc:postgresql://postgres:5432/keycloak
      - KC_DB_USERNAME=keycloak
      - KC_DB_PASSWORD=${KEYCLOAK_DB_PASSWORD}
    networks:
      - promptcraft-enterprise
    ports:
      - "8080:8080"
    depends_on:
      - postgres
    restart: unless-stopped
    command: start --optimized

  vault:
    image: vault:latest
    container_name: promptcraft-vault
    environment:
      - VAULT_DEV_ROOT_TOKEN_ID=${VAULT_TOKEN}
      - VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200
    volumes:
      - vault_data:/vault/data
      - ./config/vault.hcl:/vault/config/vault.hcl
    networks:
      - promptcraft-enterprise
    ports:
      - "8200:8200"
    restart: unless-stopped
    cap_add:
      - IPC_LOCK

  # === Monitoring & Observability ===
  prometheus:
    image: prom/prometheus:latest
    container_name: promptcraft-prometheus
    volumes:
      - prometheus_data:/prometheus
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - promptcraft-enterprise
    ports:
      - "9090:9090"
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    container_name: promptcraft-grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./config/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./config/grafana/datasources:/etc/grafana/provisioning/datasources
    networks:
      - promptcraft-enterprise
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
    restart: unless-stopped

  jaeger:
    image: jaegertracing/all-in-one:latest
    container_name: promptcraft-jaeger
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - promptcraft-enterprise
    ports:
      - "16686:16686"
      - "14268:14268"
    restart: unless-stopped

  # === ML & Analytics ===
  mlflow:
    image: python:3.11-slim
    container_name: promptcraft-mlflow
    environment:
      - MLFLOW_BACKEND_STORE_URI=postgresql://analytics_user:${ANALYTICS_DB_PASSWORD}@postgres:5432/promptcraft_analytics
      - MLFLOW_DEFAULT_ARTIFACT_ROOT=/mlflow/artifacts
    volumes:
      - mlflow_data:/mlflow/artifacts
    networks:
      - promptcraft-enterprise
    ports:
      - "5000:5000"
    depends_on:
      - postgres
    restart: unless-stopped
    command: >
      bash -c "
        pip install mlflow psycopg2-binary &&
        mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri postgresql://analytics_user:${ANALYTICS_DB_PASSWORD}@postgres:5432/promptcraft_analytics --default-artifact-root /mlflow/artifacts
      "

  # === Custom MCP Registry ===
  mcp-registry:
    build:
      context: .
      dockerfile: Dockerfile.mcp-registry
    container_name: promptcraft-mcp-registry
    environment:
      - REGISTRY_DB_URL=postgresql://analytics_user:${ANALYTICS_DB_PASSWORD}@postgres:5432/promptcraft_analytics
      - VALIDATION_ENABLED=true
    networks:
      - promptcraft-enterprise
    ports:
      - "8001:8001"
    depends_on:
      - postgres
    restart: unless-stopped

  # === Background Workers ===
  celery-worker:
    build: .
    container_name: promptcraft-celery-worker
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - ANALYTICS_DB_URL=postgresql://analytics_user:${ANALYTICS_DB_PASSWORD}@postgres:5432/promptcraft_analytics
    networks:
      - promptcraft-enterprise
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    command: celery -A src.enterprise.tasks worker --loglevel=info

  celery-beat:
    build: .
    container_name: promptcraft-celery-beat
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    networks:
      - promptcraft-enterprise
    depends_on:
      - redis
    restart: unless-stopped
    command: celery -A src.enterprise.tasks beat --loglevel=info
```

This implementation document provides the complete technical foundation for Phase 4 enterprise features, including automated agent creation, advanced analytics, SSO integration, and comprehensive monitoring systems.
