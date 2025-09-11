"""
Prometheus metrics endpoint for PromptCraft-Hybrid.

This module provides HTTP endpoints for Prometheus metrics collection,
integrated with the unified observability system.
"""

from typing import Any


try:
    from fastapi import APIRouter, Depends, HTTPException, Response
    from fastapi.responses import PlainTextResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    APIRouter = HTTPException = Response = Depends = PlainTextResponse = None

try:
    from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    generate_latest = CONTENT_TYPE_LATEST = CollectorRegistry = None

from src.utils.observability_init import get_observability_status
from src.utils.unified_observability import get_logger, get_metrics, get_observability_system


# Create API router
if FASTAPI_AVAILABLE:
    router = APIRouter(prefix="/metrics", tags=["metrics"])
else:
    router = None


def get_prometheus_metrics() -> str:
    """Generate Prometheus metrics in text format."""
    if not PROMETHEUS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Prometheus client not available")

    metrics_collector = get_metrics()
    if not metrics_collector or not metrics_collector.registry:
        raise HTTPException(status_code=503, detail="Metrics collection not enabled")

    try:
        # Generate metrics from our registry
        return generate_latest(metrics_collector.registry).decode("utf-8")
    except Exception as e:
        logger = get_logger(__name__)
        logger.error("Failed to generate Prometheus metrics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {e}")


def get_metrics_summary() -> dict[str, Any]:
    """Get human-readable metrics summary."""
    metrics_collector = get_metrics()
    observability_status = get_observability_status()

    summary = {
        "observability_status": observability_status,
        "metrics_available": metrics_collector is not None,
        "prometheus_available": PROMETHEUS_AVAILABLE,
    }

    if metrics_collector and PROMETHEUS_AVAILABLE:
        try:
            # Get some basic metrics counts
            registry = metrics_collector.registry
            metric_families = list(registry.collect())

            summary.update(
                {
                    "total_metrics": len(metric_families),
                    "metric_families": [
                        {
                            "name": family.name,
                            "type": family.type,
                            "help": family.documentation,
                            "samples_count": len(family.samples) if hasattr(family, "samples") else 0,
                        }
                        for family in metric_families
                    ],
                },
            )

        except Exception as e:
            logger = get_logger(__name__)
            logger.warning("Failed to collect metrics summary", error=str(e))
            summary["error"] = str(e)

    return summary


