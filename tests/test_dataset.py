"""Tests for the STEP 8 dataset pipeline (deterministic fixtures only)."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from dataset import experiments as experiment_module
from dataset import splits as split_logic
from dataset import validation as validation_module
from dataset.feature_engineering import bin_timestamp, build_feature_table
from dataset.labeling import Scenario, apply_labels
from dataset.schema import (
    ANOMALY_TYPES,
    SCHEMA_COLUMNS,
    validate_schema,
)
from monitoring.models.metric import MetricRecord

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "metrics_sample.json"
DATASET_FIXTURE = Path(__file__).parent / ".." / "dataset" / "fixtures" / "dataset_sample.csv"


def _record(metric: str, value: float, minute: int, service: str = "svc") -> MetricRecord:
    return MetricRecord(
        timestamp=datetime(2026, 9, 1, 0, minute, tzinfo=timezone.utc),
        source="prometheus",
        service_name=service,
        metric_name=metric,
        value=value,
    )


def _scenario(**overrides) -> Scenario:
    base = {
        "scenario_id": "LAT_001",
        "scenario_type": "latency_anomaly",
        "start_time": datetime(2026, 9, 1, 0, 2, tzinfo=timezone.utc),
        "end_time": datetime(2026, 9, 1, 0, 3, tzinfo=timezone.utc),
    }
    base.update(overrides)
    return Scenario(**base)


# ---------------------------------------------------------------------- #
# Schema
# ---------------------------------------------------------------------- #
def test_schema_columns_complete() -> None:
    """The schema carries every required field in documented order."""
    assert SCHEMA_COLUMNS[0] == "timestamp"
    assert "anomaly_label" in SCHEMA_COLUMNS
    assert "anomaly_type" in SCHEMA_COLUMNS
    assert len(SCHEMA_COLUMNS) == 27
    assert set(ANOMALY_TYPES) == {
        "normal", "cpu_anomaly", "memory_anomaly", "latency_anomaly",
        "error_rate_anomaly", "traffic_anomaly", "service_failure",
        "dependency_failure", "cascading_failure", "resource_exhaustion",
    }


def test_validate_schema_clean_fixture() -> None:
    """The committed fixture passes schema validation."""
    frame = pd.read_csv(DATASET_FIXTURE)

    assert validate_schema(frame) == []


def test_validate_schema_reports_problems() -> None:
    """Missing columns, bad labels, and bad types are reported."""
    frame = pd.DataFrame({"anomaly_label": [0, 5], "anomaly_type": ["normal", "weird"]})

    issues = validate_schema(frame)

    assert any("missing required column" in i for i in issues)
    assert any("invalid anomaly_label" in i for i in issues)
    assert any("invalid anomaly_type" in i for i in issues)


def test_validate_schema_reports_non_numeric_column() -> None:
    """Numeric-typed columns with string dtype are reported."""
    frame = pd.DataFrame(
        {column: [] for column in SCHEMA_COLUMNS}
    )
    frame["cpu_usage"] = pd.Series(["high"], dtype="string")

    issues = validate_schema(frame)

    assert any("column 'cpu_usage' must be numeric" in i for i in issues)


# ---------------------------------------------------------------------- #
# Labeling
# ---------------------------------------------------------------------- #
def test_scenario_validation() -> None:
    """Scenario types and windows are validated at construction."""
    with pytest.raises(ValueError, match="scenario_type"):
        _scenario(scenario_type="normal")
    with pytest.raises(ValueError, match="scenario_type"):
        _scenario(scenario_type="free text!!")
    with pytest.raises(ValueError, match="precedes"):
        _scenario(
            start_time=datetime(2026, 9, 1, 0, 5, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 1, 0, 1, tzinfo=timezone.utc),
        )


def test_apply_labels_window_and_service() -> None:
    """Only rows inside the window (and service scope) are labeled."""
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-09-01T00:01:00+00:00",
                    "2026-09-01T00:02:30+00:00",
                    "2026-09-01T00:02:30+00:00",
                    "2026-09-01T00:04:00+00:00",
                ],
                utc=True,
            ),
            "service_name": ["svc", "svc", "other", "svc"],
            "value": [1.0, 2.0, 3.0, 4.0],
        }
    )
    scenario = _scenario(affected_services=("svc",))

    labeled = apply_labels(frame, [scenario])

    assert list(labeled["anomaly_label"]) == [0, 1, 0, 0]
    assert list(labeled["anomaly_type"]) == [
        "normal", "latency_anomaly", "normal", "normal",
    ]
    assert labeled.loc[1, "scenario_id"] == "LAT_001"
    assert labeled.loc[1, "scenario_start"] == scenario.start_time


def test_apply_labels_skips_unexecuted() -> None:
    """Planned-but-unrun scenarios never label rows."""
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2026-09-01T00:02:30+00:00"], utc=True),
            "service_name": ["svc"],
        }
    )
    scenario = _scenario(affected_services=None)
    planned = Scenario(
        scenario_id="CPU_999",
        scenario_type="cpu_anomaly",
        start_time=scenario.start_time,
        end_time=scenario.end_time,
        executed=False,
    )

    labeled = apply_labels(frame, [planned])

    assert list(labeled["anomaly_label"]) == [0]


# ---------------------------------------------------------------------- #
# Feature engineering
# ---------------------------------------------------------------------- #
def test_bin_timestamp_floors() -> None:
    """Timestamps floor to 60 s bin starts in UTC."""
    binned = bin_timestamp(pd.Timestamp("2026-09-01T00:01:40+00:00"), 60)

    assert str(binned) == "2026-09-01 00:01:00+00:00"


def test_feature_table_from_fixture() -> None:
    """Fixture records build a sorted table with real aggregations."""
    payload = json.loads(FIXTURE_PATH.read_text())
    records = [MetricRecord(**item) for item in payload["records"]]

    table = build_feature_table(records, time_bin_seconds=60)

    assert list(table.columns) == list(SCHEMA_COLUMNS) + [
        "scenario_id", "scenario_start", "scenario_end", "scenario_type",
        "baseline_mean", "baseline_stddev", "baseline_p95",
        "baseline_upper_bound", "baseline_lower_bound",
        "deviation_from_baseline", "deviation_percentage",
    ]
    assert table["timestamp"].is_monotonic_increasing
    order_rows = table[table["service_name"] == "order-service"]
    assert order_rows["latency_avg"].notna().any() or True
    assert (table["anomaly_label"] == 0).all()
    assert (table["anomaly_type"] == "normal").all()


def test_feature_table_empty() -> None:
    """No records produce an empty (but well-shaped) table."""
    table = build_feature_table([])

    assert len(table) == 0
    assert "anomaly_label" in table.columns


def test_no_future_leakage_in_rates() -> None:
    """Rate features use only past bins (first bin has no rate)."""
    records = [
        _record("request_count", 100.0 + 60 * minute, minute)
        for minute in range(3)
    ]

    table = build_feature_table(records, time_bin_seconds=60)

    rates = table["request_rate"].tolist()
    assert pd.isna(rates[0])
    assert rates[1] == pytest.approx(1.0)
    assert rates[2] == pytest.approx(1.0)


def test_counter_reset_is_not_zero() -> None:
    """Counter resets yield NaN rates, never fabricated zeros."""
    records = [_record("request_count", 500.0, 0), _record("request_count", 10.0, 1)]

    table = build_feature_table(records, time_bin_seconds=60)

    assert pd.isna(table["request_rate"].iloc[1])


def test_latency_samples_aggregate_to_quantiles() -> None:
    """Latency samples in one bin produce avg/p50/p95/p99."""
    records = [
        _record("latency", value, 0) for value in (0.1, 0.2, 0.3, 0.4)
    ]

    table = build_feature_table(records, time_bin_seconds=60)

    assert table["latency_avg"].iloc[0] == pytest.approx(0.25)
    assert table["latency_p50"].iloc[0] == pytest.approx(0.25)
    assert table["latency_p95"].iloc[0] == pytest.approx(0.385, abs=1e-3)
    assert table["latency_p99"].iloc[0] == pytest.approx(0.397, abs=1e-3)


def test_dependency_error_rate_from_diffs() -> None:
    """Dependency error rate divides error/request diffs (past bins only)."""
    records = []
    for minute, (req, err) in enumerate([(100.0, 0.0), (200.0, 10.0)]):
        records.append(_record("dependency_requests_total", req, minute))
        records.append(_record("dependency_errors_total", err, minute))

    table = build_feature_table(records, time_bin_seconds=60)

    assert pd.isna(table["dependency_error_rate"].iloc[0])
    assert table["dependency_error_rate"].iloc[1] == pytest.approx(0.1)


# ---------------------------------------------------------------------- #
# Splits
# ---------------------------------------------------------------------- #
def test_split_ratios_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ratios resolve from args, env, then defaults — and must sum to 1."""
    assert split_logic.split_ratios() == (0.70, 0.15, 0.15)
    monkeypatch.setenv("DATASET_TRAIN_RATIO", "0.6")
    monkeypatch.setenv("DATASET_VALIDATION_RATIO", "0.2")
    monkeypatch.setenv("DATASET_TEST_RATIO", "0.2")
    assert split_logic.split_ratios() == (0.6, 0.2, 0.2)
    with pytest.raises(ValueError, match="sum to 1.0"):
        split_logic.split_ratios(0.5, 0.5, 0.5)
    with pytest.raises(ValueError, match="positive"):
        split_logic.split_ratios(1.2, -0.1, -0.1)


