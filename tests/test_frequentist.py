"""Tests for frequentist A/B test methods."""

import numpy as np
import pytest

from src.analytics.ab_testing.frequentist import (
    two_proportion_z_test,
    welch_t_test,
    chi_square_test,
    cohens_d,
)


class TestTwoProportionZTest:
    def test_significant_result(self):
        result = two_proportion_z_test(
            control_conversions=500, control_total=10000,
            treatment_conversions=600, treatment_total=10000,
        )
        assert result.significant is True
        assert result.p_value < 0.05
        assert result.absolute_effect == pytest.approx(0.01, abs=0.001)
        assert result.ci_lower < result.absolute_effect < result.ci_upper

    def test_not_significant(self):
        result = two_proportion_z_test(
            control_conversions=500, control_total=10000,
            treatment_conversions=510, treatment_total=10000,
        )
        assert result.significant is False

    def test_known_values(self):
        # p_c = 0.10, p_t = 0.12
        result = two_proportion_z_test(
            control_conversions=1000, control_total=10000,
            treatment_conversions=1200, treatment_total=10000,
        )
        assert result.control_mean == pytest.approx(0.10, abs=0.001)
        assert result.treatment_mean == pytest.approx(0.12, abs=0.001)
        assert result.relative_effect == pytest.approx(0.20, abs=0.01)

    def test_effect_size_returned(self):
        result = two_proportion_z_test(
            control_conversions=500, control_total=10000,
            treatment_conversions=600, treatment_total=10000,
        )
        assert result.effect_size is not None
        assert abs(result.effect_size) > 0


class TestWelchTTest:
    def test_significant_difference(self, ab_revenue_data):
        result = welch_t_test(
            ab_revenue_data["control_values"],
            ab_revenue_data["treatment_values"],
        )
        assert result.treatment_mean > result.control_mean
        assert result.effect_size is not None

    def test_equal_groups(self):
        np.random.seed(42)
        values = np.random.normal(50, 10, 5000)
        result = welch_t_test(values, values)
        assert result.p_value > 0.05
        assert abs(result.absolute_effect) < 0.1

    def test_known_effect(self):
        np.random.seed(42)
        control = np.random.normal(100, 10, 10000)
        treatment = np.random.normal(105, 10, 10000)
        result = welch_t_test(control, treatment)
        assert result.significant is True
        assert result.absolute_effect == pytest.approx(5, abs=1)


class TestChiSquare:
    def test_significant(self):
        observed = [[900, 100], [850, 150]]
        result = chi_square_test(observed)
        assert result.significant is True

    def test_not_significant(self):
        observed = [[900, 100], [895, 105]]
        result = chi_square_test(observed)
        assert result.significant is False


class TestCohensD:
    def test_no_effect(self):
        np.random.seed(42)
        values = np.random.normal(50, 10, 1000)
        d = cohens_d(values, values)
        assert abs(d) < 0.01

    def test_medium_effect(self):
        np.random.seed(42)
        control = np.random.normal(50, 10, 5000)
        treatment = np.random.normal(55, 10, 5000)
        d = cohens_d(control, treatment)
        assert d == pytest.approx(0.5, abs=0.1)
