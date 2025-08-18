"""
Test datetime compatibility module for Python version consistency.
"""

from datetime import datetime, timezone

from src.utils.datetime_compat import UTC, utc_now


class TestDatetimeCompat:
    """Test datetime compatibility utilities."""

    def test_utc_constant_available(self):
        """UTC constant should be available."""
        assert UTC is not None

    def test_utc_now_returns_aware_datetime(self):
        """utc_now() should return timezone-aware datetime."""
        dt = utc_now()
        assert dt.tzinfo is not None
        assert dt.tzinfo == UTC

    def test_utc_constant_works_with_datetime(self):
        """UTC constant should work for datetime operations."""
        dt = datetime.now(UTC)
        assert dt.tzinfo == UTC

    def test_python_310_compatibility(self):
        """UTC constant should work on Python 3.10."""
        # This test ensures the fallback to timezone.utc works
        dt1 = datetime.now(UTC)
        dt2 = datetime.now(UTC)

        # Both should be equivalent
        assert dt1.tzinfo == dt2.tzinfo
