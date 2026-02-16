"""Frequentist A/B test analysis — z-test, t-test, chi-square."""

from __future__ import annotations

import numpy as np
from scipy import stats

from src.analytics.ab_testing.models import FrequentistResult


def two_proportion_z_test(
    control_conversions: int,
    control_total: int,
    treatment_conversions: int,
    treatment_total: int,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> FrequentistResult:
    """Two-proportion z-test for conversion metrics."""
    p_c = control_conversions / control_total
    p_t = treatment_conversions / treatment_total
    p_pool = (control_conversions + treatment_conversions) / (control_total + treatment_total)

    se = np.sqrt(p_pool * (1 - p_pool) * (1 / control_total + 1 / treatment_total))
    z = (p_t - p_c) / se if se > 0 else 0

    if alternative == "two-sided":
        p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    elif alternative == "greater":
        p_value = 1 - stats.norm.cdf(z)
    else:
        p_value = stats.norm.cdf(z)

    # Confidence interval for the difference
    se_diff = np.sqrt(p_c * (1 - p_c) / control_total + p_t * (1 - p_t) / treatment_total)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    ci_lower = (p_t - p_c) - z_crit * se_diff
    ci_upper = (p_t - p_c) + z_crit * se_diff

    # Cohen's h (effect size for proportions)
    h = 2 * (np.arcsin(np.sqrt(p_t)) - np.arcsin(np.sqrt(p_c)))

    absolute_effect = p_t - p_c
    relative_effect = absolute_effect / p_c if p_c > 0 else 0

    return FrequentistResult(
        test_name="Two-Proportion Z-Test",
        statistic=round(float(z), 4),
        p_value=round(float(p_value), 6),
        significant=bool(p_value < alpha),
        confidence_level=1 - alpha,
        control_mean=round(p_c, 6),
        treatment_mean=round(p_t, 6),
        absolute_effect=round(absolute_effect, 6),
        relative_effect=round(relative_effect, 4),
        ci_lower=round(float(ci_lower), 6),
        ci_upper=round(float(ci_upper), 6),
        effect_size=round(float(h), 4),
    )


def welch_t_test(
    control_values: np.ndarray,
    treatment_values: np.ndarray,
    alpha: float = 0.05,
    alternative: str = "two-sided",
) -> FrequentistResult:
    """Welch's t-test for revenue/continuous metrics."""
    control_values = np.asarray(control_values, dtype=float)
    treatment_values = np.asarray(treatment_values, dtype=float)

    n_c, n_t = len(control_values), len(treatment_values)
    mean_c, mean_t = control_values.mean(), treatment_values.mean()
    var_c, var_t = control_values.var(ddof=1), treatment_values.var(ddof=1)

    se = np.sqrt(var_c / n_c + var_t / n_t)
    t_stat = (mean_t - mean_c) / se if se > 0 else 0

    # Welch-Satterthwaite degrees of freedom
    num = (var_c / n_c + var_t / n_t) ** 2
    denom = (var_c / n_c) ** 2 / (n_c - 1) + (var_t / n_t) ** 2 / (n_t - 1)
    df = num / denom if denom > 0 else 1

    if alternative == "two-sided":
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    elif alternative == "greater":
        p_value = 1 - stats.t.cdf(t_stat, df)
    else:
        p_value = stats.t.cdf(t_stat, df)

    t_crit = stats.t.ppf(1 - alpha / 2, df)
    ci_lower = (mean_t - mean_c) - t_crit * se
    ci_upper = (mean_t - mean_c) + t_crit * se

    # Cohen's d
    pooled_std = np.sqrt(((n_c - 1) * var_c + (n_t - 1) * var_t) / (n_c + n_t - 2))
    d = (mean_t - mean_c) / pooled_std if pooled_std > 0 else 0

    absolute_effect = mean_t - mean_c
    relative_effect = absolute_effect / mean_c if mean_c != 0 else 0

    return FrequentistResult(
        test_name="Welch's T-Test",
        statistic=round(float(t_stat), 4),
        p_value=round(float(p_value), 6),
        significant=bool(p_value < alpha),
        confidence_level=1 - alpha,
        control_mean=round(float(mean_c), 4),
        treatment_mean=round(float(mean_t), 4),
        absolute_effect=round(float(absolute_effect), 4),
        relative_effect=round(float(relative_effect), 4),
        ci_lower=round(float(ci_lower), 4),
        ci_upper=round(float(ci_upper), 4),
        effect_size=round(float(d), 4),
    )


def chi_square_test(
    observed: list[list[int]],
    alpha: float = 0.05,
) -> FrequentistResult:
    """Chi-square test for categorical outcomes.

    observed: 2D array, rows=variants, cols=categories.
    """
    observed = np.array(observed)
    chi2, p_value, dof, expected = stats.chi2_contingency(observed)

    row_totals = observed.sum(axis=1)
    proportions = observed / row_totals[:, np.newaxis]

    return FrequentistResult(
        test_name="Chi-Square Test",
        statistic=round(float(chi2), 4),
        p_value=round(float(p_value), 6),
        significant=bool(p_value < alpha),
        confidence_level=1 - alpha,
        control_mean=round(float(proportions[0, 0]), 6) if proportions.shape[1] > 0 else 0,
        treatment_mean=round(float(proportions[1, 0]), 6) if proportions.shape[0] > 1 else 0,
        absolute_effect=0,
        relative_effect=0,
        ci_lower=0,
        ci_upper=0,
        effect_size=round(float(np.sqrt(chi2 / observed.sum())), 4),  # Cramér's V (2x2 → phi)
    )


def cohens_d(control_values: np.ndarray, treatment_values: np.ndarray) -> float:
    """Compute Cohen's d effect size."""
    control_values = np.asarray(control_values, dtype=float)
    treatment_values = np.asarray(treatment_values, dtype=float)
    n_c, n_t = len(control_values), len(treatment_values)
    pooled_std = np.sqrt(
        ((n_c - 1) * control_values.var(ddof=1) + (n_t - 1) * treatment_values.var(ddof=1))
        / (n_c + n_t - 2)
    )
    return (treatment_values.mean() - control_values.mean()) / pooled_std if pooled_std > 0 else 0
