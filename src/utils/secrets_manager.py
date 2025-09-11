"""
Cloud-agnostic secrets management for PromptCraft-Hybrid production environments.

This module provides secure secret retrieval from various sources with fallback support:
- HashiCorp Vault (production)
- Encrypted .env files (development/staging)
- Environment variables (development fallback)
"""

import asyncio
from dataclasses import dataclass
import json
import logging
import os
from pathlib import Path
from typing import Any
import urllib.error
import urllib.parse
import urllib.request

from .encryption import EncryptionError, GPGError, load_encrypted_env


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

    def __init__(self, config: SecretConfig):
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
            req = urllib.request.Request(url)
            req.add_header("X-Vault-Token", self.config.vault_token)

            if self.config.vault_namespace:
                req.add_header("X-Vault-Namespace", self.config.vault_namespace)

            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                if response.status in (200, 429, 473, 503):  # Various healthy states
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

        import time

        timestamp = self._cache_timestamps.get(secret_name, 0)
        return (time.time() - timestamp) < self.config.cache_ttl_seconds

    def _cache_secret(self, secret_name: str, value: str) -> None:
        """Cache a secret value."""
        if not self.config.cache_enabled:
            return

        import time

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
            self.logger.debug("Retrieved secret '%s' from cache", secret_name)
            return self._cache[secret_name]

        # Try HashiCorp Vault first
        if self.config.vault_url and self.config.vault_token:
            try:
                for attempt in range(self.config.retry_attempts):
                    try:
                        secret = await asyncio.wait_for(
                            asyncio.create_task(self._get_vault_secret(secret_name)), timeout=self.config.timeout,
                        )
                        if secret:
                            self._cache_secret(secret_name, secret)
                            self.logger.debug("Retrieved secret '%s' from HashiCorp Vault", secret_name)
                            return secret
                        break
                    except TimeoutError:
                        self.logger.warning(
                            "HashiCorp Vault timeout (attempt %d/%d) for secret '%s'",
                            attempt + 1,
                            self.config.retry_attempts,
                            secret_name,
                        )
                        if attempt == self.config.retry_attempts - 1:
                            break
                        await asyncio.sleep(2**attempt)  # Exponential backoff
            except Exception as e:
                self.logger.warning("Failed to retrieve secret '%s' from HashiCorp Vault: %s", secret_name, e)

        # Fallback to encrypted env files
        try:
            secret = self._get_encrypted_secret(secret_name)
            if secret:
                self._cache_secret(secret_name, secret)
                self.logger.debug("Retrieved secret '%s' from encrypted env file", secret_name)
                return secret
        except (EncryptionError, GPGError, FileNotFoundError) as e:
            self.logger.debug("Could not retrieve secret '%s' from encrypted files: %s", secret_name, e)

        # Final fallback to environment variables
        env_secret = os.getenv(f"PROMPTCRAFT_{secret_name.upper()}")
        if env_secret:
            self._cache_secret(secret_name, env_secret)
            self.logger.debug("Retrieved secret '%s' from environment variable", secret_name)
            return env_secret

        self.logger.warning("Secret '%s' not found in any source", secret_name)
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
            self.logger.error("Failed to retrieve secret '%s': %s", secret_name, e)
            raise SecretsManagerError(f"Secret retrieval failed for '{secret_name}': {e}") from e

    async def _get_vault_secret(self, secret_name: str) -> str | None:
        """Retrieve secret from HashiCorp Vault."""
        if not self.config.vault_url or not self.config.vault_token:
            return None

        try:
            # Convert secret name to Vault path format (replace underscores with slashes for nested paths)
            vault_path = f"{self.config.vault_mount_point}/data/promptcraft/{secret_name}"
            url = f"{self.config.vault_url.rstrip('/')}/v1/{vault_path}"

            def _sync_get_secret():
                req = urllib.request.Request(url)
                req.add_header("X-Vault-Token", self.config.vault_token)

                if self.config.vault_namespace:
                    req.add_header("X-Vault-Namespace", self.config.vault_namespace)

                with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        return data.get("data", {}).get("data", {}).get("value")
                    return None

            # Run the synchronous request in a thread pool
            secret = await asyncio.get_event_loop().run_in_executor(None, _sync_get_secret)

            return secret

        except Exception as e:
            self.logger.debug("HashiCorp Vault secret '%s' not found or inaccessible: %s", secret_name, e)
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
                    env_vars = load_encrypted_env(str(env_file))
                else:
                    env_vars = self._load_plain_env(env_file)

                # Look for the secret with PROMPTCRAFT_ prefix
                full_key = f"PROMPTCRAFT_{secret_name.upper()}"
                if full_key in env_vars:
                    return env_vars[full_key]

            except Exception as e:
                self.logger.debug("Could not load env file '%s': %s", env_file, e)
                continue

        return None

    def _load_plain_env(self, env_file: Path) -> dict[str, str]:
        """Load environment variables from plain .env file."""
        env_vars = {}

        try:
            with env_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip().strip("\"'")
        except Exception as e:
            self.logger.debug("Error reading plain env file '%s': %s", env_file, e)

        return env_vars

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
            self.logger.error("Failed to retrieve multiple secrets: %s", e)
            raise SecretsManagerError(f"Multiple secret retrieval failed: {e}") from e

    async def _get_multiple_secrets_async(self, secret_names: list[str]) -> dict[str, str | None]:
        """Retrieve multiple secrets asynchronously."""
        tasks = [self.get_secret_async(name) for name in secret_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            name: result if not isinstance(result, Exception) else None for name, result in zip(secret_names, results, strict=False)
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
    global _secrets_manager

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
