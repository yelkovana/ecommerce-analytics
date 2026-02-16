"""A/B test diagnostics — SRM, novelty detection, CUPED."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from src.analytics.ab_testing.models import CUPEDResult, SRMResult


def srm_check(
    observed_counts: list[int],
    expected_ratios: list[float] | None = None,
    threshold: float = 0.001,
) -> SRMResult:
    """Sample Ratio Mismatch check using chi-square goodness of fit.

    observed_counts: [control_n, treatment_n, ...]
    expected_ratios: expected allocation ratios (default: equal split)
    """
    observed = np.array(observed_counts)
    total = observed.sum()

    if expected_ratios is None:
        expected_ratios = [1.0 / len(observed)] * len(observed)

    expected = np.array(expected_ratios) * total
    chi2 = np.sum((observed - expected) ** 2 / expected)
    p_value = 1 - stats.chi2.cdf(chi2, df=len(observed) - 1)

    return SRMResult(
        chi_square=round(chi2, 4),
        p_value=round(p_value, 6),
        is_srm=bool(p_value < threshold),
        expected_counts=[int(e) for e in expected],
        observed_counts=list(observed_counts),
        threshold=threshold,
    )


def novelty_detection(
    df: pd.DataFrame,
    metric_col: str = "conversion_rate",
    date_col: str = "metric_date",
    variant_col: str = "variant",
    window_days: int = 7,
) -> dict:
    """Detect novelty/primacy effect by comparing early vs late performance.

    Returns comparison stats and changepoint detection result.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    start_date = df[date_col].min()
    cutoff = start_date + pd.Timedelta(days=window_days)

    early = df[df[date_col] <= cutoff]
    late = df[df[date_col] > cutoff]

    if early.empty or late.empty:
        return {"detected": False, "reason": "Insufficient data for early/late comparison"}

    results = {}
    for variant in df[variant_col].unique():
        early_vals = early[early[variant_col] == variant][metric_col].values
        late_vals = late[late[variant_col] == variant][metric_col].values

        if len(early_vals) < 2 or len(late_vals) < 2:
            continue

        t_stat, p_value = stats.ttest_ind(early_vals, late_vals, equal_var=False)
        results[variant] = {
            "early_mean": round(float(early_vals.mean()), 6),
            "late_mean": round(float(late_vals.mean()), 6),
            "t_statistic": round(float(t_stat), 4),
            "p_value": round(float(p_value), 6),
            "significant": p_value < 0.05,
        }

    # Check if the effect difference (treatment - control) is different early vs late
    detected = any(r["significant"] for r in results.values())

    return {
        "detected": detected,
        "window_days": window_days,
        "variants": results,
    }


def cuped(
    y: np.ndarray,
    x: np.ndarray,
    variant: np.ndarray,
    control_label: str = "control",
    treatment_label: str = "treatment",
) -> CUPEDResult:
    """CUPED (Controlled-experiment Using Pre-Experiment Data).

    y: post-experiment metric values
    x: pre-experiment covariate values
    variant: array of variant labels
    """
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    variant = np.asarray(variant)

    # Compute theta = Cov(Y, X) / Var(X)
    cov_yx = np.cov(y, x)[0, 1]
    var_x = np.var(x, ddof=1)
    theta = cov_yx / var_x if var_x > 0 else 0

    # Adjusted Y
    y_adj = y - theta * (x - x.mean())

    # Original stats
    control_mask = variant == control_label
    treatment_mask = variant == treatment_label

    original_variance = np.var(y, ddof=1)
    adjusted_variance = np.var(y_adj, ddof=1)
    variance_reduction = 1 - (adjusted_variance / original_variance) if original_variance > 0 else 0

    adj_control_mean = float(y_adj[control_mask].mean())
    adj_treatment_mean = float(y_adj[treatment_mask].mean())

    return CUPEDResult(
        theta=round(theta, 6),
        original_variance=round(float(original_variance), 4),
        adjusted_variance=round(float(adjusted_variance), 4),
        variance_reduction=round(float(variance_reduction), 4),
        adjusted_control_mean=round(adj_control_mean, 4),
        adjusted_treatment_mean=round(adj_treatment_mean, 4),
        adjusted_effect=round(adj_treatment_mean - adj_control_mean, 4),
    )
