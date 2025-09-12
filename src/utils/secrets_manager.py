"""
Cloud-agnostic secrets management for PromptCraft-Hybrid production environments.

This module provides secure secret retrieval from various sources with fallback support:
- HashiCorp Vault (production)
- Encrypted .env files (development/staging)
- Environment variables (development fallback)
"""

import asyncio
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import time
from typing import Any, NoReturn

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # type: ignore[import-untyped]


# Optional encryption support with graceful fallback
try:
    from .encryption import EncryptionError, GPGError, load_encrypted_env

    ENCRYPTION_AVAILABLE = True
except ImportError as e:
    logging.error("Failed to import encryption module: %s. Encrypted env loading is unavailable.", e)

    # Define fallback exception classes to match the real ones
    class EncryptionError(Exception):  # type: ignore[no-redef]
        pass

    class GPGError(Exception):  # type: ignore[no-redef]
        pass

    # Fallback function with matching signature to the real one
    def load_encrypted_env(env_file_path: str = "") -> NoReturn:  # type: ignore[misc]
        raise NotImplementedError("Encryption module is missing; encrypted env loading is unavailable.")

    ENCRYPTION_AVAILABLE = False


@dataclass
class SecretConfig:
    """Configuration for secret management."""

    vault_url: str | None = None
    vault_token: str | None = None
    vault_namespace: str | None = None
    vault_mount_point: str = "secret"
    timeout: float = 30.0
    retry_attempts: int = 3
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes


class SecretsManagerError(Exception):
    """Raised when secrets management operations fail."""


