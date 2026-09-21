"""Tests for the incident analysis agent."""

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from agents import AgentResult, Finding, IncidentAnalysisAgent
from ai import IQRDetector, ZScoreDetector
from dataset import compute_signal_baseline


def _reference_window(n: int = 60, seed: int = 0) -> pd.DataFrame:
    """Steady-state telemetry used for fitting the detector and baselines."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "cpu": 15.0 + rng.normal(0, 1.0, size=n),
            "memory": 128.0 + rng.normal(0, 4.0, size=n),
        }
    )


def _telemetry_with_anomaly(outliers: list[float] | None = None) -> pd.DataFrame:
    """A short window that contains a clear CPU spike."""
    index = pd.date_range("2026-01-01 10:00", periods=12, freq="min", tz="UTC")
    values = [14.5, 15.2, 14.8, 15.1, 15.0, 14.9, 15.3, 14.7, 15.0, 14.8, 15.1, 15.0]
    if outliers:
        for pos, val in outliers:
            values[pos] = val
    return pd.DataFrame(
        {
            "cpu": values,
            "memory": [128.0] * 12,
        },
        index=index,
    )


def _fitted_agent() -> IncidentAnalysisAgent:
    reference = _reference_window()
    detector = ZScoreDetector(threshold=3.0).fit(reference)
    baselines = {
        "cpu": compute_signal_baseline(reference["cpu"]),
        "memory": compute_signal_baseline(reference["memory"]),
    }
    return IncidentAnalysisAgent(detector, baselines)


def test_agent_flags_an_anomaly_with_structured_finding() -> None:
    """A clear spike yields one finding with signal, value, and severity."""
    agent = _fitted_agent()
    telemetry = _telemetry_with_anomaly(outliers=[(5, 100.0)])

    result = agent.analyze(telemetry)

    assert isinstance(result, AgentResult)
    assert result.n_findings >= 1

    finding = result.findings[0]
    assert isinstance(finding, Finding)
    assert finding.signal == "cpu"
    assert finding.value == pytest.approx(100.0)
    assert finding.severity == "high"
    assert finding.timestamp is not None
    assert finding.timestamp == telemetry.index[5].to_pydatetime()
    # Grounded against the fitted baseline's normal range.
    assert finding.expected_range[0] < 15.0 < finding.expected_range[1]
    assert "baseline mean" in finding.details


def test_agent_reports_no_anomalies_for_clean_window() -> None:
    """A window within the normal range produces no findings."""
    agent = _fitted_agent()
    telemetry = _telemetry_with_anomaly()

    result = agent.analyze(telemetry)

    assert result.n_findings == 0
    assert result.findings == ()
    assert "No anomalies" in result.summary


def test_agent_supports_iqr_detector() -> None:
    """The agent works with any BaseDetector implementation."""
    reference = _reference_window()
    detector = IQRDetector(k=1.5).fit(reference)
    agent = IncidentAnalysisAgent(detector)

    result = agent.analyze(_telemetry_with_anomaly(outliers=[(3, 100.0)]))

    assert result.n_findings >= 1
    assert result.findings[0].score > 0


def test_agent_handles_empty_and_non_numeric_input() -> None:
    """Empty or text-only telemetry yields an empty-but-valid result."""
    agent = _fitted_agent()

    empty = agent.analyze(pd.DataFrame())
    assert empty.n_findings == 0
    assert "No telemetry" in empty.summary

    text_only = agent.analyze(pd.DataFrame({"host": ["a", "b", "c"]}))
    assert text_only.n_findings == 0
    assert "No numeric signals" in text_only.summary


def test_agent_handles_plain_row_index() -> None:
    """Without a timestamp index, findings carry no timestamp."""
    agent = _fitted_agent()
    telemetry = _telemetry_with_anomaly(outliers=[(5, 100.0)])
    telemetry.index = pd.RangeIndex(len(telemetry))

    finding = agent.analyze(telemetry).findings[0]

    assert finding.timestamp is None


def test_agent_accepts_python_datetime_index() -> None:
    """Raw Python datetime index values are surfaced on findings."""
    agent = _fitted_agent()
    telemetry = _telemetry_with_anomaly(outliers=[(5, 100.0)])
    # Keep raw Python datetimes (object dtype) so the datetime branch is used.
    telemetry.index = pd.Index(
        [
            datetime(2026, 1, 1, 10, minute, tzinfo=timezone.utc)
            for minute in range(len(telemetry))
        ],
        dtype=object,
    )

    finding = agent.analyze(telemetry).findings[0]

    assert finding.timestamp == telemetry.index[5]


def test_agent_severity_thresholds() -> None:
    """Findings are labelled low/medium/high by standardized deviation."""
    reference = _reference_window()
    # Standard deviation ~1.0 for cpu, so deviations map directly to scores.
    detector = ZScoreDetector(threshold=0.01).fit(reference)
    agent = IncidentAnalysisAgent(
        detector,
        {"cpu": compute_signal_baseline(reference["cpu"])},
        medium_deviation=1.0,
        high_deviation=3.0,
    )

    low = agent.analyze(_telemetry_with_anomaly(outliers=[(0, 15.8)])).findings[0]
    assert low.severity == "low"

    medium = agent.analyze(_telemetry_with_anomaly(outliers=[(0, 17.0)])).findings[0]
    assert medium.severity == "medium"

    high = agent.analyze(_telemetry_with_anomaly(outliers=[(0, 20.0)])).findings[0]
    assert high.severity == "high"


def test_agent_rejects_bad_thresholds() -> None:
    with pytest.raises(ValueError, match="medium_deviation"):
        IncidentAnalysisAgent(ZScoreDetector(), medium_deviation=5.0, high_deviation=3.0)


def test_agent_result_serialises_to_dict() -> None:
    """AgentResult converts to a plain serialisable dictionary."""
    agent = _fitted_agent()
    result = agent.analyze(_telemetry_with_anomaly(outliers=[(5, 100.0)]))

    payload = result.as_dict()

    assert payload["n_findings"] == result.n_findings
    assert payload["findings"][0]["signal"] == "cpu"
    assert isinstance(payload["findings"][0]["timestamp"], str)
    assert isinstance(payload["findings"][0]["expected_range"], list)