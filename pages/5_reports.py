"""Report Generation page."""

import streamlit as st
from datetime import date

from src.reporting.generator import ReportGenerator
from src.config.loader import load_settings
from src.utils.date_utils import get_date_range, format_date_range, date_to_str

settings = load_settings()
generator = ReportGenerator()

st.title("Report Generation")

# --- Configuration ---
st.subheader("1. Select Audience")
audiences = generator.get_available_audiences()
audience_labels = {a["key"]: f"{a['label']} (max {a['max_pages'] or '∞'} pages)" for a in audiences}
selected_audience = st.selectbox("Target audience", list(audience_labels.keys()),
                                  format_func=lambda k: audience_labels[k])

st.subheader("2. Select Modules")
modules = st.multiselect(
    "Include modules",
    ["Overview KPIs", "Clickstream", "Orders & Revenue", "Recommendations", "A/B Testing"],
    default=["Overview KPIs", "Orders & Revenue"],
)

st.subheader("3. Date Range")
date_range = st.date_input(
    "Report period",
    value=get_date_range(settings.app.default_date_range_days),
    max_value=date.today(),
    key="report_dates",
)
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = get_date_range(settings.app.default_date_range_days)

st.subheader("4. Output Format")
output_format = st.radio("Format", ["PDF", "HTML"], horizontal=True)

# --- Preview & Generate ---
st.divider()

if st.button("Generate Report", type="primary"):
    with st.spinner("Generating report..."):
        # Build report data (would normally query BQ and run analyzers)
        report_data = {
            "kpis": [
                {"label": "GMV", "value": "$1,234,567", "delta": 0.12},
                {"label": "Sessions", "value": "456,789", "delta": 0.08},
                {"label": "Conversion Rate", "value": "3.2%", "delta": -0.02},
                {"label": "AOV", "value": "$45.67", "delta": 0.05},
            ],
            "sections": [],
            "alerts": [],
            "action_items": [],
            "health_indicators": [
                {"label": "Revenue", "status": "good"},
                {"label": "Conversion", "status": "warning"},
                {"label": "Bounce Rate", "status": "good"},
            ],
            "trends": [
                {"label": "Revenue +12% WoW", "direction": "up"},
                {"label": "AOV +5% WoW", "direction": "up"},
                {"label": "Bounce Rate -2% WoW", "direction": "down"},
            ],
        }

        if "Clickstream" in modules:
            report_data["sections"].append({
                "title": "Clickstream Summary",
                "description": "Session and engagement metrics for the selected period.",
                "table": {
                    "columns": ["Metric", "Value", "Change"],
                    "rows": [
                        ["Sessions", "456,789", "+8%"],
                        ["Bounce Rate", "38.5%", "-2%"],
                        ["Pages/Session", "3.8", "+5%"],
                    ],
                },
            })

        if "Orders & Revenue" in modules:
            report_data["sections"].append({
                "title": "Revenue Analysis",
                "description": "Order and revenue performance overview.",
                "table": {
                    "columns": ["Metric", "Value", "Change"],
                    "rows": [
                        ["GMV", "$1,234,567", "+12%"],
                        ["Orders", "27,123", "+10%"],
                        ["AOV", "$45.67", "+5%"],
                    ],
                },
            })

        if "A/B Testing" in modules:
            report_data["sections"].append({
                "title": "A/B Test Results",
                "description": "Summary of active and recently concluded experiments.",
                "methodology": "Two-proportion z-test with Benjamini-Hochberg FDR correction.",
                "table": {
                    "columns": ["Test", "Variant", "Conv. Rate", "p-value", "Significant"],
                    "rows": [
                        ["Checkout Redesign", "Treatment", "4.2%", "0.003", "Yes"],
                        ["New Rec Algorithm", "Treatment", "3.1%", "0.142", "No"],
                    ],
                },
            })

        report_data["action_items"] = [
            "Investigate conversion rate decline on mobile devices",
            "Consider rolling out Checkout Redesign experiment to 100%",
            "Review recommendation algorithm coverage for long-tail products",
        ]

        try:
            date_range_str = format_date_range(start_date, end_date)
            result = generator.generate(
                audience=selected_audience,
                data=report_data,
                output_format=output_format.lower(),
                date_range=date_range_str,
            )

            if output_format == "HTML":
                st.subheader("Preview")
                st.components.v1.html(result, height=800, scrolling=True)
                st.download_button(
                    "Download HTML",
                    data=result,
                    file_name=f"report_{selected_audience}_{date_to_str(end_date)}.html",
                    mime="text/html",
                )
            else:
                st.success("PDF generated successfully!")
                st.download_button(
                    "Download PDF",
                    data=result,
                    file_name=f"report_{selected_audience}_{date_to_str(end_date)}.pdf",
                    mime="application/pdf",
                )
        except Exception as e:
            st.error(f"Report generation failed: {e}")
