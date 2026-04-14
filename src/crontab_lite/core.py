"""Core cron parsing and matching functionality."""
from datetime import datetime, timedelta
from typing import Union, Optional

from .errors import CrontabError
from .models import CronExpression


def parse(expression: str) -> CronExpression:
    """Parse a standard 5-field cron expression into a CronExpression object.

    Args:
        expression: A cron expression string with exactly 5 space-separated fields:
                   minute hour day-of-month month day-of-week

    Returns:
        A CronExpression dataclass with parsed field sets.

    Raises:
        CrontabError: If the expression is invalid.
    """
    _validate_expression_type(expression)
    fields = expression.strip().split()
    _validate_field_count(fields)

    try:
        fields_parsed = _parse_all_fields(fields)
    except (ValueError, IndexError) as e:
        raise CrontabError(f"Invalid cron expression: {e}")

    return fields_parsed


def _parse_all_fields(fields: list) -> CronExpression:
    """Parse all 5 cron fields."""
    minute = _parse_field(fields[0], 0, 59)
    hour = _parse_field(fields[1], 0, 23)
    dom = _parse_field(fields[2], 1, 31)
    month = _parse_field(fields[3], 1, 12)
    dow = _parse_field(fields[4], 0, 7)

    # Normalize dow: 7 should map to 0 (Sunday)
    if 7 in dow:
        dow.discard(7)
        dow.add(0)

    return CronExpression(minute=minute, hour=hour, dom=dom, month=month, dow=dow)


def _validate_expression_type(expression: str) -> None:
    """Validate that expression is a string.

    Raises:
        CrontabError: If expression is not a string.
    """
    if not isinstance(expression, str):
        raise CrontabError("Expression must be a string")


def _validate_field_count(fields: list) -> None:
    """Validate that exactly 5 fields are present.

    Raises:
        CrontabError: If field count is not exactly 5.
    """
    if len(fields) != 5:
        raise CrontabError(f"Expression must have exactly 5 fields, got {len(fields)}")


def _parse_field(field: str, min_val: int, max_val: int) -> set:
    """Parse a single cron field into a set of valid values.

    Args:
        field: A cron field string (e.g., "*, 0-30/5, 1,3,5").
        min_val: Minimum valid value for this field.
        max_val: Maximum valid value for this field.

    Returns:
        A set of integers representing valid values.

    Raises:
        ValueError: If the field is invalid.
    """
    if not field or field.isspace():
        raise ValueError("Empty field")

    if field == "*":
        return set(range(min_val, max_val + 1))

    result = set()
    for part in field.split(","):
        values = _parse_field_part(part, min_val, max_val)
        result.update(values)

    return result


def _parse_field_part(part: str, min_val: int, max_val: int) -> set:
    """Parse a single part of a cron field (handles steps, ranges, values).

    Args:
        part: A part string (e.g., "*/15", "1-5", "10").
        min_val: Minimum valid value.
        max_val: Maximum valid value.

    Returns:
        A set of integers representing valid values.

    Raises:
        ValueError: If the part is invalid.
    """
    part = part.strip()
    if not part:
        raise ValueError("Empty list element")

    if "/" not in part:
        return _parse_field_without_step(part, min_val, max_val)

    return _parse_field_with_step(part, min_val, max_val)


def _parse_field_with_step(part: str, min_val: int, max_val: int) -> set:
    """Parse field part with step (e.g., '*/15', '1-5/2')."""
    range_part, step_str = part.rsplit("/", 1)
    try:
        step = int(step_str)
    except ValueError:
        raise ValueError(f"Invalid step value: {step_str}")

    if step <= 0:
        raise ValueError(f"Step must be positive, got {step}")

    if range_part == "*":
        return set(range(min_val, max_val + 1, step))

    if "-" in range_part:
        start, end = _parse_range(range_part, min_val, max_val)
        return set(range(start, end + 1, step))

    try:
        val = int(range_part)
    except ValueError:
        raise ValueError(f"Invalid value: {range_part}")

    return {val} if min_val <= val <= max_val else set()


def _parse_field_without_step(part: str, min_val: int, max_val: int) -> set:
    """Parse a field part without step (handles ranges and values).

    Args:
        part: A part string (e.g., "1-5", "10").
        min_val: Minimum valid value.
        max_val: Maximum valid value.

    Returns:
        A set of integers representing valid values.

    Raises:
        ValueError: If the part is invalid.
    """
    if "-" not in part:
        try:
            val = int(part)
        except ValueError:
            raise ValueError(f"Invalid value: {part}")

        if not (min_val <= val <= max_val):
            raise ValueError(f"Value {val} out of range [{min_val}, {max_val}]")

        return {val}

    start, end = _parse_range(part, min_val, max_val)
    return set(range(start, end + 1))


