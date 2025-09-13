"""
Comprehensive tests for Standards Discovery System.

This test suite provides comprehensive coverage for the StandardsDiscoverySystem
and StandardsManager classes, testing standards discovery, caching, content loading,
and compliance validation across project and user standard directories.
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.standards.discovery import StandardDefinition, StandardsDiscoverySystem, StandardsManager
from src.utils.datetime_compat import utc_now


class TestStandardDefinition:
    """Test suite for StandardDefinition dataclass."""

    def test_standard_definition_creation(self):
        """Test creating a StandardDefinition instance."""
        file_path = Path("/test/standard.md")
        last_updated = utc_now()

        standard = StandardDefinition(
            standard_id="test-standard",
            name="Test Standard",
            description="A test standard",
            file_path=file_path,
            source_type="project",
            content="# Test Content",
            version="1.0.0",
            last_updated=last_updated,
        )

        assert standard.standard_id == "test-standard"
        assert standard.name == "Test Standard"
        assert standard.description == "A test standard"
        assert standard.file_path == file_path
        assert standard.source_type == "project"
        assert standard.content == "# Test Content"
        assert standard.version == "1.0.0"
        assert standard.last_updated == last_updated

    def test_standard_definition_defaults(self):
        """Test StandardDefinition with default values."""
        file_path = Path("/test/standard.md")

        standard = StandardDefinition(
            standard_id="test-standard",
            name="Test Standard",
            description="A test standard",
            file_path=file_path,
            source_type="project",
        )

        assert standard.content is None
        assert standard.version is None
        assert standard.last_updated is None


class TestStandardsDiscoverySystem:
    """Test suite for StandardsDiscoverySystem class."""

    @pytest.fixture
    def mock_project_root(self):
        """Create a mock project root path."""
        return Path("/test/project")

    @pytest.fixture
    def discovery_system(self, mock_project_root):
        """Create a StandardsDiscoverySystem instance for testing."""
        return StandardsDiscoverySystem(project_root=mock_project_root)

    def test_initialization_with_project_root(self, mock_project_root):
        """Test StandardsDiscoverySystem initialization with project root."""
        system = StandardsDiscoverySystem(project_root=mock_project_root)

        assert system.project_root == mock_project_root
        assert system.project_standards_path == mock_project_root / ".claude" / "standards"
        assert system.user_standards_path == Path.home() / ".claude" / "standards"
        assert system._standards_cache == {}
        assert system._cache_timestamp is None
        assert system._cache_ttl_seconds == 300

    def test_initialization_without_project_root(self):
        """Test StandardsDiscoverySystem initialization without project root."""
        with patch("pathlib.Path.cwd", return_value=Path("/current/dir")):
            system = StandardsDiscoverySystem()

            assert system.project_root == Path("/current/dir")
            assert system.project_standards_path == Path("/current/dir") / ".claude" / "standards"

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

    def test_get_available_standards_empty_cache(self, discovery_system):
        """Test getting available standards when cache is empty."""
        with (
            patch.object(discovery_system, "_should_refresh_cache", return_value=True),
            patch.object(discovery_system, "_refresh_standards_cache") as mock_refresh,
        ):
            discovery_system._standards_cache = {}

            standards = discovery_system.get_available_standards()

            assert standards == []
            mock_refresh.assert_called_once()

    def test_get_available_standards_with_cache(self, discovery_system):
        """Test getting available standards when cache has standards."""
        mock_standard1 = Mock(spec=StandardDefinition)
        mock_standard2 = Mock(spec=StandardDefinition)

        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._standards_cache = {
                "standard1": mock_standard1,
                "standard2": mock_standard2,
            }

            standards = discovery_system.get_available_standards()

            assert set(standards) == {"standard1", "standard2"}

    def test_get_available_standards_force_refresh(self, discovery_system):
        """Test getting available standards with forced refresh."""
        with patch.object(discovery_system, "_refresh_standards_cache") as mock_refresh:
            discovery_system._standards_cache = {"existing": Mock()}

            discovery_system.get_available_standards(refresh_cache=True)

            mock_refresh.assert_called_once()

    def test_get_standard_exists(self, discovery_system):
        """Test getting a standard that exists in cache."""
        mock_standard = Mock(spec=StandardDefinition)

        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._standards_cache = {"test-standard": mock_standard}

            result = discovery_system.get_standard("test-standard")

            assert result == mock_standard

    def test_get_standard_not_exists(self, discovery_system):
        """Test getting a standard that doesn't exist."""
        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            discovery_system._standards_cache = {}

            result = discovery_system.get_standard("nonexistent")

            assert result is None

    def test_get_standard_with_cache_refresh(self, discovery_system):
        """Test getting a standard that triggers cache refresh."""
        mock_standard = Mock(spec=StandardDefinition)

        with (
            patch.object(discovery_system, "_should_refresh_cache", return_value=True),
            patch.object(discovery_system, "_refresh_standards_cache") as mock_refresh,
        ):
            discovery_system._standards_cache = {"test-standard": mock_standard}

            result = discovery_system.get_standard("test-standard")

            assert result == mock_standard
            mock_refresh.assert_called_once()

    def test_get_standard_content_success(self, discovery_system):
        """Test getting standard content successfully."""
        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = "# Standard Content"

        mock_standard = StandardDefinition(
            standard_id="test",
            name="Test",
            description="Test standard",
            file_path=mock_path,
            source_type="project",
        )

        with patch.object(discovery_system, "get_standard", return_value=mock_standard):
            content = discovery_system.get_standard_content("test")

            assert content == "# Standard Content"
            mock_path.read_text.assert_called_once_with(encoding="utf-8")
            assert mock_standard.content == "# Standard Content"

    def test_get_standard_content_cached(self, discovery_system):
        """Test getting standard content that's already cached."""
        mock_path = Mock(spec=Path)

        mock_standard = StandardDefinition(
            standard_id="test",
            name="Test",
            description="Test standard",
            file_path=mock_path,
            source_type="project",
            content="# Cached Content",
        )

        with patch.object(discovery_system, "get_standard", return_value=mock_standard):
            content = discovery_system.get_standard_content("test")

            assert content == "# Cached Content"
            mock_path.read_text.assert_not_called()

    def test_get_standard_content_standard_not_found(self, discovery_system):
        """Test getting standard content when standard doesn't exist."""
        with patch.object(discovery_system, "get_standard", return_value=None):
            content = discovery_system.get_standard_content("nonexistent")

            assert content is None

    def test_get_standard_content_file_read_error(self, discovery_system):
        """Test getting standard content when file read fails."""
        mock_path = Mock(spec=Path)
        mock_path.read_text.side_effect = OSError("File not found")

        mock_standard = StandardDefinition(
            standard_id="test",
            name="Test",
            description="Test standard",
            file_path=mock_path,
            source_type="project",
        )

        with patch.object(discovery_system, "get_standard", return_value=mock_standard):
            content = discovery_system.get_standard_content("test")

            assert content is None

    def test_discover_standard_from_project(self, discovery_system):
        """Test discovering a standard from project source."""
        mock_standard = Mock(spec=StandardDefinition)

        with (
            patch.object(discovery_system, "_search_project_standards", return_value=mock_standard),
            patch.object(discovery_system, "_search_user_standards", return_value=None),
            patch.object(discovery_system, "_search_default_standards", return_value=None),
        ):
            result = discovery_system.discover_standard("test-standard")

            assert result == mock_standard
            assert result.source_type == "project"

    def test_discover_standard_from_user_fallback(self, discovery_system):
        """Test discovering a standard from user source as fallback."""
        mock_standard = Mock(spec=StandardDefinition)

        with patch.object(discovery_system, "_search_project_standards", return_value=None):
            with patch.object(discovery_system, "_search_user_standards", return_value=mock_standard):
                with patch.object(discovery_system, "_search_default_standards", return_value=None):
                    result = discovery_system.discover_standard("test-standard")

                    assert result == mock_standard
                    assert result.source_type == "user"

    def test_discover_standard_not_found(self, discovery_system):
        """Test discovering a standard that doesn't exist anywhere."""
        with patch.object(discovery_system, "_search_project_standards", return_value=None):
            with patch.object(discovery_system, "_search_user_standards", return_value=None):
                with patch.object(discovery_system, "_search_default_standards", return_value=None):
                    result = discovery_system.discover_standard("nonexistent")

                    assert result is None

    def test_discover_standard_with_search_error(self, discovery_system):
        """Test discovering a standard when search methods raise exceptions."""
        mock_standard = Mock(spec=StandardDefinition)

        with (
            patch.object(
                discovery_system,
                "_search_project_standards",
                side_effect=Exception("Project search failed"),
            ),
            patch.object(discovery_system, "_search_user_standards", return_value=mock_standard),
        ):
            with patch.object(discovery_system, "_search_default_standards", return_value=None):
                result = discovery_system.discover_standard("test-standard")

                assert result == mock_standard
                assert result.source_type == "user"

    def test_search_project_standards_success(self, discovery_system):
        """Test searching for standard in project directory."""
        mock_standard = Mock(spec=StandardDefinition)

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(discovery_system, "_create_standard_definition", return_value=mock_standard):
                result = discovery_system._search_project_standards("test-standard")

                assert result == mock_standard

    def test_search_project_standards_directory_not_exists(self, discovery_system):
        """Test searching for standard when project directory doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = discovery_system._search_project_standards("test-standard")

            assert result is None

    def test_search_project_standards_file_not_exists(self, discovery_system):
        """Test searching for standard when project file doesn't exist."""

        def mock_exists(self):
            # Directory exists, but file doesn't
            return str(self) == str(discovery_system.project_standards_path)

        with patch("pathlib.Path.exists", mock_exists):
            result = discovery_system._search_project_standards("test-standard")

            assert result is None

    def test_search_user_standards_success(self, discovery_system):
        """Test searching for standard in user directory."""
        mock_standard = Mock(spec=StandardDefinition)

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(discovery_system, "_create_standard_definition", return_value=mock_standard):
                result = discovery_system._search_user_standards("test-standard")

                assert result == mock_standard

    def test_search_user_standards_directory_not_exists(self, discovery_system):
        """Test searching for standard when user directory doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = discovery_system._search_user_standards("test-standard")

            assert result is None

    def test_search_default_standards(self, discovery_system):
        """Test searching for default standards (currently returns None)."""
        result = discovery_system._search_default_standards("test-standard")
        assert result is None

    def test_create_standard_definition_simple(self, discovery_system):
        """Test creating a standard definition without YAML frontmatter."""
        mock_stat = Mock()
        mock_stat.st_mtime = 1234567890.0

        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = "# Simple Standard\nContent here"
        mock_path.stat.return_value = mock_stat

        standard = discovery_system._create_standard_definition("test-standard", mock_path, "project")

        assert standard.standard_id == "test-standard"
        assert standard.name == "Test Standard"  # Converted from kebab-case
        assert standard.description == "Test Standard development standard"
        assert standard.file_path == mock_path
        assert standard.source_type == "project"
        assert standard.content == "# Simple Standard\nContent here"
        assert standard.version is None
        assert standard.last_updated == datetime.fromtimestamp(1234567890.0, tz=timezone.utc)

    def test_create_standard_definition_with_yaml_frontmatter(self, discovery_system):
        """Test creating a standard definition with YAML frontmatter."""
        content_with_frontmatter = "---\ntitle: Custom Title\ndescription: Custom description\nversion: 2.0.0\n---\n# Standard Content\nThis is the content."

        mock_stat = Mock()
        mock_stat.st_mtime = 1234567890.0

        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = content_with_frontmatter
        mock_path.stat.return_value = mock_stat

        with patch("yaml.safe_load") as mock_yaml:
            mock_yaml.return_value = {
                "title": "Custom Title",
                "description": "Custom description",
                "version": "2.0.0",
            }

            standard = discovery_system._create_standard_definition("test-standard", mock_path, "project")

            assert standard.name == "Custom Title"
            assert standard.description == "Custom description"
            assert standard.version == "2.0.0"

    def test_create_standard_definition_yaml_parse_error(self, discovery_system):
        """Test creating a standard definition when YAML parsing fails."""
        content_with_bad_yaml = """---
