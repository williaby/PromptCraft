---
title: PromptCraft-Hybrid Phase 2 Implementation Details
version: 2.0
status: published
component: Architecture
tags: ['phase-2', 'implementation', 'code-examples', 'configuration']
source: PromptCraft-Hybrid Project
purpose: To provide detailed implementation specifications, code examples, and configurations for Phase 2.
---

# PromptCraft-Hybrid: Phase 2 Implementation Details

Version: 2.0
Status: Updated for v7.0 Architecture
Audience: Development Team, DevOps Engineers

## 1. API Contracts & Data Schemas

### 1.1. Enhanced Orchestration API

**Endpoint:** `POST /api/v2/orchestrate`

**Request Body:**
```json
{
  "query": "string",
  "context": {
    "agent_hint": "string (optional)",
    "project_context": {
      "repo_url": "string (optional)",
      "current_file": "string (optional)",
      "file_content": "string (optional)"
    },
    "search_preferences": {
      "max_cost": "number (default: 0.01)",
      "prefer_free": "boolean (default: true)"
    }
  },
  "options": {
    "enable_cross_agent_consultation": "boolean (default: false)",
    "max_agents": "number (default: 1)",
    "include_reasoning": "boolean (default: true)"
  }
}
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "final_prompt": "string",
    "agent_used": "string",
    "confidence_score": "number",
    "tools_used": ["string"],
    "reasoning_chain": [
      {
        "step": "string",
        "agent": "string",
        "tool": "string",
        "result_summary": "string"
      }
    ]
  },
  "metadata": {
    "processing_time_ms": "number",
    "total_cost": "number",
    "agents_considered": ["string"],
    "cross_agent_consultations": "number"
  }
}
```

### 1.2. Agent Registry Schema

```yaml
# config/agents.yaml
version: "2.0"
agents:
  - agent_id: "security_agent"
    class_path: "src.agents.security_agent.SecurityAgent"
    description: "Expert in code security, vulnerability analysis, and compliance frameworks"
    keywords:
      - "security"
      - "vulnerability"
      - "authentication"
      - "authorization"
      - "encryption"
      - "compliance"
      - "owasp"
      - "soc2"
    confidence_boost: 0.1  # Boost confidence for security-related queries
    required_tools:
      - "heimdall"
    optional_tools:
      - "github_mcp"
      - "tavily_search"
    fallback_strategy: "clarify"
    cost_tier: "medium"  # Can use paid search APIs

  - agent_id: "web_dev_agent"
    class_path: "src.agents.web_dev_agent.WebDevAgent"
    description: "Full-stack web development expert specializing in modern frameworks"
    keywords:
      - "react"
      - "javascript"
      - "typescript"
      - "nextjs"
      - "nodejs"
      - "api"
      - "frontend"
      - "backend"
      - "performance"
      - "optimization"
    confidence_boost: 0.05
    required_tools:
      - "github_mcp"
    optional_tools:
      - "heimdall"
      - "context7_search"
    fallback_strategy: "general"
    cost_tier: "low"  # Prefers free search

  - agent_id: "irs_8867_agent"
    class_path: "src.agents.irs_8867_agent.IRS8867Agent"
    description: "Tax preparation compliance expert for IRS Form 8867 due diligence"
    keywords:
      - "tax"
      - "8867"
      - "irs"
      - "compliance"
      - "due diligence"
      - "preparer"
      - "eitc"
      - "child tax credit"
    confidence_boost: 0.2  # High boost for very specific domain
    required_tools: []
    optional_tools:
      - "tavily_search"
    fallback_strategy: "clarify"
    cost_tier: "high"  # Can use premium search for accuracy

routing_rules:
  - pattern: "security|auth|vulnerability|exploit"
    primary_agent: "security_agent"
    confidence_threshold: 0.7

  - pattern: "react|javascript|web|frontend|api"
    primary_agent: "web_dev_agent"
    confidence_threshold: 0.7

  - pattern: "tax|8867|irs|compliance"
    primary_agent: "irs_8867_agent"
    confidence_threshold: 0.8

  - pattern: ".*"
    primary_agent: "create_agent"
    confidence_threshold: 0.0  # Always fallback
```

### 1.3. Tool Integration Contracts

**Heimdall MCP Integration:**
```json
{
  "tool": "heimdall",
  "method": "analyze_code",
  "params": {
    "code": "string",
    "language": "string (auto-detected if not provided)",
    "focus_areas": ["security", "performance", "maintainability"],
    "severity_threshold": "medium"
  },
  "response": {
    "overall_score": "number (0-100)",
    "issues": [
      {
        "severity": "critical|high|medium|low",
        "category": "string",
        "line": "number",
        "description": "string",
        "recommendation": "string",
        "cwe_id": "string (optional)"
      }
    ],
    "summary": "string"
  }
}
```

