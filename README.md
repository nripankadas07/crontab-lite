# crontab-lite

Parse and evaluate standard cron expressions to check datetime matches.

## Installation

```bash
pip install .
```

## Quick Start

```python
from datetime import datetime
from crontab_lite import parse, matches, next_fire, prev_fire

# Parse a cron expression
expr = parse("30 12 * * *")  # Daily at 12:30

# Check if a datetime matches
dt = datetime(2026, 4, 15, 12, 30)
print(matches(expr, dt))  # True

# Find next occurrence
next_dt = next_fire(expr, datetime(2026, 4, 15, 12, 0))
print(next_dt)  # 2026-04-15 12:30:00

# Find previous occurrence
prev_dt = prev_fire(expr, datetime(2026, 4, 15, 13, 0))
print(prev_dt)  # 2026-04-15 12:30:00

# Or use the expression string directly
if matches("0 9 * * 1-5", datetime(2026, 4, 15, 9, 0)):
    print("It's 9 AM on a weekday!")
```

## API Reference

### `parse(expression: str) -> CronExpression`

Parse a standard 5-field cron expression into a structured object.

**Fields:**
- Minute (0-59)
- Hour (0-23)
- Day of Month (1-31)
- Month (1-12)
- Day of Week (0-7, where 0 and 7 are Sunday)

**Syntax:**
- `*` â Match any value
- `5` â Match specific value
- `1-5` â Match range
- `1,3,5` â Match list
- `*/5` â Match with step
- `1-30/5` â Match range with step

**Example:**
```python
expr = parse("0 9 * * 1-5")  # 9 AM on weekdays
```

**Raises:** `CrontabError` for invalid expressions

### `matches(expression: str | CronExpression, dt: datetime) -> bool`

Check if a timezone-naive datetime matches a cron expression.

**Args:**
- `expression`: Cron expression string or parsed `CronExpression`
- `dt`: Timezone-naive `datetime` object

**Returns:** `True` if the datetime matches, `False` otherwise

**Raises:** `CrontabError` for invalid inputs

**Example:**
```python
if matches("30 12 * * *", datetime(2026, 4, 15, 12, 30)):
    print("Noon exactly!")
```

### `next_fire(expression: str | CronExpression, after: datetime | None = None) -> datetime`

Find the next datetime that matches the expression.

**Args:**
- `expression`: Cron expression string or parsed `CronExpression`
- `after`: Starting datetime (default: current time). Must be timezone-naive.

**Returns:** The next matching `datetime`

**Raises:** `CrontabError` if no match found within reasonable bounds

**Example:**
```python
next_noon = next_fire("0 12 * * *", datetime(2026, 4, 15, 11, 0))
# Returns: 2026-04-15 12:00:00
```

### `prev_fire(expression: str | CronExpression, before: datetime | None = None) -> datetime`

Find the previous datetime that matched the expression.

**Args:**
- `expression`: Cron expression string or parsed `CronExpression`
- `before`: Starting datetime (default: current time). Must be timezone-naive.

**Returns:** The previous matching `datetime`

**Raises:** `CrontabError` if no match found within reasonable bounds

**Example:**
```python
prev_noon = prev_fire("0 12 * * *", datetime(2026, 4, 15, 13, 0))
# Returns: 2026-04-15 12:00:00
```

### `CronExpression` (dataclass)

Holds parsed cron fields.

**Attributes:**
- `minute: set` â Valid minute values (0-59)
- `hour: set` â Valid hour values (0-23)
- `dom: set` â Valid day-of-month values (1-31)
- `month: set` â Valid month values (1-12)
- `dow: set` â Valid day-of-week values (0-6)

### `CrontabError` (exception)

Raised for all error conditions (invalid expressions, timezone-aware datetimes, etc.).

## Features

- **5-field cron syntax** (minute hour dom month dow)
- **Special characters:** `*`, ranges (`1-5`), lists (`1,3,5`), steps (`*/15`)
- **Day-of-week normalization:** Both 0 and 7 represent Sunday
- **Timezone-naive only:** Rejects timezone-aware datetimes for safety
- **Reasonable bounds:** `next_fire` and `prev_fire` search up to 4 years
- **Edge case handling:**
  - February 29 (leap years only)
  - Day 31 in months with fewer days
  - Year boundaries
  - Invalid syntax and out-of-range values

## Running Tests

```bash
pytest tests/ -v
```

With coverage report:

```bash
pytest tests/ -v --cov=src/crontab_lite --cov-report=term-missing
```

## License

MIT License â Copyright (c) 2026 Nripanka Das
