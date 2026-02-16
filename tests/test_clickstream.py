"""Tests for ClickstreamAnalyzer."""

import pandas as pd
import pytest

from src.analytics.clickstream import ClickstreamAnalyzer


@pytest.fixture
def analyzer():
    return ClickstreamAnalyzer()


class TestSessionMetrics:
    def test_basic_metrics(self, analyzer, clickstream_session_df):
        result = analyzer.session_metrics(clickstream_session_df)
        assert "sessions" in result.columns
        assert "bounce_rate" in result.columns
        assert "pages_per_session" in result.columns
        assert result["sessions"].iloc[0] > 0
        assert 0 <= result["bounce_rate"].iloc[0] <= 1

    def test_segmented_metrics(self, analyzer, clickstream_session_df):
        result = analyzer.session_metrics(clickstream_session_df, segment="device_category")
        assert "segment" in result.columns
        assert len(result) > 1
        assert result["sessions"].sum() > 0


class TestFunnelAnalysis:
    def test_funnel_steps(self, analyzer, clickstream_funnel_df):
        steps = ["page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"]
        result = analyzer.funnel_analysis(clickstream_funnel_df, steps=steps)
        assert len(result) == 5
        assert result.iloc[0]["sessions"] >= result.iloc[-1]["sessions"]
        assert result.iloc[0]["conversion_from_start"] == 1.0

    def test_drop_off_rates(self, analyzer, clickstream_funnel_df):
        steps = ["page_view", "product_view", "add_to_cart"]
        result = analyzer.funnel_analysis(clickstream_funnel_df, steps=steps)
        assert result.iloc[0]["drop_off_rate"] == 0  # first step has no drop-off
        assert all(0 <= r <= 1 for r in result["drop_off_rate"])


class TestTrafficSourceBreakdown:
    def test_enrichment(self, analyzer, traffic_sources_df):
        result = analyzer.traffic_source_breakdown(traffic_sources_df)
        assert "conversion_rate" in result.columns
        assert "revenue_per_session" in result.columns
        assert abs(result.iloc[0]["conversion_rate"] - 200 / 5000) < 0.001


class TestDeviceSegmentation:
    def test_session_share(self, analyzer, device_df):
        result = analyzer.device_segmentation(device_df)
        assert "session_share" in result.columns
        assert abs(result["session_share"].sum() - 1.0) < 0.001


class TestPageEngagement:
    def test_engagement_score(self, analyzer, page_engagement_df):
        result = analyzer.page_engagement(page_engagement_df)
        assert "engagement_score" in result.columns
        assert all(0 <= s <= 1 for s in result["engagement_score"])
        # Checkout page has highest time, scroll, lowest exit → should rank high
        assert result.iloc[0]["page_path"] == "/checkout"
