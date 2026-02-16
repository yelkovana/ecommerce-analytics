"""Shared fixtures and mock data generators for tests."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


# ── Clickstream fixtures ──────────────────────────────────

@pytest.fixture
def clickstream_session_df() -> pd.DataFrame:
    """Mock clickstream data at event level."""
    np.random.seed(42)
    n_sessions = 200
    rows = []
    for i in range(n_sessions):
        n_pages = np.random.randint(1, 8)
        session_id = f"s_{i:04d}"
        user_id = f"u_{i % 120:04d}"
        device = np.random.choice(["desktop", "mobile", "tablet"], p=[0.5, 0.4, 0.1])
        source = np.random.choice(["google", "direct", "facebook", "email"], p=[0.4, 0.3, 0.2, 0.1])
        for j in range(n_pages):
            rows.append({
                "session_id": session_id,
                "user_id": user_id,
                "page_path": f"/page_{np.random.randint(1, 20)}",
                "time_on_page": np.random.exponential(30),
                "scroll_depth": np.random.uniform(0.1, 1.0),
                "device_category": device,
                "traffic_source": source,
                "event_name": np.random.choice(
                    ["page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"],
                    p=[0.4, 0.3, 0.15, 0.1, 0.05],
                ),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def clickstream_funnel_df() -> pd.DataFrame:
    """Mock funnel data: each row = one session × event_name."""
    data = []
    events = ["page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"]
    counts = [1000, 600, 300, 180, 100]
    session_id = 0
    for event, count in zip(events, counts):
        for _ in range(count):
            data.append({"session_id": f"s_{session_id:05d}", "event_name": event})
            session_id += 1
    # Reset session_id counter so sessions flow through multiple events:
    # Actually, for a funnel to work we need sessions that hit multiple steps.
    data = []
    for i in range(1000):
        sid = f"s_{i:05d}"
        data.append({"session_id": sid, "event_name": "page_view"})
        if i < 600:
            data.append({"session_id": sid, "event_name": "product_view"})
        if i < 300:
            data.append({"session_id": sid, "event_name": "add_to_cart"})
        if i < 180:
            data.append({"session_id": sid, "event_name": "begin_checkout"})
        if i < 100:
            data.append({"session_id": sid, "event_name": "purchase"})
    return pd.DataFrame(data)


@pytest.fixture
def traffic_sources_df() -> pd.DataFrame:
    return pd.DataFrame({
        "traffic_source": ["google", "direct", "facebook", "email"],
        "traffic_medium": ["organic", "(none)", "cpc", "email"],
        "sessions": [5000, 3000, 2000, 1000],
        "conversions": [200, 90, 80, 50],
        "revenue": [50000.0, 18000.0, 16000.0, 12000.0],
    })


@pytest.fixture
def device_df() -> pd.DataFrame:
    return pd.DataFrame({
        "device_category": ["desktop", "mobile", "tablet"],
        "browser": ["Chrome", "Safari", "Chrome"],
        "os": ["Windows", "iOS", "Android"],
        "sessions": [5000, 4000, 1000],
        "users": [3000, 2500, 700],
        "pages_per_session": [4.2, 2.8, 3.5],
        "avg_session_duration": [320.0, 180.0, 250.0],
    })


@pytest.fixture
def page_engagement_df() -> pd.DataFrame:
    return pd.DataFrame({
        "page_path": ["/home", "/product/1", "/category/shoes", "/cart", "/checkout"],
        "pageviews": [10000, 5000, 3000, 2000, 1500],
        "unique_pageviews": [8000, 4000, 2500, 1800, 1400],
        "avg_time_on_page": [15.0, 45.0, 30.0, 60.0, 90.0],
        "avg_scroll_depth": [0.3, 0.7, 0.5, 0.8, 0.9],
        "exit_rate": [0.4, 0.2, 0.3, 0.15, 0.1],
    })


# ── Orders fixtures ──────────────────────────────────────

@pytest.fixture
def orders_kpi_df() -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2025-01-01", periods=90, freq="D")
    rows = []
    for d in dates:
        n_orders = np.random.randint(50, 150)
        for _ in range(n_orders):
            rows.append({
                "order_date": d,
                "order_id": f"ord_{len(rows):06d}",
                "user_id": f"u_{np.random.randint(0, 5000):05d}",
                "session_id": f"s_{np.random.randint(0, 10000):06d}",
                "order_total": round(np.random.lognormal(3.5, 0.8), 2),
                "net_revenue": round(np.random.lognormal(3.3, 0.8), 2),
                "units": np.random.randint(1, 5),
            })
    return pd.DataFrame(rows)


@pytest.fixture
def cohort_df() -> pd.DataFrame:
    """Cohort analysis fixture: user_id, cohort_month, order_month, revenue."""
    np.random.seed(42)
    rows = []
    cohorts = pd.date_range("2024-07-01", periods=6, freq="MS")
    for cohort in cohorts:
        n_users = np.random.randint(200, 500)
        for u in range(n_users):
            uid = f"u_{cohort.strftime('%Y%m')}_{u:04d}"
            # Each user may order in subsequent months with decaying probability
            for month_offset in range(6):
                if np.random.random() < 0.5 * (0.7 ** month_offset):
                    order_month = cohort + pd.DateOffset(months=month_offset)
                    rows.append({
                        "user_id": uid,
                        "cohort_month": cohort,
                        "order_month": order_month,
                        "revenue": round(np.random.lognormal(3.5, 0.8), 2),
                    })
    return pd.DataFrame(rows)


@pytest.fixture
def product_df() -> pd.DataFrame:
    np.random.seed(42)
    products = [f"prod_{i:03d}" for i in range(50)]
    categories = ["Shoes", "Clothing", "Accessories", "Electronics", "Home"]
    return pd.DataFrame({
        "product_id": products,
        "category_l1": [np.random.choice(categories) for _ in products],
        "revenue": np.random.lognormal(7, 1.5, 50).round(2),
        "units_sold": np.random.randint(10, 500, 50),
        "return_rate": np.random.uniform(0.02, 0.15, 50).round(4),
        "margin": np.random.uniform(0.1, 0.6, 50).round(3),
    })


@pytest.fixture
def daily_revenue_df() -> pd.DataFrame:
    """Daily revenue for time series decomposition."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=365, freq="D")
    trend = np.linspace(10000, 15000, 365)
    seasonal = 2000 * np.sin(2 * np.pi * np.arange(365) / 7)
    noise = np.random.normal(0, 500, 365)
    return pd.DataFrame({
        "date": dates,
        "revenue": (trend + seasonal + noise).round(2),
    })


