"""E-Commerce Analytics — Streamlit entrypoint."""

import os

import streamlit as st

from src.config.loader import load_settings

settings = load_settings()

st.set_page_config(
    page_title=settings.app.title,
    page_icon=settings.app.page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# Demo mode indicator
if os.environ.get("DEMO_MODE", "1") == "1":
    st.sidebar.info("**Demo Mode** — mock data kullaniliyor. "
                    "BigQuery baglamak icin `DEMO_MODE=0` ile calistirin.")

# --- Navigation ---
pages = {
    "Overview": "pages/0_overview.py",
    "Clickstream": "pages/1_clickstream.py",
    "Orders & Revenue": "pages/2_orders.py",
    "Recommendations": "pages/3_recommendations.py",
    "A/B Testing": "pages/4_ab_testing.py",
    "Reports": "pages/5_reports.py",
}

pg = st.navigation([st.Page(path, title=title) for title, path in pages.items()])
pg.run()