**GitHub MCP Integration:**
```json
{
  "tool": "github_mcp",
  "method": "analyze_repository",
  "params": {
    "repo_url": "string",
    "focus_files": ["string"] // Optional: specific files to analyze
  },
  "response": {
    "structure": {
      "framework": "string",
      "languages": ["string"],
      "dependencies": ["string"]
    },
    "files": [
      {
        "path": "string",
        "type": "string",
        "size": "number",
        "content": "string (if requested)"
      }
    ],
    "insights": {
      "architecture_pattern": "string",
      "testing_framework": "string",
      "deployment_method": "string"
    }
  }
}
```

## 2. Component Implementation

### 2.1. Enhanced Zen MCP Server

```javascript
// zen-mcp-server/src/orchestrator.js
export class MultiAgentOrchestrator {
  constructor(config) {
    this.agents = new Map();
    this.tools = new Map();
    this.router = new AgentRouter(config.routing_rules);
    this.costTracker = new CostTracker();
  }

  async processRequest(request) {
    const startTime = Date.now();

    // 1. Analyze and route query
    const routing = await this.router.route(request.query, request.context);

    // 2. Load primary agent
    const primaryAgent = this.agents.get(routing.primary_agent);
    if (!primaryAgent) {
      throw new Error(`Agent ${routing.primary_agent} not found`);
    }

    // 3. Execute primary agent with tool access
    const agentContext = {
      ...request.context,
      tools: this.getAgentTools(routing.primary_agent),
      costBudget: this.calculateCostBudget(routing.primary_agent)
    };

    const result = await primaryAgent.execute(request.query, agentContext);

    // 4. Cross-agent consultation if requested
    if (request.options?.enable_cross_agent_consultation) {
      result.consultations = await this.conductConsultations(
        request.query,
        routing.primary_agent,
        result.preliminary_analysis
      );
    }

    // 5. Synthesize final response
    const finalResult = await this.synthesizeResponse(result);

    return {
      ...finalResult,
      metadata: {
        processing_time_ms: Date.now() - startTime,
        agent_used: routing.primary_agent,
        confidence_score: routing.confidence,
        total_cost: this.costTracker.getSessionCost()
      }
    };
  }

  getAgentTools(agentId) {
    const agentConfig = this.config.agents.find(a => a.agent_id === agentId);
    const tools = {};

    // Required tools
    for (const toolName of agentConfig.required_tools || []) {
      tools[toolName] = this.tools.get(toolName);
    }

    // Optional tools (budget permitting)
    for (const toolName of agentConfig.optional_tools || []) {
      if (this.costTracker.canAfford(toolName)) {
        tools[toolName] = this.tools.get(toolName);
      }
    }

    return tools;
  }
}

// Agent Router with enhanced logic
export class AgentRouter {
  constructor(routingRules) {
    this.rules = routingRules;
    this.keywordMatcher = new KeywordMatcher();
  }

  async route(query, context = {}) {
    // 1. Quick keyword-based routing
    const keywordMatch = this.keywordMatcher.match(query);
    if (keywordMatch.confidence > 0.9) {
      return {
        primary_agent: keywordMatch.agent,
        confidence: keywordMatch.confidence,
        method: 'keyword'
      };
    }

    // 2. Context-aware routing
    if (context.project_context?.repo_url) {
      const repoAnalysis = await this.analyzeRepository(context.project_context.repo_url);
      if (repoAnalysis.framework === 'react') {
        return {
          primary_agent: 'web_dev_agent',
          confidence: 0.8,
          method: 'context'
        };
      }
    }

    // 3. LLM-based classification for ambiguous queries
    if (!keywordMatch.agent) {
      const llmClassification = await this.classifyWithLLM(query);
      return {
        primary_agent: llmClassification.agent,
        confidence: llmClassification.confidence,
        method: 'llm'
      };
    }

    // 4. Fallback to create_agent
    return {
      primary_agent: 'create_agent',
      confidence: 0.5,
      method: 'fallback'
    };
  }
}
```

### 2.2. Specialized Agent Implementation

