"""Pydantic configuration schemas."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# --- Settings ---

class BigQuerySettings(BaseModel):
    project_id: str
    dataset: str
    location: str = "US"
    timeout: int = 60


class CacheSettings(BaseModel):
    ttl_seconds: int = 3600
    max_entries: int = 100


class AppSettings(BaseModel):
    title: str = "E-Commerce Analytics"
    default_date_range_days: int = 30
    page_icon: str = "📊"
    timezone: str = "UTC"


class LoggingSettings(BaseModel):
    level: str = "INFO"
    rotation: str = "10 MB"
    retention: str = "30 days"


class Settings(BaseModel):
    bigquery: BigQuerySettings
    cache: CacheSettings = CacheSettings()
    app: AppSettings = AppSettings()
    logging: LoggingSettings = LoggingSettings()


# --- Metrics ---

class MetricThresholds(BaseModel):
    good: float
    warning: float
    critical: float


class MetricDefinition(BaseModel):
    label: str
    format: str = "number"
    decimals: int = 2
    thresholds: Optional[MetricThresholds] = None
    direction: str = "higher_is_better"


class MetricsConfig(BaseModel):
    clickstream: dict[str, MetricDefinition] = Field(default_factory=dict)
    orders: dict[str, MetricDefinition] = Field(default_factory=dict)
    recommendations: dict[str, MetricDefinition] = Field(default_factory=dict)


# --- A/B Test ---

class ABTestDefaults(BaseModel):
    significance_level: float = 0.05
    power: float = 0.80
    min_detectable_effect: float = 0.02
    allocation_ratio: float = 0.5


class FrequentistSettings(BaseModel):
    test_type: str = "two-sided"
    correction_method: str = "benjamini-hochberg"


class BayesianSettings(BaseModel):
    prior_alpha: float = 1.0
    prior_beta: float = 1.0
    prior_mu: float = 0.0
    prior_sigma: float = 100.0
    rope_lower: float = -0.005
    rope_upper: float = 0.005
    n_samples: int = 10000
    credible_interval: float = 0.95


class SequentialSettings(BaseModel):
    spending_function: str = "obrien-fleming"
    max_looks: int = 5
    min_sample_fraction: float = 0.2


class DiagnosticsSettings(BaseModel):
    srm_threshold: float = 0.001
    novelty_window_days: int = 7
    cuped_enabled: bool = True


class SegmentAnalysisSettings(BaseModel):
    dimensions: list[str] = Field(default_factory=lambda: ["device", "traffic_source", "user_type"])
    correction_method: str = "bonferroni"


class ABTestConfig(BaseModel):
    defaults: ABTestDefaults = ABTestDefaults()
    frequentist: FrequentistSettings = FrequentistSettings()
    bayesian: BayesianSettings = BayesianSettings()
    sequential: SequentialSettings = SequentialSettings()
    diagnostics: DiagnosticsSettings = DiagnosticsSettings()
    segment_analysis: SegmentAnalysisSettings = SegmentAnalysisSettings()


# --- Reports ---

class AudienceConfig(BaseModel):
    label: str
    template: str
    max_pages: Optional[int] = None
    components: list[str] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)


class ReportStyling(BaseModel):
    primary_color: str = "#4F46E5"
    font_family: str = "Inter, sans-serif"
    logo_path: Optional[str] = None


class ReportsConfig(BaseModel):
    audiences: dict[str, AudienceConfig] = Field(default_factory=dict)
    formats: list[str] = Field(default_factory=lambda: ["pdf", "html"])
    styling: ReportStyling = ReportStyling()
