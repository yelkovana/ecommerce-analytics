"""Order & Revenue analysis — pure functions operating on DataFrames."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.seasonal import STL


class OrderAnalyzer:
    """Stateless analyzer for order/revenue data."""

    def revenue_kpis(
        self,
        orders_df: pd.DataFrame,
        sessions_count: Optional[int] = None,
    ) -> dict:
        """Compute core revenue KPIs.

        Expects columns: order_id, user_id, order_total, net_revenue, units (optional).
        """
        gmv = orders_df["order_total"].sum()
        net = orders_df["net_revenue"].sum() if "net_revenue" in orders_df.columns else gmv
        order_count = orders_df["order_id"].nunique()
        aov = gmv / order_count if order_count > 0 else 0
        units = orders_df["units"].sum() if "units" in orders_df.columns else None

        kpis = {
            "gmv": round(gmv, 2),
            "net_revenue": round(net, 2),
            "order_count": order_count,
            "aov": round(aov, 2),
            "unique_customers": orders_df["user_id"].nunique(),
        }
        if units is not None:
            kpis["units_sold"] = int(units)
        if sessions_count and sessions_count > 0:
            kpis["revenue_per_session"] = round(gmv / sessions_count, 2)
            kpis["conversion_rate"] = round(order_count / sessions_count, 4)
        return kpis

    def cohort_analysis(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Build cohort retention matrix.

        Expects columns: user_id, cohort_month, order_month, revenue.
        Returns pivot table: rows=cohort, columns=period_offset, values=retention_rate.
        """
        df = df.copy()
        df["cohort_month"] = pd.to_datetime(df["cohort_month"])
        df["order_month"] = pd.to_datetime(df["order_month"])
        df["period_offset"] = (
            (df["order_month"].dt.year - df["cohort_month"].dt.year) * 12
            + (df["order_month"].dt.month - df["cohort_month"].dt.month)
        )

        cohort_sizes = df.groupby("cohort_month")["user_id"].nunique().rename("cohort_size")
        retention = df.groupby(["cohort_month", "period_offset"])["user_id"].nunique().reset_index()
        retention = retention.merge(cohort_sizes, on="cohort_month")
        retention["retention_rate"] = retention["user_id"] / retention["cohort_size"]

        pivot = retention.pivot(index="cohort_month", columns="period_offset", values="retention_rate")
        return pivot

    def cohort_ltv(self, df: pd.DataFrame) -> pd.DataFrame:
        """Compute cumulative LTV curves per cohort.

        Expects columns: user_id, cohort_month, order_month, revenue.
        """
        df = df.copy()
        df["cohort_month"] = pd.to_datetime(df["cohort_month"])
        df["order_month"] = pd.to_datetime(df["order_month"])
        df["period_offset"] = (
            (df["order_month"].dt.year - df["cohort_month"].dt.year) * 12
            + (df["order_month"].dt.month - df["cohort_month"].dt.month)
        )

        cohort_sizes = df.groupby("cohort_month")["user_id"].nunique()
        rev = df.groupby(["cohort_month", "period_offset"])["revenue"].sum().reset_index()
        rev = rev.sort_values(["cohort_month", "period_offset"])
        rev["cumulative_revenue"] = rev.groupby("cohort_month")["revenue"].cumsum()
        rev["cohort_size"] = rev["cohort_month"].map(cohort_sizes)
        rev["ltv"] = rev["cumulative_revenue"] / rev["cohort_size"]
        return rev

    def product_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rank products by revenue with additional metrics.

        Expects columns: product_id, category_l1, revenue, units_sold, return_rate (optional), margin (optional).
        """
        result = df.copy()
        total_revenue = result["revenue"].sum()
        result["revenue_share"] = np.where(total_revenue > 0, result["revenue"] / total_revenue, 0)
        result["revenue_rank"] = result["revenue"].rank(ascending=False, method="min").astype(int)
        if "units_sold" in result.columns:
            result["avg_price"] = np.where(
                result["units_sold"] > 0,
                result["revenue"] / result["units_sold"],
                0,
            )
        return result.sort_values("revenue", ascending=False)

    def category_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """Hierarchical category aggregation for treemap.

        Expects columns: category_l1, category_l2, revenue, units_sold.
        """
        result = df.copy()
        total = result["revenue"].sum()
        result["revenue_share"] = np.where(total > 0, result["revenue"] / total, 0)
        return result.sort_values("revenue", ascending=False)

    def time_series_decomposition(
        self,
        df: pd.DataFrame,
        period: int = 7,
    ) -> dict[str, pd.Series]:
        """STL decomposition of daily revenue.

        Expects columns: date, revenue.
        Returns dict with trend, seasonal, residual Series.
        """
        df = df.copy().sort_values("date")
        ts = df.set_index("date")["revenue"]
        ts.index = pd.DatetimeIndex(ts.index, freq="D")

        stl = STL(ts, period=period, robust=True)
        result = stl.fit()
        return {
            "observed": ts,
            "trend": result.trend,
            "seasonal": result.seasonal,
            "residual": result.resid,
        }

    def trend_detection(
        self,
        df: pd.DataFrame,
    ) -> dict:
        """Mann-Kendall trend test + Theil-Sen slope.

        Expects columns: date, revenue.
        """
        df = df.copy().sort_values("date")
        y = df["revenue"].values
        n = len(y)

        # Mann-Kendall S statistic
        s = 0
        for k in range(n - 1):
            for j in range(k + 1, n):
                diff = y[j] - y[k]
                if diff > 0:
                    s += 1
                elif diff < 0:
                    s -= 1

        # Variance of S
        unique, counts = np.unique(y, return_counts=True)
        var_s = (n * (n - 1) * (2 * n + 5)) / 18
        for t in counts[counts > 1]:
            var_s -= (t * (t - 1) * (2 * t + 5)) / 18

        if s > 0:
            z = (s - 1) / np.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / np.sqrt(var_s)
        else:
            z = 0

        p_value = 2 * (1 - stats.norm.cdf(abs(z)))

        # Theil-Sen slope
        slopes = []
        for i in range(n):
            for j in range(i + 1, n):
                if j != i:
                    slopes.append((y[j] - y[i]) / (j - i))
        median_slope = np.median(slopes) if slopes else 0

        trend = "increasing" if z > 0 and p_value < 0.05 else (
            "decreasing" if z < 0 and p_value < 0.05 else "no trend"
        )

        return {
            "trend": trend,
            "z_statistic": round(z, 4),
            "p_value": round(p_value, 6),
            "mann_kendall_s": s,
            "theil_sen_slope": round(median_slope, 4),
        }
