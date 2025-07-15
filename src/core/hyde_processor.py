"""
HyDE (Hypothetical Document Embeddings) Processor for PromptCraft-Hybrid.

This module implements the HyDE-enhanced retrieval system that improves semantic search
accuracy through three-tier query analysis and hypothetical document generation.
HyDE enhances traditional RAG (Retrieval-Augmented Generation) by generating hypothetical
documents that better match the embedding space of relevant knowledge.

The HyDE processor provides:
- Three-tier query analysis system
- Hypothetical document generation
- Enhanced semantic embedding creation
- Improved retrieval accuracy
- Multi-modal query processing

Architecture:
    The HyDE system processes queries through three progressive tiers:
    1. Direct query embedding for simple semantic matches
    2. Query expansion and reformulation for complex queries
    3. Hypothetical document generation for advanced retrieval

    This tiered approach ensures optimal retrieval performance across different
    query types and complexity levels.

Key Components:
    - Query classification and tier selection
    - Hypothetical document generation using AI models
    - Enhanced embedding creation and indexing
    - Multi-tier retrieval strategy implementation
    - Result ranking and relevance scoring

Dependencies:
    - External AI services: For document generation and embedding
    - src.config.settings: For HyDE configuration parameters
    - Qdrant vector database: For enhanced semantic search
    - src.core.zen_mcp_error_handling: For resilient processing

Called by:
    - src.core.query_counselor: For enhanced query processing
    - Agent implementations: For improved knowledge retrieval
    - RAG pipeline components: For semantic search enhancement
    - Knowledge ingestion systems: For embedding optimization

Complexity: O(k*n) where k is number of tiers and n is query/document complexity
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.core.performance_optimizer import (
    cache_hyde_processing,
    monitor_performance,
)
from src.core.vector_store import (
    AbstractVectorStore,
    EnhancedMockVectorStore,
    SearchParameters,
    SearchResult,
    SearchStrategy,
    VectorStoreFactory,
)

# Constants for HyDE processing thresholds (per hyde-processor.md)
HIGH_SPECIFICITY_THRESHOLD = 85
LOW_SPECIFICITY_THRESHOLD = 40
MAX_HYPOTHETICAL_DOCS = 3
DEFAULT_EMBEDDING_DIMENSIONS = 384


class SpecificityLevel(str, Enum):
    """Query specificity levels for HyDE processing."""

    HIGH = "high"  # Score > 85 - Skip HyDE, direct retrieval
    MEDIUM = "medium"  # Score 40-85 - Apply Standard HyDE
    LOW = "low"  # Score < 40 - Return clarifying questions


class QueryAnalysis(BaseModel):
    """Query analysis results from the Query Counselor."""

    specificity_score: float = Field(ge=0.0, le=100.0, description="Specificity score 0-100")
    specificity_level: SpecificityLevel
    reasoning: str = Field(description="Brief explanation of the scoring")
    guiding_questions: list[str] = Field(default_factory=list, description="Questions for low-specificity queries")
    processing_time: float = Field(default=0.0, description="Analysis processing time")


class HypotheticalDocument(BaseModel):
    """Generated hypothetical document for enhanced retrieval."""

    content: str = Field(description="Generated document content")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance score")
    embedding: list[float] = Field(default_factory=list, description="Document embedding vector")
    generation_method: str = Field(default="standard", description="Generation strategy used")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SearchResult(BaseModel):
    """Search result from vector database."""

    document_id: str
    content: str
    score: float = Field(ge=0.0, le=1.0, description="Similarity score")
    metadata: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="unknown", description="Result source")


class RankedResults(BaseModel):
    """Ranked and filtered search results."""

    results: list[SearchResult]
    total_found: int
    processing_time: float
    ranking_method: str = Field(default="similarity", description="Ranking strategy used")
    hyde_enhanced: bool = Field(default=False, description="Whether HyDE was applied")


class EnhancedQuery(BaseModel):
    """Enhanced query with HyDE processing applied."""

    original_query: str
    enhanced_query: str = Field(description="Processed query for search")
    embeddings: list[list[float]] = Field(default_factory=list, description="Query embeddings")
    hypothetical_docs: list[HypotheticalDocument] = Field(
        default_factory=list, description="Generated hypothetical documents",
    )
    specificity_analysis: QueryAnalysis
    processing_strategy: str = Field(description="HyDE strategy applied")


# MockVectorStore removed - now using real AbstractVectorStore implementations
# through VectorStoreFactory which provides both EnhancedMockVectorStore and QdrantVectorStore


class MockQueryCounselor:
    """Mock Query Counselor for HyDE analysis."""

    async def analyze_query_specificity(self, query: str) -> QueryAnalysis:
        """Mock query specificity analysis."""
        start_time = time.time()

        # Simple rule-based specificity scoring
        query_lower = query.lower()
        word_count = len(query.split())
        specificity_score = 50.0  # Default medium specificity

        # Increase score for specific technical terms
        technical_terms = ["implement", "configure", "install", "error", "debug", "optimize"]
        if any(term in query_lower for term in technical_terms):
            specificity_score += 20

        # Increase score for longer, more detailed queries
        if word_count > 15:
            specificity_score += 15
        elif word_count > 8:
            specificity_score += 10

        # Decrease score for vague queries
        vague_terms = ["help", "how", "what", "general", "basic", "simple"]
        if any(term in query_lower for term in vague_terms):
            specificity_score -= 10

        # Ensure score is within bounds
        specificity_score = max(0.0, min(100.0, specificity_score))

        # Determine specificity level
        if specificity_score > HIGH_SPECIFICITY_THRESHOLD:
            level = SpecificityLevel.HIGH
        elif specificity_score >= LOW_SPECIFICITY_THRESHOLD:
            level = SpecificityLevel.MEDIUM
        else:
            level = SpecificityLevel.LOW

        # Generate guiding questions for low specificity
        guiding_questions = []
        if level == SpecificityLevel.LOW:
            guiding_questions = [
                "What specific technology or framework are you working with?",
                "What is the exact problem you're trying to solve?",
                "What have you already tried?",
            ]

        processing_time = time.time() - start_time

        return QueryAnalysis(
            specificity_score=specificity_score,
            specificity_level=level,
            reasoning=f"Score based on technical terms, query length ({word_count} words), and specificity indicators",
            guiding_questions=guiding_questions,
            processing_time=processing_time,
        )


class HydeProcessor:
    """
    HyDE (Hypothetical Document Embeddings) processor for enhanced retrieval.

    Implements three-tier query analysis and processing strategy:
    - High specificity: Direct retrieval without HyDE
    - Medium specificity: Standard HyDE with hypothetical document generation
    - Low specificity: Return clarifying questions to user
    """

    def __init__(
        self,
        vector_store: AbstractVectorStore | None = None,
        query_counselor: MockQueryCounselor | None = None,
    ) -> None:
        """Initialize HydeProcessor with optional dependencies.

        Args:
            vector_store: Vector store instance (auto-creates from settings if None)
            query_counselor: Query counselor instance (creates mock if None)
        """
        self.logger = logging.getLogger(__name__)

        # Initialize vector store using factory if not provided
        if vector_store is None:
            try:
                settings = get_settings()
                vector_config = {
                    "type": settings.vector_store_type,
                    "host": settings.qdrant_host,
                    "port": settings.qdrant_port,
                    "timeout": settings.qdrant_timeout,
                    "api_key": settings.qdrant_api_key.get_secret_value() if settings.qdrant_api_key else None,
                    "simulate_latency": settings.environment == "dev",
                    "error_rate": 0.05 if settings.environment == "dev" else 0.0,
                }
                self.vector_store = VectorStoreFactory.create_vector_store(vector_config)
                self.logger.info("Initialized vector store: %s", type(self.vector_store).__name__)
            except Exception as e:
                self.logger.warning("Failed to create real vector store, using mock: %s", str(e))
                # Fallback to enhanced mock
                self.vector_store = EnhancedMockVectorStore(
                    {"simulate_latency": True, "error_rate": 0.0, "base_latency": 0.05},
                )
        else:
            self.vector_store = vector_store

        self.query_counselor = query_counselor or MockQueryCounselor()

        # Initialize vector store connection
        self._vector_store_connected = False

    @cache_hyde_processing
    @monitor_performance("three_tier_analysis")
    async def three_tier_analysis(self, query: str) -> EnhancedQuery:
        """
        Perform three-tier analysis and determine processing strategy.

        Args:
            query: User query string

        Returns:
            EnhancedQuery: Analysis results with processing strategy
        """
        start_time = time.time()

        # Validate input
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query = query.strip()

        # Analyze query specificity
        analysis = await self.query_counselor.analyze_query_specificity(query)

        # Determine processing strategy based on specificity
        if analysis.specificity_level == SpecificityLevel.HIGH:
            strategy = "direct_retrieval"
            enhanced_query = query
            hypothetical_docs = []
        elif analysis.specificity_level == SpecificityLevel.MEDIUM:
            strategy = "standard_hyde"
            enhanced_query = query
            hypothetical_docs = await self._generate_hypothetical_docs(query)
        else:  # LOW specificity
            strategy = "clarification_needed"
            enhanced_query = query
            hypothetical_docs = []

        processing_time = time.time() - start_time

        self.logger.info(
            "Three-tier analysis completed in %.3fs: %s strategy for specificity %.1f",
            processing_time,
            strategy,
            analysis.specificity_score,
        )

        return EnhancedQuery(
            original_query=query,
            enhanced_query=enhanced_query,
            embeddings=[],  # Will be populated by embedding service
            hypothetical_docs=hypothetical_docs,
            specificity_analysis=analysis,
            processing_strategy=strategy,
        )

    async def generate_hypothetical_docs(self, query: str) -> list[HypotheticalDocument]:
        """
        Generate hypothetical documents for medium-specificity queries.

        Args:
            query: User query string

        Returns:
            List[HypotheticalDocument]: Generated hypothetical documents
        """
        return await self._generate_hypothetical_docs(query)

    async def _generate_hypothetical_docs(self, query: str) -> list[HypotheticalDocument]:
        """Internal method to generate hypothetical documents."""
        start_time = time.time()

        # Mock document generation (to be replaced with real AI service)
        docs = []

        # Generate 1-3 hypothetical documents based on query
        doc_templates = [
            f"A comprehensive guide to {query} with step-by-step instructions and best practices.",
            f"Technical documentation explaining {query} with code examples and troubleshooting tips.",
            f"Expert analysis of {query} including common pitfalls and recommended solutions.",
        ]

        for i, template in enumerate(doc_templates[:MAX_HYPOTHETICAL_DOCS]):
            # Simulate document generation processing time
            await asyncio.sleep(0.02)

            # Create mock embedding (to be replaced with real embedding service)
            mock_embedding = [0.1 * (i + 1)] * DEFAULT_EMBEDDING_DIMENSIONS

            doc = HypotheticalDocument(
                content=template,
                relevance_score=0.9 - (i * 0.1),  # Decreasing relevance
                embedding=mock_embedding,
                generation_method="mock_template",
                metadata={
                    "generated_at": time.time(),
                    "query_hash": hash(query),
                    "doc_index": i,
                },
            )
            docs.append(doc)

        processing_time = time.time() - start_time
        self.logger.info("Generated %d hypothetical documents in %.3fs", len(docs), processing_time)

        return docs

    async def enhance_embeddings(self, query: str, docs: list[HypotheticalDocument]) -> list[list[float]]:
        """
        Create enhanced embeddings from query and hypothetical documents.

        Args:
            query: Original user query
            docs: Generated hypothetical documents

        Returns:
            List[List[float]]: Enhanced embedding vectors
        """
        start_time = time.time()

        embeddings = []

        # Create embedding for original query (mock implementation)
        query_embedding = [0.5] * DEFAULT_EMBEDDING_DIMENSIONS
        embeddings.append(query_embedding)

        # Add embeddings from hypothetical documents
        for doc in docs:
            if doc.embedding:
                embeddings.append(doc.embedding)

        processing_time = time.time() - start_time
        self.logger.info("Enhanced embeddings created in %.3fs: %d vectors", processing_time, len(embeddings))

        return embeddings

    async def rank_results(self, results: list[SearchResult]) -> RankedResults:
        """
        Rank and filter search results based on relevance and quality.

        Args:
            results: Raw search results from vector database

        Returns:
            RankedResults: Ranked and filtered results
        """
        start_time = time.time()

        if not results:
            return RankedResults(
                results=[],
                total_found=0,
                processing_time=time.time() - start_time,
                ranking_method="no_results",
                hyde_enhanced=False,
            )

        # Sort by similarity score (descending)
        ranked_results = sorted(results, key=lambda x: x.score, reverse=True)

        # Apply quality filtering (remove results below threshold)
        quality_threshold = 0.3
        filtered_results = [r for r in ranked_results if r.score >= quality_threshold]

        processing_time = time.time() - start_time

        self.logger.info(
            "Ranked %d results in %.3fs (filtered from %d)",
            len(filtered_results),
            processing_time,
            len(results),
        )

        return RankedResults(
            results=filtered_results,
            total_found=len(results),
            processing_time=processing_time,
            ranking_method="similarity_score",
            hyde_enhanced=bool(filtered_results),
        )

    @monitor_performance("process_query")
    async def process_query(self, query: str) -> RankedResults:
        """
        Complete HyDE processing pipeline for a query.

        Args:
            query: User query string

        Returns:
            RankedResults: Final processed and ranked results
        """
        try:
            # Step 1: Three-tier analysis
            enhanced_query = await self.three_tier_analysis(query)

            # Step 2: Handle based on processing strategy
            if enhanced_query.processing_strategy == "clarification_needed":
                # Return empty results with clarifying questions in metadata
                return RankedResults(
                    results=[],
                    total_found=0,
                    processing_time=0.0,
                    ranking_method="clarification_needed",
                    hyde_enhanced=False,
                )

            # Step 3: Create embeddings for search
            if enhanced_query.hypothetical_docs:
                # HyDE-enhanced search
                embeddings = await self.enhance_embeddings(
                    enhanced_query.enhanced_query, enhanced_query.hypothetical_docs,
                )
                hyde_enhanced = True
            else:
                # Direct search
                embeddings = [[0.5] * DEFAULT_EMBEDDING_DIMENSIONS]  # Mock query embedding
                hyde_enhanced = False

            # Step 4: Perform vector search
            search_params = SearchParameters(
                embeddings=embeddings,
                limit=10,
                collection="default",
                strategy=SearchStrategy.SEMANTIC,
                score_threshold=0.3,
            )
            search_results = await self.vector_store.search(search_params)

            # Step 5: Rank and filter results
            ranked_results = await self.rank_results(search_results)
            ranked_results.hyde_enhanced = hyde_enhanced

            return ranked_results

        except Exception as e:
            self.logger.error("HyDE processing failed: %s", str(e))
            # Return empty results with error indication
            return RankedResults(
                results=[],
                total_found=0,
                processing_time=0.0,
                ranking_method="error",
                hyde_enhanced=False,
            )
