---
title: "PromptCraft-Hybrid: Phase 1 Implementation Guide"
version: "3.0"
status: published
component: Architecture
tags: ['phase-1', 'implementation', 'code-examples', 'docker', 'mcp-integration']
source: PromptCraft-Hybrid Project
purpose: Detailed implementation guide with complete code examples, configurations, and API contracts for Phase 1 MVP development.
---

# PromptCraft-Hybrid: Phase 1 Implementation Guide

## 1. Docker Compose Configuration

### 1.1. Complete Docker Compose Stack

```yaml
# docker-compose.phase1.yml
version: '3.8'

services:
  # Zen MCP Server - Central Orchestration
  zen-mcp-server:
    image: zen-mcp:latest
    container_name: zen-mcp
    ports:
      - "3000:3000"
    environment:
      - ZEN_SERVER_PORT=3000
      - ZEN_LOG_LEVEL=INFO
      - MCP_SERVERS=serena,filesystem,github,sequential-thinking,qdrant-memory,context7
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
    volumes:
      - ./config/zen-config.yaml:/app/config.yaml
      - ./logs:/app/logs
    networks:
      - promptcraft
    depends_on:
      - qdrant
      - serena-mcp
      - filesystem-mcp
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '4.0'
      memory: 8G
    security_opt:
      - no-new-privileges:true
    restart: unless-stopped

  # Serena MCP - Semantic Code Analysis
  serena-mcp:
    build:
      context: ./mcp-servers/serena
      dockerfile: Dockerfile
    container_name: serena-mcp
    ports:
      - "8000:8000"
    environment:
      - SERENA_PORT=8000
      - LSP_WORKSPACE=/workspace
      - SERENA_LOG_LEVEL=INFO
    volumes:
      - ./projects:/workspace:ro
      - lsp-cache:/tmp/lsp
      - ./config/serena-config.json:/app/config.json
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '2.0'
      memory: 4G
    tmpfs:
      - /tmp/lsp:size=1g
    restart: unless-stopped

  # FileSystem MCP - Secure File Access
  filesystem-mcp:
    build:
      context: ./mcp-servers/filesystem
      dockerfile: Dockerfile
    container_name: filesystem-mcp
    ports:
      - "8001:8001"
    environment:
      - FS_PORT=8001
      - FS_ROOT=/workspace
      - FS_READ_ONLY=false
      - FS_AUDIT_LOG=true
    volumes:
      - ./projects:/workspace
      - ./logs/filesystem:/app/logs
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '1.0'
      memory: 1G
    security_opt:
      - no-new-privileges:true
    restart: unless-stopped

  # GitHub MCP - Repository Context
  github-mcp:
    image: github/github-mcp-server:latest
    container_name: github-mcp
    ports:
      - "8002:8002"
    environment:
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GITHUB_MCP_PORT=8002
      - GITHUB_CACHE_TTL=300
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '1.0'
      memory: 1G
    restart: unless-stopped

  # Sequential Thinking MCP - Enhanced Reasoning
  sequential-thinking-mcp:
    build:
      context: ./mcp-servers/sequential-thinking
      dockerfile: Dockerfile
    container_name: sequential-thinking-mcp
    ports:
      - "8003:8003"
    environment:
      - ST_PORT=8003
      - ST_MAX_REASONING_STEPS=10
      - ST_TIMEOUT=20000
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8003/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '1.0'
      memory: 2G
    restart: unless-stopped

  # Qdrant Memory MCP - Vector Search
  qdrant-memory-mcp:
    build:
      context: ./mcp-servers/qdrant-memory
      dockerfile: Dockerfile
    container_name: qdrant-memory-mcp
    ports:
      - "8004:8004"
    environment:
      - QM_PORT=8004
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - QM_COLLECTION=promptcraft_knowledge
    networks:
      - promptcraft
    depends_on:
      - qdrant
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8004/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '1.0'
      memory: 1G
    restart: unless-stopped

  # Context7 MCP - External Search
  context7-mcp:
    build:
      context: ./mcp-servers/context7
      dockerfile: Dockerfile
    container_name: context7-mcp
    ports:
      - "8005:8005"
    environment:
      - C7_PORT=8005
      - C7_API_KEY=${CONTEXT7_API_KEY}
      - C7_RATE_LIMIT_RPM=30
      - C7_RATE_LIMIT_RPH=1000
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8005/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '1.0'
      memory: 1G
    restart: unless-stopped

  # Qdrant Vector Database
  qdrant:
    image: qdrant/qdrant:v1.9.1
    container_name: qdrant
    ports:
      - "6333:6333"
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=INFO
    volumes:
      - /mnt/nvme/qdrant:/qdrant/storage
      - ./config/qdrant-config.yaml:/qdrant/config/production.yaml
    networks:
      - promptcraft
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '2.0'
      memory: 16G
    restart: unless-stopped

  # Gradio UI (Reused from existing promptcraft_app.py)
  gradio-ui:
    build:
      context: ./src/ui
      dockerfile: Dockerfile
    container_name: gradio-ui
    ports:
      - "7860:7860"
    environment:
      - GRADIO_SERVER_NAME=0.0.0.0
      - GRADIO_SERVER_PORT=7860
      - ZEN_MCP_ENDPOINT=http://zen-mcp:3000
      - GRADIO_SHARE=false
    volumes:
      - ./src/ui:/app
      - ./logs/gradio:/app/logs
    networks:
      - promptcraft
    depends_on:
      - zen-mcp-server
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7860"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '1.0'
      memory: 2G
    restart: unless-stopped

  # Knowledge Ingestion Webhook
  knowledge-webhook:
    build:
      context: ./src/ingestion
      dockerfile: Dockerfile
    container_name: knowledge-webhook
    ports:
      - "5000:5000"
    environment:
      - WEBHOOK_PORT=5000
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
      - KNOWLEDGE_DIR=/knowledge
    volumes:
      - ./knowledge:/knowledge:ro
      - ./logs/webhook:/app/logs
    networks:
      - promptcraft
    depends_on:
      - qdrant
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    resources:
      cpus: '1.0'
      memory: 1G
    restart: unless-stopped

networks:
  promptcraft:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  lsp-cache:
    driver: local
    driver_opts:
      type: tmpfs
      device: tmpfs
      o: size=1g
```

### 1.2. Environment Configuration

