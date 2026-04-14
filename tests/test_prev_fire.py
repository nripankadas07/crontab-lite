"""Tests for prev_fire function."""
import pytest
from datetime import datetime
from crontab_lite import parse, prev_fire, CrontabError


class TestPrevFireBasic:
    """Test basic prev_fire functionality."""

    def test_prev_fire_every_minute(self):
        """Find previous occurrence for '* * * * *'."""
        expr = "* * * * *"
        dt = datetime(2026, 4, 15, 12, 30, 45)
        result = prev_fire(expr, dt)
        # Should be previous minute (12:29)
        assert result == datetime(2026, 4, 15, 12, 29, 0)

    def test_prev_fire_with_parsed_expression(self):
        """Find previous occurrence using parsed CronExpression."""
        expr = parse("30 12 * * *")
        dt = datetime(2026, 4, 15, 13, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 30)

    def test_prev_fire_previous_day(self):
        """Find previous occurrence on previous day."""
        expr = "0 12 * * *"
        dt = datetime(2026, 4, 15, 11, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 14, 12, 0)

    def test_prev_fire_previous_month(self):
        """Find previous occurrence in previous month."""
        expr = "0 0 1 * *"
        dt = datetime(2026, 4, 15, 12, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 1, 0, 0)

    def test_prev_fire_specific_values(self):
        """Find previous occurrence with specific minute and hour."""
        expr = "30 14 * * *"
        dt = datetime(2026, 4, 15, 15, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 14, 30)

    def test_prev_fire_with_list_values(self):
        """Find previous occurrence matching list values."""
        expr = "0 9,12,15,18 * * *"
        dt = datetime(2026, 4, 15, 17, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 15, 0)

    def test_prev_fire_with_range(self):
        """Find previous occurrence within range."""
        expr = "0 9-17 * * *"
        dt = datetime(2026, 4, 15, 18, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 17, 0)

    def test_prev_fire_with_step(self):
        """Find previous occurrence with step."""
        expr = "*/15 * * * *"
        dt = datetime(2026, 4, 15, 12, 30)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 15)


class TestPrevFireRealWorld:
    """Test real-world scenarios for prev_fire."""

    def test_prev_fire_hourly_job(self):
        """0 * * * * - previous hourly job."""
        expr = "0 * * * *"
        dt = datetime(2026, 4, 15, 12, 30)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 0)

    def test_prev_fire_daily_noon(self):
        """0 12 * * * - previous daily job at noon."""
        expr = "0 12 * * *"
        dt = datetime(2026, 4, 15, 13, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 0)

    def test_prev_fire_weekdays_9am(self):
        """0 9 * * 1-5 - previous weekday at 9am."""
        expr = "0 9 * * 1-5"
        # Monday April 20, 2026
        dt = datetime(2026, 4, 20, 10, 0)
        result = prev_fire(expr, dt)
        # Should be same Monday 9am
        assert result == datetime(2026, 4, 20, 9, 0)

    def test_prev_fire_weekdays_skip_weekend(self):
        """0 9 * * 1-5 - skip past weekend to previous Friday."""
        expr = "0 9 * * 1-5"
        # Monday April 20, 2026
        dt = datetime(2026, 4, 20, 8, 0)
        result = prev_fire(expr, dt)
        # Should be Friday April 17
        assert result == datetime(2026, 4, 17, 9, 0)

    def test_prev_fire_monthly(self):
        """0 0 15 * * - 15th of month at midnight."""
        expr = "0 0 15 * *"
        dt = datetime(2026, 4, 16, 12, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 0, 0)

    def test_prev_fire_business_hours(self):
        """0 9-17 * * 1-5 - within business hours."""
        expr = "0 9-17 * * 1-5"
        # Monday April 13, 10am
        dt = datetime(2026, 4, 13, 10, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 13, 9, 0)

    def test_prev_fire_before_start_of_range(self):
        """Find previous when current time is before the range."""
        expr = "0 9-17 * * 1-5"
        # Monday April 13, 08:00 (before business hours)
        dt = datetime(2026, 4, 13, 8, 0)
        result = prev_fire(expr, dt)
        # Should be Friday April 10 at 17:00
        assert result == datetime(2026, 4, 10, 17, 0)


class TestPrevFireBeforeParameter:
    """Test the 'before' parameter."""

    def test_prev_fire_no_before_uses_now(self):
        """Without 'before', should use current time."""
        expr = "0 * * * *"
        # Function should work without explicit before parameter
        result = prev_fire(expr)
        # Should be a past datetime
        assert isinstance(result, datetime)

    def test_prev_fire_before_parameter(self):
        """Explicitly pass 'before' parameter."""
        expr = "0 12 * * *"
        dt = datetime(2026, 4, 15, 13, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 0)


