"""Tests for edge cases and special scenarios."""
import pytest
from datetime import datetime
from crontab_lite import parse, matches, next_fire, prev_fire, CrontabError


class TestEdgeCasesWhitespace:
    """Test handling of whitespace variations."""

    def test_parse_extra_spaces(self):
        """Handle multiple spaces between fields."""
        expr = parse("*   *   *   *   *")
        assert len(expr.minute) == 60

    def test_parse_leading_trailing_spaces(self):
        """Handle leading and trailing spaces."""
        expr = parse("  * * * * *  ")
        assert len(expr.minute) == 60

    def test_parse_tabs(self):
        """Handle tab characters as delimiters."""
        expr = parse("*\t*\t*\t*\t*")
        assert len(expr.minute) == 60


class TestEdgeCasesRangeStepEdges:
    """Test edge cases with ranges and steps."""

    def test_parse_range_same_start_end(self):
        """Parse range where start equals end."""
        expr = parse("30-30 * * * *")
        assert expr.minute == {30}

    def test_parse_step_1(self):
        """Parse step of 1 (should work but be redundant)."""
        expr = parse("*/1 * * * *")
        assert len(expr.minute) == 60

    def test_parse_large_step(self):
        """Parse step larger than range."""
        expr = parse("0-10/20 * * * *")
        assert expr.minute == {0}

    def test_parse_step_at_boundary(self):
        """Parse step that aligns with boundary."""
        expr = parse("0-59/30 * * * *")
        assert expr.minute == {0, 30}


class TestEdgeCasesSpecialValues:
    """Test special value combinations."""

    def test_parse_zero_values(self):
        """Parse 0 values in valid fields."""
        expr = parse("0 0 * * *")
        assert expr.minute == {0}
        assert expr.hour == {0}

    def test_parse_max_values(self):
        """Parse maximum valid values."""
        expr = parse("59 23 31 12 7")
        assert 59 in expr.minute
        assert 23 in expr.hour
        assert 31 in expr.dom
        assert 12 in expr.month
        assert 7 in expr.dow or 0 in expr.dow  # 7 should map to 0

    def test_parse_mixed_delimiters(self):
        """Parse expression with mixed ranges, lists, and steps."""
        expr = parse("0-30/10,45 5,10-12,15-20/5 * * *")
        # minute: 0,10,20,30,45
        assert 0 in expr.minute
        assert 10 in expr.minute
        assert 45 in expr.minute
        # hour: 5,10,11,12,15,20
        assert 5 in expr.hour
        assert 10 in expr.hour


class TestEdgeCasesDayOfMonthMonth:
    """Test day-of-month and month edge cases."""

    def test_matches_feb_28_non_leap(self):
        """February 28 matches in non-leap years."""
        expr = "* * 28 2 *"
        assert matches(expr, datetime(2026, 2, 28, 10, 0)) is True

    def test_matches_feb_28_leap(self):
        """February 28 matches even in leap years."""
        expr = "* * 28 2 *"
        assert matches(expr, datetime(2024, 2, 28, 10, 0)) is True

    def test_matches_feb_29_leap(self):
       """February 29 matches only in leap years."""
        expr = "* * 29 2 *"
        assert matches(expr, datetime(2024, 2, 29, 10, 0)) is True

    def test_matches_dom_30_in_april(self):
        """Day 30 in April (has 30 days)."""
        expr = "* * 30 4 *"
        assert matches(expr, datetime(2026, 4, 30, 10, 0)) is True

    def test_matches_dom_31_in_april(self):
       """Day 31 in April (has only 30 days)."""
        expr = "* * 31 4 *"
        assert matches(expr, datetime(2026, 4, 30, 10, 0)) is False

    def test_parse_dom_values_30_31(self):
       """Parse expressions with day 30 and 31."""
        expr = parse("* * 30,31 * *")
        assert 30 in expr.dom
        assert 31 in expr.dom


class TestEdgeCasesListEdges:
    """Test list parsing edge cases."""

    def test_parse_single_item_list(self):
        """Parse list with single item (edge case)."""
        expr = parse("5 * * * *")
        assert expr.minute == {5}

    def test_parse_list_unsorted(self):
       """Parse list with unsorted values."""
        expr = parse("45,10,30 * * * *")
        assert expr.minute == {15, 30, 45}

    def test_parse_list_duplicates(self):
        """Parse list with duplicate values."""
        expr = parse("5,5,5 * * * *")
        assert expr.minute == {5}

    def test_parse_list_with_range(self):
       """Parse list containing range."""
        expr = parse("1-3,5,7-9 * * * *")
        assert expr.minute == {1, 2, 3, 5, 7, 8, 9}


class TestEdgeCasesMonthYear:
    """Test month and year-boundary edge cases."""

    def test_next_fire_december_to_january(self):
       """next_fire wraps from December to January of next year."""
        expr = "0 0 1 1 *"
        dt = datetime(2026, 12, 15, 12, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2027, 1, 1, 0, 0)

    def test_prev_fire_january_to_december(self):
        """prev_fire wraps from January to December of previous year."""
        expr = "0 0 1 12 *"
        dt = datetime(2026, 1, 15, 12, 0)
        result = prev_fire(expr, dt)
        assert result == datetime(2025, 12, 1, 0, 0)

    def test_next_fire_december_31(self):
        """next_fire from Dec 31."""
        expr = "0 0 1 * *"
        dt = datetime(2026, 12, 31, 12, 0)
        result = next_fire(expr, dt)
        assert result == datetime(2027, 1, 1, 0, 0)

    def test_prev_fire_january_1(self):
        """prev_fire from Jan 1."""
        expr = "0 0 1 * *"
        dt = datetime(2026, 1, 1, 0, 1)
        result = prev_fire(expr, dt)
        # Should wrap to Dec 31 of previous year (last day)
        # Actually should go to previous month's 1st
        assert result.day == 1


