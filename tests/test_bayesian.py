"""Tests for Bayesian A/B test methods."""

import numpy as np
import pytest

from src.analytics.ab_testing.bayesian import beta_binomial, normal_normal


class TestBetaBinomial:
    def test_treatment_better(self):
        result = beta_binomial(
            control_conversions=500, control_total=10000,
            treatment_conversions=600, treatment_total=10000,
        )
        assert result.prob_treatment_better > 0.95
        assert result.expected_lift > 0
        assert result.expected_loss_treatment < result.expected_loss_control

    def test_equal_groups(self):
        result = beta_binomial(
            control_conversions=500, control_total=10000,
            treatment_conversions=500, treatment_total=10000,
        )
        assert 0.4 < result.prob_treatment_better < 0.6
        assert abs(result.expected_lift) < 0.05

    def test_hdi_contains_zero_for_equal(self):
        result = beta_binomial(
            control_conversions=500, control_total=10000,
            treatment_conversions=505, treatment_total=10000,
        )
        assert result.hdi_lower < 0 < result.hdi_upper

    def test_rope_decision_undecided(self):
        result = beta_binomial(
            control_conversions=500, control_total=10000,
            treatment_conversions=510, treatment_total=10000,
        )
        assert result.rope_decision in ("accept", "undecided")

    def test_rope_decision_reject(self):
        result = beta_binomial(
            control_conversions=500, control_total=10000,
            treatment_conversions=700, treatment_total=10000,
            rope_lower=-0.005, rope_upper=0.005,
        )
        assert result.rope_decision == "reject"

    def test_posterior_samples_populated(self):
        result = beta_binomial(
            control_conversions=100, control_total=1000,
            treatment_conversions=120, treatment_total=1000,
            n_samples=1000,
        )
        assert result.posterior_samples is not None
        assert len(result.posterior_samples) == 1000


class TestNormalNormal:
    def test_analytic_treatment_better(self):
        np.random.seed(42)
        control = np.random.normal(50, 15, 5000)
        treatment = np.random.normal(55, 15, 5000)
        result = normal_normal(control, treatment)
        assert result.prob_treatment_better > 0.9
        assert result.expected_lift > 0

    def test_analytic_equal_groups(self):
        np.random.seed(42)
        values = np.random.normal(50, 10, 5000)
        result = normal_normal(values, values.copy())
        assert 0.3 < result.prob_treatment_better < 0.7

    def test_hdi_range(self):
        np.random.seed(42)
        control = np.random.normal(50, 10, 5000)
        treatment = np.random.normal(52, 10, 5000)
        result = normal_normal(control, treatment, credible_interval=0.95)
        assert result.hdi_lower < result.hdi_upper
