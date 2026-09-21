"""Tests for baseline metric computation."""

import numpy as np
import pandas as pd
import pytest

from dataset import (
    SignalBaseline,
    baseline_summary,
    compute_baselines,
    compute_signal_baseline,
)


def test_signal_baseline_known_values() -> None:
    """Baseline statistics match hand-computed values."""
    series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], name="cpu")

    baseline = compute_signal_baseline(series)

    assert isinstance(baseline, SignalBaseline)
    assert baseline.name == "cpu"
    assert baseline.count == 5
    assert baseline.missing_rate == 0.0
    assert baseline.mean == pytest.approx(3.0)
    assert baseline.std == pytest.approx(np.sqrt(2.0))
    assert baseline.median == 3.0
    assert baseline.min == 1.0
    assert baseline.max == 5.0
    # Linear-interpolation quantiles over [1, 5].
    assert baseline.p5 == pytest.approx(1.2)
    assert baseline.p95 == pytest.approx(4.8)


def test_signal_baseline_handles_missing_values() -> None:
    """Missing values are counted but excluded from statistics."""
    series = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0], name="mem")

    baseline = compute_signal_baseline(series)

    assert baseline.count == 4
    assert baseline.missing_rate == pytest.approx(0.2)
    assert baseline.mean == pytest.approx(3.0)


def test_signal_baseline_unnameable_series() -> None:
    """Series without a name fall back to a default label."""
    baseline = compute_signal_baseline(pd.Series([1.0, 2.0, 3.0]))
    assert baseline.name == "signal"


def test_signal_baseline_raises_for_non_numeric() -> None:
    """A signal with no numeric values cannot be baselined."""
    with pytest.raises(ValueError, match="no numeric values"):
        compute_signal_baseline(pd.Series(["a", "b", "c"]))


def test_compute_baselines_skips_non_numeric_columns() -> None:
    """Only numeric columns are baselined; others are ignored."""
    df = pd.DataFrame(
        {
            "cpu": [1.0, 2.0, 3.0],
            "latency": [10.0, 20.0, 30.0],
            "host": ["a", "b", "c"],
        }
    )

    baselines = compute_baselines(df)

    assert set(baselines) == {"cpu", "latency"}


def test_compute_baselines_requires_existing_columns() -> None:
    """Requesting a column that does not exist raises KeyError."""
    df = pd.DataFrame({"cpu": [1.0, 2.0]})
    with pytest.raises(KeyError, match="not found"):
        compute_baselines(df, columns=["cpu", "nope"])


def test_compute_baselines_explicit_columns_filter_numeric_only() -> None:
    """An explicit column list keeps numeric columns and drops non-numeric ones."""
    df = pd.DataFrame(
        {"cpu": [1.0, 2.0, 3.0], "latency": [10.0, 20.0, 30.0], "host": ["a", "b", "c"]}
    )

    baselines = compute_baselines(df, columns=["cpu", "latency", "host"])

    assert set(baselines) == {"cpu", "latency"}


def test_baseline_summary_returns_dataframe() -> None:
    """Summary output is a tidy DataFrame keyed by signal name."""
    df = pd.DataFrame({"cpu": [1.0, 2.0, 3.0], "mem": [10.0, 20.0, 30.0]})

    summary = baseline_summary(df)

    assert list(summary.index) == ["cpu", "mem"]
    assert summary.loc["cpu", "mean"] == pytest.approx(2.0)
    assert summary.loc["mem", "p95"] == pytest.approx(29.0)


def test_baseline_summary_empty_for_no_numeric_data() -> None:
    """A DataFrame with no numeric columns yields an empty summary."""
    df = pd.DataFrame({"host": ["a", "b"]})
    assert baseline_summary(df).empty