"""Bayesian A/B test analysis — Beta-Binomial (analytic) + Normal-Normal."""

from __future__ import annotations

from typing import Optional

import numpy as np
from scipy import stats as sp_stats

from src.analytics.ab_testing.models import BayesianResult


def beta_binomial(
    control_conversions: int,
    control_total: int,
    treatment_conversions: int,
    treatment_total: int,
    prior_alpha: float = 1.0,
    prior_beta: float = 1.0,
    n_samples: int = 100_000,
    credible_interval: float = 0.95,
    rope_lower: float = -0.005,
    rope_upper: float = 0.005,
) -> BayesianResult:
    """Analytic Beta-Binomial model for conversion rates. No MCMC needed."""
    # Posterior parameters
    alpha_c = prior_alpha + control_conversions
    beta_c = prior_beta + (control_total - control_conversions)
    alpha_t = prior_alpha + treatment_conversions
    beta_t = prior_beta + (treatment_total - treatment_conversions)

    # Monte Carlo sampling from posteriors (fast — no MCMC)
    rng = np.random.default_rng(42)
    samples_c = rng.beta(alpha_c, beta_c, n_samples)
    samples_t = rng.beta(alpha_t, beta_t, n_samples)

    lift_samples = (samples_t - samples_c) / samples_c

    # P(treatment > control)
    prob_better = float(np.mean(samples_t > samples_c))

    # Expected lift
    expected_lift = float(np.mean(lift_samples))

    # HDI
    tail = (1 - credible_interval) / 2
    hdi_lower = float(np.percentile(lift_samples, tail * 100))
    hdi_upper = float(np.percentile(lift_samples, (1 - tail) * 100))

    # Expected loss
    loss_if_choose_treatment = np.mean(np.maximum(samples_c - samples_t, 0))
    loss_if_choose_control = np.mean(np.maximum(samples_t - samples_c, 0))

    # Risk ratio
    risk_ratio = loss_if_choose_treatment / loss_if_choose_control if loss_if_choose_control > 0 else float('inf')

    # ROPE analysis
    diff_samples = samples_t - samples_c
    prob_in_rope = float(np.mean((diff_samples >= rope_lower) & (diff_samples <= rope_upper)))
    prob_below_rope = float(np.mean(diff_samples < rope_lower))
    prob_above_rope = float(np.mean(diff_samples > rope_upper))

    if prob_above_rope > 0.95:
        rope_decision = "reject"  # Practically significant improvement
    elif prob_in_rope > 0.95:
        rope_decision = "accept"  # Practically equivalent
    else:
        rope_decision = "undecided"

    return BayesianResult(
        prob_treatment_better=round(prob_better, 4),
        expected_lift=round(expected_lift, 4),
        hdi_lower=round(hdi_lower, 4),
        hdi_upper=round(hdi_upper, 4),
        expected_loss_control=round(float(loss_if_choose_control), 6),
        expected_loss_treatment=round(float(loss_if_choose_treatment), 6),
        risk_ratio=round(risk_ratio, 4),
        rope_decision=rope_decision,
        rope_prob_in=round(prob_in_rope, 4),
        rope_prob_below=round(prob_below_rope, 4),
        rope_prob_above=round(prob_above_rope, 4),
        posterior_samples=lift_samples.tolist(),
    )


def normal_normal(
    control_values: np.ndarray,
    treatment_values: np.ndarray,
    prior_mu: float = 0.0,
    prior_sigma: float = 100.0,
    n_samples: int = 100_000,
    credible_interval: float = 0.95,
    rope_lower: float = -1.0,
    rope_upper: float = 1.0,
    use_mcmc: bool = False,
) -> BayesianResult:
    """Normal-Normal model for revenue metrics.

    Uses conjugate analytic solution by default.
    Set use_mcmc=True for PyMC MCMC (slower, more flexible).
    """
    control_values = np.asarray(control_values, dtype=float)
    treatment_values = np.asarray(treatment_values, dtype=float)

    if use_mcmc:
        return _normal_normal_mcmc(
            control_values, treatment_values,
            prior_mu, prior_sigma, n_samples, credible_interval,
            rope_lower, rope_upper,
        )

    # Conjugate Normal-Normal (known variance approximation using sufficient stats)
    n_c, n_t = len(control_values), len(treatment_values)
    mean_c, mean_t = control_values.mean(), treatment_values.mean()
    var_c, var_t = control_values.var(ddof=1), treatment_values.var(ddof=1)

    # Posterior parameters (Normal prior + Normal likelihood)
    prior_prec = 1 / prior_sigma**2
    post_prec_c = prior_prec + n_c / var_c
    post_prec_t = prior_prec + n_t / var_t
    post_var_c = 1 / post_prec_c
    post_var_t = 1 / post_prec_t
    post_mean_c = post_var_c * (prior_prec * prior_mu + n_c * mean_c / var_c)
    post_mean_t = post_var_t * (prior_prec * prior_mu + n_t * mean_t / var_t)

    # Sample from posteriors
    rng = np.random.default_rng(42)
    samples_c = rng.normal(post_mean_c, np.sqrt(post_var_c), n_samples)
    samples_t = rng.normal(post_mean_t, np.sqrt(post_var_t), n_samples)

    return _compute_bayesian_result(
        samples_c, samples_t, credible_interval, rope_lower, rope_upper,
    )


