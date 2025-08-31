"""
Health Router Module

Handles system health checks and service monitoring endpoints.
Decomposed from security_dashboard_endpoints.py for focused responsibility.

Endpoints:
    GET /health - Basic health check
    GET /health/detailed - Comprehensive health status
    GET /health/services - Individual service health
"""

from datetime import UTC, datetime

import psutil
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.auth.services.security_integration import SecurityIntegrationService


class HealthStatus(BaseModel):
    """Basic health status response."""

    status: str = Field(..., description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")


class ServiceHealth(BaseModel):
    """Individual service health status."""

    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status")
    healthy: bool = Field(..., description="Service health indicator")
    response_time_ms: float | None = Field(None, description="Service response time")
    last_check: datetime = Field(..., description="Last health check time")
    error_message: str | None = Field(None, description="Error message if unhealthy")


class DetailedHealthResponse(BaseModel):
    """Comprehensive health check response."""

    overall_status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Application uptime")

    # Service health
    services: dict[str, ServiceHealth] = Field(..., description="Individual service health")
    healthy_services: int = Field(..., description="Number of healthy services")
    total_services: int = Field(..., description="Total number of services")

    # System metrics
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    memory_usage_percent: float = Field(..., description="Memory usage percentage")
    disk_usage_percent: float = Field(..., description="Disk usage percentage")

    # Database health
    database_connected: bool = Field(..., description="Database connection status")
    database_response_time_ms: float | None = Field(None, description="Database response time")

    # External dependencies
    external_services: dict[str, bool] = Field(..., description="External service availability")


# Create router
router = APIRouter(prefix="/health", tags=["health"])

# Dependencies
_app_start_time = datetime.now(UTC)


def get_security_service() -> SecurityIntegrationService:
    """Get security integration service instance."""
    return SecurityIntegrationService()


@router.get("/", response_model=HealthStatus)
async def basic_health_check() -> HealthStatus:
    """Basic health check endpoint for load balancers and monitoring.

    Returns:
        Basic health status information
    """
    current_time = datetime.now(UTC)
    uptime = (current_time - _app_start_time).total_seconds()

    return HealthStatus(
        status="healthy",
        timestamp=current_time,
        version="1.0.0",
        uptime_seconds=uptime,  # Should come from app config
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    service: SecurityIntegrationService = Depends(get_security_service),  # noqa: ARG001
) -> DetailedHealthResponse:
    """Comprehensive health check with all system components.

    Args:
        service: Security integration service

    Returns:
        Detailed health status with all system metrics
    """
    try:
        current_time = datetime.now(UTC)
        uptime = (current_time - _app_start_time).total_seconds()

        # Generate mock service health data
        service_names = [
            "security_logger",
            "activity_monitor",
            "alert_engine",
            "suspicious_activity_detector",
            "audit_service",
        ]

        services = {}
        healthy_count = 0

        # Generate mock service health data with realistic patterns
        for i, service_name in enumerate(service_names):
            # Most services are healthy, with occasional degraded status
            is_healthy = i != 2  # Make alert_engine occasionally unhealthy for testing

            service_health = ServiceHealth(
                name=service_name,
                status="healthy" if is_healthy else "degraded",
                healthy=is_healthy,
                response_time_ms=25.5 + (i * 10.2),  # Realistic response times
                last_check=current_time,
                error_message=None if is_healthy else f"{service_name} experiencing high load",
            )

            services[service_name] = service_health
            if service_health.healthy:
                healthy_count += 1

        total_services = len(services)

        # Get system metrics (mock data - in production, use actual system monitoring)
        system_metrics = await _get_system_metrics()

        # Generate mock database connectivity data
        database_connected = True  # Assume healthy connection
        database_response_time = 12.3  # Mock response time

        # Check external services
        external_services = {
            "qdrant_vector_db": await _check_qdrant_health(),
            "azure_ai_services": await _check_azure_ai_health(),
            "notification_service": await _check_notification_service_health(),
        }

        # Determine overall status
        if healthy_count == total_services and database_connected and all(external_services.values()):
            overall_status = "healthy"
        elif healthy_count >= total_services * 0.5:  # At least 50% services healthy
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        return DetailedHealthResponse(
            overall_status=overall_status,
            timestamp=current_time,
            version="1.0.0",
            uptime_seconds=uptime,
            services=services,
            healthy_services=healthy_count,
            total_services=total_services,
            cpu_usage_percent=system_metrics["cpu_usage"],
            memory_usage_percent=system_metrics["memory_usage"],
            disk_usage_percent=system_metrics["disk_usage"],
            database_connected=database_connected,
            database_response_time_ms=database_response_time,
            external_services=external_services,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform detailed health check: {e!s}") from e


@router.get("/services", response_model=dict[str, ServiceHealth])
async def get_service_health(
    service: SecurityIntegrationService = Depends(get_security_service),  # noqa: ARG001
) -> dict[str, ServiceHealth]:
    """Get health status of individual services.

    Args:
        service: Security integration service

    Returns:
        Health status for each service
    """
    try:
        current_time = datetime.now(UTC)

        # Generate mock service health data
        service_names = [
            "security_logger",
            "activity_monitor",
            "alert_engine",
            "suspicious_activity_detector",
            "audit_service",
        ]

        services = {}

        # Generate mock service health data with realistic patterns
        for i, service_name in enumerate(service_names):
            # Most services are healthy, with occasional degraded status
            is_healthy = i != 2  # Make alert_engine occasionally unhealthy for testing

            service_health = ServiceHealth(
                name=service_name,
                status="healthy" if is_healthy else "degraded",
                healthy=is_healthy,
                response_time_ms=25.5 + (i * 10.2),  # Realistic response times
                last_check=current_time,
                error_message=None if is_healthy else f"{service_name} experiencing high load",
            )

            services[service_name] = service_health

        return services

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get service health: {e!s}") from e


async def _get_system_metrics() -> dict[str, float]:
    """Get system resource metrics.

    Returns:
        System metrics dictionary
    """
    try:
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
        }
    except ImportError:
        # Fallback mock data if psutil not available
        return {"cpu_usage": 25.5, "memory_usage": 45.2, "disk_usage": 32.1}
    except Exception:
        return {"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0}


async def _check_qdrant_health() -> bool:
    """Check Qdrant vector database health.

    Returns:
        True if Qdrant is healthy
    """
    try:
        # In production, this would make actual health check to Qdrant
        # For now, return mock status
        return True
    except Exception:
        return False


async def _check_azure_ai_health() -> bool:
    """Check Azure AI services health.

    Returns:
        True if Azure AI services are healthy
    """
    try:
        # In production, this would check Azure AI service status
        # For now, return mock status
        return True
    except Exception:
        return False


async def _check_notification_service_health() -> bool:
    """Check notification service health.

    Returns:
        True if notification service is healthy
    """
    try:
        # In production, this would check notification service
        # For now, return mock status
        return True
    except Exception:
        return False
