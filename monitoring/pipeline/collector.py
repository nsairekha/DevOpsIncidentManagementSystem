"""Live-source collectors producing MetricRecords.

Prometheus
    |
    v
PrometheusCollector (HTTP API: instant + range queries)
    |
    v
                MetricRecord
                        |
CloudWatch ---> CloudWatchCollector (delegates to CloudWatchService)
"""

from datetime import datetime

import httpx

from monitoring.cloudwatch.service import CloudWatchService
from monitoring.models.metric import MetricRecord
from monitoring.normalization import cloudwatch as cloudwatch_norm
from monitoring.normalization import prometheus as prometheus_norm


class CollectorError(Exception):
    """A live source could not be collected (network, API error, ...)."""

    def __init__(self, source: str, message: str) -> None:
        super().__init__(message)
        self.source = source
        self.message = message


class PrometheusCollector:
    """Collect MetricRecords from a Prometheus HTTP API."""

    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = client

    def _get(self, path: str, params: dict) -> dict:
        """GET a Prometheus API path, mapping transport/API errors."""
        owned = self.client is None
        client = self.client or httpx.Client(timeout=10.0)
        try:
            try:
                response = client.get(f"{self.base_url}{path}", params=params)
                response.raise_for_status()
                body = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                raise CollectorError("prometheus", f"query failed: {exc}") from exc
        finally:
            if owned:
                client.close()
        if body.get("status") != "success":
            raise CollectorError("prometheus", f"query failed: {body.get('error')}")
        return body

    def query(
        self, expr: str, metric_name: str, unit: str | None = None
    ) -> list[MetricRecord]:
        """Run an instant query and normalize the vector into records."""
        body = self._get("/api/v1/query", {"query": expr})
        return prometheus_norm.from_instant_vector(
            body.get("data", {}).get("result", []),
            metric_name,
            unit,
        )

    def query_range(
        self,
        expr: str,
        metric_name: str,
        start: datetime,
        end: datetime,
        step: str = "15s",
        unit: str | None = None,
    ) -> list[MetricRecord]:
        """Run a range query and normalize the matrix into records."""
        body = self._get(
            "/api/v1/query_range",
            {
                "query": expr,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "step": step,
            },
        )
        return prometheus_norm.from_matrix(
            body.get("data", {}).get("result", []),
            metric_name,
            unit,
        )


class CloudWatchCollector:
    """Collect MetricRecords through the CloudWatch service layer."""

    def __init__(self, service: CloudWatchService) -> None:
        self.service = service

    def collect(
        self,
        *,
        metric_name: str,
        resource_id: str | None = None,
        lookback_minutes: int | None = None,
        statistic: str = "Average",
    ) -> list[MetricRecord]:
        """Fetch and normalize one CloudWatch metric (real or structured error)."""
        records = self.service.get_metrics(
            metric_name=metric_name,
            resource_id=resource_id,
            lookback_minutes=lookback_minutes,
            statistic=statistic,
        )
        return cloudwatch_norm.from_cloudwatch_records(records)