"""Multiple comparison correction methods."""

from __future__ import annotations

import numpy as np


def bonferroni(p_values: list[float], alpha: float = 0.05) -> list[dict]:
    """Bonferroni correction — most conservative."""
    n = len(p_values)
    results = []
    for i, p in enumerate(p_values):
        corrected = min(p * n, 1.0)
        results.append({
            "original_p": round(p, 6),
            "corrected_p": round(float(corrected), 6),
            "significant": bool(corrected < alpha),
        })
    return results


def holm_bonferroni(p_values: list[float], alpha: float = 0.05) -> list[dict]:
    """Holm-Bonferroni step-down procedure."""
    n = len(p_values)
    indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[indices]

    corrected = np.zeros(n)
    for i, p in enumerate(sorted_p):
        corrected[i] = p * (n - i)

    # Enforce monotonicity (corrected values should be non-decreasing)
    for i in range(1, n):
        corrected[i] = max(corrected[i], corrected[i - 1])

    corrected = np.minimum(corrected, 1.0)

    # Map back to original order
    results = [None] * n
    for rank, orig_idx in enumerate(indices):
        results[orig_idx] = {
            "original_p": round(p_values[orig_idx], 6),
            "corrected_p": round(float(corrected[rank]), 6),
            "significant": bool(corrected[rank] < alpha),
        }
    return results


def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> list[dict]:
    """Benjamini-Hochberg FDR correction."""
    n = len(p_values)
    indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[indices]

    corrected = np.zeros(n)
    for i in range(n):
        corrected[i] = sorted_p[i] * n / (i + 1)

    # Enforce monotonicity (step down from the largest)
    for i in range(n - 2, -1, -1):
        corrected[i] = min(corrected[i], corrected[i + 1])

    corrected = np.minimum(corrected, 1.0)

    results = [None] * n
    for rank, orig_idx in enumerate(indices):
        results[orig_idx] = {
            "original_p": round(p_values[orig_idx], 6),
            "corrected_p": round(float(corrected[rank]), 6),
            "significant": bool(corrected[rank] < alpha),
        }
    return results


def apply_correction(
    p_values: list[float],
    method: str = "benjamini-hochberg",
    alpha: float = 0.05,
) -> list[dict]:
    """Apply the specified correction method."""
    methods = {
        "bonferroni": bonferroni,
        "holm-bonferroni": holm_bonferroni,
        "holm": holm_bonferroni,
        "benjamini-hochberg": benjamini_hochberg,
        "bh": benjamini_hochberg,
        "fdr": benjamini_hochberg,
    }
    fn = methods.get(method.lower())
    if fn is None:
        raise ValueError(f"Unknown correction method: {method}. Available: {list(methods.keys())}")
    return fn(p_values, alpha)