class TestPrevFireDayOfWeek:
    """Test prev_fire with day-of-week constraints."""

    def test_prev_fire_dow_with_7_is_sunday(self):
        """Day-of-week 7 should be treated as Sunday."""
        expr = "0 9 * * 7"
        # Tuesday April 14
        dt = datetime(2026, 4, 14, 8, 0)
        result = prev_fire(expr, dt)
        # Should be Sunday April 12
        assert result == datetime(2026, 4, 12, 9, 0)

    def test_prev_fire_dow_0_is_sunday(self):
        """Day-of-week 0 should be Sunday."""
        expr = "0 9 * * 0"
        # Tuesday April 14
        dt = datetime(2026, 4, 14, 8, 0)
        result = prev_fire(expr, dt)
        # Should be Sunday April 12
        assert result == datetime(2026, 4, 12, 9, 0)

    def test_prev_fire_dow_list(self):
        """Find previous matching day from list."""
        expr = "0 9 * * 1,3,5"  # Monday, Wednesday, Friday
        # Saturday April 18
        dt = datetime(2026, 4, 18, 8, 0)
        result = prev_fire(expr, dt)
        # Should be Friday April 17
        assert result == datetime(2026, 4, 17, 9, 0)


class TestPrevFireMonth:
    """Test prev_fire with month constraints."""

    def test_prev_fire_specific_month(self):
        """Find previous occurrence in specific month."""
        expr = "0 0 1 6 *"
        dt = datetime(2026, 7, 15, 12, 0)
        result = prev_fire(expr, dt)
        # Should be June 1
        assert result == datetime(2026, 6, 1, 0, 0)

    def test_prev_fire_month_list(self):
        """Find previous occurrence in list of months."""
        expr = "0 0 1 1,4,7,10 *"  # Quarterly
        dt = datetime(2026, 8, 15, 12, 0)
        result = prev_fire(expr, dt)
        # Should be July 1
        assert result == datetime(2026, 7, 1, 0, 0)

    def test_prev_fire_month_wraps_year(self):
        """Find previous occurrence wrapping to previous year."""
        expr = "0 0 1 12 *"
        dt = datetime(2026, 1, 15, 12, 0)
        result = prev_fire(expr, dt)
        # Should be December 1, 2025
        assert result == datetime(2025, 12, 1, 0, 0)


class TestPrevFireDayOfMonth:
    """Test prev_fire with day-of-month constraints."""

    def test_prev_fire_specific_dom(self):
        """Find previous occurrence on specific day of month."""
        expr = "0 0 15 * *"
        dt = datetime(2026, 4, 20, 12, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 0, 0)

    def test_prev_fire_dom_wraps_month(self):
        """Find previous when day occurs in previous month."""
        expr = "0 0 15 * *"
        dt = datetime(2026, 4, 10, 12, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 3, 15, 0, 0)

    def test_prev_fire_dom_31(self):
        """Handle day 31 in months with fewer days."""
        expr = "0 0 31 * *"
        dt = datetime(2026, 5, 15, 12, 0)
        result = prev_fire(expr, dt)
        # Previous 31st is March 31
        assert result == datetime(2026, 3, 31, 0, 0)


class TestPrevFireErrors:
    """Test error handling in prev_fire."""

    def test_prev_fire_invalid_expression(self):
        """Reject invalid expression."""
        with pytest.raises(CrontabError):
            prev_fire("invalid", datetime(2026, 4, 15, 12, 0))

    def test_prev_fire_aware_datetime(self):
        """Reject timezone-aware datetime."""
        from datetime import timezone
        dt = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)
        with pytest.raises(CrontabError):
            prev_fire("* * * * *", dt)

    def test_prev_fire_impossible_expression(self):
        """Handle impossible expressions (e.g., Feb 31)."""
        # Feb 31 doesn't exist, but expression is syntactically valid
        expr = "0 0 31 2 *"
        dt = datetime(2026, 4, 15, 12, 0)
        # Should not find a match within reasonable bounds
        try:
            result = prev_fire(expr, dt)
            # If it returns, should be way in the past
            assert result is None or result.year < 1900
        except CrontabError:
            # Also acceptable: raise an error for impossible expression
            pass


class TestPrevFireLeapYear:
    """Test prev_fire with leap year considerations."""

    def test_prev_fire_feb_29_leap_year(self):
        """Find previous occurrence of Feb 29 (leap year)."""
        expr = "0 0 29 2 *"
        # March 2024 (2024 is a leap year)
        dt = datetime(2024, 3, 1, 12, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2024, 2, 29, 0, 0)

    def test_prev_fire_feb_29_skips_non_leap(self):
        """Feb 29 should skip non-leap years."""
        expr = "0 0 29 2 *"
        # Start from March 2026 (2026 is not a leap year)
        dt = datetime(2026, 3, 15, 12, 0)
        result = prev_fire(expr, dt)
        # Should skip back to 2024 (previous leap year)
        assert result.year == 2024
        assert result.month == 2
        assert result.day == 29
