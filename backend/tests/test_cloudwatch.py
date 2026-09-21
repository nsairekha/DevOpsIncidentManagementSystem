"""Tests for the backend CloudWatch status/metric endpoints."""

import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient

from monitoring.cloudwatch.config import CloudWatchConfig


@pytest.fixture(autouse=True)
def _clean_aws_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from any ambient AWS configuration."""
    for var in (
        "AWS_ENABLED",
        "AWS_REGION",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "CLOUDWATCH_NAMESPACE",
        "CLOUDWATCH_DIMENSION_VALUE",
        "CLOUDWATCH_LOOKBACK_MINUTES",
    ):
        monkeypatch.delenv(var, raising=False)


def test_status_disabled(client: TestClient) -> None:
    """Disabled integrations report disabled without credentials."""
    body = client.get("/api/v1/cloudwatch/status").json()

    assert body["enabled"] is False
    assert body["available"] is False
    assert "disabled" in body["message"]
    assert body["region"] is None  # no region/names leak when disabled


def test_status_enabled(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Enabled integrations report region and namespace (no credentials)."""
    monkeypatch.setenv("AWS_ENABLED", "true")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setattr(
        "monitoring.cloudwatch.service.client_module.build_client",
        lambda config: "client",
    )

    body = client.get("/api/v1/cloudwatch/status").json()

    assert body == {
        "enabled": True,
        "available": True,
        "region": "ap-south-1",
        "namespace": "AWS/EC2",
        "message": "CloudWatch integration is enabled",
    }


def test_metrics_disabled_returns_503(client: TestClient) -> None:
    """Disabled collection yields a clear non-success status, not fake data."""
    response = client.get("/api/v1/cloudwatch/metrics")

    assert response.status_code == 503
    assert "disabled" in response.json()["detail"]


def test_metrics_demo_mode(client: TestClient) -> None:
    """demo=true serves clearly-marked demo records while disabled."""
    body = client.get("/api/v1/cloudwatch/metrics?demo=true").json()

    assert body["count"] == 5
    assert all(r["source"] == "cloudwatch_demo" for r in body["records"])
    assert body["records"][0]["metric_name"] == "CPUUtilization"


def test_metrics_success(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Enabled integrations return normalized records."""
    from datetime import datetime, timezone

    from monitoring.cloudwatch import metrics as metrics_module
    from monitoring.cloudwatch import service as service_module

    now = datetime.now(timezone.utc)
    monkeypatch.setenv("AWS_ENABLED", "true")
    monkeypatch.setenv("AWS_REGION", "ap-south-1")
    monkeypatch.setenv("CLOUDWATCH_DIMENSION_VALUE", "i-123")
    monkeypatch.setattr(
        service_module.client_module, "build_client", lambda config: "client"
    )
    monkeypatch.setattr(
        metrics_module,
        "fetch_datapoints",
        lambda client, **kwargs: [
            {"Timestamp": now, "Average": 42.5, "Unit": "Percent"}
        ],
    )

    body = client.get(
        "/api/v1/cloudwatch/metrics?metric_name=CPUUtilization&statistic=Average"
    ).json()

    assert body["count"] == 1
    record = body["records"][0]
    assert record["source"] == "cloudwatch"
    assert record["value"] == 42.5
    assert record["resource_id"] == "i-123"


def test_metrics_unknown_metric_returns_400(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown metric names are rejected with a structured 400."""
    monkeypatch.setenv("AWS_ENABLED", "true")
    monkeypatch.setenv("CLOUDWATCH_DIMENSION_VALUE", "i-123")

    response = client.get("/api/v1/cloudwatch/metrics?metric_name=Bogus")

    assert response.status_code == 400
    assert "unsupported metric" in response.json()["detail"]


def test_metrics_aws_error_returns_502(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AWS-side failures surface as structured 502s."""
    from monitoring.cloudwatch import service as service_module

    class _DeniedClient:
        def get_metric_statistics(self, **kwargs) -> dict:
            raise ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "denied"}},
                "GetMetricStatistics",
            )

    monkeypatch.setenv("AWS_ENABLED", "true")
    monkeypatch.setenv("CLOUDWATCH_DIMENSION_VALUE", "i-123")
    monkeypatch.setattr(
        service_module.client_module, "build_client", lambda config: _DeniedClient()
    )

    response = client.get("/api/v1/cloudwatch/metrics")

    assert response.status_code == 502
    assert "AccessDenied" in response.json()["detail"]


def test_metrics_rejects_non_positive_lookback(client: TestClient) -> None:
    """lookback_minutes=0 fails request validation with a 422."""
    response = client.get("/api/v1/cloudwatch/metrics?lookback_minutes=0")

    assert response.status_code == 422


def test_config_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The endpoint configuration honors environment variables."""
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    monkeypatch.setenv("CLOUDWATCH_LOOKBACK_MINUTES", "30")

    config = CloudWatchConfig()

    assert config.aws_region == "eu-west-1"
    assert config.cloudwatch_lookback_minutes == 30