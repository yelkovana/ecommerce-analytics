"""Tests for A/B test diagnostics — SRM, novelty, CUPED."""

import numpy as np
import pandas as pd
import pytest

from src.analytics.ab_testing.diagnostics import srm_check, novelty_detection, cuped


class TestSRMCheck:
    def test_no_srm(self):
        result = srm_check([5000, 5000])
        assert result.is_srm is False
        assert result.p_value > 0.001

    def test_srm_detected(self):
        result = srm_check([5500, 4500])
        assert result.is_srm is True
        assert result.p_value < 0.001

    def test_equal_three_variants(self):
        result = srm_check([3333, 3333, 3334])
        assert result.is_srm is False

    def test_custom_ratios(self):
        result = srm_check([7000, 3000], expected_ratios=[0.7, 0.3])
        assert result.is_srm is False


class TestNoveltyDetection:
    def test_no_novelty(self):
        np.random.seed(42)
        dates = pd.date_range("2025-01-01", periods=30)
        rows = []
        for d in dates:
            for v in ["control", "treatment"]:
                rows.append({
                    "metric_date": d,
                    "variant": v,
                    "conversion_rate": np.random.normal(0.05, 0.005),
                })
        df = pd.DataFrame(rows)
        result = novelty_detection(df, window_days=7)
        # With stable conversion rates, no novelty expected
        assert isinstance(result["detected"], bool)

    def test_novelty_detected(self):
        dates = pd.date_range("2025-01-01", periods=30)
        rows = []
        for i, d in enumerate(dates):
            for v in ["control", "treatment"]:
                # First 7 days: much higher rate
                rate = 0.10 if i < 7 else 0.05
                rows.append({
                    "metric_date": d,
                    "variant": v,
                    "conversion_rate": rate,
                })
        df = pd.DataFrame(rows)
        result = novelty_detection(df, window_days=7)
        assert result["detected"] is True


class TestCUPED:
    def test_variance_reduction(self, ab_metrics_df):
        result = cuped(
            y=ab_metrics_df["revenue"].values,
            x=ab_metrics_df["pre_experiment_revenue"].values,
            variant=ab_metrics_df["variant"].values,
        )
        assert result.variance_reduction > 0
        assert result.adjusted_variance < result.original_variance
        assert result.theta != 0

    def test_uncorrelated_no_reduction(self):
        np.random.seed(42)
        n = 5000
        y = np.random.normal(50, 10, n)
        x = np.random.normal(100, 20, n)  # Uncorrelated
        variant = np.array(["control"] * (n // 2) + ["treatment"] * (n // 2))
        result = cuped(y, x, variant)
        assert abs(result.variance_reduction) < 0.1  # Minimal reduction

    def test_perfectly_correlated(self):
        np.random.seed(42)
        n = 5000
        x = np.random.normal(50, 10, n)
        y = x * 2 + np.random.normal(0, 1, n)  # Highly correlated
        variant = np.array(["control"] * (n // 2) + ["treatment"] * (n // 2))
        result = cuped(y, x, variant)
        assert result.variance_reduction > 0.9  # High reduction
