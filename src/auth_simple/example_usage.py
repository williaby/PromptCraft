"""Example usage of the simplified authentication system.

This file demonstrates how to integrate the streamlined auth_simple package
into a FastAPI application, replacing the complex authentication system
with a simple Cloudflare Access + email whitelist approach.
"""

import logging
from typing import Any

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse

# Import the simplified authentication system
from . import (
    create_test_config,
    get_config_manager,
    get_current_user,
    is_admin_user,
    require_admin,
    require_auth,
    setup_auth_middleware,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PromptCraft with Simplified Authentication",
    description="Example of simplified Cloudflare Access authentication",
    version="1.0.0",
)

# Environment configuration example
"""
Set these environment variables:

# Authentication configuration
PROMPTCRAFT_AUTH_MODE=cloudflare_simple
PROMPTCRAFT_EMAIL_WHITELIST=admin@example.com,user@example.com,@yourcompany.com
PROMPTCRAFT_ADMIN_EMAILS=admin@example.com
PROMPTCRAFT_SESSION_TIMEOUT=3600
PROMPTCRAFT_DEV_MODE=false

# For development/testing
PROMPTCRAFT_DEV_MODE=true
PROMPTCRAFT_DEV_USER_EMAIL=dev@example.com
"""

# Setup authentication middleware
try:
    config_manager = get_config_manager()
    setup_auth_middleware(app, config_manager)
    logger.info("Authentication configured: %s", config_manager.get_config_summary())
except Exception as e:
    logger.error("Failed to setup authentication: %s", e)
    # Fallback to test configuration for development
    test_config = create_test_config(
        email_whitelist=["dev@example.com", "@example.com"],
        admin_emails=["admin@example.com"],
    )
    from .config import ConfigManager

    config_manager = ConfigManager(test_config)
    setup_auth_middleware(app, config_manager)
    logger.warning("Using test authentication configuration")


# Public endpoints (no authentication required)
@app.get("/health")
async def health_check() -> dict[str, str]:
    """Public health check endpoint."""
    return {"status": "healthy", "auth_system": "auth_simple"}


@app.get("/api/health")
async def api_health_check() -> dict[str, Any]:
    """API health check endpoint."""
    return {"status": "healthy", "version": "1.0.0", "auth_mode": config_manager.config.auth_mode.value}


# Protected endpoints requiring authentication
@app.get("/api/user/profile")
async def get_user_profile(user: Any = Depends(require_auth)) -> dict[str, Any]:
    """Get current user profile (requires authentication)."""
    return {
        "profile": {
            "email": user["email"],
            "role": user["role"],
            "authenticated_at": user["authenticated_at"].isoformat(),
            "session_id": user["session_id"],
        },
    }


@app.get("/api/user/dashboard")
async def user_dashboard(_request: Request, user: Any = Depends(require_auth)) -> dict[str, Any]:
    """User dashboard (requires authentication)."""
    cf_context = user.get("cf_context", {})

    return {
        "dashboard": {
            "welcome_message": f"Welcome {user['email']}!",
            "role": user["role"],
            "is_admin": user["is_admin"],
            "cloudflare_info": {
                "country": cf_context.get("ip_country", "unknown"),
                "cf_ray": cf_context.get("cf_ray", "unknown"),
                "connecting_ip": cf_context.get("connecting_ip", "unknown"),
            },
        },
    }


# Admin-only endpoints
@app.get("/api/admin/users")
async def list_users(user: Any = Depends(require_admin)) -> dict[str, Any]:
    """List all users (admin only)."""
    return {
        "admin_action": "list_users",
        "performed_by": user["email"],
        "users": [{"email": "admin@example.com", "role": "admin"}, {"email": "user@example.com", "role": "user"}],
    }


@app.get("/api/admin/config")
async def get_config(user: Any = Depends(require_admin)) -> dict[str, Any]:
    """Get system configuration (admin only)."""
    return {"config": config_manager.get_config_summary(), "requested_by": user["email"]}


# Alternative authentication checking without dependencies
@app.get("/api/check-auth")
async def check_auth_status(request: Request) -> dict[str, Any]:
    """Check authentication status without requiring auth."""
    user = get_current_user(request)

    if not user:
        return {"authenticated": False, "message": "No authentication found"}

    return {
        "authenticated": True,
        "user": {"email": user["email"], "role": user["role"], "is_admin": is_admin_user(request)},
    }


# Error handlers
@app.exception_handler(401)
async def unauthorized_handler(_request: Request, _exc: Any) -> JSONResponse:
    """Handle unauthorized access."""
    return JSONResponse(
        status_code=401,
        content={
            "error": "Authentication required",
            "detail": "Please authenticate via Cloudflare Access",
            "auth_mode": config_manager.config.auth_mode.value,
        },
    )


@app.exception_handler(403)
async def forbidden_handler(request: Request, _exc: Any) -> JSONResponse:
    """Handle forbidden access."""
    user = get_current_user(request)
    user_email = user["email"] if user else "unknown"

    return JSONResponse(
        status_code=403,
        content={
            "error": "Access forbidden",
            "detail": f"User {user_email} does not have required permissions",
            "required": "Valid email in whitelist",
        },
    )


# Development utilities
if config_manager.config.dev_mode:

    @app.get("/dev/simulate-cloudflare-user")
    async def simulate_cloudflare_user(email: str = "dev@example.com") -> dict[str, Any]:
        """Development endpoint to simulate Cloudflare user headers."""
        mock_headers = config_manager.get_mock_headers()
        mock_headers["cf-access-authenticated-user-email"] = email

        return {
            "dev_mode": True,
            "simulated_headers": mock_headers,
            "instructions": "Use these headers in your requests for testing",
        }


# Application startup
@app.on_event("startup")
async def startup_event() -> None:
    """Application startup event."""
    logger.info("PromptCraft starting with simplified authentication")
    logger.info("Configuration: %s", config_manager.get_config_summary())

    # Validate configuration
    warnings = config_manager.config.validate_configuration()
    for warning in warnings:
        logger.warning("Config warning: %s", warning)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Application shutdown event."""
    logger.info("PromptCraft shutting down")


if __name__ == "__main__":
    import uvicorn

    # Development server
    uvicorn.run(
        "example_usage:app",
        host="0.0.0.0",  # noqa: S104  # nosec B104
        port=8000,
        reload=True,
        log_level="info",
    )
