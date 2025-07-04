# Generate Qdrant Schema

Create Qdrant collection schemas and configurations for agent knowledge bases: $ARGUMENTS

## Expected Arguments

- **Agent ID**: Agent identifier for schema generation (e.g., `security_agent`, `new_agent`)

## Analysis Required

1. **Agent Validation**: Verify agent exists and has knowledge base
2. **Knowledge Base Analysis**: Assess content volume and complexity
3. **Schema Optimization**: Determine optimal vector and indexing configuration
4. **Blue-Green Setup**: Generate deployment configurations
5. **Integration Configuration**: Create MCP and ingestion pipeline configs
6. **Performance Tuning**: Optimize for expected query patterns

## Qdrant Collection Configuration

### Base Collection Schema
```python
# config/qdrant_collections.py

COLLECTION_CONFIGS = {
    "{agent_id}": {
        # Vector Configuration
        "vector_config": {
            "size": 384,  # SentenceTransformers all-MiniLM-L6-v2
            "distance": "Cosine",
            "on_disk": True  # For large collections
        },

        # HNSW Index Configuration
        "hnsw_config": {
            "m": 16,                    # Number of connections
            "ef_construct": 100,        # Construction time accuracy
            "full_scan_threshold": 10000,  # Fallback threshold
            "max_indexing_threads": 0   # Auto-detect CPU cores
        },

        # Quantization (for memory efficiency)
        "quantization_config": {
            "scalar": {
                "type": "int8",
                "quantile": 0.99,
                "always_ram": True
            }
        },

        # Storage Optimization
        "optimizers_config": {
            "deleted_threshold": 0.2,
            "vacuum_min_vector_number": 1000,
            "default_segment_number": 2,
            "max_segment_size": 200000,
            "memmap_threshold": 50000,
            "indexing_threshold": 20000,
            "flush_interval_sec": 5,
            "max_optimization_threads": 2
        },

        # Write Ahead Log
        "wal_config": {
            "wal_capacity_mb": 32,
            "wal_segments_ahead": 0
        }
    }
}
```

### Agent-Specific Optimizations

#### High-Volume Agents (>1000 documents)
```python
"{agent_id}": {
    "vector_config": {
        "size": 384,
        "distance": "Cosine",
        "on_disk": True  # Essential for large collections
    },
    "hnsw_config": {
        "m": 32,           # Increased connectivity
        "ef_construct": 200, # Higher accuracy
        "full_scan_threshold": 20000
    },
    "quantization_config": {
        "scalar": {
            "type": "int8",
            "quantile": 0.99,
            "always_ram": True
        }
    },
    "optimizers_config": {
        "default_segment_number": 4,  # More segments
        "max_segment_size": 100000,   # Smaller segments
        "memmap_threshold": 20000     # Earlier mmap usage
    }
}
```

#### Low-Volume Agents (<100 documents)
```python
"{agent_id}": {
    "vector_config": {
        "size": 384,
        "distance": "Cosine",
        "on_disk": False  # Keep in memory
    },
    "hnsw_config": {
        "m": 8,            # Reduced connectivity
        "ef_construct": 50, # Lower construction cost
        "full_scan_threshold": 1000
    },
    # No quantization for small collections
    "optimizers_config": {
        "default_segment_number": 1,
        "max_segment_size": 50000,
        "indexing_threshold": 1000
    }
}
```

#### Real-Time Agents (frequent updates)
```python
"{agent_id}": {
    "vector_config": {
        "size": 384,
        "distance": "Cosine",
        "on_disk": False
    },
    "hnsw_config": {
        "m": 16,
        "ef_construct": 100,
        "full_scan_threshold": 5000
    },
    "optimizers_config": {
        "flush_interval_sec": 1,      # Frequent flushes
        "vacuum_min_vector_number": 100,
        "deleted_threshold": 0.1,     # Aggressive cleanup
        "max_optimization_threads": 4
    },
    "wal_config": {
        "wal_capacity_mb": 64,        # Larger WAL
        "wal_segments_ahead": 2
    }
}
```

## Blue-Green Deployment Configuration

### Collection Naming Strategy
```python
# Blue-Green Collection Names
BLUE_GREEN_CONFIG = {
    "{agent_id}": {
        "blue_collection": "{agent_id}_blue",
        "green_collection": "{agent_id}_green",
        "production_alias": "{agent_id}_production",
        "staging_alias": "{agent_id}_staging"
    }
}

# Deployment States
DEPLOYMENT_STATES = {
    "blue_active": {
        "production": "{agent_id}_blue",
        "staging": "{agent_id}_green"
    },
    "green_active": {
        "production": "{agent_id}_green",
        "staging": "{agent_id}_blue"
    }
}
```