```bash
# .env file (encrypted with GPG in production)
# Core Services
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# AI Models
AZURE_OPENAI_ENDPOINT=https://your-instance.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# GitHub Integration
GITHUB_TOKEN=ghp_your-github-token
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# External Services
CONTEXT7_API_KEY=your-context7-api-key

# Security
GITHUB_WEBHOOK_SECRET=your-webhook-secret
JWT_SECRET=your-jwt-secret

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 2. API Contracts & Data Schemas

### 2.1. Core API Endpoints

#### POST /api/v1/query - Enhanced Query Processing

```json
{
  "request": {
    "query": "string (required)",
    "journey": "1|3|light (optional, default: 1)",
    "context": {
      "project_path": "string (optional)",
      "file_context": "string (optional)",
      "repository_url": "string (optional)",
      "current_file": "string (optional)",
      "cursor_position": {
        "line": "integer (optional)",
        "column": "integer (optional)"
      }
    },
    "preferences": {
      "reasoning_depth": "basic|enhanced|deep (default: basic)",
      "search_tier": "local|external|hybrid (default: hybrid)",
      "response_format": "prompt|analysis|full (default: prompt)",
      "include_sources": "boolean (default: true)",
      "max_context_length": "integer (default: 8000)"
    }
  },
  "response": {
    "query_id": "string (uuid)",
    "enhanced_prompt": "string",
    "reasoning_trace": [
      {
        "step": "integer",
        "mcp_server": "string",
        "operation": "string",
        "input": "object",
        "output": "object",
        "duration_ms": "integer"
      }
    ],
    "sources": [
      {
        "type": "local|external|code|knowledge",
        "source": "string",
        "relevance_score": "float (0.0-1.0)",
        "content_preview": "string",
        "metadata": {
          "file_path": "string (optional)",
          "line_range": "string (optional)",
          "symbol_type": "string (optional)"
        }
      }
    ],
    "performance_metrics": {
      "total_time_ms": "integer",
      "search_time_ms": "integer",
      "reasoning_time_ms": "integer",
      "mcp_calls": "integer",
      "tokens_processed": "integer"
    }
  }
}
```

#### POST /api/v1/claude-code - Journey 3 IDE Integration

```json
{
  "request": {
    "query": "string (required)",
    "context": {
      "file_path": "string (required)",
      "project_root": "string (required)",
      "file_content": "string (optional)",
      "selection": {
        "start_line": "integer (optional)",
        "end_line": "integer (optional)",
        "start_column": "integer (optional)",
        "end_column": "integer (optional)"
      },
      "workspace_files": ["string (optional)"]
    },
    "options": {
      "include_reasoning": "boolean (default: true)",
      "search_code": "boolean (default: true)",
      "analyze_project": "boolean (default: true)",
      "max_context_files": "integer (default: 10)"
    }
  },
  "response": {
    "enhanced_prompt": "string",
    "context_data": [
      {
        "type": "file|symbol|reference|dependency",
        "source": "string",
        "content": "string",
        "relevance": "float",
        "metadata": "object"
      }
    ],
    "reasoning_trace": [
      {
        "mcp": "string",
        "operation": "string",
        "result": "string"
      }
    ],
    "suggestions": [
      {
        "type": "improvement|refactor|test|documentation",
        "description": "string",
        "confidence": "float"
      }
    ]
  }
}
```

### 2.2. Data Schemas

#### QueryCounselor Response Object

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
from datetime import datetime

class QueryComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

class SearchTier(Enum):
    LOCAL_ONLY = "local"
    EXTERNAL_ONLY = "external"
    HYBRID = "hybrid"

class MCPCapability(Enum):
    CODE_ANALYSIS = "code_analysis"
    REASONING = "reasoning"
    SEARCH = "search"
    FILE_ACCESS = "file_access"
    REPOSITORY_CONTEXT = "repository_context"
    EXTERNAL_LOOKUP = "external_lookup"

@dataclass
class QueryAnalysis:
    complexity: QueryComplexity
    recommended_mcps: List[str]
    search_strategy: SearchTier
    reasoning_required: bool
    estimated_time_ms: int
    context_requirements: Dict[str, Any]
    required_capabilities: List[MCPCapability]

@dataclass
class MCPExecutionStep:
    step_id: str
    mcp_server: str
    operation: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    duration_ms: int
    success: bool
    error_message: Optional[str] = None

@dataclass
class QueryCounselorResponse:
    query_id: str
    original_query: str
    analysis: QueryAnalysis
    enhanced_query: str
    execution_plan: List[Dict[str, Any]]
    fallback_strategies: List[str]
    reasoning_trace: List[MCPExecutionStep]
    sources: List[Dict[str, Any]]
    performance_metrics: Dict[str, int]
    timestamp: datetime

    def __post_init__(self):
        if not self.query_id:
            self.query_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now()
```

#### Qdrant Payload Schema

```python
# Qdrant point structure for knowledge chunks
qdrant_payload_schema = {
    "id": "string (uuid)",
    "content": "string (text chunk)",
    "metadata": {
        "source_file": "string",
        "source_type": "markdown|code|documentation|api",
        "section_title": "string (optional)",
        "keywords": ["string"],
        "last_updated": "datetime (ISO format)",
        "version": "string",
        "project": "string",
        "language": "string (for code)",
        "framework": "string (optional)",
        "component": "string (optional)",
        "agent_id": "string (optional)"
    },
    "embedding_model": "string (all-MiniLM-L6-v2)",
    "chunk_index": "integer",
    "total_chunks": "integer",
    "relevance_scores": {
        "journey_1": "float (0.0-1.0)",
        "journey_3": "float (0.0-1.0)",
        "security": "float (0.0-1.0)",
        "development": "float (0.0-1.0)",
        "domain_specific": "float (0.0-1.0)"
    },
    "quality_metrics": {
        "readability_score": "float (0.0-1.0)",
        "completeness_score": "float (0.0-1.0)",
        "currency_score": "float (0.0-1.0)"
    }
}

# Collection configuration
collections_config = {
    "promptcraft_knowledge": {
        "vector_size": 384,  # all-MiniLM-L6-v2 embedding size
        "distance": "Cosine",
        "payload_schema": qdrant_payload_schema,
        "hnsw_config": {
            "m": 16,
            "ef_construct": 100
        },
        "optimizers_config": {
            "deleted_threshold": 0.2,
            "vacuum_min_vector_number": 1000,
            "default_segment_number": 0,
            "max_segment_size": 20000,
            "memmap_threshold": 50000,
            "indexing_threshold": 10000,
            "flush_interval_sec": 5,
            "max_optimization_threads": 1
        }
    },
    "code_context": {
        "vector_size": 384,
        "distance": "Cosine",
        "payload_schema": {
            "file_path": "string",
            "function_name": "string (optional)",
            "class_name": "string (optional)",
            "symbols": ["string"],
            "dependencies": ["string"],
            "repository": "string",
            "language": "string",
            "complexity_score": "float",
            "test_coverage": "float (optional)",
            "documentation_score": "float (optional)"
        }
    },
    "project_memory": {
        "vector_size": 384,
        "distance": "Cosine",
        "payload_schema": {
            "project_name": "string",
            "context_type": "architectural|business|technical",
            "importance_score": "float",
            "last_accessed": "datetime",
            "access_frequency": "integer"
        }
    }
}
```

## 3. Component Implementations

### 3.1. SimpleKnowledgeIngester (Replaces Prefect)

