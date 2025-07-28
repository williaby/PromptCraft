#!/usr/bin/env python3
"""
Quick test runner for Phase 1 Issue 5 remediation fixes.

This script performs basic validation of the security and functionality fixes
implemented to address the critical issues identified by the multi-agent review.
"""

import inspect
import sys
import tempfile
import traceback
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.ui.multi_journey_interface import MultiJourneyInterface


def test_security_fixes() -> None:
    """Test security vulnerability fixes."""
    interface = MultiJourneyInterface()

    # Test 1: File count validation
    if not hasattr(interface.settings, "max_files"):
        raise ValueError("Security fix missing: interface.settings.max_files attribute not found")
    expected_max_files = 5
    if interface.settings.max_files != expected_max_files:
        raise ValueError(f"Security fix error: max_files should be 5, got {interface.settings.max_files}")

    # Test 2: File size validation
    if not hasattr(interface.settings, "max_file_size"):
        raise ValueError("Security fix missing: interface.settings.max_file_size attribute not found")
    expected_max_file_size = 10485760  # 10MB
    if interface.settings.max_file_size != expected_max_file_size:
        raise ValueError(
            f"Security fix error: max_file_size should be 10485760, got {interface.settings.max_file_size}",
        )

    # Test 3: Memory-safe file processing
    if not hasattr(interface, "_process_file_safely"):
        raise ValueError("Security fix missing: interface._process_file_safely method not found")

    # Test 4: MIME type validation
    if not hasattr(interface, "_is_safe_mime_type"):
        raise ValueError("Security fix missing: interface._is_safe_mime_type method not found")
    if interface._is_safe_mime_type("text/plain", ".txt") is not True:
        raise ValueError("MIME type validation error: text/plain should be safe")
    if interface._is_safe_mime_type("application/x-executable", ".txt") is not False:
        raise ValueError("MIME type validation error: application/x-executable should be unsafe")


def test_functionality_fixes() -> None:
    """Test functionality bug fixes."""
    interface = MultiJourneyInterface()

    # Test 1: Model selection validation
    if not hasattr(interface, "model_costs"):
        raise ValueError("Functionality fix missing: interface.model_costs attribute not found")
    if "gpt-4o-mini" not in interface.model_costs:
        raise ValueError("Model selection error: gpt-4o-mini not found in model_costs")

    # Test 2: Session state isolation
    if not hasattr(interface, "update_session_cost"):
        raise ValueError("Functionality fix missing: interface.update_session_cost method not found")
    # Verify the method takes session_state parameter (user isolation)
    sig = inspect.signature(interface.update_session_cost)
    if "session_state" not in sig.parameters:
        raise ValueError("Session isolation error: update_session_cost missing session_state parameter")

    # Test 3: Error handling and fallbacks
    if not hasattr(interface, "_create_fallback_result"):
        raise ValueError("Error handling fix missing: interface._create_fallback_result method not found")
    if not hasattr(interface, "_create_timeout_fallback_result"):
        raise ValueError("Error handling fix missing: interface._create_timeout_fallback_result method not found")
    if not hasattr(interface, "_create_error_fallback_result"):
        raise ValueError("Error handling fix missing: interface._create_error_fallback_result method not found")

    # Test fallback result structure
    test_input = "Test input"
    test_model = "gpt-4o-mini"
    fallback = interface._create_fallback_result(test_input, test_model)
    expected_fallback_fields = 9  # Correct number of output fields
    if len(fallback) != expected_fallback_fields:
        raise ValueError(f"Fallback result structure error: expected 9 fields, got {len(fallback)}")
    if "Fallback Mode" not in fallback[0]:
        raise ValueError("Fallback result error: 'Fallback Mode' not found in result[0]")


def test_memory_and_performance() -> None:
    """Test memory and performance improvements."""

    interface = MultiJourneyInterface()

    # Test 1: Memory bounds implementation
    # Create a test file processing scenario
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp_file:
        content = "x" * 1000  # Small test content
        tmp_file.write(content)
        tmp_file.flush()

        try:
            result = interface._process_file_safely(tmp_file.name, len(content.encode()))
            if len(result) != len(content):  # Should process small files normally
                raise ValueError(f"File processing error: expected {len(content)} chars, got {len(result)}")
            # Small file processing works correctly
        finally:
            Path(tmp_file.name).unlink()

    # Test 2: Chunk-based processing
    # Streaming/chunked processing implemented
    # Verify the method accepts chunk_size parameter

    sig = inspect.signature(interface._process_file_safely)
    if "chunk_size" not in sig.parameters:
        raise ValueError("Performance fix missing: _process_file_safely missing chunk_size parameter")

    # Memory and performance fixes validated successfully


def test_error_recovery() -> None:
    """Test error recovery and graceful degradation."""

    interface = MultiJourneyInterface()

    # Test timeout fallback
    timeout_result = interface._create_timeout_fallback_result("test input", "gpt-4o-mini")
    if "Timeout Recovery" not in timeout_result[0]:
        raise ValueError("Timeout recovery error: 'Timeout Recovery' not found in result[0]")
    if "⏱️" not in timeout_result[1]:  # Timeout emoji in context
        raise ValueError("Timeout recovery error: timeout emoji not found in result[1]")
    # Timeout recovery implemented

    # Test error fallback
    error_result = interface._create_error_fallback_result("test input", "gpt-4o-mini", "test error")
    if "Error Recovery" not in error_result[0]:
        raise ValueError("Error recovery error: 'Error Recovery' not found in result[0]")
    if "🔧" not in error_result[1]:  # Error recovery emoji
        raise ValueError("Error recovery error: error recovery emoji not found in result[1]")
    # Error recovery implemented

    # Test general fallback
    fallback_result = interface._create_fallback_result("test input", "gpt-4o-mini")
    if "Fallback Mode" not in fallback_result[0]:
        raise ValueError("General fallback error: 'Fallback Mode' not found in result[0]")
    if "🤖" not in fallback_result[7]:  # Fallback mode indicator
        raise ValueError("General fallback error: fallback mode indicator not found in result[7]")
    # General fallback implemented

    # Error recovery validated successfully


def main() -> int:
    """Run all remediation tests."""

    try:
        test_security_fixes()
        test_functionality_fixes()
        test_memory_and_performance()
        test_error_recovery()

        # All remediation fixes validated successfully

        return 0

    except Exception:
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
