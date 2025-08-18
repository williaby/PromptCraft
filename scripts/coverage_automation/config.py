"""
Configuration management for coverage automation.
"""

from pathlib import Path
from typing import Any

import yaml


class TestPatternConfig:
    """Configuration loader for test pattern definitions."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize with config file path. Defaults to config/test_patterns.yaml"""
        if config_path is None:
            # Default to config/test_patterns.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "test_patterns.yaml"

        self.config_path: Path = config_path
        self._config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """Load and parse the YAML configuration file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"⚠️  Configuration file not found: {self.config_path}")
            print("⚠️  Using fallback hardcoded patterns")
            return self._get_fallback_config()
        except yaml.YAMLError as e:
            print(f"⚠️  Error parsing YAML config: {e}")
            print("⚠️  Using fallback hardcoded patterns")
            return self._get_fallback_config()

    def _get_fallback_config(self) -> dict[str, Any]:
        """Provide fallback configuration if YAML file is unavailable."""
        return {
            "test_types": {
                "auth": {
                    "priority": 1,
                    "patterns": ["tests/auth/", "tests/unit/auth/"],
                    "description": "Authentication and authorization tests",
                },
                "security": {
                    "priority": 2,
                    "patterns": ["tests/security/", "tests/unit/test_security_*"],
                    "description": "Security-focused tests",
                },
                "integration": {"priority": 3, "patterns": ["tests/integration/"], "description": "Integration tests"},
                "unit": {"priority": 8, "patterns": ["tests/unit/"], "description": "Unit tests"},
            },
            "global": {
                "security": {"max_file_size_mb": 1},
                "performance": {"cache_size_test_mapping": 32, "cache_size_file_analysis": 256},
            },
        }

    def get_test_type_config(self, test_type: str) -> dict[str, Any]:
        """Get configuration for a specific test type."""
        return self._config.get("test_types", {}).get(test_type, {})

    def get_patterns_by_priority(self) -> list[tuple[str, dict]]:
        """Return test types ordered by priority (most specific first)."""
        types = []
        for name, config in self._config.get("test_types", {}).items():
            priority = config.get("priority", 999)
            types.append((priority, name, config))
        return [(name, config) for _, name, config in sorted(types)]

    def get_global_config(self, section: str = None) -> dict[str, Any]:
        """Get global configuration section."""
        global_config = self._config.get("global", {})
        if section:
            return global_config.get(section, {})
        return global_config

    def get_all_test_types(self) -> list[str]:
        """Get all defined test types."""
        return list(self._config.get("test_types", {}).keys())

    def get_codecov_flag_mapping(self) -> dict[str, list[str]]:
        """Get Codecov flag mapping from codecov.yaml if available."""
        codecov_config = self._config.get("codecov_integration", {})
        if not codecov_config.get("enabled", False):
            return {}

        # Try to load codecov.yaml
        project_root = self.config_path.parent.parent
        codecov_file = project_root / "codecov.yaml"

        if codecov_file.exists():
            try:
                with open(codecov_file, encoding="utf-8") as f:
                    codecov_data = yaml.safe_load(f)
                    flags = codecov_data.get("flags", {})

                    # Convert to simple mapping
                    flag_mapping = {}
                    for flag_name, flag_config in flags.items():
                        paths = flag_config.get("paths", [])
                        flag_mapping[flag_name] = paths

                    return flag_mapping
            except (yaml.YAMLError, OSError):
                pass

        return {}
