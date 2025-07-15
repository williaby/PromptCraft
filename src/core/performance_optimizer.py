"""
Performance optimization utilities for PromptCraft-Hybrid core components.

This module provides performance enhancements to ensure the <2s response time
requirement is met consistently across all operations. It includes caching,
connection pooling, async optimizations, and monitoring.

Key optimizations:
- LRU caching for frequent operations
- Connection pooling for vector stores
- Async batching for multiple operations
- Query result caching
- Performance monitoring and alerting
"""

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, TypeVar

# Type variables for generic caching
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])

# Performance constants
CACHE_TTL_SECONDS = 300  # 5 minutes
MAX_CACHE_SIZE = 1000
BATCH_SIZE = 50
PERFORMANCE_THRESHOLD_MS = 2000  # 2 seconds
MAX_METRICS_COUNT = 10000
METRICS_TRIMMED_COUNT = 5000
RECENT_METRICS_SECONDS = 300  # 5 minutes


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""

    operation_name: str
    start_time: float
    end_time: float = 0.0
    duration_ms: float = 0.0
    cache_hit: bool = False
    batch_size: int = 1
    error_occurred: bool = False

    def complete(self) -> None:
        """Mark operation as complete and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

    def is_slow(self) -> bool:
        """Check if operation exceeded performance threshold."""
        return self.duration_ms > PERFORMANCE_THRESHOLD_MS


# Alias for backward compatibility
PerformanceMetric = PerformanceMetrics


class LRUCache:
    """High-performance LRU cache with TTL support."""

    def __init__(self, max_size: int = MAX_CACHE_SIZE, ttl_seconds: int = CACHE_TTL_SECONDS) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired."""
        return time.time() - timestamp > self.ttl_seconds

    def _evict_expired(self) -> None:
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items() if current_time - timestamp > self.ttl_seconds
        ]
        for key in expired_keys:
            del self.cache[key]
            self.stats["evictions"] += 1

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        self._evict_expired()

        if key in self.cache:
            value, timestamp = self.cache[key]
            if not self._is_expired(timestamp):
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.stats["hits"] += 1
                return value
            del self.cache[key]
            self.stats["evictions"] += 1

        self.stats["misses"] += 1
        return None

    def put(self, key: str, value: Any) -> None:
        """Put value in cache."""
        current_time = time.time()

        if key in self.cache:
            # Update existing entry
            self.cache[key] = (value, current_time)
            self.cache.move_to_end(key)
        else:
            # Add new entry
            if len(self.cache) >= self.max_size:
                # Remove least recently used
                self.cache.popitem(last=False)
                self.stats["evictions"] += 1

            self.cache[key] = (value, current_time)

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": hit_rate,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "evictions": self.stats["evictions"],
        }