invalid: yaml: content
---
# Standard Content
"""

        mock_stat = Mock()
        mock_stat.st_mtime = 1234567890.0

        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = content_with_bad_yaml
        mock_path.stat.return_value = mock_stat

        with patch("yaml.safe_load", side_effect=Exception("YAML parse error")):
            standard = discovery_system._create_standard_definition("test-standard", mock_path, "project")

            # Should fall back to default values
            assert standard.name == "Test Standard"
            assert standard.description == "Test Standard development standard"
            assert standard.version is None

    def test_create_standard_definition_file_read_error(self, discovery_system):
        """Test creating a standard definition when file read fails."""
        mock_path = Mock(spec=Path)
        mock_path.read_text.side_effect = OSError("File read error")

        with pytest.raises(IOError, match="File read error"):
            discovery_system._create_standard_definition("test-standard", mock_path, "project")

    def test_refresh_standards_cache(self, discovery_system):
        """Test refreshing the standards cache."""
        # Mock file paths
        project_file1 = Mock(spec=Path)
        project_file1.stem = "standard1"
        project_file2 = Mock(spec=Path)
        project_file2.stem = "standard2"

        user_file1 = Mock(spec=Path)
        user_file1.stem = "standard3"
        user_file2 = Mock(spec=Path)
        user_file2.stem = "standard1"  # Same as project - should be overridden

        # Mock standards
        mock_standard1 = Mock(spec=StandardDefinition)
        mock_standard2 = Mock(spec=StandardDefinition)
        mock_standard3 = Mock(spec=StandardDefinition)

        def mock_exists(self):
            return True  # Both directories exist

        def mock_glob(self, pattern):
            if str(self) == str(discovery_system.project_standards_path) and pattern == "*.md":
                return [project_file1, project_file2]
            if str(self) == str(discovery_system.user_standards_path) and pattern == "*.md":
                return [user_file1, user_file2]
            return []

        def mock_discover_standard(standard_id):
            if standard_id == "standard1":
                return mock_standard1
            if standard_id == "standard2":
                return mock_standard2
            if standard_id == "standard3":
                return mock_standard3
            return None

        with patch("pathlib.Path.exists", mock_exists), patch("pathlib.Path.glob", mock_glob):
            with patch.object(discovery_system, "discover_standard", side_effect=mock_discover_standard):
                discovery_system._refresh_standards_cache()

                assert len(discovery_system._standards_cache) == 3
                assert discovery_system._standards_cache["standard1"] == mock_standard1
                assert discovery_system._standards_cache["standard2"] == mock_standard2
                assert discovery_system._standards_cache["standard3"] == mock_standard3
                assert discovery_system._cache_timestamp is not None

    def test_refresh_standards_cache_no_directories(self, discovery_system):
        """Test refreshing cache when no directories exist."""
        with patch("pathlib.Path.exists", return_value=False):
            discovery_system._refresh_standards_cache()

            assert discovery_system._standards_cache == {}
            assert discovery_system._cache_timestamp is not None

    def test_get_discovery_status(self, discovery_system):
        """Test getting discovery status information."""
        discovery_system._standards_cache = {"standard1": Mock(), "standard2": Mock()}
        discovery_system._cache_timestamp = utc_now() - timedelta(seconds=100)

        with patch("pathlib.Path.exists", return_value=True):
            with patch.object(discovery_system, "get_available_standards", return_value=["standard1", "standard2"]):
                status = discovery_system.get_discovery_status()

                expected_project_path = str(discovery_system.project_standards_path)
                expected_user_path = str(discovery_system.user_standards_path)

                assert status["project_standards_path"] == expected_project_path
                assert status["user_standards_path"] == expected_user_path
                assert status["project_standards_available"] is True
                assert status["user_standards_available"] is True
                assert status["cached_standards_count"] == 2
                assert abs(status["cache_age_seconds"] - 100) < 1  # Allow small timing differences
                assert status["available_standards"] == ["standard1", "standard2"]

    def test_get_discovery_status_no_cache_timestamp(self, discovery_system):
        """Test getting discovery status when no cache timestamp is set."""
        discovery_system._cache_timestamp = None

        with patch("pathlib.Path.exists", return_value=False):
            with patch.object(discovery_system, "get_available_standards", return_value=[]):
                status = discovery_system.get_discovery_status()

                assert status["cache_age_seconds"] is None


class TestStandardsManager:
    """Test suite for StandardsManager class."""

    @pytest.fixture
    def mock_project_root(self):
        """Create a mock project root path."""
        return Path("/test/project")

    @pytest.fixture
    def standards_manager(self, mock_project_root):
        """Create a StandardsManager instance for testing."""
        return StandardsManager(project_root=mock_project_root)

    def test_initialization(self, mock_project_root):
        """Test StandardsManager initialization."""
        manager = StandardsManager(project_root=mock_project_root)

        assert isinstance(manager.discovery_system, StandardsDiscoverySystem)
        assert manager.discovery_system.project_root == mock_project_root

    def test_initialization_without_project_root(self):
        """Test StandardsManager initialization without project root."""
        with patch("pathlib.Path.cwd", return_value=Path("/current/dir")):
            manager = StandardsManager()

            assert manager.discovery_system.project_root == Path("/current/dir")

    def test_get_linting_standard(self, standards_manager):
        """Test getting linting standard content."""
        with patch.object(
            standards_manager.discovery_system,
            "get_standard_content",
            return_value="# Linting Standard",
        ):
            content = standards_manager.get_linting_standard()

            assert content == "# Linting Standard"
            standards_manager.discovery_system.get_standard_content.assert_called_once_with("linting")

    def test_get_python_standard(self, standards_manager):
        """Test getting Python standard content."""
        with patch.object(standards_manager.discovery_system, "get_standard_content", return_value="# Python Standard"):
            content = standards_manager.get_python_standard()

            assert content == "# Python Standard"
            standards_manager.discovery_system.get_standard_content.assert_called_once_with("python")

    def test_get_git_workflow_standard(self, standards_manager):
        """Test getting Git workflow standard content."""
        with patch.object(standards_manager.discovery_system, "get_standard_content", return_value="# Git Workflow"):
            content = standards_manager.get_git_workflow_standard()

            assert content == "# Git Workflow"
            standards_manager.discovery_system.get_standard_content.assert_called_once_with("git-workflow")

    def test_get_security_standard(self, standards_manager):
        """Test getting security standard content."""
        with patch.object(
            standards_manager.discovery_system,
            "get_standard_content",
            return_value="# Security Standard",
        ):
            content = standards_manager.get_security_standard()

            assert content == "# Security Standard"
            standards_manager.discovery_system.get_standard_content.assert_called_once_with("security")

    def test_validate_project_compliance_default_standards(self, standards_manager):
        """Test validating project compliance with default standards."""
        mock_standards = {
            "linting": Mock(spec=StandardDefinition),
            "python": Mock(spec=StandardDefinition),
            "git-workflow": None,  # Missing standard
            "security": Mock(spec=StandardDefinition),
        }

        def mock_get_standard(standard_id):
            return mock_standards.get(standard_id)

        with patch.object(standards_manager.discovery_system, "get_standard", side_effect=mock_get_standard):
            compliance = standards_manager.validate_project_compliance()

            assert compliance == {
                "linting": True,
                "python": True,
                "git-workflow": False,
                "security": True,
            }

    def test_validate_project_compliance_custom_standards(self, standards_manager):
        """Test validating project compliance with custom standards."""
        mock_standards = {
            "custom1": Mock(spec=StandardDefinition),
            "custom2": None,  # Missing standard
        }

        def mock_get_standard(standard_id):
            return mock_standards.get(standard_id)

        with patch.object(standards_manager.discovery_system, "get_standard", side_effect=mock_get_standard):
            compliance = standards_manager.validate_project_compliance(["custom1", "custom2"])

            assert compliance == {
                "custom1": True,
                "custom2": False,
            }

    def test_validate_project_compliance_empty_list(self, standards_manager):
        """Test validating project compliance with empty standards list."""
        compliance = standards_manager.validate_project_compliance([])

        assert compliance == {}


class TestStandardsManagerIntegration:
    """Integration tests for StandardsManager."""

    def test_full_workflow_with_mocked_filesystem(self):
        """Test the complete workflow with mocked filesystem."""
        project_root = Path("/test/project")
        manager = StandardsManager(project_root=project_root)

        # Mock filesystem structure
        project_linting_file = project_root / ".claude" / "standards" / "linting.md"
        user_python_file = Path.home() / ".claude" / "standards" / "python.md"

        linting_content = "---\ntitle: Project Linting Standard\ndescription: Project-specific linting rules\nversion: 1.2.0\n---\n# Linting Rules\nUse Black and Ruff."

        python_content = """# Python Standard