# ── Recommendation fixtures ──────────────────────────────

@pytest.fixture
def rec_engagement_df() -> pd.DataFrame:
    widgets = ["homepage_recs", "pdp_similar", "cart_upsell", "email_recs"]
    algorithms = ["collaborative", "content_based", "hybrid", "popular"]
    rows = []
    np.random.seed(42)
    for w, a in zip(widgets, algorithms):
        impressions = np.random.randint(5000, 20000)
        clicks = int(impressions * np.random.uniform(0.02, 0.08))
        atc = int(clicks * np.random.uniform(0.1, 0.3))
        purchases = int(atc * np.random.uniform(0.2, 0.5))
        rows.append({
            "widget_id": w,
            "algorithm": a,
            "impressions": impressions,
            "clicks": clicks,
            "add_to_carts": atc,
            "purchases": purchases,
            "revenue": round(purchases * np.random.uniform(30, 80), 2),
        })
    return pd.DataFrame(rows)


@pytest.fixture
def rec_product_df() -> pd.DataFrame:
    """Products shown in recommendations for coverage/diversity analysis."""
    np.random.seed(42)
    n_products = 200
    return pd.DataFrame({
        "product_id": [f"prod_{i:04d}" for i in range(n_products)],
        "times_recommended": np.random.zipf(1.5, n_products).clip(max=500),
        "times_clicked": np.random.zipf(1.3, n_products).clip(max=100),
        "is_new_item": np.random.choice([True, False], n_products, p=[0.2, 0.8]),
    })


# ── A/B test fixtures ────────────────────────────────────

@pytest.fixture
def ab_conversion_data() -> dict:
    """Known conversion data for A/B test validation."""
    return {
        "control_conversions": 500,
        "control_total": 10000,
        "treatment_conversions": 550,
        "treatment_total": 10000,
    }


@pytest.fixture
def ab_revenue_data() -> dict:
    """Known revenue data for A/B test."""
    np.random.seed(42)
    return {
        "control_values": np.random.normal(50, 15, 5000),
        "treatment_values": np.random.normal(52, 15, 5000),
    }


@pytest.fixture
def ab_assignment_df() -> pd.DataFrame:
    """A/B test assignment data for SRM check."""
    np.random.seed(42)
    n = 20000
    return pd.DataFrame({
        "user_id": [f"u_{i:06d}" for i in range(n)],
        "variant": np.random.choice(["control", "treatment"], n, p=[0.5, 0.5]),
        "device": np.random.choice(["desktop", "mobile", "tablet"], n, p=[0.5, 0.4, 0.1]),
        "traffic_source": np.random.choice(["google", "direct", "facebook"], n, p=[0.5, 0.3, 0.2]),
        "user_type": np.random.choice(["new", "returning"], n, p=[0.4, 0.6]),
    })


@pytest.fixture
def ab_metrics_df() -> pd.DataFrame:
    """A/B test metrics data with pre-experiment data for CUPED."""
    np.random.seed(42)
    n = 10000
    pre_revenue = np.random.lognormal(3, 1, n)
    treatment_effect = np.where(np.arange(n) < n // 2, 0, 3)  # first half = control
    post_revenue = pre_revenue * 0.6 + np.random.lognormal(3, 0.8, n) + treatment_effect
    return pd.DataFrame({
        "user_id": [f"u_{i:06d}" for i in range(n)],
        "variant": ["control"] * (n // 2) + ["treatment"] * (n // 2),
        "converted": np.random.binomial(1, np.where(np.arange(n) < n // 2, 0.05, 0.055), n),
        "revenue": post_revenue.round(2),
        "pre_experiment_revenue": pre_revenue.round(2),
        "metric_date": pd.date_range("2025-01-15", periods=n, freq="h"),
    })


@pytest.fixture
def sequential_data() -> dict:
    """Data for sequential testing."""
    return {
        "max_sample_size": 20000,
        "current_sample_size": 10000,
        "n_looks": 3,
        "max_looks": 5,
        "alpha": 0.05,
        "z_stat": 2.1,
    }
