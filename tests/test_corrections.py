"""Tests for multiple comparison corrections."""

import pytest

from src.analytics.ab_testing.corrections import (
    bonferroni,
    holm_bonferroni,
    benjamini_hochberg,
    apply_correction,
)


class TestBonferroni:
    def test_basic(self):
        p_values = [0.01, 0.04, 0.03]
        results = bonferroni(p_values, alpha=0.05)
        # 0.01 * 3 = 0.03 → significant
        assert results[0]["significant"] is True
        assert results[0]["corrected_p"] == pytest.approx(0.03)
        # 0.04 * 3 = 0.12 → not significant
        assert results[1]["significant"] is False

    def test_cap_at_one(self):
        results = bonferroni([0.5, 0.6])
        assert all(r["corrected_p"] <= 1.0 for r in results)


class TestHolmBonferroni:
    def test_step_down(self):
        p_values = [0.01, 0.04, 0.03]
        results = holm_bonferroni(p_values, alpha=0.05)
        # Sorted: 0.01, 0.03, 0.04
        # 0.01 * 3 = 0.03 → significant
        assert results[0]["significant"] is True

    def test_less_conservative_than_bonferroni(self):
        p_values = [0.01, 0.02, 0.03, 0.04]
        bonf = bonferroni(p_values)
        holm = holm_bonferroni(p_values)
        # Holm should find at least as many significant results
        bonf_sig = sum(1 for r in bonf if r["significant"])
        holm_sig = sum(1 for r in holm if r["significant"])
        assert holm_sig >= bonf_sig


class TestBenjaminiHochberg:
    def test_fdr_control(self):
        p_values = [0.01, 0.02, 0.03, 0.04, 0.50]
        results = benjamini_hochberg(p_values, alpha=0.05)
        # First few should be significant
        assert results[0]["significant"] is True
        # 0.50 should not
        assert results[4]["significant"] is False

    def test_less_conservative_than_bonferroni(self):
        p_values = [0.01, 0.02, 0.03, 0.04]
        bonf = bonferroni(p_values)
        bh = benjamini_hochberg(p_values)
        bonf_sig = sum(1 for r in bonf if r["significant"])
        bh_sig = sum(1 for r in bh if r["significant"])
        assert bh_sig >= bonf_sig

    def test_monotonicity(self):
        p_values = [0.005, 0.01, 0.02, 0.04, 0.1]
        results = benjamini_hochberg(p_values)
        sorted_corrected = sorted(r["corrected_p"] for r in results)
        for i in range(len(sorted_corrected) - 1):
            assert sorted_corrected[i] <= sorted_corrected[i + 1]


class TestApplyCorrection:
    def test_valid_methods(self):
        p_values = [0.01, 0.04]
        for method in ["bonferroni", "holm", "holm-bonferroni", "benjamini-hochberg", "bh", "fdr"]:
            results = apply_correction(p_values, method=method)
            assert len(results) == 2

    def test_invalid_method(self):
        with pytest.raises(ValueError):
            apply_correction([0.01], method="invalid")
