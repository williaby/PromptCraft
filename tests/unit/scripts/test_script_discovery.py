"""
Comprehensive tests for Scripts Discovery System.

This test suite provides comprehensive coverage for the ScriptsDiscoverySystem
and ScriptsManager classes, testing script discovery, categorization, content loading,
and metadata parsing across project and user script directories.
"""

from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.scripts.discovery import (
    ScriptDefinition,
    ScriptsDiscoverySystem,
    ScriptsManager,
)
from src.utils.datetime_compat import utc_now


class TestScriptDefinition:
    """Test suite for ScriptDefinition dataclass."""

    def test_script_definition_creation(self):
        """Test creating a ScriptDefinition instance."""
        file_path = Path("/test/script.py")
        last_updated = utc_now()

        script = ScriptDefinition(
            script_id="test-script",
            name="Test Script",
            description="A test script",
            file_path=file_path,
            source_type="project",
            script_type="python",
            is_executable=True,
            content="print('hello')",
            version="1.0.0",
            category="development",
            dependencies=["requests"],
            parameters=["--verbose"],
            last_updated=last_updated,
        )

        assert script.script_id == "test-script"
        assert script.name == "Test Script"
        assert script.description == "A test script"
        assert script.file_path == file_path
        assert script.source_type == "project"
        assert script.script_type == "python"
        assert script.is_executable is True
        assert script.content == "print('hello')"
        assert script.version == "1.0.0"
        assert script.category == "development"
        assert script.dependencies == ["requests"]
        assert script.parameters == ["--verbose"]
        assert script.last_updated == last_updated

    def test_script_definition_defaults(self):
        """Test ScriptDefinition with default values."""
        file_path = Path("/test/script.py")

        script = ScriptDefinition(
            script_id="test-script",
            name="Test Script",
            description="A test script",
            file_path=file_path,
            source_type="project",
            script_type="python",
        )

        assert script.is_executable is False
        assert script.content is None
        assert script.version is None
        assert script.category is None
        assert script.dependencies == []
        assert script.parameters == []
        assert script.last_updated is None

    def test_script_definition_post_init(self):
        """Test ScriptDefinition default field factories."""
        file_path = Path("/test/script.py")

        script = ScriptDefinition(
            script_id="test-script",
            name="Test Script",
            description="A test script",
            file_path=file_path,
            source_type="project",
            script_type="python",
            # dependencies and parameters omitted - should default to empty lists
        )

        # default_factory should initialize empty lists
        assert script.dependencies == []
        assert script.parameters == []


