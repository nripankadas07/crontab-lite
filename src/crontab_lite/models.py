"""Data models for crontab-lite."""
from dataclasses import dataclass


@dataclass(frozen=True)
class CronExpression:
    """Parsed cron expression with five fields.

    Attributes:
        minute: Set of valid minute values (0-59).
        hour: Set of valid hour values (0-23).
        dom: Set of valid day-of-month values (1-31).
        month: Set of valid month values (1-12).
        dow: Set of valid day-of-week values (0-6, where 0 is Sunday).
    """

    minute: set
    hour: set
    dom: set
    month: set
    dow: set
