# Vector Store Integration Guide

This guide provides comprehensive documentation for the vector store integration system in PromptCraft-Hybrid, including
abstract interfaces, mock implementations, and real Qdrant integration.

## Overview

The vector store system provides a pluggable architecture that enables seamless switching between mock and real vector
database implementations. This design supports development with mock data while preparing for production Qdrant
integration at 192.168.1.16:6333.

## Architecture

### Core Components

1. **AbstractVectorStore**: Base interface defining the contract for all implementations
2. **EnhancedMockVectorStore**: Feature-rich mock implementation for development and testing
3. **QdrantVectorStore**: Production-ready Qdrant client for external vector database
4. **VectorStoreFactory**: Factory pattern for creating appropriate store instances
5. **Supporting Models**: Pydantic models for type safety and validation

### Key Features

- **Connection Management**: Automatic connection pooling, health checks, and cleanup
- **Performance Monitoring**: Built-in metrics tracking and performance optimization
- **Error Resilience**: Circuit breaker patterns and retry logic
- **Multiple Search Strategies**: Exact, semantic, hybrid, and filtered search modes
- **Batch Operations**: Efficient bulk document insertion and deletion
- **Backward Compatibility**: Seamless integration with existing HydeProcessor

## Quick Start

### Basic Usage

```python
import asyncio
from src.core.vector_store import (
    VectorStoreFactory,
    VectorDocument,
    SearchParameters,
    VectorStoreType,
    SearchStrategy
)

async def basic_example():
    # Create mock vector store
    config = {
        "type": VectorStoreType.MOCK,
        "simulate_latency": False
    }

    store = VectorStoreFactory.create_vector_store(config)
    await store.connect()

    # Insert a document
    doc = VectorDocument(
        id="example_doc",
        content="Example document content",
        embedding=[0.1, 0.2, 0.3] + [0.0] * 381,  # 384-dimensional
        metadata={"category": "example"},
        collection="default"
    )

    result = await store.insert_documents([doc])
    print(f"Inserted: {result.success_count} documents")

    # Search for similar documents
    search_params = SearchParameters(
        embeddings=[[0.1, 0.2, 0.3] + [0.0] * 381],
        limit=5,
        strategy=SearchStrategy.SEMANTIC
    )

    results = await store.search(search_params)
    print(f"Found: {len(results)} results")

    await store.disconnect()

asyncio.run(basic_example())
```

### Context Manager Usage

```python
from src.core.vector_store import vector_store_connection

async def context_example():
    config = {"type": VectorStoreType.MOCK}

    async with vector_store_connection(config) as store:
        # Store is automatically connected and will be disconnected on exit
        health = await store.health_check()
        print(f"Store health: {health.status}")

        # Perform operations...
```

## Configuration

### Mock Store Configuration

```python
mock_config = {
    "type": VectorStoreType.MOCK,
    "simulate_latency": True,      # Simulate realistic latency
    "error_rate": 0.1,             # 10% error rate for testing
    "base_latency": 0.05           # Base latency in seconds
}
```

### Qdrant Store Configuration

```python
qdrant_config = {
    "type": VectorStoreType.QDRANT,
    "host": "192.168.1.16",        # External Qdrant on Unraid
    "port": 6333,
    "api_key": "your_api_key",     # Optional API key
    "timeout": 30.0                # Connection timeout
}
```

### Auto-Detection Configuration

```python
auto_config = {
    "type": VectorStoreType.AUTO,  # Auto-detect based on environment
    "host": "192.168.1.16",        # Qdrant connection details
    "port": 6333,
    # Falls back to mock if Qdrant unavailable
}
```

## Data Models

### VectorDocument

```python
from src.core.vector_store import VectorDocument

doc = VectorDocument(
    id="unique_document_id",
    content="Document text content",
    embedding=[0.1, 0.2, 0.3] + [0.0] * 381,  # 384-dimensional vector
    metadata={
        "category": "documentation",
        "difficulty": "intermediate",
        "tags": ["python", "async"],
        "author": "John Doe"
    },
    collection="knowledge_base",
    timestamp=1234567890.0  # Optional, defaults to current time
)
```

### SearchParameters

```python
from src.core.vector_store import SearchParameters, SearchStrategy

params = SearchParameters(
    embeddings=[[0.1, 0.2, 0.3] + [0.0] * 381],  # List of query embeddings
    limit=10,                                      # Maximum results
    collection="knowledge_base",                   # Collection to search
    strategy=SearchStrategy.SEMANTIC,             # Search strategy
    filters={"category": "documentation"},         # Metadata filters
    score_threshold=0.7,                          # Minimum similarity score
    timeout=30.0                                  # Operation timeout
)
```

## Search Strategies

### 1. Exact Search

```python
# Exact similarity matching
params = SearchParameters(
    embeddings=[query_embedding],
    strategy=SearchStrategy.EXACT
)
```

### 2. Semantic Search

```python
# Semantic similarity search (default)
params = SearchParameters(
    embeddings=[query_embedding],
    strategy=SearchStrategy.SEMANTIC
)
```

