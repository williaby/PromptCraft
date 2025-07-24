"""
Unit tests for Multi-Journey Interface components.

This module provides comprehensive test coverage for the multi-journey interface,
including rate limiting, session management, and UI component functionality.
"""

import time
from unittest.mock import Mock, patch

import pytest

from src.ui.multi_journey_interface import MultiJourneyInterface, RateLimiter


@pytest.mark.unit
class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_rate_limiter_init(self):
        """Test RateLimiter initialization with default values."""
        limiter = RateLimiter()

        assert limiter.max_requests_per_minute == 30
        assert limiter.max_requests_per_hour == 200
        assert limiter.max_file_uploads_per_hour == 50
        assert limiter.cleanup_interval == 300

    def test_rate_limiter_init_custom_values(self):
        """Test RateLimiter initialization with custom values."""
        limiter = RateLimiter(max_requests_per_minute=50, max_requests_per_hour=500, max_file_uploads_per_hour=100)

        assert limiter.max_requests_per_minute == 50
        assert limiter.max_requests_per_hour == 500
        assert limiter.max_file_uploads_per_hour == 100

    def test_check_request_rate_within_limits(self):
        """Test request rate checking within limits."""
        limiter = RateLimiter(max_requests_per_minute=10, max_requests_per_hour=100)
        session_id = "test_session_1"

        # First request should be allowed
        assert limiter.check_request_rate(session_id) is True

        # Multiple requests within limits should be allowed
        for i in range(5):
            assert limiter.check_request_rate(session_id) is True

    def test_check_request_rate_minute_limit_exceeded(self):
        """Test request rate limiting when minute limit is exceeded."""
        limiter = RateLimiter(max_requests_per_minute=3, max_requests_per_hour=100)
        session_id = "test_session_2"

        # First 3 requests should be allowed
        for i in range(3):
            assert limiter.check_request_rate(session_id) is True

        # 4th request should be denied
        assert limiter.check_request_rate(session_id) is False

    def test_check_request_rate_hour_limit_exceeded(self):
        """Test request rate limiting when hour limit is exceeded."""
        limiter = RateLimiter(max_requests_per_minute=1000, max_requests_per_hour=5)
        session_id = "test_session_3"

        # First 5 requests should be allowed
        for i in range(5):
            assert limiter.check_request_rate(session_id) is True

        # 6th request should be denied
        assert limiter.check_request_rate(session_id) is False

    def test_check_file_upload_rate_within_limits(self):
        """Test file upload rate checking within limits."""
        limiter = RateLimiter(max_file_uploads_per_hour=10)
        session_id = "test_session_4"

        # First few uploads should be allowed
        for i in range(5):
            assert limiter.check_file_upload_rate(session_id) is True

    def test_check_file_upload_rate_limit_exceeded(self):
        """Test file upload rate limiting when limit is exceeded."""
        limiter = RateLimiter(max_file_uploads_per_hour=3)
        session_id = "test_session_5"

        # First 3 uploads should be allowed
        for i in range(3):
            assert limiter.check_file_upload_rate(session_id) is True

        # 4th upload should be denied
        assert limiter.check_file_upload_rate(session_id) is False

    def test_cleanup_old_entries(self):
        """Test cleanup of old entries."""
        limiter = RateLimiter()
        session_id = "test_session_6"

        # Add some requests
        limiter.check_request_rate(session_id)
        assert session_id in limiter.request_windows

        # Force cleanup by setting old timestamp
        limiter.last_cleanup = time.time() - 400  # Force cleanup
        old_time = time.time() - 7200  # 2 hours ago
        limiter.request_windows[session_id].appendleft(old_time)

        # Trigger cleanup
        limiter._cleanup_old_entries()

        # Old entries should be removed
        if session_id in limiter.request_windows:
            assert old_time not in limiter.request_windows[session_id]

    def test_separate_session_limits(self):
        """Test that different sessions have separate rate limits."""
        limiter = RateLimiter(max_requests_per_minute=2)

        session1 = "session_1"
        session2 = "session_2"

        # Each session should be able to make 2 requests
        assert limiter.check_request_rate(session1) is True
        assert limiter.check_request_rate(session1) is True
        assert limiter.check_request_rate(session2) is True
        assert limiter.check_request_rate(session2) is True

        # Third request for each should be denied
        assert limiter.check_request_rate(session1) is False
        assert limiter.check_request_rate(session2) is False

    @patch("time.time")
    def test_time_window_sliding(self, mock_time):
        """Test that rate limiting uses sliding time windows."""
        # Mock time progression
        mock_time.side_effect = [1000, 1000, 1000, 1030, 1070]  # 30s, then 40s later

        limiter = RateLimiter(max_requests_per_minute=2)
        session_id = "test_session_7"

        # Use up minute limit
        assert limiter.check_request_rate(session_id) is True  # t=1000
        assert limiter.check_request_rate(session_id) is True  # t=1000
        assert limiter.check_request_rate(session_id) is False  # t=1000, denied

        # After 70 seconds, should be allowed again (sliding window)
        assert limiter.check_request_rate(session_id) is True  # t=1070