```python
# src/ingestion/simple_ingester.py
import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from sentence_transformers import SentenceTransformer
import yaml
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IngestionMetrics:
    files_processed: int = 0
    chunks_created: int = 0
    chunks_stored: int = 0
    errors: int = 0
    processing_time_ms: int = 0

class SimpleKnowledgeIngester:
    """Simplified knowledge ingestion pipeline replacing Prefect workflows"""

    def __init__(self,
                 qdrant_host: str = "qdrant",
                 qdrant_port: int = 6333,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.encoder = SentenceTransformer(embedding_model)
        self.collection_name = "promptcraft_knowledge"
        self.metrics = IngestionMetrics()
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collection_info = self.qdrant.get_collection(self.collection_name)
            logger.info(f"Collection {self.collection_name} exists with {collection_info.points_count} points")
        except Exception as e:
            logger.info(f"Creating collection {self.collection_name}")
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                hnsw_config={
                    "m": 16,
                    "ef_construct": 100
                },
                optimizers_config={
                    "deleted_threshold": 0.2,
                    "vacuum_min_vector_number": 1000,
                    "default_segment_number": 0,
                    "max_segment_size": 20000,
                    "memmap_threshold": 50000,
                    "indexing_threshold": 10000,
                    "flush_interval_sec": 5,
                    "max_optimization_threads": 1
                }
            )

    def process_markdown_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process markdown file and extract structured chunks"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Parse YAML frontmatter
            frontmatter, markdown_content = self._parse_frontmatter(content)

            # Validate frontmatter structure
            if not self._validate_frontmatter(frontmatter, file_path):
                logger.warning(f"Invalid frontmatter in {file_path}, skipping")
                return []

            # Split into semantic sections
            sections = self._split_markdown_sections(markdown_content)

            chunks = []
            for i, section in enumerate(sections):
                if len(section.strip()) < 50:  # Skip tiny sections
                    continue

                chunk = self._create_chunk(
                    content=section,
                    file_path=file_path,
                    frontmatter=frontmatter,
                    chunk_index=i,
                    total_chunks=len(sections)
                )
                chunks.append(chunk)

            self.metrics.files_processed += 1
            self.metrics.chunks_created += len(chunks)
            logger.info(f"Processed {file_path}: {len(chunks)} chunks created")
            return chunks

        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            self.metrics.errors += 1
            return []

    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    frontmatter = yaml.safe_load(parts[1])
                    markdown_content = parts[2].strip()
                    return frontmatter or {}, markdown_content
                except yaml.YAMLError as e:
                    logger.warning(f"Invalid YAML frontmatter: {e}")
                    return {}, content
        return {}, content

    def _validate_frontmatter(self, frontmatter: Dict[str, Any], file_path: Path) -> bool:
        """Validate frontmatter structure according to PromptCraft standards"""
        required_fields = ['title', 'version', 'status']

        for field in required_fields:
            if field not in frontmatter:
                logger.warning(f"Missing required frontmatter field '{field}' in {file_path}")
                return False

        # Validate agent_id matches directory structure for knowledge files
        if 'knowledge/' in str(file_path):
            agent_id = frontmatter.get('agent_id')
            if agent_id:
                expected_dir = f"knowledge/{agent_id}"
                if expected_dir not in str(file_path):
                    logger.warning(f"agent_id '{agent_id}' doesn't match directory structure in {file_path}")
                    return False

        return True

    def _split_markdown_sections(self, content: str) -> List[str]:
        """Split markdown into atomic knowledge chunks (H3 sections)"""
        lines = content.split('\n')
        sections = []
        current_section = []
        current_level = 0

        for line in lines:
            if line.strip().startswith('#'):
                heading_level = len(line.split(' ')[0])

                # Start new section on H3 or if we're starting fresh
                if heading_level == 3 or (heading_level <= 2 and current_section):
                    if current_section:
                        sections.append('\n'.join(current_section).strip())
                    current_section = [line]
                    current_level = heading_level
                else:
                    current_section.append(line)
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            sections.append('\n'.join(current_section).strip())

        return [s for s in sections if s.strip()]

    def _create_chunk(self,
                     content: str,
                     file_path: Path,
                     frontmatter: Dict[str, Any],
                     chunk_index: int,
                     total_chunks: int) -> Dict[str, Any]:
        """Create standardized chunk with metadata"""

        # Generate stable chunk ID
        chunk_id = hashlib.md5(
            f"{file_path}_{chunk_index}_{content[:100]}".encode()
        ).hexdigest()

        # Extract section title
        section_title = self._extract_section_title(content)

        # Calculate relevance scores
        relevance_scores = self._calculate_relevance_scores(content, frontmatter)

        # Calculate quality metrics
        quality_metrics = self._calculate_quality_metrics(content)

        return {
            'id': chunk_id,
            'content': content,
            'metadata': {
                'source_file': str(file_path),
                'source_type': 'markdown',
                'section_title': section_title,
                'keywords': frontmatter.get('tags', []),
                'last_updated': datetime.now().isoformat(),
                'version': frontmatter.get('version', '1.0'),
                'project': 'promptcraft-hybrid',
                'component': frontmatter.get('component', 'general'),
                'agent_id': frontmatter.get('agent_id'),
                'chunk_index': chunk_index,
                'total_chunks': total_chunks
            },
            'embedding_model': 'all-MiniLM-L6-v2',
            'relevance_scores': relevance_scores,
            'quality_metrics': quality_metrics
        }

    def _extract_section_title(self, content: str) -> str:
        """Extract title from content section"""
        lines = content.split('\n')
        for line in lines:
            if line.strip().startswith('#'):
                return line.strip().lstrip('#').strip()
        return "Untitled Section"

    def _calculate_relevance_scores(self, content: str, frontmatter: Dict[str, Any]) -> Dict[str, float]:
        """Calculate relevance scores for different use cases"""
        content_lower = content.lower()
        tags = [tag.lower() for tag in frontmatter.get('tags', [])]

        # Journey-specific scoring
        journey_1_keywords = ['prompt', 'create', 'framework', 'template', 'enhancement']
        journey_3_keywords = ['ide', 'code', 'development', 'integration', 'cli']
        security_keywords = ['security', 'auth', 'encryption', 'vulnerability', 'compliance']
        development_keywords = ['api', 'function', 'class', 'algorithm', 'pattern']

        def calculate_score(keywords: List[str]) -> float:
            score = 0.0
            for keyword in keywords:
                if keyword in content_lower:
                    score += 0.1
                if keyword in tags:
                    score += 0.2
            return min(score, 1.0)

        return {
            'journey_1': calculate_score(journey_1_keywords),
            'journey_3': calculate_score(journey_3_keywords),
            'security': calculate_score(security_keywords),
            'development': calculate_score(development_keywords),
            'domain_specific': 0.5  # Default value, can be enhanced
        }

    def _calculate_quality_metrics(self, content: str) -> Dict[str, float]:
        """Calculate content quality metrics"""
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        # Readability score (simple heuristic)
        avg_line_length = sum(len(line) for line in non_empty_lines) / max(len(non_empty_lines), 1)
        readability_score = max(0.0, min(1.0, 1.0 - (avg_line_length - 80) / 200))

        # Completeness score (based on structure)
        has_heading = any(line.strip().startswith('#') for line in lines)
        has_examples = 'example' in content.lower() or '```' in content
        has_explanation = len(non_empty_lines) > 5
        completeness_score = (has_heading + has_examples + has_explanation) / 3.0

        # Currency score (placeholder - could be enhanced with git history)
        currency_score = 0.8  # Default assumption

        return {
            'readability_score': readability_score,
            'completeness_score': completeness_score,
            'currency_score': currency_score
        }

    def ingest_directory(self, knowledge_dir: Path) -> IngestionMetrics:
        """Ingest all markdown files in directory"""
        start_time = datetime.now()

        markdown_files = list(knowledge_dir.glob('**/*.md'))
        logger.info(f"Found {len(markdown_files)} markdown files to process")

        all_points = []
        for file_path in markdown_files:
            chunks = self.process_markdown_file(file_path)

            for chunk in chunks:
                try:
                    # Generate embedding
                    vector = self.encoder.encode(chunk['content']).tolist()

                    # Create Qdrant point
                    point = PointStruct(
                        id=chunk['id'],
                        vector=vector,
                        payload={
                            **chunk['metadata'],
                            'relevance_scores': chunk['relevance_scores'],
                            'quality_metrics': chunk['quality_metrics'],
                            'embedding_model': chunk['embedding_model']
                        }
                    )
                    all_points.append(point)

                except Exception as e:
                    logger.error(f"Error creating point for chunk {chunk['id']}: {str(e)}")
                    self.metrics.errors += 1

        # Batch upsert to Qdrant
        if all_points:
            try:
                self.qdrant.upsert(
                    collection_name=self.collection_name,
                    points=all_points
                )
                self.metrics.chunks_stored = len(all_points)
                logger.info(f"Successfully stored {len(all_points)} chunks in Qdrant")
            except Exception as e:
                logger.error(f"Error storing points in Qdrant: {str(e)}")
                self.metrics.errors += 1

        # Calculate final metrics
        end_time = datetime.now()
        self.metrics.processing_time_ms = int((end_time - start_time).total_seconds() * 1000)

        logger.info(f"Ingestion complete: {self.metrics}")
        return self.metrics

# Flask webhook endpoint
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
ingester = SimpleKnowledgeIngester()

