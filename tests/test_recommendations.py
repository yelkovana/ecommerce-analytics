"""Tests for RecommendationAnalyzer."""

import numpy as np
import pandas as pd
import pytest

from src.analytics.recommendations import RecommendationAnalyzer


@pytest.fixture
def analyzer():
    return RecommendationAnalyzer()


class TestEngagementMetrics:
    def test_rates(self, analyzer, rec_engagement_df):
        result = analyzer.engagement_metrics(rec_engagement_df)
        assert "ctr" in result.columns
        assert "conversion_rate" in result.columns
        assert all(result["ctr"] >= 0)
        assert all(result["ctr"] <= 1)


class TestRevenueImpact:
    def test_lift_calculation(self, analyzer):
        df = pd.DataFrame({
            "interacted_with_recs": [0, 1],
            "sessions": [8000, 2000],
            "revenue": [160000, 80000],
            "avg_revenue_per_session": [20.0, 40.0],
            "aov": [50.0, 60.0],
            "orders": [3200, 1200],
        })
        result = analyzer.revenue_impact(df)
        assert result["lift"]["revenue_per_session_lift"] == 1.0  # 40/20 - 1
        assert result["lift"]["aov_lift"] == 0.2  # 60/50 - 1


class TestCoverageDiversity:
    def test_metrics(self, analyzer, rec_product_df):
        result = analyzer.coverage_diversity(rec_product_df, total_catalog_size=1000)
        assert 0 < result["catalog_coverage"] <= 1
        assert 0 <= result["gini_coefficient"] <= 1
        assert result["products_recommended"] == 200

    def test_full_coverage(self, analyzer, rec_product_df):
        result = analyzer.coverage_diversity(rec_product_df, total_catalog_size=200)
        assert result["catalog_coverage"] == 1.0


class TestColdStart:
    def test_cold_start_ctr(self, analyzer):
        df = pd.DataFrame({
            "is_new_user": [True, True, False, False],
            "is_new_item": [True, False, True, False],
            "impressions": [1000, 2000, 1500, 5000],
            "clicks": [20, 80, 45, 300],
            "purchases": [2, 10, 5, 50],
        })
        result = analyzer.cold_start_analysis(df)
        assert len(result) == 4
        # New user + new item should have lowest CTR
        new_both = result[(result["is_new_user"]) & (result["is_new_item"])]
        assert new_both["ctr"].iloc[0] == pytest.approx(0.02)
