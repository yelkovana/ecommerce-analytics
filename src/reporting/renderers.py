"""HTML and PDF rendering."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from loguru import logger

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=False,
    keep_trailing_newline=True,
)


def render_html(template_name: str, context: dict[str, Any]) -> str:
    """Render an HTML report from a Jinja2 template."""
    template = _env.get_template(template_name)
    return template.render(**context)


def render_pdf(html_content: str) -> bytes:
    """Convert HTML to PDF using WeasyPrint."""
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content, base_url=str(TEMPLATES_DIR)).write_pdf()
        logger.info("PDF generated ({} bytes)", len(pdf_bytes))
        return pdf_bytes
    except ImportError:
        logger.warning("WeasyPrint not installed — returning HTML as fallback")
        return html_content.encode("utf-8")
    except Exception as e:
        logger.error("PDF generation failed: {}", e)
        raise