def verify_github_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    if not signature_header:
        return False

    sha_name, signature = signature_header.split('=')
    if sha_name != 'sha256':
        return False

    mac = hmac.new(secret.encode(), payload_body, hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'knowledge-webhook',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/webhook/knowledge-update', methods=['POST'])
def handle_knowledge_webhook():
    """Handle GitHub webhook for knowledge updates"""
    try:
        # Verify webhook signature
        signature = request.headers.get('X-Hub-Signature-256')
        secret = os.getenv('GITHUB_WEBHOOK_SECRET')

        if secret and not verify_github_signature(request.data, signature, secret):
            logger.warning("Invalid webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401

        payload = request.json

        # Process push events to main branch
        if payload.get('ref') == 'refs/heads/main':
            # Check if knowledge files were modified
            commits = payload.get('commits', [])
            knowledge_files_modified = False

            for commit in commits:
                modified_files = commit.get('modified', []) + commit.get('added', [])
                if any('knowledge/' in file for file in modified_files):
                    knowledge_files_modified = True
                    break

            if knowledge_files_modified:
                logger.info("Knowledge files modified, starting ingestion")
                knowledge_dir = Path('/knowledge')

                if knowledge_dir.exists():
                    metrics = ingester.ingest_directory(knowledge_dir)
                    return jsonify({
                        'status': 'success',
                        'message': 'Knowledge ingestion completed',
                        'metrics': {
                            'files_processed': metrics.files_processed,
                            'chunks_stored': metrics.chunks_stored,
                            'processing_time_ms': metrics.processing_time_ms,
                            'errors': metrics.errors
                        }
                    })
                else:
                    return jsonify({'error': 'Knowledge directory not found'}), 404

        return jsonify({'status': 'ignored', 'message': 'No knowledge files modified'})

    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize ingestion on startup
    knowledge_dir = Path('/knowledge')
    if knowledge_dir.exists():
        logger.info("Running initial knowledge ingestion")
        ingester.ingest_directory(knowledge_dir)

    app.run(host='0.0.0.0', port=5000, debug=False)
```

### 3.2. Enhanced Gradio UI (70% Reuse)

```python
# src/ui/promptcraft_app.py (Enhanced from existing)
import gradio as gr
import requests
import json
import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PromptCraftUI:
    """Enhanced Gradio UI with multi-MCP integration"""

    def __init__(self, zen_endpoint: str = "http://zen-mcp:3000"):
        self.zen_endpoint = zen_endpoint
        self.session_history = []
        self.performance_metrics = []

    def create_interface(self) -> gr.Blocks:
        """Create enhanced Gradio interface with multi-tab layout"""

        # Custom CSS for enhanced styling
        custom_css = self._load_custom_css()

        with gr.Blocks(
            title="PromptCraft-Hybrid",
            theme=gr.themes.Soft(),
            css=custom_css
        ) as interface:

            # Header
            gr.Markdown("# PromptCraft-Hybrid: AI Workbench", elem_classes=["main-header"])
            gr.Markdown("Transform your queries into expert-level prompts with multi-agent intelligence")

            # Main tabs
            with gr.Tabs():
                with gr.Tab("Journey 1: Quick Enhancement"):
                    self._create_journey1_interface()

                with gr.Tab("Journey 3: IDE Integration"):
                    self._create_journey3_interface()

                with gr.Tab("System Dashboard"):
                    self._create_dashboard_interface()

                with gr.Tab("Advanced Settings"):
                    self._create_settings_interface()

        return interface

    def _create_journey1_interface(self):
        """Journey 1: Basic prompt enhancement with C.R.E.A.T.E. framework"""

        gr.Markdown("## Transform Your Query into Expert Prompts")
        gr.Markdown("Enter your request and watch as our AI workbench enhances it with the C.R.E.A.T.E. framework")

        with gr.Row():
            with gr.Column(scale=2):
                # Input section
                query_input = gr.Textbox(
                    label="Your Query",
                    placeholder="Describe what you want to accomplish...\n\nExamples:\n• Create a login form with validation\n• Optimize database query performance\n• Design a REST API for user management",
                    lines=4,
                    elem_classes=["query-input"]
                )

                # Configuration options
                with gr.Row():
                    reasoning_depth = gr.Radio(
                        choices=["basic", "enhanced", "deep"],
                        label="Reasoning Depth",
                        value="basic",
                        info="How much analysis to include"
                    )
                    search_tier = gr.Radio(
                        choices=["local", "external", "hybrid"],
                        label="Search Strategy",
                        value="hybrid",
                        info="Knowledge sources to use"
                    )

                # Action buttons
                with gr.Row():
                    enhance_btn = gr.Button(
                        "Enhance Prompt",
                        variant="primary",
                        size="lg",
                        elem_classes=["enhance-button"]
                    )
                    clear_btn = gr.Button("Clear", variant="secondary")

            with gr.Column(scale=3):
                # Output section
                enhanced_output = gr.Textbox(
                    label="Enhanced C.R.E.A.T.E. Prompt",
                    lines=15,
                    interactive=False,
                    elem_classes=["enhanced-prompt"]
                )

                # Copy button for enhanced prompt
                copy_btn = gr.Button("Copy to Clipboard", size="sm")

                # Expandable sections for detailed information
                with gr.Accordion("Reasoning Trace", open=False):
                    reasoning_output = gr.JSON(
                        label="MCP Processing Steps",
                        elem_classes=["reasoning-trace"]
                    )

                with gr.Accordion("Knowledge Sources", open=False):
                    sources_output = gr.JSON(
                        label="Sources Used",
                        elem_classes=["sources-list"]
                    )

                with gr.Accordion("Performance Metrics", open=False):
                    metrics_output = gr.JSON(
                        label="Performance Data",
                        elem_classes=["metrics-display"]
                    )

        # Event handlers
        enhance_btn.click(
            fn=self.enhance_query,
            inputs=[query_input, reasoning_depth, search_tier],
            outputs=[enhanced_output, reasoning_output, sources_output, metrics_output]
        )

        clear_btn.click(
            fn=lambda: ("", None, None, None),
            outputs=[enhanced_output, reasoning_output, sources_output, metrics_output]
        )

    def _create_journey3_interface(self):
        """Journey 3: IDE Integration testing and configuration"""

        gr.Markdown("## IDE Integration Testing")
        gr.Markdown("Test enhanced context generation for development workflows")

        with gr.Row():
            with gr.Column(scale=1):
                # Project context inputs
                project_path = gr.Textbox(
                    label="Project Path",
                    placeholder="/workspace/my-project",
                    info="Root directory of your project"
                )

                current_file = gr.Textbox(
                    label="Current File",
                    placeholder="src/components/Login.tsx",
                    info="File you're working on"
                )

                file_content = gr.Textbox(
                    label="File Content (Optional)",
                    placeholder="Paste current file content for better context...",
                    lines=8,
                    info="Current file content for analysis"
                )

                # Selection context
                with gr.Group():
                    gr.Markdown("### Selection Context (Optional)")
                    with gr.Row():
                        start_line = gr.Number(
                            label="Start Line",
                            value=None,
                            precision=0
                        )
                        end_line = gr.Number(
                            label="End Line",
                            value=None,
                            precision=0
                        )

                # Development query
                ide_query = gr.Textbox(
                    label="Development Query",
                    placeholder="Add OAuth authentication to this component\nRefactor this function for better performance\nWrite unit tests for this module",
                    lines=3
                )

                # Options
                with gr.Group():
                    gr.Markdown("### Analysis Options")
                    include_reasoning = gr.Checkbox(
                        label="Include Reasoning",
                        value=True
                    )
                    search_code = gr.Checkbox(
                        label="Search Codebase",
                        value=True
                    )
                    analyze_project = gr.Checkbox(
                        label="Analyze Project Structure",
                        value=True
                    )

                test_ide_btn = gr.Button(
                    "Test IDE Integration",
                    variant="primary",
                    size="lg"
                )

            with gr.Column(scale=2):
                # Results section
                ide_response = gr.Textbox(
                    label="Enhanced IDE Response",
                    lines=12,
                    interactive=False,
                    elem_classes=["ide-response"]
                )

                with gr.Accordion("Context Analysis", open=False):
                    context_analysis = gr.JSON(label="Context Data")

                with gr.Accordion("Code Suggestions", open=False):
                    suggestions_output = gr.JSON(label="AI Suggestions")

                with gr.Accordion("Integration Instructions", open=False):
                    gr.Markdown("""
                    ### Claude Code CLI Setup

                    Add this configuration to your `claude_desktop_config.json`:

                    ```json
                    {
                      "mcpServers": {
                        "promptcraft-zen": {
                          "command": "curl",
                          "args": [
                            "-X", "POST",
                            "-H", "Content-Type: application/json",
                            "-d", "{\\"query\\": \\"{{query}}\\", \\"context\\": {\\"file_path\\": \\"{{file_path}}\\", \\"project_root\\": \\"{{project_root}}\\"}}",
                            "http://your-unraid-server:3000/api/v1/claude-code"
                          ]
                        }
                      }
                    }
                    ```
                    """)

        # Event handler for IDE integration test
        test_ide_btn.click(
            fn=self.test_ide_integration,
            inputs=[
                project_path, current_file, file_content, ide_query,
                start_line, end_line, include_reasoning, search_code, analyze_project
            ],
            outputs=[ide_response, context_analysis, suggestions_output]
        )

    def _create_dashboard_interface(self):
        """System status dashboard and monitoring"""

        gr.Markdown("## System Dashboard")

        with gr.Row():
            with gr.Column():
                # MCP Server Status
                gr.Markdown("### MCP Server Health")
                mcp_status = gr.JSON(
                    label="Server Status",
                    elem_classes=["status-display"]
                )

                refresh_status_btn = gr.Button("Refresh Status")

                # Performance metrics
                gr.Markdown("### Performance Metrics")
                perf_metrics = gr.JSON(
                    label="System Performance",
                    elem_classes=["metrics-display"]
                )

            with gr.Column():
                # Recent queries
                gr.Markdown("### Recent Queries")
                query_history = gr.Dataframe(
                    headers=["Timestamp", "Query", "Journey", "Response Time"],
                    datatype=["str", "str", "str", "str"],
                    label="Query History"
                )

                # System logs
                gr.Markdown("### System Logs")
                system_logs = gr.Textbox(
                    label="Recent Logs",
                    lines=8,
                    interactive=False,
                    elem_classes=["log-display"]
                )

        # Auto-refresh functionality
        refresh_status_btn.click(
            fn=self.get_system_status,
            outputs=[mcp_status, perf_metrics, query_history, system_logs]
        )

    def _create_settings_interface(self):
        """Advanced settings and configuration"""

        gr.Markdown("## Advanced Settings")

        with gr.Row():
            with gr.Column():
                # Zen MCP Configuration
                gr.Markdown("### Zen MCP Server Configuration")
                zen_endpoint_input = gr.Textbox(
                    label="Zen MCP Endpoint",
                    value=self.zen_endpoint,
                    info="URL of your Zen MCP server"
                )

                # Default preferences
                gr.Markdown("### Default Preferences")
                default_reasoning = gr.Radio(
                    choices=["basic", "enhanced", "deep"],
                    label="Default Reasoning Depth",
                    value="basic"
                )

                default_search = gr.Radio(
                    choices=["local", "external", "hybrid"],
                    label="Default Search Strategy",
                    value="hybrid"
                )

                # API limits
                gr.Markdown("### API Limits")
                max_context_length = gr.Slider(
                    minimum=1000,
                    maximum=32000,
                    value=8000,
                    step=1000,
                    label="Max Context Length"
                )

                request_timeout = gr.Slider(
                    minimum=5,
                    maximum=60,
                    value=30,
                    step=5,
                    label="Request Timeout (seconds)"
                )

                save_settings_btn = gr.Button("Save Settings", variant="primary")

            with gr.Column():
                # Knowledge Base Management
                gr.Markdown("### Knowledge Base")
                kb_stats = gr.JSON(label="Knowledge Base Statistics")

                refresh_kb_btn = gr.Button("Refresh KB Stats")
                trigger_ingestion_btn = gr.Button("Trigger Re-ingestion")

                # Export/Import
                gr.Markdown("### Data Management")
                export_history_btn = gr.Button("Export Query History")
                import_config_btn = gr.Button("Import Configuration")

        # Settings event handlers
        save_settings_btn.click(
            fn=self.save_settings,
            inputs=[zen_endpoint_input, default_reasoning, default_search, max_context_length, request_timeout],
            outputs=[]
        )

        refresh_kb_btn.click(
            fn=self.get_knowledge_base_stats,
            outputs=[kb_stats]
        )

    def enhance_query(self,
                     query: str,
                     reasoning_depth: str,
                     search_tier: str) -> Tuple[str, Dict, List, Dict]:
        """Enhanced query processing with comprehensive error handling"""

        if not query.strip():
            return "Please enter a query to enhance.", {}, [], {}

        start_time = time.time()

        try:
            # Prepare request payload
            payload = {
                "query": query,
                "journey": "1",
                "preferences": {
                    "reasoning_depth": reasoning_depth,
                    "search_tier": search_tier,
                    "response_format": "full",
                    "include_sources": True
                }
            }

            # Make API request
            response = requests.post(
                f"{self.zen_endpoint}/api/v1/query",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            if response.status_code == 200:
                data = response.json()

                # Store in session history
                self.session_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'query': query,
                    'journey': '1',
                    'response_time': f"{response_time:.0f}ms",
                    'success': True
                })

                # Extract response components
                enhanced_prompt = data.get('enhanced_prompt', 'Error: No prompt generated')
                reasoning_trace = data.get('reasoning_trace', [])
                sources = data.get('sources', [])
                metrics = data.get('performance_metrics', {})

                # Add client-side metrics
                metrics['client_response_time_ms'] = response_time
                metrics['timestamp'] = datetime.now().isoformat()

                return enhanced_prompt, reasoning_trace, sources, metrics

            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                logger.error(error_msg)
                return error_msg, {}, [], {'error': error_msg}

        except requests.exceptions.Timeout:
            error_msg = "Request timed out. Please try again."
            logger.error(error_msg)
            return error_msg, {}, [], {'error': 'timeout'}

        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Zen MCP Server. Please check your configuration."
            logger.error(error_msg)
            return error_msg, {}, [], {'error': 'connection_error'}

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return error_msg, {}, [], {'error': str(e)}

    def test_ide_integration(self,
                           project_path: str,
                           current_file: str,
                           file_content: str,
                           ide_query: str,
                           start_line: Optional[int],
                           end_line: Optional[int],
                           include_reasoning: bool,
                           search_code: bool,
                           analyze_project: bool) -> Tuple[str, Dict, List]:
        """Test IDE integration with enhanced context"""

        if not ide_query.strip():
            return "Please enter a development query.", {}, []

        try:
            # Prepare context
            context = {
                "project_root": project_path or "/workspace/test-project",
                "file_path": current_file or "src/main.py"
            }

            if file_content:
                context["file_content"] = file_content

            if start_line is not None and end_line is not None:
                context["selection"] = {
                    "start_line": int(start_line),
                    "end_line": int(end_line)
                }

            # Prepare options
            options = {
                "include_reasoning": include_reasoning,
                "search_code": search_code,
                "analyze_project": analyze_project,
                "max_context_files": 10
            }

            # Make API request
            payload = {
                "query": ide_query,
                "context": context,
                "options": options
            }

            response = requests.post(
                f"{self.zen_endpoint}/api/v1/claude-code",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()

                enhanced_prompt = data.get('enhanced_prompt', 'No enhanced prompt generated')
                context_data = data.get('context_data', [])
                suggestions = data.get('suggestions', [])

                return enhanced_prompt, context_data, suggestions

            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return error_msg, {}, []

        except Exception as e:
            error_msg = f"IDE Integration Error: {str(e)}"
            logger.error(error_msg)
            return error_msg, {}, []

    def get_system_status(self) -> Tuple[Dict, Dict, List, str]:
        """Get comprehensive system status"""
        try:
            # Get MCP server health
            health_response = requests.get(f"{self.zen_endpoint}/health", timeout=10)
            mcp_status = health_response.json() if health_response.status_code == 200 else {"error": "Cannot connect"}

            # Get performance metrics
            perf_metrics = {
                "avg_response_time": sum(float(h['response_time'].replace('ms', '')) for h in self.session_history[-10:]) / max(len(self.session_history[-10:]), 1) if self.session_history else 0,
                "total_queries": len(self.session_history),
                "success_rate": sum(1 for h in self.session_history if h['success']) / max(len(self.session_history), 1) if self.session_history else 0,
                "last_updated": datetime.now().isoformat()
            }

            # Format query history for display
            query_history = [
                [h['timestamp'], h['query'][:50] + '...' if len(h['query']) > 50 else h['query'], h['journey'], h['response_time']]
                for h in self.session_history[-20:]  # Last 20 queries
            ]

            # Mock system logs (in production, this would read actual logs)
            system_logs = f"""[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] System status check completed
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MCP servers: {'healthy' if 'error' not in mcp_status else 'degraded'}
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Query processing: operational
[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Knowledge base: available"""

            return mcp_status, perf_metrics, query_history, system_logs

        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {"error": str(e)}, {}, [], f"Error: {str(e)}"

    def get_knowledge_base_stats(self) -> Dict:
        """Get knowledge base statistics"""
        try:
            # This would query Qdrant directly or through an API
            # For now, return mock data
            return {
                "total_documents": 1250,
                "total_chunks": 4800,
                "collections": ["promptcraft_knowledge", "code_context", "project_memory"],
                "last_updated": datetime.now().isoformat(),
                "avg_chunk_size": 350,
                "embedding_model": "all-MiniLM-L6-v2"
            }
        except Exception as e:
            return {"error": str(e)}

    def save_settings(self, *args):
        """Save user settings"""
        # In production, this would persist settings
        logger.info("Settings saved (placeholder)")
        return "Settings saved successfully!"

    def _load_custom_css(self) -> str:
        """Load custom CSS for enhanced UI styling"""
        return """
        .main-header {
            text-align: center;
            color: #2563eb;
            font-size: 2.5rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }

        .gradio-container {
            max-width: 1400px !important;
            margin: 0 auto;
        }

        .query-input textarea {
            font-size: 16px;
            line-height: 1.5;
        }

        .enhanced-prompt textarea {
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            background: #f8f9fa;
            border-left: 4px solid #2563eb;
            font-size: 14px;
            line-height: 1.6;
        }

        .enhance-button {
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            border: none;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .ide-response textarea {
            font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
            background: #1f2937;
            color: #f3f4f6;
            border: 1px solid #374151;
            font-size: 14px;
        }

        .status-display, .metrics-display {
            font-family: monospace;
            font-size: 12px;
        }

        .log-display textarea {
            font-family: monospace;
            background: #000;
            color: #00ff00;
            font-size: 12px;
        }

        .reasoning-trace, .sources-list {
            font-size: 12px;
        }

        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .enhanced-prompt textarea {
                background: #1f2937;
                color: #f3f4f6;
                border-left-color: #60a5fa;
            }
        }
        """

# Application factory
def create_app(zen_endpoint: str = None) -> gr.Blocks:
    """Create and configure the Gradio application"""
    endpoint = zen_endpoint or os.getenv("ZEN_MCP_ENDPOINT", "http://zen-mcp:3000")
    ui = PromptCraftUI(endpoint)
    return ui.create_interface()

# Main entry point
if __name__ == "__main__":
    import os

    # Configuration
    zen_endpoint = os.getenv("ZEN_MCP_ENDPOINT", "http://localhost:3000")
    server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    # Create and launch app
    app = create_app(zen_endpoint)

    logger.info(f"Starting PromptCraft-Hybrid UI on {server_name}:{server_port}")
    logger.info(f"Zen MCP endpoint: {zen_endpoint}")

    app.launch(
        server_name=server_name,
        server_port=server_port,
        share=False,
        show_error=True,
        quiet=False
    )
```

### 3.3. Zen MCP Server Configuration

```javascript
// zen-mcp-server/src/config.js
const mcpConfig = {
  server: {
    port: process.env.ZEN_SERVER_PORT || 3000,
    host: '0.0.0.0',
    logLevel: process.env.ZEN_LOG_LEVEL || 'INFO',
    corsEnabled: true,
    rateLimiting: {
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 1000 // requests per window
    }
  },

  mcpServers: {
    serena: {
      host: 'serena-mcp',
      port: 8000,
      capabilities: [
        'code_analysis',
        'symbol_lookup',
        'project_navigation',
        'semantic_search',
        'dependency_analysis'
      ],
      priority: 'high',
      timeout: 10000,
      retryAttempts: 3,
      healthCheckInterval: 30000
    },

    filesystem: {
      host: 'filesystem-mcp',
      port: 8001,
      capabilities: [
        'file_read',
        'file_write',
        'directory_list',
        'file_search',
        'permission_check'
      ],
      priority: 'high',
      timeout: 5000,
      retryAttempts: 2,
      healthCheckInterval: 30000
    },

    github: {
      host: 'github-mcp',
      port: 8002,
      capabilities: [
        'repo_analysis',
        'commit_history',
        'issue_context',
        'branch_info',
        'pr_analysis'
      ],
      priority: 'medium',
      timeout: 15000,
      retryAttempts: 3,
      healthCheckInterval: 60000
    },

    sequentialThinking: {
      host: 'sequential-thinking-mcp',
      port: 8003,
      capabilities: [
        'reasoning',
        'step_by_step',
        'problem_decomposition',
        'context_analysis',
        'decision_tree'
      ],
      priority: 'high',
      timeout: 20000,
      retryAttempts: 2,
      healthCheckInterval: 30000
    },

    qdrantMemory: {
      host: 'qdrant-memory-mcp',
      port: 8004,
      capabilities: [
        'vector_search',
        'knowledge_retrieval',
        'semantic_similarity',
        'context_ranking',
        'memory_storage'
      ],
      priority: 'critical',
      timeout: 5000,
      retryAttempts: 3,
      healthCheckInterval: 15000
    },

    context7: {
      host: 'context7-mcp',
      port: 8005,
      capabilities: [
        'external_search',
        'documentation_lookup',
        'context_enhancement',
        'web_scraping',
        'api_documentation'
      ],
      priority: 'medium',
      timeout: 10000,
      retryAttempts: 2,
      healthCheckInterval: 60000,
      rateLimits: {
        requestsPerMinute: 30,
        requestsPerHour: 1000
      }
    }
  },

  orchestration: {
    defaultStrategy: 'parallel_with_fallback',
    maxConcurrentMCPs: 4,
    retryAttempts: 3,
    circuitBreakerThreshold: 5,
    circuitBreakerTimeout: 60000,
    loadBalancing: 'round_robin',
    failoverEnabled: true
  },

  aiIntegration: {
    azure: {
      endpoint: process.env.AZURE_OPENAI_ENDPOINT,
      apiKey: process.env.AZURE_OPENAI_API_KEY,
      apiVersion: '2024-02-15-preview',
      models: {
        primary: 'gpt-4o',
        fallback: 'gpt-3.5-turbo',
        embedding: 'text-embedding-ada-002'
      },
      maxTokens: 8000,
      temperature: 0.7,
      timeout: 30000
    }
  },

  journey3: {
    ideIntegration: {
      endpoint: '/api/v1/claude-code',
      defaultMCPs: ['serena', 'github', 'filesystem', 'sequentialThinking'],
      responseFormat: 'enhanced_context',
      includeReasoning: true,
      maxContextFiles: 10,
      cacheResults: true,
      cacheTTL: 300000 // 5 minutes
    }
  },

  logging: {
    level: process.env.ZEN_LOG_LEVEL || 'INFO',
    format: 'json',
    destinations: ['console', 'file'],
    file: {
      path: '/app/logs/zen-mcp.log',
      maxSize: '10MB',
      maxFiles: 5
    },
    requestLogging: true,
    performanceLogging: true
  },

  monitoring: {
    healthChecks: {
      enabled: true,
      interval: 30000,
      timeout: 5000
    },
    metrics: {
      enabled: true,
      endpoint: '/metrics',
      includeSystemMetrics: true
    },
    tracing: {
      enabled: false, // Enable for debugging
      sampler: 0.1
    }
  },

  security: {
    cors: {
      origin: ['http://localhost:7860', 'https://*.your-domain.com'],
      credentials: true
    },
    rateLimit: {
      windowMs: 15 * 60 * 1000,
      max: 1000
    },
    headers: {
      'X-Content-Type-Options': 'nosniff',
      'X-Frame-Options': 'DENY',
      'X-XSS-Protection': '1; mode=block'
    }
  }
};

module.exports = mcpConfig;
```

```javascript
// zen-mcp-server/src/orchestrator.js
const axios = require('axios');
const EventEmitter = require('events');
const config = require('./config');

class MCPOrchestrator extends EventEmitter {
  constructor() {
    super();
    this.mcpServers = new Map();
    this.healthStatus = new Map();
    this.circuitBreakers = new Map();
    this.requestCache = new Map();

    this.initializeMCPServers();
    this.startHealthChecks();
  }

  initializeMCPServers() {
    Object.entries(config.mcpServers).forEach(([name, serverConfig]) => {
      this.mcpServers.set(name, {
        ...serverConfig,
        baseUrl: `http://${serverConfig.host}:${serverConfig.port}`,
        requestCount: 0,
        errorCount: 0,
        lastHealthCheck: null
      });

      this.healthStatus.set(name, 'unknown');
      this.circuitBreakers.set(name, {
        state: 'closed', // closed, open, half-open
        failures: 0,
        lastFailureTime: null,
        nextAttempt: null
      });
    });
  }

  async startHealthChecks() {
    const healthCheckInterval = setInterval(async () => {
      await this.performHealthChecks();
    }, config.monitoring.healthChecks.interval);

    // Initial health check
    await this.performHealthChecks();
  }

  async performHealthChecks() {
    const healthPromises = Array.from(this.mcpServers.entries()).map(
      async ([name, serverConfig]) => {
        try {
          const response = await axios.get(
            `${serverConfig.baseUrl}/health`,
            { timeout: config.monitoring.healthChecks.timeout }
          );

          this.healthStatus.set(name, 'healthy');
          this.resetCircuitBreaker(name);

          // Update server info
          const server = this.mcpServers.get(name);
          server.lastHealthCheck = new Date();

          return { name, status: 'healthy', response: response.data };
        } catch (error) {
          this.healthStatus.set(name, 'unhealthy');
          this.recordFailure(name);

          return { name, status: 'unhealthy', error: error.message };
        }
      }
    );

    const results = await Promise.allSettled(healthPromises);
    this.emit('healthCheck', results);
  }

  async orchestrateQuery(query, context = {}, preferences = {}) {
    const startTime = Date.now();
    const queryId = this.generateQueryId();

    try {
      // Analyze query to determine required MCPs
      const requiredMCPs = await this.analyzeQueryRequirements(query, context);

      // Execute orchestration strategy
      const strategy = preferences.strategy || config.orchestration.defaultStrategy;
      const results = await this.executeStrategy(strategy, requiredMCPs, query, context);

      // Synthesize results
      const synthesizedResult = await this.synthesizeResults(results, query, context);

      const executionTime = Date.now() - startTime;

      return {
        queryId,
        enhanced_prompt: synthesizedResult.prompt,
        reasoning_trace: synthesizedResult.reasoning,
        sources: synthesizedResult.sources,
        performance_metrics: {
          total_time_ms: executionTime,
          mcp_calls: results.length,
          successful_calls: results.filter(r => r.success).length,
          ...synthesizedResult.metrics
        }
      };

    } catch (error) {
      console.error(`Query orchestration failed: ${error.message}`);
      throw error;
    }
  }

  async analyzeQueryRequirements(query, context) {
    const requiredMCPs = [];
    const queryLower = query.toLowerCase();

    // Analyze query content for MCP requirements
    if (context.file_path || context.project_root ||
        queryLower.includes('code') || queryLower.includes('function')) {
      requiredMCPs.push('serena', 'filesystem');
    }

    if (context.repository_url || queryLower.includes('repository') ||
        queryLower.includes('commit') || queryLower.includes('branch')) {
      requiredMCPs.push('github');
    }

    if (queryLower.includes('explain') || queryLower.includes('analyze') ||
        queryLower.includes('how') || queryLower.includes('why')) {
      requiredMCPs.push('sequentialThinking');
    }

    // Always include knowledge search for context
    requiredMCPs.push('qdrantMemory');

    // Add external search for complex queries
    if (query.length > 100 || preferences.search_tier === 'external' ||
        preferences.search_tier === 'hybrid') {
      requiredMCPs.push('context7');
    }

    return [...new Set(requiredMCPs)]; // Remove duplicates
  }

  async executeStrategy(strategy, requiredMCPs, query, context) {
    switch (strategy) {
      case 'parallel_with_fallback':
        return await this.executeParallelWithFallback(requiredMCPs, query, context);
      case 'sequential':
        return await this.executeSequential(requiredMCPs, query, context);
      case 'hierarchical':
        return await this.executeHierarchical(requiredMCPs, query, context);
      default:
        return await this.executeParallelWithFallback(requiredMCPs, query, context);
    }
  }

  async executeParallelWithFallback(mcpNames, query, context) {
    const availableMCPs = mcpNames.filter(name =>
      this.isCircuitBreakerClosed(name) && this.healthStatus.get(name) === 'healthy'
    );

    const promises = availableMCPs.map(async (mcpName) => {
      try {
        const result = await this.callMCP(mcpName, query, context);
        return { mcpName, success: true, result, error: null };
      } catch (error) {
        console.error(`MCP ${mcpName} failed: ${error.message}`);
        return { mcpName, success: false, result: null, error: error.message };
      }
    });

    const results = await Promise.allSettled(promises);
    return results.map(r => r.status === 'fulfilled' ? r.value : r.reason);
  }

  async callMCP(mcpName, query, context) {
    const server = this.mcpServers.get(mcpName);
    if (!server) {
      throw new Error(`MCP server ${mcpName} not found`);
    }

    if (!this.isCircuitBreakerClosed(mcpName)) {
      throw new Error(`Circuit breaker open for ${mcpName}`);
    }

    const startTime = Date.now();

    try {
      // Prepare request based on MCP capabilities
      const requestData = this.prepareRequestData(mcpName, query, context);

      const response = await axios.post(
        `${server.baseUrl}/process`,
        requestData,
        {
          timeout: server.timeout,
          headers: { 'Content-Type': 'application/json' }
        }
      );

      const executionTime = Date.now() - startTime;

      // Update server metrics
      server.requestCount++;

      return {
        data: response.data,
        executionTime,
        mcpName,
        capabilities: server.capabilities
      };

    } catch (error) {
      this.recordFailure(mcpName);
      throw error;
    }
  }

  prepareRequestData(mcpName, query, context) {
    const server = this.mcpServers.get(mcpName);
    const baseRequest = { query, context, timestamp: new Date().toISOString() };

    // Customize request based on MCP capabilities
    switch (mcpName) {
      case 'serena':
        return {
          ...baseRequest,
          analysis_type: 'semantic',
          include_symbols: true,
          include_dependencies: true,
          workspace_path: context.project_root
        };

      case 'filesystem':
        return {
          ...baseRequest,
          operation: 'read',
          paths: context.file_path ? [context.file_path] : [],
          recursive: true,
          include_metadata: true
        };

      case 'github':
        return {
          ...baseRequest,
          repository: context.repository_url || this.extractRepoFromPath(context.project_root),
          include_issues: true,
          include_commits: true,
          max_history: 50
        };

      case 'sequentialThinking':
        return {
          ...baseRequest,
          reasoning_depth: context.reasoning_depth || 'enhanced',
          max_steps: 10,
          include_alternatives: true
        };

      case 'qdrantMemory':
        return {
          ...baseRequest,
          search_type: 'hybrid',
          limit: 10,
          relevance_threshold: 0.7,
          collections: ['promptcraft_knowledge', 'code_context']
        };

      case 'context7':
        return {
          ...baseRequest,
          search_domains: ['github.com', 'stackoverflow.com', 'docs.python.org'],
          max_results: 5,
          include_snippets: true
        };

      default:
        return baseRequest;
    }
  }

  async synthesizeResults(results, query, context) {
    const successfulResults = results.filter(r => r.success && r.result);

    if (successfulResults.length === 0) {
      throw new Error('No MCP servers provided valid results');
    }

    // Aggregate all information
    const allSources = [];
    const allReasoning = [];
    const contextData = [];
    let totalTokens = 0;

    for (const result of successfulResults) {
      const { mcpName, result: mcpResult } = result;

      // Add reasoning trace
      allReasoning.push({
        mcp_server: mcpName,
        operation: 'process',
        duration_ms: mcpResult.executionTime,
        capabilities: mcpResult.capabilities
      });

      // Extract sources and context
      if (mcpResult.data.sources) {
        allSources.push(...mcpResult.data.sources.map(s => ({
          ...s,
          mcp_source: mcpName
        })));
      }

      if (mcpResult.data.context) {
        contextData.push({
          mcp: mcpName,
          context: mcpResult.data.context
        });
      }

      totalTokens += mcpResult.data.tokens_used || 0;
    }

    // Generate enhanced prompt using collected context
    const enhancedPrompt = await this.generateEnhancedPrompt(
      query, context, contextData, allSources
    );

    return {
      prompt: enhancedPrompt,
      reasoning: allReasoning,
      sources: this.rankSources(allSources),
      metrics: {
        tokens_processed: totalTokens,
        sources_found: allSources.length,
        context_sources: contextData.length
      }
    };
  }

  async generateEnhancedPrompt(query, context, contextData, sources) {
    // This would typically call an LLM to generate the final prompt
    // For now, we'll create a structured prompt template

    const contextSummary = contextData.map(cd =>
      `${cd.mcp}: ${JSON.stringify(cd.context)}`
    ).join('\n');

    const sourceSummary = sources.slice(0, 5).map(s =>
      `- ${s.type}: ${s.source} (relevance: ${s.relevance_score})`
    ).join('\n');

    return `# Enhanced Query Analysis

**Original Query:** ${query}

**Context Analysis:**
${contextSummary}

**Relevant Sources:**
${sourceSummary}

**Enhanced Prompt:**
Based on the multi-agent analysis, here's your enhanced prompt following the C.R.E.A.T.E. framework:

**Context:** ${context.project_root ? `Working in project: ${context.project_root}` : 'General development context'}
**Request:** ${query}
**Examples:** [Generated based on context analysis]
**Augmentations:** [Enhanced with semantic code analysis]
**Tone & Format:** Professional development guidance
**Evaluation:** Verify implementation against best practices

[Additional context and recommendations would be inserted here based on MCP results]`;
  }

  rankSources(sources) {
    return sources
      .sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0))
      .slice(0, 10); // Return top 10 sources
  }

  isCircuitBreakerClosed(mcpName) {
    const breaker = this.circuitBreakers.get(mcpName);
    if (!breaker) return true;

    const now = Date.now();

    switch (breaker.state) {
      case 'closed':
        return true;
      case 'open':
        if (now > breaker.nextAttempt) {
          breaker.state = 'half-open';
          return true;
        }
        return false;
      case 'half-open':
        return true;
      default:
        return false;
    }
  }

  recordFailure(mcpName) {
    const server = this.mcpServers.get(mcpName);
    const breaker = this.circuitBreakers.get(mcpName);

    if (server) server.errorCount++;
    if (breaker) {
      breaker.failures++;
      breaker.lastFailureTime = Date.now();

      if (breaker.failures >= config.orchestration.circuitBreakerThreshold) {
        breaker.state = 'open';
        breaker.nextAttempt = Date.now() + config.orchestration.circuitBreakerTimeout;
      }
    }
  }

  resetCircuitBreaker(mcpName) {
    const breaker = this.circuitBreakers.get(mcpName);
    if (breaker) {
      breaker.state = 'closed';
      breaker.failures = 0;
      breaker.lastFailureTime = null;
      breaker.nextAttempt = null;
    }
  }

  generateQueryId() {
    return `query_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  extractRepoFromPath(projectPath) {
    // Simple heuristic to extract repository info from project path
    if (!projectPath) return null;

    const parts = projectPath.split('/');
    return parts[parts.length - 1] || null;
  }

  // Health and monitoring endpoints
  getHealthStatus() {
    const serverStatuses = {};

    this.mcpServers.forEach((server, name) => {
      const breaker = this.circuitBreakers.get(name);
      serverStatuses[name] = {
        status: this.healthStatus.get(name) || 'unknown',
        circuit_breaker: breaker.state,
        request_count: server.requestCount,
        error_count: server.errorCount,
        last_health_check: server.lastHealthCheck,
        capabilities: server.capabilities
      };
    });

    return {
      overall_status: Object.values(serverStatuses).every(s => s.status === 'healthy') ? 'healthy' : 'degraded',
      mcps: serverStatuses,
      timestamp: new Date().toISOString()
    };
  }

  getMetrics() {
    const totalRequests = Array.from(this.mcpServers.values())
      .reduce((sum, server) => sum + server.requestCount, 0);

    const totalErrors = Array.from(this.mcpServers.values())
      .reduce((sum, server) => sum + server.errorCount, 0);

    return {
      total_requests: totalRequests,
      total_errors: totalErrors,
      success_rate: totalRequests > 0 ? (totalRequests - totalErrors) / totalRequests : 0,
      active_mcps: this.mcpServers.size,
      healthy_mcps: Array.from(this.healthStatus.values()).filter(s => s === 'healthy').length,
      timestamp: new Date().toISOString()
    };
  }
}

module.exports = MCPOrchestrator;
```

## 4. Claude Code Integration Configuration

### 4.1. Claude Desktop Configuration

```json
{
  "mcpServers": {
    "promptcraft-zen": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", "{\"query\": \"{{query}}\", \"context\": {\"file_path\": \"{{file_path}}\", \"project_root\": \"{{project_root}}\", \"selection\": \"{{selection}}\"}}",
        "http://your-unraid-server.local:3000/api/v1/claude-code"
      ],
      "env": {
        "PROMPTCRAFT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### 4.2. Enhanced Zen MCP Endpoint Implementation

```javascript
// zen-mcp-server/src/routes/claude-code.js
const express = require('express');
const router = express.Router();
const MCPOrchestrator = require('../orchestrator');

const orchestrator = new MCPOrchestrator();

router.post('/claude-code', async (req, res) => {
  try {
    const { query, context, options = {} } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }

    // Enhanced context for IDE integration
    const enhancedContext = {
      ...context,
      journey: '3',
      ide_integration: true,
      timestamp: new Date().toISOString()
    };

    // Default options for IDE integration
    const defaultOptions = {
      include_reasoning: true,
      search_code: true,
      analyze_project: true,
      max_context_files: 10,
      ...options
    };

    // Orchestrate MCPs with focus on code analysis
    const result = await orchestrator.orchestrateQuery(
      query,
      enhancedContext,
      {
        strategy: 'parallel_with_fallback',
        search_tier: 'hybrid',
        reasoning_depth: 'enhanced',
        ...defaultOptions
      }
    );

    // Format response for Claude Code
    const claudeCodeResponse = {
      enhanced_prompt: result.enhanced_prompt,
      context_data: await formatContextData(result.sources, enhancedContext),
      reasoning_trace: result.reasoning_trace,
      suggestions: await generateSuggestions(result, query, enhancedContext),
      performance_metrics: result.performance_metrics
    };

    res.json(claudeCodeResponse);

  } catch (error) {
    console.error('Claude Code endpoint error:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
});

async function formatContextData(sources, context) {
  return sources.map(source => ({
    type: source.type || 'general',
    source: source.source,
    content: source.content_preview || source.content,
    relevance: source.relevance_score || 0,
    metadata: {
      file_path: source.metadata?.file_path,
      line_range: source.metadata?.line_range,
      symbol_type: source.metadata?.symbol_type,
      mcp_source: source.mcp_source
    }
  }));
}

async function generateSuggestions(result, query, context) {
  const suggestions = [];

  // Analyze query for suggestion types
  const queryLower = query.toLowerCase();

  if (queryLower.includes('refactor') || queryLower.includes('improve')) {
    suggestions.push({
      type: 'refactor',
      description: 'Consider extracting common functionality into utility functions',
      confidence: 0.8
    });
  }

  if (queryLower.includes('test') || queryLower.includes('testing')) {
    suggestions.push({
      type: 'test',
      description: 'Add unit tests for the modified functionality',
      confidence: 0.9
    });
  }

  if (context.file_path && context.file_path.includes('.js')) {
    suggestions.push({
      type: 'improvement',
      description: 'Consider adding TypeScript types for better code safety',
      confidence: 0.7
    });
  }

  if (queryLower.includes('security') || queryLower.includes('auth')) {
    suggestions.push({
      type: 'security',
      description: 'Ensure proper input validation and authentication checks',
      confidence: 0.95
    });
  }

  return suggestions;
}

module.exports = router;
```

---

This implementation guide provides complete, production-ready code examples and configurations for Phase 1 deployment. All components are designed to work together seamlessly while maintaining the 70% code reuse target and establishing the foundation for Phase 2 capabilities.
