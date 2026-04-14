"""Tests for cron expression matching."""
import pytest
from datetime import datetime
from crontab_lite import parse, matches, CrontabError


class TestMatchesBasic:
    """Test basic matching of cron expressions against datetimes."""

    def test_matches_every_minute(self):
        """'* * * * *' matches any datetime."""
        dt = datetime(2026, 4, 15, 12, 30)
        assert matches("* * * * *", dt) is True

    def test_matches_specific_minute_hour(self):
        """Match on specific minute and hour."""
        expr = "30 12 * * *"
        assert matches(expr, datetime(2026, 4, 15, 12, 30)) is True
        assert matches(expr, datetime(2026, 4, 15, 12, 31)) is False
        assert matches(expr, datetime(2026, 4, 15, 11, 30)) is False

    def test_matches_specific_dom(self):
        """Match on specific day of month."""
        expr = "* * 15 * *"
        assert matches(expr, datetime(2026, 4, 15, 10, 0)) is True
        assert matches(expr, datetime(2026, 4, 16, 10, 0)) is False

    def test_matches_specific_month(self):
        """Match on specific month."""
        expr = "* * * 6 *"
        assert matches(expr, datetime(2026, 6, 15, 10, 0)) is True
        assert matches(expr, datetime(2026, 5, 15, 10, 0)) is False

    def test_matches_specific_dow(self):
        """Match on specific day of week."""
        expr = "* * * * 1"
        assert matches(expr, datetime(2026, 4, 13, 10, 0)) is True
        assert matches(expr, datetime(2026, 4, 14, 10, 0)) is False

    def test_matches_list_values(self):
        """Match against list values."""
        expr = "0,30 * * * *"
        assert matches(expr, datetime(2026, 4, 15, 12, 0)) is True
        assert matches(expr, datetime(2026, 4, 15, 12, 30)) is True
        assert matches(expr, datetime(2026, 4, 15, 12, 15)) is False

    def test_matches_range(self):
        """Match against range values."""
        expr = "* 9-17 * * *"
        assert matches(expr, datetime(2026, 4, 15, 9, 0)) is True
        assert matches(expr, datetime(2026, 4, 15, 17, 0)) is True
        assert matches(expr, datetime(2026, 4, 15, 8, 0)) is False
        assert matches(expr, datetime(2026, 4, 15, 18, 0)) is False

    def test_matches_step(self):
        """Match against step values."""
        expr = "*/15 * * * *"
        assert matches(expr, datetime(2026, 4, 15, 12, 0)) is True
        assert matches(expr, datetime(2026, 4, 15, 12, 15)) is True
        assert matches(expr, datetime(2026, 4, 15, 12, 30)) is True
        assert matches(expr, datetime(2026, 4, 15, 12, 45)) is True
        assert matches(expr, datetime(2026, 4, 15, 12, 1)) is False

    def test_matches_parsed_expression(self):
        """Match with a pre-parsed CronExpression object."""
        expr = parse("30 12 15 6 1")
        assert matches(expr, datetime(2026, 6, 15, 12, 30)) is True
        assert matches(expr, datetime(2026, 6, 15, 12, 31)) is False


class TestMatchesRealWorld:
    """Test real-world cron expression scenarios."""

    def test_matches_every_hour(self):
        expr = "0 * * * *"
        assert matches(expr, datetime(2026, 4, 15, 12, 0)) is True
        assert matches(expr, datetime(2026, 4, 15, 12, 1)) is False

    def test_matches_daily_noon(self):
        expr = "0 12 * * *"
        assert matches(expr, datetime(2026, 4, 15, 12, 0)) is True
        assert matches(expr, datetime(2026, 4, 15, 13, 0)) is False

    def test_matches_weekdays_9am(self):
        expr = "0 9 * * 1-5"
        assert matches(expr, datetime(2026, 4, 13, 9, 0)) is True
        assert matches(expr, datetime(2026, 4, 18, 9, 0)) is False

    def test_matches_monthly(self):
        expr = "0 0 1 * *"
        assert matches(expr, datetime(2026, 5, 1, 0, 0)) is True
        assert matches(expr, datetime(2026, 5, 2, 0, 0)) is False

    def test_matches_quarterly(self):
        expr = "0 0 1 1,4,7,10 *"
        assert matches(expr, datetime(2026, 1, 1, 0, 0)) is True
        assert matches(expr, datetime(2026, 4, 1, 0, 0)) is True
        assert matches(expr, datetime(2026, 2, 1, 0, 0)) is False

    def test_matches_business_hours(self):
        expr = "0 9-17 * * 1-5"
        assert matches(expr, datetime(2026, 4, 13, 9, 0)) is True
        assert matches(expr, datetime(2026, 4, 13, 17, 0)) is True
        assert matches(expr, datetime(2026, 4, 13, 8, 0)) is False
        assert matches(expr, datetime(2026, 4, 13, 18, 0)) is False


class TestMatchesDayOfWeek:
    def test_matches_dow_sunday_as_0(self):
        expr = "* * * * 0"
        assert matches(expr, datetime(2026, 4, 12, 10, 0)) is True
        assert matches(expr, datetime(2026, 4, 13, 10, 0)) is False

    def test_matches_dow_sunday_as_7(self):
        expr = "* * * * 7"
        assert matches(expr, datetime(2026, 4, 12, 10, 0)) is True
        assert matches(expr, datetime(2026, 4, 13, 10, 0)) is False

    def test_matches_dow_in_list_with_7(self):
        expr = "* * * * 0,3,7"
        assert matches(expr, datetime(2026, 4, 12, 10, 0)) is True
        assert matches(expr, datetime(2026, 4, 15, 10, 0)) is True
        assert matches(expr, datetime(2026, 4, 13, 10, 0)) is False


class TestMatchesErrors:
    def test_matches_aware_datetime_raises(self):
        from datetime import timezone
        dt = datetime(2026, 4, 15, 12, 0, tzinfo=timezone.utc)
        with pytest.raises(CrontabError):
            matches("* * * * *", dt)

    def test_matches_invalid_expression_string(self):
        with pytest.raises(CrontabError):
            matches("invalid", datetime(2026, 4, 15, 12, 0))

    def test_matches_none_datetime(self):
        with pytest.raises(CrontabError):
            matches("* * * * *", None)


class TestMatchesEdgeCases:
    def test_matches_feb_29_leap_year(self):
        expr = "* * 29 2 *"
        assert matches(expr, datetime(2024, 2, 29, 10, 0)) is True

    def test_matches_dom_31_in_month_with_30_days(self):
        expr = "* * 31 * *"
        assert matches(expr, datetime(2026, 4, 30, 10, 0)) is False
        assert matches(expr, datetime(2026, 5, 31, 10, 0)) is True

    def test_matches_combined_ranges_and_lists(self):
        expr = "0 9,12,15,18 1-15 * *"
        assert matches(expr, datetime(2026, 4, 1, 9, 0)) is True
        assert matches(expr, datetime(2026, 4, 15, 18, 0)) is True
        assert matches(expr, datetime(2026, 4, 16, 9, 0)) is False
        assert matches(expr, datetime(2026, 4, 1, 10, 0)) is False