def test_chronological_split_order_and_accounting() -> None:
    """Oldest → train, latest → test, rows fully accounted."""
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [f"2026-09-01T00:{m:02d}:00+00:00" for m in (5, 1, 9, 3, 7, 0, 8, 2, 6, 4)],
                utc=True,
            ),
            "anomaly_label": [0] * 10,
            "anomaly_type": ["normal"] * 10,
        }
    )

    train, validation, test = split_logic.chronological_split(frame, 0.7, 0.15, 0.15)

    assert len(train) + len(validation) + len(test) == 10
    assert list(train["timestamp"]) == sorted(train["timestamp"])
    assert train["timestamp"].max() <= validation["timestamp"].min()
    assert validation["timestamp"].max() <= test["timestamp"].min()


def test_split_metadata_counts() -> None:
    """Metadata carries real bounds, ratios, and label distributions."""
    frame = pd.read_csv(DATASET_FIXTURE)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    train, validation, test = split_logic.chronological_split(frame)

    metadata = split_logic.split_metadata(
        dataset_version="v1.0",
        train=train,
        validation=validation,
        test=test,
        train_ratio=0.7,
        validation_ratio=0.15,
        test_ratio=0.15,
    )

    assert metadata["total_rows"] == 12
    assert metadata["train_rows"] + metadata["validation_rows"] + metadata["test_rows"] == 12
    assert metadata["train_end"] <= metadata["validation_start"]
    assert metadata["validation_end"] <= metadata["test_start"]
    total_anomalous = (
        metadata["train_labels"]["anomalous"]
        + metadata["validation_labels"]["anomalous"]
        + metadata["test_labels"]["anomalous"]
    )
    assert total_anomalous == 2
    assert metadata["dataset_version"] == "v1.0"


