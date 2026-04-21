"""
Pact Configuration for MCP Contract Testing

Configures Pact settings for consumer-driven contract testing between
PromptCraft and MCP servers (zen-mcp-server, heimdall-mcp-server).
"""

import os
from pathlib import Path
from typing import Any

import pytest


# Pact configuration constants
PACT_BROKER_URL = os.getenv("PACT_BROKER_URL", "http://localhost:9292")  # Optional Pact Broker
PACT_DIR = Path(__file__).parent.parent.parent / "pacts"  # Store pact files in project root
PACT_MOCK_SERVICE_PORT_START = 1234  # Starting port for Pact mock services

# Consumer and provider names
CONSUMER_NAME = "promptcraft"
ZEN_PROVIDER_NAME = "zen-mcp-server"
HEIMDALL_PROVIDER_NAME = "heimdall-mcp-server"

# Test server ports (different from Pact mock service ports)
TEST_SERVER_PORTS = {
    "zen-mcp-server": 8080,
    "heimdall-stub": 8081,
}


class PactConfiguration:
    """Configuration manager for Pact contract testing."""

    def __init__(self):
        self.pact_dir = PACT_DIR
        self.consumer_name = CONSUMER_NAME

        # Ensure pacts directory exists
        self.pact_dir.mkdir(exist_ok=True)

    def get_pact_config(self, provider_name: str, mock_port: int | None = None) -> dict[str, Any]:
        """Get Pact configuration for a specific provider."""
        if mock_port is None:
            mock_port = PACT_MOCK_SERVICE_PORT_START + hash(provider_name) % 1000

        return {
            "consumer_name": self.consumer_name,
            "provider_name": provider_name,
            "pact_dir": str(self.pact_dir),
            "mock_port": mock_port,
            "host": "localhost",
            "publish": False,  # Set to True if using Pact Broker
            "version": "1.0.0",
        }

    def get_zen_config(self) -> dict[str, Any]:
        """Get Pact configuration for zen-mcp-server."""
        return self.get_pact_config(ZEN_PROVIDER_NAME, 1234)

    def get_heimdall_config(self) -> dict[str, Any]:
        """Get Pact configuration for heimdall-mcp-server."""
        return self.get_pact_config(HEIMDALL_PROVIDER_NAME, 1235)

    def get_pact_file_path(self, provider_name: str) -> Path:
        """Get the path where pact file will be saved."""
        filename = f"{self.consumer_name}-{provider_name}.json"
        return self.pact_dir / filename

    @property
    def zen_pact_file(self) -> Path:
        """Path to zen-mcp-server pact file."""
        return self.get_pact_file_path(ZEN_PROVIDER_NAME)

    @property
    def heimdall_pact_file(self) -> Path:
        """Path to heimdall-mcp-server pact file."""
        return self.get_pact_file_path(HEIMDALL_PROVIDER_NAME)


class PactTestSettings:
    """Test execution settings for Pact contract tests."""

    # Test modes
    CONSUMER_TEST = "consumer"  # Generate pact files from consumer tests
    PROVIDER_TEST = "provider"  # Verify providers against pact files
    BOTH = "both"  # Run both consumer and provider tests

    def __init__(self):
        self.mode = os.getenv("PACT_TEST_MODE", self.CONSUMER_TEST)
        self.log_level = os.getenv("PACT_LOG_LEVEL", "INFO")
        self.timeout = int(os.getenv("PACT_TIMEOUT", "30"))
        self.publish_pacts = os.getenv("PACT_PUBLISH", "false").lower() == "true"

    @property
    def should_run_consumer_tests(self) -> bool:
        """Whether to run consumer contract tests."""
        return self.mode in (self.CONSUMER_TEST, self.BOTH)

    @property
    def should_run_provider_tests(self) -> bool:
        """Whether to run provider verification tests."""
        return self.mode in (self.PROVIDER_TEST, self.BOTH)

    @property
    def pact_verification_settings(self) -> dict[str, Any]:
        """Settings for provider verification."""
        return {
            "timeout": self.timeout,
            "publish": self.publish_pacts,
            "log_level": self.log_level,
        }


# Global instances
pact_config = PactConfiguration()
pact_settings = PactTestSettings()


def pytest_configure(config):
    """Configure pytest with Pact markers."""
    config.addinivalue_line(
        "markers",
        "contract: mark test as a contract test",
    )
    config.addinivalue_line(
        "markers",
        "pact_consumer: mark test as a Pact consumer test",
    )
    config.addinivalue_line(
        "markers",
        "pact_provider: mark test as a Pact provider verification test",
    )


@pytest.fixture(scope="session")
def pact_config_instance() -> PactConfiguration:
    """Provide Pact configuration to tests."""
    return pact_config


@pytest.fixture(scope="session")
def pact_settings_instance() -> PactTestSettings:
    """Provide Pact test settings to tests."""
    return pact_settings


def get_contract_test_env() -> dict[str, str]:
    """Environment variables for contract testing."""
    return {
        "CONTRACT_TEST": "true",
        "PACT_TEST_MODE": pact_settings.mode,
        "LOG_LEVEL": "INFO",
        "DISABLE_EXTERNAL_SERVICES": "true",  # Disable external API calls in tests
        "TEST_MODE": "contract",
    }
