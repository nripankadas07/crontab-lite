"""Tests for next_fire function."""
import pytest
from datetime import datetime
from crontab_lite import parse, next_fire, CrontabError


class TestNextFireBasic:
    """Test basic next_fire functionality."""

    def test_next_fire_every_minute(self):
        """Find next occurrence for '* * * * *'."""
        expr = "* * * * *"
        dt = datetime(2026, 4, 15, 12, 30, 45)
        result = next_fire(expr, dt)
        # Should be next minute boundary
        assert result == datetime(2026, 4, 15, 12, 31, 0)

    def test_next_fire_with_parsed_expression(self):
       """Find next occurrence using parsed CronExpression."""
        expr = parse("30 12 * * *")
        dt = datetime(2026, 4, 15, 12, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 30)

    def test_next_fire_next_day(self):
        """Find next occurrence on next day."""
        expr = "0 12 * * *"
        dt = datetime(2026, 4, 15, 13, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 16, 12, 0)

    def test_next_fire_next_month(self):
        """Find next occurrence in next month."""
        expr = "0 0 1 * *"
        dt = datetime(2026, 4, 15, 12, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 5, 1, 0, 0)

    def test_next_fire_specific_values(self):
        """Find next occurrence with specific minute and hour."""
        expr = "30 14 * * *"
        dt = datetime(2026, 4, 15, 14, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 14, 30)

    def test_next_fire_with_list_values(self):
        """Find next occurrence matching list values."""
        expr = "0 9,12,15,1 * * *"
        dt = datetime(2026, 4, 15, 10, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 0)

    def test_next_fire_with_range(self):
        """Find next occurrence within range."""
        expr = "0 9-17 * * *"
        dt = datetime(2026, 4, 15, 8, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 9, 0)

    def test_next_fire_with_step(self):
        """Find next occurrence with step."""
        expr = "*/15 * * * *"
        dt = datetime(2026, 4, 15, 12, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 15)


class TestNextFireRealWorld:
    """Test real-world scenarios for next_fire."""

    def test_next_fire_hourly_job(self):
        """0 * * * * - next hourly job."""
        expr = "0 * * * *"
        dt = datetime(2026, 4, 15, 12, 30)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 13, 0)

    def test_next_fire_daily_noon(self):
        """0 12 * * * - next daily job at noon."""
        expr = "0 12 * * *"
        dt = datetime(2026, 4, 15, 11, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 0)

    def test_next_fire_weekdays_9am(self):
        """0 9 * * 1-5 - next weekday at 9am."""
        expr = "0 9 * * 1-5"
        # Saturday April 18, 2026
        dt = datetime(2026, 4, 18, 8, 0)
        result = next_fire(expr, dt)
        # Should be Monday April 20, 2026
        assert result == datetime(2026, 4, 20, 9, 0)

    def test_next_fire_monthly(self):
        """0 0 15 * * - 15th of month at midnight."""
        expr = "0 0 15 * *"
        dt = datetime(2026, 4, 14, 12, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 0, 0)

    def test_next_fire_business_hours(self):
        """0 9-17 * * 1-5 - within business hours."""
        expr = "0 9-17 * * 1-5"
        # Monday April 13, 10am
        dt = datetime(2026, 4, 13, 10, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 13, 11, 0)

    def test_next_fire_past_end_of_range(self):
        """Find next when current time is past the range."""
        expr = "0 9-17 * * 1-5"
        # Monday April 13, 18:00 (after business hours)
        dt = datetime(2026, 4, 13, 18, 0)
        result = next_fire(expr, dt)
        # Should be Tuesday 9am
        assert result == datetime(2026, 4, 14, 9, 0)


class TestNextFireAfterParameter:
    """Test the 'after' parameter (default behavior)."""

    def test_next_fire_no_after_uses_now(self):
        """Without 'after', should use current time."""
        expr = "0 * * * *"
        # Function should work without explicit after parameter
        result = next_fire(expr)
        # Should be a future datetime
        assert isinstance(result, datetime)

    def test_next_fire_after_parameter(self):
        """Explicitly pass 'after' parameter."""
        expr = "0 12 * * *"
        dt = datetime(2026, 4, 15, 11, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 12, 0)