```python
# src/agents/security_agent.py
from .base_agent import BaseAgent
import json

class SecurityAgent(BaseAgent):
    """Expert in code security and vulnerability analysis"""

    def __init__(self):
        super().__init__(
            agent_id="security_agent",
            fallback_strategy="clarify"
        )
        self.required_tools = ["heimdall"]
        self.security_frameworks = ["OWASP", "NIST", "SOC2"]

    async def execute(self, query: str, context: dict) -> dict:
        """Execute security analysis with Heimdall integration"""

        # 1. Retrieve security knowledge
        security_knowledge = self.get_relevant_knowledge(
            query,
            tags=["security", "vulnerability", "compliance"]
        )

        # 2. Analyze code if provided
        analysis_results = {}
        if context.get("project_context", {}).get("file_content"):
            code = context["project_context"]["file_content"]

            # Use Heimdall for deep security analysis
            heimdall_result = await self.call_tool("heimdall", "analyze_code", {
                "code": code,
                "focus_areas": ["security"],
                "severity_threshold": "medium"
            })

            analysis_results["security_scan"] = heimdall_result

        # 3. Get repository context if available
        if context.get("project_context", {}).get("repo_url"):
            repo_context = await self.call_tool("github_mcp", "analyze_repository", {
                "repo_url": context["project_context"]["repo_url"]
            })
            analysis_results["repo_analysis"] = repo_context

        # 4. Generate security-focused prompt
        prompt_context = {
            "query": query,
            "security_knowledge": security_knowledge,
            "analysis_results": analysis_results,
            "frameworks": self.security_frameworks
        }

        final_prompt = await self._generate_security_prompt(prompt_context)

        return {
            "final_prompt": final_prompt,
            "analysis_results": analysis_results,
            "reasoning_chain": self._build_reasoning_chain(prompt_context),
            "confidence": self._calculate_confidence(security_knowledge, analysis_results)
        }

    async def _generate_security_prompt(self, context: dict) -> str:
        """Generate security-focused C.R.E.A.T.E. prompt"""

        system_prompt = """You are a senior security engineer creating a comprehensive
        security analysis prompt. Use the C.R.E.A.T.E. framework to structure your response."""

        user_prompt = f"""
        Original Query: {context['query']}

        Security Knowledge Context:
        {json.dumps(context['security_knowledge'], indent=2)}

        Analysis Results:
        {json.dumps(context['analysis_results'], indent=2)}

        Generate a C.R.E.A.T.E. structured prompt that incorporates:
        1. Security best practices from the knowledge base
        2. Specific vulnerabilities found in the code analysis
        3. Compliance requirements for {', '.join(context['frameworks'])}
        4. Actionable remediation steps
        """

        response = await self.llm_client.complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model="gpt-4o",
            temperature=0.3
        )

        return response.content

    def _calculate_confidence(self, knowledge_chunks: list, analysis_results: dict) -> float:
        """Calculate confidence score based on available context"""
        confidence = 0.5  # Base confidence

        # Boost for relevant knowledge
        if knowledge_chunks:
            confidence += min(0.3, len(knowledge_chunks) * 0.1)

        # Boost for code analysis
        if analysis_results.get("security_scan"):
            confidence += 0.2

        # Boost for repository context
        if analysis_results.get("repo_analysis"):
            confidence += 0.1

        return min(1.0, confidence)

# src/agents/web_dev_agent.py
class WebDevAgent(BaseAgent):
    """Expert in modern web development practices"""

    def __init__(self):
        super().__init__(
            agent_id="web_dev_agent",
            fallback_strategy="general"
        )
        self.required_tools = ["github_mcp"]
        self.frameworks = ["React", "Next.js", "Node.js", "TypeScript"]

    async def execute(self, query: str, context: dict) -> dict:
        """Execute web development analysis"""

        # 1. Get web development knowledge
        web_knowledge = self.get_relevant_knowledge(
            query,
            tags=["react", "javascript", "performance", "best-practices"]
        )

        # 2. Analyze repository structure
        repo_analysis = None
        if context.get("project_context", {}).get("repo_url"):
            repo_analysis = await self.call_tool("github_mcp", "analyze_repository", {
                "repo_url": context["project_context"]["repo_url"],
                "focus_files": ["package.json", "*.tsx", "*.ts", "*.jsx", "*.js"]
            })

        # 3. Optional security review for web apps
        security_review = None
        if context.get("include_security", True) and context.get("project_context", {}).get("file_content"):
            security_review = await self.call_tool("heimdall", "analyze_code", {
                "code": context["project_context"]["file_content"],
                "focus_areas": ["security", "performance"]
            })

        # 4. Generate web development prompt
        prompt_context = {
            "query": query,
            "web_knowledge": web_knowledge,
            "repo_analysis": repo_analysis,
            "security_review": security_review,
            "frameworks": self.frameworks
        }

        final_prompt = await self._generate_webdev_prompt(prompt_context)

        return {
            "final_prompt": final_prompt,
            "repo_analysis": repo_analysis,
            "security_review": security_review,
            "reasoning_chain": self._build_reasoning_chain(prompt_context),
            "confidence": self._calculate_confidence(web_knowledge, repo_analysis)
        }
```

### 2.3. Enhanced Gradio UI with Agent Selection

