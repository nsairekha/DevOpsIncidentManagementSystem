"""Incident analysis agent.

The agent consumes a telemetry window, runs a fitted anomaly detector over it,
and turns every flagged sample into a structured :class:`Finding`: it blames
the signal with the largest deviation, grounds the observation against the
per-signal baseline (or the window's own statistics), and assigns a severity.
"""

from datetime import datetime

import numpy as np
import pandas as pd

from agents.base import AgentResult, Finding
from ai.base import BaseDetector
from dataset.baseline import SignalBaseline


class IncidentAnalysisAgent:
    """Analyse a telemetry window and emit structured anomaly findings."""

    def __init__(
        self,
        detector: BaseDetector,
        baselines: dict[str, SignalBaseline] | None = None,
        *,
        medium_deviation: float = 3.0,
        high_deviation: float = 5.0,
    ) -> None:
        if not (0.0 < medium_deviation < high_deviation):
            raise ValueError("require 0 < medium_deviation < high_deviation")
        self.detector = detector
        self.baselines = baselines or {}
        self.medium_deviation = medium_deviation
        self.high_deviation = high_deviation

    def analyze(self, telemetry: pd.DataFrame) -> AgentResult:
        """Run the agent over a telemetry window.

        Args:
            telemetry: Metric samples, one column per signal. The index may be
                timestamps (used for `Finding.timestamp`) or plain row indices.

        Returns:
            An :class:`AgentResult` containing the structured findings.
        """
        if telemetry.empty:
            return AgentResult(findings=(), n_findings=0, summary="No telemetry to analyze.")

        numeric = telemetry.select_dtypes(include=[np.number])
        if numeric.empty:
            return AgentResult(
                findings=(), n_findings=0, summary="No numeric signals to analyze."
            )

        column_stats = {
            col: (float(numeric[col].mean()), float(numeric[col].std()))
            for col in numeric.columns
        }

        result = self.detector.predict(numeric)

        findings = []
        for rel_idx in np.flatnonzero(result.is_anomaly):
            row = numeric.iloc[int(rel_idx)]
            signal, value, std_deviation = self._worst_signal(row, column_stats)
            baseline = self.baselines.get(signal)
            expected_range = (baseline.p5, baseline.p95) if baseline else (None, None)

            findings.append(
                Finding(
                    signal=signal,
                    value=value,
                    expected_range=expected_range,
                    score=float(result.scores[int(rel_idx)]),
                    severity=self._severity(std_deviation),
                    timestamp=self._timestamp_at(telemetry, int(rel_idx)),
                    details=self._describe(signal, value, baseline, std_deviation),
                )
            )

        return AgentResult(
            findings=tuple(findings),
            n_findings=len(findings),
            summary=self._summarize(findings),
        )

    def _worst_signal(
        self, row: pd.Series, column_stats: dict[str, tuple[float, float]]
    ) -> tuple[str, float, float]:
        """Blame the signal with the largest standardized deviation in ``row``."""
        worst_signal = str(row.index[0])
        worst_value = float(row.iloc[0])
        worst_score = -np.inf
        for signal, value in row.items():
            score = self._signal_score(signal, value, column_stats)
            if score > worst_score:
                worst_signal, worst_value, worst_score = signal, float(value), score
        return worst_signal, worst_value, worst_score

    def _signal_score(
        self, signal: str, value: float, column_stats: dict[str, tuple[float, float]]
    ) -> float:
        """Standardized deviation of a value for one signal."""
        baseline = self.baselines.get(signal)
        if baseline is not None and baseline.std > 0:
            return abs(value - baseline.mean) / baseline.std
        mean, std = column_stats.get(signal, (0.0, 0.0))
        if std > 0:
            return abs(value - mean) / std
        return 0.0

    def _severity(self, score: float) -> str:
        if score >= self.high_deviation:
            return "high"
        if score >= self.medium_deviation:
            return "medium"
        return "low"

    @staticmethod
    def _timestamp_at(telemetry: pd.DataFrame, index: int) -> datetime | None:
        ts = telemetry.index[index]
        if isinstance(ts, pd.Timestamp):
            return ts.to_pydatetime()
        if isinstance(ts, datetime):
            return ts
        return None

    @staticmethod
    def _describe(
        signal: str, value: float, baseline: SignalBaseline | None, deviation: float
    ) -> str:
        if baseline is not None:
            return (
                f"signal '{signal}' observed {value:.3f} with baseline "
                f"mean {baseline.mean:.3f} ± {baseline.std:.3f} "
                f"(standardized deviation {deviation:.2f})"
            )
        return f"signal '{signal}' observed {value:.3f} (standardized deviation {deviation:.2f})"

    @staticmethod
    def _summarize(findings: list[Finding]) -> str:
        if not findings:
            return "No anomalies detected in the analyzed window."
        signals = ", ".join(sorted({f.signal for f in findings}))
        return f"Detected {len(findings)} anomalous sample(s) in signal(s): {signals}."