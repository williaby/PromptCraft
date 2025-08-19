"""
Test datetime compatibility module for Python version consistency.
"""

# ruff: noqa: DTZ001,DTZ005  # Tests need to create naive datetimes intentionally

import time
import warnings
from datetime import datetime, timedelta, timezone

import pytest

from src.utils.datetime_compat import (
    UTC,
    assert_datetime_aware,
    aware_to_naive,
    ensure_aware,
    is_aware,
    is_naive,
    naive_to_aware,
    safe_compare,
    utc_from_timestamp,
    utc_now,
    utcfromtimestamp_compat,
    utcnow_compat,
)


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


class TestUtcNow:
    """Test utc_now() function."""

    def test_returns_timezone_aware_datetime(self):
        """utc_now() should return timezone-aware datetime."""
        dt = utc_now()
        assert is_aware(dt)
        assert dt.tzinfo == UTC

    def test_returns_current_time(self):
        """utc_now() should return current time within reasonable delta."""
        before = time.time()
        dt = utc_now()
        after = time.time()

        dt_timestamp = dt.timestamp()
        assert before <= dt_timestamp <= after

    def test_consistent_timezone(self):
        """Multiple calls should use same timezone."""
        dt1 = utc_now()
        dt2 = utc_now()
        assert dt1.tzinfo == dt2.tzinfo == UTC


class TestUtcFromTimestamp:
    """Test utc_from_timestamp() function."""

    def test_creates_aware_datetime(self):
        """utc_from_timestamp() should create timezone-aware datetime."""
        timestamp = 1640995200.0  # 2022-01-01 00:00:00 UTC
        dt = utc_from_timestamp(timestamp)
        assert is_aware(dt)
        assert dt.tzinfo == UTC

    def test_correct_timestamp_conversion(self):
        """Should correctly convert timestamp to datetime."""
        timestamp = 1640995200.0  # 2022-01-01 00:00:00 UTC
        dt = utc_from_timestamp(timestamp)
        assert dt.year == 2022
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0

    def test_with_fractional_seconds(self):
        """Should handle fractional seconds."""
        timestamp = 1640995200.123456
        dt = utc_from_timestamp(timestamp)
        assert dt.microsecond == 123456

    def test_with_negative_timestamp(self):
        """Should handle negative timestamps (before epoch)."""
        timestamp = -86400.0  # 1969-12-31 00:00:00 UTC
        dt = utc_from_timestamp(timestamp)
        assert dt.year == 1969
        assert dt.month == 12
        assert dt.day == 31


class TestAwarenessChecks:
    """Test is_aware() and is_naive() functions."""

    def test_is_aware_with_timezone(self):
        """is_aware() should return True for timezone-aware datetimes."""
        dt = datetime.now(UTC)
        assert is_aware(dt) is True

    def test_is_aware_without_timezone(self):
        """is_aware() should return False for naive datetimes."""
        dt = datetime.now()
        assert is_aware(dt) is False

    def test_is_naive_with_timezone(self):
        """is_naive() should return False for timezone-aware datetimes."""
        dt = datetime.now(UTC)
        assert is_naive(dt) is False

    def test_is_naive_without_timezone(self):
        """is_naive() should return True for naive datetimes."""
        dt = datetime.now()
        assert is_naive(dt) is True

    def test_is_aware_with_none_tzinfo(self):
        """is_aware() should handle None tzinfo correctly."""
        dt = datetime.now()
        dt = dt.replace(tzinfo=None)
        assert is_aware(dt) is False

    def test_timezone_with_zero_offset(self):
        """Should handle timezone with zero UTC offset."""
        zero_offset_tz = timezone(timedelta(0))
        dt = datetime.now(zero_offset_tz)
        assert is_aware(dt) is True


class TestEnsureAware:
    """Test ensure_aware() function."""

    def test_with_naive_datetime_default_utc(self):
        """ensure_aware() should add UTC timezone to naive datetime."""
        naive_dt = datetime(2022, 1, 1, 12, 0, 0)
        aware_dt = ensure_aware(naive_dt)
        assert is_aware(aware_dt)
        assert aware_dt.tzinfo == UTC

    def test_with_naive_datetime_custom_timezone(self):
        """ensure_aware() should add specified timezone to naive datetime."""
        naive_dt = datetime(2022, 1, 1, 12, 0, 0)
        custom_tz = timezone(timedelta(hours=5))
        aware_dt = ensure_aware(naive_dt, custom_tz)
        assert is_aware(aware_dt)
        assert aware_dt.tzinfo == custom_tz

    def test_with_already_aware_datetime(self):
        """ensure_aware() should return aware datetime unchanged."""
        original_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=UTC)
        result_dt = ensure_aware(original_dt)
        assert result_dt is original_dt
        assert result_dt.tzinfo == UTC

    def test_preserves_time_components(self):
        """ensure_aware() should preserve all time components."""
        naive_dt = datetime(2022, 5, 15, 14, 30, 45, 123456)
        aware_dt = ensure_aware(naive_dt)
        assert aware_dt.year == 2022
        assert aware_dt.month == 5
        assert aware_dt.day == 15
        assert aware_dt.hour == 14
        assert aware_dt.minute == 30
        assert aware_dt.second == 45
        assert aware_dt.microsecond == 123456


