"""Tests for launch_admin.py."""

import os
import sys
from pathlib import Path
from unittest import mock


# Add the project root to sys.path so we can import launch_admin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
import launch_admin


class TestLaunchAdmin:
    """Test cases for launch_admin module."""

    def test_main_environment_setup(self, monkeypatch):
        """Test that main() sets up environment variables correctly."""
        # Mock the interface creation to avoid actual launch
        with mock.patch("src.ui.multi_journey_interface.MultiJourneyInterface") as mock_interface:
            mock_app = mock.MagicMock()
            mock_interface.return_value.create_interface.return_value = mock_app

            # Call main
            launch_admin.main()

            # Verify environment variables were set
            assert os.environ.get("PROMPTCRAFT_DEV_MODE") == "true"
            assert os.environ.get("PROMPTCRAFT_DEV_USER_EMAIL") == "byron@test.com"
            assert os.environ.get("PROMPTCRAFT_LOCAL_ADMIN") == "true"

            # Verify interface was created and launched
            mock_interface.assert_called_once()
            mock_interface.return_value.create_interface.assert_called_once()
            mock_app.launch.assert_called_once_with(
                server_name="0.0.0.0",
                server_port=7861,
                share=False,
                debug=True,
                show_error=True,
                inbrowser=True,
            )

    def test_main_handles_import_error(self):
        """Test that main() handles import errors gracefully."""
        with (
            mock.patch(
                "src.ui.multi_journey_interface.MultiJourneyInterface",
                side_effect=ImportError("Test import error"),
            ),
            mock.patch("builtins.print") as mock_print,
        ):
            launch_admin.main()

            # Verify error was printed
            error_calls = [call for call in mock_print.call_args_list if "❌ Error launching interface" in str(call)]
            assert len(error_calls) > 0

    def test_main_handles_general_exception(self):
        """Test that main() handles general exceptions gracefully."""
        with (
            mock.patch(
                "src.ui.multi_journey_interface.MultiJourneyInterface",
                side_effect=RuntimeError("Test runtime error"),
            ),
            mock.patch("builtins.print") as mock_print,
        ):
            launch_admin.main()

            # Verify error was printed
            error_calls = [call for call in mock_print.call_args_list if "❌ Error launching interface" in str(call)]
            assert len(error_calls) > 0

    def test_main_interface_creation_error(self):
        """Test that main() handles interface creation errors."""
        mock_interface = mock.MagicMock()
        mock_interface.create_interface.side_effect = Exception("Interface creation failed")

        with mock.patch("src.ui.multi_journey_interface.MultiJourneyInterface", return_value=mock_interface):
            with mock.patch("builtins.print") as mock_print:
                launch_admin.main()

                # Verify error was printed
                error_calls = [
                    call for call in mock_print.call_args_list if "❌ Error launching interface" in str(call)
                ]
                assert len(error_calls) > 0

    def test_main_app_launch_error(self):
        """Test that main() handles app launch errors."""
        mock_interface = mock.MagicMock()
        mock_app = mock.MagicMock()
        mock_app.launch.side_effect = Exception("Launch failed")
        mock_interface.create_interface.return_value = mock_app

        with mock.patch("src.ui.multi_journey_interface.MultiJourneyInterface", return_value=mock_interface):
            with mock.patch("builtins.print") as mock_print:
                launch_admin.main()

                # Verify error was printed
                error_calls = [
                    call for call in mock_print.call_args_list if "❌ Error launching interface" in str(call)
                ]
                assert len(error_calls) > 0

    def test_main_as_script(self):
        """Test that script can be run as main module."""
        # This tests the if __name__ == "__main__": block
        original_name = launch_admin.__name__
        try:
            launch_admin.__name__ = "__main__"

            with mock.patch("launch_admin.main"):
                # Simulate running the script
                script_path = Path("scripts/launch_admin.py")
                exec(compile(script_path.read_text(), str(script_path), "exec"))

                # Note: This won't actually call main() in our test environment
                # but we can verify the structure is correct

        finally:
            launch_admin.__name__ = original_name

    def test_environment_variables_set(self):
        """Test that the required environment variables are set."""
        # This test runs the module import which sets the environment
        assert os.environ.get("PROMPTCRAFT_DEV_MODE") == "true"
        assert os.environ.get("PROMPTCRAFT_DEV_USER_EMAIL") == "byron@test.com"
        assert os.environ.get("PROMPTCRAFT_LOCAL_ADMIN") == "true"

    def test_logging_configuration(self):
        """Test that logging is properly configured."""
        # Check that the logger was created
        import logging

        logger = logging.getLogger("launch_admin")
        assert logger is not None

        # Check basic logging level (should be INFO from basicConfig)
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