### 3. Hybrid Search

```python
# Combines dense vectors with metadata
params = SearchParameters(
    embeddings=[query_embedding],
    strategy=SearchStrategy.HYBRID  # Returns embeddings in results
)
```

### 4. Filtered Search

```python
# Search with metadata filtering
params = SearchParameters(
    embeddings=[query_embedding],
    strategy=SearchStrategy.FILTERED,
    filters={
        "difficulty": "intermediate",
        "tags": ["python", "async"],
        "year": {"gte": 2022}  # Range filter
    }
)
```

## Metadata Filtering

The vector store supports sophisticated metadata filtering:

### Simple Filters

```python
filters = {
    "category": "documentation",     # Exact match
    "difficulty": "intermediate"
}
```

### List Filters

```python
filters = {
    "tags": ["python", "async"],     # Match any in list
    "categories": ["docs", "tutorial"]
}
```

### Range Filters

```python
filters = {
    "year": {"gte": 2022, "lte": 2024},  # Greater/less than
    "score": {"gte": 0.8}                # Minimum score
}
```

## Performance Monitoring

### Getting Metrics

```python
metrics = store.get_metrics()
print(f"Searches: {metrics.search_count}")
print(f"Inserts: {metrics.insert_count}")
print(f"Avg Latency: {metrics.avg_latency:.3f}s")
print(f"Errors: {metrics.error_count}")
```

### Health Checks

```python
health = await store.health_check()
print(f"Status: {health.status}")
print(f"Latency: {health.latency:.3f}s")
print(f"Details: {health.details}")
```

## Error Handling

### Circuit Breaker Pattern

The vector store implements circuit breaker patterns for fault tolerance:

```python
# Circuit breaker automatically opens after threshold failures
# Operations return empty results when circuit is open
# Automatic recovery attempts are made periodically

# Check circuit breaker status
is_open = store._circuit_breaker_open
failures = store._circuit_breaker_failures
```

### Retry Logic Example

```python
import asyncio

async def resilient_search(store, search_params, max_retries=3):
    """Example of implementing retry logic with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return await store.search(search_params)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e

            # Exponential backoff
            await asyncio.sleep(0.1 * (2 ** attempt))

    return []  # Fallback to empty results
```

## HydeProcessor Integration

### Using Enhanced Mock Store with HydeProcessor

```python
from src.core.hyde_processor import HydeProcessor
from src.core.vector_store import MockVectorStore

# Create compatible mock store for HydeProcessor
hyde_store = MockVectorStore()  # Auto-connects

# Create HydeProcessor
processor = HydeProcessor(vector_store=hyde_store)

# Process queries
results = await processor.process_query("Python caching strategies")
```

### Storing HyDE-Generated Documents

```python
# Generate hypothetical documents
enhanced_query = await processor.three_tier_analysis(query)

if enhanced_query.processing_strategy == "standard_hyde":
    # Convert to VectorDocument format
    vector_docs = []
    for i, hyde_doc in enumerate(enhanced_query.hypothetical_docs):
        vector_doc = VectorDocument(
            id=f"hyde_{hash(query)}_{i}",
            content=hyde_doc.content,
            embedding=hyde_doc.embedding,
            metadata={
                "source": "hyde_generated",
                "relevance_score": hyde_doc.relevance_score,
                "generation_method": hyde_doc.generation_method,
                **hyde_doc.metadata
            },
            collection="hyde_documents"
        )
        vector_docs.append(vector_doc)

    # Store in enhanced vector store
    result = await enhanced_store.insert_documents(vector_docs)
```

## Collection Management

### Creating Collections

```python
# Create collection with specific vector dimensions
success = await store.create_collection("user_preferences", vector_size=512)

# Get collection information
if success:
    info = await store.get_collection_info("user_preferences")
    print(f"Vector size: {info['vector_size']}")
    print(f"Document count: {info['document_count']}")
```

### Listing Collections

```python
collections = await store.list_collections()
print(f"Available collections: {collections}")
```

### Collection-Specific Operations

```python
# Insert documents into specific collection
docs = [VectorDocument(..., collection="user_preferences")]
await store.insert_documents(docs)

# Search within specific collection
params = SearchParameters(
    embeddings=[query_embedding],
    collection="user_preferences"
)
results = await store.search(params)
```

## Batch Operations

### Bulk Document Insertion

```python
# Prepare large batch of documents
documents = []
for i in range(1000):
    doc = VectorDocument(
        id=f"bulk_doc_{i}",
        content=f"Bulk document {i}",
        embedding=[0.1 * i] * 384,
        metadata={"batch_id": "bulk_2024", "index": i}
    )
    documents.append(doc)

# Batch insert
result = await store.insert_documents(documents)
print(f"Success: {result.success_count}/{result.total_count}")
print(f"Processing time: {result.processing_time:.3f}s")
```

### Bulk Document Deletion

```python
# Delete multiple documents
document_ids = [f"bulk_doc_{i}" for i in range(100)]
result = await store.delete_documents(document_ids, collection="default")

print(f"Deleted: {result.success_count} documents")
if result.errors:
    print(f"Errors: {result.errors}")
```

