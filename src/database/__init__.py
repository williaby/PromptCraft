"""Database package for PromptCraft authentication enhancement.

This package provides PostgreSQL integration for enhanced Cloudflare Access authentication
including session management, event logging, and user metadata storage.
"""

from .connection import DatabaseConnectionError, DatabaseError, DatabaseManager, get_database_manager, get_db_session
from .models import AuthenticationEvent, Base, UserSession

__all__ = [
    "AuthenticationEvent",
    "Base",
    "DatabaseConnectionError",
    "DatabaseError",
    "DatabaseManager",
    "UserSession",
    "get_database_manager",
    "get_db_session",
]
