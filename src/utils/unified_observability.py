"""
Unified observability system for PromptCraft-Hybrid.

This module consolidates all logging, metrics, and tracing into a single,
consistent observability framework using structlog as the foundation.
It provides backward compatibility with standard logging while enabling
structured JSON output for production monitoring.

Key Features:
- Single configuration point for all observability
- Structured JSON logging with correlation IDs
- Automatic metrics collection and Prometheus integration
- OpenTelemetry tracing support
- Backward compatibility with existing logging.getLogger() calls
- Request/response correlation
- Security event tracking
- Performance monitoring
"""

from collections.abc import Callable
from contextlib import contextmanager
from enum import Enum
from functools import wraps
import logging
import logging.config
import os
import sys
import threading
import time
from typing import Any

import structlog
from structlog.stdlib import LoggerFactory


# Optional imports with graceful degradation
try:
    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.trace import Status, StatusCode

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    trace = None

try:
    from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    Counter = Histogram = Gauge = CollectorRegistry = None

try:
    from fastapi import Request

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    Request = None


class LogLevel(Enum):
    """Unified log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ObservabilityConfig:
    """Configuration for unified observability system."""

    def __init__(
        self,
        environment: str = "development",
        service_name: str = "promptcraft-hybrid",
        service_version: str = "0.1.0",
        structured_logging: bool = True,
        json_logs: bool = True,
        correlation_ids: bool = True,
        tracing_enabled: bool = True,
        metrics_enabled: bool = True,
        jaeger_endpoint: str | None = None,
        log_level: LogLevel = LogLevel.INFO,
        max_log_size_mb: int = 100,
        backup_count: int = 5,
    ):
        """Initialize observability configuration."""
        self.environment = environment
        self.service_name = service_name
        self.service_version = service_version
        self.structured_logging = structured_logging
        self.json_logs = json_logs
        self.correlation_ids = correlation_ids
        self.tracing_enabled = tracing_enabled and OPENTELEMETRY_AVAILABLE
        self.metrics_enabled = metrics_enabled and PROMETHEUS_AVAILABLE
        self.jaeger_endpoint = jaeger_endpoint
        self.log_level = log_level
        self.max_log_size_mb = max_log_size_mb
        self.backup_count = backup_count


class CorrelationContext:
    """Thread-local correlation context for request tracing."""

    def __init__(self):
        """Initialize correlation context."""
        self._local = threading.local()

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID for current thread."""
        self._local.correlation_id = correlation_id

    def get_correlation_id(self) -> str | None:
        """Get correlation ID for current thread."""
        return getattr(self._local, "correlation_id", None)

    def set_request_id(self, request_id: str) -> None:
        """Set request ID for current thread."""
        self._local.request_id = request_id

    def get_request_id(self) -> str | None:
        """Get request ID for current thread."""
        return getattr(self._local, "request_id", None)

    def set_user_id(self, user_id: str) -> None:
        """Set user ID for current thread."""
        self._local.user_id = user_id

    def get_user_id(self) -> str | None:
        """Get user ID for current thread."""
        return getattr(self._local, "user_id", None)

    def clear(self) -> None:
        """Clear all correlation data."""
        for attr in ["correlation_id", "request_id", "user_id"]:
            setattr(self._local, attr, None)


# Global correlation context
correlation_context = CorrelationContext()


class MetricsCollector:
    """Prometheus metrics collector for application observability."""

    def __init__(self, registry: CollectorRegistry | None = None):
        """Initialize metrics collector."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.registry = registry or CollectorRegistry()
        self._initialize_metrics()

    def _initialize_metrics(self) -> None:
        """Initialize standard metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        # Request metrics
        self.request_count = Counter(
            "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"], registry=self.registry,
        )

        self.request_duration = Histogram(
            "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"], registry=self.registry,
        )

        # Application metrics
        self.active_connections = Gauge("active_connections", "Active connections", registry=self.registry)

        # Error metrics
        self.error_count = Counter(
            "application_errors_total", "Total application errors", ["error_type", "severity"], registry=self.registry,
        )

        # Security metrics
        self.security_events = Counter(
            "security_events_total", "Security events", ["event_type", "severity"], registry=self.registry,
        )

    def record_request(self, method: str, endpoint: str, status_code: int, duration: float) -> None:
        """Record HTTP request metrics."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.request_count.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

    def record_error(self, error_type: str, severity: str = "error") -> None:
        """Record application error."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.error_count.labels(error_type=error_type, severity=severity).inc()

    def record_security_event(self, event_type: str, severity: str = "info") -> None:
        """Record security event."""
        if not PROMETHEUS_AVAILABLE:
            return

        self.security_events.labels(event_type=event_type, severity=severity).inc()


