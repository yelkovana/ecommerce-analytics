"""Tests for sequential testing."""

import pytest
from scipy import stats

from src.analytics.ab_testing.sequential import (
    obrien_fleming_boundary,
    pocock_boundary,
    interim_analysis,
)


class TestOBrienFleming:
    def test_boundaries_decrease(self):
        """OF boundaries should decrease as looks increase."""
        boundaries = [obrien_fleming_boundary(0.05, 5, i) for i in range(1, 6)]
        for i in range(len(boundaries) - 1):
            assert boundaries[i] > boundaries[i + 1]

    def test_first_boundary_very_high(self):
        boundary = obrien_fleming_boundary(0.05, 5, 1)
        assert boundary > 3.0

    def test_last_boundary_near_standard(self):
        boundary = obrien_fleming_boundary(0.05, 5, 5)
        z_standard = stats.norm.ppf(0.975)
        # Last boundary should be close to but slightly below standard z
        assert abs(boundary - z_standard) < 0.5


class TestPocock:
    def test_constant_boundaries(self):
        """Pocock boundaries should be approximately constant."""
        boundaries = [pocock_boundary(0.05, 5, i) for i in range(1, 6)]
        assert all(abs(b - boundaries[0]) < 0.01 for b in boundaries)


class TestInterimAnalysis:
    def test_continue_decision(self):
        result = interim_analysis(z_stat=1.5, current_look=1, max_looks=5)
        assert result.decision == "continue"

    def test_stop_decision_large_z(self):
        result = interim_analysis(z_stat=5.0, current_look=1, max_looks=5)
        assert result.decision == "stop_reject"

    def test_final_look_accept(self):
        result = interim_analysis(z_stat=0.5, current_look=5, max_looks=5)
        assert result.decision == "stop_accept"

    def test_boundaries_list(self):
        result = interim_analysis(z_stat=2.0, current_look=3, max_looks=5)
        assert len(result.boundaries) == 5

    def test_pocock_spending(self):
        result = interim_analysis(z_stat=2.0, current_look=2, max_looks=5,
                                   spending_function="pocock")
        assert result.spending_function == "pocock"