@pytest.mark.unit
class TestMultiJourneyInterface:
    """Test cases for MultiJourneyInterface class."""

    @patch("src.ui.multi_journey_interface.gr")
    def test_multi_journey_interface_init(self, mock_gr):
        """Test MultiJourneyInterface initialization."""
        # Mock Gradio components
        mock_gr.Blocks.return_value = Mock()

        interface = MultiJourneyInterface()

        assert interface.rate_limiter is not None
        assert interface.session_states == {}
        assert interface.active_sessions == {}

    @patch("src.ui.multi_journey_interface.gr")
    def test_create_interface(self, mock_gr):
        """Test interface creation."""
        # Mock Gradio components
        mock_blocks = Mock()
        mock_gr.Blocks.return_value = mock_blocks
        mock_gr.Tab.return_value = Mock()
        mock_gr.Column.return_value = Mock()
        mock_gr.Row.return_value = Mock()

        interface = MultiJourneyInterface()
        result = interface.create_interface()

        # Should return the Gradio Blocks object
        assert result == mock_blocks

    @patch("src.ui.multi_journey_interface.gr")
    def test_create_journey1_tab(self, mock_gr):
        """Test Journey 1 tab creation."""
        mock_gr.Tab.return_value = Mock()
        mock_gr.Column.return_value = Mock()
        mock_gr.Textbox.return_value = Mock()
        mock_gr.Button.return_value = Mock()

        interface = MultiJourneyInterface()
        components = interface._create_journey1_tab()

        # Should return dictionary of components
        assert isinstance(components, dict)
        assert "input_text" in components
        assert "enhance_button" in components
        assert "output_text" in components

    @patch("src.ui.multi_journey_interface.gr")
    def test_create_journey2_tab(self, mock_gr):
        """Test Journey 2 tab creation."""
        mock_gr.Tab.return_value = Mock()
        mock_gr.Column.return_value = Mock()
        mock_gr.Textbox.return_value = Mock()
        mock_gr.Button.return_value = Mock()

        interface = MultiJourneyInterface()
        components = interface._create_journey2_tab()

        assert isinstance(components, dict)
        assert "search_input" in components
        assert "search_button" in components
        assert "results_output" in components

    @patch("src.ui.multi_journey_interface.gr")
    def test_create_journey3_tab(self, mock_gr):
        """Test Journey 3 tab creation."""
        mock_gr.Tab.return_value = Mock()
        mock_gr.Column.return_value = Mock()
        mock_gr.Button.return_value = Mock()
        mock_gr.Markdown.return_value = Mock()

        interface = MultiJourneyInterface()
        components = interface._create_journey3_tab()

        assert isinstance(components, dict)
        assert "launch_button" in components
        assert "status_display" in components

    @patch("src.ui.multi_journey_interface.gr")
    def test_create_journey4_tab(self, mock_gr):
        """Test Journey 4 tab creation."""
        mock_gr.Tab.return_value = Mock()
        mock_gr.Column.return_value = Mock()
        mock_gr.Textbox.return_value = Mock()
        mock_gr.Checkbox.return_value = Mock()
        mock_gr.Button.return_value = Mock()

        interface = MultiJourneyInterface()
        components = interface._create_journey4_tab()

        assert isinstance(components, dict)
        assert "workflow_input" in components
        assert "free_mode_toggle" in components
        assert "execute_button" in components

    def test_handle_journey1_request_rate_limited(self):
        """Test Journey 1 request handling with rate limiting."""
        interface = MultiJourneyInterface()

        # Mock rate limiter to deny request
        interface.rate_limiter.check_request_rate = Mock(return_value=False)

        result = interface.handle_journey1_request("test input", "session_123")

        assert "Rate limit exceeded" in result
        assert "Please wait before making another request" in result

    def test_handle_journey1_request_valid(self):
        """Test valid Journey 1 request handling."""
        interface = MultiJourneyInterface()

        # Mock rate limiter to allow request
        interface.rate_limiter.check_request_rate = Mock(return_value=True)

        # Mock the journey processor
        with patch.object(interface, "_process_journey1") as mock_process:
            mock_process.return_value = "Enhanced prompt result"

            result = interface.handle_journey1_request("test input", "session_123")

            assert result == "Enhanced prompt result"
            mock_process.assert_called_once_with("test input", "session_123")

    def test_handle_journey2_search_rate_limited(self):
        """Test Journey 2 search handling with rate limiting."""
        interface = MultiJourneyInterface()

        # Mock rate limiter to deny request
        interface.rate_limiter.check_request_rate = Mock(return_value=False)

        result = interface.handle_journey2_search("test query", "session_123")

        assert "Rate limit exceeded" in result

    def test_handle_journey2_search_valid(self):
        """Test valid Journey 2 search handling."""
        interface = MultiJourneyInterface()

        # Mock rate limiter to allow request
        interface.rate_limiter.check_request_rate = Mock(return_value=True)

        # Mock the search processor
        with patch.object(interface, "_process_journey2_search") as mock_search:
            mock_search.return_value = "Search results"

            result = interface.handle_journey2_search("test query", "session_123")

            assert result == "Search results"
            mock_search.assert_called_once_with("test query", "session_123")

    def test_handle_file_upload_rate_limited(self):
        """Test file upload handling with rate limiting."""
        interface = MultiJourneyInterface()

        # Mock rate limiter to deny upload
        interface.rate_limiter.check_file_upload_rate = Mock(return_value=False)

        result = interface.handle_file_upload(["file1.txt"], "session_123")

        assert "File upload rate limit exceeded" in result

    def test_handle_file_upload_valid(self):
        """Test valid file upload handling."""
        interface = MultiJourneyInterface()

        # Mock rate limiter to allow upload
        interface.rate_limiter.check_file_upload_rate = Mock(return_value=True)

        # Mock file processing
        with patch.object(interface, "_process_file_uploads") as mock_process:
            mock_process.return_value = "Files processed successfully"

            result = interface.handle_file_upload(["file1.txt"], "session_123")

            assert result == "Files processed successfully"
            mock_process.assert_called_once_with(["file1.txt"], "session_123")

    def test_get_session_state_new_session(self):
        """Test getting session state for new session."""
        interface = MultiJourneyInterface()

        session_id = "new_session_123"
        state = interface.get_session_state(session_id)

        assert state["session_id"] == session_id
        assert state["created_at"] is not None
        assert state["request_count"] == 0
        assert state["last_activity"] is not None

    def test_get_session_state_existing_session(self):
        """Test getting session state for existing session."""
        interface = MultiJourneyInterface()

        session_id = "existing_session_123"

        # Create initial state
        initial_state = interface.get_session_state(session_id)
        initial_count = initial_state["request_count"]

        # Get state again
        state = interface.get_session_state(session_id)

        assert state["session_id"] == session_id
        assert state["request_count"] == initial_count  # Should be same object

    def test_update_session_activity(self):
        """Test updating session activity."""
        interface = MultiJourneyInterface()

        session_id = "test_session_456"

        # Get initial state
        state = interface.get_session_state(session_id)
        initial_time = state["last_activity"]
        initial_count = state["request_count"]

        # Update activity
        time.sleep(0.01)  # Small delay to ensure time difference
        interface.update_session_activity(session_id)

        # Check updates
        updated_state = interface.get_session_state(session_id)
        assert updated_state["last_activity"] > initial_time
        assert updated_state["request_count"] == initial_count + 1

    def test_cleanup_inactive_sessions(self):
        """Test cleanup of inactive sessions."""
        interface = MultiJourneyInterface()

        session_id = "inactive_session"

        # Create session
        interface.get_session_state(session_id)
        assert session_id in interface.session_states

        # Mock old timestamp
        interface.session_states[session_id]["last_activity"] = time.time() - 7200  # 2 hours ago

        # Run cleanup
        interface.cleanup_inactive_sessions(max_age=3600)  # 1 hour max age

        # Session should be removed
        assert session_id not in interface.session_states

    def test_get_system_status(self):
        """Test getting system status."""
        interface = MultiJourneyInterface()

        # Create some sessions
        interface.get_session_state("session1")
        interface.get_session_state("session2")

        status = interface.get_system_status()

        assert "active_sessions" in status
        assert "total_requests" in status
        assert "uptime" in status
        assert status["active_sessions"] >= 2

    def test_error_handling_invalid_input(self):
        """Test error handling for invalid inputs."""
        interface = MultiJourneyInterface()

        # Test with None inputs
        result = interface.handle_journey1_request(None, "session")
        assert "error" in result.lower() or "invalid" in result.lower()

        # Test with empty session ID
        result = interface.handle_journey1_request("test", "")
        assert isinstance(result, str)  # Should handle gracefully

    def test_model_selection_integration(self):
        """Test model selection integration."""
        interface = MultiJourneyInterface()

        # Test model list retrieval
        models = interface.get_available_models()
        assert isinstance(models, list)

        # Test model selection
        selected_model = interface.select_model("claude-3-5-sonnet")
        assert selected_model is not None

    def test_copy_code_functionality(self):
        """Test code copying functionality."""
        interface = MultiJourneyInterface()

        test_code = "def hello():\n    print('Hello, World!')"

        # Test formatting for copy
        formatted = interface.format_code_for_copy(test_code, "python")
        assert "def hello()" in formatted
        assert isinstance(formatted, str)

    def test_file_validation(self):
        """Test file validation functionality."""
        interface = MultiJourneyInterface()

        # Test valid file
        is_valid, message = interface.validate_file("test.txt", 1024)
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)

        # Test oversized file
        is_valid, message = interface.validate_file("large.txt", 50 * 1024 * 1024)  # 50MB
        assert is_valid is False
        assert "too large" in message.lower()

    def test_export_functionality(self):
        """Test export functionality integration."""
        interface = MultiJourneyInterface()

        test_content = "Test content for export"

        # Test export in different formats
        for format_type in ["txt", "md", "json"]:
            exported = interface.export_content(test_content, format_type)
            assert isinstance(exported, str)
            assert len(exported) > 0

    def test_health_check(self):
        """Test health check functionality."""
        interface = MultiJourneyInterface()

        health = interface.health_check()

        assert "status" in health
        assert "components" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