class PerformanceMonitor:
    """Performance monitoring and alerting system."""

    def __init__(self) -> None:
        self.metrics: list[PerformanceMetrics] = []
        self.alerts: list[str] = []
        self.logger = logging.getLogger(__name__)

    def start_operation(self, operation_name: str) -> PerformanceMetrics:
        """Start tracking an operation."""
        return PerformanceMetrics(operation_name=operation_name, start_time=time.time())

    def complete_operation(
        self,
        metric: PerformanceMetrics,
        cache_hit: bool = False,
        batch_size: int = 1,
        error_occurred: bool = False,
    ) -> None:
        """Complete operation tracking."""
        metric.complete()
        metric.cache_hit = cache_hit
        metric.batch_size = batch_size
        metric.error_occurred = error_occurred

        self.metrics.append(metric)

        # Check for performance issues
        if metric.is_slow():
            alert = f"Slow operation detected: {metric.operation_name} took {metric.duration_ms:.0f}ms"
            self.alerts.append(alert)
            self.logger.warning(alert)

        # Keep only recent metrics
        if len(self.metrics) > MAX_METRICS_COUNT:
            self.metrics = self.metrics[-METRICS_TRIMMED_COUNT:]

    def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary statistics."""
        if not self.metrics:
            return {"total_operations": 0}

        recent_metrics = [m for m in self.metrics if time.time() - m.end_time < RECENT_METRICS_SECONDS]

        durations = [m.duration_ms for m in recent_metrics]
        cache_hits = sum(1 for m in recent_metrics if m.cache_hit)
        errors = sum(1 for m in recent_metrics if m.error_occurred)
        slow_operations = sum(1 for m in recent_metrics if m.is_slow())

        return {
            "total_operations": len(recent_metrics),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "cache_hit_rate": cache_hits / len(recent_metrics) if recent_metrics else 0,
            "error_rate": errors / len(recent_metrics) if recent_metrics else 0,
            "slow_operation_rate": slow_operations / len(recent_metrics) if recent_metrics else 0,
            "recent_alerts": self.alerts[-10:] if self.alerts else [],
        }


# Global instances
_query_cache = LRUCache(max_size=500, ttl_seconds=300)
_hyde_cache = LRUCache(max_size=200, ttl_seconds=600)
_vector_cache = LRUCache(max_size=1000, ttl_seconds=180)
_performance_monitor = PerformanceMonitor()


def cache_query_analysis(func: F) -> F:
    """Decorator to cache query analysis results."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Create cache key from query content
        query = args[1] if args and len(args) > 1 else kwargs.get("query", "")

        cache_key = f"query_analysis:{hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()}"

        # Check cache first
        cached_result = _query_cache.get(cache_key)
        if cached_result:
            return cached_result

        # Execute function and cache result
        result = await func(*args, **kwargs)
        _query_cache.put(cache_key, result)

        return result

    return wrapper  # type: ignore[return-value]


def cache_hyde_processing(func: F) -> F:
    """Decorator to cache HyDE processing results."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Create cache key from query and parameters
        query = args[1] if args and len(args) > 1 else kwargs.get("query", "")

        cache_key = f"hyde_processing:{hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()}"

        # Check cache first
        cached_result = _hyde_cache.get(cache_key)
        if cached_result:
            return cached_result

        # Execute function and cache result
        result = await func(*args, **kwargs)
        _hyde_cache.put(cache_key, result)

        return result

    return wrapper  # type: ignore[return-value]


def cache_vector_search(func: F) -> F:
    """Decorator to cache vector search results."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Create cache key from search parameters
        params = args[1] if args and len(args) > 1 else kwargs.get("parameters")

        if params is not None and hasattr(params, "embeddings") and params.embeddings:
            # Create hash from embeddings and parameters
            embedding_str = str(params.embeddings[0][:10])  # First 10 dimensions
            cache_key = f"vector_search:{hashlib.md5(embedding_str.encode(), usedforsecurity=False).hexdigest()}:{params.limit}:{params.collection}"
        else:
            return await func(*args, **kwargs)

        # Check cache first
        cached_result = _vector_cache.get(cache_key)
        if cached_result:
            return cached_result

        # Execute function and cache result
        result = await func(*args, **kwargs)
        _vector_cache.put(cache_key, result)

        return result

    return wrapper  # type: ignore[return-value]


def monitor_performance(operation_name: str) -> Callable[[F], F]:
    """Decorator to monitor operation performance."""

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            metric = _performance_monitor.start_operation(operation_name)

            try:
                result = await func(*args, **kwargs)
                _performance_monitor.complete_operation(metric, error_occurred=False)
                return result
            except Exception:
                _performance_monitor.complete_operation(metric, error_occurred=True)
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


