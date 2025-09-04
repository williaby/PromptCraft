from src.utils.datetime_compat import utc_now


"""
Comprehensive tests for Templates Discovery and Management System.

This test suite provides comprehensive coverage for the TemplatesManager class,
testing template discovery, caching, content loading, and error handling across
both project and user template directories.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

from src.templates import TemplateDefinition, TemplatesManager


class TestTemplateDefinition:
    """Test suite for TemplateDefinition dataclass."""
    
    def test_template_definition_creation(self):
        """Test creating a TemplateDefinition instance."""
        file_path = Path("/test/template.md")
        last_updated = utc_now()
        
        template = TemplateDefinition(
            template_id="test-template",
            name="Test Template",
            description="A test template",
            file_path=file_path,
            source_type="project",
            content="# Test Content",
            template_type="markdown",
            last_updated=last_updated
        )
        
        assert template.template_id == "test-template"
        assert template.name == "Test Template"
        assert template.description == "A test template"
        assert template.file_path == file_path
        assert template.source_type == "project"
        assert template.content == "# Test Content"
        assert template.template_type == "markdown"
        assert template.last_updated == last_updated
    
    def test_template_definition_defaults(self):
        """Test TemplateDefinition with default values."""
        file_path = Path("/test/template.md")
        
        template = TemplateDefinition(
            template_id="test-template",
            name="Test Template",
            description="A test template",
            file_path=file_path,
            source_type="project"
        )
        
        assert template.content is None
        assert template.template_type == "markdown"
        assert template.last_updated is None


class TestTemplatesManager:
    """Test suite for TemplatesManager class."""
    
    @pytest.fixture
    def mock_project_root(self):
        """Create a mock project root path."""
        return Path("/test/project")
    
    @pytest.fixture
    def manager(self, mock_project_root):
        """Create a TemplatesManager instance for testing."""
        return TemplatesManager(project_root=mock_project_root)
    
    def test_initialization_with_project_root(self, mock_project_root):
        """Test TemplatesManager initialization with project root."""
        manager = TemplatesManager(project_root=mock_project_root)
        
        assert manager.project_root == mock_project_root
        assert manager.project_templates_path == mock_project_root / ".claude" / "templates"
        assert manager.user_templates_path == Path.home() / ".claude" / "templates"
        assert manager._templates_cache == {}
    
    def test_initialization_without_project_root(self):
        """Test TemplatesManager initialization without project root."""
        with patch('pathlib.Path.cwd', return_value=Path("/current/dir")):
            manager = TemplatesManager()
            
            assert manager.project_root == Path("/current/dir")
            assert manager.project_templates_path == Path("/current/dir") / ".claude" / "templates"
    
    def test_get_available_templates_empty(self, manager):
        """Test getting available templates when none exist."""
        with patch.object(manager, '_refresh_cache') as mock_refresh:
            manager._templates_cache = {}
            
            templates = manager.get_available_templates()
            
            assert templates == []
            mock_refresh.assert_called_once()
    
    def test_get_available_templates_with_templates(self, manager):
        """Test getting available templates when templates exist."""
        mock_template1 = Mock(spec=TemplateDefinition)
        mock_template2 = Mock(spec=TemplateDefinition)
        
        with patch.object(manager, '_refresh_cache') as mock_refresh:
            manager._templates_cache = {
                "template1": mock_template1,
                "template2": mock_template2
            }
            
            templates = manager.get_available_templates()
            
            assert set(templates) == {"template1", "template2"}
            mock_refresh.assert_called_once()
    
    def test_get_template_exists(self, manager):
        """Test getting a template that exists."""
        mock_template = Mock(spec=TemplateDefinition)
        
        with patch.object(manager, '_refresh_cache') as mock_refresh:
            manager._templates_cache = {"test-template": mock_template}
            
            result = manager.get_template("test-template")
            
            assert result == mock_template
            mock_refresh.assert_called_once()
    
    def test_get_template_not_exists(self, manager):
        """Test getting a template that doesn't exist."""
        with patch.object(manager, '_refresh_cache') as mock_refresh:
            manager._templates_cache = {}
            
            result = manager.get_template("nonexistent")
            
            assert result is None
            mock_refresh.assert_called_once()
    
    def test_get_template_content_success(self, manager):
        """Test getting template content successfully."""
        mock_path = Mock(spec=Path)
        mock_path.read_text.return_value = "# Template Content"
        
        mock_template = TemplateDefinition(
            template_id="test",
            name="Test",
            description="Test template",
            file_path=mock_path,
            source_type="project"
        )
        
        with patch.object(manager, 'get_template', return_value=mock_template):
            content = manager.get_template_content("test")
            
            assert content == "# Template Content"
            mock_path.read_text.assert_called_once_with(encoding='utf-8')
            assert mock_template.content == "# Template Content"
    
    def test_get_template_content_cached(self, manager):
        """Test getting template content that's already cached."""
        mock_path = Mock(spec=Path)
        
        mock_template = TemplateDefinition(
            template_id="test",
            name="Test",
            description="Test template",
            file_path=mock_path,
            source_type="project",
            content="# Cached Content"
        )
        
        with patch.object(manager, 'get_template', return_value=mock_template):
            content = manager.get_template_content("test")
            
            assert content == "# Cached Content"
            mock_path.read_text.assert_not_called()
    
    def test_get_template_content_template_not_found(self, manager):
        """Test getting template content when template doesn't exist."""
        with patch.object(manager, 'get_template', return_value=None):
            content = manager.get_template_content("nonexistent")
            
            assert content is None
    
    def test_get_template_content_file_read_error(self, manager):
        """Test getting template content when file read fails."""
        mock_path = Mock(spec=Path)
        mock_path.read_text.side_effect = IOError("File not found")
        
        mock_template = TemplateDefinition(
            template_id="test",
            name="Test",
            description="Test template",
            file_path=mock_path,
            source_type="project"
        )
        
        with patch.object(manager, 'get_template', return_value=mock_template):
            with patch('src.templates.logger') as mock_logger:
                content = manager.get_template_content("test")
                
                assert content is None
                mock_logger.error.assert_called_once()
    
    def test_refresh_cache_no_directories(self, manager):
        """Test refreshing cache when template directories don't exist."""
        with patch('pathlib.Path.exists', return_value=False):
            manager._refresh_cache()
            
            assert manager._templates_cache == {}
    
    def test_refresh_cache_project_templates_only(self, manager):
        """Test refreshing cache with only project templates."""
        mock_file1 = Mock(spec=Path)
        mock_file1.stem = "template1"
        mock_file2 = Mock(spec=Path)
        mock_file2.stem = "template2"
        
        def mock_exists(self):
            return str(self) == str(manager.project_templates_path)
        
        def mock_glob(self, pattern):
            if str(self) == str(manager.project_templates_path) and pattern == "*.md":
                return [mock_file1, mock_file2]
            return []
        
        with patch('pathlib.Path.exists', mock_exists):
            with patch('pathlib.Path.glob', mock_glob):
                with patch.object(manager, '_create_template_definition') as mock_create:
                    mock_template1 = Mock(spec=TemplateDefinition)
                    mock_template2 = Mock(spec=TemplateDefinition)
                    mock_create.side_effect = [mock_template1, mock_template2]
                    
                    manager._refresh_cache()
                    
                    assert manager._templates_cache == {
                        "template1": mock_template1,
                        "template2": mock_template2
                    }
                    assert mock_create.call_count == 2
                    mock_create.assert_any_call("template1", mock_file1, "project")
                    mock_create.assert_any_call("template2", mock_file2, "project")
    
    def test_refresh_cache_user_templates_only(self, manager):
        """Test refreshing cache with only user templates."""
        mock_file1 = Mock(spec=Path)
        mock_file1.stem = "user-template1"
        
        def mock_exists(self):
            return str(self) == str(manager.user_templates_path)
        
        def mock_glob(self, pattern):
            if str(self) == str(manager.user_templates_path) and pattern == "*.md":
                return [mock_file1]
            return []
        
        with patch('pathlib.Path.exists', mock_exists):
            with patch('pathlib.Path.glob', mock_glob):
                with patch.object(manager, '_create_template_definition') as mock_create:
                    mock_template = Mock(spec=TemplateDefinition)
                    mock_create.return_value = mock_template
                    
                    manager._refresh_cache()
                    
                    assert manager._templates_cache == {"user-template1": mock_template}
                    mock_create.assert_called_once_with("user-template1", mock_file1, "user")
    
    def test_refresh_cache_project_precedence(self, manager):
        """Test that project templates take precedence over user templates."""
        # Project template
        mock_project_file = Mock(spec=Path)
        mock_project_file.stem = "shared-template"
        
        # User template with same name
        mock_user_file = Mock(spec=Path)
        mock_user_file.stem = "shared-template"
        
        def mock_exists(self):
            return True  # Both directories exist
        
        def mock_glob(self, pattern):
            if str(self) == str(manager.project_templates_path) and pattern == "*.md":
                return [mock_project_file]
            elif str(self) == str(manager.user_templates_path) and pattern == "*.md":
                return [mock_user_file]
            return []
        
        with patch('pathlib.Path.exists', mock_exists):
            with patch('pathlib.Path.glob', mock_glob):
                with patch.object(manager, '_create_template_definition') as mock_create:
                    mock_project_template = Mock(spec=TemplateDefinition)
                    mock_create.return_value = mock_project_template
                    
                    manager._refresh_cache()
                    
                    # Project template should be in cache, not user template
                    assert manager._templates_cache == {"shared-template": mock_project_template}
                    # User template creation should be skipped due to existing key
                    assert mock_create.call_count == 1
                    mock_create.assert_called_with("shared-template", mock_project_file, "project")
    
    def test_create_template_definition(self, manager):
        """Test creating a template definition from file path."""
        mock_stat = Mock()
        mock_stat.st_mtime = 1234567890.0
        
        mock_path = Mock(spec=Path)
        mock_path.stat.return_value = mock_stat
        
        expected_datetime = datetime.fromtimestamp(1234567890.0)
        
        template = manager._create_template_definition("test-template", mock_path, "project")
        
        assert template.template_id == "test-template"
        assert template.name == "Test Template"  # Converted from kebab-case
        assert template.description == "Test Template template"
        assert template.file_path == mock_path
        assert template.source_type == "project"
        assert template.content is None
        assert template.template_type == "markdown"
        assert template.last_updated == expected_datetime
    
    def test_create_template_definition_name_conversion(self, manager):
        """Test template name conversion from different formats."""
        mock_path = Mock(spec=Path)
        mock_path.stat.return_value = Mock(st_mtime=1234567890.0)
        
        # Test kebab-case
        template1 = manager._create_template_definition("kebab-case-name", mock_path, "project")
        assert template1.name == "Kebab Case Name"
        
        # Test snake_case
        template2 = manager._create_template_definition("snake_case_name", mock_path, "project")
        assert template2.name == "Snake Case Name"
        
        # Test mixed
        template3 = manager._create_template_definition("mixed-case_name", mock_path, "project")
        assert template3.name == "Mixed Case Name"
    
    def test_get_discovery_status_empty(self, manager):
        """Test getting discovery status when no templates exist."""
        with patch.object(manager, '_refresh_cache'):
            manager._templates_cache = {}
            
            def mock_exists(self):
                return str(self) == str(manager.user_templates_path)
            
            with patch('pathlib.Path.exists', mock_exists):
                status = manager.get_discovery_status()
                
                expected_project_path = str(manager.project_templates_path)
                expected_user_path = str(manager.user_templates_path)
                
                assert status == {
                    "project_templates_path": expected_project_path,
                    "user_templates_path": expected_user_path,
                    "project_templates_available": False,
                    "user_templates_available": True,
                    "cached_templates_count": 0,
                    "available_templates": [],
                    "templates_by_source": {"project": 0, "user": 0}
                }
    
    def test_get_discovery_status_with_templates(self, manager):
        """Test getting discovery status with templates."""
        # Create mock templates
        project_template = Mock(spec=TemplateDefinition)
        project_template.source_type = "project"
        
        user_template1 = Mock(spec=TemplateDefinition)
        user_template1.source_type = "user"
        
        user_template2 = Mock(spec=TemplateDefinition)
        user_template2.source_type = "user"
        
        manager._templates_cache = {
            "project-template": project_template,
            "user-template1": user_template1,
            "user-template2": user_template2
        }
        
        with patch.object(manager, '_refresh_cache'):
            with patch('pathlib.Path.exists', return_value=True):
                with patch.object(manager, 'get_available_templates', return_value=["project-template", "user-template1", "user-template2"]):
                    status = manager.get_discovery_status()
                    
                    assert status["cached_templates_count"] == 3
                    assert set(status["available_templates"]) == {"project-template", "user-template1", "user-template2"}
                    assert status["templates_by_source"] == {"project": 1, "user": 2}
                    assert status["project_templates_available"] is True
                    assert status["user_templates_available"] is True


