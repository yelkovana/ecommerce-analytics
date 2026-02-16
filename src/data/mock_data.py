"""Mock data generator for demo mode — no BigQuery needed."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _seed():
    return np.random.default_rng(42)


def mock_session_metrics(**kwargs) -> pd.DataFrame:
    segment = kwargs.get("segment")
    if segment:
        segments = {
            "device_category": ["desktop", "mobile", "tablet"],
            "traffic_source": ["google", "direct", "facebook", "email"],
            "traffic_medium": ["organic", "(none)", "cpc", "email"],
        }.get(segment, ["A", "B", "C"])
        rows = []
        rng = _seed()
        for s in segments:
            rows.append({
                "segment": s,
                "sessions": int(rng.integers(1000, 10000)),
                "users": int(rng.integers(800, 8000)),
                "pages_per_session": round(rng.uniform(2, 5), 2),
                "avg_session_duration": round(rng.uniform(60, 400), 1),
                "bounce_rate": round(rng.uniform(0.2, 0.6), 4),
            })
        return pd.DataFrame(rows)
    return pd.DataFrame([{
        "sessions": 45678,
        "users": 32100,
        "pages_per_session": 3.8,
        "avg_session_duration": 245.0,
        "bounce_rate": 0.385,
    }])


def mock_funnel(**kwargs) -> pd.DataFrame:
    steps = kwargs.get("funnel_steps", ["page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"])
    counts = [10000, 6000, 3000, 1800, 1000]
    rows = []
    for step, count in zip(steps, counts[:len(steps)]):
        for i in range(count):
            rows.append({"session_id": f"s_{len(rows):06d}", "event_name": step})
    # Build proper funnel: sessions flow through multiple steps
    rows = []
    for i in range(counts[0]):
        sid = f"s_{i:06d}"
        for j, (step, c) in enumerate(zip(steps, counts[:len(steps)])):
            if i < c:
                rows.append({"session_id": sid, "event_name": step})
    return pd.DataFrame(rows)


def mock_traffic_sources(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "traffic_source": ["google", "direct", "facebook", "email", "bing", "twitter", "instagram", "referral"],
        "traffic_medium": ["organic", "(none)", "cpc", "email", "organic", "social", "social", "referral"],
        "sessions": [15200, 9800, 6500, 3200, 2100, 1800, 1500, 900],
        "conversions": [760, 392, 260, 192, 84, 54, 45, 36],
        "revenue": [152000, 78400, 52000, 38400, 16800, 10800, 9000, 7200],
    })


def mock_device_segmentation(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "device_category": ["desktop", "desktop", "mobile", "mobile", "mobile", "tablet"],
        "browser": ["Chrome", "Safari", "Safari", "Chrome", "Samsung Internet", "Safari"],
        "os": ["Windows", "macOS", "iOS", "Android", "Android", "iPadOS"],
        "sessions": [12000, 5000, 10000, 8000, 2000, 3000],
        "users": [8000, 3500, 7000, 5500, 1400, 2100],
        "pages_per_session": [4.2, 4.5, 2.8, 2.6, 2.3, 3.5],
        "avg_session_duration": [320.0, 340.0, 180.0, 170.0, 150.0, 250.0],
    })


def mock_page_engagement(**kwargs) -> pd.DataFrame:
    pages = ["/home", "/category/shoes", "/category/clothing", "/product/nike-air-max",
             "/product/adidas-ultra", "/product/levis-501", "/cart", "/checkout",
             "/checkout/payment", "/order-confirmation", "/about", "/contact",
             "/search", "/account", "/wishlist"]
    rng = _seed()
    n = min(int(kwargs.get("limit", 50)), len(pages))
    return pd.DataFrame({
        "page_path": pages[:n],
        "pageviews": [int(x) for x in rng.integers(500, 15000, n)],
        "unique_pageviews": [int(x) for x in rng.integers(400, 12000, n)],
        "avg_time_on_page": [round(x, 1) for x in rng.uniform(10, 120, n)],
        "avg_scroll_depth": [round(x, 2) for x in rng.uniform(0.2, 0.95, n)],
        "exit_rate": [round(x, 3) for x in rng.uniform(0.05, 0.5, n)],
    })


def mock_revenue_kpis(**kwargs) -> pd.DataFrame:
    return pd.DataFrame([{
        "order_count": 8523,
        "unique_customers": 6891,
        "gmv": 1234567.89,
        "net_revenue": 1111111.00,
        "aov": 144.85,
        "units_sold": 24567,
    }])


def mock_daily_revenue(**kwargs) -> pd.DataFrame:
    rng = _seed()
    start = pd.to_datetime(kwargs.get("start_date", "2025-12-01"))
    end = pd.to_datetime(kwargs.get("end_date", "2025-12-31"))
    dates = pd.date_range(start, end, freq="D")
    n = len(dates)
    trend = np.linspace(35000, 42000, n)
    seasonal = 3000 * np.sin(2 * np.pi * np.arange(n) / 7)
    noise = rng.normal(0, 1500, n)
    revenue = (trend + seasonal + noise).clip(min=5000)
    return pd.DataFrame({
        "date": dates,
        "orders": [int(x) for x in (revenue / 145 + rng.normal(0, 10, n)).clip(min=50)],
        "revenue": [round(x, 2) for x in revenue],
        "aov": [round(x, 2) for x in (revenue / (revenue / 145 + rng.normal(0, 10, n)).clip(min=50))],
    })


def mock_cohort(**kwargs) -> pd.DataFrame:
    rng = _seed()
    rows = []
    cohorts = pd.date_range("2025-07-01", periods=6, freq="MS")
    for cohort in cohorts:
        n_users = int(rng.integers(200, 500))
        for u in range(n_users):
            uid = f"u_{cohort.strftime('%Y%m')}_{u:04d}"
            for month_offset in range(6):
                if rng.random() < 0.5 * (0.7 ** month_offset):
                    order_month = cohort + pd.DateOffset(months=month_offset)
                    rows.append({
                        "user_id": uid,
                        "cohort_month": cohort,
                        "order_month": order_month,
                        "revenue": round(float(rng.lognormal(3.5, 0.8)), 2),
                    })
    return pd.DataFrame(rows)


def mock_product_performance(**kwargs) -> pd.DataFrame:
    rng = _seed()
    n = int(kwargs.get("limit", 50))
    categories = ["Shoes", "Clothing", "Accessories", "Electronics", "Home & Living"]
    products = [f"SKU-{i:04d}" for i in range(n)]
    names = [f"Product {i+1}" for i in range(n)]
    return pd.DataFrame({
        "product_id": products,
        "product_name": names,
        "category_l1": [categories[i % len(categories)] for i in range(n)],
        "category_l2": [f"Sub-{(i % 15) + 1}" for i in range(n)],
        "revenue": [round(x, 2) for x in sorted(rng.lognormal(8, 1.5, n), reverse=True)],
        "units_sold": [int(x) for x in sorted(rng.integers(10, 800, n), reverse=True)],
        "return_rate": [round(x, 4) for x in rng.uniform(0.02, 0.12, n)],
        "margin": [round(x, 3) for x in rng.uniform(0.15, 0.55, n)],
    })


def mock_category_performance(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "category_l1": ["Shoes", "Shoes", "Clothing", "Clothing", "Accessories", "Electronics", "Home & Living"],
        "category_l2": ["Sneakers", "Boots", "T-Shirts", "Jeans", "Bags", "Headphones", "Candles"],
        "revenue": [320000, 180000, 250000, 200000, 120000, 95000, 70000],
        "units_sold": [4200, 1800, 5500, 2800, 3200, 950, 1800],
        "order_count": [3800, 1600, 5000, 2500, 2900, 900, 1600],
        "unique_customers": [3200, 1400, 4200, 2100, 2500, 800, 1400],
    })


def mock_rec_engagement(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "widget_id": ["homepage_recs", "pdp_similar", "cart_upsell", "email_recs"],
        "algorithm": ["collaborative", "content_based", "hybrid", "popular"],
        "impressions": [185000, 142000, 68000, 95000],
        "clicks": [9250, 8520, 4760, 3800],
        "add_to_carts": [1850, 2130, 1428, 760],
        "purchases": [740, 852, 571, 304],
    })


def mock_rec_revenue_impact(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "interacted_with_recs": [0, 1],
        "sessions": [32000, 8500],
        "revenue": [640000, 340000],
        "avg_revenue_per_session": [20.0, 40.0],
        "aov": [52.0, 68.0],
        "orders": [6400, 3400],
    })


def mock_rec_widget_comparison(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "widget_id": ["homepage_recs", "pdp_similar", "cart_upsell", "email_recs"],
        "impressions": [185000, 142000, 68000, 95000],
        "clicks": [9250, 8520, 4760, 3800],
        "add_to_carts": [1850, 2130, 1428, 760],
        "purchases": [740, 852, 571, 304],
        "unique_sessions": [45000, 38000, 18000, 25000],
        "click_sessions": [8200, 7500, 4200, 3400],
    })


def mock_rec_algorithm_comparison(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "algorithm": ["collaborative", "content_based", "hybrid", "popular"],
        "widget_id": ["homepage_recs", "pdp_similar", "cart_upsell", "email_recs"],
        "impressions": [185000, 142000, 68000, 95000],
        "clicks": [9250, 8520, 4760, 3800],
        "purchases": [740, 852, 571, 304],
        "unique_products_shown": [4200, 3800, 2100, 1200],
    })


def mock_rec_coverage(**kwargs) -> pd.DataFrame:
    rng = _seed()
    n = 2500
    return pd.DataFrame({
        "product_id": [f"prod_{i:04d}" for i in range(n)],
        "times_recommended": [int(x) for x in rng.zipf(1.5, n).clip(max=500)],
        "times_clicked": [int(x) for x in rng.zipf(1.3, n).clip(max=100)],
        "is_new_item": [bool(x) for x in rng.choice([True, False], n, p=[0.15, 0.85])],
    })


def mock_rec_cold_start(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "is_new_user": [True, True, False, False],
        "is_new_item": [True, False, True, False],
        "impressions": [12000, 35000, 18000, 125000],
        "clicks": [240, 1400, 540, 7500],
        "purchases": [24, 210, 72, 1875],
    })


def mock_ab_test_list(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "test_id": ["test_001", "test_002", "test_003"],
        "test_name": ["Checkout Redesign", "New Rec Algorithm", "Free Shipping Banner"],
        "start_date": pd.to_datetime(["2025-12-01", "2025-12-08", "2025-12-15"]),
        "end_date": pd.to_datetime(["2025-12-28", "2026-01-05", "2026-01-12"]),
        "status": ["active", "active", "active"],
        "hypothesis": [
            "Simplified checkout increases conversion",
            "Hybrid algorithm improves recommendation CTR",
            "Free shipping banner increases AOV",
        ],
        "primary_metric": ["conversion_rate", "ctr", "aov"],
        "allocation_ratio": [0.5, 0.5, 0.5],
    })


def mock_ab_assignments(**kwargs) -> pd.DataFrame:
    rng = _seed()
    n = 20000
    return pd.DataFrame({
        "user_id": [f"u_{i:06d}" for i in range(n)],
        "variant": [str(x) for x in rng.choice(["control", "treatment"], n)],
        "device": [str(x) for x in rng.choice(["desktop", "mobile", "tablet"], n, p=[0.5, 0.4, 0.1])],
        "traffic_source": [str(x) for x in rng.choice(["google", "direct", "facebook"], n, p=[0.5, 0.3, 0.2])],
        "user_type": [str(x) for x in rng.choice(["new", "returning"], n, p=[0.4, 0.6])],
    })


def mock_ab_summary(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "variant": ["control", "treatment"],
        "users": [10050, 9950],
        "conversions": [502, 547],
        "conversion_rate": [0.04995, 0.05497],
        "total_revenue": [251000.0, 285000.0],
        "avg_revenue": [24.98, 28.64],
        "std_revenue": [45.2, 48.7],
    })


def mock_ab_metrics(**kwargs) -> pd.DataFrame:
    rng = _seed()
    n = 20000
    pre_rev = rng.lognormal(3, 1, n)
    variant = np.array(["control"] * (n // 2) + ["treatment"] * (n // 2))
    effect = np.where(variant == "treatment", 3.0, 0.0)
    post_rev = pre_rev * 0.5 + rng.lognormal(3, 0.8, n) + effect
    converted = rng.binomial(1, np.where(variant == "control", 0.05, 0.055), n)
    return pd.DataFrame({
        "user_id": [f"u_{i:06d}" for i in range(n)],
        "variant": variant.tolist(),
        "metric_date": list(pd.date_range("2025-12-01", periods=n, freq="h")),
        "converted": converted.tolist(),
        "revenue": [round(float(x), 2) for x in post_rev],
        "pre_experiment_revenue": [round(float(x), 2) for x in pre_rev],
        "pre_experiment_sessions": [int(x) for x in rng.integers(1, 20, n)],
    })


def mock_ab_daily_metrics(**kwargs) -> pd.DataFrame:
    rng = _seed()
    dates = pd.date_range("2025-12-01", periods=28, freq="D")
    rows = []
    for d in dates:
        for v in ["control", "treatment"]:
            base_rate = 0.05 if v == "control" else 0.055
            rows.append({
                "variant": v,
                "metric_date": d,
                "users": int(rng.integers(300, 400)),
                "conversions": int(rng.binomial(350, base_rate)),
                "conversion_rate": round(float(rng.normal(base_rate, 0.005)), 5),
                "total_revenue": round(float(rng.normal(9000 if v == "control" else 10200, 800)), 2),
                "avg_revenue": round(float(rng.normal(25 if v == "control" else 29, 3)), 2),
            })
    return pd.DataFrame(rows)


def mock_ab_segment_metrics(**kwargs) -> pd.DataFrame:
    dim = kwargs.get("segment_dimension", "device")
    segments = {
        "device": ["desktop", "mobile", "tablet"],
        "traffic_source": ["google", "direct", "facebook"],
        "user_type": ["new", "returning"],
    }.get(dim, ["A", "B", "C"])

    rng = _seed()
    rows = []
    for seg in segments:
        for v in ["control", "treatment"]:
            users = int(rng.integers(1000, 5000))
            rate = float(rng.uniform(0.03, 0.07))
            convs = int(users * rate)
            rows.append({
                "segment": seg,
                "variant": v,
                "users": users,
                "conversions": convs,
                "conversion_rate": round(rate, 5),
                "avg_revenue": round(float(rng.normal(27, 5)), 2),
            })
    return pd.DataFrame(rows)


# ── Router ────────────────────────────────────────────────

MOCK_HANDLERS = {
    ("clickstream.sql", "session_metrics"): mock_session_metrics,
    ("clickstream.sql", "funnel"): mock_funnel,
    ("clickstream.sql", "traffic_sources_with_conversions"): mock_traffic_sources,
    ("clickstream.sql", "traffic_sources"): mock_traffic_sources,
    ("clickstream.sql", "device_segmentation"): mock_device_segmentation,
    ("clickstream.sql", "page_engagement"): mock_page_engagement,
    ("orders.sql", "revenue_kpis"): mock_revenue_kpis,
    ("orders.sql", "daily_revenue"): mock_daily_revenue,
    ("orders.sql", "cohort"): mock_cohort,
    ("orders.sql", "product_performance"): mock_product_performance,
    ("orders.sql", "category_performance"): mock_category_performance,
    ("recommendations.sql", "engagement_metrics"): mock_rec_engagement,
    ("recommendations.sql", "revenue_impact"): mock_rec_revenue_impact,
    ("recommendations.sql", "widget_comparison"): mock_rec_widget_comparison,
    ("recommendations.sql", "algorithm_comparison"): mock_rec_algorithm_comparison,
    ("recommendations.sql", "coverage_diversity"): mock_rec_coverage,
    ("recommendations.sql", "cold_start"): mock_rec_cold_start,
    ("ab_tests.sql", "test_list"): mock_ab_test_list,
    ("ab_tests.sql", "test_assignments"): mock_ab_assignments,
    ("ab_tests.sql", "test_summary"): mock_ab_summary,
    ("ab_tests.sql", "test_metrics"): mock_ab_metrics,
    ("ab_tests.sql", "daily_metrics"): mock_ab_daily_metrics,
    ("ab_tests.sql", "segment_metrics"): mock_ab_segment_metrics,
}


def get_mock_data(template_name: str, **kwargs) -> pd.DataFrame:
    """Route a query to the appropriate mock data generator."""
    query_type = kwargs.get("query_type", "")
    handler = MOCK_HANDLERS.get((template_name, query_type))
    if handler:
        return handler(**kwargs)
    return pd.DataFrame()
