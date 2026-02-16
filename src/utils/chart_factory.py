"""Plotly chart builder with consistent theme."""

from __future__ import annotations

from typing import Optional

import plotly.express as px
import plotly.graph_objects as go

COLORS = {
    "primary": "#4F46E5",
    "secondary": "#06B6D4",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "neutral": "#64748B",
}

PALETTE = ["#4F46E5", "#06B6D4", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#64748B"]

_LAYOUT_DEFAULTS = dict(
    font=dict(family="Inter, sans-serif", size=12, color="#1E293B"),
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=40, r=20, t=40, b=40),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    colorway=PALETTE,
)


def apply_theme(fig: go.Figure) -> go.Figure:
    """Apply standard theme to a Plotly figure."""
    fig.update_layout(**_LAYOUT_DEFAULTS)
    fig.update_xaxes(showgrid=False, showline=True, linewidth=1, linecolor="#E2E8F0")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#F1F5F9", showline=False)
    return fig


def line_chart(df, x: str, y: str, color: Optional[str] = None, title: str = "") -> go.Figure:
    fig = px.line(df, x=x, y=y, color=color, title=title)
    return apply_theme(fig)


def bar_chart(df, x: str, y: str, color: Optional[str] = None, title: str = "",
              orientation: str = "v") -> go.Figure:
    fig = px.bar(df, x=x, y=y, color=color, title=title, orientation=orientation)
    return apply_theme(fig)


def funnel_chart(stages: list[str], values: list[float], title: str = "") -> go.Figure:
    fig = go.Figure(go.Funnel(y=stages, x=values, textinfo="value+percent initial"))
    fig.update_layout(title=title)
    return apply_theme(fig)


def heatmap(df, x: str, y: str, z: str, title: str = "", color_scale: str = "Blues") -> go.Figure:
    pivot = df.pivot(index=y, columns=x, values=z)
    fig = px.imshow(pivot, color_continuous_scale=color_scale, title=title, aspect="auto",
                    text_auto=".1%")
    return apply_theme(fig)


def treemap(df, path: list[str], values: str, title: str = "") -> go.Figure:
    fig = px.treemap(df, path=path, values=values, title=title, color_continuous_scale="Blues")
    return apply_theme(fig)


def pie_chart(df, names: str, values: str, title: str = "") -> go.Figure:
    fig = px.pie(df, names=names, values=values, title=title, color_discrete_sequence=PALETTE)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return apply_theme(fig)


def sparkline(values: list[float], color: str = COLORS["primary"]) -> go.Figure:
    """Minimal sparkline chart for KPI cards."""
    fig = go.Figure(go.Scatter(
        y=values, mode="lines", line=dict(color=color, width=2),
        fill="tozeroy", fillcolor=f"rgba(79, 70, 229, 0.1)",
    ))
    fig.update_layout(
        height=60, margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def traffic_light(status: str) -> str:
    """Return a colored circle emoji based on status."""
    mapping = {"good": "🟢", "warning": "🟡", "critical": "🔴"}
    return mapping.get(status, "⚪")
