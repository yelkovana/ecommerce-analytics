"""Sample size and power calculations."""

from __future__ import annotations

import numpy as np
from scipy import stats

from src.analytics.ab_testing.models import PowerResult


def sample_size_proportion(
    baseline_rate: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
    alternative: str = "two-sided",
) -> PowerResult:
    """Required sample size per variant for a proportion test."""
    p1 = baseline_rate
    p2 = baseline_rate + mde

    if alternative == "two-sided":
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)

    n = ((z_alpha * np.sqrt(2 * p1 * (1 - p1)) + z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))
         / (p2 - p1)) ** 2

    n = int(np.ceil(n))

    return PowerResult(
        required_sample_size=n * 2,
        required_sample_per_variant=n,
        power=power,
        alpha=alpha,
        mde=mde,
        baseline_rate=baseline_rate,
    )


def sample_size_mean(
    baseline_mean: float,
    baseline_std: float,
    mde_absolute: float,
    alpha: float = 0.05,
    power: float = 0.80,
    alternative: str = "two-sided",
) -> PowerResult:
    """Required sample size per variant for a mean test."""
    if alternative == "two-sided":
        z_alpha = stats.norm.ppf(1 - alpha / 2)
    else:
        z_alpha = stats.norm.ppf(1 - alpha)
    z_beta = stats.norm.ppf(power)

    n = int(np.ceil(2 * ((z_alpha + z_beta) * baseline_std / mde_absolute) ** 2))

    return PowerResult(
        required_sample_size=n * 2,
        required_sample_per_variant=n,
        power=power,
        alpha=alpha,
        mde=mde_absolute,
        baseline_rate=baseline_mean,
    )


def adjust_for_cuped(
    original_result: PowerResult,
    variance_reduction: float,
) -> PowerResult:
    """Adjust sample size using CUPED variance reduction."""
    factor = 1 - variance_reduction
    adjusted_per_variant = int(np.ceil(original_result.required_sample_per_variant * factor))

    return PowerResult(
        required_sample_size=adjusted_per_variant * 2,
        required_sample_per_variant=adjusted_per_variant,
        power=original_result.power,
        alpha=original_result.alpha,
        mde=original_result.mde,
        baseline_rate=original_result.baseline_rate,
        cuped_adjusted_size=adjusted_per_variant * 2,
        variance_reduction=variance_reduction,
    )


def estimate_duration(
    sample_size: int,
    daily_traffic: int,
    allocation_ratio: float = 1.0,
) -> float:
    """Estimate experiment duration in days."""
    effective_daily = daily_traffic * min(allocation_ratio, 1.0)
    return sample_size / effective_daily if effective_daily > 0 else float('inf')
