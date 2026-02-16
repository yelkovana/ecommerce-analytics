"""Singleton BigQuery client with query execution."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from google.cloud import bigquery
from loguru import logger

from src.config.loader import load_settings


class BigQueryClient:
    _instance: Optional[BigQueryClient] = None

    def __new__(cls) -> BigQueryClient:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        settings = load_settings()
        self._client = bigquery.Client(
            project=settings.bigquery.project_id,
            location=settings.bigquery.location,
        )
        self._dataset = settings.bigquery.dataset
        self._timeout = settings.bigquery.timeout
        self._initialized = True
        logger.info("BigQuery client initialized for project={}", settings.bigquery.project_id)

    @property
    def dataset(self) -> str:
        return self._dataset

    def execute_query(self, sql: str, params: Optional[dict] = None) -> pd.DataFrame:
        logger.debug("Executing query ({} chars)", len(sql))
        job_config = bigquery.QueryJobConfig()
        if params:
            job_config.query_parameters = [
                bigquery.ScalarQueryParameter(k, "STRING", v)
                for k, v in params.items()
            ]
        query_job = self._client.query(sql, job_config=job_config, timeout=self._timeout)
        df = query_job.to_dataframe()
        logger.debug("Query returned {} rows", len(df))
        return df