class TestScriptsDiscoverySystem:
    """Test suite for ScriptsDiscoverySystem class."""

    @pytest.fixture
    def mock_project_root(self):
        """Create a mock project root path."""
        return Path("/test/project")

    @pytest.fixture
    def discovery_system(self, mock_project_root):
        """Create a ScriptsDiscoverySystem instance for testing."""
        return ScriptsDiscoverySystem(project_root=mock_project_root)

    def test_initialization_with_project_root(self, mock_project_root):
        """Test ScriptsDiscoverySystem initialization with project root."""
        system = ScriptsDiscoverySystem(project_root=mock_project_root)

        assert system.project_root == mock_project_root
        assert system.project_scripts_path == mock_project_root / ".claude" / "scripts"
        assert system.user_scripts_path == Path.home() / ".claude" / "scripts"
        assert system._scripts_cache == {}
        assert system._cache_timestamp is None
        assert system._cache_ttl_seconds == 300

        # Test script categories and extensions are properly initialized
        assert "setup" in system.script_categories
        assert ".py" in system.script_extensions
        assert system.script_extensions[".py"] == "python"

    def test_initialization_without_project_root(self):
        """Test ScriptsDiscoverySystem initialization without project root."""
        with patch("pathlib.Path.cwd", return_value=Path("/current/dir")):
            system = ScriptsDiscoverySystem()

            assert system.project_root == Path("/current/dir")
            assert system.project_scripts_path == Path("/current/dir") / ".claude" / "scripts"

    def test_should_refresh_cache_no_timestamp(self, discovery_system):
        """Test cache refresh check when no timestamp is set."""
        assert discovery_system._should_refresh_cache() is True

    def test_should_refresh_cache_within_ttl(self, discovery_system):
        """Test cache refresh check within TTL."""
        discovery_system._cache_timestamp = utc_now()
        assert discovery_system._should_refresh_cache() is False

    def test_should_refresh_cache_expired(self, discovery_system):
        """Test cache refresh check when cache is expired."""
        discovery_system._cache_timestamp = utc_now() - timedelta(seconds=400)
        assert discovery_system._should_refresh_cache() is True

    def test_get_available_scripts_empty_cache(self, discovery_system):
        """Test getting available scripts when cache is empty."""
        with patch.object(discovery_system, "_should_refresh_cache", return_value=True):
            with patch.object(discovery_system, "_refresh_scripts_cache") as mock_refresh:
                discovery_system._scripts_cache = {}

                scripts = discovery_system.get_available_scripts()

                assert scripts == []
                mock_refresh.assert_called_once()

    def test_get_available_scripts_with_cache(self, discovery_system):
        """Test getting available scripts when cache has scripts."""
        mock_script1 = Mock(spec=ScriptDefinition)
        mock_script2 = Mock(spec=ScriptDefinition)

        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._scripts_cache = {
                "script1": mock_script1,
                "script2": mock_script2,
            }

            scripts = discovery_system.get_available_scripts()

            assert set(scripts) == {"script1", "script2"}

    def test_get_scripts_by_category_direct_match(self, discovery_system):
        """Test getting scripts by category with direct category match."""
        mock_script1 = Mock(spec=ScriptDefinition)
        mock_script1.category = "setup"
        mock_script1.script_id = "install-deps"

        mock_script2 = Mock(spec=ScriptDefinition)
        mock_script2.category = "validation"
        mock_script2.script_id = "check-quality"

        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._scripts_cache = {
                "install-deps": mock_script1,
                "check-quality": mock_script2,
            }

            setup_scripts = discovery_system.get_scripts_by_category("setup")

            assert len(setup_scripts) == 1
            assert setup_scripts[0] == mock_script1

    def test_get_scripts_by_category_keyword_match(self, discovery_system):
        """Test getting scripts by category with keyword matching."""
        mock_script = Mock(spec=ScriptDefinition)
        mock_script.category = None
        mock_script.script_id = "validate-project"

        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._scripts_cache = {"validate-project": mock_script}

            validation_scripts = discovery_system.get_scripts_by_category("validation")

            assert len(validation_scripts) == 1
            assert validation_scripts[0] == mock_script
            assert mock_script.category == "validation"  # Should be set by the method

    def test_get_scripts_by_type(self, discovery_system):
        """Test getting scripts by script type."""
        mock_python_script = Mock(spec=ScriptDefinition)
        mock_python_script.script_type = "python"

        mock_shell_script = Mock(spec=ScriptDefinition)
        mock_shell_script.script_type = "shell"

        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._scripts_cache = {
                "python_script": mock_python_script,
                "shell_script": mock_shell_script,
            }

            python_scripts = discovery_system.get_scripts_by_type("python")

            assert len(python_scripts) == 1
            assert python_scripts[0] == mock_python_script

    def test_get_executable_scripts(self, discovery_system):
        """Test getting only executable scripts."""
        mock_executable = Mock(spec=ScriptDefinition)
        mock_executable.is_executable = True

        mock_not_executable = Mock(spec=ScriptDefinition)
        mock_not_executable.is_executable = False

        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._scripts_cache = {
                "executable": mock_executable,
                "not_executable": mock_not_executable,
            }

            executable_scripts = discovery_system.get_executable_scripts()

            assert len(executable_scripts) == 1
            assert executable_scripts[0] == mock_executable

    def test_get_script_exists(self, discovery_system):
        """Test getting a script that exists in cache."""
        mock_script = Mock(spec=ScriptDefinition)

        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._scripts_cache = {"test-script": mock_script}

            result = discovery_system.get_script("test-script")

            assert result == mock_script

    def test_get_script_not_exists(self, discovery_system):
        """Test getting a script that doesn't exist."""
        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._scripts_cache = {}

            result = discovery_system.get_script("nonexistent")

            assert result is None

    def test_get_script_content_success(self, discovery_system):
        """Test getting script content successfully."""
        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = "#!/usr/bin/env python\nprint('hello')"

        mock_script = ScriptDefinition(
            script_id="test",
            name="Test",
            description="Test script",
            file_path=mock_path,
            source_type="project",
            script_type="python",
        )

        with patch.object(discovery_system, "get_script", return_value=mock_script):
            with patch.object(discovery_system, "_parse_script_metadata") as mock_parse:
                content = discovery_system.get_script_content("test")

                assert content == "#!/usr/bin/env python\nprint('hello')"
                mock_path.read_text.assert_called_once_with(encoding="utf-8")
                mock_parse.assert_called_once_with(mock_script)
                assert mock_script.content == "#!/usr/bin/env python\nprint('hello')"

    def test_get_script_content_cached(self, discovery_system):
        """Test getting script content that's already cached."""
        mock_path = Mock(spec=Path)

        mock_script = ScriptDefinition(
            script_id="test",
            name="Test",
            description="Test script",
            file_path=mock_path,
            source_type="project",
            script_type="python",
            content="# Cached Content",
        )

        with patch.object(discovery_system, "get_script", return_value=mock_script):
            content = discovery_system.get_script_content("test")

            assert content == "# Cached Content"
            mock_path.read_text.assert_not_called()

    def test_get_script_content_script_not_found(self, discovery_system):
        """Test getting script content when script doesn't exist."""
        with patch.object(discovery_system, "get_script", return_value=None):
            content = discovery_system.get_script_content("nonexistent")

            assert content is None

    def test_get_script_content_file_read_error(self, discovery_system):
        """Test getting script content when file read fails."""
        mock_path = Mock(spec=Path)
        mock_path.read_text.side_effect = OSError("File not found")

        mock_script = ScriptDefinition(
            script_id="test",
            name="Test",
            description="Test script",
            file_path=mock_path,
            source_type="project",
            script_type="python",
        )

        with patch.object(discovery_system, "get_script", return_value=mock_script):
            content = discovery_system.get_script_content("test")

            assert content is None

    def test_discover_script_from_project(self, discovery_system):
        """Test discovering a script from project source."""
        mock_script = Mock(spec=ScriptDefinition)

        with patch.object(discovery_system, "_search_project_scripts", return_value=mock_script):
            with patch.object(discovery_system, "_search_user_scripts", return_value=None):
                with patch.object(discovery_system, "_search_builtin_scripts", return_value=None):
                    result = discovery_system.discover_script("test-script")

                    assert result == mock_script
                    assert result.source_type == "project"

    def test_discover_script_from_user_fallback(self, discovery_system):
        """Test discovering a script from user source as fallback."""
        mock_script = Mock(spec=ScriptDefinition)

        with patch.object(discovery_system, "_search_project_scripts", return_value=None):
            with patch.object(discovery_system, "_search_user_scripts", return_value=mock_script):
                with patch.object(discovery_system, "_search_builtin_scripts", return_value=None):
                    result = discovery_system.discover_script("test-script")

                    assert result == mock_script
                    assert result.source_type == "user"

    def test_discover_script_not_found(self, discovery_system):
        """Test discovering a script that doesn't exist anywhere."""
        with patch.object(discovery_system, "_search_project_scripts", return_value=None):
            with patch.object(discovery_system, "_search_user_scripts", return_value=None):
                with patch.object(discovery_system, "_search_builtin_scripts", return_value=None):
                    result = discovery_system.discover_script("nonexistent")

                    assert result is None

    def test_search_scripts(self, discovery_system):
        """Test searching scripts by query."""
        mock_script1 = Mock(spec=ScriptDefinition)
        mock_script1.script_id = "setup-database"
        mock_script1.name = "Database Setup"
        mock_script1.description = "Sets up the database"

        mock_script2 = Mock(spec=ScriptDefinition)
        mock_script2.script_id = "validate-config"
        mock_script2.name = "Config Validator"
        mock_script2.description = "Validates configuration"

        mock_script3 = Mock(spec=ScriptDefinition)
        mock_script3.script_id = "deploy-app"
        mock_script3.name = "App Deployer"
        mock_script3.description = "Deploys the application"

        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._scripts_cache = {
                "setup-database": mock_script1,
                "validate-config": mock_script2,
                "deploy-app": mock_script3,
            }

            # Search by script ID
            results = discovery_system.search_scripts("setup")
            assert len(results) == 1
            assert results[0] == mock_script1

            # Search by name
            results = discovery_system.search_scripts("validator")
            assert len(results) == 1
            assert results[0] == mock_script2

            # Search by description
            results = discovery_system.search_scripts("application")
            assert len(results) == 1
            assert results[0] == mock_script3

    def test_search_project_scripts_with_extension(self, discovery_system):
        """Test searching for script in project directory with extension."""
        mock_script = Mock(spec=ScriptDefinition)

        def mock_exists(self):
            path_str = str(self)
            # Allow directory to exist
            if path_str == str(discovery_system.project_scripts_path):
                return True
            # Allow specific script file to exist
            return path_str == str(discovery_system.project_scripts_path / "test-script.py")

        with patch("pathlib.Path.exists", mock_exists):
            with patch.object(discovery_system, "_create_script_definition", return_value=mock_script):
                result = discovery_system._search_project_scripts("test-script")

                assert result == mock_script

    def test_search_project_scripts_exact_filename(self, discovery_system):
        """Test searching for script with exact filename match."""
        mock_script = Mock(spec=ScriptDefinition)

        def mock_exists(self):
            path_str = str(self)
            # Only the exact filename exists, no extensions
            return path_str == str(discovery_system.project_scripts_path) or path_str == str(
                discovery_system.project_scripts_path / "test-script",
            )

        with patch("pathlib.Path.exists", mock_exists):
            with patch.object(discovery_system, "_create_script_definition", return_value=mock_script):
                result = discovery_system._search_project_scripts("test-script")

                assert result == mock_script

    def test_search_project_scripts_directory_not_exists(self, discovery_system):
        """Test searching when project directory doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = discovery_system._search_project_scripts("test-script")

            assert result is None

    def test_search_user_scripts_success(self, discovery_system):
        """Test searching for script in user directory."""
        mock_script = Mock(spec=ScriptDefinition)

        def mock_exists(self):
            path_str = str(self)
            # Allow directory to exist
            if path_str == str(discovery_system.user_scripts_path):
                return True
            # Allow specific script file to exist
            return path_str == str(discovery_system.user_scripts_path / "test-script.py")

        with patch("pathlib.Path.exists", mock_exists):
            with patch.object(discovery_system, "_create_script_definition", return_value=mock_script):
                result = discovery_system._search_user_scripts("test-script")

                assert result == mock_script

    def test_search_builtin_scripts(self, discovery_system):
        """Test searching for built-in scripts (currently returns None)."""
        result = discovery_system._search_builtin_scripts("test-script")
        assert result is None

    def test_create_script_definition_python(self, discovery_system):
        """Test creating a script definition for Python script."""
        mock_stat = Mock()
        mock_stat.st_mtime = 1234567890.0

        mock_path = Mock(spec=Path)
        mock_path.suffix = ".py"
        mock_path.read_text.return_value = "#!/usr/bin/env python\n# Test script\nprint('hello')"
        mock_path.stat.return_value = mock_stat

        with patch("os.access", return_value=True):
            with patch.object(discovery_system, "_parse_script_metadata") as mock_parse:
                script = discovery_system._create_script_definition("test-script", mock_path, "project")

                assert script.script_id == "test-script"
                assert script.name == "Test Script"
                assert script.script_type == "python"
                assert script.is_executable is True
                assert script.source_type == "project"
                assert script.content is not None
                mock_parse.assert_called_once_with(script)

    def test_create_script_definition_shell(self, discovery_system):
        """Test creating a script definition for shell script."""
        mock_stat = Mock()
        mock_stat.st_mtime = 1234567890.0

        mock_path = Mock(spec=Path)
        mock_path.suffix = ".sh"
        mock_path.read_text.return_value = "#!/bin/bash\n# Deploy script\necho 'deploying'"
        mock_path.stat.return_value = mock_stat

        with patch("os.access", return_value=False), patch.object(discovery_system, "_parse_script_metadata"):
            script = discovery_system._create_script_definition("deploy", mock_path, "user")

            assert script.script_type == "shell"
            assert script.is_executable is False
            assert script.source_type == "user"

    def test_create_script_definition_with_description_extraction(self, discovery_system):
        """Test creating script definition with description extracted from comments."""
        content = """#!/usr/bin/env python
