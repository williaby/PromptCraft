# Agent Error Handling Guide

This guide covers exception conventions, external service failure patterns, recovery strategies,
and how errors surface to users through the journey UI for agents built on the PromptCraft agent system.

## Exception Hierarchy

All agent exceptions inherit from `AgentError` in `src/agents/exceptions.py`. Every exception carries
four structured fields: `message`, `error_code`, `context`, and optional `agent_id`/`request_id` for
tracing. Never raise bare `Exception` from within an agent; always raise a typed `AgentError` subclass
so callers can branch on `error_code`.

| Class | Default error code | Typical cause |
| --- | --- | --- |
| `AgentError` | `UNKNOWN_ERROR` | Base class; use a subclass instead |
| `AgentConfigurationError` | `CONFIGURATION_ERROR` | Missing or invalid config at init time |
| `AgentExecutionError` | `EXECUTION_ERROR` | Runtime failure inside `execute()` |
| `AgentTimeoutError` | `EXECUTION_TIMEOUT` | Subclass of execution; timeout exceeded |
| `AgentValidationError` | `VALIDATION_ERROR` | Bad input or output shape |
| `AgentRegistrationError` | `REGISTRATION_ERROR` | Duplicate ID or invalid class at register time |

Use the `create_agent_error(error_type, message, **kwargs)` factory when the error type is determined
at runtime, and `handle_agent_error(exc, agent_id, request_id)` to coerce generic exceptions into
typed `AgentError` instances before re-raising.

## Writing the `execute()` Method

Structure `execute()` with a narrow inner try/except that converts non-agent exceptions and re-raises
`AgentError` subclasses directly:

```python
async def execute(self, agent_input: AgentInput) -> AgentOutput:
    try:
        result = await self._call_external_service(agent_input.content)
        return self._create_output(content=result, request_id=agent_input.request_id)

    except AgentError:
        raise  # Already typed; let it propagate unchanged

    except TimeoutError as exc:
        raise AgentTimeoutError(
            message="External service call timed out",
            timeout=self.config.get("timeout", 30.0),
            agent_id=self.agent_id,
            request_id=agent_input.request_id,
        ) from exc

    except Exception as exc:
        raise AgentExecutionError(
            message=f"Unexpected failure during processing: {exc}",
            error_code="PROCESSING_ERROR",
            context={"error_type": type(exc).__name__},
            agent_id=self.agent_id,
            request_id=agent_input.request_id,
        ) from exc
```

Key rules:

- Re-raise with `from exc` to preserve the original traceback (PEP 3134, Bandit B904).
- Catch `AgentError` first and re-raise before the broad `Exception` catch so typed errors are not
  double-wrapped.
- Log at `ERROR` level inside the exception handler only if no upstream handler will log it; avoid
  double logging.

## Handling External Service Failures

### Qdrant

Qdrant is the external vector database at `192.168.1.16:6333`. Network partitions and collection
mismatches are the most common failure modes.

```python
from src.utils.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError, CircuitBreakerConfig

_qdrant_breaker = CircuitBreaker(
    name="qdrant",
    config=CircuitBreakerConfig(
        failure_threshold=5,
        recovery_timeout=60,
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
    ),
)

async def _search_qdrant(self, query_vector: list[float]) -> list[dict]:
    try:
        return await _qdrant_breaker.call_async(
            self._qdrant_client.search,
            collection_name=self._collection,
            query_vector=query_vector,
            limit=10,
        )
    except CircuitBreakerOpenError:
        self.logger.warning(
            "Qdrant circuit breaker open; returning empty results",
            agent_id=self.agent_id,
        )
        return []  # Degrade gracefully: no results beats a hard failure for search
```

When the circuit is open, agents that perform knowledge retrieval should return a degraded but valid
`AgentOutput` (empty results, reduced confidence) rather than raising. Flag the degradation in output
`metadata` so the journey UI can inform the user.

### Azure AI

Azure AI LLM calls are latency-sensitive. Use `AgentTimeoutError` with the configured timeout so the
UI can show a clear message:

```python
import asyncio
from src.agents.exceptions import AgentTimeoutError, AgentExecutionError

async def _call_azure(self, prompt: str) -> str:
    timeout = self.config.get("timeout", 30.0)
    try:
        return await asyncio.wait_for(
            self._azure_client.complete(prompt),
            timeout=timeout,
        )
    except asyncio.TimeoutError as exc:
        raise AgentTimeoutError(
            timeout=timeout,
            agent_id=self.agent_id,
        ) from exc
    except Exception as exc:
        raise AgentExecutionError(
            message=f"Azure AI call failed: {exc}",
            error_code="LLM_CALL_FAILED",
            context={"model": self.config.get("model"), "error_type": type(exc).__name__},
            agent_id=self.agent_id,
        ) from exc
```

