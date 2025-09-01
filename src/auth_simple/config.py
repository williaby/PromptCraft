"""Simple configuration management for streamlined authentication.

This module provides configuration management for the simplified Cloudflare Access
authentication system, including environment variable loading, validation, and
feature flag management.
"""

import os
import logging
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from pydantic import BaseModel, validator, Field
from enum import Enum

logger = logging.getLogger(__name__)


class AuthMode(str, Enum):
    """Authentication modes supported by the system."""
    CLOUDFLARE_SIMPLE = "cloudflare_simple"
    DISABLED = "disabled"  # For development/testing only


class LogLevel(str, Enum):
    """Logging levels for authentication."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class CloudflareConfig:
    """Cloudflare-specific configuration."""
    validate_headers: bool = True
    required_headers: List[str] = field(default_factory=lambda: ['cf-ray'])
    log_events: bool = True
    trust_cf_headers: bool = True


class AuthConfig(BaseModel):
    """Main authentication configuration model."""
    
    # Core authentication settings
    auth_mode: AuthMode = AuthMode.CLOUDFLARE_SIMPLE
    enabled: bool = True
    
    # Email whitelist configuration
    email_whitelist: List[str] = Field(default_factory=list, description="List of allowed emails and domains")
    admin_emails: List[str] = Field(default_factory=list, description="List of admin email addresses")
    case_sensitive_emails: bool = False
    
    # Session management
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")
    enable_session_cookies: bool = True
    session_cookie_secure: bool = True
    session_cookie_httponly: bool = True
    
    # Public paths (no authentication required)
    public_paths: Set[str] = Field(
        default_factory=lambda: {
            '/', '/ping',  # Basic application endpoints
            '/health', '/api/health', '/api/v1/health',  # Health endpoints
            '/health/config', '/health/mcp', '/health/circuit-breakers',  # Detailed health endpoints
            '/docs', '/openapi.json', '/redoc',  # Documentation endpoints
            '/api/v1/validate', '/api/v1/search'  # Test/demo endpoints
        },
        description="Paths that don't require authentication"
    )
    
    # Cloudflare configuration
    cloudflare: CloudflareConfig = Field(default_factory=CloudflareConfig)
    
    # Logging and monitoring
    log_level: LogLevel = LogLevel.INFO
    log_auth_events: bool = True
    log_failed_attempts: bool = True
    
    # Development/testing settings
    dev_mode: bool = False
    mock_cf_headers: Dict[str, str] = Field(default_factory=dict)
    
    @validator('email_whitelist', pre=True)
    def parse_email_whitelist(cls, v):
        """Parse email whitelist from string or list."""
        if isinstance(v, str):
            return [email.strip() for email in v.split(',') if email.strip()]
        return v or []
    
    @validator('admin_emails', pre=True)
    def parse_admin_emails(cls, v):
        """Parse admin emails from string or list."""
        if isinstance(v, str):
            return [email.strip() for email in v.split(',') if email.strip()]
        return v or []
    
    @validator('public_paths', pre=True)
    def parse_public_paths(cls, v):
        """Parse public paths from string, list, or set."""
        if isinstance(v, str):
            return {path.strip() for path in v.split(',') if path.strip()}
        elif isinstance(v, list):
            return set(v)
        return v or set()
    
    @validator('session_timeout')
    def validate_session_timeout(cls, v):
        """Ensure session timeout is reasonable."""
        if v < 60:  # Minimum 1 minute
            raise ValueError("Session timeout must be at least 60 seconds")
        if v > 86400:  # Maximum 24 hours
            raise ValueError("Session timeout must be less than 24 hours")
        return v
    
    def validate_configuration(self) -> List[str]:
        """Validate the configuration and return warnings.
        
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check for empty whitelist in production
        if not self.dev_mode and not self.email_whitelist:
            warnings.append("Email whitelist is empty in production mode")
        
        # Check admin emails are in whitelist
        from .whitelist import EmailWhitelistValidator
        validator = EmailWhitelistValidator(
            self.email_whitelist, 
            self.admin_emails, 
            self.case_sensitive_emails
        )
        
        for admin_email in self.admin_emails:
            if not validator.is_authorized(admin_email):
                warnings.append(f"Admin email {admin_email} is not in whitelist")
        
        # Check for insecure configurations
        if not self.session_cookie_secure and not self.dev_mode:
            warnings.append("Session cookies should be secure in production")
        
        # Check for public email domains in whitelist
        public_domains = ['@gmail.com', '@outlook.com', '@yahoo.com', '@hotmail.com']
        for domain in public_domains:
            if domain in self.email_whitelist:
                warnings.append(f"Public email domain {domain} in whitelist may be insecure")
        
        return warnings


