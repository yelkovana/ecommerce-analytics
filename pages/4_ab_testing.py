"""A/B Testing Analysis — 6-section page."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

from src.analytics.ab_testing.frequentist import two_proportion_z_test, welch_t_test
from src.analytics.ab_testing.bayesian import beta_binomial, normal_normal
from src.analytics.ab_testing.sequential import interim_analysis
from src.analytics.ab_testing.power import sample_size_proportion, sample_size_mean, estimate_duration
from src.analytics.ab_testing.diagnostics import srm_check, novelty_detection, cuped
from src.analytics.ab_testing.corrections import apply_correction
from src.analytics.ab_testing.models import FrequentistResult, BayesianResult
from src.data.cache import cached_query
from src.config.loader import load_settings, load_ab_test_config
from src.utils.formatters import format_percent, format_number, format_currency
from src.utils.date_utils import get_date_range, date_to_str
from src.utils.chart_factory import apply_theme, COLORS, PALETTE

settings = load_settings()
ab_cfg = load_ab_test_config()

st.title("A/B Testing")

dataset = settings.bigquery.dataset

# --- Sidebar: Test selection ---
with st.sidebar:
    st.subheader("Test Selection")
    try:
        tests_df = cached_query("ab_tests.sql", query_type="test_list", dataset=dataset, status="active")
        if not tests_df.empty:
            test_options = dict(zip(tests_df["test_name"], tests_df["test_id"]))
            selected_test_name = st.selectbox("Select test", list(test_options.keys()))
            selected_test_id = test_options[selected_test_name]
        else:
            st.info("No active tests found.")
            selected_test_id = None
    except Exception:
        st.warning("Could not load test list. Using demo mode.")
        selected_test_id = None

# ═══════════════════════════════════════════════════════════
# Section 1: Test Overview + SRM Check
# ═══════════════════════════════════════════════════════════
st.header("1. Test Overview & SRM Check")

if selected_test_id:
    try:
        assignments_df = cached_query(
            "ab_tests.sql", query_type="test_assignments",
            dataset=dataset, test_id=selected_test_id,
        )
        summary_df = cached_query(
            "ab_tests.sql", query_type="test_summary",
            dataset=dataset, test_id=selected_test_id,
        )

        if not summary_df.empty:
            st.dataframe(summary_df, use_container_width=True)

            # SRM Check
            variant_counts = summary_df.set_index("variant")["users"].to_dict()
            counts = list(variant_counts.values())
            srm = srm_check(counts)

            if srm.is_srm:
                st.error(f"⚠️ Sample Ratio Mismatch detected! (χ²={srm.chi_square:.2f}, p={srm.p_value:.6f})")
            else:
                st.success(f"✓ No SRM detected (χ²={srm.chi_square:.2f}, p={srm.p_value:.4f})")
    except Exception as e:
        st.error(f"Failed to load test data: {e}")
else:
    st.info("Select an active test from the sidebar, or use the sample size calculator below.")

# ═══════════════════════════════════════════════════════════
# Section 2: Sample Size Calculator
# ═══════════════════════════════════════════════════════════
st.header("2. Sample Size Calculator")

calc_col1, calc_col2 = st.columns(2)
with calc_col1:
    metric_type = st.radio("Metric type", ["Proportion (conversion)", "Mean (revenue)"], key="calc_type")
    alpha_input = st.slider("Significance level (α)", 0.01, 0.10, ab_cfg.defaults.significance_level, 0.01)
    power_input = st.slider("Power (1-β)", 0.70, 0.99, ab_cfg.defaults.power, 0.01)

with calc_col2:
    if metric_type.startswith("Proportion"):
        baseline = st.number_input("Baseline conversion rate", 0.001, 0.5, 0.05, 0.005, format="%.3f")
        mde = st.number_input("Min detectable effect (absolute)", 0.001, 0.1, 0.01, 0.001, format="%.3f")
        result = sample_size_proportion(baseline, mde, alpha_input, power_input)
    else:
        baseline_mean = st.number_input("Baseline mean", 0.01, 10000.0, 50.0)
        baseline_std = st.number_input("Baseline std dev", 0.01, 10000.0, 15.0)
        mde_abs = st.number_input("Min detectable effect (absolute)", 0.01, 1000.0, 2.0)
        result = sample_size_mean(baseline_mean, baseline_std, mde_abs, alpha_input, power_input)

    daily_traffic = st.number_input("Daily traffic (users)", 100, 10_000_000, 10000)

st.metric("Required sample size (total)", format_number(result.required_sample_size))
st.metric("Per variant", format_number(result.required_sample_per_variant))
days = estimate_duration(result.required_sample_size, daily_traffic)
st.metric("Estimated duration", f"{days:.1f} days")

# ═══════════════════════════════════════════════════════════
# Section 3: Frequentist vs Bayesian Results
# ═══════════════════════════════════════════════════════════
st.header("3. Test Results")

if selected_test_id:
    try:
        metrics_df = cached_query(
            "ab_tests.sql", query_type="test_metrics",
            dataset=dataset, test_id=selected_test_id,
        )
        summary_df = cached_query(
            "ab_tests.sql", query_type="test_summary",
            dataset=dataset, test_id=selected_test_id,
        )

        if not metrics_df.empty and not summary_df.empty:
            control = summary_df[summary_df["variant"] == "control"].iloc[0]
            treatment = summary_df[summary_df["variant"] == "treatment"].iloc[0]

            freq_col, bayes_col = st.columns(2)

            # --- Frequentist ---
            with freq_col:
                st.subheader("Frequentist")

                # Conversion test
                freq_conv = two_proportion_z_test(
                    int(control["conversions"]), int(control["users"]),
                    int(treatment["conversions"]), int(treatment["users"]),
                    alpha=ab_cfg.defaults.significance_level,
                )
                st.write(f"**{freq_conv.test_name}**")
                st.write(f"Control: {freq_conv.control_mean:.4f} | Treatment: {freq_conv.treatment_mean:.4f}")
                st.write(f"Z = {freq_conv.statistic:.3f}, p = {freq_conv.p_value:.4f}")
                st.write(f"Effect: {freq_conv.absolute_effect:.4f} ({freq_conv.relative_effect:.1%})")
                st.write(f"95% CI: [{freq_conv.ci_lower:.4f}, {freq_conv.ci_upper:.4f}]")
                if freq_conv.significant:
                    st.success("✓ Statistically significant")
                else:
                    st.warning("✗ Not significant")

                # Revenue test
                ctrl_rev = metrics_df[metrics_df["variant"] == "control"]["revenue"].values
                treat_rev = metrics_df[metrics_df["variant"] == "treatment"]["revenue"].values
                if len(ctrl_rev) > 0 and len(treat_rev) > 0:
                    freq_rev = welch_t_test(ctrl_rev, treat_rev, alpha=ab_cfg.defaults.significance_level)
                    st.write(f"\n**{freq_rev.test_name} (Revenue)**")
                    st.write(f"Control: ${freq_rev.control_mean:.2f} | Treatment: ${freq_rev.treatment_mean:.2f}")
                    st.write(f"t = {freq_rev.statistic:.3f}, p = {freq_rev.p_value:.4f}")
                    st.write(f"Cohen's d = {freq_rev.effect_size:.3f}")

            # --- Bayesian ---
            with bayes_col:
                st.subheader("Bayesian")

                bayes_conv = beta_binomial(
                    int(control["conversions"]), int(control["users"]),
                    int(treatment["conversions"]), int(treatment["users"]),
                    prior_alpha=ab_cfg.bayesian.prior_alpha,
                    prior_beta=ab_cfg.bayesian.prior_beta,
                    rope_lower=ab_cfg.bayesian.rope_lower,
                    rope_upper=ab_cfg.bayesian.rope_upper,
                )
                st.write(f"**P(Treatment > Control)**: {bayes_conv.prob_treatment_better:.1%}")
                st.write(f"**Expected Lift**: {bayes_conv.expected_lift:.2%}")
                st.write(f"**95% HDI**: [{bayes_conv.hdi_lower:.4f}, {bayes_conv.hdi_upper:.4f}]")
                st.write(f"**Expected Loss (Treatment)**: {bayes_conv.expected_loss_treatment:.6f}")
                st.write(f"**ROPE Decision**: {bayes_conv.rope_decision}")

                # Posterior distribution plot
                if bayes_conv.posterior_samples:
                    fig = go.Figure(go.Histogram(
                        x=bayes_conv.posterior_samples,
                        nbinsx=100,
                        marker_color=COLORS["primary"],
                        opacity=0.7,
                    ))
                    fig.add_vline(x=0, line_dash="dash", line_color="red")
                    fig.update_layout(title="Posterior Lift Distribution",
                                      xaxis_title="Relative Lift", yaxis_title="Frequency")
                    st.plotly_chart(apply_theme(fig), use_container_width=True)
    except Exception as e:
        st.error(f"Failed to load test results: {e}")
else:
    st.info("Select a test to view results.")

# ═══════════════════════════════════════════════════════════
# Section 4: Sequential Analysis
# ═══════════════════════════════════════════════════════════
st.header("4. Sequential Analysis")

if selected_test_id and 'freq_conv' in dir():
    seq_col1, seq_col2 = st.columns(2)
    with seq_col1:
        spending_fn = st.selectbox("Spending function",
                                    ["obrien-fleming", "pocock"],
                                    index=0)
        max_looks = st.slider("Max looks", 2, 10, ab_cfg.sequential.max_looks)
        current_look = st.slider("Current look", 1, max_looks, min(3, max_looks))

    seq_result = interim_analysis(
        z_stat=freq_conv.statistic,
        current_look=current_look,
        max_looks=max_looks,
        alpha=ab_cfg.defaults.significance_level,
        spending_function=spending_fn,
    )

    with seq_col2:
        st.metric("Decision", seq_result.decision)
        st.metric("Boundary", f"{seq_result.boundary_value:.4f}")
        st.metric("Z-stat", f"{seq_result.z_statistic:.4f}")
        st.metric("Alpha spent", f"{seq_result.alpha_spent:.4f}")

    # Monitoring chart
    fig = go.Figure()
    looks = list(range(1, max_looks + 1))
    fig.add_trace(go.Scatter(x=looks, y=seq_result.boundaries, mode="lines+markers",
                              name="Upper Boundary", line=dict(color="red", dash="dash")))
    fig.add_trace(go.Scatter(x=looks, y=[-b for b in seq_result.boundaries], mode="lines+markers",
                              name="Lower Boundary", line=dict(color="red", dash="dash")))
    fig.add_trace(go.Scatter(x=[current_look], y=[freq_conv.statistic],
                              mode="markers", marker=dict(size=12, color=COLORS["primary"]),
                              name="Current Z-stat"))
    fig.update_layout(title="Sequential Monitoring", xaxis_title="Look", yaxis_title="Z-statistic")
    st.plotly_chart(apply_theme(fig), use_container_width=True)
else:
    st.info("Sequential analysis requires an active test with results.")

# ═══════════════════════════════════════════════════════════
# Section 5: CUPED
# ═══════════════════════════════════════════════════════════
st.header("5. CUPED Variance Reduction")

cuped_enabled = st.toggle("Enable CUPED", value=ab_cfg.diagnostics.cuped_enabled)

if cuped_enabled and selected_test_id:
    try:
        if not metrics_df.empty and "pre_experiment_revenue" in metrics_df.columns:
            cuped_result = cuped(
                y=metrics_df["revenue"].values,
                x=metrics_df["pre_experiment_revenue"].values,
                variant=metrics_df["variant"].values,
            )
            c1, c2, c3 = st.columns(3)
            c1.metric("Variance Reduction", format_percent(cuped_result.variance_reduction))
            c2.metric("Adjusted Control Mean", f"${cuped_result.adjusted_control_mean:.2f}")
            c3.metric("Adjusted Treatment Mean", f"${cuped_result.adjusted_treatment_mean:.2f}")
            st.write(f"**θ (theta)**: {cuped_result.theta:.4f}")
            st.write(f"**Adjusted Effect**: ${cuped_result.adjusted_effect:.4f}")
        else:
            st.warning("Pre-experiment data not available for CUPED.")
    except Exception as e:
        st.error(f"CUPED analysis failed: {e}")
elif not cuped_enabled:
    st.info("Toggle CUPED to enable variance reduction analysis.")

# ═══════════════════════════════════════════════════════════
# Section 6: Diagnostics — Novelty + Segments
# ═══════════════════════════════════════════════════════════
st.header("6. Diagnostics")

diag_tab1, diag_tab2 = st.tabs(["Novelty Detection", "Segment Breakdown"])

with diag_tab1:
    if selected_test_id:
        try:
            daily_df = cached_query(
                "ab_tests.sql", query_type="daily_metrics",
                dataset=dataset, test_id=selected_test_id,
            )
            if not daily_df.empty:
                novelty = novelty_detection(
                    daily_df,
                    window_days=ab_cfg.diagnostics.novelty_window_days,
                )
                if novelty["detected"]:
                    st.warning("⚠️ Novelty/Primacy effect detected!")
                else:
                    st.success("✓ No novelty effect detected")
                for variant, data in novelty.get("variants", {}).items():
                    st.write(f"**{variant}**: early={data['early_mean']:.4f}, "
                             f"late={data['late_mean']:.4f}, p={data['p_value']:.4f}")
        except Exception as e:
            st.error(f"Novelty detection failed: {e}")
    else:
        st.info("Select a test for novelty detection.")

with diag_tab2:
    if selected_test_id:
        for dim in ab_cfg.segment_analysis.dimensions:
            st.subheader(f"By {dim}")
            try:
                seg_df = cached_query(
                    "ab_tests.sql", query_type="segment_metrics",
                    dataset=dataset, test_id=selected_test_id,
                    segment_dimension=dim,
                )
                if not seg_df.empty:
                    p_values = []
                    segment_results = []
                    for seg_val in seg_df["segment"].unique():
                        seg_data = seg_df[seg_df["segment"] == seg_val]
                        ctrl = seg_data[seg_data["variant"] == "control"]
                        treat = seg_data[seg_data["variant"] == "treatment"]
                        if not ctrl.empty and not treat.empty:
                            r = two_proportion_z_test(
                                int(ctrl.iloc[0]["conversions"]), int(ctrl.iloc[0]["users"]),
                                int(treat.iloc[0]["conversions"]), int(treat.iloc[0]["users"]),
                            )
                            p_values.append(r.p_value)
                            segment_results.append({"segment": seg_val, **vars(r)})

                    if p_values:
                        corrected = apply_correction(
                            p_values,
                            method=ab_cfg.segment_analysis.correction_method,
                        )
                        for i, sr in enumerate(segment_results):
                            sr["corrected_p"] = corrected[i]["corrected_p"]
                            sr["sig_after_correction"] = corrected[i]["significant"]

                        st.dataframe(pd.DataFrame(segment_results)[[
                            "segment", "control_mean", "treatment_mean",
                            "p_value", "corrected_p", "sig_after_correction",
                        ]], use_container_width=True)
            except Exception as e:
                st.error(f"Segment analysis for {dim} failed: {e}")
    else:
        st.info("Select a test for segment analysis.")
