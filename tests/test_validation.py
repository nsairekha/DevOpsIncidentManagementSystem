"""Tests for data quality validation."""

from datetime import datetime, timezone

from monitoring.models.metric import MetricRecord
from monitoring.validation.validators import (
    find_duplicates,
    validate_ordering,
    validate_record,
    validate_records,
)


def _record(**overrides) -> MetricRecord:
    base = {
        "timestamp": datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc),
        "source": "prometheus",
        "service_name": "order-service",
        "metric_name": "request_count",
        "value": 1.0,
    }
    base.update(overrides)
    return MetricRecord(**base)


def test_valid_record_has_no_issues() -> None:
    """A well-formed record passes every check."""
    assert validate_record(_record()) == []


def test_bad_timestamp_reported() -> None:
    """Non-datetime timestamps produce a useful message."""
    record = MetricRecord.model_construct(
        timestamp="yesterday",
        source="prometheus",
        metric_name="m",
        value=1.0,
    )

    issues = validate_record(record, index=3)

    assert len(issues) == 1
    assert issues[0].check == "valid_timestamp"
    assert issues[0].index == 3
    assert "yesterday" in issues[0].message


def test_missing_value_reported_not_zeroed() -> None:
    """NaN values are reported as missing."""
    record = MetricRecord.model_construct(
        timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc),
        source="prometheus",
        metric_name="m",
        value=float("nan"),
    )

    issues = validate_record(record)

    assert [issue.check for issue in issues] == ["missing_value"]
    assert "nan" in issues[0].message


def test_non_numeric_value_reported() -> None:
    """Non-numeric values are reported as missing."""
    record = MetricRecord.model_construct(
        timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc),
        source="prometheus",
        metric_name="m",
        value="lots",
    )

    issues = validate_record(record)

    assert [issue.check for issue in issues] == ["missing_value"]


def test_unknown_source_reported() -> None:
    """Sources outside the known set are reported (constructed past validation)."""
    record = MetricRecord.model_construct(
        timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc),
        source="mystery",
        metric_name="m",
        value=1.0,
    )

    issues = validate_record(record)

    assert [issue.check for issue in issues] == ["known_source"]
    assert "mystery" in issues[0].message


def test_empty_metric_name_reported() -> None:
    """Empty names are reported (constructed past validation for the check)."""
    record = MetricRecord.model_construct(
        timestamp=datetime(2026, 9, 1, tzinfo=timezone.utc),
        source="prometheus",
        metric_name="  ",
        value=1.0,
    )

    assert [issue.check for issue in validate_record(record)] == [
        "valid_metric_name"
    ]


def test_ordering_detects_regression() -> None:
    """Out-of-order timestamps are reported with positions."""
    first = _record()
    earlier = _record(
        timestamp=datetime(2026, 8, 31, 23, 59, tzinfo=timezone.utc)
    )

    issues = validate_ordering([first, earlier])

    assert len(issues) == 1
    assert issues[0].check == "chronological_ordering"
    assert issues[0].index == 1


def test_ordered_series_passes() -> None:
    """Chronological series produce no ordering issues."""
    assert validate_ordering([_record(), _record()]) == []


def test_duplicates_detected() -> None:
    """Exact repeats are reported; differing values are kept silently."""
    first = _record(value=1.0)
    repeat = _record(value=1.0)
    changed = _record(value=2.0)

    issues = find_duplicates([first, repeat, changed])

    assert len(issues) == 1
    assert issues[0].check == "duplicate_records"
    assert "duplicates position 0" in issues[0].message


def test_validate_records_aggregates() -> None:
    """The aggregate runner combines per-record, ordering, and duplicates."""
    first = _record()
    repeat = _record()  # exact duplicate of position 0

    issues = validate_records([first, repeat])

    assert [issue.check for issue in issues] == ["duplicate_records"]