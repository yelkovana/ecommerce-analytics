"""Report generator orchestrator."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from loguru import logger

from src.config.loader import load_reports_config
from src.reporting.renderers import render_html, render_pdf


class ReportGenerator:
    """Orchestrates report generation for different audiences."""

    def __init__(self) -> None:
        self.config = load_reports_config()

    def generate(
        self,
        audience: str,
        data: dict[str, Any],
        output_format: str = "pdf",
        date_range: str = "",
    ) -> bytes | str:
        """Generate a report for the given audience.

        Args:
            audience: "executive", "business", or "technical"
            data: Dict with kpis, sections, alerts, action_items, etc.
            output_format: "pdf" or "html"
            date_range: Display string for date range

        Returns:
            PDF bytes or HTML string.
        """
        audience_cfg = self.config.audiences.get(audience)
        if audience_cfg is None:
            raise ValueError(f"Unknown audience: {audience}. Available: {list(self.config.audiences.keys())}")

        template_name = audience_cfg.template
        styling = self.config.styling

        context = {
            "report_title": f"E-Commerce Analytics — {audience_cfg.label}",
            "date_range": date_range,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "primary_color": styling.primary_color,
            "font_family": styling.font_family,
            **data,
        }

        logger.info("Generating {} report for audience={}", output_format, audience)

        html_content = render_html(template_name, context)

        if output_format == "html":
            return html_content
        elif output_format == "pdf":
            return render_pdf(html_content)
        else:
            raise ValueError(f"Unknown format: {output_format}")

    def get_available_audiences(self) -> list[dict]:
        return [
            {"key": k, "label": v.label, "max_pages": v.max_pages}
            for k, v in self.config.audiences.items()
        ]