class ConfigLoader:
    """Loads authentication configuration from environment variables."""
    
    ENV_PREFIX = "PROMPTCRAFT_"
    
    @classmethod
    def load_from_env(cls, prefix: str = None) -> AuthConfig:
        """Load configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix (default: PROMPTCRAFT_)
            
        Returns:
            AuthConfig instance
        """
        prefix = prefix or cls.ENV_PREFIX
        
        config_data = {}
        
        # Core authentication settings
        config_data['auth_mode'] = os.getenv(f'{prefix}AUTH_MODE', 'cloudflare_simple')
        config_data['enabled'] = cls._get_bool_env(f'{prefix}AUTH_ENABLED', True)
        
        # Email settings
        config_data['email_whitelist'] = os.getenv(f'{prefix}EMAIL_WHITELIST', '')
        config_data['admin_emails'] = os.getenv(f'{prefix}ADMIN_EMAILS', '')
        config_data['case_sensitive_emails'] = cls._get_bool_env(f'{prefix}CASE_SENSITIVE_EMAILS', False)
        
        # Session settings
        config_data['session_timeout'] = cls._get_int_env(f'{prefix}SESSION_TIMEOUT', 3600)
        config_data['enable_session_cookies'] = cls._get_bool_env(f'{prefix}ENABLE_SESSION_COOKIES', True)
        config_data['session_cookie_secure'] = cls._get_bool_env(f'{prefix}SESSION_COOKIE_SECURE', True)
        
        # Public paths
        config_data['public_paths'] = os.getenv(f'{prefix}PUBLIC_PATHS', '')
        
        # Logging settings
        config_data['log_level'] = os.getenv(f'{prefix}LOG_LEVEL', 'INFO')
        config_data['log_auth_events'] = cls._get_bool_env(f'{prefix}LOG_AUTH_EVENTS', True)
        config_data['log_failed_attempts'] = cls._get_bool_env(f'{prefix}LOG_FAILED_ATTEMPTS', True)
        
        # Development settings
        config_data['dev_mode'] = cls._get_bool_env(f'{prefix}DEV_MODE', False)
        
        # Cloudflare settings
        cloudflare_config = {
            'validate_headers': cls._get_bool_env(f'{prefix}CF_VALIDATE_HEADERS', True),
            'log_events': cls._get_bool_env(f'{prefix}CF_LOG_EVENTS', True),
            'trust_cf_headers': cls._get_bool_env(f'{prefix}CF_TRUST_HEADERS', True)
        }
        config_data['cloudflare'] = CloudflareConfig(**cloudflare_config)
        
        # Mock headers for development
        if config_data['dev_mode']:
            config_data['mock_cf_headers'] = {
                'cf-access-authenticated-user-email': os.getenv(f'{prefix}DEV_USER_EMAIL', 'dev@example.com'),
                'cf-ray': os.getenv(f'{prefix}DEV_CF_RAY', 'dev-ray-123'),
                'cf-ipcountry': os.getenv(f'{prefix}DEV_IP_COUNTRY', 'US')
            }
        
        try:
            config = AuthConfig(**config_data)
            logger.info(f"Loaded authentication configuration with mode: {config.auth_mode}")
            return config
        except Exception as e:
            logger.error(f"Failed to load authentication configuration: {e}")
            raise
    
    @staticmethod
    def _get_bool_env(key: str, default: bool = False) -> bool:
        """Get boolean value from environment variable."""
        value = os.getenv(key, '').lower()
        if value in ('true', '1', 'yes', 'on'):
            return True
        elif value in ('false', '0', 'no', 'off'):
            return False
        else:
            return default
    
    @staticmethod
    def _get_int_env(key: str, default: int) -> int:
        """Get integer value from environment variable."""
        try:
            return int(os.getenv(key, str(default)))
        except (ValueError, TypeError):
            return default


class ConfigManager:
    """Manages authentication configuration and provides utilities."""
    
    def __init__(self, config: AuthConfig = None):
        """Initialize configuration manager.
        
        Args:
            config: AuthConfig instance (loads from env if None)
        """
        self.config = config or ConfigLoader.load_from_env()
        self._setup_logging()
        self._validate_config()
    
    def _setup_logging(self):
        """Setup logging based on configuration."""
        logging.getLogger('src.auth_simple').setLevel(self.config.log_level.value)
    
    def _validate_config(self):
        """Validate configuration and log warnings."""
        warnings = self.config.validate_configuration()
        for warning in warnings:
            logger.warning(f"Configuration warning: {warning}")
    
    def is_dev_mode(self) -> bool:
        """Check if running in development mode."""
        return self.config.dev_mode
    
    def get_mock_headers(self) -> Dict[str, str]:
        """Get mock Cloudflare headers for development."""
        return self.config.mock_cf_headers if self.config.dev_mode else {}
    
    def create_whitelist_validator(self):
        """Create email whitelist validator from config."""
        from .whitelist import EmailWhitelistValidator
        return EmailWhitelistValidator(
            whitelist=self.config.email_whitelist,
            admin_emails=self.config.admin_emails,
            case_sensitive=self.config.case_sensitive_emails
        )
    
    def create_middleware(self):
        """Create authentication middleware from config."""
        from .middleware import CloudflareAccessMiddleware, SimpleSessionManager
        
        validator = self.create_whitelist_validator()
        session_manager = SimpleSessionManager(session_timeout=self.config.session_timeout)
        
        return CloudflareAccessMiddleware(
            app=None,  # Will be set by FastAPI
            whitelist_validator=validator,
            session_manager=session_manager,
            public_paths=self.config.public_paths,
            enable_session_cookies=self.config.enable_session_cookies
        )
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for logging/debugging.
        
        Returns:
            Dictionary with configuration summary (safe for logging)
        """
        return {
            'auth_mode': self.config.auth_mode.value,
            'enabled': self.config.enabled,
            'whitelist_count': len(self.config.email_whitelist),
            'admin_count': len(self.config.admin_emails),
            'session_timeout': self.config.session_timeout,
            'public_paths_count': len(self.config.public_paths),
            'dev_mode': self.config.dev_mode,
            'log_level': self.config.log_level.value
        }


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get or create global configuration manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_auth_config() -> AuthConfig:
    """Get authentication configuration."""
    return get_config_manager().config


def reset_config():
    """Reset global configuration (for testing)."""
    global _config_manager
    _config_manager = None