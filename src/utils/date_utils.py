"""Date range helper utilities."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional


def get_date_range(days: int = 30, end_date: Optional[date] = None) -> tuple[date, date]:
    """Return (start_date, end_date) going back N days from end_date."""
    if end_date is None:
        end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def previous_period(start_date: date, end_date: date) -> tuple[date, date]:
    """Return the equivalent previous period for comparison."""
    period_length = (end_date - start_date).days
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_length)
    return prev_start, prev_end


def format_date_range(start_date: date, end_date: date) -> str:
    """Format date range for display."""
    return f"{start_date.strftime('%b %d, %Y')} — {end_date.strftime('%b %d, %Y')}"


def date_to_str(d: date) -> str:
    """Convert date to YYYY-MM-DD string for SQL queries."""
    return d.strftime("%Y-%m-%d")


def week_boundaries(d: date) -> tuple[date, date]:
    """Return Monday and Sunday of the week containing d."""
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def month_boundaries(d: date) -> tuple[date, date]:
    """Return first and last day of the month containing d."""
    first = d.replace(day=1)
    if d.month == 12:
        last = d.replace(year=d.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        last = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
    return first, last
