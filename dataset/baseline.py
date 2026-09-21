"""Baseline metrics for telemetry signals.

A baseline summarises what "normal" looks like for a monitored signal over a
reference period. Later milestones (anomaly detection) will compare incoming
telemetry against these baselines.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SignalBaseline:
    """Statistical baseline for a single telemetry signal."""

    name: str
    count: int
    missing_rate: float
    mean: float
    std: float
    median: float
    min: float
    max: float
    p5: float
    p95: float

    def to_dict(self) -> dict:
        """Return the baseline as a plain dictionary."""
        return {
            "name": self.name,
            "count": self.count,
            "missing_rate": self.missing_rate,
            "mean": self.mean,
            "std": self.std,
            "median": self.median,
            "min": self.min,
            "max": self.max,
            "p5": self.p5,
            "p95": self.p95,
        }


def compute_signal_baseline(series: pd.Series) -> SignalBaseline:
    """Compute baseline statistics for a single numeric signal.

    Args:
        series: A numeric pandas Series. Non-numeric values are dropped;
            missing values are counted but excluded from statistics.

    Returns:
        A :class:`SignalBaseline` for the signal.

    Raises:
        ValueError: If the series contains no numeric values.
    """
    name = str(series.name) if series.name is not None else "signal"
    numeric = pd.to_numeric(series, errors="coerce")
    valid = numeric.dropna()

    if valid.empty:
        raise ValueError(f"Signal '{name}' has no numeric values; cannot build a baseline")

    return SignalBaseline(
        name=name,
        count=int(len(valid)),
        missing_rate=float(numeric.isna().mean()),
        mean=float(valid.mean()),
        std=float(valid.std(ddof=0)),
        median=float(valid.median()),
        min=float(valid.min()),
        max=float(valid.max()),
        p5=float(valid.quantile(0.05)),
        p95=float(valid.quantile(0.95)),
    )


def compute_baselines(
    df: pd.DataFrame,
    columns: list[str] | None = None,
) -> dict[str, SignalBaseline]:
    """Compute baselines for every numeric column in ``df``.

    Args:
        df: Telemetry as a DataFrame (one column per signal).
        columns: Optional subset of columns to baseline. Defaults to all
            numeric columns.

    Returns:
        A mapping of signal name to :class:`SignalBaseline`.
    """
    if columns is None:
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    else:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise KeyError(f"Columns not found in DataFrame: {missing}")
        numeric_columns = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]

    return {col: compute_signal_baseline(df[col]) for col in numeric_columns}


def baseline_summary(
    df: pd.DataFrame, columns: list[str] | None = None
) -> pd.DataFrame:
    """Return baselines as a tidy summary DataFrame."""
    baselines = compute_baselines(df, columns)
    if not baselines:
        return pd.DataFrame()
    return pd.DataFrame([b.to_dict() for b in baselines.values()]).set_index("name")