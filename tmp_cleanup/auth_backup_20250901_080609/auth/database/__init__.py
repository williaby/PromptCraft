"""Authentication database package.

This package contains database management for authentication and security events.
"""

from .security_events_postgres import SecurityEventsDatabase

__all__ = ["SecurityEventsDatabase"]