### MCP Servers

MCP servers can go offline between requests. Use the `CompositeResilienceHandler` from
`src/utils/resilience.py` when you need both retry and circuit-breaker protection on the same call:

```python
from src.utils.resilience import CompositeResilienceHandler

handler = CompositeResilienceHandler(strategies=[retry_strategy, breaker_strategy])

async def _call_mcp_tool(self, tool_name: str, params: dict) -> dict:
    return await handler.execute_with_protection(
        self._mcp_client.call_tool,
        fallback_func=self._mcp_fallback,
        tool_name=tool_name,
        params=params,
    )

async def _mcp_fallback(self, tool_name: str, params: dict) -> dict:
    self.logger.warning("MCP tool %s unavailable; using fallback", tool_name)
    return {"result": None, "degraded": True}
```

## Recovery Patterns

### Exponential Backoff with Jitter

`CircuitBreakerConfig` enables jitter by default (`jitter=True`). Jitter randomises delays within
10% of the calculated value, which prevents thundering-herd restarts after a shared outage. Do not
disable jitter in production configuration.

### Fallback Outputs

When an external dependency is unavailable and the agent can still return a partial result, do so.
Set `confidence` low (below 0.5) and include a `degraded` flag in `metadata`:

```python
return AgentOutput(
    agent_id=self.agent_id,
    request_id=agent_input.request_id,
    content="",
    confidence=0.0,
    metadata={"degraded": True, "reason": "qdrant_unavailable"},
)
```

### Health-Check Integration

Register a health-check function with `CircuitBreaker` so the breaker can self-heal without waiting
for a live request to test recovery:

```python
async def _qdrant_health() -> bool:
    try:
        await client.get_collections()
        return True
    except Exception:
        return False

breaker = CircuitBreaker(name="qdrant", health_check_func=_qdrant_health)
await breaker.start_health_monitoring()
```

Call `start_health_monitoring()` in your agent's startup hook and `stop_health_monitoring()` on
shutdown to avoid background task leaks.

## Error Propagation to the Journey UI

The Gradio journey interface receives `AgentOutput` objects. Errors surface via two paths:

1. **Typed `AgentError` raised from `execute()`**: The orchestration layer catches these, logs
   them with `request_id`, and returns a user-facing message derived from `error_code`. Map codes
   to messages in the UI layer rather than exposing raw exception text to users.

2. **Degraded `AgentOutput` with `metadata["degraded"] = True`**: The UI checks this flag and
   appends a service-degraded notice to the rendered response. This is preferred for soft failures
   (knowledge retrieval unavailable) where a partial answer is still useful.

Never let raw exception text reach the Gradio response string. Sanitise in the orchestration layer
before passing to `gr.update()` or equivalent.

## Configuration Reference

Resilience configuration comes from `ApplicationSettings`. The relevant fields and their defaults are:

| Setting | Default | Purpose |
| --- | --- | --- |
| `circuit_breaker_failure_threshold` | 5 | Failures before opening |
| `circuit_breaker_success_threshold` | 3 | Successes to close from half-open |
| `circuit_breaker_recovery_timeout` | 60 | Seconds before testing recovery |
| `circuit_breaker_max_retries` | 3 | Retry attempts per call |
| `circuit_breaker_base_delay` | 1.0 | Base backoff delay (seconds) |
| `circuit_breaker_max_delay` | 60.0 | Maximum backoff delay (seconds) |
| `circuit_breaker_backoff_multiplier` | 2.0 | Exponential multiplier |
| `circuit_breaker_jitter_enabled` | true | Randomise delays |

Pass settings to `create_circuit_breaker_config_from_settings(settings)` in
`src/utils/circuit_breaker.py` to build a `CircuitBreakerConfig` from the application config
rather than hardcoding values.

## Related Documentation

- [Agent Extension Guidelines](./agent_extension_guidelines.md) - Full agent authoring guide
- [Agent Registration Best Practices](./agent_registration_best_practices.md) - Registry patterns
- [Vector Store Integration Guide](./vector-store-integration-guide.md) - Qdrant error patterns
- [Conservative Fallback System](./conservative_fallback_system.md) - Fallback chain and circuit breaker ops
- [MCP Client Usage](./mcp-client-usage.md) - MCP server connection and circuit breaker
