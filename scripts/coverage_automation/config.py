"""
Configuration management for coverage automation.
Handles loading and validation of test pattern configurations.
"""

from pathlib import Path
from typing import Any

import yaml

from .logging_utils import get_logger


class TestPatternConfig:
    """Configuration loader for test pattern definitions with Codecov integration."""

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize with config file path. Defaults to config/test_patterns.yaml"""
        self.logger = get_logger("config")

        if config_path is None:
            # Default to config/test_patterns.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "test_patterns.yaml"

        self.config_path: Path = config_path
        self._config: dict[str, Any] = self._load_config()
        self._codecov_config: dict[str, Any] = self._load_codecov_config()

        self.logger.info(
            "Configuration loaded successfully",
            config_path=str(self.config_path),
            test_types_count=len(self.get_all_test_types()),
        )

    def _load_config(self) -> dict[str, Any]:
        """Load and parse the YAML configuration file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Validate configuration structure
            self._validate_config(config)
            return config

        except FileNotFoundError:
            self.logger.warning("Configuration file not found, using fallback", config_path=str(self.config_path))
            return self._get_fallback_config()

        except yaml.YAMLError as e:
            self.logger.error(
                "Error parsing YAML config, using fallback", error=str(e), config_path=str(self.config_path),
            )
            return self._get_fallback_config()

        except Exception as e:
            self.logger.error(
                "Unexpected error loading config, using fallback", error=str(e), config_path=str(self.config_path),
            )
            return self._get_fallback_config()

    def _load_codecov_config(self) -> dict[str, Any]:
        """Load codecov.yaml to align flag mappings."""
        try:
            codecov_path = self.config_path.parent.parent / "codecov.yaml"
            if codecov_path.exists():
                with open(codecov_path, encoding="utf-8") as f:
                    codecov_config = yaml.safe_load(f)

                self.logger.info("Codecov configuration loaded for flag alignment", codecov_path=str(codecov_path))
                return codecov_config
            self.logger.warning("Codecov configuration not found")
            return {}

        except Exception as e:
            self.logger.error("Error loading codecov configuration", error=str(e))
            return {}

    def _validate_config(self, config: dict[str, Any]) -> None:
        """Validate configuration structure and content."""
        required_sections = ["test_types", "global"]
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")

        # Validate test types structure
        test_types = config.get("test_types", {})
        for test_type, test_config in test_types.items():
            required_fields = ["priority", "description", "patterns"]
            for field in required_fields:
                if field not in test_config:
                    raise ValueError(f"Test type '{test_type}' missing required field: {field}")

            # Validate priority is numeric
            if not isinstance(test_config["priority"], int):
                raise ValueError(f"Test type '{test_type}' priority must be integer")

            # Validate patterns is a list
            if not isinstance(test_config["patterns"], list):
                raise ValueError(f"Test type '{test_type}' patterns must be a list")

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
        """Get Codecov flag to source path mappings for unified views."""
        flag_mapping = {}

        if "flags" in self._codecov_config:
            for flag_name, flag_config in self._codecov_config["flags"].items():
                paths = flag_config.get("paths", [])
                flag_mapping[flag_name] = paths

        return flag_mapping

    def get_codecov_status_targets(self) -> dict[str, float]:
        """Get Codecov status target percentages by flag."""
        targets = {}

        coverage_config = self._codecov_config.get("coverage", {})
        status_config = coverage_config.get("status", {})
        project_config = status_config.get("project", {})

        for target_name, target_config in project_config.items():
            if isinstance(target_config, dict) and "target" in target_config:
                target_str = target_config["target"]
                if isinstance(target_str, str) and target_str.endswith("%"):
                    try:
                        targets[target_name] = float(target_str.rstrip("%"))
                    except ValueError:
                        continue

        return targets

    def align_with_codecov_flags(self, test_type: str) -> list[str]:
        """
        Get source paths for a test type aligned with Codecov flags.
        Returns paths that should be included for this test type based on Codecov configuration.
        """
        codecov_mapping = self.get_codecov_flag_mapping()

        # Direct mapping if test type exists as Codecov flag
        if test_type in codecov_mapping:
            return codecov_mapping[test_type]

        # Default patterns if no Codecov alignment
        test_config = self.get_test_type_config(test_type)
        return test_config.get("patterns", [])