# FastAPI endpoints (if available)
if FASTAPI_AVAILABLE and router:

    @router.get("/", response_class=PlainTextResponse)
    async def prometheus_metrics_endpoint():
        """
        Prometheus metrics endpoint.

        Returns metrics in Prometheus text format for scraping.
        Compatible with standard Prometheus collectors.

        **Response Format:** Prometheus text format
        **Content-Type:** application/openmetrics-text; version=1.0.0; charset=utf-8
        """
        logger = get_logger(__name__)
        logger.debug("Prometheus metrics endpoint accessed")

        try:
            metrics_text = get_prometheus_metrics()

            # Record the metrics access
            metrics_collector = get_metrics()
            if metrics_collector:
                metrics_collector.record_request("GET", "/metrics", 200, 0.0)

            return Response(
                content=metrics_text,
                media_type=CONTENT_TYPE_LATEST,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"},
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Unexpected error in metrics endpoint", error=str(e))

            # Record the error
            metrics_collector = get_metrics()
            if metrics_collector:
                metrics_collector.record_request("GET", "/metrics", 500, 0.0)
                metrics_collector.record_error("metrics_endpoint_error")

            raise HTTPException(status_code=500, detail="Internal server error")

    @router.get("/summary")
    async def metrics_summary_endpoint():
        """
        Human-readable metrics summary endpoint.

        Returns a JSON summary of available metrics and observability status.
        Useful for debugging and monitoring system health.

        **Response Format:** JSON
        """
        logger = get_logger(__name__)
        logger.debug("Metrics summary endpoint accessed")

        try:
            summary = get_metrics_summary()

            # Record the access
            metrics_collector = get_metrics()
            if metrics_collector:
                metrics_collector.record_request("GET", "/metrics/summary", 200, 0.0)

            return summary

        except Exception as e:
            logger.error("Failed to generate metrics summary", error=str(e))

            # Record the error
            metrics_collector = get_metrics()
            if metrics_collector:
                metrics_collector.record_request("GET", "/metrics/summary", 500, 0.0)
                metrics_collector.record_error("metrics_summary_error")

            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/health")
    async def metrics_health_endpoint():
        """
        Metrics system health check endpoint.

        Returns health status of the metrics collection system.
        Used by monitoring systems to verify metrics availability.

        **Response Format:** JSON
        """
        logger = get_logger(__name__)
        logger.debug("Metrics health endpoint accessed")

        observability_status = get_observability_status()
        metrics_collector = get_metrics()

        health_status = {
            "status": "healthy" if observability_status.get("initialized") and metrics_collector else "unhealthy",
            "observability_initialized": observability_status.get("initialized", False),
            "metrics_enabled": observability_status.get("metrics_enabled", False),
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "collector_available": metrics_collector is not None,
            "timestamp": str(
                get_observability_system().config.environment if get_observability_system() else "unknown",
            ),
        }

        status_code = 200 if health_status["status"] == "healthy" else 503

        # Record the health check
        if metrics_collector:
            metrics_collector.record_request("GET", "/metrics/health", status_code, 0.0)

        if status_code != 200:
            raise HTTPException(status_code=status_code, detail=health_status)

        return health_status


# Flask integration (if needed)
def create_flask_metrics_blueprint():
    """Create Flask blueprint for metrics endpoints."""
    try:
        from flask import Blueprint, Response, jsonify
    except ImportError:
        return None

    blueprint = Blueprint("metrics", __name__, url_prefix="/metrics")

    @blueprint.route("/")
    def prometheus_metrics():
        """Prometheus metrics endpoint for Flask."""
        try:
            metrics_text = get_prometheus_metrics()
            return Response(
                metrics_text,
                mimetype=CONTENT_TYPE_LATEST,
                headers={"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"},
            )
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @blueprint.route("/summary")
    def metrics_summary():
        """Metrics summary endpoint for Flask."""
        try:
            return jsonify(get_metrics_summary())
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @blueprint.route("/health")
    def metrics_health():
        """Metrics health endpoint for Flask."""
        try:
            observability_status = get_observability_status()
            metrics_collector = get_metrics()

            health_status = {
                "status": "healthy" if observability_status.get("initialized") and metrics_collector else "unhealthy",
                "observability_initialized": observability_status.get("initialized", False),
                "metrics_enabled": observability_status.get("metrics_enabled", False),
                "prometheus_available": PROMETHEUS_AVAILABLE,
                "collector_available": metrics_collector is not None,
            }

            status_code = 200 if health_status["status"] == "healthy" else 503
            return jsonify(health_status), status_code

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return blueprint


# Standalone WSGI application for metrics only
def create_metrics_wsgi_app():
    """Create standalone WSGI app for metrics collection."""
    try:
        from flask import Flask

        app = Flask(__name__)

        blueprint = create_flask_metrics_blueprint()
        if blueprint:
            app.register_blueprint(blueprint)

        return app

    except ImportError:
        return None


# Direct function access for custom integrations
def get_metrics_text() -> str:
    """Get Prometheus metrics as text - for custom integrations."""
    return get_prometheus_metrics()


def get_metrics_dict() -> dict[str, Any]:
    """Get metrics summary as dictionary - for custom integrations."""
    return get_metrics_summary()


# Export the router for FastAPI integration
__all__ = [
    "create_flask_metrics_blueprint",
    "create_metrics_wsgi_app",
    "get_metrics_dict",
    "get_metrics_summary",
    "get_metrics_text",
    "get_prometheus_metrics",
    "router",
]
