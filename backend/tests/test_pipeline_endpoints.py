"""Tests for the metric pipeline backend endpoints (Prometheus mocked)."""

import pytest
from fastapi.testclient import TestClient

from backend.app.config import settings
from monitoring.pipeline.collector import PrometheusCollector


@pytest.fixture(autouse=True)
def _prometheus_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the backend at a fake Prometheus server."""
    monkeypatch.setattr(settings, "prometheus_url", "http://prom:9090")


def _vector(value: str = "1") -> list[dict]:
    return [{"metric": {"service": "order-service"}, "value": [1726900000, value]}]


def _matrix() -> list[dict]:
    return [
        {
            "metric": {"service": "order-service"},
            "values": [[1726900000, "0.1"], [1726900060, "0.2"]],
        }
    ]


def _fake_query(self, expr, metric_name, unit=None) -> list:
    from monitoring.normalization import prometheus as prometheus_norm

    return prometheus_norm.from_instant_vector(_vector(), metric_name)


def _fake_range(self, expr, *args, **kwargs) -> list:
    from monitoring.normalization import prometheus as prometheus_norm

    if expr != "http_request_duration_seconds":
        return []
    return prometheus_norm.from_matrix(_matrix(), expr)


def test_list_metrics_live(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GET /api/v1/metrics returns normalized live records."""
    monkeypatch.setattr(PrometheusCollector, "query", _fake_query)

    body = client.get("/api/v1/metrics").json()

    assert body["count"] == 2
    assert sorted(r["metric_name"] for r in body["records"]) == [
        "request_count",
        "up",
    ]
    assert body["records"][0]["source"] == "prometheus"


def test_list_metrics_unconfigured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without PROMETHEUS_URL the endpoint returns an honest empty response."""
    monkeypatch.setattr(settings, "prometheus_url", None)

    body = client.get("/api/v1/metrics").json()

    assert body == {
        "count": 0,
        "records": [],
        "message": "Prometheus is not configured (PROMETHEUS_URL is empty)",
    }


def test_list_metrics_unreachable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreachable Prometheus yields an empty response, not an error."""
    from monitoring.pipeline.collector import CollectorError

    def broken(self, *args, **kwargs) -> list:
        raise CollectorError("prometheus", "down")

    monkeypatch.setattr(PrometheusCollector, "query", broken)

    body = client.get("/api/v1/metrics").json()

    assert body["count"] == 0
    assert body["message"] == "Prometheus is unreachable"


def test_summary_reports_real_values(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GET /api/v1/metrics/summary reflects live source state."""
    monkeypatch.setattr(PrometheusCollector, "query", _fake_query)

    body = client.get("/api/v1/metrics/summary").json()

    assert body["sources"]["prometheus"] == {
        "available": True,
        "metric_count": 2,
    }
    assert body["sources"]["cloudwatch"]["available"] is False
    assert body["sources"]["cloudwatch"]["metric_count"] == 0
    assert body["services"] == [
        "user-service",
        "order-service",
        "payment-service",
        "notification-service",
    ]
    assert body["timestamp"]


def test_summary_prometheus_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An unreachable Prometheus is reported as unavailable with zero count."""
    from monitoring.pipeline.collector import CollectorError

    def broken(self, *args, **kwargs) -> list:
        raise CollectorError("prometheus", "down")

    monkeypatch.setattr(PrometheusCollector, "query", broken)

    body = client.get("/api/v1/metrics/summary").json()

    assert body["sources"]["prometheus"] == {"available": False, "metric_count": 0}


def test_list_baselines_live(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GET /api/v1/baselines calculates baselines from range data."""
    monkeypatch.setattr(PrometheusCollector, "query_range", _fake_range)

    body = client.get("/api/v1/baselines").json()

    assert body["count"] == 1
    baseline = body["baselines"][0]
    assert baseline["metric_name"] == "latency"
    assert baseline["observation_count"] == 2
    assert baseline["mean"] == pytest.approx(0.15)


def test_list_baselines_empty(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No observations produce an honest empty message."""
    monkeypatch.setattr(
        PrometheusCollector, "query_range", lambda self, *a, **k: []
    )

    body = client.get("/api/v1/baselines").json()

    assert body == {
        "count": 0,
        "baselines": [],
        "message": "no metric observations found",
    }


def test_list_baselines_unconfigured(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unconfigured Prometheus produces an honest empty message."""
    monkeypatch.setattr(settings, "prometheus_url", None)

    body = client.get("/api/v1/baselines").json()

    assert body["count"] == 0
    assert "not configured" in (body["message"] or "")


def test_get_baseline_by_name(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """GET /api/v1/baselines/{name} filters to one canonical metric."""
    monkeypatch.setattr(PrometheusCollector, "query_range", _fake_range)

    body = client.get("/api/v1/baselines/latency").json()

    assert body["count"] == 1
    assert body["baselines"][0]["metric_name"] == "latency"


def test_list_baselines_unreachable(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unreachable Prometheus yields an honest empty baselines response."""
    from monitoring.pipeline.collector import CollectorError

    def broken(self, *args, **kwargs) -> list:
        raise CollectorError("prometheus", "down")

    monkeypatch.setattr(PrometheusCollector, "query_range", broken)

    body = client.get("/api/v1/baselines").json()

    assert body == {
        "count": 0,
        "baselines": [],
        "message": "Prometheus is unreachable",
    }


def test_get_baseline_unreachable_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unreachable Prometheus 404s for single-metric baselines."""
    from monitoring.pipeline.collector import CollectorError

    def broken(self, *args, **kwargs) -> list:
        raise CollectorError("prometheus", "down")

    monkeypatch.setattr(PrometheusCollector, "query_range", broken)

    response = client.get("/api/v1/baselines/latency")

    assert response.status_code == 404


def test_get_baseline_unknown_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown metric names 404 instead of fabricating a baseline."""
    monkeypatch.setattr(
        PrometheusCollector, "query_range", lambda self, *a, **k: []
    )

    response = client.get("/api/v1/baselines/nope")

    assert response.status_code == 404
    assert "no baseline" in response.json()["detail"]


def test_get_baseline_unconfigured_returns_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unconfigured Prometheus 404s with an explanatory message."""
    monkeypatch.setattr(settings, "prometheus_url", None)

    response = client.get("/api/v1/baselines/latency")

    assert response.status_code == 404