class TestNaiveToAware:
    """Test naive_to_aware() function."""

    def test_converts_naive_to_aware(self):
        """naive_to_aware() should convert naive datetime to aware."""
        naive_dt = datetime(2022, 1, 1, 12, 0, 0)
        aware_dt = naive_to_aware(naive_dt)
        assert is_aware(aware_dt)
        assert aware_dt.tzinfo == UTC

    def test_with_custom_timezone(self):
        """naive_to_aware() should use specified timezone."""
        naive_dt = datetime(2022, 1, 1, 12, 0, 0)
        custom_tz = timezone(timedelta(hours=-8))
        aware_dt = naive_to_aware(naive_dt, custom_tz)
        assert is_aware(aware_dt)
        assert aware_dt.tzinfo == custom_tz

    def test_raises_error_with_aware_datetime(self):
        """naive_to_aware() should raise error with already aware datetime."""
        aware_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=UTC)
        with pytest.raises(ValueError, match="datetime is already timezone-aware"):
            naive_to_aware(aware_dt)

    def test_preserves_time_components(self):
        """naive_to_aware() should preserve all time components."""
        naive_dt = datetime(2022, 8, 20, 16, 45, 30, 987654)
        aware_dt = naive_to_aware(naive_dt)
        assert aware_dt.year == 2022
        assert aware_dt.month == 8
        assert aware_dt.day == 20
        assert aware_dt.hour == 16
        assert aware_dt.minute == 45
        assert aware_dt.second == 30
        assert aware_dt.microsecond == 987654


class TestAwareToNaive:
    """Test aware_to_naive() function."""

    def test_converts_aware_to_naive_preserve_utc(self):
        """aware_to_naive() should convert to naive UTC time by default."""
        # Create aware datetime in different timezone
        eastern_tz = timezone(timedelta(hours=-5))
        aware_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=eastern_tz)
        naive_dt = aware_to_naive(aware_dt, preserve_utc=True)

        assert is_naive(naive_dt)
        # Should be converted to UTC (17:00 UTC = 12:00 EST)
        assert naive_dt.hour == 17

    def test_converts_aware_to_naive_no_preserve(self):
        """aware_to_naive() should strip timezone without conversion."""
        eastern_tz = timezone(timedelta(hours=-5))
        aware_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=eastern_tz)
        naive_dt = aware_to_naive(aware_dt, preserve_utc=False)

        assert is_naive(naive_dt)
        # Should keep local time (12:00)
        assert naive_dt.hour == 12

    def test_raises_error_with_naive_datetime(self):
        """aware_to_naive() should raise error with already naive datetime."""
        naive_dt = datetime(2022, 1, 1, 12, 0, 0)
        with pytest.raises(ValueError, match="datetime is already naive"):
            aware_to_naive(naive_dt)

    def test_with_utc_timezone(self):
        """aware_to_naive() should handle UTC timezone correctly."""
        aware_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=UTC)
        naive_dt = aware_to_naive(aware_dt)

        assert is_naive(naive_dt)
        assert naive_dt.hour == 12  # UTC time preserved


