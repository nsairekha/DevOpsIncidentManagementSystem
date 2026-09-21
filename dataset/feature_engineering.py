"""Feature engineering: MetricRecords → canonical feature table (STEP 8).

One row per (service, time bin). Bins sort oldest-first and every derived
feature uses only past-and-present data — a feature at time T never sees
T+1. Unavailable features stay NaN (documented, never invented):

- ``throughput`` mirrors ``request_rate`` (per-status success splits are not
  collected by the STEP 8 query set; documented approximation).
- ``error_rate`` / ``http_4xx`` / ``http_5xx`` stay NaN (no status-split
  counters collected yet).
- ``restart_count`` / ``timeout_count`` / ``retry_count`` stay NaN (no
  source yet).
- ``cloudwatch_metrics`` counts CloudWatch-sourced observations per bin.
- Baseline columns describe ``latency_avg`` (falling back to
  ``request_rate`` when latency is absent) via causal expanding statistics.
"""

import numpy as np
import pandas as pd

from dataset.schema import (
    BASELINE_COLUMNS,
    SCENARIO_COLUMNS,
    SCHEMA_COLUMNS,
)
from monitoring.models.metric import MetricRecord
from monitoring.normalization.normalizer import normalize_all

#: Canonical metric → feature column for last-value-in-bin aggregation.
LAST_VALUE_FEATURES: dict[str, str] = {
    "cpu_utilization": "cpu_usage",
    "memory_utilization": "memory_usage",
    "disk_utilization": "disk_usage",
    "disk_read_bytes": "disk_read_bytes",
    "disk_write_bytes": "disk_write_bytes",
    "network_in": "network_in",
    "network_out": "network_out",
    "network_packets_in": "network_packets_in",
    "network_packets_out": "network_packets_out",
    "up": "availability",
    "dependency_requests_total": "dependency_request_count",
    "dependency_errors_total": "_dep_errors_last",
}

FEATURE_DEFAULTS: dict[str, float | None] = {
    "anomaly_label": 0,
}


def bin_timestamp(timestamp: pd.Timestamp, bin_seconds: int) -> pd.Timestamp:
    """Floor a timestamp to its bin start (UTC)."""
    epoch = int(timestamp.timestamp())
    return pd.Timestamp(epoch - (epoch % bin_seconds), unit="s", tz="UTC")


def _service_key(record: MetricRecord) -> str:
    """Service identity: service name, else the resource id."""
    return record.service_name or f"resource:{record.resource_id or 'unknown'}"


def build_feature_table(
    records: list[MetricRecord], time_bin_seconds: int = 60
) -> pd.DataFrame:
    """Build the canonical feature table from normalized records."""
    columns = list(SCHEMA_COLUMNS + SCENARIO_COLUMNS + BASELINE_COLUMNS)
    if not records:
        return pd.DataFrame({column: [] for column in columns})

    normalized = normalize_all(records)
    frame = pd.DataFrame(
        [
            {
                "timestamp": record.timestamp,
                "service": _service_key(record),
                "source": record.source,
                "metric": record.metric_name,
                "value": record.value,
            }
            for record in normalized
        ]
    )
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    frame["bin"] = frame["timestamp"].apply(
        lambda ts: bin_timestamp(ts, time_bin_seconds)
    )
    frame = frame.sort_values(["service", "bin", "timestamp"]).reset_index(drop=True)

    rows: list[dict] = []
    for (service, bin_start), group in frame.groupby(["service", "bin"]):
        rows.append(_aggregate_bin(service, bin_start, group, time_bin_seconds))

    table = pd.DataFrame(rows)
    table = table.sort_values(["timestamp", "service_name"]).reset_index(drop=True)
    table = _add_rates(table, time_bin_seconds)
    table = _add_baseline_columns(table)
    table["anomaly_label"] = 0
    table["anomaly_type"] = "normal"
    for column in SCENARIO_COLUMNS:
        table[column] = None
    for column in columns:
        if column not in table.columns:
            table[column] = np.nan
    return table[columns]