## Production Deployment

### Qdrant Integration

For production deployment with external Qdrant at 192.168.1.16:6333:

1. **Install Qdrant Client**:

   ```bash
   poetry add qdrant-client
   ```

2. **Configuration**:

   ```python
   import os

   config = {
       "type": VectorStoreType.QDRANT,
       "host": os.getenv("QDRANT_HOST", "192.168.1.16"),
       "port": int(os.getenv("QDRANT_PORT", "6333")),
       "api_key": os.getenv("QDRANT_API_KEY"),
       "timeout": 30.0
   }
   ```

3. **Health Monitoring**:

   ```python
   # Regular health checks
   async def monitor_vector_store(store):
       while True:
           health = await store.health_check()
           if health.status != ConnectionStatus.HEALTHY:
               logger.warning(f"Vector store unhealthy: {health.error_message}")

           await asyncio.sleep(60)  # Check every minute
   ```

### Environment Variables

Set these environment variables for production:

```bash
QDRANT_HOST=192.168.1.16
QDRANT_PORT=6333
QDRANT_API_KEY=your_production_api_key
```

## Migration from Week 1 to Week 2

### Phase 1: Mock Development (Week 1)

```python
# Week 1: Use enhanced mock store
config = {"type": VectorStoreType.MOCK}
store = VectorStoreFactory.create_vector_store(config)
```

### Phase 2: Real Qdrant Integration (Week 2)

```python
# Week 2: Switch to real Qdrant
config = {
    "type": VectorStoreType.QDRANT,
    "host": "192.168.1.16",
    "port": 6333
}
store = VectorStoreFactory.create_vector_store(config)
```

### Gradual Migration

```python
# Use auto-detection for gradual migration
config = {
    "type": VectorStoreType.AUTO,
    "host": "192.168.1.16",
    "port": 6333
}
# Automatically uses Qdrant if available, falls back to mock
store = VectorStoreFactory.create_vector_store(config)
```

## Best Practices

### 1. Connection Management

```python
# Always use context managers when possible
async with vector_store_connection(config) as store:
    # Operations here
    pass

# Or ensure proper cleanup
store = VectorStoreFactory.create_vector_store(config)
try:
    await store.connect()
    # Operations here
finally:
    await store.disconnect()
```

### 2. Error Handling

```python
# Implement proper error handling
try:
    results = await store.search(search_params)
except Exception as e:
    logger.error(f"Search failed: {e}")
    # Implement fallback logic
    results = []
```

### 3. Performance Optimization

```python
# Batch operations when possible
await store.insert_documents(document_batch)  # Better than individual inserts

# Use appropriate search limits
params = SearchParameters(embeddings=[...], limit=10)  # Don't over-fetch

# Monitor performance
metrics = store.get_metrics()
if metrics.avg_latency > 1.0:
    logger.warning("High latency detected")
```

### 4. Collection Strategy

```python
# Use separate collections for different data types
collections = {
    "user_knowledge": {"vector_size": 384, "purpose": "User preferences"},
    "code_examples": {"vector_size": 768, "purpose": "Code snippets"},
    "documentation": {"vector_size": 512, "purpose": "API docs"}
}

for name, config in collections.items():
    await store.create_collection(name, config["vector_size"])
```

## Testing

### Unit Tests

```python
import pytest
from src.core.vector_store import EnhancedMockVectorStore

@pytest.mark.asyncio
async def test_vector_store_operations():
    config = {"type": VectorStoreType.MOCK, "simulate_latency": False}
    store = EnhancedMockVectorStore(config)
    await store.connect()

    # Test operations
    # ... test code here

    await store.disconnect()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_hyde_integration():
    # Test HydeProcessor with enhanced vector store
    # ... integration test code here
```

## Troubleshooting

### Common Issues

1. **Connection Failures**:
   - Check Qdrant server status at 192.168.1.16:6333
   - Verify network connectivity
   - Check API key configuration

2. **Performance Issues**:
   - Monitor metrics: `store.get_metrics()`
   - Check circuit breaker status
   - Optimize batch sizes

3. **Search Quality**:
   - Verify embedding dimensions match collection
   - Check metadata filter syntax
   - Adjust score thresholds

### Debug Mode

```python
import logging

# Enable debug logging
logging.getLogger("src.core.vector_store").setLevel(logging.DEBUG)

# Use debug configuration
debug_config = {
    "type": VectorStoreType.MOCK,
    "simulate_latency": True,
    "error_rate": 0.1,  # Simulate some errors
    "base_latency": 0.1  # Slower for debugging
}
```

## Examples

See `/examples/vector_store_usage.py` for comprehensive usage examples covering:

- Basic operations
- Advanced search strategies
- HydeProcessor integration
- Performance monitoring
- Error handling patterns
- Collection management
- Qdrant configuration

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review unit tests in `/tests/unit/test_vector_store.py`
3. Examine integration tests in `/tests/integration/test_vector_store_integration.py`
4. Refer to examples in `/examples/vector_store_usage.py`
