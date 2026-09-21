"""Validation checks producing useful, actionable error messages.

Per-record checks: timestamp type, finite numeric value (missing values are
reported, never zero-filled), known source, non-empty metric name.
Series checks: chronological ordering, exact duplicates, missing values.

NaN/None values are reported as issues and excluded downstream — they are
never silently replaced with zero, which would corrupt baselines.
"""

from datetime import datetime

from pydantic import BaseModel

from monitoring.models.metric import KNOWN_SOURCES, MetricRecord


class ValidationIssue(BaseModel):
    """One data quality finding."""

    check: str
    message: str
    metric_name: str | None = None
    index: int | None = None


def _is_missing(value: float) -> bool:
    return value != value  # NaN is the only float unequal to itself


def validate_record(record: MetricRecord, index: int | None = None) -> list[ValidationIssue]:
    """Run per-record checks on a single record."""
    issues: list[ValidationIssue] = []
    if not isinstance(record.timestamp, datetime):
        issues.append(
            ValidationIssue(
                check="valid_timestamp",
                message=f"record has non-datetime timestamp: {record.timestamp!r}",
                metric_name=record.metric_name,
                index=index,
            )
        )
    if not isinstance(record.value, (int, float)) or _is_missing(float(record.value)):
        issues.append(
            ValidationIssue(
                check="missing_value",
                message=f"record has missing/non-numeric value: {record.value!r}",
                metric_name=record.metric_name,
                index=index,
            )
        )
    if record.source not in KNOWN_SOURCES:
        issues.append(
            ValidationIssue(
                check="known_source",
                message=f"unknown source '{record.source}'; expected one of {', '.join(KNOWN_SOURCES)}",
                metric_name=record.metric_name,
                index=index,
            )
        )
    if not record.metric_name or not record.metric_name.strip():
        issues.append(
            ValidationIssue(
                check="valid_metric_name",
                message="record has an empty metric name",
                metric_name=record.metric_name,
                index=index,
            )
        )
    return issues


def validate_ordering(records: list[MetricRecord]) -> list[ValidationIssue]:
    """Report records that arrive out of chronological order."""
    issues: list[ValidationIssue] = []
    for position in range(1, len(records)):
        if records[position].timestamp < records[position - 1].timestamp:
            issues.append(
                ValidationIssue(
                    check="chronological_ordering",
                    message=(
                        f"record at position {position} "
                        f"({records[position].timestamp.isoformat()}) precedes "
                        f"position {position - 1} "
                        f"({records[position - 1].timestamp.isoformat()})"
                    ),
                    metric_name=records[position].metric_name,
                    index=position,
                )
            )
    return issues


def find_duplicates(records: list[MetricRecord]) -> list[ValidationIssue]:
    """Report exact duplicate observations (same identity, timestamp, value)."""
    seen: dict[tuple, int] = {}
    issues: list[ValidationIssue] = []
    for position, record in enumerate(records):
        key = (
            record.timestamp,
            record.source,
            record.service_name,
            record.metric_name,
            record.resource_id,
            tuple(sorted(record.labels.items())),
            record.value,
        )
        if key in seen:
            issues.append(
                ValidationIssue(
                    check="duplicate_records",
                    message=(
                        f"record at position {position} duplicates position "
                        f"{seen[key]} for metric '{record.metric_name}'"
                    ),
                    metric_name=record.metric_name,
                    index=position,
                )
            )
        else:
            seen[key] = position
    return issues


def validate_records(records: list[MetricRecord]) -> list[ValidationIssue]:
    """Run all checks (per-record, ordering, duplicates) in record order."""
    issues: list[ValidationIssue] = []
    for position, record in enumerate(records):
        issues.extend(validate_record(record, index=position))
    issues.extend(validate_ordering(records))
    issues.extend(find_duplicates(records))
    return issues