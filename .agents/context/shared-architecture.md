# Shared Architecture Patterns

Common system architectures and integration patterns for PromptCraft agents.

## Core Architecture

### Hybrid Orchestration Model
- **Zen MCP Server**: Real-time user interactions and agent coordination
- **External Qdrant**: Vector database at 192.168.1.16:6333 for semantic search
- **FastAPI Backend**: REST API and WebSocket support
- **Gradio Frontend**: Progressive user interface with four journey levels

### Data Flow Patterns
```
User Input → HyDE Enhancement → Qdrant Retrieval → Agent Processing → Response Synthesis
```

### Agent Communication
- **MCP Protocol**: Inter-agent messaging and tool sharing
- **Async/Await**: Non-blocking operations and parallel processing
- **Circuit Breakers**: Resilience and graceful degradation
- **Event Streaming**: Real-time updates and progress tracking

## Integration Points

### Vector Database (Qdrant)
- Endpoint: `192.168.1.16:6333`
- Collections: `promptcraft_knowledge`, `user_contexts`, `agent_memories`
- Embedding Model: Azure OpenAI text-embedding-3-large
- Search Strategy: Hybrid (dense + sparse) with HyDE enhancement

### MCP Server Integration
- Protocol: Model Context Protocol over stdio/HTTP
- Discovery: Smart detection with fallback strategies
- Resource Management: Memory and CPU limits with monitoring
- Health Monitoring: Automatic restart and degradation handling

### Agent Registry
- Dynamic discovery and loading
- Capability-based routing
- Resource allocation and limits
- Performance monitoring and optimization

## Common Patterns

### Error Handling
- Graceful degradation with fallback agents
- Circuit breaker pattern for external services
- Retry logic with exponential backoff
- Comprehensive logging and monitoring

### Performance Optimization
- Token usage tracking and optimization
- Request batching and parallel processing
- Caching strategies for embeddings and responses
- Resource pooling and connection management

### Security Standards
- Input validation and sanitization
- Rate limiting and abuse prevention
- Secure secret management
- Audit logging and compliance