"""FastAPI integration for AUTH-4 dependency injection system.

This module provides seamless integration between the AUTH-4 service container
and FastAPI's dependency injection system, enabling clean service resolution
in API endpoints.

Features:
- Automatic service resolution for FastAPI endpoints
- Request-scoped and singleton service management
- Health check endpoints for service monitoring
- Service metrics and status endpoints
- Error handling and graceful fallbacks
- Startup and shutdown lifecycle management

Performance target: < 1ms service resolution per request
Architecture: FastAPI Depends() integration with service container resolution
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional, Type, TypeVar

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.auth.database.security_events_postgres import SecurityEventsPostgreSQL
from src.auth.services.alert_engine import AlertEngine
from src.auth.services.audit_service import AuditService
from src.auth.services.bootstrap import (
    ServiceBootstrapError,
    bootstrap_services_async,
    get_container_for_environment,
)
from src.auth.services.container import ServiceContainer, ServiceResolutionError
from src.auth.services.security_logger import SecurityLogger
from src.auth.services.security_monitor import SecurityMonitor
from src.auth.services.suspicious_activity_detector import SuspiciousActivityDetector

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Global container instance for FastAPI integration
_app_container: Optional[ServiceContainer] = None


class ServiceHealthResponse(BaseModel):
    """Response model for service health checks."""
    
    service_name: str
    status: str
    healthy: bool
    error_message: Optional[str] = None
    last_check: Optional[str] = None


class ContainerMetricsResponse(BaseModel):
    """Response model for container metrics."""
    
    services: Dict[str, Any]
    performance: Dict[str, Any]
    health: Dict[str, Any]
    configuration: Dict[str, Any]


class ServiceIntegrationError(Exception):
    """Exception raised when FastAPI service integration fails."""
    pass


async def setup_service_container(
    app: FastAPI,
    environment: str = "development",
    auto_initialize: bool = True,
) -> ServiceContainer:
    """Setup service container for FastAPI application.
    
    Args:
        app: FastAPI application instance
        environment: Environment name (development, test, production)
        auto_initialize: Whether to automatically initialize services
        
    Returns:
        Configured and initialized service container
        
    Raises:
        ServiceIntegrationError: If setup fails
    """
    global _app_container
    
    try:
        logger.info(f"Setting up service container for FastAPI app in {environment} environment")
        
        if auto_initialize:
            # Bootstrap services automatically
            container = await bootstrap_services_async(environment)
        else:
            # Just create container without initialization
            container = get_container_for_environment(environment)
        
        # Store container globally for dependency resolution
        _app_container = container
        
        # Store container in app state for access in endpoints
        app.state.service_container = container
        
        # Add health check endpoints
        add_health_check_routes(app)
        
        logger.info("Service container setup completed successfully")
        return container
        
    except Exception as e:
        logger.error(f"Failed to setup service container: {e}")
        raise ServiceIntegrationError(f"Container setup failed: {e}") from e


def get_service_container() -> ServiceContainer:
    """Get the global service container instance.
    
    Returns:
        Global service container
        
    Raises:
        ServiceIntegrationError: If container is not initialized
    """
    if _app_container is None:
        raise ServiceIntegrationError(
            "Service container not initialized. Call setup_service_container() first."
        )
    return _app_container


def create_service_dependency(service_type: Type[T]) -> T:
    """Create a FastAPI dependency function for resolving services.
    
    Args:
        service_type: Type of service to resolve
        
    Returns:
        Dependency function for FastAPI Depends()
        
    Example:
        @app.get("/api/monitor")
        async def get_monitor_status(
            monitor: SecurityMonitor = Depends(create_service_dependency(SecurityMonitor))
        ):
            return await monitor.get_monitoring_stats()
    """
    def dependency() -> T:
        try:
            container = get_service_container()
            return container.resolve(service_type)
        except ServiceResolutionError as e:
            logger.error(f"Failed to resolve service {service_type.__name__}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Service resolution failed: {service_type.__name__}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error resolving service {service_type.__name__}: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal service error"
            ) from e
    
    return dependency


# Pre-configured dependency functions for common services
def get_security_logger() -> SecurityLogger:
    """Get SecurityLogger instance via dependency injection."""
    return create_service_dependency(SecurityLogger)()


def get_security_monitor() -> SecurityMonitor:
    """Get SecurityMonitor instance via dependency injection."""
    return create_service_dependency(SecurityMonitor)()


def get_alert_engine() -> AlertEngine:
    """Get AlertEngine instance via dependency injection."""
    return create_service_dependency(AlertEngine)()


def get_audit_service() -> AuditService:
    """Get AuditService instance via dependency injection."""
    return create_service_dependency(AuditService)()


def get_suspicious_activity_detector() -> SuspiciousActivityDetector:
    """Get SuspiciousActivityDetector instance via dependency injection."""
    return create_service_dependency(SuspiciousActivityDetector)()


def get_database() -> SecurityEventsPostgreSQL:
    """Get SecurityEventsPostgreSQL instance via dependency injection."""
    return create_service_dependency(SecurityEventsPostgreSQL)()


def add_health_check_routes(app: FastAPI) -> None:
    """Add health check and monitoring routes to FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get("/health/container", response_model=ContainerMetricsResponse)
    async def get_container_metrics():
        """Get service container health and performance metrics."""
        try:
            container = get_service_container()
            metrics = container.get_container_metrics()
            return ContainerMetricsResponse(**metrics)
        except Exception as e:
            logger.error(f"Failed to get container metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to get container metrics")
    
    @app.get("/health/services")
    async def get_service_health():
        """Get health status of all registered services."""
        try:
            container = get_service_container()
            health_status = {}
            
            # Check health of all registered services
            for service_type in container._registrations.keys():
                try:
                    service_status = container.get_service_status(service_type)
                    health_status[service_type.__name__] = {
                        "status": service_status.value,
                        "healthy": service_status.value == "ready",
                    }
                    
                    # Get additional details from instance if available
                    if service_type in container._instances:
                        instance = container._instances[service_type]
                        health_status[service_type.__name__].update({
                            "error_count": instance.error_count,
                            "last_error": instance.last_error,
                            "created_at": instance.created_at.isoformat(),
                        })
                        
                except Exception as e:
                    health_status[service_type.__name__] = {
                        "status": "error", 
                        "healthy": False,
                        "error": str(e),
                    }
            
            return {"services": health_status}
            
        except Exception as e:
            logger.error(f"Failed to get service health: {e}")
            raise HTTPException(status_code=500, detail="Failed to get service health")
    
    @app.get("/health/service/{service_name}")
    async def get_individual_service_health(service_name: str):
        """Get health status of a specific service."""
        try:
            container = get_service_container()
            
            # Find service type by name
            service_type = None
            for svc_type in container._registrations.keys():
                if svc_type.__name__.lower() == service_name.lower():
                    service_type = svc_type
                    break
            
            if not service_type:
                raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
            
            status = container.get_service_status(service_type)
            response = ServiceHealthResponse(
                service_name=service_type.__name__,
                status=status.value,
                healthy=status.value == "ready",
            )
            
            # Add instance details if available
            if service_type in container._instances:
                instance = container._instances[service_type]
                response.error_message = instance.last_error
                response.last_check = instance.last_health_check.isoformat() if instance.last_health_check else None
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get service health for {service_name}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get service health")


