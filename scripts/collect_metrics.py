"""Collect live metric observations into ``dataset/raw/`` (STEP 7).

1. Queries Prometheus instant vectors for a small fixed query set.
2. Normalizes them into MetricRecords (``source=prometheus``).
3. When CloudWatch is enabled, retrieves configured observations and
   normalizes them (``source=cloudwatch`` — never demo data).
4. Combines and stores the records as CSV (labels/metadata as JSON).

Usage::

    python scripts/collect_metrics.py [--prometheus-url URL] [--out PATH]
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring.cloudwatch.config import CloudWatchConfig
from monitoring.cloudwatch.service import CloudWatchService
from monitoring.models.metric import MetricRecord
from monitoring.normalization import cloudwatch as cloudwatch_norm
from monitoring.pipeline.collector import CollectorError, PrometheusCollector

#: (expr, record name, unit) instant queries collected by default.
DEFAULT_QUERIES: tuple[tuple[str, str, str | None], ...] = (
    ("up", "up", None),
    ("http_requests_total", "http_requests_total", "count"),
    ("http_request_duration_seconds", "http_request_duration_seconds", "seconds"),
    ("http_requests_in_progress", "http_requests_in_progress", "count"),
)

CSV_FIELDS = (
    "timestamp",
    "source",
    "service_name",
    "metric_name",
    "value",
    "unit",
    "resource_id",
    "labels_json",
    "metadata_json",
)


def collect_prometheus(
    base_url: str, client=None
) -> tuple[list[MetricRecord], str | None]:
    """Collect the default query set; returns ``(records, error)``."""
    collector = PrometheusCollector(base_url, client=client)
    records: list[MetricRecord] = []
    try:
        for expr, name, unit in DEFAULT_QUERIES:
            records.extend(collector.query(expr, name, unit))
    except CollectorError as exc:
        return [], exc.message
    return records, None


def collect_cloudwatch() -> tuple[list[MetricRecord], str | None]:
    """Collect one CloudWatch metric per supported name when enabled.

    Returns ``(records, note)`` where ``note`` explains why nothing was
    collected (disabled, unconfigured resource, AWS error).
    """
    service = CloudWatchService(CloudWatchConfig())
    if not service.config.aws_enabled:
        return [], "cloudwatch disabled (AWS_ENABLED=false)"
    collected: list[MetricRecord] = []
    notes: list[str] = []
    for metric_name in (
        "CPUUtilization",
        "NetworkIn",
        "NetworkOut",
    ):
        try:
            collected.extend(
                cloudwatch_norm.from_cloudwatch_records(
                    service.get_metrics(metric_name=metric_name)
                )
            )
        except Exception as exc:  # structured errors carry the reason
            notes.append(f"{metric_name}: {exc}")
    if not collected and not notes:
        notes.append("no datapoints returned")
    return collected, "; ".join(notes) if notes else None


def save_records_csv(records: list[MetricRecord], path: str) -> None:
    """Store records as CSV (labels/metadata serialized as JSON)."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CSV_FIELDS))
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "timestamp": record.timestamp.isoformat(),
                    "source": record.source,
                    "service_name": record.service_name or "",
                    "metric_name": record.metric_name,
                    "value": record.value,
                    "unit": record.unit or "",
                    "resource_id": record.resource_id or "",
                    "labels_json": json.dumps(record.labels, sort_keys=True),
                    "metadata_json": json.dumps(record.metadata, sort_keys=True),
                }
            )


def load_records_csv(path: str) -> list[MetricRecord]:
    """Load records previously stored with :func:`save_records_csv`."""
    records = []
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            records.append(
                MetricRecord(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    source=row["source"],
                    service_name=row["service_name"] or None,
                    metric_name=row["metric_name"],
                    value=float(row["value"]),
                    unit=row["unit"] or None,
                    resource_id=row["resource_id"] or None,
                    labels=json.loads(row["labels_json"] or "{}"),
                    metadata=json.loads(row["metadata_json"] or "{}"),
                )
            )
    return records


def default_output_path() -> str:
    """Timestamped default output under ``dataset/raw/``."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, "dataset", "raw", f"metrics_{stamp}.csv")


def main(argv: list[str] | None = None) -> int:
    """Entry point: collect from all sources and store one CSV."""
    parser = argparse.ArgumentParser(description="Collect metric observations")
    parser.add_argument(
        "--prometheus-url",
        default=os.environ.get("PROMETHEUS_URL", ""),
        help="Prometheus base URL (empty skips Prometheus)",
    )
    parser.add_argument("--out", default=None, help="Output CSV path")
    args = parser.parse_args(argv)

    records: list[MetricRecord] = []
    if args.prometheus_url:
        prom_records, error = collect_prometheus(args.prometheus_url)
        records.extend(prom_records)
        print(f"prometheus: {len(prom_records)} records" + (f" ({error})" if error else ""))
    else:
        print("prometheus: skipped (no PROMETHEUS_URL)")
    cloud_records, note = collect_cloudwatch()
    records.extend(cloud_records)
    print(f"cloudwatch: {len(cloud_records)} records" + (f" ({note})" if note else ""))

    out = args.out or default_output_path()
    save_records_csv(records, out)
    print(f"stored {len(records)} records in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())