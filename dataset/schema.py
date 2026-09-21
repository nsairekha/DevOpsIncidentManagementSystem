"""Canonical tabular dataset schema (STEP 8).

One row = one (timestamp bin, service) observation. Required columns are
always present; unavailable features stay null/NaN per the missing-data
policy (documented in ``dataset/README.md``) — never invented.
"""

#: Required columns in canonical order.
SCHEMA_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "service_name",
    "source",
    "cpu_usage",
    "memory_usage",
    "disk_usage",
    "network_in",
    "network_out",
    "request_rate",
    "throughput",
    "latency_avg",
    "latency_p50",
    "latency_p95",
    "latency_p99",
    "error_rate",
    "http_4xx",
    "http_5xx",
    "availability",
    "restart_count",
    "timeout_count",
    "retry_count",
    "dependency_request_count",
    "dependency_latency",
    "dependency_error_rate",
    "cloudwatch_metrics",
    "anomaly_label",
    "anomaly_type",
)

#: Optional scenario-provenance columns (recorded for controlled experiments).
SCENARIO_COLUMNS: tuple[str, ...] = (
    "scenario_id",
    "scenario_start",
    "scenario_end",
    "scenario_type",
)

#: Optional baseline-derived columns (causal expanding statistics only).
BASELINE_COLUMNS: tuple[str, ...] = (
    "baseline_mean",
    "baseline_stddev",
    "baseline_p95",
    "baseline_upper_bound",
    "baseline_lower_bound",
    "deviation_from_baseline",
    "deviation_percentage",
)

#: Controlled anomaly-type vocabulary (no free-text labels).
ANOMALY_TYPES: tuple[str, ...] = (
    "normal",
    "cpu_anomaly",
    "memory_anomaly",
    "latency_anomaly",
    "error_rate_anomaly",
    "traffic_anomaly",
    "service_failure",
    "dependency_failure",
    "cascading_failure",
    "resource_exhaustion",
)

NORMAL_LABEL = 0
ANOMALOUS_LABEL = 1

#: Columns that must be numeric when present (null/NaN allowed).
NUMERIC_COLUMNS: tuple[str, ...] = tuple(
    col
    for col in SCHEMA_COLUMNS + BASELINE_COLUMNS
    if col
    not in (
        "timestamp",
        "service_name",
        "source",
        "anomaly_type",
        "scenario_id",
        "scenario_start",
        "scenario_end",
        "scenario_type",
    )
)


def validate_schema(df, *, check_labels: bool = True) -> list[str]:
    """Check a feature table against the schema; return issue messages.

    Checks: required columns present, anomaly labels in {0, 1},
    anomaly types within the controlled vocabulary. Dtypes are checked
    loosely (numeric columns must be numeric dtype; nulls allowed).
    """
    issues: list[str] = []
    columns = list(df.columns)
    for required in SCHEMA_COLUMNS:
        if required not in columns:
            issues.append(f"missing required column: {required}")
    if check_labels and "anomaly_label" in columns:
        bad_labels = set(df["anomaly_label"].dropna().unique()) - {
            NORMAL_LABEL,
            ANOMALOUS_LABEL,
        }
        if bad_labels:
            issues.append(f"invalid anomaly_label values: {sorted(bad_labels)}")
    if check_labels and "anomaly_type" in columns:
        bad_types = set(df["anomaly_type"].dropna().unique()) - set(ANOMALY_TYPES)
        if bad_types:
            issues.append(f"invalid anomaly_type values: {sorted(bad_types)}")
    for column in NUMERIC_COLUMNS:
        if column in columns and not _is_numeric_dtype(df[column]):
            issues.append(f"column '{column}' must be numeric")
    return issues


def _is_numeric_dtype(series) -> bool:
    import pandas as pd

    return pd.api.types.is_numeric_dtype(series.dtype)