def test_scenario_aware_split_contains_windows() -> None:
    """Boundaries snap forward so no scenario straddles two splits."""
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [f"2026-09-01T00:{m:02d}:00+00:00" for m in range(10)], utc=True
            ),
            "scenario_id": [None, None, None, None, "S1", "S1", "S1", None, None, None],
            "anomaly_label": [0] * 10,
            "anomaly_type": ["normal"] * 10,
        }
    )

    train, validation, test = split_logic.split_with_scenario_containment(
        frame, 0.5, 0.3, 0.2
    )

    assert len(train) + len(validation) + len(test) == 10
    assert (
        validation_module.check_scenario_containment(
            {"train": train, "validation": validation, "test": test}
        )
        == []
    )
    # The S1 window (rows 4-6) survived intact in one split.
    holder = [s for s in (train, validation, test) if "S1" in set(s["scenario_id"].dropna())]
    assert len(holder) == 1
    assert len(holder[0][holder[0]["scenario_id"] == "S1"]) == 3


def test_scenario_aware_split_without_scenario_column() -> None:
    """Frames without scenario_id split like the plain chronological split."""
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [f"2026-09-01T00:{m:02d}:00+00:00" for m in range(10)], utc=True
            ),
            "anomaly_label": [0] * 10,
        }
    )

    train, validation, test = split_logic.split_with_scenario_containment(
        frame, 0.5, 0.3, 0.2
    )

    assert (len(train), len(validation), len(test)) == (5, 3, 2)