class GenericSecretsManager:
    """
    Cloud-agnostic secrets manager with fallback support.

    Provides secure secret retrieval with the following precedence:
    1. HashiCorp Vault (production)
    2. Encrypted .env files (development/staging)
    3. Environment variables (development fallback)
    """

    def __init__(self, config: SecretConfig) -> None:
        """Initialize the secrets manager.

        Args:
            config: Secret configuration settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._cache: dict[str, Any] = {}
        self._cache_timestamps: dict[str, float] = {}

        if config.vault_url:
            self._test_vault_connection()

    def _test_vault_connection(self) -> None:
        """Test HashiCorp Vault connection."""
        if not self.config.vault_url or not self.config.vault_token:
            return

        try:
            url = f"{self.config.vault_url.rstrip('/')}/v1/sys/health"
            headers = {"X-Vault-Token": self.config.vault_token}

            if self.config.vault_namespace:
                headers["X-Vault-Namespace"] = self.config.vault_namespace

            session = self._create_secure_session()
            response = session.get(url, headers=headers, timeout=self.config.timeout)

            if response.status_code in (200, 429, 473, 503):  # Various healthy states
                self.logger.info("HashiCorp Vault connection verified")
                return

        except Exception as e:
            self.logger.warning("HashiCorp Vault connection test failed: %s", e)

    def _is_cache_valid(self, secret_name: str) -> bool:
        """Check if cached secret is still valid."""
        if not self.config.cache_enabled:
            return False

        if secret_name not in self._cache:
            return False

        timestamp = self._cache_timestamps.get(secret_name, 0)
        return (time.time() - timestamp) < self.config.cache_ttl_seconds

    def _cache_secret(self, secret_name: str, value: str) -> None:
        """Cache a secret value."""
        if not self.config.cache_enabled:
            return

        self._cache[secret_name] = value
        self._cache_timestamps[secret_name] = time.time()

    async def get_secret_async(self, secret_name: str) -> str | None:
        """
        Retrieve a secret asynchronously with fallback hierarchy.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            Secret value or None if not found

        Raises:
            SecretsManagerError: If all retrieval methods fail
        """
        # Check cache first
        if self._is_cache_valid(secret_name):
            self.logger.debug("Retrieved secret from cache")
            cached_value = self._cache[secret_name]
            return str(cached_value) if cached_value is not None else None

        # Try HashiCorp Vault first
        if self.config.vault_url and self.config.vault_token:
            try:
                for attempt in range(self.config.retry_attempts):
                    try:
                        secret = await asyncio.wait_for(
                            asyncio.create_task(self._get_vault_secret(secret_name)),
                            timeout=self.config.timeout,
                        )
                        if secret:
                            self._cache_secret(secret_name, secret)
                            self.logger.debug("Retrieved secret from HashiCorp Vault")
                            return secret
                        break
                    except TimeoutError:
                        self.logger.warning(
                            "HashiCorp Vault timeout (attempt %d/%d)",
                            attempt + 1,
                            self.config.retry_attempts,
                        )
                        if attempt == self.config.retry_attempts - 1:
                            break
                        await asyncio.sleep(2**attempt)  # Exponential backoff
            except Exception:
                self.logger.warning("Failed to retrieve secret from HashiCorp Vault")

        # Fallback to encrypted env files
        try:
            secret = self._get_encrypted_secret(secret_name)
            if secret:
                self._cache_secret(secret_name, secret)
                self.logger.debug("Retrieved secret from encrypted env file")
                return secret
        except (EncryptionError, GPGError, FileNotFoundError):
            self.logger.debug("Could not retrieve secret from encrypted files")

        # Final fallback to environment variables
        env_secret = os.getenv(f"PROMPTCRAFT_{secret_name.upper()}")
        if env_secret:
            self._cache_secret(secret_name, env_secret)
            self.logger.debug("Retrieved secret from environment variable")
            return env_secret

        self.logger.warning("Secret not found in any source")
        return None

    def get_secret(self, secret_name: str) -> str | None:
        """
        Retrieve a secret synchronously with fallback hierarchy.

        Args:
            secret_name: Name of the secret to retrieve

        Returns:
            Secret value or None if not found
        """
        try:
            return asyncio.run(self.get_secret_async(secret_name))
        except Exception as e:
            self.logger.error("Failed to retrieve secret")
            raise SecretsManagerError(f"Secret retrieval failed for '{secret_name}': {e}") from e

    async def _get_vault_secret(self, secret_name: str) -> str | None:
        """Retrieve secret from HashiCorp Vault."""
        if not self.config.vault_url or not self.config.vault_token:
            return None

        try:
            # Convert secret name to Vault path format (replace underscores with slashes for nested paths)
            vault_path = f"{self.config.vault_mount_point}/data/promptcraft/{secret_name}"
            url = f"{self.config.vault_url.rstrip('/')}/v1/{vault_path}"

            def _sync_get_secret() -> str | None:
                headers = {"X-Vault-Token": self.config.vault_token}

                if self.config.vault_namespace:
                    headers["X-Vault-Namespace"] = self.config.vault_namespace

                session = self._create_secure_session()
                response = session.get(url, headers=headers, timeout=self.config.timeout)

                if response.status_code == 200:
                    data = response.json()
                    value = data.get("data", {}).get("data", {}).get("value")
                    return str(value) if value is not None else None
                return None

            # Run the synchronous request in a thread pool
            return await asyncio.get_event_loop().run_in_executor(None, _sync_get_secret)

        except Exception:
            self.logger.debug("HashiCorp Vault secret not found or inaccessible")
            return None

    def _get_encrypted_secret(self, secret_name: str) -> str | None:
        """Retrieve secret from encrypted .env files."""
        project_root = Path(__file__).parent.parent.parent

        # Try environment-specific encrypted file first
        current_env = os.getenv("PROMPTCRAFT_ENVIRONMENT", "dev")
        env_files = [
            project_root / f".env.{current_env}.gpg",
            project_root / ".env.gpg",
            project_root / f".env.{current_env}",
            project_root / ".env",
        ]

        for env_file in env_files:
            if not env_file.exists():
                continue

            try:
                if env_file.suffix == ".gpg":
                    if not ENCRYPTION_AVAILABLE:
                        self.logger.warning("Encryption module unavailable, skipping encrypted file: %s", env_file)
                        continue
                    env_vars = load_encrypted_env(str(env_file))
                else:
                    env_vars = self._load_plain_env(env_file)

                # Look for the secret with PROMPTCRAFT_ prefix
                full_key = f"PROMPTCRAFT_{secret_name.upper()}"
                if full_key in env_vars:
                    return str(env_vars[full_key])

            except Exception as e:
                self.logger.debug("Could not load env file '%s': %s", env_file, e)
                continue

        return None

    def _load_plain_env(self, env_file: Path) -> dict[str, str]:
        """Load environment variables from plain .env file."""
        env_vars = {}

        try:
            with env_file.open("r", encoding="utf-8") as f:
                for raw_line in f:
                    line = raw_line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip().strip("\"'")
        except Exception as e:
            self.logger.debug("Error reading plain env file '%s': %s", env_file, e)

        return env_vars

    def _create_secure_session(self) -> requests.Session:
        """Create a secure requests session with proper configuration."""
        session = requests.Session()

        # Configure retry strategy with exponential backoff
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)

        # Security: Verify SSL certificates
        session.verify = True

        # Set reasonable timeout (note: timeout is set per request, not on session)

        return session

    def get_multiple_secrets(self, secret_names: list[str]) -> dict[str, str | None]:
        """
        Retrieve multiple secrets efficiently.

        Args:
            secret_names: List of secret names to retrieve

        Returns:
            Dictionary mapping secret names to their values (or None if not found)
        """
        try:
            return asyncio.run(self._get_multiple_secrets_async(secret_names))
        except Exception as e:
            self.logger.error("Failed to retrieve multiple secrets")
            raise SecretsManagerError(f"Multiple secret retrieval failed: {e}") from e

    async def _get_multiple_secrets_async(self, secret_names: list[str]) -> dict[str, str | None]:
        """Retrieve multiple secrets asynchronously."""
        tasks = [self.get_secret_async(name) for name in secret_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            name: str(result) if not isinstance(result, BaseException) and result is not None else None
            for name, result in zip(secret_names, results, strict=True)
        }

    def clear_cache(self) -> None:
        """Clear the secrets cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
        self.logger.debug("Secrets cache cleared")


