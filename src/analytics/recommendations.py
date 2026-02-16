"""Recommendation Engine analysis — pure functions operating on DataFrames."""

from __future__ import annotations

import numpy as np
import pandas as pd


class RecommendationAnalyzer:
    """Stateless analyzer for recommendation system data."""

    def engagement_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute CTR, conversion rate, ATC rate per widget/algorithm.

        Expects columns: widget_id, algorithm, impressions, clicks, add_to_carts, purchases.
        """
        result = df.copy()
        result["ctr"] = np.where(result["impressions"] > 0, result["clicks"] / result["impressions"], 0)
        result["atc_rate"] = np.where(result["clicks"] > 0, result["add_to_carts"] / result["clicks"], 0)
        result["conversion_rate"] = np.where(
            result["impressions"] > 0, result["purchases"] / result["impressions"], 0
        )
        result["click_to_purchase"] = np.where(
            result["clicks"] > 0, result["purchases"] / result["clicks"], 0
        )
        return result

    def revenue_impact(self, df: pd.DataFrame) -> dict:
        """Compare revenue metrics between rec-interacted vs non-interacted sessions.

        Expects columns: interacted_with_recs, sessions, revenue, avg_revenue_per_session, aov, orders.
        """
        rec = df[df["interacted_with_recs"] == 1].iloc[0] if len(df[df["interacted_with_recs"] == 1]) > 0 else None
        no_rec = df[df["interacted_with_recs"] == 0].iloc[0] if len(df[df["interacted_with_recs"] == 0]) > 0 else None

        result = {"rec_interacted": {}, "non_interacted": {}, "lift": {}}
        if rec is not None:
            result["rec_interacted"] = {
                "sessions": int(rec["sessions"]),
                "revenue": float(rec["revenue"]),
                "avg_revenue_per_session": float(rec["avg_revenue_per_session"]),
                "aov": float(rec["aov"]),
            }
        if no_rec is not None:
            result["non_interacted"] = {
                "sessions": int(no_rec["sessions"]),
                "revenue": float(no_rec["revenue"]),
                "avg_revenue_per_session": float(no_rec["avg_revenue_per_session"]),
                "aov": float(no_rec["aov"]),
            }
        if rec is not None and no_rec is not None and no_rec["avg_revenue_per_session"] > 0:
            result["lift"] = {
                "revenue_per_session_lift": round(
                    (rec["avg_revenue_per_session"] - no_rec["avg_revenue_per_session"])
                    / no_rec["avg_revenue_per_session"], 4
                ),
                "aov_lift": round(
                    (rec["aov"] - no_rec["aov"]) / no_rec["aov"], 4
                ) if no_rec["aov"] > 0 else 0,
            }
        return result

    def engagement_depth(self, df: pd.DataFrame) -> pd.DataFrame:
        """Session-level engagement depth for rec-interacted sessions.

        Expects columns: widget_id, unique_sessions, click_sessions, impressions, clicks.
        """
        result = df.copy()
        result["session_ctr"] = np.where(
            result["unique_sessions"] > 0,
            result["click_sessions"] / result["unique_sessions"],
            0,
        )
        result["clicks_per_session"] = np.where(
            result["click_sessions"] > 0,
            result["clicks"] / result["click_sessions"],
            0,
        )
        return result

    def widget_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """Cross-widget performance matrix.

        Expects columns: widget_id, impressions, clicks, add_to_carts, purchases.
        """
        result = self.engagement_metrics(df)
        # Normalize each metric to [0, 1] for comparison
        for col in ["ctr", "atc_rate", "conversion_rate"]:
            max_val = result[col].max()
            result[f"{col}_normalized"] = np.where(max_val > 0, result[col] / max_val, 0)
        return result

    def algorithm_comparison(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compare algorithms with CTR and conversion stats.

        Expects columns: algorithm, impressions, clicks, purchases, unique_products_shown (optional).
        """
        result = df.copy()
        result["ctr"] = np.where(result["impressions"] > 0, result["clicks"] / result["impressions"], 0)
        result["conversion_rate"] = np.where(
            result["impressions"] > 0, result["purchases"] / result["impressions"], 0
        )
        return result

    def coverage_diversity(
        self,
        rec_products_df: pd.DataFrame,
        total_catalog_size: int,
    ) -> dict:
        """Compute catalog coverage, Gini coefficient, long-tail ratio.

        Expects columns: product_id, times_recommended, times_clicked, is_new_item.
        """
        n_recommended = rec_products_df["product_id"].nunique()
        coverage = n_recommended / total_catalog_size if total_catalog_size > 0 else 0

        # Gini coefficient of recommendation frequency
        freq = np.sort(rec_products_df["times_recommended"].values).astype(float)
        n = len(freq)
        if n > 0 and freq.sum() > 0:
            index = np.arange(1, n + 1)
            gini = (2 * np.sum(index * freq) - (n + 1) * np.sum(freq)) / (n * np.sum(freq))
        else:
            gini = 0

        # Long-tail ratio: % of products below median recommendation count
        median_count = np.median(freq) if n > 0 else 0
        long_tail_ratio = (freq <= median_count).mean() if n > 0 else 0

        # New item coverage
        new_items = rec_products_df[rec_products_df["is_new_item"] == True]
        new_item_share = len(new_items) / n_recommended if n_recommended > 0 else 0

        return {
            "catalog_coverage": round(coverage, 4),
            "products_recommended": n_recommended,
            "total_catalog_size": total_catalog_size,
            "gini_coefficient": round(gini, 4),
            "long_tail_ratio": round(long_tail_ratio, 4),
            "new_item_share": round(new_item_share, 4),
        }

    def cold_start_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze performance for new users and new items separately.

        Expects columns: is_new_user, is_new_item, impressions, clicks, purchases.
        """
        result = df.copy()
        result["ctr"] = np.where(result["impressions"] > 0, result["clicks"] / result["impressions"], 0)
        result["conversion_rate"] = np.where(
            result["impressions"] > 0, result["purchases"] / result["impressions"], 0
        )
        return result