class TestNextFireDayOfWeek:
    """Test next_fire with day-of-week constraints."""

    def test_next_fire_dow_with_7_is_sunday(self):
        """Day-of-week 7 should be treated as Sunday."""
        expr = "0 9 * * 7"
        # Tuesday April 14
        dt = datetime(2026, 4, 14, 8, 0)
        result = next_fire(expr, dt)
        # Should be Sunday April 19
        assert result == datetime(2026, 4, 19, 9, 0)

    def test_next_fire_dow_0_is_sunday(self):
        """Day-of-week 0 should be Sunday."""
        expr = "0 9 * * 0"
        # Tuesday April 14
        dt = datetime(2026, 4, 14, 8, 0)
        result = next_fire(expr, dt)
        # Should be Sunday April 19
        assert result == datetime(2026, 4, 19, 9, 0)

    def test_next_fire_dow_list(self):
        """Find next matching day from list."""
        expr = "0 9 * * 1,4,7,10 *"  # Monday, Wednesday, Friday
        # Tuesday April 14
        dt = datetime(2026, 4, 14, 8, 0)
        result = next_fire(expr, dt)
        # Should be Wednesday April 15
        assert result == datetime(2026, 4, 15, 9, 0)


class TestNextFireMonth:
    """Test next_fire with month constraints."""

    def test_next_fire_specific_month(self):
        """Find next occurrence in specific month."""
        expr = "0 0 1 6 *"
        dt = datetime(2026, 4, 15, 12, 0)
        result = next_fire(expr, dt)
        # Should be June 1
        assert result == datetime(2026, 6, 1, 0, 0)

    def test_next_fire_month_list(self):
        """Find next occurrence in list of months."""
        expr = "0 0 1 1,4,7,10 *"  # Quarterly
        dt = datetime(2026, 2, 15, 12, 0)
        result = next_fire(expr, dt)
        # Should be April 1
        assert result == datetime(2026, 4, 1, 0, 0)

    def test_next_fire_month_wraps_year(self):
        """Find next occurrence wrapping to next year."""
        expr = "0 0 1 1 *"
        dt = datetime(2026, 12, 15, 12, 0)
        result = next_fire(expr, dt)
        # Should be January 1, 2027
        assert result == datetime(2027, 1, 1, 0, 0)


class TestNextFireDayOfMonth:
    """Test next_fire with day-of-month constraints."""

    def test_next_fire_specific_dom(self):
        """Find next occurrence on specific day of month."""
        expr = "0 0 15 * *"
        dt = datetime(2026, 4, 10, 12, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 0, 0)

    def test_next_fire_dom_wraps_month(self):
        """Find next when day occurs in next month."""
        expr = "0 0 15 * *"
        dt = datetime(2026, 4, 20, 12, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 5, 15, 0, 0)

    def test_next_fire_dom_31(self):
        """Handle day 31 in months with fewer days."""
        expr = "0 0 31 * *"
        dt = datetime(2026, 4, 15, 12, 0)
        result = next_fire(expr, dt)
        # Next month with 31 days is May
        assert result == datetime(2026, 5, 31, 0, 0)


class TestNextFireErrors:
    """Test error handling in next_fire."""

    def test_next_fire_invalid_expression(self):
        """Reject invalid expression."""
        with pytest.raises(CrontabError):
            next_fire("invalid", datetime(2026, 4, 15, 12, 0))

    def test_next_fire_aware_datetime(self):
        """Reject timezone-aware datetime."""
        from datetime import timezone
        dt = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)
        with pytest.raises(CrontabError):
            next_fire("* * * * *", dt)

    def test_next_fire_impossible_expression(self):
        """Handle impossible expressions (e.g., Feb 31)."""
        # Feb 31 doesn't exist, but expression is syntactically valid
        expr = "0 0 31 2 *"
        dt = datetime(2026, 4, 15, 12, 0)
        # Should not find a match within reasonable bounds
        # This tests the timeout/max iteration behavior
        try:
            result = next_fire(expr, dt)
            # If it returns, should be way in the future or raise
            assert result is None or result.year > 2100
        except CrontabError:
            # Also acceptable: raise an error for impossible expression
            pass


class TestNextFireLeapYear:
    """Test next_fire with leap year considerations."""

    def test_next_fire_feb_29_leap_year(self):
        """Find next occurrence of Feb 29 (leap year)."""
        expr = "0 0 29 2 *"
        # 2024 is a leap year
        dt = datetime(2024, 2, 28, 12, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2024, 2, 29, 0, 0)

    def test_next_fire_feb_29_skips_non_leap(self):
        """Feb 29 should skip non-leap years."""
        expr = "0 0 29 2 *"
        # Start from Feb 2026 (non-leap year)
        dt = datetime(2026, 2, 15, 12, 0)
        result = next_fire(expr, dt)
        # Should skip to 2028 (next leap year)
        assert result.year == 2028
        assert result.month == 2
        assert result.day == 29
