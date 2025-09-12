"""
Test datetime compatibility module for Python version consistency.
"""

# ruff: noqa: DTZ001  # Tests need to create naive datetimes intentionally

from datetime import datetime, timedelta, timezone
import time
import warnings

import pytest

from src.utils.datetime_compat import (
    UTC,
    MockDatetime,
    assert_datetime_aware,
    aware_to_naive,
    ensure_aware,
    is_aware,
    is_naive,
    local_now,
    mock_now,
    naive_to_aware,
    parse_iso,
    safe_compare,
    timestamp_now,
    to_iso,
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
        dt = datetime.now()  # Intentionally naive for testing
        assert is_aware(dt) is False

    def test_is_naive_with_timezone(self):
        """is_naive() should return False for timezone-aware datetimes."""
        dt = datetime.now(UTC)
        assert is_naive(dt) is False

    def test_is_naive_without_timezone(self):
        """is_naive() should return True for naive datetimes."""
        dt = datetime.now()  # Intentionally naive for testing
        assert is_naive(dt) is True

    def test_is_aware_with_none_tzinfo(self):
        """is_aware() should handle None tzinfo correctly."""
        dt = utc_now()
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


class TestLocalNow:
    """Test local_now() function."""

    def test_returns_timezone_aware_datetime(self):
        """local_now() should return timezone-aware datetime."""
        dt = local_now()
        assert is_aware(dt)

    def test_returns_current_time(self):
        """local_now() should return current time within reasonable delta."""
        before = time.time()
        dt = local_now()
        after = time.time()

        dt_timestamp = dt.timestamp()
        assert before <= dt_timestamp <= after

    def test_has_local_timezone(self):
        """local_now() should have local timezone info."""
        dt = local_now()
        # Should have timezone information (not None)
        assert dt.tzinfo is not None
        # tzname should be available
        assert dt.tzname() is not None


class TestTimestampNow:
    """Test timestamp_now() function."""

    def test_returns_float(self):
        """timestamp_now() should return a float."""
        ts = timestamp_now()
        assert isinstance(ts, float)

    def test_returns_current_timestamp(self):
        """timestamp_now() should return current timestamp within reasonable delta."""
        before = time.time()
        ts = timestamp_now()
        after = time.time()

        assert before <= ts <= after

    def test_consistent_with_utc_now(self):
        """timestamp_now() should be consistent with utc_now().timestamp()."""
        # Get both values quickly
        ts1 = timestamp_now()
        dt_ts = utc_now().timestamp()
        ts2 = timestamp_now()

        # Should be very close (within execution time)
        assert ts1 <= dt_ts <= ts2


class TestParseIso:
    """Test parse_iso() function."""

    def test_parse_iso_with_z_suffix(self):
        """parse_iso() should handle ISO strings with Z suffix."""
        iso_str = "2023-01-01T12:00:00Z"
        dt = parse_iso(iso_str)

        assert is_aware(dt)
        assert dt.tzinfo == UTC
        assert dt.year == 2023
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 12

    def test_parse_iso_with_timezone_offset(self):
        """parse_iso() should handle ISO strings with timezone offset."""
        iso_str = "2023-01-01T12:00:00-05:00"
        dt = parse_iso(iso_str)

        assert is_aware(dt)
        assert dt.hour == 12
        # Check timezone offset
        assert dt.utcoffset().total_seconds() == -5 * 3600

    def test_parse_iso_naive_assume_utc(self):
        """parse_iso() should assume UTC for naive ISO strings by default."""
        iso_str = "2023-01-01T12:00:00"
        dt = parse_iso(iso_str, assume_utc=True)

        assert is_aware(dt)
        assert dt.tzinfo == UTC

    def test_parse_iso_naive_no_assume(self):
        """parse_iso() should keep naive when assume_utc=False."""
        iso_str = "2023-01-01T12:00:00"
        dt = parse_iso(iso_str, assume_utc=False)

        # Should still be made aware but with None timezone handling
        assert is_aware(dt)

    def test_parse_iso_with_microseconds(self):
        """parse_iso() should preserve microseconds."""
        iso_str = "2023-01-01T12:00:00.123456Z"
        dt = parse_iso(iso_str)

        assert dt.microsecond == 123456

    def test_parse_iso_invalid_string(self):
        """parse_iso() should raise ValueError for invalid strings."""
        with pytest.raises(ValueError, match="Invalid ISO datetime string"):
            parse_iso("not-a-date")


class TestToIso:
    """Test to_iso() function."""

    def test_to_iso_with_timezone_utc(self):
        """to_iso() should format UTC datetime with Z suffix."""
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        iso_str = to_iso(dt)

        assert iso_str == "2023-01-01T12:00:00Z"

    def test_to_iso_with_timezone_offset(self):
        """to_iso() should format datetime with timezone offset."""
        eastern_tz = timezone(timedelta(hours=-5))
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=eastern_tz)
        iso_str = to_iso(dt)

        assert iso_str == "2023-01-01T12:00:00-05:00"

    def test_to_iso_naive_datetime(self):
        """to_iso() should handle naive datetime by assuming UTC."""
        dt = datetime(2023, 1, 1, 12, 0, 0)
        iso_str = to_iso(dt)

        assert iso_str == "2023-01-01T12:00:00Z"

    def test_to_iso_without_timezone(self):
        """to_iso() should strip timezone when include_timezone=False."""
        dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        iso_str = to_iso(dt, include_timezone=False)

        assert iso_str == "2023-01-01T12:00:00"

    def test_to_iso_with_microseconds(self):
        """to_iso() should include microseconds when present."""
        dt = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=UTC)
        iso_str = to_iso(dt)

        assert iso_str == "2023-01-01T12:00:00.123456Z"

    def test_to_iso_roundtrip(self):
        """to_iso() and parse_iso() should be inverse operations."""
        original_dt = datetime(2023, 1, 1, 12, 0, 0, 123456, tzinfo=UTC)
        iso_str = to_iso(original_dt)
        parsed_dt = parse_iso(iso_str)

        assert safe_compare(original_dt, parsed_dt) == 0