class TestEdgeCasesTimeOfDay:
    """Test time-of-day edge cases."""

    def test_next_fire_midnight(self):
        """next_fire crossing midnight."""
        expr = "0 0 * * *"
        dt = datetime(2026, 4, 15, 23, 30)
        result = next_fire(expr, dt)
        assert result == datetime(2026, 4, 16, 0, 0)

    def test_prev_fire_midnight(self):
        """prev_fire crossing midnight backwards."""
        expr = "0 0 * * *"
        dt = datetime(2026, 4, 15, 0, 1)
        result = prev_fire(expr, dt)
        assert result == datetime(2026, 4, 15, 0, 0)

    def test_next_fire_exact_match(self):
       """next_fire when current time is exact match."""
        expr = "30 12 * * *"
        dt = datetime(2026, 4, 15, 12, 30)
        result = next_fire(expr, dt)
        # Should be next day, not same time
        assert result == datetime(2026, 4, 16, 12, 30)

    def test_prev_fire_exact_match(self):
        """prev_fire when current time is exact match."""
        expr = "30 12 * * *"
        dt = datetime(2026, 4, 15, 12, 30)
        result = prev_fire(expr, dt)
        # Should be previous day, not same time
        assert result == datetime(2026, 4, 14, 12, 30)


class TestEdgeCasesInvalidSyntax:
    """Test various invalid syntax patterns."""

    def test_parse_empty_field(self):
        """Reject empty field."""
        with pytest.raises(CrontabError):
            parse("* * * * ")

    def test_parse_double_dash(self):
        """Reject double dash."""
        with pytest.raises(CrontabError):
            parse("1-5 * * * *")

    def test_parse_leading_dash(self):
        """Reject leading dash (not a negative number context)."""
        with pytest.raises(CrontabError):
            parse("-5 * * * *")

    def test_parse_trailing_dash(self):
        """Reject trailing dash in range."""
        with pytest.raises(CrontabError):
            parse("1- * * * *")

    def test_parse_slash_no_step(self):
        """Reject slash without step value."""
        with pytest.raises(CrontabError):
            parse("*/   * * * *")

    def test_parse_multiple_slashes(self):
        """Reject multiple slashes."""
        with pytest.raises(CrontabError):
            parse("*/5/2 * * * *")

    def test_parse_invalid_characters(self):
        """Reject invalid characters."""
        with pytest.raises(CrontabError):
            parse("* * * * &")

        with pytest.raises(CrontabError):
            parse("* * * * @")


class TestEdgeCasesComplexExpressions:
    """Test complex real-world expressions."""

    def test_parse_complex_expression(self):
        """Parse complex expression with multiple features."""
        expr = parse("0,15,30,45 9-17 1-7,15-20 * 1-5")
        assert expr.minute == {0, 15, 30, 45}
        assert len(expr.hour) == 9  # 9-17 inclusive
        assert len(expr.dow) == 5  # 1-5 inclusive

    def test_matches_complex_expression(self):
        """Match against complex expression."""
        expr = "0,30 9-17 1-7,15-20 * 1-5"
        # Tuesday April 7, 2026 at 9:30 (within 1-7 dom range, weekday)
        assert matches(expr, datetime(2026, 4, 7, 9, 30)) is True
        # Out of hour range
        assert matches(expr, datetime(2026, 4, 7, 8, 30)) is False
        # Out of dom range
        assert matches(expr, datetime(2026, 4, 10, 9, 30)) is False
        # Weekend
        assert matches(expr, datetime(2026, 4, 11, 9, 30)) is False

    def test_next_fire_complex_expression(self):
        """Find next occurrence of complex expression."""
        expr = "0,30 9-17 1-7,15-20 * 1-5"
        dt = datetime(2026, 4, 6, 8, 0)  # Monday (within 1-7 dom)
        result = next_fire(expr, dt)
        # Should be same day at 9:00
        assert result.day == 6
        assert result.hour == 9
        assert result.minute == 0


class TestEdgeCasesStepBoundaries:
    """Test step calculation at boundaries."""

    def test_parse_step_at_min(self):
        """Step starting at minimum value."""
        expr = parse("0-59/15 * * * *")
        assert 0 in expr.minute
        assert 15 in expr.minute
        assert 30 in expr.minute
        assert 45 in expr.minute

    def test_parse_step_at_max(self):
        """Step ending near maximum value."""
        expr = parse("0-59/20 * * * *")
        assert 0 in expr.minute
        assert 20 in expr.minute
        assert 40 in expr.minute

    def test_parse_hour_step(self):
        """Step in hours field."""
        expr = parse("* 0-23/6 * * *")
        assert 0 in expr.hour
        assert 6 in expr.hour
        assert 12 in expr.hour
        assert 18 in expr.hour

    def test_parse_month_step(self):
        """Step in months field."""
        expr = parse("* * * 1-12/3 *")
        assert 1 in expr.month
        assert 4 in expr.month
        assert 7 in expr.month
        assert 10 in expr.month