# This is a comprehensive testing script that validates all components
# Version: 2.1.0
import sys
print('test')
"""

        mock_stat = Mock()
        mock_stat.st_mtime = 1234567890.0

        mock_path = Mock(spec=Path)
        mock_path.suffix = ".py"
        mock_path.read_text.return_value = content
        mock_path.stat.return_value = mock_stat

        with patch("os.access", return_value=True), patch.object(discovery_system, "_parse_script_metadata"):
            script = discovery_system._create_script_definition("test", mock_path, "project")

            assert "comprehensive testing script" in script.description
            assert script.version == "2.1.0"

    def test_create_script_definition_content_read_error(self, discovery_system):
        """Test creating script definition when content read fails."""
        mock_stat = Mock()
        mock_stat.st_mtime = 1234567890.0

        mock_path = Mock(spec=Path)
        mock_path.suffix = ".py"
        mock_path.read_text.side_effect = OSError("Read error")
        mock_path.stat.return_value = mock_stat

        with patch("os.access", return_value=True):
            script = discovery_system._create_script_definition("test", mock_path, "project")

            assert script.content is None
            assert script.version is None

    def test_parse_script_metadata_shebang_detection(self, discovery_system):
        """Test parsing script metadata with shebang detection."""
        script = ScriptDefinition(
            script_id="test",
            name="Test",
            description="Test",
            file_path=Path("/test"),
            source_type="project",
            script_type="other",
            content="#!/usr/bin/env python3\n# Test script\nprint('hello')",
        )

        discovery_system._parse_script_metadata(script)

        assert script.script_type == "python"

    def test_parse_script_metadata_dependencies_and_parameters(self, discovery_system):
        """Test parsing dependencies and parameters from script content."""
        script = ScriptDefinition(
            script_id="test",
            name="Test",
            description="Test",
            file_path=Path("/test"),
            source_type="project",
            script_type="python",
            content="""#!/usr/bin/env python