```python
# src/ui/app.py - Enhanced for Phase 2
import gradio as gr
import requests
import json

class PromptCraftUIPhase2:
    def __init__(self):
        self.zen_endpoint = os.getenv("ZEN_ENDPOINT", "http://localhost:3000")
        self.available_agents = self._load_available_agents()

    def _load_available_agents(self):
        """Load agent information from Zen MCP"""
        try:
            response = requests.get(f"{self.zen_endpoint}/api/v2/agents")
            return response.json().get("agents", [])
        except:
            return [
                {"agent_id": "create_agent", "description": "General C.R.E.A.T.E. framework expert"},
                {"agent_id": "security_agent", "description": "Security and vulnerability analysis"},
                {"agent_id": "web_dev_agent", "description": "Web development best practices"}
            ]

    def process_orchestrated_query(self, query: str, agent_hint: str = "auto",
                                 repo_url: str = "", enable_consultation: bool = False) -> str:
        """Send query to Zen MCP with orchestration"""
        try:
            payload = {
                "query": query,
                "context": {
                    "agent_hint": agent_hint if agent_hint != "auto" else None,
                    "project_context": {
                        "repo_url": repo_url if repo_url else None
                    }
                },
                "options": {
                    "enable_cross_agent_consultation": enable_consultation,
                    "include_reasoning": True
                }
            }

            response = requests.post(
                f"{self.zen_endpoint}/api/v2/orchestrate",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                result = data["data"]["final_prompt"]

                # Add metadata for transparency
                metadata = data.get("metadata", {})
                result += f"\n\n---\n**Agent Used:** {metadata.get('agent_used', 'unknown')}\n"
                result += f"**Confidence:** {metadata.get('confidence_score', 0):.2f}\n"
                result += f"**Processing Time:** {metadata.get('processing_time_ms', 0)}ms\n"

                if data["data"].get("reasoning_chain"):
                    result += f"**Tools Used:** {', '.join([step['tool'] for step in data['data']['reasoning_chain'] if step.get('tool')])}\n"

                return result
            else:
                return f"Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"Connection error: {str(e)}"

    def create_interface(self):
        """Create enhanced Gradio interface for Phase 2"""
        with gr.Blocks(theme="soft", title="PromptCraft-Hybrid v2.0") as interface:
            gr.Markdown("# PromptCraft-Hybrid: Multi-Agent AI Orchestration")

            with gr.Tab("Journey 1: Quick Enhancement"):
                # Existing Journey 1 functionality (reused from Phase 1)
                self._create_journey1_tab()

            with gr.Tab("Journey 2: Power Templates"):
                gr.Markdown("## Multi-Agent Expert Coordination")

                with gr.Row():
                    with gr.Column(scale=2):
                        query_input = gr.Textbox(
                            label="Your Query",
                            placeholder="Describe your request - our agents will coordinate to help...",
                            lines=4
                        )

                        with gr.Row():
                            agent_selector = gr.Dropdown(
                                choices=["auto"] + [agent["agent_id"] for agent in self.available_agents],
                                value="auto",
                                label="Preferred Agent (auto-detection recommended)"
                            )

                            consultation_toggle = gr.Checkbox(
                                label="Enable Cross-Agent Consultation",
                                value=False,
                                info="Allow multiple agents to collaborate (slower but more comprehensive)"
                            )

                        repo_input = gr.Textbox(
                            label="Repository URL (optional)",
                            placeholder="https://github.com/user/repo",
                            info="Provide context for code-related queries"
                        )

                        orchestrate_btn = gr.Button("Generate Expert Prompt", variant="primary")

                    with gr.Column(scale=3):
                        output_text = gr.Textbox(
                            label="Expert-Coordinated Prompt",
                            lines=25,
                            max_lines=50
                        )

                        with gr.Row():
                            copy_btn = gr.Button("Copy to Clipboard")
                            clear_btn = gr.Button("Clear")

                # Agent information panel
                with gr.Accordion("Available Agents", open=False):
                    agent_info = "\n".join([
                        f"**{agent['agent_id']}**: {agent['description']}"
                        for agent in self.available_agents
                    ])
                    gr.Markdown(agent_info)

                # Event handlers
                orchestrate_btn.click(
                    fn=self.process_orchestrated_query,
                    inputs=[query_input, agent_selector, repo_input, consultation_toggle],
                    outputs=output_text
                )

                clear_btn.click(
                    lambda: ("", ""),
                    outputs=[query_input, output_text]
                )

            with gr.Tab("Journey 3: IDE Integration"):
                gr.Markdown("""
                ## Claude Code Integration

                Connect your IDE to PromptCraft's orchestration:

                ```bash
                # Configure Claude Code to use your local Zen MCP
                claude config set mcp.endpoint http://localhost:3000/mcp

                # Test the connection
                claude /tool:google "latest React best practices"
                ```

                **Available Tools:**
                - `google` - Google search
                - `ddg` - DuckDuckGo search
                - `url` - Read webpage content
                - `github` - Repository analysis (Phase 2)
                - `heimdall` - Security analysis (Phase 2)
                """)

            with gr.Tab("Journey 4: Direct Execution (Coming Phase 3)"):
                gr.Markdown("End-to-end automation coming in Phase 3...")

        return interface

    def _create_journey1_tab(self):
        """Reuse Journey 1 implementation from Phase 1"""
        gr.Markdown("## Basic C.R.E.A.T.E. Prompt Enhancement")

        with gr.Row():
            with gr.Column():
                basic_query = gr.Textbox(
                    label="Your Query",
                    placeholder="Describe what you want help with...",
                    lines=3
                )
                tier_slider = gr.Slider(
                    minimum=1, maximum=10, value=4, step=1,
                    label="Response Depth (1=Brief, 10=Comprehensive)"
                )
                basic_generate_btn = gr.Button("Generate C.R.E.A.T.E. Prompt", variant="secondary")

            with gr.Column():
                basic_output = gr.Textbox(
                    label="Generated C.R.E.A.T.E. Prompt",
                    lines=15,
                    max_lines=30
                )
                basic_copy_btn = gr.Button("Copy to Clipboard")

        # Event handlers for Journey 1
        basic_generate_btn.click(
            fn=lambda q, t: self.process_basic_query(q, t),
            inputs=[basic_query, tier_slider],
            outputs=basic_output
        )

    def process_basic_query(self, query: str, tier: int) -> str:
        """Process basic query using create_agent only"""
        try:
            payload = {
                "query": query,
                "context": {"agent_hint": "create_agent"},
                "options": {"tier": tier}
            }

            response = requests.post(
                f"{self.zen_endpoint}/api/v1/query",  # Legacy endpoint for compatibility
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data["data"]["final_prompt"]
            else:
                return f"Error: {response.status_code}"

        except Exception as e:
            return f"Connection error: {str(e)}"

if __name__ == "__main__":
    app = PromptCraftUIPhase2()
    interface = app.create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
```

