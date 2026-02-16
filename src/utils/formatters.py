"""Number, currency, percentage, and duration formatting utilities."""

from __future__ import annotations


def format_number(value: float, decimals: int = 0) -> str:
    """Format a number with thousands separators."""
    return f"{value:,.{decimals}f}"


def format_currency(value: float, decimals: int = 2, symbol: str = "$") -> str:
    """Format a currency value."""
    return f"{symbol}{value:,.{decimals}f}"


def format_percent(value: float, decimals: int = 1) -> str:
    """Format a value as percentage (0.05 → '5.0%')."""
    return f"{value * 100:,.{decimals}f}%"


def format_duration(seconds: float) -> str:
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes < 60:
        return f"{minutes}m {secs}s"
    hours = int(minutes // 60)
    mins = minutes % 60
    return f"{hours}h {mins}m"


def format_delta(value: float, decimals: int = 1) -> str:
    """Format a delta value with +/- prefix as percentage."""
    sign = "+" if value >= 0 else ""
    return f"{sign}{value * 100:.{decimals}f}%"


def format_metric(value: float, fmt: str, decimals: int = 2) -> str:
    """Format a metric value based on its format type."""
    formatters = {
        "number": lambda v: format_number(v, decimals),
        "currency": lambda v: format_currency(v, decimals),
        "percent": lambda v: format_percent(v, decimals),
        "duration": lambda v: format_duration(v),
    }
    formatter = formatters.get(fmt, formatters["number"])
    return formatter(value)