class TestTemplatesManagerIntegration:
    """Integration tests for TemplatesManager."""
    
    def test_full_workflow_with_mocked_filesystem(self):
        """Test the complete workflow with mocked filesystem."""
        project_root = Path("/test/project")
        manager = TemplatesManager(project_root=project_root)
        
        # Mock filesystem structure
        project_template_file = project_root / ".claude" / "templates" / "project-template.md"
        user_template_file = Path.home() / ".claude" / "templates" / "user-template.md"
        
        project_content = "# Project Template\nThis is a project template."
        user_content = "# User Template\nThis is a user template."
        
        def mock_exists(self):
            return str(self) in [
                str(manager.project_templates_path),
                str(manager.user_templates_path)
            ]
        
        def mock_glob(self, pattern):
            if pattern == "*.md":
                if str(self) == str(manager.project_templates_path):
                    return [project_template_file]
                elif str(self) == str(manager.user_templates_path):
                    return [user_template_file]
            return []
        
        def mock_stat(self):
            mock_stat_result = Mock()
            mock_stat_result.st_mtime = 1234567890.0
            return mock_stat_result
        
        def mock_read_text(self, encoding='utf-8'):
            if "project-template" in str(self):
                return project_content
            elif "user-template" in str(self):
                return user_content
            return ""
        
        with patch('pathlib.Path.exists', mock_exists):
            with patch('pathlib.Path.glob', mock_glob):
                with patch('pathlib.Path.stat', mock_stat):
                    with patch('pathlib.Path.read_text', mock_read_text):
                        # Test getting available templates
                        templates = manager.get_available_templates()
                        assert set(templates) == {"project-template", "user-template"}
                        
                        # Test getting specific templates
                        project_template = manager.get_template("project-template")
                        assert project_template is not None
                        assert project_template.source_type == "project"
                        
                        user_template = manager.get_template("user-template")
                        assert user_template is not None
                        assert user_template.source_type == "user"
                        
                        # Test getting template content
                        project_content_result = manager.get_template_content("project-template")
                        assert project_content_result == project_content
                        
                        user_content_result = manager.get_template_content("user-template")
                        assert user_content_result == user_content
                        
                        # Test discovery status
                        status = manager.get_discovery_status()
                        assert status["cached_templates_count"] == 2
                        assert status["templates_by_source"] == {"project": 1, "user": 1}


class TestTemplatesModuleExports:
    """Test module exports and imports."""
    
    def test_module_exports(self):
        """Test that the module exports the expected classes."""
        from src.templates import TemplateDefinition, TemplatesManager, __all__
        
        assert __all__ == ["TemplateDefinition", "TemplatesManager"]
        assert TemplateDefinition is not None
        assert TemplatesManager is not None