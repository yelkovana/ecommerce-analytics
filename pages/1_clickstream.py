"""Clickstream Analysis — 5-tab page."""

import streamlit as st
import pandas as pd
from datetime import date, timedelta

from src.analytics.clickstream import ClickstreamAnalyzer
from src.data.cache import cached_query
from src.config.loader import load_settings, load_metrics
from src.utils.formatters import format_number, format_percent, format_duration, format_delta
from src.utils.date_utils import get_date_range, previous_period, date_to_str
from src.utils.chart_factory import (
    line_chart, bar_chart, funnel_chart, heatmap, pie_chart, apply_theme, COLORS,
)

settings = load_settings()
metrics_cfg = load_metrics()
analyzer = ClickstreamAnalyzer()

st.title("Clickstream Analysis")

# --- Sidebar filters ---
with st.sidebar:
    st.subheader("Filters")
    date_range = st.date_input(
        "Date range",
        value=get_date_range(settings.app.default_date_range_days),
        max_value=date.today(),
    )
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = get_date_range(settings.app.default_date_range_days)

    segment_options = ["None", "device_category", "traffic_source", "traffic_medium"]
    segment_choice = st.selectbox("Segment by", segment_options)
    segment = None if segment_choice == "None" else segment_choice

dataset = settings.bigquery.dataset
start_str = date_to_str(start_date)
end_str = date_to_str(end_date)

# --- Tabs ---
tab_sessions, tab_funnels, tab_sources, tab_devices, tab_pages = st.tabs(
    ["Sessions", "Funnels", "Traffic Sources", "Devices", "Page Engagement"]
)

# ── Sessions ──────────────────────────────────────────────
with tab_sessions:
    try:
        df_sessions = cached_query(
            "clickstream.sql",
            query_type="session_metrics",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
            segment=segment,
        )
        result = analyzer.session_metrics(df_sessions, segment=segment) if not df_sessions.empty else df_sessions

        if not result.empty:
            cols = st.columns(4)
            row = result.iloc[0] if segment is None else result
            if segment is None:
                cols[0].metric("Sessions", format_number(row["sessions"]))
                cols[1].metric("Pages / Session", f"{row['pages_per_session']:.1f}")
                cols[2].metric("Avg Duration", format_duration(row["avg_session_duration"]))
                cols[3].metric("Bounce Rate", format_percent(row["bounce_rate"]))
            else:
                st.dataframe(result, use_container_width=True)

            if segment and len(result) > 1:
                fig = bar_chart(result, x="segment", y="sessions", title="Sessions by Segment")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No session data for the selected period.")
    except Exception as e:
        st.error(f"Failed to load session data: {e}")

# ── Funnels ───────────────────────────────────────────────
with tab_funnels:
    default_steps = ["page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"]
    funnel_steps = st.multiselect("Funnel steps", default_steps, default=default_steps)

    if len(funnel_steps) >= 2:
        try:
            df_funnel = cached_query(
                "clickstream.sql",
                query_type="funnel",
                dataset=dataset,
                start_date=start_str,
                end_date=end_str,
                funnel_steps=funnel_steps,
            )
            if not df_funnel.empty:
                result = analyzer.funnel_analysis(df_funnel, steps=funnel_steps)
                fig = funnel_chart(
                    stages=result["step"].tolist(),
                    values=result["sessions"].tolist(),
                    title="Conversion Funnel",
                )
                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(
                    result.style.format({
                        "drop_off_rate": "{:.1%}",
                        "conversion_from_start": "{:.1%}",
                    }),
                    use_container_width=True,
                )
            else:
                st.info("No funnel data for the selected steps.")
        except Exception as e:
            st.error(f"Failed to load funnel data: {e}")
    else:
        st.warning("Select at least 2 funnel steps.")

# ── Traffic Sources ───────────────────────────────────────
with tab_sources:
    try:
        df_sources = cached_query(
            "clickstream.sql",
            query_type="traffic_sources_with_conversions",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df_sources.empty:
            result = analyzer.traffic_source_breakdown(df_sources)
            st.dataframe(
                result.style.format({
                    "conversion_rate": "{:.2%}",
                    "revenue_per_session": "${:.2f}",
                    "revenue": "${:,.0f}",
                }),
                use_container_width=True,
            )

            col1, col2 = st.columns(2)
            with col1:
                fig = bar_chart(
                    result.head(10), x="traffic_source", y="sessions",
                    title="Top 10 Sources by Sessions",
                )
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = bar_chart(
                    result.head(10), x="traffic_source", y="revenue",
                    title="Top 10 Sources by Revenue",
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No traffic source data.")
    except Exception as e:
        st.error(f"Failed to load traffic source data: {e}")

# ── Devices ───────────────────────────────────────────────
with tab_devices:
    try:
        df_devices = cached_query(
            "clickstream.sql",
            query_type="device_segmentation",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df_devices.empty:
            result = analyzer.device_segmentation(df_devices)

            col1, col2 = st.columns(2)
            with col1:
                device_agg = result.groupby("device_category")["sessions"].sum().reset_index()
                fig = pie_chart(device_agg, names="device_category", values="sessions",
                                title="Sessions by Device")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                browser_agg = result.groupby("browser")["sessions"].sum().reset_index()
                fig = bar_chart(browser_agg.head(10), x="browser", y="sessions",
                                title="Top 10 Browsers")
                st.plotly_chart(fig, use_container_width=True)

            st.dataframe(result, use_container_width=True)
        else:
            st.info("No device data.")
    except Exception as e:
        st.error(f"Failed to load device data: {e}")

# ── Page Engagement ───────────────────────────────────────
with tab_pages:
    page_limit = st.slider("Number of pages to show", 10, 200, 50)
    try:
        df_pages = cached_query(
            "clickstream.sql",
            query_type="page_engagement",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
            limit=page_limit,
        )
        if not df_pages.empty:
            result = analyzer.page_engagement(df_pages)
            st.dataframe(
                result.style.format({
                    "avg_time_on_page": "{:.1f}s",
                    "avg_scroll_depth": "{:.0%}",
                    "exit_rate": "{:.1%}",
                    "engagement_score": "{:.3f}",
                }).background_gradient(subset=["engagement_score"], cmap="Blues"),
                use_container_width=True,
            )
        else:
            st.info("No page engagement data.")
    except Exception as e:
        st.error(f"Failed to load page engagement data: {e}")
