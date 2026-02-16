"""Clickstream analysis — pure functions operating on DataFrames."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


class ClickstreamAnalyzer:
    """Stateless analyzer: receives DataFrames, returns analysis results."""

    def session_metrics(
        self,
        df: pd.DataFrame,
        segment: Optional[str] = None,
    ) -> pd.DataFrame:
        """Compute session-level metrics, optionally segmented.

        Expects columns: session_id, user_id, pages_per_session | page_path,
                         session_duration | time_on_page, and optionally segment column.
        Returns: sessions, users, pages_per_session, avg_duration, bounce_rate.
        """
        if segment and segment in df.columns:
            groups = df.groupby(segment)
        else:
            df = df.copy()
            df["_all"] = "All"
            groups = df.groupby("_all")

        results = []
        for name, group in groups:
            session_agg = group.groupby("session_id").agg(
                pages=("page_path", "count") if "page_path" in group.columns else ("pages_per_session", "first"),
                duration=("time_on_page", "sum") if "time_on_page" in group.columns else ("session_duration", "first"),
                user_id=("user_id", "first"),
            )
            sessions = len(session_agg)
            users = session_agg["user_id"].nunique()
            pages_per_session = session_agg["pages"].mean()
            avg_duration = session_agg["duration"].mean()
            bounce_rate = (session_agg["pages"] == 1).mean()

            results.append({
                "segment": name,
                "sessions": sessions,
                "users": users,
                "pages_per_session": round(pages_per_session, 2),
                "avg_session_duration": round(avg_duration, 1),
                "bounce_rate": round(bounce_rate, 4),
            })

        result_df = pd.DataFrame(results)
        if segment is None or segment not in df.columns:
            result_df = result_df.drop(columns=["segment"])
        return result_df

    def funnel_analysis(
        self,
        df: pd.DataFrame,
        steps: list[str],
    ) -> pd.DataFrame:
        """Compute funnel drop-off analysis.

        Expects columns: session_id, event_name.
        Returns: step, sessions, drop_off_rate, conversion_from_start.
        """
        step_counts = []
        for step in steps:
            count = df[df["event_name"] == step]["session_id"].nunique()
            step_counts.append(count)

        results = []
        for i, (step, count) in enumerate(zip(steps, step_counts)):
            prev_count = step_counts[i - 1] if i > 0 else count
            drop_off = 1 - (count / prev_count) if prev_count > 0 else 0
            conv_from_start = count / step_counts[0] if step_counts[0] > 0 else 0

            results.append({
                "step": step,
                "sessions": count,
                "drop_off_rate": round(drop_off, 4),
                "conversion_from_start": round(conv_from_start, 4),
            })

        return pd.DataFrame(results)

    def traffic_source_breakdown(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Break down metrics by traffic source/medium.

        Expects columns: traffic_source, traffic_medium, sessions, conversions, revenue.
        Returns the same DataFrame enriched with conversion_rate.
        """
        result = df.copy()
        if "conversions" in result.columns and "sessions" in result.columns:
            result["conversion_rate"] = np.where(
                result["sessions"] > 0,
                result["conversions"] / result["sessions"],
                0,
            )
        if "revenue" in result.columns and "sessions" in result.columns:
            result["revenue_per_session"] = np.where(
                result["sessions"] > 0,
                result["revenue"] / result["sessions"],
                0,
            )
        return result

    def device_segmentation(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Device / browser / OS breakdown.

        Expects columns: device_category, browser, os, sessions, users,
                         pages_per_session, avg_session_duration.
        Returns the input enriched with session_share.
        """
        result = df.copy()
        total = result["sessions"].sum()
        result["session_share"] = np.where(total > 0, result["sessions"] / total, 0)
        return result.sort_values("sessions", ascending=False)

    def page_engagement(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Page-level engagement metrics.

        Expects columns: page_path, pageviews, unique_pageviews,
                         avg_time_on_page, avg_scroll_depth, exit_rate.
        Returns the input enriched with engagement_score.
        """
        result = df.copy()
        # Composite engagement score: normalized time × scroll depth × (1 - exit_rate)
        max_time = result["avg_time_on_page"].max()
        if max_time > 0:
            norm_time = result["avg_time_on_page"] / max_time
        else:
            norm_time = 0

        scroll = result["avg_scroll_depth"] if "avg_scroll_depth" in result.columns else 0.5
        exit_penalty = 1 - result["exit_rate"].fillna(0)

        result["engagement_score"] = (norm_time * 0.4 + scroll * 0.3 + exit_penalty * 0.3).round(3)
        return result.sort_values("engagement_score", ascending=False)
