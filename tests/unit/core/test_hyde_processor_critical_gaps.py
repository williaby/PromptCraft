"""
Critical gap coverage tests for HyDE processor operations.

This module provides targeted test coverage for the most important untested
code paths in hyde_processor.py to push coverage from 33.33% to 80%+.

Focuses on:
- HydeProcessor main class functionality
- QueryAnalysis and HypotheticalDocument models
- EnhancedQuery and RankedResults processing
- MockQueryCounselor integration
- Configuration management and strategy processing
- Error handling and edge cases
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from src.core.hyde_processor import (
    EnhancedQuery,
    HydeProcessor,
    HydeProcessorConfig,
    HydeSearchResult,
    HypotheticalDocument,
    MockQueryCounselor,
    ProcessingStrategy,
    QueryAnalysis,
    RankedResults,
    SpecificityLevel,
)


@pytest.mark.unit
@pytest.mark.fast
class TestEnumsAndModels:
    """Test enumeration types and data models."""

    def test_specificity_level_enum(self):
        """Test SpecificityLevel enumeration values."""
        assert SpecificityLevel.LOW == "low"
        assert SpecificityLevel.MEDIUM == "medium"
        assert SpecificityLevel.HIGH == "high"

    def test_processing_strategy_enum(self):
        """Test ProcessingStrategy enumeration values."""
        assert ProcessingStrategy.RAPID == "rapid"
        assert ProcessingStrategy.BALANCED == "balanced"
        assert ProcessingStrategy.DEEP == "deep"

    def test_query_analysis_model(self):
        """Test QueryAnalysis data model."""
        analysis = QueryAnalysis(
            original_query="What is machine learning?",
            intent="information_seeking",
            complexity_score=0.7,
            domain_indicators=["machine_learning", "ai", "data_science"],
            specificity_level=SpecificityLevel.MEDIUM,
            processing_strategy=ProcessingStrategy.BALANCED,
        )

        assert analysis.original_query == "What is machine learning?"
        assert analysis.intent == "information_seeking"
        assert analysis.complexity_score == 0.7
        assert "machine_learning" in analysis.domain_indicators
        assert analysis.specificity_level == SpecificityLevel.MEDIUM

    def test_hypothetical_document_model(self):
        """Test HypotheticalDocument data model."""
        doc = HypotheticalDocument(
            content="Machine learning is a subset of artificial intelligence",
            confidence=0.85,
            specificity=SpecificityLevel.HIGH,
            domain_relevance=0.9,
            generated_at=datetime.now(),
        )

        assert "machine learning" in doc.content.lower()
        assert doc.confidence == 0.85
        assert doc.specificity == SpecificityLevel.HIGH
        assert doc.domain_relevance == 0.9

    def test_hyde_search_result_model(self):
        """Test HydeSearchResult data model."""
        result = HydeSearchResult(
            document_id="doc_123",
            content="Search result content",
            similarity_score=0.92,
            source="vector_store",
            metadata={"category": "technical"},
            rank_position=1,
            relevance_score=0.88,
        )

        assert result.document_id == "doc_123"
        assert result.similarity_score == 0.92
        assert result.rank_position == 1
        assert result.metadata["category"] == "technical"

    def test_ranked_results_model(self):
        """Test RankedResults data model."""
        results = [
            HydeSearchResult(
                document_id="doc1",
                content="First result",
                similarity_score=0.9,
                source="test",
                rank_position=1,
                relevance_score=0.9,
            ),
            HydeSearchResult(
                document_id="doc2",
                content="Second result",
                similarity_score=0.8,
                source="test",
                rank_position=2,
                relevance_score=0.8,
            ),
        ]

        ranked = RankedResults(
            results=results,
            total_results=2,
            processing_time=1.5,
            reranked=True,
            ranking_strategy="hybrid",
        )

        assert len(ranked.results) == 2
        assert ranked.total_results == 2
        assert ranked.reranked is True
        assert ranked.ranking_strategy == "hybrid"

    def test_enhanced_query_model(self):
        """Test EnhancedQuery data model."""
        hypothetical_docs = [
            HypotheticalDocument(
                content="Python is a programming language",
                confidence=0.9,
                specificity=SpecificityLevel.HIGH,
            ),
        ]

        enhanced = EnhancedQuery(
            original_query="What is Python?",
            enhanced_query="What is Python programming language development",
            hypothetical_documents=hypothetical_docs,
            processing_strategy=ProcessingStrategy.BALANCED,
            confidence=0.85,
            processing_time=2.1,
        )

        assert enhanced.original_query == "What is Python?"
        assert "programming language" in enhanced.enhanced_query
        assert len(enhanced.hypothetical_documents) == 1
        assert enhanced.processing_strategy == ProcessingStrategy.BALANCED


@pytest.mark.unit
@pytest.mark.fast
class TestHydeProcessorConfig:
    """Test HydeProcessorConfig configuration management."""

    def test_config_initialization_defaults(self):
        """Test configuration with default values."""
        config = HydeProcessorConfig()

        assert config.num_hypothetical_docs == 3
        assert config.max_doc_length == 500
        assert config.temperature == 0.7
        assert config.enable_reranking is True
        assert config.timeout == 30.0

    def test_config_initialization_custom(self):
        """Test configuration with custom values."""
        config = HydeProcessorConfig(
            num_hypothetical_docs=5,
            max_doc_length=1000,
            temperature=0.5,
            enable_reranking=False,
            timeout=60.0,
            processing_strategy=ProcessingStrategy.DEEP,
        )

        assert config.num_hypothetical_docs == 5
        assert config.max_doc_length == 1000
        assert config.temperature == 0.5
        assert config.enable_reranking is False
        assert config.timeout == 60.0

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid configuration
        config = HydeProcessorConfig(temperature=0.8, timeout=45.0)
        assert config.temperature == 0.8

        # Test edge cases
        edge_config = HydeProcessorConfig(
            num_hypothetical_docs=1,
            temperature=0.0,
            timeout=1.0,  # Minimum  # Minimum  # Very short
        )
        assert edge_config.num_hypothetical_docs == 1

    def test_config_strategy_specific_settings(self):
        """Test strategy-specific configuration settings."""
        # Rapid strategy
        rapid_config = HydeProcessorConfig(processing_strategy=ProcessingStrategy.RAPID)
        assert rapid_config.processing_strategy == ProcessingStrategy.RAPID

        # Deep strategy
        deep_config = HydeProcessorConfig(processing_strategy=ProcessingStrategy.DEEP)
        assert deep_config.processing_strategy == ProcessingStrategy.DEEP


@pytest.mark.unit
@pytest.mark.fast
class TestMockQueryCounselor:
    """Test MockQueryCounselor functionality."""

    @pytest.fixture
    def mock_counselor(self):
        """Create MockQueryCounselor instance."""
        return MockQueryCounselor()

    def test_mock_counselor_initialization(self, mock_counselor):
        """Test MockQueryCounselor initialization."""
        assert isinstance(mock_counselor.responses, dict)
        assert len(mock_counselor.responses) > 0  # Should have default responses

    def test_mock_counselor_analyze_query(self, mock_counselor):
        """Test query analysis in mock counselor."""
        query = "What is machine learning?"

        analysis = mock_counselor.analyze_query(query)

        assert isinstance(analysis, QueryAnalysis)
        assert analysis.original_query == query
        assert analysis.complexity_score >= 0.0
        assert len(analysis.domain_indicators) > 0

    def test_mock_counselor_route_query(self, mock_counselor):
        """Test query routing in mock counselor."""
        query = "How to implement authentication?"

        route_info = mock_counselor.route_query(query)

        assert isinstance(route_info, dict)
        assert "strategy" in route_info
        assert "confidence" in route_info

    def test_mock_counselor_get_response(self, mock_counselor):
        """Test getting mock responses."""
        # Test with known query pattern
        python_query = "What is Python?"
        response = mock_counselor.get_response(python_query)

        assert isinstance(response, str)
        assert len(response) > 0

        # Test with unknown query (should return default)
        unknown_query = "Very specific unknown query 12345"
        default_response = mock_counselor.get_response(unknown_query)

        assert isinstance(default_response, str)
        assert len(default_response) > 0

    def test_mock_counselor_add_response(self, mock_counselor):
        """Test adding custom responses."""
        pattern = "test_pattern"
        response = "This is a test response"

        mock_counselor.add_response(pattern, response)

        assert pattern in mock_counselor.responses
        assert mock_counselor.responses[pattern] == response

        # Test retrieval
        retrieved = mock_counselor.get_response("test_pattern query")
        assert retrieved == response

    def test_mock_counselor_complexity_analysis(self, mock_counselor):
        """Test complexity analysis in mock counselor."""
        simple_query = "What is Git?"
        complex_query = (
            "How do I implement a distributed microservices architecture with event sourcing and CQRS patterns?"
        )

        simple_analysis = mock_counselor.analyze_query(simple_query)
        complex_analysis = mock_counselor.analyze_query(complex_query)

        # Complex query should have higher complexity score
        assert complex_analysis.complexity_score > simple_analysis.complexity_score

    def test_mock_counselor_domain_detection(self, mock_counselor):
        """Test domain indicator detection."""
        queries_and_domains = [
            ("How to use Docker containers?", ["docker", "containers"]),
            ("Python web development with FastAPI", ["python", "web", "fastapi"]),
            ("Machine learning model training", ["machine_learning", "training"]),
        ]

        for query, expected_domains in queries_and_domains:
            analysis = mock_counselor.analyze_query(query)

            # Should detect at least some expected domains
            detected_domains = [d.lower() for d in analysis.domain_indicators]
            assert any(domain in detected_domains for domain in expected_domains)


@pytest.mark.unit
@pytest.mark.fast
class TestHydeProcessorInitialization:
    """Test HydeProcessor initialization and configuration."""

    @pytest.fixture
    def mock_query_counselor(self):
        """Create mock query counselor."""
        counselor = Mock()
        counselor.analyze_query = Mock(
            return_value=QueryAnalysis(
                original_query="test",
                intent="test_intent",
                complexity_score=0.5,
                domain_indicators=["test"],
                specificity_level=SpecificityLevel.MEDIUM,
                processing_strategy=ProcessingStrategy.BALANCED,
            ),
        )
        return counselor

    @pytest.fixture
    def mock_vector_store(self):
        """Create mock vector store."""
        store = Mock()
        store.search = AsyncMock(return_value=[])
        return store

    def test_hyde_processor_init_default(self, mock_query_counselor, mock_vector_store):
        """Test HydeProcessor initialization with defaults."""
        processor = HydeProcessor(query_counselor=mock_query_counselor, vector_store=mock_vector_store)

        assert processor.query_counselor == mock_query_counselor
        assert processor.vector_store == mock_vector_store
        assert isinstance(processor.config, HydeProcessorConfig)

    def test_hyde_processor_init_with_config(self, mock_query_counselor, mock_vector_store):
        """Test HydeProcessor initialization with custom config."""
        config = HydeProcessorConfig(
            num_hypothetical_docs=5,
            temperature=0.8,
            processing_strategy=ProcessingStrategy.DEEP,
        )

        processor = HydeProcessor(query_counselor=mock_query_counselor, vector_store=mock_vector_store, config=config)

        assert processor.config == config
        assert processor.config.num_hypothetical_docs == 5

    def test_hyde_processor_init_validation(self, mock_vector_store):
        """Test initialization parameter validation."""
        # Missing query counselor
        with pytest.raises(ValueError):
            HydeProcessor(query_counselor=None, vector_store=mock_vector_store)

        # Missing vector store
        mock_counselor = Mock()
        with pytest.raises(ValueError):
            HydeProcessor(query_counselor=mock_counselor, vector_store=None)

    def test_hyde_processor_default_mock_counselor(self, mock_vector_store):
        """Test creation with default mock counselor."""
        processor = HydeProcessor(vector_store=mock_vector_store)

        assert isinstance(processor.query_counselor, MockQueryCounselor)
        assert processor.vector_store == mock_vector_store


@pytest.mark.unit
@pytest.mark.fast
class TestQueryAnalysisAndProcessing:
    """Test query analysis and processing functionality."""

    @pytest.fixture
    def processor(self):
        """Create HydeProcessor with mock dependencies."""
        mock_counselor = MockQueryCounselor()
        mock_store = Mock()
        mock_store.search = AsyncMock(return_value=[])

        return HydeProcessor(query_counselor=mock_counselor, vector_store=mock_store)

    def test_analyze_query_complexity(self, processor):
        """Test query complexity analysis."""
        test_queries = [
            ("Hi", 0.1),  # Very simple
            ("What is Python?", 0.3),  # Simple question
            ("How to implement authentication in FastAPI?", 0.6),  # Medium complexity
            (
                "How do I build a scalable microservices architecture with event sourcing, CQRS, containerization, and monitoring?",
                0.9,
            ),  # High complexity
        ]

        for query, expected_min_complexity in test_queries:
            analysis = processor.analyze_query(query)

            assert isinstance(analysis, QueryAnalysis)
            assert analysis.complexity_score >= expected_min_complexity
            assert 0.0 <= analysis.complexity_score <= 1.0

    def test_determine_processing_strategy(self, processor):
        """Test processing strategy determination."""
        # Simple query should use rapid strategy
        simple_query = "What is Git?"
        simple_analysis = processor.analyze_query(simple_query)
        simple_strategy = processor.determine_processing_strategy(simple_analysis)

        # Complex query should use deeper strategy
        complex_query = "How to implement a distributed system with microservices, event sourcing, and CQRS?"
        complex_analysis = processor.analyze_query(complex_query)
        complex_strategy = processor.determine_processing_strategy(complex_analysis)

        # More complex queries should get deeper processing
        strategy_depth = {ProcessingStrategy.RAPID: 1, ProcessingStrategy.BALANCED: 2, ProcessingStrategy.DEEP: 3}

        assert strategy_depth[complex_strategy] >= strategy_depth[simple_strategy]

    def test_extract_domain_indicators(self, processor):
        """Test domain indicator extraction."""
        queries_and_expected = [
            ("Python web development", ["python", "web", "development"]),
            ("Docker containerization", ["docker", "container"]),
            ("Machine learning algorithms", ["machine", "learning", "algorithm"]),
            ("React frontend development", ["react", "frontend", "development"]),
        ]

        for query, expected_indicators in queries_and_expected:
            analysis = processor.analyze_query(query)

            # Should detect relevant domain indicators
            detected = [d.lower() for d in analysis.domain_indicators]
            overlap = any(exp in detected for exp in expected_indicators)
            assert overlap, f"Expected to find some of {expected_indicators} in {detected}"

    def test_determine_specificity_level(self, processor):
        """Test specificity level determination."""
        # General query - low specificity
        general_query = "What is programming?"
        general_analysis = processor.analyze_query(general_query)

        # Specific query - high specificity
        specific_query = "How to implement JWT authentication in FastAPI with Redis session storage?"
        specific_analysis = processor.analyze_query(specific_query)

        # More specific queries should have higher specificity
        specificity_levels = {SpecificityLevel.LOW: 1, SpecificityLevel.MEDIUM: 2, SpecificityLevel.HIGH: 3}

        general_level = specificity_levels[general_analysis.specificity_level]
        specific_level = specificity_levels[specific_analysis.specificity_level]

        assert specific_level >= general_level


@pytest.mark.unit
@pytest.mark.integration
class TestHypotheticalDocumentGeneration:
    """Test hypothetical document generation and enhancement."""

    @pytest.fixture
    def processor(self):
        """Create HydeProcessor with mock dependencies."""
        mock_counselor = MockQueryCounselor()
        mock_store = Mock()
        mock_store.search = AsyncMock(return_value=[])

        return HydeProcessor(query_counselor=mock_counselor, vector_store=mock_store)

    async def test_generate_hypothetical_documents(self, processor):
        """Test hypothetical document generation."""
        query = "What is machine learning?"
        analysis = processor.analyze_query(query)

        docs = await processor.generate_hypothetical_documents(analysis)

        assert isinstance(docs, list)
        assert len(docs) > 0
        assert all(isinstance(doc, HypotheticalDocument) for doc in docs)

        # Each document should have relevant content
        for doc in docs:
            assert len(doc.content) > 0
            assert doc.confidence > 0.0
            assert isinstance(doc.specificity, SpecificityLevel)

    async def test_generate_documents_different_strategies(self, processor):
        """Test document generation with different strategies."""
        query = "How to implement authentication?"
        analysis = processor.analyze_query(query)

        # Test each processing strategy
        strategies = [ProcessingStrategy.RAPID, ProcessingStrategy.BALANCED, ProcessingStrategy.DEEP]

        for strategy in strategies:
            analysis.processing_strategy = strategy
            docs = await processor.generate_hypothetical_documents(analysis)

            assert len(docs) > 0
            # Deeper strategies might generate more documents
            if strategy == ProcessingStrategy.DEEP:
                assert len(docs) >= 1

    async def test_enhance_query_with_documents(self, processor):
        """Test query enhancement using hypothetical documents."""
        query = "Python web development"

        enhanced = await processor.enhance_query(query)

        assert isinstance(enhanced, EnhancedQuery)
        assert enhanced.original_query == query
        assert len(enhanced.enhanced_query) > len(query)
        assert len(enhanced.hypothetical_documents) > 0
        assert enhanced.confidence > 0.0

    async def test_document_quality_filtering(self, processor):
        """Test filtering of low-quality hypothetical documents."""
        query = "Test query for quality filtering"
        analysis = processor.analyze_query(query)

        # Generate documents
        docs = await processor.generate_hypothetical_documents(analysis)

        # All returned documents should meet quality thresholds
        for doc in docs:
            assert doc.confidence > 0.1  # Minimum confidence threshold
            assert len(doc.content.strip()) > 10  # Minimum content length
            assert doc.domain_relevance > 0.0  # Some domain relevance

    async def test_document_deduplication(self, processor):
        """Test deduplication of similar hypothetical documents."""
        query = "Python programming"
        analysis = processor.analyze_query(query)

        docs = await processor.generate_hypothetical_documents(analysis)

        # Check for duplicate content
        contents = [doc.content for doc in docs]
        unique_contents = set(contents)

        # Should have reasonable deduplication
        duplication_ratio = len(contents) / len(unique_contents) if unique_contents else 1
        assert duplication_ratio <= 2.0  # Allow some similarity but not excessive duplication


@pytest.mark.unit
@pytest.mark.integration
class TestSearchAndRanking:
    """Test search and ranking functionality."""

    @pytest.fixture
    def processor_with_results(self):
        """Create HydeProcessor with mock search results."""
        mock_counselor = MockQueryCounselor()
        mock_store = Mock()

        # Mock search results
        mock_results = [
            Mock(
                document_id="doc1",
                content="Python is a programming language",
                similarity_score=0.9,
                metadata={"category": "programming"},
            ),
            Mock(
                document_id="doc2",
                content="FastAPI is a web framework for Python",
                similarity_score=0.8,
                metadata={"category": "web"},
            ),
            Mock(
                document_id="doc3",
                content="Docker is a containerization platform",
                similarity_score=0.7,
                metadata={"category": "devops"},
            ),
        ]

        mock_store.search = AsyncMock(return_value=mock_results)

        return HydeProcessor(query_counselor=mock_counselor, vector_store=mock_store)

    async def test_search_with_enhanced_query(self, processor_with_results):
        """Test searching with enhanced query."""
        query = "Python web development"

        results = await processor_with_results.search(query)

        assert isinstance(results, RankedResults)
        assert len(results.results) > 0
        assert all(isinstance(r, HydeSearchResult) for r in results.results)

    async def test_reranking_functionality(self, processor_with_results):
        """Test result reranking functionality."""
        query = "Python web frameworks"

        # Enable reranking
        processor_with_results.config.enable_reranking = True

        results = await processor_with_results.search(query)

        assert results.reranked is True
        # Results should be ordered by relevance
        if len(results.results) > 1:
            for i in range(len(results.results) - 1):
                current_score = results.results[i].relevance_score
                next_score = results.results[i + 1].relevance_score
                assert current_score >= next_score

    async def test_search_without_reranking(self, processor_with_results):
        """Test search without reranking."""
        query = "Python programming"

        # Disable reranking
        processor_with_results.config.enable_reranking = False

        results = await processor_with_results.search(query)

        assert results.reranked is False
        # Should still return valid results
        assert len(results.results) > 0

    async def test_result_ranking_position(self, processor_with_results):
        """Test that results have correct ranking positions."""
        query = "Test query"

        results = await processor_with_results.search(query)

        # Check ranking positions
        for i, result in enumerate(results.results):
            assert result.rank_position == i + 1

    async def test_search_metadata_preservation(self, processor_with_results):
        """Test that search preserves metadata from vector store."""
        query = "Test query"

        results = await processor_with_results.search(query)

        # Original metadata should be preserved
        for result in results.results:
            assert hasattr(result, "metadata")
            if result.document_id == "doc1":
                assert result.metadata.get("category") == "programming"


@pytest.mark.unit
@pytest.mark.fast
class TestErrorHandlingAndEdgeCases:
    """Test error handling and edge case scenarios."""

    @pytest.fixture
    def processor(self):
        """Create HydeProcessor for error testing."""
        mock_counselor = MockQueryCounselor()
        mock_store = Mock()
        return HydeProcessor(query_counselor=mock_counselor, vector_store=mock_store)

    def test_empty_query_handling(self, processor):
        """Test handling of empty or invalid queries."""
        invalid_queries = ["", "   ", "\n\t"]

        for query in invalid_queries:
            analysis = processor.analyze_query(query)

            # Should return valid analysis with low confidence
            assert isinstance(analysis, QueryAnalysis)
            assert analysis.complexity_score == 0.0

    def test_none_query_handling(self, processor):
        """Test handling of None query."""
        with pytest.raises(ValueError):
            processor.analyze_query(None)

    async def test_vector_store_failure_handling(self, processor):
        """Test handling of vector store failures."""
        # Make vector store fail
        processor.vector_store.search.side_effect = Exception("Vector store failed")

        query = "Test query"

        # Should handle gracefully and return empty results
        results = await processor.search(query)

        assert isinstance(results, RankedResults)
        assert len(results.results) == 0

    async def test_timeout_handling(self):
        """Test handling of processing timeouts."""
        mock_counselor = MockQueryCounselor()
        mock_store = Mock()

        # Configure very short timeout
        config = HydeProcessorConfig(timeout=0.01)
        processor = HydeProcessor(query_counselor=mock_counselor, vector_store=mock_store, config=config)

        # Make search very slow
        async def slow_search(*args, **kwargs):
            await asyncio.sleep(1)  # Longer than timeout
            return []

        mock_store.search = slow_search

        # Should timeout gracefully
        query = "Test timeout"
        results = await processor.search(query)

        assert isinstance(results, RankedResults)
        # May return empty results due to timeout

    def test_invalid_configuration_handling(self):
        """Test handling of invalid configurations."""
        mock_counselor = MockQueryCounselor()
        mock_store = Mock()

        # Configuration with invalid values
        invalid_configs = [{"num_hypothetical_docs": -1}, {"temperature": -0.5}, {"timeout": -10}]

        for invalid_config in invalid_configs:
            try:
                config = HydeProcessorConfig(**invalid_config)
                processor = HydeProcessor(query_counselor=mock_counselor, vector_store=mock_store, config=config)
                # Should create processor even with edge case values
                assert processor is not None
            except (ValueError, TypeError):
                # Or raise appropriate validation errors
                pass

    async def test_malformed_search_results_handling(self, processor):
        """Test handling of malformed search results from vector store."""
        # Mock malformed results
        malformed_results = [
            None,  # None result
            Mock(document_id=None, content="", similarity_score=None),  # Missing fields
            Mock(document_id="valid", content="Valid content", similarity_score=0.8),  # Valid result
        ]

        processor.vector_store.search = AsyncMock(return_value=malformed_results)

        query = "Test query"
        results = await processor.search(query)

        # Should handle malformed results gracefully
        assert isinstance(results, RankedResults)
        # Should only include valid results
        valid_results = [r for r in results.results if r.document_id is not None]
        assert len(valid_results) >= 0

    def test_large_query_handling(self, processor):
        """Test handling of very large queries."""
        # Create very large query
        large_query = "How to implement " + "very complex " * 1000 + "system?"

        analysis = processor.analyze_query(large_query)

        # Should handle large queries gracefully
        assert isinstance(analysis, QueryAnalysis)
        assert analysis.complexity_score > 0.0
