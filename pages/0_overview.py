"""Overview — Executive Dashboard with cross-module KPIs."""

import streamlit as st
import pandas as pd
from datetime import date

from src.data.cache import cached_query
from src.config.loader import load_settings, load_metrics
from src.utils.formatters import format_currency, format_number, format_percent, format_duration, format_metric
from src.utils.date_utils import get_date_range, previous_period, date_to_str
from src.utils.chart_factory import sparkline, traffic_light, COLORS

settings = load_settings()
metrics_cfg = load_metrics()

st.title("E-Commerce Analytics Overview")

# --- Sidebar ---
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

dataset = settings.bigquery.dataset
start_str = date_to_str(start_date)
end_str = date_to_str(end_date)

# Previous period for delta calculations
prev_start, prev_end = previous_period(start_date, end_date)
prev_start_str = date_to_str(prev_start)
prev_end_str = date_to_str(prev_end)

# ═══════════════════════════════════════════════════════════
# KPI Cards
# ═══════════════════════════════════════════════════════════
st.subheader("Key Metrics")

try:
    # Current period
    df_orders = cached_query(
        "orders.sql", query_type="revenue_kpis",
        dataset=dataset, start_date=start_str, end_date=end_str,
    )
    df_sessions = cached_query(
        "clickstream.sql", query_type="session_metrics",
        dataset=dataset, start_date=start_str, end_date=end_str, segment=None,
    )

    # Previous period
    df_orders_prev = cached_query(
        "orders.sql", query_type="revenue_kpis",
        dataset=dataset, start_date=prev_start_str, end_date=prev_end_str,
    )
    df_sessions_prev = cached_query(
        "clickstream.sql", query_type="session_metrics",
        dataset=dataset, start_date=prev_start_str, end_date=prev_end_str, segment=None,
    )

    def safe_get(df, col, default=0):
        if df.empty:
            return default
        return df.iloc[0].get(col, default)

    def calc_delta(current, previous):
        if previous and previous != 0:
            return (current - previous) / abs(previous)
        return None

    gmv = safe_get(df_orders, "gmv")
    gmv_prev = safe_get(df_orders_prev, "gmv")
    sessions = safe_get(df_sessions, "sessions")
    sessions_prev = safe_get(df_sessions_prev, "sessions")
    orders = safe_get(df_orders, "order_count")
    orders_prev = safe_get(df_orders_prev, "order_count")
    aov = safe_get(df_orders, "aov")
    aov_prev = safe_get(df_orders_prev, "aov")

    conv_rate = orders / sessions if sessions > 0 else 0
    conv_prev = orders_prev / sessions_prev if sessions_prev > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("GMV", format_currency(gmv, 0),
                delta=f"{calc_delta(gmv, gmv_prev):+.1%}" if calc_delta(gmv, gmv_prev) else None)
    col2.metric("Sessions", format_number(sessions),
                delta=f"{calc_delta(sessions, sessions_prev):+.1%}" if calc_delta(sessions, sessions_prev) else None)
    col3.metric("Conversion Rate", format_percent(conv_rate, 2),
                delta=f"{calc_delta(conv_rate, conv_prev):+.1%}" if calc_delta(conv_rate, conv_prev) else None)
    col4.metric("AOV", format_currency(aov),
                delta=f"{calc_delta(aov, aov_prev):+.1%}" if calc_delta(aov, aov_prev) else None)

except Exception as e:
    st.warning(f"Could not load KPI data: {e}")
    st.info("Connect to BigQuery to see live data. Showing placeholder layout.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("GMV", "$—")
    col2.metric("Sessions", "—")
    col3.metric("Conversion Rate", "—")
    col4.metric("AOV", "$—")

# ═══════════════════════════════════════════════════════════
# Sparkline Trends
# ═══════════════════════════════════════════════════════════
st.subheader("7-Day Trends")

try:
    df_daily = cached_query(
        "orders.sql", query_type="daily_revenue",
        dataset=dataset, start_date=start_str, end_date=end_str,
    )
    if not df_daily.empty:
        recent = df_daily.tail(7)
        tc1, tc2, tc3 = st.columns(3)
        with tc1:
            st.caption("Revenue")
            st.plotly_chart(sparkline(recent["revenue"].tolist()), use_container_width=True)
        with tc2:
            st.caption("Orders")
            st.plotly_chart(sparkline(recent["orders"].tolist(), color=COLORS["secondary"]),
                            use_container_width=True)
        with tc3:
            st.caption("AOV")
            st.plotly_chart(sparkline(recent["aov"].tolist(), color=COLORS["success"]),
                            use_container_width=True)
except Exception:
    st.info("Daily trend data unavailable.")

# ═══════════════════════════════════════════════════════════
# Health Indicators
# ═══════════════════════════════════════════════════════════
st.subheader("Module Health")


def evaluate_health(value, metric_def):
    """Evaluate metric health based on thresholds."""
    if metric_def.thresholds is None:
        return "good"
    t = metric_def.thresholds
    if metric_def.direction == "higher_is_better":
        if value >= t.good:
            return "good"
        elif value >= t.warning:
            return "warning"
        else:
            return "critical"
    else:  # lower_is_better
        if value <= t.good:
            return "good"
        elif value <= t.warning:
            return "warning"
        else:
            return "critical"


health_items = {
    "Clickstream": "good",
    "Orders & Revenue": "good",
    "Recommendations": "good",
    "A/B Testing": "good",
}

# Try to evaluate actual health from metrics
try:
    bounce = safe_get(df_sessions, "bounce_rate", 0.4) if 'df_sessions' in dir() else 0.4
    if "bounce_rate" in metrics_cfg.clickstream:
        health_items["Clickstream"] = evaluate_health(bounce, metrics_cfg.clickstream["bounce_rate"])
except Exception:
    pass

hc = st.columns(len(health_items))
for i, (module, status) in enumerate(health_items.items()):
    with hc[i]:
        st.markdown(f"{traffic_light(status)} **{module}**")
        st.caption(status.capitalize())
