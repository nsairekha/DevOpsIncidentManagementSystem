"""Tests for collectors, the processor, and the collection scripts."""

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from monitoring.baseline.service import BaselineService
from monitoring.models.metric import MetricRecord
from monitoring.pipeline.collector import (
    CloudWatchCollector,
    CollectorError,
    PrometheusCollector,
)
from monitoring.pipeline.processor import MetricProcessor
from scripts import build_baselines, collect_metrics

FIXTURE = Path(__file__).parent / "fixtures" / "metrics_sample.json"


def _record(metric_name: str, value: float, minute: int = 0) -> MetricRecord:
    return MetricRecord(
        timestamp=datetime(2026, 9, 1, 0, minute, tzinfo=timezone.utc),
        source="prometheus",
        service_name="order-service",
        metric_name=metric_name,
        value=value,
    )


def _prometheus_api(result: list | dict, status: str = "success") -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": status, "data": {"result": result}})

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_prometheus_instant_query() -> None:
    """Instant vectors normalize into records with service labels."""
    client = _prometheus_api(
        [{"metric": {"service": "order-service"}, "value": [1726900000, "4"]}]
    )

    records = PrometheusCollector("http://prom:9090", client=client).query(
        "up", "up"
    )

    assert len(records) == 1
    assert records[0].service_name == "order-service"
    assert records[0].value == 4.0


def test_prometheus_range_query() -> None:
    """Range matrices expand into one record per sample."""
    client = _prometheus_api(
        [
            {
                "metric": {"service": "order-service"},
                "values": [[1726900000, "1"], [1726900060, "2"]],
            }
        ]
    )
    collector = PrometheusCollector("http://prom:9090", client=client)

    records = collector.query_range(
        "up",
        "up",
        datetime(2026, 9, 1, tzinfo=timezone.utc),
        datetime(2026, 9, 1, 0, 5, tzinfo=timezone.utc),
    )

    assert [r.value for r in records] == [1.0, 2.0]


def test_prometheus_transport_error() -> None:
    """Unreachable servers become CollectorError, not tracebacks."""
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    collector = PrometheusCollector(
        "http://prom:9090",
        client=httpx.Client(transport=httpx.MockTransport(refused)),
    )

    with pytest.raises(CollectorError) as exc:
        collector.query("up", "up")

    assert exc.value.source == "prometheus"


def test_prometheus_api_error_status() -> None:
    """API-level error payloads become CollectorError."""
    collector = PrometheusCollector(
        "http://prom:9090", client=_prometheus_api([], status="error")
    )

    with pytest.raises(CollectorError):
        collector.query("up", "up")


