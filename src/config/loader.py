"""YAML configuration loading with Pydantic validation."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from src.config.models import ABTestConfig, MetricsConfig, ReportsConfig, Settings

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"


def _load_yaml(filename: str) -> dict:
    path = CONFIG_DIR / filename
    with open(path) as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_settings() -> Settings:
    return Settings(**_load_yaml("settings.yaml"))


@lru_cache(maxsize=1)
def load_metrics() -> MetricsConfig:
    return MetricsConfig(**_load_yaml("metrics.yaml"))


@lru_cache(maxsize=1)
def load_ab_test_config() -> ABTestConfig:
    return ABTestConfig(**_load_yaml("ab_test.yaml"))


@lru_cache(maxsize=1)
def load_reports_config() -> ReportsConfig:
    return ReportsConfig(**_load_yaml("reports.yaml"))
