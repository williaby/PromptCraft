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

from src.config.constants import (
    CORS_ORIGINS_BY_ENVIRONMENT,
    HEALTH_CHECK_ERROR_LIMIT,
    HEALTH_CHECK_SUGGESTION_LIMIT,
)
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
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
            "Application started successfully: %s v%s (%s)",
            settings.app_name,
            settings.version,
            settings.environment,
        )

        # Store settings in app state for access in endpoints
        app.state.settings = settings

        yield

    except ConfigurationValidationError as e:
        logger.error("Configuration validation failed during startup: %s", e)
        # Log detailed errors for debugging
        for error in e.field_errors:
            logger.error("  Configuration error: %s", error)
        for suggestion in e.suggestions:
            logger.info("  Suggestion: %s", suggestion)
        raise
    except Exception as e:
        logger.error("Unexpected error during application startup: %s", e)
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
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning("Settings format error for app creation: %s", type(e).__name__)
        # Use defaults if settings unavailable
        settings = ApplicationSettings()
    except Exception:
        logger.exception("Failed to load settings for app creation")
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

    # Add CORS middleware with environment-specific origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS_BY_ENVIRONMENT.get(settings.environment, CORS_ORIGINS_BY_ENVIRONMENT["dev"]),
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
    except Exception as e:  # noqa: BLE001 # Catch-all for unhandled endpoint errors
        logger.error("Health check endpoint failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "service": "promptcraft-hybrid",
                "error": "Health check failed",
            },
        ) from e


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
        logger.error("Configuration validation failed in health check: %s", e)

        # Try to get settings for debug mode check, fallback to production mode
        try:
            settings = get_settings(validate_on_startup=False)
            debug_mode = settings.debug
        except Exception:  # noqa: BLE001
            debug_mode = False

        # Only expose detailed errors in debug mode
        if debug_mode:
            detail = {
                "error": "Configuration validation failed",
                "field_errors": e.field_errors[:HEALTH_CHECK_ERROR_LIMIT],
                "suggestions": e.suggestions[:HEALTH_CHECK_SUGGESTION_LIMIT],
            }
        else:
            detail = {
                "error": "Configuration validation failed",
                "details": "Contact system administrator",
            }

        raise HTTPException(status_code=500, detail=detail) from e
    except Exception as e:  # noqa: BLE001 # Catch-all for unhandled endpoint errors
        logger.error("Configuration health check failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Configuration health check failed",
                "details": "See application logs for more information",
            },
        ) from e


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
    import sys

    import uvicorn

    try:
        settings = get_settings()
        logger.info(
            "Starting development server on %s:%d",
            settings.api_host,
            settings.api_port,
        )
        uvicorn.run(
            "src.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.debug,
            log_level="info" if not settings.debug else "debug",
        )
    except ConfigurationValidationError as e:
        logger.error("Cannot start server due to configuration errors: %s", e)
        sys.exit(1)
    except (OSError, RuntimeError) as e:
        logger.error("Failed to start development server: %s", e)
        sys.exit(1)
    except Exception:  # Catch-all for startup errors
        logger.exception("Unexpected error starting development server")
        sys.exit(1)