### Deployment Scripts
```python
# deployment/qdrant_deploy.py

async def deploy_agent_collection(agent_id: str, deployment_state: str):
    """Deploy agent collection with blue-green strategy."""

    config = COLLECTION_CONFIGS[agent_id]
    bg_config = BLUE_GREEN_CONFIG[agent_id]

    # Create staging collection
    staging_collection = get_staging_collection(agent_id, deployment_state)

    await qdrant_client.create_collection(
        collection_name=staging_collection,
        vectors_config=config["vector_config"],
        hnsw_config=config["hnsw_config"],
        optimizers_config=config["optimizers_config"],
        quantization_config=config.get("quantization_config"),
        wal_config=config.get("wal_config")
    )

    # Ingest knowledge base
    await ingest_agent_knowledge(agent_id, staging_collection)

    # Validate deployment
    validation_results = await validate_collection(staging_collection)

    if validation_results.passed:
        # Switch production alias
        await switch_production_alias(agent_id, deployment_state)
        return {"status": "success", "collection": staging_collection}
    else:
        # Rollback
        await cleanup_failed_deployment(staging_collection)
        return {"status": "failed", "errors": validation_results.errors}
```

## Integration Configurations

### MCP Server Integration
```python
# src/mcp_integration/qdrant_config.py

AGENT_COLLECTION_MAPPING = {
    "{agent_id}": {
        "collection_name": "{agent_id}_production",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "search_params": {
            "limit": 10,
            "score_threshold": 0.7,
            "ef": 128  # Search time accuracy
        },
        "metadata_filter": {
            "must": [
                {"key": "agent_id", "match": {"value": "{agent_id}"}},
                {"key": "status", "match": {"value": "published"}}
            ]
        }
    }
}
```

### Ingestion Pipeline Configuration
```python
# src/ingestion/pipeline_config.py

INGESTION_CONFIGS = {
    "{agent_id}": {
        "source_directory": "knowledge/{agent_id}/",
        "file_patterns": ["*.md"],
        "excluded_files": ["README.md"],

        # Processing Configuration
        "chunk_strategy": "heading_based",  # Split on H2/H3
        "min_chunk_size": 100,
        "max_chunk_size": 1000,
        "overlap_size": 50,

        # Metadata Extraction
        "extract_yaml_frontmatter": True,
        "extract_headings": True,
        "extract_links": True,

        # Quality Filters
        "min_content_length": 50,
        "exclude_draft_status": True,
        "validate_agent_id": True,

        # Embedding Configuration
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "batch_size": 32,
        "normalize_embeddings": True
    }
}
```

## Performance Monitoring Configuration

### Collection Metrics
```python
# monitoring/qdrant_metrics.py

COLLECTION_METRICS = {
    "{agent_id}": {
        "performance_targets": {
            "search_latency_p95": 100,  # milliseconds
            "index_memory_mb": 500,
            "disk_usage_gb": 2.0,
            "ingestion_rate_docs_sec": 10
        },

        "alerting_thresholds": {
            "search_latency_p95": 200,
            "memory_usage_percent": 80,
            "disk_usage_percent": 90,
            "error_rate_percent": 5
        },

        "monitoring_queries": [
            "authentication best practices",
            "security implementation",
            "oauth2 configuration"
        ]
    }
}
```

## Required Output Format

### Complete Schema Package
```markdown
# Qdrant Schema Generation Report

## Agent: {agent_id}

### Collection Configuration
```python
# Generated configuration for {agent_id}
COLLECTION_CONFIGS["{agent_id}"] = {
    "vector_config": {
        "size": 384,
        "distance": "Cosine",
        "on_disk": {on_disk_setting}
    },
    "hnsw_config": {
        "m": {m_value},
        "ef_construct": {ef_construct_value},
        "full_scan_threshold": {threshold_value}
    },
    # Additional optimizations based on analysis...
}
```

### Blue-Green Deployment
- **Blue Collection**: {agent_id}_blue
- **Green Collection**: {agent_id}_green
- **Production Alias**: {agent_id}_production
- **Staging Alias**: {agent_id}_staging

### Integration Points
- **MCP Server Config**: Updated with collection mapping
- **Ingestion Pipeline**: Configured for knowledge/{agent_id}/ directory
- **Search Parameters**: Optimized for agent domain
- **Monitoring**: Performance targets and alerting setup

### Deployment Commands
```bash
# Create collections
python scripts/create_qdrant_collection.py {agent_id}

# Deploy with blue-green
python deployment/deploy_agent.py {agent_id} --blue-green

# Validate deployment
python scripts/validate_collection.py {agent_id}_production
```

### Optimization Rationale
- **Collection Size**: {estimated_size} documents
- **Memory Strategy**: {on_disk_reasoning}
- **Index Configuration**: {index_reasoning}
- **Performance Targets**: {performance_reasoning}
```

## Validation and Testing

### Schema Validation
- [ ] Collection configuration is valid
- [ ] Blue-green aliases are properly configured
- [ ] Integration configurations are complete
- [ ] Performance targets are realistic

### Deployment Testing
- [ ] Collections can be created successfully
- [ ] Blue-green deployment works correctly
- [ ] Aliases switch properly
- [ ] Rollback procedures function

### Performance Testing
- [ ] Search latency meets targets
- [ ] Memory usage is within limits
- [ ] Ingestion performs adequately
- [ ] Concurrent access works properly

## Important Notes

- Schema optimizations based on estimated collection size and usage patterns
- Blue-green deployment enables zero-downtime knowledge updates
- Performance configurations tuned for PromptCraft-Hybrid query patterns
- Integration configurations align with MCP server requirements
- Monitoring setup provides operational visibility
- Rollback procedures ensure deployment safety
- Configuration follows infrastructure as code principles