def _aggregate_bin(service: str, bin_start: pd.Timestamp, group: pd.DataFrame, time_bin_seconds: int) -> dict:
    """Aggregate one (service, bin) group into a feature row."""
    row: dict = {
        "timestamp": bin_start,
        "service_name": service,
        "source": ",".join(sorted(group["source"].unique())),
    }
    by_metric = {name: sub["value"] for name, sub in group.groupby("metric")}
    for canonical, feature in LAST_VALUE_FEATURES.items():
        if canonical in by_metric:
            row[feature] = float(np.asarray(by_metric[canonical])[-1])
    if "latency" in by_metric:
        samples = np.asarray(by_metric["latency"], dtype=float)
        row["latency_avg"] = float(np.mean(samples))
        row["latency_p50"] = float(np.percentile(samples, 50))
        row["latency_p95"] = float(np.percentile(samples, 95))
        row["latency_p99"] = float(np.percentile(samples, 99))
    if "request_count" in by_metric:
        row["_request_count_last"] = float(np.asarray(by_metric["request_count"])[-1])
    cloudwatch_mask = group["source"] == "cloudwatch"
    row["cloudwatch_metrics"] = int(cloudwatch_mask.sum())
    return row


def _add_rates(table: pd.DataFrame, time_bin_seconds: int) -> pd.DataFrame:
    """Derive per-service rates from consecutive bins (past data only)."""
    table = table.copy()
    table["request_rate"] = np.nan
    table["throughput"] = np.nan
    table["dependency_error_rate"] = np.nan
    for service, group in table.groupby("service_name"):
        index = group.index
        if "_request_count_last" in group:
            counts = pd.to_numeric(group["_request_count_last"], errors="coerce")
            rate = counts.diff() / time_bin_seconds
            # Counter reset: unknown rate, never zero-filled.
            rate = rate.where((rate >= 0) | (rate.isna()), np.nan)
            table.loc[index, "request_rate"] = rate
            table.loc[index, "throughput"] = rate
        if "dependency_request_count" in group and "_dep_errors_last" in group:
            requests = pd.to_numeric(
                group["dependency_request_count"], errors="coerce"
            ).diff()
            errors = pd.to_numeric(group["_dep_errors_last"], errors="coerce").diff()
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = errors / requests
            ratio[(requests <= 0) | (requests.isna())] = np.nan
            table.loc[index, "dependency_error_rate"] = ratio
    table = table.drop(
        columns=[c for c in ("_request_count_last", "_dep_errors_last") if c in table.columns]
    )
    return table


def _add_baseline_columns(table: pd.DataFrame) -> pd.DataFrame:
    """Causal expanding baseline stats for latency (else request_rate).

    Expanding windows only ever see past-and-present rows, so no future
    information leaks into any row.
    """
    table = table.copy()
    signal = "latency_avg" if "latency_avg" in table else "request_rate"
    for column in BASELINE_COLUMNS:
        table[column] = np.nan
    for service, group in table.groupby("service_name"):
        index = group.index
        values = pd.to_numeric(group[signal], errors="coerce") if signal in group else pd.Series(np.nan, index=index)
        mean = values.expanding(min_periods=1).mean()
        std = values.expanding(min_periods=1).std().fillna(0.0)
        p95 = values.expanding(min_periods=1).quantile(0.95)
        upper = mean + 3.0 * std
        lower = (mean - 3.0 * std).clip(lower=0.0)
        current = values
        deviation = current - mean
        with np.errstate(divide="ignore", invalid="ignore"):
            percentage = deviation / mean * 100.0
        percentage[mean == 0] = 0.0
        table.loc[index, "baseline_mean"] = mean
        table.loc[index, "baseline_stddev"] = std
        table.loc[index, "baseline_p95"] = p95
        table.loc[index, "baseline_upper_bound"] = upper
        table.loc[index, "baseline_lower_bound"] = lower
        table.loc[index, "deviation_from_baseline"] = deviation
        table.loc[index, "deviation_percentage"] = percentage
    return table