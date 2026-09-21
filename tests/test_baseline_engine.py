"""Tests for the baseline calculator and service (controlled datasets)."""

from datetime import datetime, timezone

import pytest

from monitoring.baseline import calculator
from monitoring.baseline.service import BaselineConfig, BaselineService
from monitoring.models.metric import MetricRecord


def _records(values: list[float], **overrides) -> list[MetricRecord]:
    base = {
        "source": "prometheus",
        "service_name": "order-service",
        "metric_name": "latency",
    }
    base.update(overrides)
    return [
        MetricRecord(
            timestamp=datetime(2026, 9, 1, 0, minute, tzinfo=timezone.utc),
            value=value,
            **base,
        )
        for minute, value in enumerate(values)
    ]


def test_full_baseline_statistics() -> None:
    """Mean/median/min/max/std/percentiles match hand-computed values."""
    baseline = calculator.compute_baseline(
        metric_name="latency",
        source="prometheus",
        values=[10.0, 20.0, 30.0, 40.0],
    )

    assert baseline.mean == pytest.approx(25.0)
    assert baseline.median == pytest.approx(25.0)
    assert baseline.minimum == 10.0
    assert baseline.maximum == 40.0
    assert baseline.standard_deviation == pytest.approx(11.1803, abs=1e-3)
    assert baseline.p50 == pytest.approx(25.0)
    assert baseline.observation_count == 4
    assert baseline.current_value == 40.0


def test_percentile_helpers() -> None:
    """P50/P95/P99 use linear interpolation over 1..100."""
    p50, p95, p99 = calculator.percentiles([float(v) for v in range(1, 101)])

    assert p50 == pytest.approx(50.5)
    assert p95 == pytest.approx(95.05, abs=1e-6)
    assert p99 == pytest.approx(99.01, abs=1e-6)


def test_moving_average_and_rolling_std_use_window() -> None:
    """Only the latest N observations feed the rolling statistics."""
    baseline = calculator.compute_baseline(
        metric_name="m",
        source="prometheus",
        values=[0.0, 0.0, 0.0, 10.0, 20.0],
        rolling_window=2,
    )

    assert baseline.moving_average == pytest.approx(15.0)
    assert baseline.rolling_standard_deviation == pytest.approx(5.0)


def test_normal_bounds_default_three_sigma() -> None:
    """Bounds are mean ± 3σ by default (tight series stays positive)."""
    baseline = calculator.compute_baseline(
        metric_name="m", source="prometheus", values=[100.0, 101.0, 102.0, 103.0]
    )

    assert baseline.normal_lower_bound == pytest.approx(
        baseline.mean - 3 * baseline.standard_deviation
    )
    assert baseline.normal_upper_bound == pytest.approx(
        baseline.mean + 3 * baseline.standard_deviation
    )


def test_normal_bounds_clamped_for_non_negative() -> None:
    """All-non-negative series never report a negative lower bound."""
    baseline = calculator.compute_baseline(
        metric_name="cpu_utilization",
        source="cloudwatch",
        values=[1.0, 1.0, 1.0, 50.0],
    )

    assert baseline.normal_lower_bound == 0.0
    assert baseline.normal_upper_bound > 50.0


def test_normal_bounds_unclamped_for_signed_series() -> None:
    """Series containing negatives keep the raw statistical bound."""
    lower, upper = calculator.normal_bounds(0.0, 10.0, 3.0, minimum=-100.0)

    assert lower == pytest.approx(-30.0)
    assert upper == pytest.approx(30.0)


def test_deviation_and_percentage() -> None:
    """Deviation reports absolute and relative distance from the mean."""
    absolute, percentage = calculator.deviation(42.5, 35.2)

    assert absolute == pytest.approx(7.3)
    assert percentage == pytest.approx(20.74, abs=1e-2)


def test_deviation_zero_mean_is_safe() -> None:
    """Zero means yield 0% instead of a division-by-zero error."""
    absolute, percentage = calculator.deviation(5.0, 0.0)

    assert absolute == 5.0
    assert percentage == 0.0


