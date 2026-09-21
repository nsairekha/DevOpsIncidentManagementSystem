"""Tests for the CloudWatch integration (boto3 calls mocked, no real AWS)."""

from datetime import datetime, timezone

import pytest
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
    NoCredentialsError,
    NoRegionError,
)
from pydantic import ValidationError

from monitoring.cloudwatch import client as client_module
from monitoring.cloudwatch import metrics as metrics_module
from monitoring.cloudwatch.config import CloudWatchConfig
from monitoring.cloudwatch.models import (
    CloudWatchAWSError,
    CloudWatchConfigError,
    CloudWatchDisabledError,
    MetricRecord,
)
from monitoring.cloudwatch.service import CloudWatchService


def _config(**overrides) -> CloudWatchConfig:
    base = {
        "aws_enabled": True,
        "aws_region": "ap-south-1",
        "cloudwatch_dimension_value": "i-123",
    }
    base.update(overrides)
    return CloudWatchConfig(**base)


def _point(ts: datetime, value: float) -> dict:
    return {"Timestamp": ts, "Average": value, "Unit": "Percent"}


class _FakeBotoClient:
    """Minimal fake of the boto3 CloudWatch client."""

    def __init__(
        self,
        datapoints: list[dict] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.datapoints = datapoints if datapoints is not None else []
        self.error = error
        self.calls: list[dict] = []

    def get_metric_statistics(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return {"Datapoints": self.datapoints}


# ---------------------------------------------------------------------- #
# Configuration
# ---------------------------------------------------------------------- #
def test_config_defaults_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Without env vars the integration is disabled with EC2 defaults."""
    for var in (
        "AWS_ENABLED",
        "AWS_REGION",
        "CLOUDWATCH_NAMESPACE",
        "CLOUDWATCH_DIMENSION_VALUE",
        "CLOUDWATCH_LOOKBACK_MINUTES",
    ):
        monkeypatch.delenv(var, raising=False)

    config = CloudWatchConfig()

    assert config.aws_enabled is False
    assert config.cloudwatch_namespace == "AWS/EC2"
    assert config.cloudwatch_lookback_minutes == 10
    assert config.dimensions == {}


def test_config_dimensions(monkeypatch: pytest.MonkeyPatch) -> None:
    """A configured dimension value produces the dimension mapping."""
    monkeypatch.setenv("CLOUDWATCH_DIMENSION_VALUE", "i-abc")

    assert CloudWatchConfig().dimensions == {"InstanceId": "i-abc"}


# ---------------------------------------------------------------------- #
# Client construction
# ---------------------------------------------------------------------- #
def test_build_client_disabled_raises() -> None:
    """Building a client while disabled raises without touching boto3."""
    with pytest.raises(CloudWatchDisabledError):
        client_module.build_client(CloudWatchConfig(aws_enabled=False))


def test_build_client_with_region_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Region-only configuration forwards just the region."""
    seen: dict = {}

    def fake_client(service: str, **kwargs) -> str:
        seen["service"] = service
        seen.update(kwargs)
        return "client"

    monkeypatch.setattr("boto3.client", fake_client)

    assert client_module.build_client(_config()) == "client"
    assert seen == {"service": "cloudwatch", "region_name": "ap-south-1"}


def test_build_client_with_full_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keys and session token are forwarded when configured."""
    seen: dict = {}

    def fake_client(service: str, **kwargs) -> str:
        seen.update(kwargs)
        return "client"

    monkeypatch.setattr("boto3.client", fake_client)
    config = _config(
        aws_access_key_id="AKID",
        aws_secret_access_key="SECRET",
        aws_session_token="TOKEN",
    )

    client_module.build_client(config)

    assert seen["aws_access_key_id"] == "AKID"
    assert seen["aws_secret_access_key"] == "SECRET"
    assert seen["aws_session_token"] == "TOKEN"


def test_build_client_without_region(monkeypatch: pytest.MonkeyPatch) -> None:
    """No region means no region kwarg (IAM/default chain may supply it)."""
    seen: dict = {"region_name": "sentinel"}

    def fake_client(service: str, **kwargs) -> str:
        seen.clear()
        seen.update(kwargs)
        return "client"

    monkeypatch.setattr("boto3.client", fake_client)

    client_module.build_client(_config(aws_region=None))

    assert "region_name" not in seen


# ---------------------------------------------------------------------- #
# Retrieval
# ---------------------------------------------------------------------- #
def test_lookback_window_is_utc_and_bounded() -> None:
    """The window ends now (UTC, never the future) and spans the lookback."""
    before = datetime.now(timezone.utc)
    start, end = metrics_module.lookback_window(10)
    after = datetime.now(timezone.utc)

    assert before <= end <= after
    assert end.tzinfo is not None
    assert (end - start).total_seconds() == pytest.approx(600.0)


def test_lookback_window_rejects_non_positive() -> None:
    """Zero/negative lookbacks raise instead of querying the future."""
    with pytest.raises(CloudWatchAWSError):
        metrics_module.lookback_window(0)


def test_fetch_datapoints_sorted_oldest_first() -> None:
    """Datapoints come back sorted even when AWS returns them shuffled."""
    now = datetime.now(timezone.utc)
    fake = _FakeBotoClient([_point(now, 2.0), _point(now, 1.0)][::-1])

    points = metrics_module.fetch_datapoints(
        fake,
        namespace="AWS/EC2",
        metric_name="CPUUtilization",
        dimensions={"InstanceId": "i-123"},
        start_time=now,
        end_time=now,
        period=60,
        statistics=["Average"],
    )

    assert [p["Average"] for p in points] == [1.0, 2.0]
    call = fake.calls[0]
    assert call["Namespace"] == "AWS/EC2"
    assert call["Dimensions"] == [{"Name": "InstanceId", "Value": "i-123"}]
    assert call["Period"] == 60
    assert call["Statistics"] == ["Average"]


def test_fetch_datapoints_empty() -> None:
    """Missing metrics yield an empty list, not an error."""
    fake = _FakeBotoClient([])

    assert (
        metrics_module.fetch_datapoints(
            fake,
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={},
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            period=60,
            statistics=["Average"],
        )
        == []
    )


def _client_error() -> ClientError:
    return ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "nope"}}, "GetMetricStatistics"
    )


def test_fetch_maps_no_credentials() -> None:
    """Missing credentials become a structured AWS error."""
    with pytest.raises(CloudWatchAWSError) as exc:
        metrics_module.fetch_datapoints(
            _FakeBotoClient(error=NoCredentialsError()),
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={},
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            period=60,
            statistics=["Average"],
        )

    assert exc.value.aws_code == "NoCredentials"


def test_fetch_maps_no_region() -> None:
    """A missing region becomes a structured AWS error."""
    with pytest.raises(CloudWatchAWSError) as exc:
        metrics_module.fetch_datapoints(
            _FakeBotoClient(error=NoRegionError()),
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={},
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            period=60,
            statistics=["Average"],
        )

    assert exc.value.aws_code == "NoRegion"


def test_fetch_maps_endpoint_failure() -> None:
    """Unreachable endpoints become a structured AWS error."""
    with pytest.raises(CloudWatchAWSError) as exc:
        metrics_module.fetch_datapoints(
            _FakeBotoClient(
                error=EndpointConnectionError(endpoint_url="https://x")
            ),
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={},
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            period=60,
            statistics=["Average"],
        )

    assert exc.value.aws_code == "EndpointConnection"


def test_fetch_maps_client_error_with_code() -> None:
    """Service errors (e.g. permissions) preserve the AWS error code."""
    with pytest.raises(CloudWatchAWSError) as exc:
        metrics_module.fetch_datapoints(
            _FakeBotoClient(error=_client_error()),
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={},
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            period=60,
            statistics=["Average"],
        )

    assert exc.value.aws_code == "AccessDenied"
    assert "AccessDenied" in exc.value.message


def test_fetch_maps_generic_sdk_error() -> None:
    """Other SDK failures become unstructured-code AWS errors."""
    with pytest.raises(CloudWatchAWSError) as exc:
        metrics_module.fetch_datapoints(
            _FakeBotoClient(error=BotoCoreError()),
            namespace="AWS/EC2",
            metric_name="CPUUtilization",
            dimensions={},
            start_time=datetime.now(timezone.utc),
            end_time=datetime.now(timezone.utc),
            period=60,
            statistics=["Average"],
        )

    assert exc.value.aws_code is None


# ---------------------------------------------------------------------- #
# Service: status + retrieval + normalization + demo
# ---------------------------------------------------------------------- #
def test_status_disabled() -> None:
    """Disabled integrations report disabled without touching AWS."""
    assert CloudWatchService(CloudWatchConfig(aws_enabled=False)).status() == {
        "enabled": False,
        "available": False,
        "message": "CloudWatch integration is disabled (AWS_ENABLED=false)",
    }


def test_status_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enabled integrations report region and namespace."""
    monkeypatch.setattr(client_module, "build_client", lambda config: "client")

    assert CloudWatchService(_config()).status() == {
        "enabled": True,
        "available": True,
        "region": "ap-south-1",
        "namespace": "AWS/EC2",
        "message": "CloudWatch integration is enabled",
    }


def test_status_build_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Client construction failures are reported, not raised."""
    def broken(config) -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr(client_module, "build_client", broken)

    body = CloudWatchService(_config()).status()

    assert body["enabled"] is True
    assert body["available"] is False
    assert "boom" in body["message"]


def test_get_metrics_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Datapoints normalize into MetricRecords with source=cloudwatch."""
    now = datetime.now(timezone.utc)
    fake = _FakeBotoClient([_point(now, 42.5), {"Timestamp": now, "Unit": "Percent"}])
    monkeypatch.setattr(client_module, "build_client", lambda config: fake)

    records = CloudWatchService(_config()).get_metrics(metric_name="CPUUtilization")

    # The second datapoint lacks "Average" and is skipped.
    assert len(records) == 1
    record = records[0]
    assert record.source == "cloudwatch"
    assert record.metric_name == "CPUUtilization"
    assert record.value == 42.5
    assert record.unit == "Percent"
    assert record.resource_id == "i-123"
    assert record.metadata["namespace"] == "AWS/EC2"
    assert record.metadata["statistic"] == "Average"
    assert record.timestamp == now


def test_get_metrics_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """No datapoints means no records (never invented data)."""
    monkeypatch.setattr(
        client_module, "build_client", lambda config: _FakeBotoClient([])
    )

    assert CloudWatchService(_config()).get_metrics() == []


def test_get_metrics_disabled() -> None:
    """Disabled integrations refuse retrieval with a structured error."""
    with pytest.raises(CloudWatchDisabledError):
        CloudWatchService(CloudWatchConfig(aws_enabled=False)).get_metrics()


def test_get_metrics_unknown_metric() -> None:
    """Unknown metric names are rejected before any AWS call."""
    with pytest.raises(CloudWatchConfigError, match="unsupported metric"):
        CloudWatchService(_config()).get_metrics(metric_name="Nope")


def test_get_metrics_unknown_statistic() -> None:
    """Unknown statistics are rejected before any AWS call."""
    with pytest.raises(CloudWatchConfigError, match="unsupported statistic"):
        CloudWatchService(_config()).get_metrics(statistic="P99")


def test_get_metrics_missing_resource() -> None:
    """Without a resource the service asks for configuration, not data."""
    with pytest.raises(CloudWatchConfigError, match="no resource"):
        CloudWatchService(_config(cloudwatch_dimension_value="")).get_metrics()


def test_get_metrics_bad_lookback() -> None:
    """Non-positive lookbacks are rejected."""
    with pytest.raises(CloudWatchAWSError):
        CloudWatchService(_config()).get_metrics(lookback_minutes=-3)


def test_get_metrics_aws_error_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """AWS-side failures surface as structured errors."""
    monkeypatch.setattr(
        client_module,
        "build_client",
        lambda config: _FakeBotoClient(error=_client_error()),
    )

    with pytest.raises(CloudWatchAWSError) as exc:
        CloudWatchService(_config()).get_metrics()

    assert exc.value.aws_code == "AccessDenied"


def test_demo_records_are_clearly_marked() -> None:
    """Demo records use source=cloudwatch_demo across the window."""
    before = datetime.now(timezone.utc)
    records = CloudWatchService(_config()).get_metrics(
        metric_name="CPUUtilization", demo=True
    )
    after = datetime.now(timezone.utc)

    assert len(records) == 5
    assert all(r.source == "cloudwatch_demo" for r in records)
    assert all(r.metadata.get("mode") == "demo" for r in records)
    assert records[0].timestamp <= records[-1].timestamp <= after
    assert (after - records[0].timestamp).total_seconds() == pytest.approx(
        600.0, abs=5.0
    )


def test_normalize_datapoint_with_dimensions() -> None:
    """Raw dimension entries are preserved in labels."""
    now = datetime.now(timezone.utc)
    record = CloudWatchService.normalize_datapoint(
        {
            "Timestamp": now,
            "Average": 7.5,
            "Unit": "Bytes",
            "Dimensions": [{"Name": "InstanceId", "Value": "i-9"}],
        },
        namespace="AWS/EC2",
        metric_name="NetworkIn",
        resource_id="i-9",
        statistic="Average",
    )

    assert record.labels == {"InstanceId": "i-9"}
    assert record.value == 7.5


def test_metric_record_rejects_unknown_source() -> None:
    """Only known sources are representable (demo can never pose as real)."""
    with pytest.raises(ValidationError):
        MetricRecord(
            timestamp=datetime.now(timezone.utc),
            source="cloudwatch_real",  # type: ignore[arg-type]
            metric_name="CPUUtilization",
            value=1.0,
        )