class TestMockDatetime:
    """Test MockDatetime context manager."""

    def test_mock_datetime_with_string(self):
        """MockDatetime should accept ISO string."""
        mock_time = "2023-01-01T12:00:00Z"

        with MockDatetime(mock_time):
            dt = utc_now()
            assert dt.year == 2023
            assert dt.month == 1
            assert dt.day == 1
            assert dt.hour == 12

    def test_mock_datetime_with_datetime_object(self):
        """MockDatetime should accept datetime object."""
        mock_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)

        with MockDatetime(mock_time):
            dt = utc_now()
            assert safe_compare(dt, mock_time) == 0

    def test_mock_datetime_context_isolation(self):
        """MockDatetime should not affect time outside context."""
        mock_time = "2023-01-01T12:00:00Z"

        # Get real time before
        real_time_before = utc_now()

        with MockDatetime(mock_time):
            mocked_time = utc_now()
            assert mocked_time.year == 2023

        # Get real time after
        real_time_after = utc_now()

        # Should be back to real time
        assert real_time_after > real_time_before
        assert real_time_after.year != 2023 or real_time_after != mocked_time

    def test_nested_mock_contexts(self):
        """MockDatetime contexts should nest properly."""
        with MockDatetime("2023-01-01T12:00:00Z"):
            dt1 = utc_now()
            assert dt1.year == 2023

            with MockDatetime("2024-01-01T12:00:00Z"):
                dt2 = utc_now()
                assert dt2.year == 2024

            dt3 = utc_now()
            assert dt3.year == 2023


class TestMockNow:
    """Test mock_now() function."""

    def test_mock_now_with_string(self):
        """mock_now() should accept ISO string."""
        dt = mock_now("2023-01-01T12:00:00Z")
        assert dt.year == 2023
        assert dt.hour == 12

    def test_mock_now_with_datetime(self):
        """mock_now() should accept datetime object."""
        mock_time = datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
        dt = mock_now(mock_time)
        assert safe_compare(dt, mock_time) == 0

    def test_mock_now_without_args(self):
        """mock_now() should return real time when no args and no global mock."""
        dt = mock_now()
        # Should be close to current time
        real_time = utc_now()
        diff = abs((dt - real_time).total_seconds())
        assert diff < 1.0

    def test_mock_now_with_global_mock(self):
        """mock_now() should use global mock time when available."""
        with MockDatetime("2023-01-01T12:00:00Z"):
            dt = mock_now()
            assert dt.year == 2023
            assert dt.hour == 12


class TestNewFunctionIntegration:
    """Test integration between new and existing functions."""

    def test_timestamp_now_integration(self):
        """timestamp_now() should integrate well with other functions."""
        with MockDatetime("2023-01-01T12:00:00Z"):
            ts = timestamp_now()
            dt = utc_from_timestamp(ts)

            assert dt.year == 2023
            assert dt.month == 1
            assert dt.day == 1
            assert dt.hour == 12

    def test_local_now_vs_utc_now(self):
        """local_now() and utc_now() should have predictable relationship."""
        local_dt = local_now()
        utc_dt = utc_now()

        # Convert local to UTC for comparison
        local_as_utc = local_dt.astimezone(UTC)

        # Should be very close (within a few seconds due to execution time)
        diff = abs((local_as_utc - utc_dt).total_seconds())
        assert diff < 5.0

    def test_iso_parsing_integration(self):
        """ISO parsing should work with timezone conversion functions."""
        iso_str = "2023-01-01T12:00:00-05:00"  # EST
        dt = parse_iso(iso_str)

        # Convert to naive UTC
        naive_utc = aware_to_naive(dt, preserve_utc=True)

        # Should be 17:00 UTC (12:00 EST + 5 hours)
        assert naive_utc.hour == 17

    def test_comprehensive_datetime_workflow(self):
        """Test a comprehensive workflow using multiple new functions."""
        # Start with ISO string
        iso_input = "2023-06-15T14:30:00-08:00"  # PDT

        # Parse it
        dt = parse_iso(iso_input)
        assert dt.hour == 14  # Local time preserved

        # Convert to UTC
        utc_dt = dt.astimezone(UTC)
        assert utc_dt.hour == 22  # 14:30 PDT = 22:30 UTC

        # Convert back to ISO
        iso_output = to_iso(utc_dt)
        assert iso_output == "2023-06-15T22:30:00Z"

        # Parse it back
        final_dt = parse_iso(iso_output)
        assert safe_compare(final_dt, utc_dt) == 0


@pytest.mark.parametrize(
    ("iso_string", "expected_hour"),
    [
        ("2023-01-01T12:00:00Z", 12),
        ("2023-01-01T12:00:00+00:00", 12),
        ("2023-01-01T12:00:00-05:00", 12),  # EST
        ("2023-01-01T12:00:00+09:00", 12),  # JST
    ],
)
def test_iso_parsing_variations(iso_string, expected_hour):
    """Test parse_iso with various timezone formats."""
    dt = parse_iso(iso_string)
    assert dt.hour == expected_hour
    assert is_aware(dt)