class UnifiedLogger:
    """Unified logger that consolidates all logging approaches."""

    def __init__(self, name: str, config: ObservabilityConfig):
        """Initialize unified logger."""
        self.name = name
        self.config = config
        self.correlation_context = correlation_context

        # Create structlog logger
        if config.structured_logging:
            self.logger = structlog.get_logger(name)
        else:
            self.logger = logging.getLogger(name)

    def _enrich_event(self, event_dict: dict[str, Any]) -> dict[str, Any]:
        """Enrich log event with correlation data."""
        # Add correlation information
        if self.correlation_context.get_correlation_id():
            event_dict["correlation_id"] = self.correlation_context.get_correlation_id()

        if self.correlation_context.get_request_id():
            event_dict["request_id"] = self.correlation_context.get_request_id()

        if self.correlation_context.get_user_id():
            event_dict["user_id"] = self.correlation_context.get_user_id()

        # Add service metadata
        event_dict["service"] = self.config.service_name
        event_dict["version"] = self.config.service_version
        event_dict["environment"] = self.config.environment

        return event_dict

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        if self.config.structured_logging:
            self.logger.debug(message, **self._enrich_event(kwargs))
        else:
            self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        if self.config.structured_logging:
            self.logger.info(message, **self._enrich_event(kwargs))
        else:
            self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        if self.config.structured_logging:
            self.logger.warning(message, **self._enrich_event(kwargs))
        else:
            self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        if self.config.structured_logging:
            self.logger.error(message, **self._enrich_event(kwargs))
        else:
            self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        if self.config.structured_logging:
            self.logger.critical(message, **self._enrich_event(kwargs))
        else:
            self.logger.critical(message, extra=kwargs)

    def exception(self, message: str, **kwargs) -> None:
        """Log exception with traceback."""
        if self.config.structured_logging:
            self.logger.exception(message, **self._enrich_event(kwargs))
        else:
            self.logger.exception(message, extra=kwargs)


class ObservabilitySystem:
    """Central observability system managing logging, metrics, and tracing."""

    def __init__(self, config: ObservabilityConfig):
        """Initialize observability system."""
        self.config = config
        self.metrics_collector: MetricsCollector | None = None
        self.tracer = None
        self._configured = False

        # Configure on initialization
        self.configure()

    def configure(self) -> None:
        """Configure all observability components."""
        if self._configured:
            return

        self._configure_logging()
        self._configure_metrics()
        self._configure_tracing()

        self._configured = True

    def _configure_logging(self) -> None:
        """Configure structured logging."""
        if self.config.structured_logging:
            # Configure structlog
            processors = [
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
            ]

            if self.config.json_logs:
                processors.append(structlog.processors.JSONRenderer())
            else:
                processors.append(structlog.dev.ConsoleRenderer())

            structlog.configure(
                processors=processors,
                context_class=dict,
                logger_factory=LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )

        # Configure standard logging to be compatible
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.value),
            format=(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s" if not self.config.json_logs else "%(message)s"
            ),
        )

    def _configure_metrics(self) -> None:
        """Configure Prometheus metrics."""
        if self.config.metrics_enabled and PROMETHEUS_AVAILABLE:
            self.metrics_collector = MetricsCollector()

    def _configure_tracing(self) -> None:
        """Configure OpenTelemetry tracing."""
        if self.config.tracing_enabled and OPENTELEMETRY_AVAILABLE:
            resource = Resource(
                attributes={
                    "service.name": self.config.service_name,
                    "service.version": self.config.service_version,
                    "environment": self.config.environment,
                },
            )

            provider = TracerProvider(resource=resource)

            if self.config.jaeger_endpoint:
                jaeger_exporter = JaegerExporter(
                    agent_host_name="localhost",
                    agent_port=6831,
                )
                span_processor = BatchSpanProcessor(jaeger_exporter)
                provider.add_span_processor(span_processor)

            trace.set_tracer_provider(provider)
            self.tracer = trace.get_tracer(__name__)

    def get_logger(self, name: str) -> UnifiedLogger:
        """Get a unified logger instance."""
        return UnifiedLogger(name, self.config)

    def get_metrics(self) -> MetricsCollector | None:
        """Get metrics collector."""
        return self.metrics_collector

    @contextmanager
    def trace_span(self, name: str, **attributes):
        """Create a tracing span context manager."""
        if not self.tracer:
            yield None
            return

        with self.tracer.start_as_current_span(name) as span:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))

            try:
                yield span
            except Exception as e:
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise

    @contextmanager
    def correlation_context(self, correlation_id: str = None, request_id: str = None, user_id: str = None):
        """Set correlation context for current thread."""
        old_correlation = correlation_context.get_correlation_id()
        old_request = correlation_context.get_request_id()
        old_user = correlation_context.get_user_id()

        try:
            if correlation_id:
                correlation_context.set_correlation_id(correlation_id)
            if request_id:
                correlation_context.set_request_id(request_id)
            if user_id:
                correlation_context.set_user_id(user_id)

            yield
        finally:
            # Restore previous context
            correlation_context.set_correlation_id(old_correlation)
            correlation_context.set_request_id(old_request)
            correlation_context.set_user_id(old_user)


