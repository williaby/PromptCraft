"""Simplified authentication system for PromptCraft.

This package provides a streamlined Cloudflare Access authentication system
that replaces the complex 22K+ line authentication module with a simple
5-file, ~500 line implementation focused on:

- Cloudflare Access header extraction (Cf-Access-Authenticated-User-Email)
- Email whitelist validation with domain support (@company.com)
- Simple FastAPI middleware integration
- Basic session management
- Configuration management

Usage:
    # Basic setup
    from auth_simple import create_auth_middleware, get_auth_config

    # Create middleware from environment configuration
    middleware = create_auth_middleware()
    app.add_middleware(middleware)

    # Use authentication dependency in routes
    from auth_simple import require_auth, require_admin

    @app.get("/protected")
    async def protected_route(user=Depends(require_auth)):
        return {"user": user["email"]}

    @app.get("/admin")
    async def admin_route(user=Depends(require_admin)):
        return {"admin": user["email"]}

Environment Variables:
    PROMPTCRAFT_AUTH_MODE: Authentication mode (default: cloudflare_simple)
    PROMPTCRAFT_EMAIL_WHITELIST: Comma-separated list of allowed emails/domains
    PROMPTCRAFT_ADMIN_EMAILS: Comma-separated list of admin emails
    PROMPTCRAFT_SESSION_TIMEOUT: Session timeout in seconds (default: 3600)
    PROMPTCRAFT_DEV_MODE: Enable development mode (default: False)
"""

from .cloudflare_auth import (
    CloudflareAuthError,
    CloudflareAuthHandler,
    CloudflareUser,
    extract_user_from_cloudflare_headers,
    validate_cloudflare_request,
)
from .config import (
    AuthConfig,
    AuthMode,
    CloudflareConfig,
    ConfigLoader,
    ConfigManager,
    get_auth_config,
    get_config_manager,
    reset_config,
)
from .middleware import (
    AuthenticationDependency,
    CloudflareAccessMiddleware,
    SimpleSessionManager,
    create_auth_middleware,
    require_admin,
    require_auth,
)
from .whitelist import (
    EmailWhitelistConfig,
    EmailWhitelistValidator,
    WhitelistEntry,
    WhitelistManager,
    create_validator_from_env,
)

# Package metadata
__version__ = "1.0.0"
__author__ = "PromptCraft Development Team"
__description__ = "Simplified Cloudflare Access authentication for PromptCraft"

# Main exports for easy importing
__all__ = [
    # Core authentication
    "CloudflareAuthHandler",
    "CloudflareUser",
    "CloudflareAuthError",
    "extract_user_from_cloudflare_headers",
    "validate_cloudflare_request",
    # Email whitelist management
    "EmailWhitelistValidator",
    "EmailWhitelistConfig",
    "WhitelistManager",
    "WhitelistEntry",
    "create_validator_from_env",
    # Middleware and dependencies
    "CloudflareAccessMiddleware",
    "SimpleSessionManager",
    "AuthenticationDependency",
    "require_auth",
    "require_admin",
    "create_auth_middleware",
    # Configuration management
    "AuthConfig",
    "AuthMode",
    "CloudflareConfig",
    "ConfigLoader",
    "ConfigManager",
    "get_config_manager",
    "get_auth_config",
    "reset_config",
    # Convenience functions
    "setup_auth_middleware",
    "get_current_user",
    "is_admin_user",
]


def setup_auth_middleware(app, config_manager: ConfigManager = None):
    """Convenience function to setup authentication middleware.

    Args:
        app: FastAPI application instance
        config_manager: Optional configuration manager (creates from env if None)

    Returns:
        The configured middleware instance
    """
    if config_manager is None:
        config_manager = get_config_manager()

    # Get the middleware instance (already configured)
    middleware = config_manager.create_middleware()

    # Add the middleware to the app using the instance
    app.add_middleware(
        type(middleware),
        whitelist_validator=middleware.whitelist_validator,
        session_manager=middleware.session_manager,
        public_paths=middleware.public_paths,
        health_check_paths=middleware.health_check_paths,
        enable_session_cookies=middleware.enable_session_cookies,
    )

    return middleware


def get_current_user(request) -> dict:
    """Get current user from request state.

    Args:
        request: FastAPI request object

    Returns:
        User context dictionary or None if not authenticated
    """
    return getattr(request.state, "user", None)


def is_admin_user(request) -> bool:
    """Check if current user is an admin.

    Args:
        request: FastAPI request object

    Returns:
        True if user is admin, False otherwise
    """
    user = get_current_user(request)
    return user.get("is_admin", False) if user else False


# Version information
def get_version_info() -> dict:
    """Get version and configuration information.

    Returns:
        Dictionary with version and configuration details
    """
    config_manager = get_config_manager()

    return {
        "version": __version__,
        "auth_mode": config_manager.config.auth_mode.value,
        "package_name": __name__,
        "description": __description__,
        "config_summary": config_manager.get_config_summary(),
    }


# Development and testing utilities
def create_test_config(**overrides) -> AuthConfig:
    """Create test configuration with overrides.

    Args:
        **overrides: Configuration values to override

    Returns:
        AuthConfig for testing
    """
    defaults = {
        "dev_mode": True,
        "email_whitelist": ["test@example.com", "@testdomain.com"],
        "admin_emails": ["admin@example.com"],
        "session_timeout": 300,  # 5 minutes for testing
        "log_level": "DEBUG",
        "session_cookie_secure": False,  # For local testing
    }

    defaults.update(overrides)
    return AuthConfig(**defaults)


def create_test_middleware(**config_overrides):
    """Create test middleware with custom configuration.

    Args:
        **config_overrides: Configuration overrides

    Returns:
        Configured middleware for testing
    """
    config = create_test_config(**config_overrides)
    config_manager = ConfigManager(config)
    return config_manager.create_middleware()


# Logging setup
import logging

logger = logging.getLogger(__name__)
logger.info(f"Initialized auth_simple package v{__version__}")

# Log configuration summary on import
try:
    config_info = get_version_info()
    logger.info(f"Authentication configuration: {config_info['config_summary']}")
except Exception as e:
    logger.warning(f"Could not load configuration summary: {e}")