# Depends: requests, yaml, click
# Params: --config --verbose --dry-run
import requests
""",
        )

        discovery_system._parse_script_metadata(script)

        assert "requests" in script.dependencies
        assert "yaml" in script.dependencies
        assert "click" in script.dependencies
        assert "--config" in script.parameters
        assert "--verbose" in script.parameters
        assert "--dry-run" in script.parameters

    def test_parse_script_metadata_auto_categorization(self, discovery_system):
        """Test automatic categorization based on script ID."""
        script = ScriptDefinition(
            script_id="setup-environment",
            name="Setup Environment",
            description="Test",
            file_path=Path("/test"),
            source_type="project",
            script_type="shell",
            content="#!/bin/bash\necho 'setting up'",
        )

        discovery_system._parse_script_metadata(script)

        assert script.category == "setup"

    def test_refresh_scripts_cache(self, discovery_system):
        """Test refreshing the scripts cache."""
        # Mock file paths
        project_file1 = Mock(spec=Path)
        project_file1.is_file.return_value = True
        project_file1.name = "script1.py"
        project_file1.stem = "script1"
        project_file1.suffix = ".py"

        user_file1 = Mock(spec=Path)
        user_file1.is_file.return_value = True
        user_file1.name = "script2.sh"
        user_file1.stem = "script2"
        user_file1.suffix = ".sh"

        # Mock scripts
        mock_script1 = Mock(spec=ScriptDefinition)
        mock_script2 = Mock(spec=ScriptDefinition)

        def mock_exists(self):
            return True

        def mock_iterdir(self):
            if str(self) == str(discovery_system.project_scripts_path):
                return [project_file1]
            if str(self) == str(discovery_system.user_scripts_path):
                return [user_file1]
            return []

        def mock_parents_check(file_path):
            if file_path == project_file1:
                return [discovery_system.project_scripts_path]
            return []

        with patch("pathlib.Path.exists", mock_exists), patch("pathlib.Path.iterdir", mock_iterdir):
            with patch.object(discovery_system, "_create_script_definition") as mock_create:
                mock_create.side_effect = [mock_script1, mock_script2]

                # Mock the parents check
                project_file1.parents = [discovery_system.project_scripts_path]
                user_file1.parents = []

                discovery_system._refresh_scripts_cache()

                assert len(discovery_system._scripts_cache) == 2
                assert discovery_system._scripts_cache["script1"] == mock_script1
                assert discovery_system._scripts_cache["script2"] == mock_script2
                assert discovery_system._cache_timestamp is not None

    def test_get_discovery_status(self, discovery_system):
        """Test getting discovery status information."""
        # Mock scripts
        mock_project_script = Mock(spec=ScriptDefinition)
        mock_project_script.source_type = "project"
        mock_project_script.script_type = "python"
        mock_project_script.category = "setup"
        mock_project_script.is_executable = True

        mock_user_script = Mock(spec=ScriptDefinition)
        mock_user_script.source_type = "user"
        mock_user_script.script_type = "shell"
        mock_user_script.category = "validation"
        mock_user_script.is_executable = False

        discovery_system._scripts_cache = {
            "project-script": mock_project_script,
            "user-script": mock_user_script,
        }
        discovery_system._cache_timestamp = utc_now() - timedelta(seconds=100)

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch.object(
                discovery_system,
                "get_available_scripts",
                return_value=["project-script", "user-script"],
            ),
        ):
            status = discovery_system.get_discovery_status()

            assert status["cached_scripts_count"] == 2
            assert status["executable_scripts_count"] == 1
            assert status["scripts_by_source"]["project"] == 1
            assert status["scripts_by_source"]["user"] == 1
            assert status["scripts_by_type"]["python"] == 1
            assert status["scripts_by_type"]["shell"] == 1
            assert status["scripts_by_category"]["setup"] == 1
            assert status["scripts_by_category"]["validation"] == 1
            assert "setup" in status["supported_categories"]
            assert "python" in status["supported_types"]


class TestScriptsManager:
    """Test suite for ScriptsManager class."""

    @pytest.fixture
    def mock_project_root(self):
        """Create a mock project root path."""
        return Path("/test/project")

    @pytest.fixture
    def scripts_manager(self, mock_project_root):
        """Create a ScriptsManager instance for testing."""
        return ScriptsManager(project_root=mock_project_root)

    def test_initialization(self, mock_project_root):
        """Test ScriptsManager initialization."""
        manager = ScriptsManager(project_root=mock_project_root)

        assert isinstance(manager.discovery_system, ScriptsDiscoverySystem)
        assert manager.discovery_system.project_root == mock_project_root

    def test_execute_script_not_found(self, scripts_manager):
        """Test executing a script that doesn't exist."""
        with (
            patch.object(scripts_manager.discovery_system, "get_script", return_value=None),
            patch.object(
                scripts_manager.discovery_system,
                "get_available_scripts",
                return_value=["script1", "script2"],
            ),
        ):
            result = scripts_manager.execute_script("nonexistent")

            assert result["success"] is False
            assert "not found" in result["error"]
            assert "available_scripts" in result

    def test_execute_script_dry_run(self, scripts_manager):
        """Test executing a script in dry-run mode."""
        mock_script = Mock(spec=ScriptDefinition)
        mock_script.name = "Test Script"
        mock_script.source_type = "project"
        mock_script.script_type = "python"
        mock_script.is_executable = True

        with patch.object(scripts_manager.discovery_system, "get_script", return_value=mock_script):
            result = scripts_manager.execute_script("test-script", ["--verbose"], dry_run=True)

            assert result["success"] is True
            assert result["script_id"] == "test-script"
            assert "dry-run mode" in result["message"]
            assert result["source"] == "project"
            assert result["type"] == "python"
            assert result["executable"] is True
            assert result["parameters"] == ["--verbose"]

    def test_execute_script_real_execution_blocked(self, scripts_manager):
        """Test that real script execution is blocked for security."""
        mock_script = Mock(spec=ScriptDefinition)

        with patch.object(scripts_manager.discovery_system, "get_script", return_value=mock_script):
            result = scripts_manager.execute_script("test-script", dry_run=False)

            assert result["success"] is False
            assert "not implemented for security reasons" in result["error"]
            assert "dry_run=True" in result["recommendation"]

    def test_get_maintenance_scripts(self, scripts_manager):
        """Test getting maintenance scripts."""
        mock_scripts = [Mock(spec=ScriptDefinition), Mock(spec=ScriptDefinition)]

        with patch.object(scripts_manager.discovery_system, "get_scripts_by_category", return_value=mock_scripts):
            scripts = scripts_manager.get_maintenance_scripts()

            assert scripts == mock_scripts
            scripts_manager.discovery_system.get_scripts_by_category.assert_called_once_with("maintenance")

    def test_get_setup_scripts(self, scripts_manager):
        """Test getting setup scripts."""
        mock_scripts = [Mock(spec=ScriptDefinition)]

        with patch.object(scripts_manager.discovery_system, "get_scripts_by_category", return_value=mock_scripts):
            scripts = scripts_manager.get_setup_scripts()

            assert scripts == mock_scripts
            scripts_manager.discovery_system.get_scripts_by_category.assert_called_once_with("setup")

    def test_get_validation_scripts(self, scripts_manager):
        """Test getting validation scripts."""
        mock_scripts = [Mock(spec=ScriptDefinition)]

        with patch.object(scripts_manager.discovery_system, "get_scripts_by_category", return_value=mock_scripts):
            scripts = scripts_manager.get_validation_scripts()

            assert scripts == mock_scripts
            scripts_manager.discovery_system.get_scripts_by_category.assert_called_once_with("validation")


