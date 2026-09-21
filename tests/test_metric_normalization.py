"""Tests for the canonical MetricRecord and normalization layers."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from monitoring.cloudwatch.models import MetricRecord as CloudWatchRecord
from monitoring.models.metric import MetricRecord
from monitoring.normalization import cloudwatch as cloudwatch_norm
from monitoring.normalization import prometheus as prometheus_norm
from monitoring.normalization.normalizer import (
    CANONICAL_NAMES,
    canonical_name,
    deduplicate,
    normalize,
    normalize_all,
)

FIXTURE = Path(__file__).parent / "fixtures" / "metrics_sample.json"


def _record(**overrides) -> MetricRecord:
    base = {
        "timestamp": datetime(2026, 9, 21, 10, 0, tzinfo=timezone.utc),
        "source": "prometheus",
        "service_name": "order-service",
        "metric_name": "request_count",
        "value": 1.0,
    }
    base.update(overrides)
    return MetricRecord(**base)


def test_metric_record_matches_spec_example() -> None:
    """The canonical record carries every documented field."""
    record = _record(
        metric_name="latency",
        value=0.42,
        unit="seconds",
        labels={"method": "POST", "endpoint": "/api/v1/orders"},
    )

    assert record.source == "prometheus"
    assert record.labels["endpoint"] == "/api/v1/orders"
    assert record.resource_id is None


def test_metric_record_rejects_bad_source() -> None:
    """Unknown sources are rejected at the model boundary."""
    with pytest.raises(ValidationError):
        _record(source="mystery")


def test_metric_record_rejects_empty_name() -> None:
    """Metric names must be non-empty."""
    with pytest.raises(ValidationError):
        _record(metric_name="")


def test_metric_record_identity_groups() -> None:
    """Identities match on source/service/metric/resource/labels (not value)."""
    first, second = _record(value=1.0), _record(value=2.0)

    assert first.identity() == second.identity()
    assert first.identity() != _record(metric_name="other").identity()


def test_fixture_is_labeled_test_data() -> None:
    """The shared fixture declares itself synthetic test data."""
    payload = json.loads(FIXTURE.read_text())

    assert "TEST FIXTURE" in payload["fixture"]
    assert len(payload["records"]) == 10


def test_prometheus_instant_vector() -> None:
    """Instant results become records with service extracted from labels."""
    results = [
        {
            "metric": {"__name__": "up", "service": "order-service", "method": "GET"},
            "value": [1726900000, "3"],
        },
        {"metric": {"job": "fallback"}, "value": [1726900000, "1"]},
        {"metric": {"service": "x"}, "value": [None, None]},
    ]

    records = prometheus_norm.from_instant_vector(results, "http_requests_total")

    assert len(records) == 2  # incomplete result skipped
    assert records[0].metric_name == "request_count"  # canonical mapping applied
    assert records[0].service_name == "order-service"
    assert records[0].labels == {"method": "GET"}  # __name__ never leaks
    assert records[0].metadata["query_type"] == "instant"
    assert records[1].service_name == "fallback"
    assert records[0].timestamp.tzinfo is not None


def test_prometheus_matrix() -> None:
    """Range results expand every sample into its own record."""
    results = [
        {
            "metric": {"service": "payment-service"},
            "values": [[1726900000, "0.1"], [1726900060, "0.2"]],
        }
    ]

    records = prometheus_norm.from_matrix(results, "http_request_duration_seconds")

    assert len(records) == 2
    assert records[0].metric_name == "latency"
    assert records[0].value == 0.1
    assert records[1].timestamp > records[0].timestamp


def test_cloudwatch_record_normalization() -> None:
    """CloudWatch-module records convert with source and mapping preserved."""
    source = CloudWatchRecord(
        timestamp=datetime(2026, 9, 21, 10, tzinfo=timezone.utc),
        source="cloudwatch",
        metric_name="CPUUtilization",
        value=42.5,
        unit="Percent",
        resource_id="i-xxxx",
        labels={"InstanceId": "i-xxxx"},
        metadata={"namespace": "AWS/EC2", "statistic": "Average"},
    )

    record = cloudwatch_norm.from_cloudwatch_record(source)

    assert record.source == "cloudwatch"
    assert record.metric_name == "cpu_utilization"
    assert record.value == 42.5
    assert record.resource_id == "i-xxxx"


def test_cloudwatch_demo_source_preserved() -> None:
    """Demo records keep source=cloudwatch_demo (never rewritten as real)."""
    source = CloudWatchRecord(
        timestamp=datetime(2026, 9, 21, 10, tzinfo=timezone.utc),
        source="cloudwatch_demo",
        metric_name="CPUUtilization",
        value=1.0,
    )

    assert cloudwatch_norm.from_cloudwatch_record(source).source == "cloudwatch_demo"


def test_cloudwatch_datapoint_normalization() -> None:
    """Raw datapoints convert with namespace/statistic metadata."""
    record = cloudwatch_norm.from_datapoint(
        {"Timestamp": datetime(2026, 9, 21, 10, tzinfo=timezone.utc),
         "Average": 42.5, "Unit": "Percent"},
        namespace="AWS/EC2",
        metric_name="CPUUtilization",
        resource_id="i-xxxx",
        statistic="Average",
    )

    assert record.source == "cloudwatch"
    assert record.metric_name == "cpu_utilization"
    assert record.metadata == {"namespace": "AWS/EC2", "statistic": "Average"}


def test_canonical_mapping_table() -> None:
    """Documented raw names map; unknown names pass through unchanged."""
    assert canonical_name("CPUUtilization") == "cpu_utilization"
    assert canonical_name("NetworkIn") == "network_in"
    assert canonical_name("http_requests_total") == "request_count"
    assert canonical_name("something_new") == "something_new"
    assert "cpu_utilization" in CANONICAL_NAMES.values()


def test_normalize_applies_mapping() -> None:
    """normalize() rewrites mapped names and copies the rest."""
    mapped = normalize(_record(metric_name="CPUUtilization"))
    unmapped = _record(metric_name="custom_thing")

    assert mapped.metric_name == "cpu_utilization"
    assert normalize(unmapped).metric_name == "custom_thing"
    assert normalize_all([_record(), unmapped])[0].metric_name == "request_count"


def test_deduplicate_keeps_legitimate_repeats() -> None:
    """Only fully identical observations are dropped."""
    first = _record(value=1.0)
    exact = _record(value=1.0)
    different_value = _record(value=2.0)
    different_time = _record(
        value=1.0, timestamp=datetime(2026, 9, 21, 11, 0, tzinfo=timezone.utc)
    )

    unique = deduplicate([first, exact, different_value, different_time])

    assert unique == [first, different_value, different_time]