# Global observability system instance
_observability_system: ObservabilitySystem | None = None


def configure_observability(config: ObservabilityConfig | None = None) -> ObservabilitySystem:
    """Configure global observability system."""
    global _observability_system

    if config is None:
        # Auto-configure based on environment
        environment = os.getenv("PROMPTCRAFT_ENVIRONMENT", "development")
        service_name = os.getenv("SERVICE_NAME", "promptcraft-hybrid")
        service_version = os.getenv("SERVICE_VERSION", "0.1.0")

        config = ObservabilityConfig(
            environment=environment,
            service_name=service_name,
            service_version=service_version,
            structured_logging=environment in ("staging", "prod"),
            json_logs=environment in ("staging", "prod"),
            tracing_enabled=environment in ("staging", "prod"),
            jaeger_endpoint=os.getenv("JAEGER_ENDPOINT"),
            log_level=LogLevel(os.getenv("LOG_LEVEL", "INFO")),
        )

    _observability_system = ObservabilitySystem(config)
    return _observability_system


def get_logger(name: str = __name__) -> UnifiedLogger:
    """Get a unified logger instance - backward compatible with logging.getLogger()."""
    if _observability_system is None:
        configure_observability()

    return _observability_system.get_logger(name)


def get_metrics() -> MetricsCollector | None:
    """Get the global metrics collector."""
    if _observability_system is None:
        configure_observability()

    return _observability_system.get_metrics()


def get_observability_system() -> ObservabilitySystem:
    """Get the global observability system."""
    if _observability_system is None:
        configure_observability()

    return _observability_system


# Convenience decorators for common observability patterns
def observe_performance(operation_name: str = None):
    """Decorator to observe function performance."""

    def decorator(func: Callable) -> Callable:
        name = operation_name or f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            metrics = get_metrics()
            system = get_observability_system()

            start_time = time.time()

            with system.trace_span(name, function=func.__name__):
                try:
                    logger.debug(f"Starting {name}", operation=name, args_count=len(args))
                    result = func(*args, **kwargs)

                    duration = time.time() - start_time
                    logger.info(f"Completed {name}", operation=name, duration=duration, success=True)

                    if metrics:
                        metrics.request_duration.labels(method="function", endpoint=name).observe(duration)

                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    logger.error(f"Failed {name}", operation=name, duration=duration, error=str(e), success=False)

                    if metrics:
                        metrics.record_error(error_type=type(e).__name__)

                    raise

        return wrapper

    return decorator


def log_security_event(event_type: str, severity: str = "info", **details):
    """Log a security event with metrics."""
    logger = get_logger("security")
    metrics = get_metrics()

    logger.info(f"Security event: {event_type}", event_type=event_type, severity=severity, **details)

    if metrics:
        metrics.record_security_event(event_type, severity)


# Compatibility layer for existing logging calls
class CompatibilityHandler(logging.Handler):
    """Handler that redirects standard logging to unified system."""

    def emit(self, record):
        """Emit log record through unified system."""
        try:
            logger = get_logger(record.name)

            # Map logging levels to our methods
            level_method = {
                logging.DEBUG: logger.debug,
                logging.INFO: logger.info,
                logging.WARNING: logger.warning,
                logging.ERROR: logger.error,
                logging.CRITICAL: logger.critical,
            }.get(record.levelno, logger.info)

            # Extract extra data
            extra = {}
            for key, value in record.__dict__.items():
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "getMessage",
                    "stack_info",
                ]:
                    extra[key] = value

            level_method(record.getMessage(), **extra)

        except Exception:
            # Fallback to prevent logging errors from breaking the application
            self.handleError(record)


def install_compatibility_handler():
    """Install compatibility handler for existing logging calls."""
    handler = CompatibilityHandler()

    # Install on root logger to catch all logging calls
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    # Also install on common logger names used in the codebase
    for logger_name in ["src", "promptcraft", __package__ or "main"]:
        logger = logging.getLogger(logger_name)
        logger.addHandler(handler)


# Initialize compatibility layer on import
try:
    # Only install if we're not in a test environment
    if "pytest" not in sys.modules:
        install_compatibility_handler()
except Exception:
    # Ignore errors during compatibility installation
    pass
