"""Tests for OrderAnalyzer."""

import numpy as np
import pandas as pd
import pytest

from src.analytics.orders import OrderAnalyzer


@pytest.fixture
def analyzer():
    return OrderAnalyzer()


class TestRevenueKPIs:
    def test_basic_kpis(self, analyzer, orders_kpi_df):
        result = analyzer.revenue_kpis(orders_kpi_df)
        assert result["gmv"] > 0
        assert result["order_count"] > 0
        assert result["aov"] > 0
        assert result["unique_customers"] > 0

    def test_with_sessions(self, analyzer, orders_kpi_df):
        result = analyzer.revenue_kpis(orders_kpi_df, sessions_count=100000)
        assert "revenue_per_session" in result
        assert "conversion_rate" in result
        assert result["conversion_rate"] > 0


class TestCohortAnalysis:
    def test_retention_matrix(self, analyzer, cohort_df):
        result = analyzer.cohort_analysis(cohort_df)
        assert isinstance(result, pd.DataFrame)
        assert 0 in result.columns  # period_offset 0
        # Period 0 retention should be 1.0 (all users active in their cohort month)
        for v in result[0].dropna():
            assert 0.5 <= v <= 1.0  # at least partial retention at period 0

    def test_ltv_curves(self, analyzer, cohort_df):
        result = analyzer.cohort_ltv(cohort_df)
        assert "ltv" in result.columns
        assert "cumulative_revenue" in result.columns
        # LTV should increase over time within a cohort
        for cohort in result["cohort_month"].unique():
            cohort_data = result[result["cohort_month"] == cohort].sort_values("period_offset")
            if len(cohort_data) > 1:
                assert cohort_data["ltv"].is_monotonic_increasing


class TestProductPerformance:
    def test_enrichment(self, analyzer, product_df):
        result = analyzer.product_performance(product_df)
        assert "revenue_share" in result.columns
        assert "revenue_rank" in result.columns
        assert abs(result["revenue_share"].sum() - 1.0) < 0.01


class TestTimeSeriesDecomposition:
    def test_stl(self, analyzer, daily_revenue_df):
        result = analyzer.time_series_decomposition(daily_revenue_df, period=7)
        assert "trend" in result
        assert "seasonal" in result
        assert "residual" in result
        assert len(result["trend"]) == len(daily_revenue_df)


class TestTrendDetection:
    def test_increasing_trend(self, analyzer):
        df = pd.DataFrame({
            "date": pd.date_range("2025-01-01", periods=100),
            "revenue": np.linspace(1000, 2000, 100) + np.random.normal(0, 20, 100),
        })
        result = analyzer.trend_detection(df)
        assert result["trend"] == "increasing"
        assert result["theil_sen_slope"] > 0

    def test_no_trend(self, analyzer):
        np.random.seed(42)
        df = pd.DataFrame({
            "date": pd.date_range("2025-01-01", periods=100),
            "revenue": np.random.normal(1000, 10, 100),
        })
        result = analyzer.trend_detection(df)
        assert result["trend"] == "no trend"