class AsyncBatcher:
    """Batches async operations for better performance."""

    def __init__(self, batch_size: int = BATCH_SIZE, max_wait_time: float = 0.1) -> None:
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_operations: list[tuple[Callable, tuple, dict]] = []
        self.batch_lock = asyncio.Lock()

    async def add_operation(self, operation: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Add operation to batch."""
        async with self.batch_lock:
            self.pending_operations.append((operation, args, kwargs))

            if len(self.pending_operations) >= self.batch_size:
                return await self._execute_batch()

            # Wait for more operations or timeout
            await asyncio.sleep(self.max_wait_time)

            if self.pending_operations:
                return await self._execute_batch()

        return None

    async def _execute_batch(self) -> list[Any]:
        """Execute batched operations."""
        if not self.pending_operations:
            return []

        operations = self.pending_operations.copy()
        self.pending_operations.clear()

        # Execute all operations concurrently
        tasks = [op(*args, **kwargs) for op, args, kwargs in operations]
        return await asyncio.gather(*tasks, return_exceptions=True)


class ConnectionPool:
    """Connection pool for vector store operations."""

    def __init__(self, max_connections: int = 10) -> None:
        self.max_connections = max_connections
        self.available_connections: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.connection_lock = asyncio.Lock()

    async def acquire_connection(self) -> Any:
        """Acquire a connection from the pool."""
        try:
            # Try to get existing connection
            return self.available_connections.get_nowait()
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            async with self.connection_lock:
                if self.active_connections < self.max_connections:
                    self.active_connections += 1
                    return await self._create_connection()
                # Wait for available connection
                return await self.available_connections.get()

    async def release_connection(self, connection: Any) -> None:
        """Release a connection back to the pool."""
        if connection:
            await self.available_connections.put(connection)

    async def _create_connection(self) -> Any:
        """Create a new connection (placeholder)."""
        # This would create actual connection in real implementation
        return {"connection_id": time.time()}


def get_performance_stats() -> dict[str, Any]:
    """Get comprehensive performance statistics."""
    return {
        "query_cache": _query_cache.get_stats(),
        "hyde_cache": _hyde_cache.get_stats(),
        "vector_cache": _vector_cache.get_stats(),
        "performance_monitor": _performance_monitor.get_performance_summary(),
    }


def clear_all_caches() -> None:
    """Clear all performance caches."""
    _query_cache.clear()
    _hyde_cache.clear()
    _vector_cache.clear()


async def warm_up_system() -> None:
    """Warm up the system for better performance."""
    logger = logging.getLogger(__name__)
    logger.info("Starting system warm-up...")

    # Pre-populate caches with common queries
    common_queries = [
        "How to implement authentication in Python?",
        "Best practices for API design",
        "Database optimization techniques",
        "Error handling strategies",
        "Performance monitoring setup",
    ]

    # This would normally call actual query processing
    # For now, just log the warm-up process
    for query in common_queries:
        cache_key = f"warmup:{hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()}"
        _query_cache.put(cache_key, {"warmed_up": True})

    logger.info("System warm-up completed")


# Performance optimization utilities
class PerformanceOptimizer:
    """Main performance optimization coordinator."""

    def __init__(self) -> None:
        self.connection_pool = ConnectionPool(max_connections=20)
        self.batcher = AsyncBatcher(batch_size=25, max_wait_time=0.05)
        self.logger = logging.getLogger(__name__)

    async def optimize_query_processing(self, query: str) -> dict[str, Any]:
        """Optimize query processing with caching and batching."""
        metric = _performance_monitor.start_operation("optimize_query_processing")

        try:
            # Check cache first
            cache_key = f"optimized_query:{hashlib.md5(query.encode(), usedforsecurity=False).hexdigest()}"
            cached_result = _query_cache.get(cache_key)

            if cached_result:
                _performance_monitor.complete_operation(metric, cache_hit=True)
                return cached_result  # type: ignore[no-any-return]

            # Process query with optimizations
            result = {"query": query, "optimized": True, "cache_miss": True, "timestamp": time.time()}

            # Cache the result
            _query_cache.put(cache_key, result)

            _performance_monitor.complete_operation(metric, cache_hit=False)
            return result

        except Exception:
            _performance_monitor.complete_operation(metric, error_occurred=True)
            raise

    def get_optimization_stats(self) -> dict[str, Any]:
        """Get optimization statistics."""
        return {
            "cache_stats": get_performance_stats(),
            "connection_pool_size": self.connection_pool.active_connections,
            "batcher_pending": len(self.batcher.pending_operations),
        }
