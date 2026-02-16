"""Orders & Revenue Analysis — 5-tab page."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date

from src.analytics.orders import OrderAnalyzer
from src.data.cache import cached_query
from src.config.loader import load_settings
from src.utils.formatters import format_currency, format_number, format_percent
from src.utils.date_utils import get_date_range, date_to_str
from src.utils.chart_factory import (
    line_chart, bar_chart, heatmap, treemap, apply_theme, COLORS,
)

settings = load_settings()
analyzer = OrderAnalyzer()

st.title("Orders & Revenue")

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

tab_kpis, tab_cohorts, tab_products, tab_categories, tab_trends = st.tabs(
    ["KPIs", "Cohorts", "Products", "Categories", "Trends"]
)

# ── KPIs ──────────────────────────────────────────────────
with tab_kpis:
    try:
        df = cached_query(
            "orders.sql",
            query_type="revenue_kpis",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df.empty:
            row = df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("GMV", format_currency(row.get("gmv", 0), 0))
            c2.metric("Orders", format_number(row.get("order_count", 0)))
            c3.metric("AOV", format_currency(row.get("aov", 0)))
            c4.metric("Units Sold", format_number(row.get("units_sold", 0)))

        # Daily trend
        df_daily = cached_query(
            "orders.sql",
            query_type="daily_revenue",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df_daily.empty:
            fig = line_chart(df_daily, x="date", y="revenue", title="Daily Revenue")
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Failed to load KPI data: {e}")

# ── Cohorts ───────────────────────────────────────────────
with tab_cohorts:
    try:
        cohort_period = st.selectbox("Cohort period", ["MONTH", "WEEK"], index=0)
        df_cohort = cached_query(
            "orders.sql",
            query_type="cohort",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
            cohort_period=cohort_period,
        )
        if not df_cohort.empty:
            retention = analyzer.cohort_analysis(df_cohort)
            fig = go.Figure(data=go.Heatmap(
                z=retention.values,
                x=[f"M+{c}" for c in retention.columns],
                y=[str(d.date()) if hasattr(d, 'date') else str(d) for d in retention.index],
                colorscale="Blues",
                text=[[f"{v:.0%}" if pd.notna(v) else "" for v in row] for row in retention.values],
                texttemplate="%{text}",
                hovertemplate="Cohort: %{y}<br>Period: %{x}<br>Retention: %{z:.1%}<extra></extra>",
            ))
            fig.update_layout(title="Cohort Retention Matrix", xaxis_title="Period", yaxis_title="Cohort")
            st.plotly_chart(apply_theme(fig), use_container_width=True)

            st.subheader("LTV Curves")
            ltv = analyzer.cohort_ltv(df_cohort)
            fig_ltv = line_chart(ltv, x="period_offset", y="ltv", color="cohort_month",
                                 title="Cumulative LTV by Cohort")
            st.plotly_chart(fig_ltv, use_container_width=True)
        else:
            st.info("No cohort data.")
    except Exception as e:
        st.error(f"Failed to load cohort data: {e}")

# ── Products ──────────────────────────────────────────────
with tab_products:
    product_limit = st.slider("Top N products", 10, 200, 50, key="prod_limit")
    try:
        df_prod = cached_query(
            "orders.sql",
            query_type="product_performance",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
            limit=product_limit,
        )
        if not df_prod.empty:
            result = analyzer.product_performance(df_prod)
            st.dataframe(
                result.style.format({
                    "revenue": "${:,.2f}",
                    "revenue_share": "{:.2%}",
                    "avg_price": "${:,.2f}",
                }),
                use_container_width=True,
            )
            fig = bar_chart(result.head(20), x="product_id", y="revenue",
                            title="Top 20 Products by Revenue")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No product data.")
    except Exception as e:
        st.error(f"Failed to load product data: {e}")

# ── Categories ────────────────────────────────────────────
with tab_categories:
    try:
        df_cat = cached_query(
            "orders.sql",
            query_type="category_performance",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
            include_l3=False,
        )
        if not df_cat.empty:
            result = analyzer.category_analysis(df_cat)
            fig = treemap(result, path=["category_l1", "category_l2"], values="revenue",
                          title="Revenue by Category")
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(result, use_container_width=True)
        else:
            st.info("No category data.")
    except Exception as e:
        st.error(f"Failed to load category data: {e}")

# ── Trends ────────────────────────────────────────────────
with tab_trends:
    try:
        df_daily = cached_query(
            "orders.sql",
            query_type="daily_revenue",
            dataset=dataset,
            start_date=start_str,
            end_date=end_str,
        )
        if not df_daily.empty and len(df_daily) >= 14:
            st.subheader("STL Decomposition")
            period = st.selectbox("Seasonality period (days)", [7, 14, 30], index=0)
            decomp = analyzer.time_series_decomposition(df_daily, period=period)
            for component in ["observed", "trend", "seasonal", "residual"]:
                fig = line_chart(
                    pd.DataFrame({"date": decomp[component].index, component: decomp[component].values}),
                    x="date", y=component, title=component.capitalize(),
                )
                st.plotly_chart(fig, use_container_width=True)

            st.subheader("Trend Detection")
            trend_result = analyzer.trend_detection(df_daily)
            c1, c2, c3 = st.columns(3)
            c1.metric("Trend", trend_result["trend"])
            c2.metric("Mann-Kendall Z", f"{trend_result['z_statistic']:.3f}")
            c3.metric("p-value", f"{trend_result['p_value']:.4f}")
            st.write(f"**Theil-Sen slope**: {trend_result['theil_sen_slope']:.2f} per day")
        elif not df_daily.empty:
            st.warning("Need at least 14 days of data for trend analysis.")
        else:
            st.info("No daily revenue data.")
    except Exception as e:
        st.error(f"Failed to load trend data: {e}")
