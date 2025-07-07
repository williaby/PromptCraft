"""Secure error handling for FastAPI applications.

This module provides production-safe error handlers that prevent information
disclosure through stack traces while maintaining useful error responses
for debugging in development environments.
"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


def create_secure_error_response(
    request: Request,
    error: Exception,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail: str = "Internal server error",
) -> JSONResponse:
    """Create a secure error response that prevents information disclosure.

    Args:
        request: The incoming request
        error: The exception that occurred
        status_code: HTTP status code to return
        detail: Error detail message (production-safe)

    Returns:
        JSONResponse with sanitized error information
    """
    settings = get_settings(validate_on_startup=False)

    # Base response with safe information
    response_data: dict[str, Any] = {
        "error": detail,
        "status_code": status_code,
        "timestamp": request.state.timestamp if hasattr(request.state, "timestamp") else None,
        "path": str(request.url.path),
    }

    # Add debug information only in development
    if settings.debug and settings.environment == "dev":
        response_data["debug"] = {
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        # Include traceback only in development with explicit debug flag
        if isinstance(error, Exception) and not isinstance(error, HTTPException | StarletteHTTPException):
            response_data["debug"]["traceback"] = traceback.format_exc()

    # Log the actual error for monitoring (with full details)
    logger.error(
        "Application error: %s - %s (Path: %s, IP: %s)",
        type(error).__name__,
        str(error),
        request.url.path,
        request.client.host if request.client else "unknown",
        exc_info=True,
    )

    return JSONResponse(
        status_code=status_code,
        content=response_data,
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with secure error responses.

    Args:
        request: The incoming request
        exc: The HTTP exception

    Returns:
        Secure JSON error response
    """
    return create_secure_error_response(
        request=request,
        error=exc,
        status_code=exc.status_code,
        detail=exc.detail if isinstance(exc.detail, str) else "HTTP error",
    )


async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle Starlette HTTP exceptions with secure error responses.

    Args:
        request: The incoming request
        exc: The Starlette HTTP exception

    Returns:
        Secure JSON error response
    """
    return create_secure_error_response(
        request=request,
        error=exc,
        status_code=exc.status_code,
        detail=exc.detail if isinstance(exc.detail, str) else "HTTP error",
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle request validation errors with secure responses.

    Args:
        request: The incoming request
        exc: The validation error

    Returns:
        Secure JSON error response with validation details
    """
    settings = get_settings(validate_on_startup=False)

    # Create sanitized validation error details
    if settings.debug and settings.environment == "dev":
        # In development, provide detailed validation errors
        detail = "Request validation failed"
        validation_errors = []

        for error in exc.errors():
            validation_errors.append(
                {
                    "field": " -> ".join(str(loc) for loc in error["loc"]),
                    "message": error["msg"],
                    "type": error["type"],
                },
            )

        response_data = {
            "error": detail,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "validation_errors": validation_errors,
        }
    else:
        # In production, provide minimal validation error information
        response_data = {
            "error": "Invalid request data",
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Please check your request parameters and try again",
        }

    logger.warning(
        "Request validation failed: %s (Path: %s, IP: %s)",
        exc.errors(),
        request.url.path,
        request.client.host if request.client else "unknown",
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data,
        headers={
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions with secure error responses.

    This is the catch-all handler that prevents any stack traces from
    leaking to clients in production environments.

    Args:
        request: The incoming request
        exc: The unhandled exception

    Returns:
        Secure JSON error response
    """
    return create_secure_error_response(
        request=request,
        error=exc,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred",
    )


def setup_secure_error_handlers(app: FastAPI) -> None:
    """Configure secure error handlers for the FastAPI application.

    This function registers all necessary error handlers to prevent
    information disclosure through stack traces and error messages.

    Args:
        app: The FastAPI application instance
    """
    # Register exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Secure error handlers configured for application")


# Utility function for manual error creation
def create_secure_http_exception(
    status_code: int,
    detail: str,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """Create an HTTPException with security headers.

    Args:
        status_code: HTTP status code
        detail: Error detail message
        headers: Additional headers to include

    Returns:
        HTTPException with secure headers
    """
    secure_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    }

    if headers:
        secure_headers.update(headers)

    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers=secure_headers,
    )
