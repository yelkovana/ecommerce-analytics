"""Jinja2 SQL template renderer."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

QUERIES_DIR = Path(__file__).resolve().parent / "queries"

_env = Environment(
    loader=FileSystemLoader(str(QUERIES_DIR)),
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_query(template_name: str, **kwargs) -> str:
    """Render a SQL template with the given parameters."""
    template = _env.get_template(template_name)
    return template.render(**kwargs)
