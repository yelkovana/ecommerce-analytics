"""Streamlit cache wrappers for BigQuery queries — with demo mode fallback."""

from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import streamlit as st

from src.data.query_builder import render_query

DEMO_MODE = os.environ.get("DEMO_MODE", "1") == "1"


def _use_bigquery() -> bool:
    """Check if BigQuery is available."""
    if DEMO_MODE:
        return False
    try:
        from src.data.bigquery_client import BigQueryClient
        BigQueryClient()
        return True
    except Exception:
        return False


@st.cache_data(ttl=3600, show_spinner="Loading data...")
def cached_query(template_name: str, **kwargs) -> pd.DataFrame:
    """Execute a cached query — BigQuery or mock data."""
    if _use_bigquery():
        from src.data.bigquery_client import BigQueryClient
        sql = render_query(template_name, **kwargs)
        client = BigQueryClient()
        return client.execute_query(sql)
    else:
        from src.data.mock_data import get_mock_data
        return get_mock_data(template_name, **kwargs)


@st.cache_data(ttl=3600, show_spinner="Loading data...")
def cached_raw_query(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    """Execute a cached raw SQL query."""
    if _use_bigquery():
        from src.data.bigquery_client import BigQueryClient
        client = BigQueryClient()
        return client.execute_query(sql, params)
    return pd.DataFrame()
