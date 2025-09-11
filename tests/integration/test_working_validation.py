"""
Working Authentication and Journey 1 Integration Tests.

Simple integration tests using correct imports and function names.
"""

from pathlib import Path
import tempfile

import pytest

from src.auth_simple import (
    AuthConfig,
    EmailWhitelistValidator,
    SimpleSessionManager,
)
from src.ui.journeys.journey1_smart_templates import Journey1SmartTemplates


class TestAuthSystemWorking:
    """Working authentication system tests with correct imports."""

    def test_auth_config_basic(self):
        """Test basic AuthConfig functionality."""
        config = AuthConfig()

        assert config.auth_mode.value == "cloudflare_simple"
        assert config.session_timeout == 3600
        assert len(config.public_paths) > 10
        assert config.enabled is True

    def test_email_whitelist_validator(self):
        """Test EmailWhitelistValidator with correct method names."""
        validator = EmailWhitelistValidator(
            whitelist=["admin@test.com", "user@test.com", "@company.com"],
            admin_emails=["admin@test.com"],
        )

        # Test authorization (correct method name)
        assert validator.is_authorized("admin@test.com") is True
        assert validator.is_authorized("user@test.com") is True
        assert validator.is_authorized("any@company.com") is True
        assert validator.is_authorized("hacker@evil.com") is False

        # Test admin detection
        assert validator.is_admin("admin@test.com") is True
        assert validator.is_admin("user@test.com") is False

        # Test role detection
        assert validator.get_user_role("admin@test.com") == "admin"
        assert validator.get_user_role("user@test.com") == "user"

    def test_session_manager(self):
        """Test SimpleSessionManager functionality."""
        manager = SimpleSessionManager(session_timeout=3600)

        # Use correct API signature: create_session(email, is_admin, user_tier, cf_context=None)
        session_id = manager.create_session(
            email="test@user.com",
            is_admin=False,
            user_tier="user",
            cf_context={"test": True},
        )

        assert session_id is not None
        assert len(session_id) > 10

        # Test session retrieval
        retrieved = manager.get_session(session_id)
        assert retrieved is not None
        assert retrieved["email"] == "test@user.com"

        # Test invalid session
        assert manager.get_session("invalid_id") is None


class TestJourney1Working:
    """Working Journey 1 tests with correct method signatures."""

    @pytest.fixture
    def journey1_processor(self):
        """Create Journey1SmartTemplates instance."""
        return Journey1SmartTemplates()

    def test_journey1_initialization(self, journey1_processor):
        """Test Journey1SmartTemplates initialization."""
        assert journey1_processor.supported_file_types == [".txt", ".md", ".pdf", ".docx", ".csv", ".json"]
        assert journey1_processor.max_file_size == 10 * 1024 * 1024  # 10MB
        assert journey1_processor.max_files == 5

    def test_file_extraction(self, journey1_processor):
        """Test file content extraction."""
        # Create temporary file
        test_content = "This is a test document with project information."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            content, file_type = journey1_processor.extract_file_content(temp_path)

            assert file_type == ".txt"
            assert test_content in content
            assert len(content) >= len(test_content)

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_enhance_prompt_full_signature(self, journey1_processor):
        """Test enhance_prompt with all required parameters."""
        test_input = "Write a professional email about a project delay"

        result = journey1_processor.enhance_prompt(
            text_input=test_input,
            files=[],
            model_mode="openrouter",
            custom_model="gpt-4o-mini",
            reasoning_depth="detailed",
            search_tier="basic",
            temperature=0.7,
        )

        # Should return tuple of 10 elements (updated from 9 per production)
        assert isinstance(result, tuple)
        assert len(result) == 10

        (
            enhanced_prompt,
            clean_prompt,
            context,
            request,
            examples,
            augmentations,
            tone,
            evaluation,
            model_attr,
            file_sources,
        ) = result

        # Verify components have content
        assert len(enhanced_prompt) > len(test_input)
        assert len(context) > 50  # Should have meaningful context analysis
        assert len(request) > 50  # Should have request specification

        # Verify enhancement quality
        assert "professional" in enhanced_prompt.lower() or "professional" in context.lower()

    def test_empty_input_handling(self, journey1_processor):
        """Test handling of empty file input."""
        content, file_type = journey1_processor.extract_file_content("")

        assert file_type == "error"
        assert "Error processing file" in content

    def test_file_validation_logic(self, journey1_processor):
        """Test file validation parameters."""
        # Test supported file types
        supported_types = journey1_processor.supported_file_types

        for file_type in [".txt", ".md", ".pdf", ".docx", ".csv", ".json"]:
            assert file_type in supported_types

        # Verify limits
        assert journey1_processor.max_file_size == 10 * 1024 * 1024  # 10MB
        assert journey1_processor.max_files == 5


class TestIntegrationWorking:
    """Working integration tests."""

    def test_auth_and_journey1_compatibility(self):
        """Test compatibility between auth and journey1 systems."""
        # Test that both systems can be initialized together
        config = AuthConfig()
        validator = EmailWhitelistValidator(whitelist=["test@user.com"], admin_emails=["admin@user.com"])
        session_manager = SimpleSessionManager(session_timeout=3600)
        journey1 = Journey1SmartTemplates()

        # All systems should initialize without conflicts
        assert config is not None
        assert validator is not None
        assert session_manager is not None
        assert journey1 is not None

        # Test basic operations don't interfere
        assert validator.is_authorized("test@user.com") is True
        assert len(journey1.supported_file_types) == 6

    def test_user_session_context_flow(self):
        """Test user context flow from auth to journey1."""
        # Simulate user session creation
        validator = EmailWhitelistValidator(whitelist=["user@company.com"], admin_emails=[])
        session_manager = SimpleSessionManager(session_timeout=3600)

        # User authentication
        user_email = "user@company.com"
        assert validator.is_authorized(user_email) is True
        user_role = validator.get_user_role(user_email)

        # Session creation with correct API signature
        is_admin = user_role == "admin"  # Convert role to boolean
        session_id = session_manager.create_session(
            email=user_email,
            is_admin=is_admin,
            user_tier=user_role,
            cf_context={"cf_ray": "test-123"},
        )

        # Session retrieval (simulating request processing)
        session_data = session_manager.get_session(session_id)
        assert session_data is not None
        assert session_data["email"] == user_email
        assert "is_admin" in session_data  # Session has admin info

        # Journey1 processing (with user context available)
        journey1 = Journey1SmartTemplates()

        # In real integration, user context would influence processing
        # For now, just verify journey1 works with session context available
        result = journey1.enhance_prompt(
            text_input="Write an email update",
            files=[],
            model_mode="openrouter",
            custom_model="gpt-4o-mini",
            reasoning_depth="basic",
            search_tier="basic",
            temperature=0.7,
        )

        assert isinstance(result, tuple)
        assert len(result) == 10  # Updated from 9 to match production API
        enhanced_prompt = result[0]
        assert len(enhanced_prompt) > 10  # Should generate meaningful output


# Test markers
pytestmark = pytest.mark.integration