class TestScriptsManagerIntegration:
    """Integration tests for ScriptsManager."""

    def test_full_workflow_with_mocked_filesystem(self):
        """Test the complete workflow with mocked filesystem."""
        project_root = Path("/test/project")
        manager = ScriptsManager(project_root=project_root)

        # Mock filesystem structure
        project_setup_file = project_root / ".claude" / "scripts" / "setup.py"
        user_validate_file = Path.home() / ".claude" / "scripts" / "validate.sh"

        setup_content = """#!/usr/bin/env python
# Setup script for the project
# Depends: click, requests
# Params: --environment --verbose
import click
print('Setting up project')
"""

        validate_content = """#!/bin/bash
# Validation script
echo "Validating configuration"
"""

        def mock_exists(self):
            path_str = str(self)
            return (
                path_str == str(manager.discovery_system.project_scripts_path)
                or path_str == str(manager.discovery_system.user_scripts_path)
                or path_str == str(project_setup_file)
                or path_str == str(user_validate_file)
            )

        def mock_iterdir(self):
            if str(self) == str(manager.discovery_system.project_scripts_path):
                mock_file = Mock(spec=Path)
                mock_file.is_file.return_value = True
                mock_file.name = "setup.py"
                mock_file.stem = "setup"
                mock_file.suffix = ".py"
                # Create a mock parents object that supports 'in' operator
                mock_parents = Mock()
                mock_parents.__contains__ = lambda self, item: item == manager.discovery_system.project_scripts_path
                mock_parents.__iter__ = lambda self: iter([manager.discovery_system.project_scripts_path])
                mock_file.parents = mock_parents
                # Add stat method to mock file
                mock_stat_result = Mock()
                mock_stat_result.st_mtime = 1234567890.0
                mock_file.stat.return_value = mock_stat_result
                mock_file.read_text.return_value = setup_content
                return [mock_file]
            if str(self) == str(manager.discovery_system.user_scripts_path):
                mock_file = Mock(spec=Path)
                mock_file.is_file.return_value = True
                mock_file.name = "validate.sh"
                mock_file.stem = "validate"
                mock_file.suffix = ".sh"
                # Create a mock parents object that supports 'in' operator
                mock_parents_user = Mock()
                mock_parents_user.__contains__ = lambda self, item: False  # No parents for user scripts
                mock_parents_user.__iter__ = lambda self: iter([])
                mock_file.parents = mock_parents_user
                # Add stat method to mock file
                mock_stat_result = Mock()
                mock_stat_result.st_mtime = 1234567890.0
                mock_file.stat.return_value = mock_stat_result
                mock_file.read_text.return_value = validate_content
                return [mock_file]
            return []

        def mock_stat(self):
            mock_stat_result = Mock()
            mock_stat_result.st_mtime = 1234567890.0
            return mock_stat_result

        def mock_read_text(self, encoding="utf-8"):
            if "setup" in str(self):
                return setup_content
            if "validate" in str(self):
                return validate_content
            return ""

        with patch("pathlib.Path.exists", mock_exists), patch("pathlib.Path.iterdir", mock_iterdir):
            with patch("pathlib.Path.stat", mock_stat):
                with patch("pathlib.Path.read_text", mock_read_text):
                    with patch("os.access", return_value=True):
                        # Test getting available scripts
                        scripts = manager.discovery_system.get_available_scripts()
                        assert set(scripts) == {"setup", "validate"}

                        # Test getting specific scripts
                        setup_script = manager.discovery_system.get_script("setup")
                        assert setup_script is not None
                        assert setup_script.source_type == "project"
                        assert setup_script.script_type == "python"
                        assert setup_script.category == "setup"
                        assert "click" in setup_script.dependencies
                        assert "--environment" in setup_script.parameters

                        validate_script = manager.discovery_system.get_script("validate")
                        assert validate_script is not None
                        assert validate_script.source_type == "user"
                        assert validate_script.script_type == "shell"

                        # Test categorized retrieval
                        setup_scripts = manager.get_setup_scripts()
                        assert len(setup_scripts) == 1
                        assert setup_scripts[0].script_id == "setup"

                        validation_scripts = manager.get_validation_scripts()
                        assert len(validation_scripts) == 1
                        assert validation_scripts[0].script_id == "validate"

                        # Test script execution (dry run)
                        result = manager.execute_script("setup", ["--environment", "dev"], dry_run=True)
                        assert result["success"] is True
                        assert "dry-run mode" in result["message"]


class TestScriptsModuleExports:
    """Test module exports and imports."""

    def test_module_exports(self):
        """Test that the module exports the expected classes."""
        from src.scripts.discovery import ScriptDefinition, ScriptsDiscoverySystem, ScriptsManager, __all__

        assert __all__ == ["ScriptDefinition", "ScriptsDiscoverySystem", "ScriptsManager"]
        assert ScriptDefinition is not None
        assert ScriptsDiscoverySystem is not None
        assert ScriptsManager is not None