def test_compute_baseline_end_to_end_deviation() -> None:
    """Current value, deviation, and percentage ride on the record."""
    baseline = calculator.compute_baseline(
        metric_name="cpu_utilization",
        source="cloudwatch",
        values=[35.2, 35.2, 35.2, 42.5],
        service_name="order-service",
    )

    assert baseline.current_value == 42.5
    assert baseline.deviation_from_mean == pytest.approx(42.5 - baseline.mean)
    assert baseline.metric_name == "cpu_utilization"
    assert baseline.service_name == "order-service"


def test_single_observation_has_zero_spread() -> None:
    """One observation reports value-backed center with zero spread."""
    baseline = calculator.compute_baseline(
        metric_name="m", source="prometheus", values=[7.0]
    )

    assert baseline.mean == 7.0
    assert baseline.median == 7.0
    assert baseline.standard_deviation == 0.0
    assert baseline.rolling_standard_deviation == 0.0
    assert baseline.p95 == 7.0


def test_empty_series_raises() -> None:
    """Empty datasets raise instead of returning fabricated statistics."""
    with pytest.raises(ValueError, match="no usable observations"):
        calculator.compute_baseline(
            metric_name="m", source="prometheus", values=[]
        )


def test_missing_values_dropped_not_zeroed() -> None:
    """None/NaN observations are dropped, never replaced with zero."""
    assert calculator.clean_values([1.0, None, float("nan"), 3.0]) == [1.0, 3.0]
    with pytest.raises(ValueError, match="no usable observations"):
        calculator.compute_baseline(
            metric_name="m", source="prometheus", values=[None, float("nan")]
        )


def test_config_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rolling window and multiplier come from the environment."""
    monkeypatch.setenv("BASELINE_ROLLING_WINDOW", "7")
    monkeypatch.setenv("BASELINE_STDDEV_MULTIPLIER", "2")

    config = BaselineConfig()

    assert config.rolling_window == 7
    assert config.stddev_multiplier == 2.0


def test_config_rejects_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-positive configuration values are rejected."""
    with pytest.raises(ValueError, match="BASELINE_ROLLING_WINDOW"):
        BaselineConfig(rolling_window=0)
    with pytest.raises(ValueError, match="BASELINE_STDDEV_MULTIPLIER"):
        BaselineConfig(stddev_multiplier=-1.0)


def test_service_groups_and_sorts_chronologically() -> None:
    """Groups split by identity; each group is oldest-first."""
    first = _records([2.0])[0].model_copy(
        update={"timestamp": datetime(2026, 9, 1, 0, 5, tzinfo=timezone.utc)}
    )
    second = _records([1.0])[0]
    other = _records([9.0], metric_name="other")[0]

    groups = BaselineService().group_records([first, second, other])

    assert len(groups) == 2
    ordered = [group for group in groups.values() if len(group) == 2][0]
    assert [r.value for r in ordered] == [1.0, 2.0]


def test_service_build_baseline() -> None:
    """One group produces one baseline carrying identity and stats."""
    baseline = BaselineService().build_baseline(_records([10.0, 20.0, 30.0]))

    assert baseline.metric_name == "latency"
    assert baseline.source == "prometheus"
    assert baseline.service_name == "order-service"
    assert baseline.mean == pytest.approx(20.0)
    assert baseline.observation_count == 3


def test_service_build_empty_raises() -> None:
    """Empty groups raise instead of fabricating."""
    with pytest.raises(ValueError, match="no records"):
        BaselineService().build_baseline([])


def test_service_build_all_skips_unusable() -> None:
    """Groups without usable values are skipped, valid ones kept."""
    service = BaselineService()
    good = _records([1.0, 2.0])
    bad = _records([float("nan")], metric_name="broken")

    baselines = service.build_all(good + bad)

    assert [b.metric_name for b in baselines] == ["latency"]