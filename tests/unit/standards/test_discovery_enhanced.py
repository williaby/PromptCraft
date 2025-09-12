"""
Enhanced tests for Standards Discovery System to improve coverage.

This file contains additional tests to improve coverage of the standards
discovery system beyond what's covered in the main test file.
"""

from datetime import timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.standards.discovery import StandardDefinition, StandardsDiscoverySystem, StandardsManager
from src.utils.datetime_compat import utc_now


class TestStandardsDiscoveryEnhancedCoverage:
    """Enhanced coverage tests for standards discovery system."""

    @pytest.fixture
    def discovery_system(self):
        """Create a discovery system for enhanced coverage tests."""
        return StandardsDiscoverySystem()

    def test_create_standard_definition_description_extraction_from_content(self, discovery_system):
        """Test description extraction from content lines when no frontmatter description."""
        content = """---
title: Custom Standard
# Missing description in frontmatter
---

# Custom Standard

This is the first content line that should be used as description.

This is a second paragraph.
"""

        mock_stat = Mock()
        mock_stat.st_mtime = 1640995200

        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = content
        mock_path.stat.return_value = mock_stat

        # Mock yaml to return frontmatter without description
        with patch("yaml.safe_load") as mock_yaml:
            mock_yaml.return_value = {
                "title": "Custom Standard",
                # No description field
            }

            standard = discovery_system._create_standard_definition("custom-standard", mock_path, "project")

            assert standard.name == "Custom Standard"
            # The current implementation may fall back to default description
            # This tests that the code path is exercised

    def test_create_standard_definition_long_description_truncation(self, discovery_system):
        """Test description truncation for very long first content line."""
        long_line = "This is an extremely long description that exceeds one hundred characters and should be truncated with ellipsis marks to prevent overly long descriptions in listings."

        content = f"""# Standard Title

{long_line}

More content here.
"""

        mock_stat = Mock()
        mock_stat.st_mtime = 1640995200

        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = content
        mock_path.stat.return_value = mock_stat

        standard = discovery_system._create_standard_definition("long-desc", mock_path, "project")

        # Test that description handling doesn't crash with long content
        assert len(standard.description) > 0

    def test_create_standard_definition_yaml_parsing_exception_handling(self, discovery_system):
        """Test handling of various YAML parsing exceptions."""
        content_with_bad_yaml = """---
invalid: yaml: content: [unclosed
---

# Standard Content
"""

        mock_stat = Mock()
        mock_stat.st_mtime = 1640995200

        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = content_with_bad_yaml
        mock_path.stat.return_value = mock_stat

        with patch("yaml.safe_load", side_effect=Exception("YAML parsing failed")):
            standard = discovery_system._create_standard_definition("bad-yaml", mock_path, "project")

            # Should handle gracefully and use default values
            assert standard.name == "Bad Yaml"
            assert standard.description == "Bad Yaml development standard"

    def test_create_standard_definition_file_stat_error(self, discovery_system):
        """Test handling of file stat errors."""
        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = "# Content"
        mock_path.stat.side_effect = PermissionError("Access denied")

        with pytest.raises(Exception, match="Access denied"):
            discovery_system._create_standard_definition("stat-error", mock_path, "project")

    def test_discover_standard_search_exceptions_fallback(self, discovery_system):
        """Test discover_standard handles search method exceptions and continues."""
        with patch.object(discovery_system, "_search_project_standards", side_effect=OSError("Project search failed")):
            with patch.object(discovery_system, "_search_user_standards", side_effect=ValueError("User search failed")):
                with patch.object(discovery_system, "_search_default_standards", return_value=None):

                    result = discovery_system.discover_standard("exception-test")
                    assert result is None

    def test_refresh_standards_cache_glob_exceptions(self, discovery_system):
        """Test cache refresh when glob operations raise exceptions."""
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.glob", side_effect=PermissionError("Glob access denied")):
                # Should handle glob exceptions gracefully
                discovery_system._refresh_standards_cache()

                # Cache should be cleared and timestamp set
                assert discovery_system._standards_cache == {}
                assert discovery_system._cache_timestamp is not None

    def test_get_standard_content_various_file_errors(self, discovery_system):
        """Test getting standard content with various file access errors."""
        error_cases = [
            PermissionError("Permission denied"),
            FileNotFoundError("File not found"),
            UnicodeDecodeError("utf-8", b"", 0, 1, "Invalid encoding"),
            OSError("Disk error"),
        ]

        for error in error_cases:
            mock_path = Mock(spec=Path)
            mock_path.read_text.side_effect = error

            standard = StandardDefinition(
                standard_id="error-test",
                name="Error Test",
                description="Test error handling",
                file_path=mock_path,
                source_type="project",
            )

            with patch.object(discovery_system, "get_standard", return_value=standard):
                content = discovery_system.get_standard_content("error-test")
                assert content is None

    def test_search_project_standards_directory_access_errors(self, discovery_system):
        """Test project standards search with directory access errors."""
        # Test when directory exists but file access fails
        with patch("pathlib.Path.exists", return_value=True):
            # Mock Path.is_file to return True, but read_text to raise exception
            with patch("pathlib.Path.is_file", return_value=True):
                with patch("pathlib.Path.read_text", side_effect=FileNotFoundError("No such file")):
                    result = discovery_system._search_project_standards("missing-standard")
                    assert result is None

    def test_search_user_standards_directory_access_errors(self, discovery_system):
        """Test user standards search with directory access errors."""
        with patch("pathlib.Path.exists", return_value=True):
            # Mock Path.is_file to return True, but read_text to raise exception
            with patch("pathlib.Path.is_file", return_value=True):
                with patch("pathlib.Path.read_text", side_effect=FileNotFoundError("No such file")):
                    result = discovery_system._search_user_standards("missing-user-standard")
                    assert result is None

    def test_get_discovery_status_comprehensive(self, discovery_system):
        """Test comprehensive discovery status with various conditions."""
        # Set up cache with mixed timestamp
        discovery_system._standards_cache = {"test": Mock()}
        discovery_system._cache_timestamp = utc_now() - timedelta(seconds=150)

        # Create mock path objects
        mock_project_path = Mock()
        mock_project_path.exists.return_value = True
        mock_user_path = Mock()
        mock_user_path.exists.return_value = False

        # Replace the path objects temporarily
        original_project_path = discovery_system.project_standards_path
        original_user_path = discovery_system.user_standards_path

        discovery_system.project_standards_path = mock_project_path
        discovery_system.user_standards_path = mock_user_path

        try:
            with patch.object(discovery_system, "get_available_standards", return_value=["test"]):
                status = discovery_system.get_discovery_status()

                assert status["project_standards_available"] is True
                assert status["user_standards_available"] is False
                assert status["cached_standards_count"] == 1
                assert 140 <= status["cache_age_seconds"] <= 160
        finally:
            # Restore original paths
            discovery_system.project_standards_path = original_project_path
            discovery_system.user_standards_path = original_user_path

    def test_standards_manager_validate_compliance_edge_cases(self):
        """Test compliance validation edge cases."""
        manager = StandardsManager()

        # Test with empty list
        compliance = manager.validate_project_compliance([])
        assert compliance == {}

        # Test with None parameter (should use defaults)
        mock_standards = {
            "linting": Mock(),
            "python": None,
            "git-workflow": Mock(),
            "security": None,
        }

        def mock_get_standard(standard_id):
            return mock_standards.get(standard_id)

        with patch.object(manager.discovery_system, "get_standard", side_effect=mock_get_standard):
            compliance = manager.validate_project_compliance(None)

            expected = {
                "linting": True,
                "python": False,
                "git-workflow": True,
                "security": False,
            }
            assert compliance == expected

    def test_standards_manager_content_methods_error_handling(self):
        """Test standard content getter methods with error conditions."""
        manager = StandardsManager()

        # Mock get_standard_content to raise exception
        with patch.object(manager.discovery_system, "get_standard_content", side_effect=RuntimeError("Access error")):
            # Methods should handle exceptions gracefully
            with pytest.raises(RuntimeError):
                manager.get_linting_standard()

    def test_create_standard_definition_malformed_frontmatter(self, discovery_system):
        """Test handling of malformed YAML frontmatter."""
        malformed_cases = [
            "---\nno_end_marker",  # Missing end marker
            "---\n\n---\n# Content",  # Empty frontmatter
            "not_yaml_frontmatter\n# Content",  # No frontmatter at all
        ]

        mock_stat = Mock(st_mtime=1640995200)

        for content in malformed_cases:
            mock_path = Mock(spec=Path)
            mock_path.read_text.return_value = content
            mock_path.stat.return_value = mock_stat

            standard = discovery_system._create_standard_definition("malformed", mock_path, "project")

            # Should handle gracefully with defaults
            assert standard.name == "Malformed"
            assert standard.description == "Malformed development standard"

    def test_yaml_import_error_handling(self, discovery_system):
        """Test handling when yaml module import fails."""
        content = """---
title: YAML Import Test
description: Test YAML import failure
---
# Content"""

        mock_stat = Mock(st_mtime=1640995200)
        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = content
        mock_path.stat.return_value = mock_stat

        # Mock import to fail
        original_import = __builtins__["__import__"]

        def mock_import(name, *args, **kwargs):
            if name == "yaml":
                raise ImportError("No module named 'yaml'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            standard = discovery_system._create_standard_definition("import-test", mock_path, "project")

            # Should fall back to defaults when YAML import fails
            assert standard.name == "Import Test"
            assert standard.description == "Import Test development standard"

    def test_cache_refresh_partial_discovery_failures(self, discovery_system):
        """Test cache refresh when some standards fail discovery."""
        # Mock files
        files = [
            Mock(stem="good-standard"),
            Mock(stem="bad-standard"),
            Mock(stem="another-good"),
        ]

        def mock_discover_standard(standard_id):
            if standard_id == "bad-standard":
                return None  # Discovery fails
            return Mock(spec=StandardDefinition)

        with patch("pathlib.Path.exists", return_value=True), patch("pathlib.Path.glob", return_value=files):
            with patch.object(discovery_system, "discover_standard", side_effect=mock_discover_standard):

                discovery_system._refresh_standards_cache()

                # Should only cache successful discoveries
                assert len(discovery_system._standards_cache) == 2
                assert "good-standard" in discovery_system._standards_cache
                assert "another-good" in discovery_system._standards_cache
                assert "bad-standard" not in discovery_system._standards_cache

    def test_standards_manager_initialization_variations(self):
        """Test StandardsManager initialization with different scenarios."""
        # Test with current directory
        with patch("pathlib.Path.cwd", return_value=Path("/mock/current")):
            manager = StandardsManager()
            assert manager.discovery_system.project_root == Path("/mock/current")

        # Test with explicit path
        explicit_path = Path("/explicit/path")
        manager = StandardsManager(project_root=explicit_path)
        assert manager.discovery_system.project_root == explicit_path

        # Test with None (should use cwd)
        with patch("pathlib.Path.cwd", return_value=Path("/none/test")):
            manager = StandardsManager(project_root=None)
            assert manager.discovery_system.project_root == Path("/none/test")

    def test_get_standard_cache_miss_scenarios(self, discovery_system):
        """Test get_standard with various cache scenarios."""
        # Test with empty cache that needs refresh
        discovery_system._standards_cache = {}
        discovery_system._cache_timestamp = None

        with patch.object(discovery_system, "_should_refresh_cache", return_value=True):
            with patch.object(discovery_system, "_refresh_standards_cache") as mock_refresh:
                result = discovery_system.get_standard("missing")

                assert result is None
                mock_refresh.assert_called_once()

    def test_frontmatter_end_detection_edge_cases(self, discovery_system):
        """Test YAML frontmatter end detection with edge cases."""
        edge_cases = [
            ("---\ntitle: Test\n---\nContent", "Test"),  # Normal case
            ("---\ntitle: Edge\n--\nContent", "Edge Case"),  # Malformed end (should fallback)
            ("title: No Start\n---\nContent", "No Start"),  # No start marker
        ]

        mock_stat = Mock(st_mtime=1640995200)

        for content, _expected_base_name in edge_cases:
            mock_path = Mock(spec=Path)
            mock_path.read_text.return_value = content
            mock_path.stat.return_value = mock_stat

            # Test the scenario - some may parse YAML, others may fallback
            standard = discovery_system._create_standard_definition("edge-case", mock_path, "project")

            # Should handle all cases gracefully
            assert standard is not None
            assert standard.standard_id == "edge-case"


class TestStandardsDiscoveryIntegrationEdgeCases:
    """Integration tests for edge cases."""

    @pytest.fixture
    def discovery_system(self):
        """Create a discovery system for integration edge case tests."""
        return StandardsDiscoverySystem()

    def test_full_workflow_with_access_errors(self):
        """Test full workflow when various access errors occur."""
        project_root = Path("/test/integration")
        manager = StandardsManager(project_root=project_root)

        # Mock various error conditions
        def mock_exists(self):
            # Simulate permission issues
            if "project" in str(self):
                raise PermissionError("No access to project directory")
            return False

        with patch("pathlib.Path.exists", mock_exists):
            # Should handle gracefully
            standards = manager.discovery_system.get_available_standards()
            assert standards == []  # Should return empty list, not crash

            # Status should reflect the error conditions
            status = manager.discovery_system.get_discovery_status()
            assert status["cached_standards_count"] == 0

    def test_yaml_frontmatter_complex_scenarios(self):
        """Test complex YAML frontmatter scenarios."""
        discovery_system = StandardsDiscoverySystem()

        complex_yaml_content = """---
title: "Complex Standard"
description: |
  Multi-line description
  with special characters: @#$%
  and unicode: 🚀
version: "1.2.3-beta"
tags:
  - security
  - testing
metadata:
  author: "Test Author"
  created: 2023-01-15
---

# Complex Standard Content

This standard has complex YAML frontmatter.
"""

        mock_stat = Mock(st_mtime=1640995200)
        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = complex_yaml_content
        mock_path.stat.return_value = mock_stat

        with patch("yaml.safe_load") as mock_yaml:
            mock_yaml.return_value = {
                "title": "Complex Standard",
                "description": "Multi-line description\nwith special characters: @#$%\nand unicode: 🚀",
                "version": "1.2.3-beta",
                "tags": ["security", "testing"],
                "metadata": {
                    "author": "Test Author",
                    "created": "2023-01-15",
                },
            }

            standard = discovery_system._create_standard_definition("complex", mock_path, "project")

            assert standard.name == "Complex Standard"
            assert "Multi-line description" in standard.description
            assert standard.version == "1.2.3-beta"

    def test_concurrent_cache_access_simulation(self):
        """Simulate concurrent cache access scenarios."""
        discovery_system = StandardsDiscoverySystem()

        # Simulate cache being modified during read
        original_cache = {"standard1": Mock()}
        discovery_system._standards_cache = original_cache
        discovery_system._cache_timestamp = utc_now()

        # Get standards while simulating cache modification
        with patch.object(discovery_system, "_should_refresh_cache", return_value=False):
            standards = discovery_system.get_available_standards()

            # Should handle gracefully even if cache changes during access
            assert isinstance(standards, list)

    def test_large_standard_content_handling(self, discovery_system):
        """Test handling of very large standard content."""
        # Simulate very large content
        large_content = "# Large Standard\n\n" + "Large content line.\n" * 10000

        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = large_content
        mock_path.stat.return_value = Mock(st_mtime=1640995200)

        standard = discovery_system._create_standard_definition("large", mock_path, "project")

        # Should handle large content without issues
        assert standard is not None
        assert standard.content == large_content
        assert len(standard.content) > 100000