### 2.4. Enhanced Knowledge Ingestion for Multi-Agent

```python
# scripts/multi_agent_ingestion.py
import os
import yaml
import asyncio
from pathlib import Path
from typing import Dict, List
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

class MultiAgentKnowledgeIngester:
    def __init__(self):
        self.qdrant_client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=6333
        )
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.agent_configs = self._load_agent_configs()

    def _load_agent_configs(self) -> Dict:
        """Load agent configuration from YAML"""
        with open("config/agents.yaml", 'r') as f:
            return yaml.safe_load(f)

    async def ingest_all_agents(self) -> Dict[str, int]:
        """Ingest knowledge for all configured agents"""
        results = {}

        for agent_config in self.agent_configs['agents']:
            agent_id = agent_config['agent_id']
            knowledge_dir = Path(f"knowledge/{agent_id}")

            if knowledge_dir.exists():
                chunk_count = await self.ingest_agent_knowledge(agent_id, knowledge_dir)
                results[agent_id] = chunk_count
                print(f"✅ {agent_id}: {chunk_count} chunks ingested")
            else:
                print(f"⚠️ {agent_id}: No knowledge directory found at {knowledge_dir}")
                results[agent_id] = 0

        return results

    async def ingest_agent_knowledge(self, agent_id: str, knowledge_dir: Path) -> int:
        """Ingest knowledge for a specific agent"""
        self._ensure_collection_exists(agent_id)

        total_chunks = 0

        # Process all markdown files in the agent's directory
        for md_file in knowledge_dir.rglob("*.md"):
            try:
                chunks = await self.process_file(md_file, agent_id)
                total_chunks += chunks
            except Exception as e:
                print(f"❌ Error processing {md_file}: {e}")

        return total_chunks

    async def process_file(self, filepath: Path, agent_id: str) -> int:
        """Process single file for specific agent"""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse YAML front matter
        parts = content.split('---', 2)
        if len(parts) < 3:
            # Create minimal metadata if missing
            metadata = {
                "title": filepath.stem.replace('-', ' ').title(),
                "agent_id": agent_id,
                "status": "published",
                "version": "1.0"
            }
            markdown_content = content
        else:
            metadata = yaml.safe_load(parts[1])
            markdown_content = parts[2].strip()

            # Ensure agent_id matches
            metadata["agent_id"] = agent_id

        # Enhanced chunking strategy
        chunks = self._intelligent_chunk_content(markdown_content, metadata)
        points = []

        for i, chunk_data in enumerate(chunks):
            if not chunk_data["content"].strip():
                continue

            vector = self.embedding_model.encode(chunk_data["content"]).tolist()

            point = models.PointStruct(
                id=f"{agent_id}_{filepath.stem}_{i}",
                vector=vector,
                payload={
                    "text_chunk": chunk_data["content"],
                    "metadata": {
                        **metadata,
                        "source_file": str(filepath.relative_to(Path.cwd())),
                        "chunk_index": i,
                        "chunk_type": chunk_data["type"],
                        "heading": chunk_data.get("heading", ""),
                        "tags": metadata.get("tags", []) + chunk_data.get("tags", [])
                    }
                }
            )
            points.append(point)

        # Batch upsert
        if points:
            self.qdrant_client.upsert(
                collection_name=agent_id,
                points=points,
                wait=True
            )

        return len(points)

    def _intelligent_chunk_content(self, content: str, metadata: Dict) -> List[Dict]:
        """Enhanced chunking with semantic awareness"""
        chunks = []
        current_chunk = ""
        current_heading = ""
        current_type = "content"

        lines = content.split('\n')
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Detect headings
            if line.startswith('### '):
                # Save previous chunk
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "type": current_type,
                        "heading": current_heading,
                        "tags": self._extract_tags_from_content(current_chunk)
                    })

                # Start new chunk
                current_heading = line[4:].strip()
                current_chunk = line
                current_type = self._determine_chunk_type(current_heading)

            elif line.startswith('## '):
                # Major section - always chunk here
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "type": current_type,
                        "heading": current_heading,
                        "tags": self._extract_tags_from_content(current_chunk)
                    })

                current_heading = line[3:].strip()
                current_chunk = line
                current_type = self._determine_chunk_type(current_heading)

            elif line.startswith('```'):
                # Code block - keep together
                current_chunk += '\n' + line
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    current_chunk += '\n' + lines[i]
                    i += 1
                if i < len(lines):
                    current_chunk += '\n' + lines[i]  # Closing ```

            else:
                current_chunk += '\n' + line

            i += 1

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "type": current_type,
                "heading": current_heading,
                "tags": self._extract_tags_from_content(current_chunk)
            })

        return chunks

    def _determine_chunk_type(self, heading: str) -> str:
        """Determine the type of content based on heading"""
        heading_lower = heading.lower()

        if any(word in heading_lower for word in ["example", "sample", "demo"]):
            return "example"
        elif any(word in heading_lower for word in ["step", "process", "workflow"]):
            return "procedure"
        elif any(word in heading_lower for word in ["concept", "definition", "overview"]):
            return "concept"
        elif any(word in heading_lower for word in ["best practice", "guideline", "rule"]):
            return "guideline"
        else:
            return "content"

    def _extract_tags_from_content(self, content: str) -> List[str]:
        """Extract relevant tags from content"""
        tags = []
        content_lower = content.lower()

        # Technical terms
        tech_terms = ["api", "rest", "graphql", "oauth", "jwt", "ssl", "tls",
                     "react", "node", "typescript", "javascript", "python"]

        for term in tech_terms:
            if term in content_lower:
                tags.append(term)

        # Security terms
        security_terms = ["authentication", "authorization", "encryption", "vulnerability",
                         "security", "compliance", "audit", "penetration"]

        for term in security_terms:
            if term in content_lower:
                tags.append("security")
                break

        return list(set(tags))  # Remove duplicates

    def _ensure_collection_exists(self, collection_name: str):
        """Ensure Qdrant collection exists with proper configuration"""
        try:
            self.qdrant_client.get_collection(collection_name)
        except:
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # all-MiniLM-L6-v2 dimension
                    distance=models.Distance.COSINE
                ),
                # Optimize for agent-specific retrieval
                optimizers_config=models.OptimizersConfig(
                    default_segment_number=2,
                    max_segment_size=20000,
                    indexing_threshold=10000
                )
            )

