"""Authentication API package.

This package contains API endpoints for authentication and security dashboard functionality.
All endpoints use FastAPI async patterns and include comprehensive error handling.
"""

from .security_dashboard_endpoints import router as security_dashboard_router

__all__ = ["security_dashboard_router"]