def test_prometheus_owned_client_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Collectors without an injected client own (and close) their client."""
    closed = {"value": False}
    transport_client = _prometheus_api(
        [{"metric": {}, "value": [1726900000, "1"]}]
    )
    original_close = transport_client.close

    def close() -> None:
        closed["value"] = True
        original_close()

    transport_client.close = close  # type: ignore[method-assign]
    monkeypatch.setattr(httpx, "Client", lambda timeout: transport_client)

    records = PrometheusCollector("http://prom:9090").query("up", "up")

    assert len(records) == 1
    assert closed["value"] is True


def test_cloudwatch_collector_delegates() -> None:
    """The collector normalizes whatever the CloudWatch service returns."""

    class _Service:
        def get_metrics(self, **kwargs):
            assert kwargs["metric_name"] == "CPUUtilization"
            return [
                MetricRecord(
                    timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc),
                    source="cloudwatch",
                    metric_name="CPUUtilization",
                    value=10.0,
                )
            ]

    records = CloudWatchCollector(_Service()).collect(metric_name="CPUUtilization")  # type: ignore[arg-type]

    assert len(records) == 1
    assert records[0].metric_name == "cpu_utilization"  # canonicalized


def test_processor_end_to_end_with_fixture() -> None:
    """The TEST FIXTURE processes into two baselines without issues."""
    payload = json.loads(FIXTURE.read_text())
    records = [MetricRecord(**item) for item in payload["records"]]

    baselines, issues = MetricProcessor(BaselineService()).process(records)

    # The fixture interleaves two identities, so one global ordering issue
    # is legitimately reported; grouping still yields both baselines.
    assert [issue.check for issue in issues] == ["chronological_ordering"]
    assert sorted(b.metric_name for b in baselines) == [
        "cpu_utilization",
        "request_count",
    ]
    by_name = {b.metric_name: b for b in baselines}
    assert by_name["request_count"].observation_count == 6
    assert by_name["request_count"].mean == pytest.approx(12.0)
    assert by_name["cpu_utilization"].observation_count == 4


def test_processor_flags_problems_and_sorts() -> None:
    """Duplicates/issues surface while usable data still gets baselines."""
    first = _record("latency", 1.0, minute=1)
    shuffled = _record("latency", 3.0, minute=0)
    repeat = _record("latency", 1.0, minute=1)

    baselines, issues = MetricProcessor().process([first, shuffled, repeat])

    assert [b.metric_name for b in baselines] == ["latency"]
    assert baselines[0].observation_count == 2  # duplicate dropped
    assert baselines[0].current_value == 1.0  # chronological: minute 1 last
    checks = {issue.check for issue in issues}
    assert "chronological_ordering" in checks
    assert "duplicate_records" in checks


def test_collect_prometheus_function() -> None:
    """The script helper collects the default query set."""
    client = _prometheus_api(
        [{"metric": {"service": "s"}, "value": [1726900000, "1"]}]
    )

    records, error = collect_metrics.collect_prometheus(
        "http://prom:9090", client=client
    )

    assert error is None
    assert len(records) == len(collect_metrics.DEFAULT_QUERIES)


def test_collect_prometheus_unreachable() -> None:
    """Unreachable Prometheus yields an explanatory note, not data."""
    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    records, error = collect_metrics.collect_prometheus(
        "http://prom:9090",
        client=httpx.Client(transport=httpx.MockTransport(refused)),
    )

    assert records == []
    assert error is not None


def test_collect_cloudwatch_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disabled CloudWatch explains itself without AWS calls."""
    monkeypatch.setenv("AWS_ENABLED", "false")

    records, note = collect_metrics.collect_cloudwatch()

    assert records == []
    assert "disabled" in (note or "")


def test_csv_roundtrip(tmp_path: Path) -> None:
    """Stored CSVs reload into identical records."""
    records = [_record("latency", 0.5), _record("latency", 0.7, minute=2)]
    path = str(tmp_path / "metrics.csv")

    collect_metrics.save_records_csv(records, path)
    reloaded = collect_metrics.load_records_csv(path)

    assert reloaded == records


def test_collect_main_writes_csv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """main() collects (mocked) and stores one CSV, returning 0."""
    records = [
        MetricRecord(
            timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc),
            source="prometheus",
            service_name="s",
            metric_name="up",
            value=1.0,
        )
    ]
    out = str(tmp_path / "out.csv")
    monkeypatch.setenv("PROMETHEUS_URL", "http://prom:9090")
    monkeypatch.setenv("AWS_ENABLED", "false")
    monkeypatch.setattr(
        collect_metrics, "collect_prometheus", lambda *a, **k: (records, None)
    )

    assert collect_metrics.main(["--out", out]) == 0
    assert collect_metrics.load_records_csv(out) == records


def test_build_baselines_end_to_end(tmp_path: Path) -> None:
    """The fixture builds file-backed baselines without ML labels."""
    payload = json.loads(FIXTURE.read_text())
    records = [MetricRecord(**item) for item in payload["records"]]

    baselines = build_baselines.build_baselines(records)
    out = str(tmp_path / "baselines.json")
    build_baselines.save_baselines_json(baselines, out)

    stored = json.loads(Path(out).read_text())
    assert sorted(b["metric_name"] for b in stored) == [
        "cpu_utilization",
        "request_count",
    ]
    assert all("anomaly" not in json.dumps(b).lower() for b in stored)


def test_build_main_roundtrip(tmp_path: Path) -> None:
    """main() with explicit paths stores baselines and returns 0."""
    payload = json.loads(FIXTURE.read_text())
    records = [MetricRecord(**item) for item in payload["records"]]
    input_path = str(tmp_path / "in.csv")
    output_path = str(tmp_path / "out.json")
    collect_metrics.save_records_csv(records, input_path)

    assert (
        build_baselines.main(["--in", input_path, "--out", output_path]) == 0
    )
    stored = json.loads(Path(output_path).read_text())
    assert len(stored) == 2