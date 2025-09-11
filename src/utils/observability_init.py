"""
Initialize observability system at application startup.

This module ensures that the unified observability system is properly
configured when the application starts, providing consistent logging,
metrics, and tracing across all components.
"""

import os
import sys

from src.utils.unified_observability import (
    LogLevel,
    ObservabilityConfig,
    configure_observability,
    install_compatibility_handler,
)


def initialize_observability() -> None:
    """Initialize the observability system with environment-appropriate configuration."""

    # Determine environment
    environment = os.getenv("PROMPTCRAFT_ENVIRONMENT", "development")

    # Service metadata
    service_name = os.getenv("SERVICE_NAME", "promptcraft-hybrid")
    service_version = os.getenv("SERVICE_VERSION", "0.1.0")

    # Logging configuration
    log_level_str = os.getenv("LOG_LEVEL", "INFO" if environment != "development" else "DEBUG")
    try:
        log_level = LogLevel(log_level_str.upper())
    except ValueError:
        log_level = LogLevel.INFO

    # Structured logging and JSON output for production environments
    structured_logging = environment in ("staging", "prod") or os.getenv("STRUCTURED_LOGGING", "").lower() == "true"
    json_logs = environment in ("staging", "prod") or os.getenv("JSON_LOGS", "").lower() == "true"

    # Correlation IDs for request tracking
    correlation_ids = os.getenv("CORRELATION_IDS", "true").lower() == "true"

    # Tracing configuration
    tracing_enabled = environment in ("staging", "prod") or os.getenv("TRACING_ENABLED", "").lower() == "true"
    jaeger_endpoint = os.getenv("JAEGER_ENDPOINT")

    # Metrics configuration
    metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"

    # File logging configuration
    max_log_size_mb = int(os.getenv("MAX_LOG_SIZE_MB", "100"))
    backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

    # Create configuration
    config = ObservabilityConfig(
        environment=environment,
        service_name=service_name,
        service_version=service_version,
        structured_logging=structured_logging,
        json_logs=json_logs,
        correlation_ids=correlation_ids,
        tracing_enabled=tracing_enabled,
        metrics_enabled=metrics_enabled,
        jaeger_endpoint=jaeger_endpoint,
        log_level=log_level,
        max_log_size_mb=max_log_size_mb,
        backup_count=backup_count,
    )

    # Configure the global observability system
    system = configure_observability(config)

    # Install compatibility layer for existing logging calls
    install_compatibility_handler()

    # Log initialization success
    logger = system.get_logger(__name__)
    logger.info(
        "Observability system initialized",
        environment=environment,
        service_name=service_name,
        service_version=service_version,
        structured_logging=structured_logging,
        json_logs=json_logs,
        tracing_enabled=tracing_enabled,
        metrics_enabled=metrics_enabled,
        log_level=log_level.value,
    )

    return system


def get_observability_status() -> dict:
    """Get current observability system status."""
    from src.utils.unified_observability import OPENTELEMETRY_AVAILABLE, PROMETHEUS_AVAILABLE, _observability_system

    if _observability_system is None:
        return {"initialized": False, "error": "Observability system not initialized"}

    config = _observability_system.config

    return {
        "initialized": True,
        "environment": config.environment,
        "service_name": config.service_name,
        "service_version": config.service_version,
        "structured_logging": config.structured_logging,
        "json_logs": config.json_logs,
        "correlation_ids": config.correlation_ids,
        "tracing_enabled": config.tracing_enabled,
        "metrics_enabled": config.metrics_enabled,
        "log_level": config.log_level.value,
        "opentelemetry_available": OPENTELEMETRY_AVAILABLE,
        "prometheus_available": PROMETHEUS_AVAILABLE,
    }


# Auto-initialize if this module is imported and we're not in test mode
if __name__ != "__main__" and "pytest" not in sys.modules:
    try:
        initialize_observability()
    except Exception as e:
        # Fallback to basic logging if initialization fails
        import logging

        logging.basicConfig(level=logging.INFO)
        logging.getLogger(__name__).error(f"Failed to initialize observability system: {e}")


if __name__ == "__main__":
    # Command-line tool for testing observability initialization
    import json

    print("Initializing observability system...")
    system = initialize_observability()

    print("\nObservability system status:")
    status = get_observability_status()
    print(json.dumps(status, indent=2))

    print("\nTesting unified logger...")
    logger = system.get_logger("test")
    logger.info("Test info message", test_key="test_value", number=42)
    logger.warning("Test warning message", warning_type="test")
    logger.error("Test error message", error_code="TEST_ERROR")

    print("\nObservability system test completed successfully!")
