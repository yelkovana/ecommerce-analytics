"""Data classes for A/B test results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class FrequentistResult:
    test_name: str
    statistic: float
    p_value: float
    significant: bool
    confidence_level: float
    control_mean: float
    treatment_mean: float
    absolute_effect: float
    relative_effect: float
    ci_lower: float
    ci_upper: float
    effect_size: Optional[float] = None  # Cohen's d


@dataclass
class BayesianResult:
    prob_treatment_better: float
    expected_lift: float
    hdi_lower: float
    hdi_upper: float
    expected_loss_control: float
    expected_loss_treatment: float
    risk_ratio: float
    rope_decision: Optional[str] = None  # "accept", "reject", "undecided"
    rope_prob_in: Optional[float] = None
    rope_prob_below: Optional[float] = None
    rope_prob_above: Optional[float] = None
    posterior_samples: Optional[list] = None


@dataclass
class SequentialResult:
    current_look: int
    max_looks: int
    spending_function: str
    alpha_spent: float
    boundary_value: float
    z_statistic: float
    decision: str  # "stop_reject", "stop_accept", "continue"
    cumulative_alpha: float
    boundaries: list[float] = field(default_factory=list)


@dataclass
class PowerResult:
    required_sample_size: int
    required_sample_per_variant: int
    estimated_days: Optional[float] = None
    power: float = 0.8
    alpha: float = 0.05
    mde: float = 0.0
    baseline_rate: float = 0.0
    cuped_adjusted_size: Optional[int] = None
    variance_reduction: Optional[float] = None


@dataclass
class SRMResult:
    chi_square: float
    p_value: float
    is_srm: bool
    expected_counts: list[int]
    observed_counts: list[int]
    threshold: float = 0.001


@dataclass
class CUPEDResult:
    theta: float
    original_variance: float
    adjusted_variance: float
    variance_reduction: float
    adjusted_control_mean: float
    adjusted_treatment_mean: float
    adjusted_effect: float


@dataclass
class SegmentResult:
    segment_name: str
    segment_value: str
    result: FrequentistResult
    corrected_p_value: float
    significant_after_correction: bool