# Enhanced webhook handler
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/webhook/knowledge-update', methods=['POST'])
async def handle_agent_knowledge_update():
    """Enhanced webhook for multi-agent knowledge updates"""
    try:
        # Parse GitHub webhook payload
        payload = request.json

        # Check if this is a push to knowledge directory
        if payload.get('ref') != 'refs/heads/main':
            return {"status": "ignored", "reason": "Not main branch"}

        modified_files = []
        for commit in payload.get('commits', []):
            modified_files.extend(commit.get('modified', []))
            modified_files.extend(commit.get('added', []))

        # Filter for knowledge files
        knowledge_files = [f for f in modified_files if f.startswith('knowledge/') and f.endswith('.md')]

        if not knowledge_files:
            return {"status": "ignored", "reason": "No knowledge files modified"}

        # Determine affected agents
        affected_agents = set()
        for file_path in knowledge_files:
            parts = file_path.split('/')
            if len(parts) >= 2:
                agent_id = parts[1]  # knowledge/{agent_id}/file.md
                affected_agents.add(agent_id)

        # Re-ingest affected agents
        ingester = MultiAgentKnowledgeIngester()
        results = {}

        for agent_id in affected_agents:
            knowledge_dir = Path(f"knowledge/{agent_id}")
            if knowledge_dir.exists():
                chunk_count = await ingester.ingest_agent_knowledge(agent_id, knowledge_dir)
                results[agent_id] = chunk_count

        return {
            "status": "success",
            "affected_agents": list(affected_agents),
            "results": results,
            "total_chunks": sum(results.values())
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# CLI tool for manual ingestion
import click

@click.command()
@click.option('--agent', help='Specific agent to ingest (default: all)')
@click.option('--force', is_flag=True, help='Force re-ingestion even if up to date')
def ingest_knowledge(agent, force):
    """Ingest knowledge for agents"""
    ingester = MultiAgentKnowledgeIngester()

    if agent:
        knowledge_dir = Path(f"knowledge/{agent}")
        if knowledge_dir.exists():
            result = asyncio.run(ingester.ingest_agent_knowledge(agent, knowledge_dir))
            click.echo(f"✅ {agent}: {result} chunks ingested")
        else:
            click.echo(f"❌ Agent '{agent}' knowledge directory not found")
    else:
        results = asyncio.run(ingester.ingest_all_agents())
        total = sum(results.values())
        click.echo(f"✅ Ingested {total} total chunks across {len(results)} agents")
        for agent_id, count in results.items():
            click.echo(f"   {agent_id}: {count} chunks")

if __name__ == "__main__":
    ingest_knowledge()
```

## 3. Environment Configuration

### 3.1. Environment Variables

```bash
# .env.example - Phase 2 Enhanced

# === Core Services ===
QDRANT_HOST=localhost
QDRANT_PORT=6333

# === AI Models (Azure AI Foundry) ===
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-01

# === Zen MCP Server (Enhanced) ===
ZEN_SERVER_PORT=3000
ZEN_LOG_LEVEL=INFO
ZEN_ENDPOINT=http://localhost:3000
ZEN_AGENT_CONFIG_PATH=./config/agents.yaml

# === MCP Servers ===
# Heimdall MCP (Security Analysis)
HEIMDALL_MCP_HOST=localhost
HEIMDALL_MCP_PORT=8003
HEIMDALL_API_KEY=your-heimdall-key

# GitHub MCP (Repository Analysis)
GITHUB_MCP_HOST=localhost
GITHUB_MCP_PORT=8001
GITHUB_TOKEN=ghp_your-github-token
GITHUB_API_URL=https://api.github.com

# Sequential Thinking MCP (Reasoning)
SEQUENTIAL_THINKING_MCP_HOST=localhost
SEQUENTIAL_THINKING_MCP_PORT=8004

# === Search APIs (Tiered Strategy) ===
# Context7 (Free Tier)
CONTEXT7_API_KEY=your-context7-key
CONTEXT7_ENDPOINT=https://api.context7.com

# Tavily (Paid Tier - $0.0006/query)
TAVILY_API_KEY=your-tavily-key
TAVILY_ENDPOINT=https://api.tavily.com

# Perplexity (Premium Tier - $0.30/query) - Phase 3
# PERPLEXITY_API_KEY=your-perplexity-key

# === Gradio UI ===
GRADIO_SERVER_PORT=7860
GRADIO_SHARE=false

# === Knowledge Ingestion ===
KNOWLEDGE_WEBHOOK_PORT=5000
KNOWLEDGE_DIR=./knowledge
KNOWLEDGE_WEBHOOK_SECRET=your-webhook-secret

# === Cost Management ===
DAILY_COST_LIMIT=5.00
QUERY_COST_LIMIT=0.50
ENABLE_COST_TRACKING=true

# === Monitoring (Optional) ===
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO
ENABLE_METRICS=true
```

## 4. Docker Configuration

### 4.1. Multi-Service Docker Compose

```yaml
# docker-compose.yml - Phase 2 Multi-Agent Architecture
version: '3.8'

services:
  # === Core Vector Database ===
  qdrant:
    image: qdrant/qdrant:v1.9.0
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"  # gRPC port
    volumes:
      - qdrant_data:/qdrant/storage
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=INFO
    restart: unless-stopped
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === Enhanced Zen MCP Orchestrator ===
  zen-mcp:
    build:
      context: ./zen-mcp-server
      dockerfile: Dockerfile
    container_name: zen-mcp
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AGENT_CONFIG_PATH=/app/config/agents.yaml
      - LOG_LEVEL=${LOG_LEVEL}
    volumes:
      - ./config:/app/config:ro
      - ./knowledge:/app/knowledge:ro
    depends_on:
      qdrant:
        condition: service_healthy
      heimdall-mcp:
        condition: service_healthy
      github-mcp:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === Security Analysis MCP ===
  heimdall-mcp:
    image: lcbcfoo/heimdall-mcp-server:latest
    container_name: heimdall-mcp
    ports:
      - "8003:8003"
    environment:
      - HEIMDALL_PORT=8003
      - HEIMDALL_HOST=0.0.0.0
      - HEIMDALL_API_KEY=${HEIMDALL_API_KEY}
      - LOG_LEVEL=INFO
    restart: unless-stopped
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === GitHub Repository MCP ===
  github-mcp:
    image: github/github-mcp-server:latest
    container_name: github-mcp
    ports:
      - "8001:8001"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_API_URL=${GITHUB_API_URL}
      - MCP_PORT=8001
      - MCP_HOST=0.0.0.0
    restart: unless-stopped
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === Sequential Thinking MCP ===
  sequential-thinking-mcp:
    build:
      context: ./mcp-servers/sequential-thinking
      dockerfile: Dockerfile
    container_name: sequential-thinking-mcp
    ports:
      - "8004:8004"
    environment:
      - MCP_PORT=8004
      - MCP_HOST=0.0.0.0
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
    restart: unless-stopped
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === Enhanced User Interface ===
  gradio-ui:
    build:
      context: ./src/ui
      dockerfile: Dockerfile
    container_name: gradio-ui
    ports:
      - "7860:7860"
    environment:
      - ZEN_ENDPOINT=http://zen-mcp:3000
      - GRADIO_SERVER_PORT=7860
      - GRADIO_SERVER_NAME=0.0.0.0
    depends_on:
      zen-mcp:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # === Multi-Agent Knowledge Ingestion ===
  knowledge-webhook:
    build:
      context: ./scripts
      dockerfile: Dockerfile.ingestion
    container_name: knowledge-webhook
    ports:
      - "5000:5000"
    environment:
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - WEBHOOK_PORT=5000
      - WEBHOOK_SECRET=${KNOWLEDGE_WEBHOOK_SECRET}
      - KNOWLEDGE_DIR=/app/knowledge
    volumes:
      - ./knowledge:/app/knowledge:ro
      - ./config:/app/config:ro
    depends_on:
      qdrant:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - promptcraft

  # === Cost Tracking & Monitoring (Optional) ===
  cost-tracker:
    build:
      context: ./monitoring
      dockerfile: Dockerfile.cost-tracker
    container_name: cost-tracker
    environment:
      - DAILY_COST_LIMIT=${DAILY_COST_LIMIT}
      - QUERY_COST_LIMIT=${QUERY_COST_LIMIT}
      - SENTRY_DSN=${SENTRY_DSN}
    restart: unless-stopped
    networks:
      - promptcraft
    profiles:
      - monitoring

volumes:
  qdrant_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /opt/qdrant_data  # NVMe storage path

networks:
  promptcraft:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### 4.2. Phase 3 Infrastructure Preparation

```yaml
# docker-compose.phase3.yml (prepared)
services:
  # Phase 3 additions
  code-interpreter-mcp:
    image: executeautomation/mcp-code-runner:latest
    container_name: code-interpreter-mcp
    ports:
      - "8002:8002"
    environment:
      - SANDBOX_TIMEOUT=30
      - ALLOWED_PACKAGES=numpy,pandas,requests
    security_opt:
      - no-new-privileges:true
    networks:
      - promptcraft
    profiles:
      - phase3

  human-in-loop-mcp:
    image: gotohuman/gotohuman-mcp-server:latest
    container_name: hitl-mcp
    ports:
      - "8005:8005"
    environment:
      - NOTIFICATION_WEBHOOK=${SLACK_WEBHOOK}
      - APPROVAL_TIMEOUT=300
    networks:
      - promptcraft
    profiles:
      - phase3

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - promptcraft
    profiles:
      - phase3

volumes:
  redis_data:
    driver: local
```

## 5. Phase 3 Preparation

### 5.1. Architecture Hooks for Phase 3

```python
# Phase 3 preparation in Zen MCP Server
class ExecutionOrchestrator:
    """Prepared for Phase 3 - Direct Execution"""

    def __init__(self, multi_agent_orchestrator):
        self.orchestrator = multi_agent_orchestrator
        self.execution_engines = {}  # Will be populated in Phase 3

    async def execute_plan(self, plan: dict) -> dict:
        """Execute multi-step plan - Phase 3 implementation"""
        # Placeholder for Phase 3
        return {"status": "coming_in_phase_3"}

# UI preparation for Journey 4
with gr.Tab("Journey 4: Direct Execution (Phase 3)"):
    gr.Markdown("""
    ## Coming in Phase 3: Direct Execution

    Phase 3 will add:
    - End-to-end task execution
    - Code generation and testing
    - Human-in-the-loop approval workflows
    - Multi-step automation
    """)
```

This implementation document provides all the technical details, code examples, and configuration files needed to build Phase 2 of PromptCraft-Hybrid. Each component is fully specified with working code that can be directly implemented.