@asynccontextmanager
async def service_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Context manager for FastAPI lifespan events with service container management.
    
    This function handles startup and shutdown of the service container,
    ensuring proper initialization and cleanup.
    
    Args:
        app: FastAPI application instance
        
    Example:
        app = FastAPI(lifespan=service_lifespan)
    """
    # Startup
    logger.info("Starting AUTH-4 services...")
    
    try:
        # Get environment from app settings or default to development
        environment = getattr(app.state, "environment", "development")
        
        # Setup service container
        await setup_service_container(app, environment=environment, auto_initialize=True)
        
        logger.info("AUTH-4 services started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start AUTH-4 services: {e}")
        raise ServiceIntegrationError(f"Service startup failed: {e}") from e
    
    # Yield control to the application
    yield
    
    # Shutdown
    logger.info("Shutting down AUTH-4 services...")
    
    try:
        container = get_service_container()
        await container.shutdown()
        
        # Reset global container
        global _app_container
        _app_container = None
        
        logger.info("AUTH-4 services shut down successfully")
        
    except Exception as e:
        logger.error(f"Error during service shutdown: {e}")


def create_fastapi_app(
    environment: str = "development",
    enable_health_checks: bool = True,
    **fastapi_kwargs: Any,
) -> FastAPI:
    """Create a FastAPI application with AUTH-4 services pre-configured.
    
    Args:
        environment: Environment name (development, test, production)
        enable_health_checks: Whether to add health check endpoints
        **fastapi_kwargs: Additional arguments passed to FastAPI constructor
        
    Returns:
        Configured FastAPI application with service container integration
    """
    # Create FastAPI app with lifespan management
    app = FastAPI(
        lifespan=service_lifespan,
        **fastapi_kwargs
    )
    
    # Store environment in app state
    app.state.environment = environment
    
    # Add middleware for request context (if needed)
    @app.middleware("http")
    async def service_context_middleware(request: Request, call_next):
        """Middleware to provide service context for requests."""
        # Add request ID or other context if needed
        response = await call_next(request)
        return response
    
    # Add health check routes if enabled
    if enable_health_checks:
        add_health_check_routes(app)
    
    logger.info(f"FastAPI application created with AUTH-4 services for {environment} environment")
    return app


# Example usage functions for common patterns
async def with_services(
    security_monitor: SecurityMonitor = Depends(get_security_monitor),
    alert_engine: AlertEngine = Depends(get_alert_engine),
    audit_service: AuditService = Depends(get_audit_service),
) -> Dict[str, Any]:
    """Dependency function that provides multiple common services.
    
    This is a convenience function for endpoints that need multiple services.
    
    Example:
        @app.post("/api/security/analyze")
        async def analyze_security_event(
            event_data: dict,
            services = Depends(with_services),
        ):
            monitor = services["security_monitor"]
            alert_engine = services["alert_engine"]
            # ... use services
    """
    return {
        "security_monitor": security_monitor,
        "alert_engine": alert_engine,
        "audit_service": audit_service,
    }


async def with_logging(
    security_logger: SecurityLogger = Depends(get_security_logger),
    request: Request = None,
) -> SecurityLogger:
    """Dependency function that provides SecurityLogger with request context.
    
    This can be extended to automatically add request metadata to log events.
    """
    # Could add request metadata to logger context here if needed
    return security_logger