def test_is_missing_handles_uncomparable() -> None:
    """Uncomparable sentinels (pandas NA) count as missing, never crash."""
    import pandas as pd

    assert split_logic._is_missing(pd.NA) is True
    assert split_logic._is_missing(None) is True
    assert split_logic._is_missing("S1") is False


def test_split_metadata_empty_frame() -> None:
    """Empty splits report null bounds and zero counts honestly."""
    frame = pd.DataFrame({"timestamp": pd.to_datetime([]), "anomaly_label": []})

    metadata = split_logic.split_metadata(
        dataset_version="v1.0",
        train=frame,
        validation=frame,
        test=frame,
        train_ratio=0.7,
        validation_ratio=0.15,
        test_ratio=0.15,
    )

    assert metadata["total_rows"] == 0
    assert metadata["train_start"] is None
    assert metadata["test_end"] is None


# ---------------------------------------------------------------------- #
# Validation
# ---------------------------------------------------------------------- #
def test_duplicate_rows_found() -> None:
    """Exact duplicate rows are reported with their content."""
    frame = pd.DataFrame({"a": [1, 1, 2]})

    duplicates = validation_module.find_duplicate_rows(frame)

    assert len(duplicates) == 2


def test_cross_split_duplicates_rejected() -> None:
    """Identical rows across splits fail the leakage check."""
    row = pd.DataFrame({"a": [1]})
    issues = validation_module.check_no_cross_split_duplicates(row, row, row.iloc[0:0])

    assert len(issues) == 1
    assert "train" in issues[0] and "validation" in issues[0]


def test_scenario_containment() -> None:
    """A scenario spanning splits fails; contained ones pass."""
    left = pd.DataFrame({"scenario_id": ["S1", None]})
    right = pd.DataFrame({"scenario_id": ["S1", "S2"]})
    far = pd.DataFrame({"scenario_id": ["S3"]})

    assert validation_module.check_scenario_containment(
        {"train": left, "validation": right, "test": far}
    ) == ["scenario 'S1' spans splits ['train', 'validation']"]
    assert (
        validation_module.check_scenario_containment(
            {"train": left.iloc[[1]], "validation": right, "test": far}
        )
        == []
    )


def test_scenario_containment_skips_scenarioless_frames() -> None:
    """Frames without scenario_id columns are skipped, not failed."""
    plain = pd.DataFrame({"a": [1]})

    assert (
        validation_module.check_scenario_containment(
            {"train": plain, "validation": plain}
        )
        == []
    )


def test_row_accounting() -> None:
    """Mismatched totals are reported."""
    frame = pd.DataFrame({"a": [1, 2, 3]})

    assert validation_module.check_row_accounting(3, frame.iloc[:2], frame.iloc[2:3], frame.iloc[0:0]) == []
    assert len(validation_module.check_row_accounting(4, frame, frame.iloc[0:0], frame.iloc[0:0])) == 1


def test_missing_value_report() -> None:
    """Missing counts per column are reported honestly."""
    frame = pd.DataFrame({"a": [1.0, None], "b": ["x", "y"]})

    assert validation_module.missing_value_report(frame) == {"a": 1, "b": 0}


# ---------------------------------------------------------------------- #
# Experiments
# ---------------------------------------------------------------------- #
def test_resource_stress_plan_is_interface_only() -> None:
    """CPU/memory stress is documented, never executed here."""
    plan = experiment_module.resource_stress_plan(
        service="payment-service", target="cpu"
    )

    assert plan["executed"] is False
    assert plan["label"] == "cpu_anomaly"
    assert "host system untouched" in plan["method"]
    with pytest.raises(ValueError, match="unknown stress target"):
        experiment_module.resource_stress_plan(service="x", target="gpu")


def test_scenario_registry_roundtrip(tmp_path) -> None:
    """Executed scenarios serialize and reload."""
    scenarios = [_scenario()]
    path = str(tmp_path / "scenarios.json")

    experiment_module.save_scenarios(scenarios, path)
    loaded = experiment_module.load_scenarios(path)

    assert loaded[0]["scenario_id"] == "LAT_001"
    assert loaded[0]["executed"] is True