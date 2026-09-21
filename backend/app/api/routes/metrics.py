"""Metric pipeline endpoints (``/api/v1``).

All data is calculated live: Prometheus is queried for real series (when
``PROMETHEUS_URL`` is configured and reachable) and CloudWatch status is
read from its service. With no observations the endpoints return honest
empty responses — never hard-coded samples.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.app.config import Settings, get_settings
from backend.app.schemas.metrics import (
    BaselinesListResponse,
    MetricsListResponse,
    MetricsSummaryResponse,
    SourceSummary,
)
from monitoring.baseline.service import BaselineService
from monitoring.cloudwatch.config import CloudWatchConfig
from monitoring.cloudwatch.service import CloudWatchService
from monitoring.models.metric import MetricRecord
from monitoring.pipeline.collector import CollectorError, PrometheusCollector

router = APIRouter(tags=["metrics"])

KNOWN_SERVICES = [
    "user-service",
    "order-service",
    "payment-service",
    "notification-service",
]

#: Instant queries backing GET /api/v1/metrics: (expr, record name, unit).
INSTANT_QUERIES: tuple[tuple[str, str, str | None], ...] = (
    ("up", "up", None),
    ("http_requests_total", "http_requests_total", "count"),
)

#: Range queries backing the baselines endpoints (last 15 minutes).
RANGE_QUERIES: tuple[tuple[str, str, str | None], ...] = (
    ("up", "up", None),
    ("http_requests_total", "http_requests_total", "count"),
    ("http_request_duration_seconds", "http_request_duration_seconds", "seconds"),
)
RANGE_MINUTES = 15


def _collector(settings: Settings) -> PrometheusCollector | None:
    """Build the Prometheus collector, or None when unconfigured."""
    if not settings.prometheus_url:
        return None
    return PrometheusCollector(settings.prometheus_url)


def _collect_instant(
    collector: PrometheusCollector,
) -> tuple[list[MetricRecord], bool]:
    """Run the instant queries; ``(records, reachable)``."""
    try:
        records: list[MetricRecord] = []
        for expr, name, unit in INSTANT_QUERIES:
            records.extend(collector.query(expr, name, unit))
    except CollectorError:
        return [], False
    return records, True


def _collect_range(
    collector: PrometheusCollector,
) -> tuple[list[MetricRecord], bool]:
    """Run the range queries over the trailing window; ``(records, reachable)``."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=RANGE_MINUTES)
    try:
        records = []
        for expr, name, unit in RANGE_QUERIES:
            records.extend(collector.query_range(expr, name, start, end, unit=unit))
    except CollectorError:
        return [], False
    return records, True


def _baselines_for(
    records: list[MetricRecord], request: Request, metric_name: str | None = None
) -> list:
    """Calculate baselines, optionally filtered to one canonical name."""
    service: BaselineService = request.app.state.baseline_service
    if metric_name is not None:
        records = [r for r in records if r.metric_name == metric_name]
    return service.build_all(records)


@router.get("/api/v1/metrics", response_model=MetricsListResponse, summary="Current metric records")
def list_metrics(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> MetricsListResponse:
    """Return live normalized records from Prometheus (empty when unreachable)."""
    collector = _collector(settings)
    if collector is None:
        return MetricsListResponse(
            count=0,
            records=[],
            message="Prometheus is not configured (PROMETHEUS_URL is empty)",
        )
    records, reachable = _collect_instant(collector)
    if not reachable:
        return MetricsListResponse(
            count=0, records=[], message="Prometheus is unreachable"
        )
    return MetricsListResponse(count=len(records), records=records)


@router.get(
    "/api/v1/metrics/summary",
    response_model=MetricsSummaryResponse,
    summary="Metric snapshot across sources",
)
def metrics_summary(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> MetricsSummaryResponse:
    """Report per-source availability/counts and the known services (real values)."""
    collector = _collector(settings)
    prom_available, prom_count = False, 0
    if collector is not None:
        records, reachable = _collect_instant(collector)
        prom_available, prom_count = reachable, len(records) if reachable else 0

    cloudwatch = CloudWatchService(_cloudwatch_config()).status()

    return MetricsSummaryResponse(
        timestamp=datetime.now(timezone.utc).isoformat(),
        sources={
            "prometheus": SourceSummary(
                available=prom_available, metric_count=prom_count
            ),
            "cloudwatch": SourceSummary(
                available=bool(cloudwatch.get("available")),
                metric_count=0,
            ),
        },
        services=list(KNOWN_SERVICES),
    )


@router.get(
    "/api/v1/baselines", response_model=BaselinesListResponse, summary="Baseline records"
)
def list_baselines(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> BaselinesListResponse:
    """Calculate baselines from the trailing Prometheus window (empty when none)."""
    collector = _collector(settings)
    if collector is None:
        return BaselinesListResponse(
            count=0,
            baselines=[],
            message="Prometheus is not configured (PROMETHEUS_URL is empty)",
        )
    records, reachable = _collect_range(collector)
    if not reachable:
        return BaselinesListResponse(
            count=0, baselines=[], message="Prometheus is unreachable"
        )
    baselines = _baselines_for(records, request)
    if not baselines:
        return BaselinesListResponse(
            count=0, baselines=[], message="no metric observations found"
        )
    return BaselinesListResponse(count=len(baselines), baselines=baselines)


@router.get(
    "/api/v1/baselines/{metric_name}",
    response_model=BaselinesListResponse,
    summary="Baseline for one metric",
)
def get_baseline(
    metric_name: str,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> BaselinesListResponse:
    """Calculate the baseline for one canonical metric name (404 when absent)."""
    collector = _collector(settings)
    if collector is None:
        raise HTTPException(
            status_code=404,
            detail=f"no baseline for metric '{metric_name}' (Prometheus unconfigured)",
        )
    records, reachable = _collect_range(collector)
    if not reachable:
        raise HTTPException(
            status_code=404,
            detail=f"no baseline for metric '{metric_name}' (Prometheus unreachable)",
        )
    baselines = _baselines_for(records, request, metric_name)
    if not baselines:
        raise HTTPException(
            status_code=404, detail=f"no baseline for metric '{metric_name}'"
        )
    return BaselinesListResponse(count=len(baselines), baselines=baselines)


def _cloudwatch_config() -> CloudWatchConfig:
    """Build CloudWatch configuration from the environment."""
    return CloudWatchConfig()