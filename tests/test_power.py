"""Tests for power analysis."""

import pytest

from src.analytics.ab_testing.power import (
    sample_size_proportion,
    sample_size_mean,
    adjust_for_cuped,
    estimate_duration,
)


class TestSampleSizeProportion:
    def test_known_values(self):
        # Baseline 5%, MDE 1%, alpha=0.05, power=0.80
        result = sample_size_proportion(0.05, 0.01, 0.05, 0.80)
        # Should be around 7,000-8,000 per variant for these parameters
        assert 6000 < result.required_sample_per_variant < 9000

    def test_smaller_mde_needs_more_samples(self):
        r1 = sample_size_proportion(0.05, 0.01)
        r2 = sample_size_proportion(0.05, 0.005)
        assert r2.required_sample_per_variant > r1.required_sample_per_variant

    def test_higher_power_needs_more_samples(self):
        r1 = sample_size_proportion(0.05, 0.01, power=0.80)
        r2 = sample_size_proportion(0.05, 0.01, power=0.95)
        assert r2.required_sample_per_variant > r1.required_sample_per_variant


class TestSampleSizeMean:
    def test_known_values(self):
        result = sample_size_mean(50, 15, 2.0)
        assert result.required_sample_per_variant > 100

    def test_higher_variance_needs_more(self):
        r1 = sample_size_mean(50, 10, 2.0)
        r2 = sample_size_mean(50, 20, 2.0)
        assert r2.required_sample_per_variant > r1.required_sample_per_variant


class TestCUPEDAdjustment:
    def test_reduces_sample_size(self):
        original = sample_size_proportion(0.05, 0.01)
        adjusted = adjust_for_cuped(original, variance_reduction=0.3)
        assert adjusted.required_sample_per_variant < original.required_sample_per_variant
        assert adjusted.variance_reduction == 0.3

    def test_zero_reduction_no_change(self):
        original = sample_size_proportion(0.05, 0.01)
        adjusted = adjust_for_cuped(original, variance_reduction=0.0)
        assert adjusted.required_sample_per_variant == original.required_sample_per_variant


class TestEstimateDuration:
    def test_basic(self):
        days = estimate_duration(10000, 1000)
        assert days == pytest.approx(10.0)

    def test_with_allocation(self):
        days = estimate_duration(10000, 1000, allocation_ratio=0.5)
        assert days == pytest.approx(20.0)
