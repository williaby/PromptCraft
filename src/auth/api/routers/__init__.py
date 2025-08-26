"""
API Routers Module

Focused router modules decomposed from monolithic security_dashboard_endpoints.py.
Each router handles a specific domain with single responsibility.

Routers:
    - metrics_router: System metrics and health endpoints
    - alerts_router: Security alert management endpoints
    - users_router: User management and monitoring endpoints
    - events_router: Security event logging endpoints
    - audit_router: Audit trail and compliance endpoints
    - charts_router: Dashboard visualization endpoints
    - health_router: System health check endpoints
    - analytics_router: Security analytics endpoints
"""

from .alerts_router import router as alerts_router
from .analytics_router import router as analytics_router
from .audit_router import router as audit_router
from .charts_router import router as charts_router
from .events_router import router as events_router
from .health_router import router as health_router
from .metrics_router import router as metrics_router
from .users_router import router as users_router

__all__ = [
    "alerts_router",
    "analytics_router",
    "audit_router",
    "charts_router",
    "events_router",
    "health_router",
    "metrics_router",
    "users_router",
]
