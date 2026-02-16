"""Sequential testing — alpha spending functions and interim analysis."""

from __future__ import annotations

import numpy as np
from scipy import stats

from src.analytics.ab_testing.models import SequentialResult


def obrien_fleming_boundary(alpha: float, n_looks: int, current_look: int) -> float:
    """O'Brien-Fleming alpha spending boundary at a given look."""
    info_fraction = current_look / n_looks
    if info_fraction <= 0:
        return float('inf')
    z_alpha2 = stats.norm.ppf(1 - alpha / 2)
    return z_alpha2 / np.sqrt(info_fraction)


def pocock_boundary(alpha: float, n_looks: int, current_look: int) -> float:
    """Pocock (constant) alpha spending boundary — approximate."""
    # Pocock boundaries are constant; use Bonferroni-like approximation
    adjusted_alpha = alpha / n_looks
    return stats.norm.ppf(1 - adjusted_alpha / 2)


def alpha_spending_obrien_fleming(alpha: float, info_fraction: float) -> float:
    """O'Brien-Fleming alpha spending function: alpha*(t) = 2 - 2*Phi(z_alpha/2 / sqrt(t))."""
    if info_fraction <= 0:
        return 0
    z = stats.norm.ppf(1 - alpha / 2)
    return 2 * (1 - stats.norm.cdf(z / np.sqrt(info_fraction)))


def alpha_spending_pocock(alpha: float, info_fraction: float) -> float:
    """Pocock alpha spending function: alpha*(t) = alpha * log(1 + (e-1)*t)."""
    if info_fraction <= 0:
        return 0
    return alpha * np.log(1 + (np.e - 1) * info_fraction)


def interim_analysis(
    z_stat: float,
    current_look: int,
    max_looks: int,
    alpha: float = 0.05,
    spending_function: str = "obrien-fleming",
) -> SequentialResult:
    """Perform interim analysis check against spending function boundaries."""
    if spending_function == "obrien-fleming":
        boundary_fn = obrien_fleming_boundary
        spending_fn = alpha_spending_obrien_fleming
    else:
        boundary_fn = pocock_boundary
        spending_fn = alpha_spending_pocock

    # Compute boundaries for all looks
    boundaries = []
    for look in range(1, max_looks + 1):
        boundaries.append(round(boundary_fn(alpha, max_looks, look), 4))

    current_boundary = boundaries[current_look - 1]
    info_fraction = current_look / max_looks
    cumulative_alpha = spending_fn(alpha, info_fraction)

    if abs(z_stat) >= current_boundary:
        decision = "stop_reject"
    elif current_look == max_looks:
        # Final look: use standard alpha
        decision = "stop_reject" if abs(z_stat) >= stats.norm.ppf(1 - alpha / 2) else "stop_accept"
    else:
        decision = "continue"

    return SequentialResult(
        current_look=current_look,
        max_looks=max_looks,
        spending_function=spending_function,
        alpha_spent=round(cumulative_alpha, 6),
        boundary_value=round(current_boundary, 4),
        z_statistic=round(z_stat, 4),
        decision=decision,
        cumulative_alpha=round(cumulative_alpha, 6),
        boundaries=boundaries,
    )