def _parse_range(range_str: str, min_val: int, max_val: int) -> tuple:
    """Parse a range string like '1-5'.

    Args:
        range_str: A range string (e.g., "1-5").
        min_val: Minimum valid value.
        max_val: Maximum valid value.

    Returns:
        A tuple (start, end).

    Raises:
        ValueError: If the range is invalid.
    """
    parts = range_str.split("-")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"Invalid range: {range_str}")

    try:
        start = int(parts[0])
        end = int(parts[1])
    except ValueError:
        raise ValueError(f"Invalid range: {range_str}")

    _validate_range_bounds(start, end, min_val, max_val)
    return start, end


def _validate_range_bounds(
    start: int, end: int, min_val: int, max_val: int
) -> None:
    """Validate that range bounds are valid.

    Raises:
        ValueError: If bounds are invalid.
    """
    if not (min_val <= start <= max_val and min_val <= end <= max_val):
        raise ValueError(
            f"Range [{start}, {end}] out of bounds [{min_val}, {max_val}]"
        )

    if start > end:
        raise ValueError(f"Invalid range: start {start} > end {end}")


def matches(
    expression: Union[str, CronExpression], dt: datetime
) -> bool:
    """Check if a datetime matches a cron expression.

    Args:
        expression: A cron expression string or CronExpression object.
        dt: A timezone-naive datetime to check.

    Returns:
        True if dt matches the expression, False otherwise.

    Raises:
        CrontabError: If the expression or datetime is invalid.
    """
    if isinstance(expression, str):
        expression = parse(expression)

    _validate_datetime(dt)

    if not _check_time_fields(dt, expression):
        return False

    return _check_day_fields(dt, expression)


def _validate_datetime(dt: datetime) -> None:
    """Validate that dt is a timezone-naive datetime.

    Raises:
        CrontabError: If dt is invalid.
    """
    if not isinstance(dt, datetime):
        raise CrontabError("Datetime must be a datetime object")

    if dt.tzinfo is not None:
        raise CrontabError("Timezone-aware datetimes are not supported")


def _check_time_fields(dt: datetime, expr: CronExpression) -> bool:
    """Check if time fields (minute, hour, month) match.

    Args:
        dt: The datetime to check.
        expr: The parsed cron expression.

    Returns:
        True if all time fields match.
    """
    return (
        dt.minute in expr.minute
        and dt.hour in expr.hour
        and dt.month in expr.month
    )


def _check_day_fields(dt: datetime, expr: CronExpression) -> bool:
    """Check if day fields (dom and dow) match.

    Args:
        dt: The datetime to check.
        expr: The parsed cron expression.

    Returns:
        True if at least one of dom or dow matches.
    """
    dom_match = dt.day in expr.dom
    actual_dow = (dt.weekday() + 1) % 7
    dow_match = actual_dow in expr.dow
    return dom_match and dow_match


def next_fire(
    expression: Union[str, CronExpression], after: Optional[datetime] = None
) -> datetime:
    """Find the next datetime that matches a cron expression.

    Args:
        expression: A cron expression string or CronExpression object.
        after: Starting datetime (default: now). Must be timezone-naive.

    Returns:
        The next datetime matching the expression.

    Raises:
        CrontabError: If the expression is invalid or no match is found within limits.
    """
    if isinstance(expression, str):
        expression = parse(expression)

    if after is None:
        after = datetime.now()

    if after.tzinfo is not None:
        raise CrontabError("Timezone-aware datetimes are not supported")

    return _find_fire(expression, after, direction=1)


def prev_fire(
    expression: Union[str, CronExpression], before: Optional[datetime] = None
) -> datetime:
    """Find the previous datetime that matched a cron expression.

    Args:
        expression: A cron expression string or CronExpression object.
        before: Starting datetime (default: now). Must be timezone-naive.

    Returns:
        The previous datetime matching the expression.

    Raises:
        CrontabError: If the expression is invalid or no match is found within limits.
    """
    if isinstance(expression, str):
        expression = parse(expression)

    if before is None:
        before = datetime.now()

    if before.tzinfo is not None:
        raise CrontabError("Timezone-aware datetimes are not supported")

    return _find_fire(expression, before, direction=-1)


def _find_fire(expr: CronExpression, start: datetime, direction: int) -> datetime:
    """Find the next or previous fire time.

    Args:
        expr: The parsed cron expression.
        start: Starting datetime.
        direction: 1 for next, -1 for previous.

    Returns:
        The matching datetime.

    Raises:
        CrontabError: If no match found within bounds.
    """
    # Start from next/previous minute
    delta = timedelta(minutes=direction)
    current = start.replace(second=0, microsecond=0) + delta

    # Limit search to 4 years
    max_iterations = 4 * 365 * 24 * 60 + 100

    for _ in range(max_iterations):
        if matches(expr, current):
            return current
        current += delta

    raise CrontabError("No matching datetime found within reasonable time bounds")


