"""Realistic mock data generator for demo mode.

Simulates a mid-size fashion e-commerce site (~$1.2M/month GMV)
with seasonal patterns, realistic product names, and correlated metrics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

# ── Realistic product catalog ─────────────────────────────

PRODUCTS = [
    ("Nike Air Max 90", "Shoes", "Sneakers", 129.99),
    ("Adidas Ultraboost 22", "Shoes", "Running", 189.99),
    ("New Balance 574", "Shoes", "Sneakers", 89.99),
    ("Converse Chuck 70", "Shoes", "Casual", 85.00),
    ("Dr. Martens 1460", "Shoes", "Boots", 169.99),
    ("Vans Old Skool", "Shoes", "Casual", 69.99),
    ("Timberland 6-Inch", "Shoes", "Boots", 198.00),
    ("Levi's 501 Original", "Clothing", "Jeans", 79.50),
    ("Levi's 511 Slim", "Clothing", "Jeans", 69.50),
    ("Zara Oversized Blazer", "Clothing", "Outerwear", 119.00),
    ("H&M Basic Tee (3-Pack)", "Clothing", "T-Shirts", 24.99),
    ("Uniqlo Heattech Crew", "Clothing", "T-Shirts", 19.90),
    ("Ralph Lauren Polo", "Clothing", "Polo Shirts", 98.50),
    ("Tommy Hilfiger Hoodie", "Clothing", "Sweatshirts", 89.99),
    ("Calvin Klein Boxer Brief 3pk", "Clothing", "Underwear", 42.50),
    ("North Face Puffer Jacket", "Clothing", "Outerwear", 249.00),
    ("Patagonia Better Sweater", "Clothing", "Fleece", 139.00),
    ("Champion Reverse Weave", "Clothing", "Sweatshirts", 65.00),
    ("Ray-Ban Wayfarer", "Accessories", "Sunglasses", 161.00),
    ("Herschel Little America", "Accessories", "Backpacks", 109.99),
    ("Fjallraven Kanken", "Accessories", "Backpacks", 79.99),
    ("Daniel Wellington Classic", "Accessories", "Watches", 199.00),
    ("Casio G-Shock GA2100", "Accessories", "Watches", 99.99),
    ("Nike Dri-FIT Cap", "Accessories", "Hats", 24.00),
    ("Apple AirPods Pro", "Electronics", "Audio", 249.00),
    ("Sony WH-1000XM5", "Electronics", "Audio", 349.99),
    ("JBL Charge 5", "Electronics", "Speakers", 179.95),
    ("Samsung Galaxy Buds2", "Electronics", "Audio", 149.99),
    ("Anker PowerCore 20000", "Electronics", "Chargers", 45.99),
    ("Yankee Candle Large Jar", "Home & Living", "Candles", 29.50),
    ("IKEA KALLAX Shelf", "Home & Living", "Furniture", 69.99),
    ("Dyson V15 Detect", "Home & Living", "Appliances", 749.99),
]

TRAFFIC_SOURCES = [
    ("google", "organic", 0.28),
    ("google", "cpc", 0.18),
    ("direct", "(none)", 0.16),
    ("facebook", "cpc", 0.10),
    ("instagram", "social", 0.08),
    ("email", "newsletter", 0.06),
    ("bing", "organic", 0.04),
    ("tiktok", "social", 0.03),
    ("youtube", "cpc", 0.03),
    ("twitter", "social", 0.02),
    ("pinterest", "social", 0.01),
    ("referral", "blog", 0.01),
]


def _daily_pattern(n: int) -> np.ndarray:
    """Realistic daily e-commerce pattern: weekday dip, weekend spike, overall growth."""
    days = np.arange(n)
    trend = np.linspace(1.0, 1.08, n)  # 8% growth over period
    # Weekly seasonality: dip Mon-Wed, peak Fri-Sun
    weekly = 1 + 0.15 * np.sin(2 * np.pi * (days - 2) / 7)
    noise = RNG.normal(1, 0.05, n)
    return (trend * weekly * noise).clip(min=0.5)


# ── Clickstream ───────────────────────────────────────────

def mock_session_metrics(**kwargs) -> pd.DataFrame:
    segment = kwargs.get("segment")
    base = {"sessions": 127834, "users": 89245, "pages_per_session": 3.72,
            "avg_session_duration": 234.5, "bounce_rate": 0.3847}

    if segment:
        configs = {
            "device_category": [
                ("desktop", 0.42, 4.3, 285, 0.31),
                ("mobile", 0.45, 2.9, 165, 0.46),
                ("tablet", 0.13, 3.6, 240, 0.35),
            ],
            "traffic_source": [
                ("google", 0.46, 3.8, 220, 0.36),
                ("direct", 0.16, 4.5, 310, 0.28),
                ("facebook", 0.10, 2.6, 130, 0.52),
                ("instagram", 0.08, 2.4, 95, 0.55),
                ("email", 0.06, 5.2, 380, 0.22),
                ("bing", 0.04, 3.5, 200, 0.38),
                ("tiktok", 0.03, 2.1, 75, 0.61),
                ("other", 0.07, 3.2, 180, 0.40),
            ],
            "traffic_medium": [
                ("organic", 0.32, 3.9, 240, 0.34),
                ("cpc", 0.28, 3.2, 175, 0.41),
                ("(none)", 0.16, 4.5, 310, 0.28),
                ("social", 0.12, 2.4, 100, 0.53),
                ("newsletter", 0.06, 5.2, 380, 0.22),
                ("referral", 0.06, 3.0, 160, 0.39),
            ],
        }
        data = configs.get(segment, configs["device_category"])
        rows = []
        for name, share, pps, dur, br in data:
            sess = int(base["sessions"] * share * RNG.uniform(0.95, 1.05))
            rows.append({
                "segment": name,
                "sessions": sess,
                "users": int(sess * RNG.uniform(0.65, 0.75)),
                "pages_per_session": round(pps + RNG.normal(0, 0.1), 2),
                "avg_session_duration": round(dur + RNG.normal(0, 10), 1),
                "bounce_rate": round(br + RNG.normal(0, 0.01), 4),
            })
        return pd.DataFrame(rows)

    return pd.DataFrame([base])


def mock_funnel(**kwargs) -> pd.DataFrame:
    steps = kwargs.get("funnel_steps",
                       ["page_view", "product_view", "add_to_cart", "begin_checkout", "purchase"])
    # Realistic conversion funnel: 100% → 47% → 18% → 11% → 6.2%
    rates = [1.0, 0.47, 0.18, 0.11, 0.062]
    base_sessions = 42500
    rows = []
    for i in range(min(len(steps), len(rates))):
        count = int(base_sessions * rates[i])
        sid_start = sum(int(base_sessions * rates[j]) for j in range(i))
        for s in range(count):
            sid = f"s_{s:06d}"
            rows.append({"session_id": sid, "event_name": steps[i]})
    # Rebuild so sessions flow through: session 0 hits all steps, session 42499 only page_view
    rows = []
    for s in range(base_sessions):
        sid = f"s_{s:06d}"
        for i, (step, rate) in enumerate(zip(steps, rates[:len(steps)])):
            if s < int(base_sessions * rate):
                rows.append({"session_id": sid, "event_name": step})
    return pd.DataFrame(rows)


def mock_traffic_sources(**kwargs) -> pd.DataFrame:
    total_sessions = 127834
    rows = []
    for source, medium, share in TRAFFIC_SOURCES:
        sess = int(total_sessions * share * RNG.uniform(0.92, 1.08))
        conv_rate = RNG.uniform(0.02, 0.06) if medium != "newsletter" else RNG.uniform(0.06, 0.10)
        convs = int(sess * conv_rate)
        aov = RNG.uniform(85, 165)
        rows.append({
            "traffic_source": source,
            "traffic_medium": medium,
            "sessions": sess,
            "conversions": convs,
            "revenue": round(convs * aov, 2),
        })
    return pd.DataFrame(rows).sort_values("sessions", ascending=False).reset_index(drop=True)


def mock_device_segmentation(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "device_category": ["desktop", "desktop", "desktop", "mobile", "mobile", "mobile", "tablet", "tablet"],
        "browser": ["Chrome", "Safari", "Firefox", "Safari", "Chrome", "Samsung Internet", "Safari", "Chrome"],
        "os": ["Windows", "macOS", "Windows", "iOS", "Android", "Android", "iPadOS", "Android"],
        "sessions": [32450, 14200, 6800, 28900, 21500, 8200, 10800, 4984],
        "users": [21200, 9800, 4900, 20100, 14800, 5700, 7500, 3445],
        "pages_per_session": [4.5, 4.8, 4.1, 2.8, 2.6, 2.3, 3.7, 3.4],
        "avg_session_duration": [310, 335, 280, 165, 155, 130, 250, 225],
    })


def mock_page_engagement(**kwargs) -> pd.DataFrame:
    pages = [
        ("/", 48200, 38500, 12.5, 0.35, 0.28),
        ("/category/shoes", 22100, 18400, 35.2, 0.58, 0.18),
        ("/category/clothing", 19800, 16200, 32.8, 0.55, 0.19),
        ("/product/nike-air-max-90", 8900, 7100, 68.4, 0.78, 0.12),
        ("/product/adidas-ultraboost-22", 7200, 5800, 72.1, 0.82, 0.11),
        ("/product/levis-501-original", 6100, 4900, 55.3, 0.71, 0.14),
        ("/product/north-face-puffer", 5400, 4300, 62.7, 0.76, 0.13),
        ("/product/ray-ban-wayfarer", 4800, 3900, 48.9, 0.68, 0.15),
        ("/search", 15600, 12800, 18.2, 0.42, 0.25),
        ("/cart", 12400, 10200, 85.3, 0.88, 0.08),
        ("/checkout", 7800, 6500, 120.5, 0.92, 0.05),
        ("/checkout/payment", 6200, 5100, 95.2, 0.90, 0.04),
        ("/order-confirmation", 5300, 4800, 22.0, 0.45, 0.65),
        ("/account/orders", 3200, 2800, 42.5, 0.60, 0.35),
        ("/account/wishlist", 2800, 2300, 38.1, 0.55, 0.30),
        ("/about", 1800, 1500, 25.0, 0.48, 0.45),
        ("/contact", 1200, 1000, 32.0, 0.52, 0.40),
        ("/blog/style-guide-2026", 4500, 3800, 180.0, 0.85, 0.22),
        ("/sale", 9200, 7600, 45.0, 0.62, 0.20),
        ("/new-arrivals", 8100, 6700, 40.0, 0.58, 0.21),
    ]
    n = min(int(kwargs.get("limit", 50)), len(pages))
    df = pd.DataFrame(pages[:n], columns=[
        "page_path", "pageviews", "unique_pageviews",
        "avg_time_on_page", "avg_scroll_depth", "exit_rate",
    ])
    return df


# ── Orders ────────────────────────────────────────────────

def mock_revenue_kpis(**kwargs) -> pd.DataFrame:
    return pd.DataFrame([{
        "order_count": 7892,
        "unique_customers": 6234,
        "gmv": 1_187_345.67,
        "net_revenue": 1_068_611.10,
        "aov": 150.45,
        "units_sold": 18_234,
    }])


def mock_daily_revenue(**kwargs) -> pd.DataFrame:
    start = pd.to_datetime(kwargs.get("start_date", "2026-01-17"))
    end = pd.to_datetime(kwargs.get("end_date", "2026-02-16"))
    dates = pd.date_range(start, end, freq="D")
    n = len(dates)

    pattern = _daily_pattern(n)
    base_rev = 38500
    revenue = (base_rev * pattern).round(2)

    orders = (revenue / RNG.uniform(140, 160, n)).astype(int).clip(min=80)
    aov = (revenue / orders).round(2)

    return pd.DataFrame({
        "date": dates,
        "orders": orders.tolist(),
        "revenue": revenue.tolist(),
        "aov": aov.tolist(),
    })


def mock_cohort(**kwargs) -> pd.DataFrame:
    rows = []
    cohorts = pd.date_range("2025-09-01", periods=6, freq="MS")
    retention_curve = [1.0, 0.38, 0.25, 0.18, 0.14, 0.11]

    for cohort in cohorts:
        cohort_size = int(RNG.integers(800, 1500))
        for month_offset in range(6):
            retained = int(cohort_size * retention_curve[month_offset] * RNG.uniform(0.85, 1.15))
            order_month = cohort + pd.DateOffset(months=month_offset)
            for u in range(retained):
                rows.append({
                    "user_id": f"u_{cohort.strftime('%Y%m')}_{u:04d}",
                    "cohort_month": cohort,
                    "order_month": order_month,
                    "revenue": round(float(RNG.lognormal(4.2, 0.7)), 2),
                })
    return pd.DataFrame(rows)


def mock_product_performance(**kwargs) -> pd.DataFrame:
    n = min(int(kwargs.get("limit", 50)), len(PRODUCTS))
    products = PRODUCTS[:n]

    # Zipf-like revenue distribution: top products get much more
    revenue_weights = np.sort(RNG.zipf(1.3, n))[::-1].astype(float)
    revenue_weights = revenue_weights / revenue_weights.sum() * 1_187_345

    rows = []
    for i, (name, cat1, cat2, price) in enumerate(products):
        rev = round(float(revenue_weights[i]), 2)
        units = max(int(rev / price * RNG.uniform(0.8, 1.2)), 1)
        rows.append({
            "product_id": f"SKU-{i+1:04d}",
            "product_name": name,
            "category_l1": cat1,
            "category_l2": cat2,
            "revenue": rev,
            "units_sold": units,
            "return_rate": round(float(RNG.uniform(0.02, 0.12)), 4),
            "margin": round(float(RNG.uniform(0.25, 0.55)), 3),
        })
    return pd.DataFrame(rows)


def mock_category_performance(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "category_l1": ["Shoes", "Shoes", "Shoes", "Clothing", "Clothing", "Clothing",
                        "Accessories", "Accessories", "Electronics", "Electronics", "Home & Living"],
        "category_l2": ["Sneakers", "Boots", "Running", "Jeans", "T-Shirts", "Outerwear",
                        "Sunglasses", "Backpacks", "Audio", "Chargers", "Candles"],
        "revenue": [285000, 142000, 98000, 168000, 95000, 145000,
                    72000, 58000, 89000, 22000, 13345],
        "units_sold": [3200, 1100, 680, 2800, 4500, 850,
                       520, 680, 420, 580, 480],
        "order_count": [2900, 980, 620, 2500, 4100, 780,
                        480, 620, 390, 540, 440],
        "unique_customers": [2400, 850, 540, 2100, 3600, 680,
                             420, 540, 350, 480, 380],
    })


# ── Recommendations ───────────────────────────────────────

def mock_rec_engagement(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "widget_id": ["homepage_top_picks", "pdp_similar_items", "pdp_complete_look",
                      "cart_upsell", "post_purchase_email", "search_recs"],
        "algorithm": ["collaborative_filtering", "content_based", "style_match",
                      "frequently_bought_together", "personalized_digest", "hybrid_search"],
        "impressions": [425000, 312000, 185000, 98000, 145000, 210000],
        "clicks": [21250, 21840, 9250, 6860, 10150, 8400],
        "add_to_carts": [4250, 5460, 2405, 2744, 2030, 1680],
        "purchases": [1700, 2184, 962, 1098, 812, 672],
    })


def mock_rec_revenue_impact(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "interacted_with_recs": [0, 1],
        "sessions": [89200, 38634],
        "revenue": [580000, 607345],
        "avg_revenue_per_session": [6.50, 15.72],
        "aov": [128.50, 168.20],
        "orders": [4512, 3612],
    })


def mock_rec_widget_comparison(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "widget_id": ["homepage_top_picks", "pdp_similar_items", "pdp_complete_look",
                      "cart_upsell", "post_purchase_email", "search_recs"],
        "impressions": [425000, 312000, 185000, 98000, 145000, 210000],
        "clicks": [21250, 21840, 9250, 6860, 10150, 8400],
        "add_to_carts": [4250, 5460, 2405, 2744, 2030, 1680],
        "purchases": [1700, 2184, 962, 1098, 812, 672],
        "unique_sessions": [118000, 86000, 52000, 28000, 40000, 58000],
        "click_sessions": [19500, 19200, 8500, 6200, 9200, 7600],
    })


def mock_rec_algorithm_comparison(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "algorithm": ["collaborative_filtering", "content_based", "style_match",
                      "frequently_bought_together", "personalized_digest", "hybrid_search"],
        "widget_id": ["homepage_top_picks", "pdp_similar_items", "pdp_complete_look",
                      "cart_upsell", "post_purchase_email", "search_recs"],
        "impressions": [425000, 312000, 185000, 98000, 145000, 210000],
        "clicks": [21250, 21840, 9250, 6860, 10150, 8400],
        "purchases": [1700, 2184, 962, 1098, 812, 672],
        "unique_products_shown": [8200, 6500, 4800, 2200, 5100, 7800],
    })


def mock_rec_coverage(**kwargs) -> pd.DataFrame:
    n = 4200  # Out of ~10k catalog
    freq = RNG.zipf(1.4, n).clip(max=800)
    return pd.DataFrame({
        "product_id": [f"SKU-{i+1:04d}" for i in range(n)],
        "times_recommended": [int(x) for x in freq],
        "times_clicked": [int(max(1, x * RNG.uniform(0.03, 0.08))) for x in freq],
        "is_new_item": [bool(x) for x in RNG.choice([True, False], n, p=[0.12, 0.88])],
    })


def mock_rec_cold_start(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "is_new_user": [True, True, False, False],
        "is_new_item": [True, False, True, False],
        "impressions": [18500, 62000, 24000, 270500],
        "clicks": [278, 2480, 600, 16230],
        "purchases": [22, 310, 60, 4055],
    })


# ── A/B Testing ───────────────────────────────────────────

def mock_ab_test_list(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "test_id": ["exp_2026_001", "exp_2026_002", "exp_2026_003"],
        "test_name": [
            "Checkout Flow: Single Page vs Multi-Step",
            "PDP: AI Size Recommender Widget",
            "Free Shipping Threshold: $75 vs $50",
        ],
        "start_date": pd.to_datetime(["2026-01-20", "2026-01-27", "2026-02-03"]),
        "end_date": pd.to_datetime(["2026-02-16", "2026-02-23", "2026-03-02"]),
        "status": ["active", "active", "active"],
        "hypothesis": [
            "Single-page checkout reduces cart abandonment and increases conversion by 8-12%",
            "AI size recommender reduces return rate by 15% and increases purchase confidence",
            "Lowering free shipping threshold from $75 to $50 increases order frequency and GMV",
        ],
        "primary_metric": ["conversion_rate", "return_rate", "aov"],
        "allocation_ratio": [0.5, 0.5, 0.5],
    })


def mock_ab_assignments(**kwargs) -> pd.DataFrame:
    n = 24680
    variants = RNG.choice(["control", "treatment"], n, p=[0.5, 0.5])
    devices = RNG.choice(["desktop", "mobile", "tablet"], n, p=[0.45, 0.43, 0.12])
    sources = RNG.choice(["google", "direct", "facebook", "email", "instagram"], n,
                         p=[0.40, 0.20, 0.18, 0.12, 0.10])
    types = RNG.choice(["new", "returning"], n, p=[0.38, 0.62])
    return pd.DataFrame({
        "user_id": [f"u_{i:06d}" for i in range(n)],
        "variant": [str(x) for x in variants],
        "device": [str(x) for x in devices],
        "traffic_source": [str(x) for x in sources],
        "user_type": [str(x) for x in types],
    })


def mock_ab_summary(**kwargs) -> pd.DataFrame:
    return pd.DataFrame({
        "variant": ["control", "treatment"],
        "users": [12340, 12340],
        "conversions": [617, 691],
        "conversion_rate": [0.05000, 0.05600],
        "total_revenue": [462750.00, 531810.00],
        "avg_revenue": [37.50, 43.10],
        "std_revenue": [62.30, 65.80],
    })


def mock_ab_metrics(**kwargs) -> pd.DataFrame:
    n = 24680
    pre_rev = RNG.lognormal(3.2, 0.9, n)
    variant = np.array(["control"] * (n // 2) + ["treatment"] * (n // 2))
    # Treatment has +12% lift in conversion, +15% lift in revenue
    base_conv = np.where(variant == "control", 0.050, 0.056)
    converted = RNG.binomial(1, base_conv, n)
    revenue_effect = np.where(variant == "treatment", 5.6, 0.0)
    post_rev = (pre_rev * 0.4 + RNG.lognormal(3.4, 0.75, n) + revenue_effect) * converted

    return pd.DataFrame({
        "user_id": [f"u_{i:06d}" for i in range(n)],
        "variant": variant.tolist(),
        "metric_date": list(pd.date_range("2026-01-20", periods=n, freq="52s")),
        "converted": converted.tolist(),
        "revenue": [round(float(x), 2) for x in post_rev],
        "pre_experiment_revenue": [round(float(x), 2) for x in pre_rev],
        "pre_experiment_sessions": [int(x) for x in RNG.integers(1, 25, n)],
    })


def mock_ab_daily_metrics(**kwargs) -> pd.DataFrame:
    dates = pd.date_range("2026-01-20", periods=28, freq="D")
    rows = []
    for d in dates:
        for v in ["control", "treatment"]:
            base_rate = 0.050 if v == "control" else 0.056
            daily_users = int(RNG.integers(380, 480))
            convs = int(RNG.binomial(daily_users, base_rate))
            rev_per_user = 37.50 if v == "control" else 43.10
            rows.append({
                "variant": v,
                "metric_date": d,
                "users": daily_users,
                "conversions": convs,
                "conversion_rate": round(convs / daily_users, 5),
                "total_revenue": round(float(daily_users * rev_per_user * RNG.uniform(0.9, 1.1)), 2),
                "avg_revenue": round(float(RNG.normal(rev_per_user, 4)), 2),
            })
    return pd.DataFrame(rows)


def mock_ab_segment_metrics(**kwargs) -> pd.DataFrame:
    dim = kwargs.get("segment_dimension", "device")
    configs = {
        "device": [
            ("desktop", 4200, 0.058, 0.065, 42.0, 48.5),
            ("mobile", 3800, 0.042, 0.048, 32.0, 37.5),
            ("tablet", 1200, 0.052, 0.058, 38.0, 43.0),
        ],
        "traffic_source": [
            ("google", 4500, 0.048, 0.054, 35.0, 40.5),
            ("direct", 2800, 0.062, 0.070, 48.0, 55.0),
            ("facebook", 2200, 0.038, 0.044, 28.0, 33.0),
        ],
        "user_type": [
            ("new", 4800, 0.035, 0.042, 28.0, 34.0),
            ("returning", 7540, 0.068, 0.074, 52.0, 58.0),
        ],
    }
    data = configs.get(dim, configs["device"])
    rows = []
    for seg, users, ctrl_rate, treat_rate, ctrl_rev, treat_rev in data:
        for v in ["control", "treatment"]:
            rate = ctrl_rate if v == "control" else treat_rate
            rev = ctrl_rev if v == "control" else treat_rev
            u = int(users * RNG.uniform(0.48, 0.52))
            convs = int(u * rate * RNG.uniform(0.95, 1.05))
            rows.append({
                "segment": seg,
                "variant": v,
                "users": u,
                "conversions": convs,
                "conversion_rate": round(convs / u, 5),
                "avg_revenue": round(float(RNG.normal(rev, 3)), 2),
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