# Global secrets manager instance
_secrets_manager: GenericSecretsManager | None = None


def get_secrets_manager() -> GenericSecretsManager:
    """
    Get or create the global secrets manager instance.

    Returns:
        Configured secrets manager instance
    """
    global _secrets_manager  # noqa: PLW0603

    if _secrets_manager is None:
        # Configuration from environment variables
        config = SecretConfig(
            vault_url=os.getenv("VAULT_URL"),
            vault_token=os.getenv("VAULT_TOKEN"),
            vault_namespace=os.getenv("VAULT_NAMESPACE"),
            vault_mount_point=os.getenv("VAULT_MOUNT_POINT", "secret"),
            timeout=float(os.getenv("SECRETS_TIMEOUT", "30.0")),
            retry_attempts=int(os.getenv("SECRETS_RETRY_ATTEMPTS", "3")),
            cache_enabled=os.getenv("SECRETS_CACHE_ENABLED", "true").lower() == "true",
            cache_ttl_seconds=int(os.getenv("SECRETS_CACHE_TTL", "300")),
        )

        _secrets_manager = GenericSecretsManager(config)

    return _secrets_manager


def get_secret(secret_name: str) -> str | None:
    """
    Convenient function to retrieve a single secret.

    Args:
        secret_name: Name of the secret to retrieve

    Returns:
        Secret value or None if not found
    """
    manager = get_secrets_manager()
    return manager.get_secret(secret_name)


def get_multiple_secrets(secret_names: list[str]) -> dict[str, str | None]:
    """
    Convenient function to retrieve multiple secrets.

    Args:
        secret_names: List of secret names to retrieve

    Returns:
        Dictionary mapping secret names to their values
    """
    manager = get_secrets_manager()
    return manager.get_multiple_secrets(secret_names)


# Required secrets for different environments
REQUIRED_SECRETS_PROD = ["secret_key", "jwt_secret_key", "database_password"]

REQUIRED_SECRETS_STAGING = ["secret_key", "database_password"]

OPTIONAL_SECRETS = ["qdrant_api_key", "mcp_api_key", "openrouter_api_key", "encryption_key"]