Follow PEP 8 guidelines.
"""

        def mock_exists(self):
            path_str = str(self)
            return (
                path_str == str(manager.discovery_system.project_standards_path)
                or path_str == str(manager.discovery_system.user_standards_path)
                or path_str == str(project_linting_file)
                or path_str == str(user_python_file)
            )

        def mock_glob(self, pattern):
            if pattern == "*.md":
                if str(self) == str(manager.discovery_system.project_standards_path):
                    return [project_linting_file]
                if str(self) == str(manager.discovery_system.user_standards_path):
                    return [user_python_file]
            return []

        def mock_stat(self):
            mock_stat_result = Mock()
            mock_stat_result.st_mtime = 1234567890.0
            return mock_stat_result

        def mock_read_text(self, encoding="utf-8"):
            if "linting" in str(self):
                return linting_content
            if "python" in str(self):
                return python_content
            return ""

        with patch("pathlib.Path.exists", mock_exists), patch("pathlib.Path.glob", mock_glob):
            with patch("pathlib.Path.stat", mock_stat):
                with patch("pathlib.Path.read_text", mock_read_text):
                    with patch("yaml.safe_load") as mock_yaml:
                        mock_yaml.return_value = {
                            "title": "Project Linting Standard",
                            "description": "Project-specific linting rules",
                            "version": "1.2.0",
                        }

                        # Test getting available standards
                        standards = manager.discovery_system.get_available_standards()
                        assert set(standards) == {"linting", "python"}

                        # Test getting specific standards
                        linting_standard = manager.discovery_system.get_standard("linting")
                        assert linting_standard is not None
                        assert linting_standard.source_type == "project"
                        assert linting_standard.name == "Project Linting Standard"
                        assert linting_standard.version == "1.2.0"

                        python_standard = manager.discovery_system.get_standard("python")
                        assert python_standard is not None
                        assert python_standard.source_type == "user"

                        # Test getting standard content via manager methods
                        linting_content_result = manager.get_linting_standard()
                        assert "# Linting Rules" in linting_content_result

                        python_content_result = manager.get_python_standard()
                        assert "# Python Standard" in python_content_result

                        # Test compliance validation
                        compliance = manager.validate_project_compliance(["linting", "python", "nonexistent"])
                        assert compliance["linting"] is True
                        assert compliance["python"] is True
                        assert compliance["nonexistent"] is False


class TestStandardsModuleExports:
    """Test module exports and imports."""

    def test_module_exports(self):
        """Test that the module exports the expected classes."""
        from src.standards.discovery import StandardDefinition, StandardsDiscoverySystem, StandardsManager, __all__

        assert __all__ == ["StandardDefinition", "StandardsDiscoverySystem", "StandardsManager"]
        assert StandardDefinition is not None
        assert StandardsDiscoverySystem is not None
        assert StandardsManager is not None