def _normal_normal_mcmc(
    control_values: np.ndarray,
    treatment_values: np.ndarray,
    prior_mu: float,
    prior_sigma: float,
    n_samples: int,
    credible_interval: float,
    rope_lower: float,
    rope_upper: float,
) -> BayesianResult:
    """PyMC MCMC for Normal-Normal model."""
    import pymc as pm
    import arviz as az

    with pm.Model() as model:
        mu_c = pm.Normal("mu_control", mu=prior_mu, sigma=prior_sigma)
        mu_t = pm.Normal("mu_treatment", mu=prior_mu, sigma=prior_sigma)
        sigma_c = pm.HalfNormal("sigma_control", sigma=control_values.std() * 2)
        sigma_t = pm.HalfNormal("sigma_treatment", sigma=treatment_values.std() * 2)

        pm.Normal("obs_control", mu=mu_c, sigma=sigma_c, observed=control_values)
        pm.Normal("obs_treatment", mu=mu_t, sigma=sigma_t, observed=treatment_values)

        diff = pm.Deterministic("diff", mu_t - mu_c)

        trace = pm.sample(n_samples // 4, tune=1000, cores=1, return_inferencedata=True,
                          progressbar=False)

    samples_c = trace.posterior["mu_control"].values.flatten()
    samples_t = trace.posterior["mu_treatment"].values.flatten()

    return _compute_bayesian_result(
        samples_c, samples_t, credible_interval, rope_lower, rope_upper,
    )


def _compute_bayesian_result(
    samples_c: np.ndarray,
    samples_t: np.ndarray,
    credible_interval: float,
    rope_lower: float,
    rope_upper: float,
) -> BayesianResult:
    """Common computation from posterior samples."""
    diff_samples = samples_t - samples_c
    lift_samples = diff_samples / np.abs(samples_c)
    lift_samples = lift_samples[np.isfinite(lift_samples)]

    prob_better = float(np.mean(samples_t > samples_c))
    expected_lift = float(np.mean(lift_samples)) if len(lift_samples) > 0 else 0

    tail = (1 - credible_interval) / 2
    hdi_lower = float(np.percentile(diff_samples, tail * 100))
    hdi_upper = float(np.percentile(diff_samples, (1 - tail) * 100))

    loss_treatment = float(np.mean(np.maximum(samples_c - samples_t, 0)))
    loss_control = float(np.mean(np.maximum(samples_t - samples_c, 0)))
    risk_ratio = loss_treatment / loss_control if loss_control > 0 else float('inf')

    prob_in_rope = float(np.mean((diff_samples >= rope_lower) & (diff_samples <= rope_upper)))
    prob_below = float(np.mean(diff_samples < rope_lower))
    prob_above = float(np.mean(diff_samples > rope_upper))

    if prob_above > 0.95:
        rope_decision = "reject"
    elif prob_in_rope > 0.95:
        rope_decision = "accept"
    else:
        rope_decision = "undecided"

    return BayesianResult(
        prob_treatment_better=round(prob_better, 4),
        expected_lift=round(expected_lift, 4),
        hdi_lower=round(hdi_lower, 4),
        hdi_upper=round(hdi_upper, 4),
        expected_loss_control=round(loss_control, 6),
        expected_loss_treatment=round(loss_treatment, 6),
        risk_ratio=round(risk_ratio, 4),
        rope_decision=rope_decision,
        rope_prob_in=round(prob_in_rope, 4),
        rope_prob_below=round(prob_below, 4),
        rope_prob_above=round(prob_above, 4),
    )
