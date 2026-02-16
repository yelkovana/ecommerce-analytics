"""Input validation utilities."""

from __future__ import annotations

from datetime import date


def validate_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise ValueError(f"start_date ({start_date}) must be before end_date ({end_date})")
    if (end_date - start_date).days > 365:
        raise ValueError("Date range cannot exceed 365 days")


def validate_positive(value: float, name: str = "value") -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")


def validate_probability(value: float, name: str = "value") -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1, got {value}")


def validate_sample_size(n: int, min_size: int = 1) -> None:
    if n < min_size:
        raise ValueError(f"Sample size must be at least {min_size}, got {n}")