class TestSafeCompare:
    """Test safe_compare() function."""

    def test_compare_same_aware_datetimes(self):
        """safe_compare() should correctly compare identical aware datetimes."""
        dt1 = datetime(2022, 1, 1, 12, 0, 0, tzinfo=UTC)
        dt2 = datetime(2022, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert safe_compare(dt1, dt2) == 0

    def test_compare_different_aware_datetimes(self):
        """safe_compare() should correctly compare different aware datetimes."""
        dt1 = datetime(2022, 1, 1, 11, 0, 0, tzinfo=UTC)
        dt2 = datetime(2022, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert safe_compare(dt1, dt2) == -1
        assert safe_compare(dt2, dt1) == 1

    def test_compare_same_naive_datetimes(self):
        """safe_compare() should correctly compare identical naive datetimes."""
        dt1 = datetime(2022, 1, 1, 12, 0, 0)
        dt2 = datetime(2022, 1, 1, 12, 0, 0)
        assert safe_compare(dt1, dt2) == 0

    def test_compare_different_naive_datetimes(self):
        """safe_compare() should correctly compare different naive datetimes."""
        dt1 = datetime(2022, 1, 1, 11, 0, 0)
        dt2 = datetime(2022, 1, 1, 12, 0, 0)
        assert safe_compare(dt1, dt2) == -1
        assert safe_compare(dt2, dt1) == 1

    def test_compare_mixed_awareness(self):
        """safe_compare() should handle mixed aware/naive datetimes."""
        naive_dt = datetime(2022, 1, 1, 12, 0, 0)
        aware_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=UTC)
        # Both should be treated as UTC for comparison
        assert safe_compare(naive_dt, aware_dt) == 0

    def test_compare_different_timezones(self):
        """safe_compare() should normalize timezones for comparison."""
        utc_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=UTC)
        eastern_tz = timezone(timedelta(hours=-5))
        eastern_dt = datetime(2022, 1, 1, 7, 0, 0, tzinfo=eastern_tz)  # Same as 12:00 UTC
        assert safe_compare(utc_dt, eastern_dt) == 0


class TestAssertDatetimeAware:
    """Test assert_datetime_aware() function."""

    def test_with_aware_datetime(self):
        """assert_datetime_aware() should return aware datetime unchanged."""
        aware_dt = datetime(2022, 1, 1, 12, 0, 0, tzinfo=UTC)
        result = assert_datetime_aware(aware_dt, "test context")
        assert result is aware_dt

    def test_with_naive_datetime_issues_warning(self):
        """assert_datetime_aware() should warn about naive datetimes."""
        naive_dt = datetime(2022, 1, 1, 12, 0, 0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = assert_datetime_aware(naive_dt, "test context")

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "Naive datetime detected in test context" in str(w[0].message)
            assert result is naive_dt

    def test_warning_includes_context(self):
        """assert_datetime_aware() warning should include context string."""
        naive_dt = datetime(2022, 1, 1, 12, 0, 0)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            assert_datetime_aware(naive_dt, "user registration")

            assert "user registration" in str(w[0].message)


class TestLegacyCompatibility:
    """Test legacy compatibility functions."""

    def test_utcnow_compat_returns_aware_datetime(self):
        """utcnow_compat() should return aware datetime and warn."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            dt = utcnow_compat()

            assert is_aware(dt)
            assert dt.tzinfo == UTC
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "utcnow_compat() is deprecated" in str(w[0].message)

    def test_utcfromtimestamp_compat_returns_aware_datetime(self):
        """utcfromtimestamp_compat() should return aware datetime and warn."""
        timestamp = 1640995200.0
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            dt = utcfromtimestamp_compat(timestamp)

            assert is_aware(dt)
            assert dt.tzinfo == UTC
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "utcfromtimestamp_compat() is deprecated" in str(w[0].message)


class TestPythonVersionCompatibility:
    """Test Python version-specific behavior."""

    def test_utc_constant_type(self):
        """UTC constant should be correct type for Python version."""
        # Should work regardless of Python version
        assert UTC is not None
        dt = datetime.now(UTC)
        assert dt.tzinfo is UTC

    def test_cross_version_consistency(self):
        """Functions should behave consistently across Python versions."""
        # These operations should work the same on all supported versions
        now = utc_now()
        timestamp = now.timestamp()
        recreated = utc_from_timestamp(timestamp)

        # Should be very close (within 1 second due to execution time)
        diff = abs((now - recreated).total_seconds())
        assert diff < 1.0


@pytest.mark.parametrize("timezone_offset", [-12, -8, -5, 0, 3, 8, 12])
def test_timezone_conversion_edge_cases(timezone_offset):
    """Test timezone conversions with various offsets."""
    custom_tz = timezone(timedelta(hours=timezone_offset))
    local_time = datetime(2022, 6, 15, 12, 0, 0, tzinfo=custom_tz)

    # Convert to naive UTC
    naive_utc = aware_to_naive(local_time, preserve_utc=True)

    # Convert back to aware
    aware_utc = naive_to_aware(naive_utc, UTC)

    # Should be equivalent to original converted to UTC
    expected_utc = local_time.astimezone(UTC)
    assert safe_compare(aware_utc, expected_utc) == 0


@pytest.mark.parametrize("microseconds", [0, 1, 999999])
def test_microsecond_precision(microseconds):
    """Test that microsecond precision is preserved."""
    timestamp = 1640995200.0 + (microseconds / 1_000_000)
    dt = utc_from_timestamp(timestamp)
    assert dt.microsecond == microseconds
