"""Tests for cron expression parsing."""
import pytest
from datetime import datetime
from crontab_lite import parse, CrontabError, CronExpression


class TestParseBasicExpressions:
    """Test parsing of valid cron expressions."""

    def test_parse_every_minute(self):
        """Parse '* * * * *' - every minute."""
        expr = parse("* * * * *")
        assert expr.minute == {i for i in range(60)}
        assert expr.hour == {i for i in range(24)}
        assert expr.dom == {i for i in range(1, 32)}
        assert expr.month == {i for i in range(1, 13)}
        assert expr.dow == {i for i in range(7)}

    def test_parse_specific_values(self):
        """Parse '30 12 15 6 2' - specific values."""
        expr = parse("30 12 15 6 2")
        assert expr.minute == {30}
        assert expr.hour == {12}
        assert expr.dom == {15}
        assert expr.month == {6}
        assert expr.dow == {2}

    def test_parse_ranges(self):
        """Parse ranges like '0-30' in fields."""
        expr = parse("0-30 1-5 1-10 1-6 1-5")
        assert expr.minute == set(range(0, 31))
        assert expr.hour == set(range(1, 6))
        assert expr.dom == set(range(1, 11))
        assert expr.month == set(range(1, 7))
        assert expr.dow == set(range(1, 6))

    def test_parse_lists(self):
        """Parse lists like '1,3,5' in fields."""
        expr = parse("1,3,5 2,4,6 1,15,30 1,6,12 0,3,5")
        assert expr.minute == {1, 3, 5}
        assert expr.hour == {2, 4, 6}
        assert expr.dom == {1, 15, 30}
        assert expr.month == {1, 6, 12}
        assert expr.dow == {0, 3, 5}

    def test_parse_steps(self):
        """Parse steps like '*/15' or '0-30/5'."""
        expr = parse("*/15 */6 */10 */3 */2")
        assert expr.minute == {0, 15, 30, 45}
        assert expr.hour == {0, 6, 12, 18}
        assert expr.dom == {1, 11, 21, 31}
        assert expr.month == {1, 4, 7, 10}
        assert expr.dow == {0, 2, 4, 6}

    def test_parse_range_with_step(self):
        """Parse ranges with steps like '1-30/5'."""
        expr = parse("0-30/5 0-20/5 1-20/5 1-12/2 0-6/2")
        assert expr.minute == {0, 5, 10, 15, 20, 25, 30}
        assert expr.hour == {0, 5, 10, 15, 20}
        assert expr.dom == {1, 6, 11, 16}
        assert expr.month == {1, 3, 5, 7, 9, 11}
        assert expr.dow == {0, 2, 4, 6}

    def test_parse_common_expressions(self):
        """Parse common real-world cron expressions."""
        # Every hour at minute 0
        expr = parse("0 * * * *")
        assert 0 in expr.minute
        assert len(expr.hour) == 24

        # At noon and midnight
        expr = parse("0 0,12 * * *")
        assert expr.hour == {0, 12}

        # Weekdays
        expr = parse("0 9 * * 1-5")
        assert expr.dow == {1, 2, 3, 4, 5}


class TestParseErrors:
    """Test error handling for invalid inputs."""

    def test_parse_empty_string(self):
        """Reject empty string."""
        with pytest.raises(CrontabError):
            parse("")

    def test_parse_none(self):
        """Reject None input."""
        with pytest.raises(CrontabError):
            parse(None)

    def test_parse_not_string(self):
        """Reject non-string input."""
        with pytest.raises(CrontabError):
            parse(123)

    def test_parse_wrong_field_count(self):
        """Reject expressions with wrong number of fields."""
        with pytest.raises(CrontabError):
            parse("* * * *")  # 4 fields

        with pytest.raises(CrontabError):
            parse("* * * * * *")  # 6 fields

    def test_parse_out_of_range_minute(self):
        """Reject minute values outside 0-59."""
        with pytest.raises(CrontabError):
            parse("60 * * * *")

        with pytest.raises(CrontabError):
            parse("-1 * * * *")

    def test_parse_out_of_range_hour(self):
        """Reject hour values outside 0-23."""
        with pytest.raises(CrontabError):
            parse("* 24 * * *")

        with pytest.raises(CrontabError):
            parse("* -1 * * *")

    def test_parse_out_of_range_dom(self):
        """Reject day-of-month values outside 1-31."""
        with pytest.raises(CrontabError):
            parse("* * 32 * *")

        with pytest.raises(CrontabError):
            parse("* * 0 * *")

    def test_parse_out_of_range_month(self):
        """Reject month values outside 1-12."""
        with pytest.raises(CrontabError):
            parse("* * * 13 *")

        with pytest.raises(CrontabError):
            parse("* * * 0 *")

    def test_parse_out_of_range_dow(self):
        """Reject day-of-week values outside 0-6 (except 7 for Sunday)."""
        with pytest.raises(CrontabError):
            parse("* * * * 8")

        with pytest.raises(CrontabError):
            parse("* * * * -1")

    def test_parse_invalid_range(self):
        """Reject ranges where start > end."""
        with pytest.raises(CrontabError):
            parse("30-10 * * * *")

        with pytest.raises(CrontabError):
            parse("* 20-5 * * *")

    def test_parse_invalid_step(self):
        """Reject step of 0 or negative."""
        with pytest.raises(CrontabError):
            parse("*/0 * * * *")

        with pytest.raises(CrontabError):
            parse("*/-5 * * * *")

    def test_parse_double_commas(self):
        """Reject malformed lists with double commas."""
        with pytest.raises(CrontabError):
            parse("1,,5 * * * *")

    def test_parse_invalid_syntax(self):
        """Reject other syntax errors."""
        with pytest.raises(CrontabError):
            parse("abc * * * *")

        with pytest.raises(CrontabError):
            parse("* * * * xyz")

        with pytest.raises(CrontabError):
            parse("1-2-3 * * * *")


class TestParseEdgeCases:
    """Test edge cases in parsing."""

    def test_parse_dow_7_is_sunday(self):
        """Day-of-week 7 should map to Sunday (0)."""
        expr = parse("* * * * 7")
        assert 0 in expr.dow
        assert 7 not in expr.dow

    def test_parse_dow_0_is_sunday(self):
        """Day-of-week 0 should map to Sunday."""
        expr = parse("* * * * 0")
        assert 0 in expr.dow

    def test_parse_dow_list_with_7(self):
        """Day-of-week list can include 7 for Sunday."""
        expr = parse("* * * * 0,3,7")
        assert expr.dow == {0, 3}

    def test_parse_whitespace(self):
        """Handle extra whitespace in expression."""
        expr = parse("  *   *   *   *   *  ")
        assert len(expr.minute) == 60


class TestParseDataclass:
    """Test CronExpression dataclass."""

    def test_cron_expression_is_dataclass(self):
        """CronExpression should be a dataclass."""
        expr = parse("30 12 15 6 2")
        assert hasattr(expr, 'minute')
        assert hasattr(expr, 'hour')
        assert hasattr(expr, 'dom')
        assert hasattr(expr, 'month')
        assert hasattr(expr, 'dow')

    def test_cron_expression_repr(self):
        """CronExpression should have a useful repr."""
        expr = parse("30 12 * * *")
        repr_str = repr(expr)
        assert "CronExpression" in repr_str or "minute" in repr_str
