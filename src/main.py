"""Main FastAPI application for PromptCraft-Hybrid.

This module defines the main FastAPI application with health check endpoints
and configuration status monitoring. It serves as the primary entry point
for the application.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

try:
    # Try relative imports first (when imported as module)
    from .config.health import (
        ConfigurationStatusModel,
        get_configuration_health_summary,
        get_configuration_status,
    )
    from .config.settings import (
        ApplicationSettings,
        ConfigurationValidationError,
        get_settings,
    )
except ImportError:
    # Fall back to absolute imports (when run directly)
    from src.config.health import (
        ConfigurationStatusModel,
        get_configuration_health_summary,
        get_configuration_status,
    )
    from src.config.settings import (
        ApplicationSettings,
        ConfigurationValidationError,
        get_settings,
    )


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown.

    This function handles application startup and shutdown events,
    including configuration validation and resource cleanup.

    Args:
        app: The FastAPI application instance

    Yields:
        None during application lifetime
    """
    logger.info("Starting PromptCraft-Hybrid application...")

    try:
        # Load and validate configuration on startup
        settings = get_settings(validate_on_startup=True)
        logger.info(
            f"Application started successfully: {settings.app_name} v{settings.version} "
            f"({settings.environment})",
        )

        # Store settings in app state for access in endpoints
        app.state.settings = settings

        yield

    except ConfigurationValidationError as e:
        logger.error(f"Configuration validation failed during startup: {e}")
        # Log detailed errors for debugging
        for error in e.field_errors:
            logger.error(f"  Configuration error: {error}")
        for suggestion in e.suggestions:
            logger.info(f"  Suggestion: {suggestion}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during application startup: {e}")
        raise
    finally:
        logger.info("PromptCraft-Hybrid application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    # Get settings for app metadata
    try:
        settings = get_settings(validate_on_startup=False)
    except Exception as e:
        logger.warning(f"Could not load settings for app creation: {e}")
        # Use defaults if settings unavailable
        settings = ApplicationSettings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description="A Zen-powered AI workbench for transforming queries into accurate, context-aware outputs",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else ["https://promptcraft.io"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    return app


# Create the FastAPI application instance
app = create_app()


@app.get("/health", response_model=dict[str, Any])
async def health_check() -> dict[str, Any]:
    """Simple health check endpoint for basic monitoring.

    This endpoint provides a quick health status without detailed
    configuration information. It's suitable for load balancers
    and simple monitoring systems.

    Returns:
        Basic health status information

    Raises:
        HTTPException: If health check fails
    """
    try:
        health_summary = get_configuration_health_summary()

        if health_summary["healthy"]:
            return {
                "status": "healthy",
                "service": "promptcraft-hybrid",
                **health_summary,
            }
        else:
            logger.warning("Health check failed - configuration unhealthy")
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "unhealthy",
                    "service": "promptcraft-hybrid",
                    **health_summary,
                },
            )
    except HTTPException:
        # Re-raise HTTPExceptions to preserve status codes
        raise
    except Exception as e:
        logger.error(f"Health check endpoint failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "service": "promptcraft-hybrid",
                "error": "Health check failed",
            },
        )


@app.get("/health/config", response_model=ConfigurationStatusModel)
async def configuration_health() -> ConfigurationStatusModel:
    """Detailed configuration health check endpoint.

    This endpoint provides comprehensive configuration status information
    for operational monitoring and debugging. It includes validation status,
    configuration sources, and secret field counts without exposing
    sensitive values.

    Returns:
        Detailed configuration status information

    Raises:
        HTTPException: If configuration status cannot be determined
    """
    try:
        settings = get_settings(validate_on_startup=False)
        return get_configuration_status(settings)
    except ConfigurationValidationError as e:
        logger.error(f"Configuration validation failed in health check: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Configuration validation failed",
                "field_errors": e.field_errors[:5],  # Limit errors for response size
                "suggestions": e.suggestions[:3],  # Limit suggestions for response size
            },
        )
    except Exception as e:
        logger.error(f"Configuration health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Configuration health check failed",
                "details": "See application logs for more information",
            },
        )


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint providing basic application information.

    Returns:
        Basic application information
    """
    try:
        settings: ApplicationSettings = app.state.settings
        return {
            "service": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "status": "running",
            "docs_url": "/docs" if settings.debug else "disabled",
        }
    except AttributeError:
        # Fallback if settings not available in app state
        return {
            "service": "PromptCraft-Hybrid",
            "version": "unknown",
            "environment": "unknown",
            "status": "running",
        }


@app.get("/ping")
async def ping() -> dict[str, str]:
    """Simple ping endpoint for load balancer checks.

    Returns:
        Simple pong response
    """
    return {"message": "pong"}


if __name__ == "__main__":
    # Development server - not for production use
    import uvicorn

    try:
        settings = get_settings()
        logger.info(
            f"Starting development server on {settings.api_host}:{settings.api_port}",
        )
        uvicorn.run(
            "src.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level="info" if not settings.debug else "debug",
        )
    except ConfigurationValidationError as e:
        logger.error(f"Cannot start server due to configuration errors: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"Failed to start development server: {e}")
        exit(1)
