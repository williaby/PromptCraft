"""Centralized configuration constants to eliminate code duplication.

This module defines shared constants used across the configuration system
to maintain consistency and reduce maintenance burden.
"""

# Secret field names used throughout the application
# These must match the field names in ApplicationSettings
SECRET_FIELD_NAMES = [
    "database_password",
    "database_url",
    "api_key",
    "secret_key",
    "azure_openai_api_key",
    "jwt_secret_key",
    "qdrant_api_key",
    "encryption_key",
]

# Sensitive error patterns for validation error sanitization
# Each tuple contains (pattern, replacement_message)
SENSITIVE_ERROR_PATTERNS = [
    (r"password", "Password configuration issue (details hidden)"),
    (r"api[\s_]key", "API key configuration issue (details hidden)"),
    (r"secret.*key", "Secret key configuration issue (details hidden)"),
    (r"key.*secret", "Secret key configuration issue (details hidden)"),
    (r"jwt.*secret", "JWT secret configuration issue (details hidden)"),
]

# File path patterns for sanitization
FILE_PATH_PATTERNS = [
    r"/home/",
    r"C:\\",
    r"/Users/",
]

# Health check response limits
HEALTH_CHECK_ERROR_LIMIT = 5
HEALTH_CHECK_SUGGESTION_LIMIT = 3

# CORS origins configuration by environment
CORS_ORIGINS_BY_ENVIRONMENT = {
    "dev": ["http://localhost:3000", "http://localhost:5173", "http://localhost:7860"],
    "staging": ["https://staging.promptcraft.io"],
    "prod": ["https://promptcraft.io"],
}
