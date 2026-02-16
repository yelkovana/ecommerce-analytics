"""Recommendation Engine Analysis — 6-tab page."""

import streamlit as st
import pandas as pd
from datetime import date

from src.analytics.recommendations import RecommendationAnalyzer
from src.data.cache import cached_query
from src.config.loader import load_settings
from src.utils.formatters import format_percent, format_currency, format_number
from src.utils.date_utils import get_date_range, date_to_str
from src.utils.chart_factory import bar_chart, pie_chart, line_chart, apply_theme, COLORS

settings = load_settings()
analyzer = RecommendationAnalyzer()

st.title("Recommendation Engine")

# --- Sidebar ---
with st.sidebar:
    st.subheader("Filters")
    date_range = st.date_input(
        "Date range",
        value=get_date_range(settings.app.default_date_range_days),
        max_value=date.today(),
        key="rec_dates",
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = get_date_range(settings.app.default_date_range_days)

dataset = settings.bigquery.dataset
start_str = date_to_str(start_date)
end_str = date_to_str(end_date)

tabs = st.tabs([
    "CTR & Conversion", "Revenue Impact", "Engagement",
    "Algorithm Comparison", "Coverage & Diversity", "Cold Start",
])

# ── CTR & Conversion ─────────────────────────────────────
with tabs[0]:
    try:
        df = cached_query(
            "recommendations.sql",
            query_type="engagement_metrics",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df.empty:
            result = analyzer.engagement_metrics(df)
            st.dataframe(
                result.style.format({
                    "ctr": "{:.2%}",
                    "atc_rate": "{:.2%}",
                    "conversion_rate": "{:.2%}",
                    "click_to_purchase": "{:.2%}",
                }),
                use_container_width=True,
            )
            col1, col2 = st.columns(2)
            with col1:
                fig = bar_chart(result, x="widget_id", y="ctr", title="CTR by Widget")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = bar_chart(result, x="widget_id", y="conversion_rate",
                                title="Conversion Rate by Widget")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No engagement data.")
    except Exception as e:
        st.error(f"Failed to load engagement data: {e}")

# ── Revenue Impact ────────────────────────────────────────
with tabs[1]:
    try:
        df = cached_query(
            "recommendations.sql",
            query_type="revenue_impact",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df.empty:
            impact = analyzer.revenue_impact(df)
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Rec-Interacted Sessions")
                if impact["rec_interacted"]:
                    for k, v in impact["rec_interacted"].items():
                        st.metric(k.replace("_", " ").title(),
                                  format_currency(v) if "revenue" in k or "aov" in k else format_number(v))
            with col2:
                st.subheader("Non-Interacted Sessions")
                if impact["non_interacted"]:
                    for k, v in impact["non_interacted"].items():
                        st.metric(k.replace("_", " ").title(),
                                  format_currency(v) if "revenue" in k or "aov" in k else format_number(v))
            if impact["lift"]:
                st.subheader("Lift")
                lc1, lc2 = st.columns(2)
                lc1.metric("Revenue/Session Lift", format_percent(impact["lift"]["revenue_per_session_lift"]))
                lc2.metric("AOV Lift", format_percent(impact["lift"]["aov_lift"]))
        else:
            st.info("No revenue impact data.")
    except Exception as e:
        st.error(f"Failed to load revenue impact data: {e}")

# ── Engagement ────────────────────────────────────────────
with tabs[2]:
    try:
        df = cached_query(
            "recommendations.sql",
            query_type="widget_comparison",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df.empty:
            result = analyzer.engagement_depth(df)
            st.dataframe(
                result.style.format({
                    "session_ctr": "{:.2%}",
                    "clicks_per_session": "{:.1f}",
                }),
                use_container_width=True,
            )
        else:
            st.info("No engagement depth data.")
    except Exception as e:
        st.error(f"Failed to load engagement depth data: {e}")

# ── Algorithm Comparison ──────────────────────────────────
with tabs[3]:
    try:
        df = cached_query(
            "recommendations.sql",
            query_type="algorithm_comparison",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df.empty:
            result = analyzer.algorithm_comparison(df)
            st.dataframe(
                result.style.format({"ctr": "{:.2%}", "conversion_rate": "{:.2%}"}),
                use_container_width=True,
            )
            fig = bar_chart(result, x="algorithm", y="ctr", color="widget_id",
                            title="CTR by Algorithm & Widget")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No algorithm comparison data.")
    except Exception as e:
        st.error(f"Failed to load algorithm data: {e}")

# ── Coverage & Diversity ──────────────────────────────────
with tabs[4]:
    total_catalog = st.number_input("Total catalog size", min_value=1, value=10000, key="catalog_size")
    try:
        df = cached_query(
            "recommendations.sql",
            query_type="coverage_diversity",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df.empty:
            result = analyzer.coverage_diversity(df, total_catalog_size=total_catalog)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Catalog Coverage", format_percent(result["catalog_coverage"]))
            c2.metric("Products Recommended", format_number(result["products_recommended"]))
            c3.metric("Gini Coefficient", f"{result['gini_coefficient']:.3f}")
            c4.metric("Long-tail Ratio", format_percent(result["long_tail_ratio"]))
            st.metric("New Item Share", format_percent(result["new_item_share"]))
        else:
            st.info("No coverage data.")
    except Exception as e:
        st.error(f"Failed to load coverage data: {e}")

# ── Cold Start ────────────────────────────────────────────
with tabs[5]:
    try:
        df = cached_query(
            "recommendations.sql",
            query_type="cold_start",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df.empty:
            result = analyzer.cold_start_analysis(df)
            st.dataframe(
                result.style.format({"ctr": "{:.2%}", "conversion_rate": "{:.2%}"}),
                use_container_width=True,
            )
        else:
            st.info("No cold start data.")
    except Exception as e:
        st.error(f"Failed to load cold start data: {e}")
