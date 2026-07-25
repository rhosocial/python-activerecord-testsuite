# tests/rhosocial/activerecord/testsuite/utils/test_datetime_helpers.py
"""
Tests for the datetime comparison helpers in
``rhosocial.activerecord.testsuite.utils``.

These helpers make round-trip datetime assertions database-agnostic by
tolerating precision truncation done by backends such as Firebird (4-digit
sub-second precision), Oracle DATE (no sub-seconds), and SQL Server
datetime (rounded to 1/300s).
"""
from datetime import datetime, timedelta, timezone

import pytest

from rhosocial.activerecord.testsuite.utils import (
    assert_datetime_equal,
    assert_datetime_close,
)


class TestAssertDatetimeEqual:
    """Behavior of the database-precision-tolerant assertions."""

    def test_identical_naive(self):
        assert_datetime_equal(datetime(2025, 1, 1, 12, 0, 0),
                              datetime(2025, 1, 1, 12, 0, 0))

    def test_within_default_tolerance(self):
        """Default 10ms tolerance crosses Firebird's 4-digit truncation."""
        a = datetime(2025, 1, 1, 12, 0, 0, 124674)
        b = datetime(2025, 1, 1, 12, 0, 0, 124600)
        assert_datetime_equal(a, b)

    def test_outside_tolerance_raises(self):
        a = datetime(2025, 1, 1, 12, 0, 0)
        b = datetime(2025, 1, 1, 12, 0, 1)  # 1 second later
        with pytest.raises(AssertionError):
            assert_datetime_equal(a, b)

    def test_strict_tolerance_when_zero(self):
        """Passing tolerance=timedelta(0) restores strict equality."""
        a = datetime(2025, 1, 1, 12, 0, 0, 124674)
        b = datetime(2025, 1, 1, 12, 0, 0, 124600)
        with pytest.raises(AssertionError):
            assert_datetime_equal(a, b, tolerance=timedelta(0))

    def test_tz_aware_and_naive(self):
        """tz-aware and tz-naive datetimes are normalized for comparison."""
        naive = datetime(2025, 1, 1, 12, 0, 0)
        aware = naive.replace(tzinfo=timezone.utc)
        assert_datetime_equal(naive, aware)

    def test_none_actual_raises(self):
        with pytest.raises(AssertionError):
            assert_datetime_equal(None, datetime(2025, 1, 1))

    def test_none_expected_raises(self):
        with pytest.raises(AssertionError):
            assert_datetime_equal(datetime(2025, 1, 1), None)

    def test_custom_tolerance_within(self):
        a = datetime(2025, 1, 1, 12, 0, 0)
        b = datetime(2025, 1, 1, 12, 0, 1)  # 1 second later
        assert_datetime_equal(a, b, tolerance=timedelta(seconds=2))

    def test_error_message_includes_difference(self):
        a = datetime(2025, 1, 1, 12, 0, 0)
        b = datetime(2025, 1, 1, 12, 0, 1)
        with pytest.raises(AssertionError) as exc_info:
            assert_datetime_equal(a, b, tolerance=timedelta(milliseconds=100))
        msg = str(exc_info.value)
        assert "1000.000 ms" in msg
        assert "100.000 ms" in msg


class TestAssertDatetimeClose:
    """``assert_datetime_close`` is an alias for ``assert_datetime_equal``."""

    def test_alias_behavior(self):
        a = datetime(2025, 1, 1, 12, 0, 0, 124674)
        b = datetime(2025, 1, 1, 12, 0, 0, 124600)
        assert_datetime_close(a, b)
