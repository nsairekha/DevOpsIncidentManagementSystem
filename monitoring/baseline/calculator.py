"""Pure statistical calculations for the baseline engine.

All functions operate on plain float lists (NaN already removed) so the
math stays dependency-light; pandas/numpy are used for percentiles. No
meaningless statistics: single-observation series report zero spread, and
empty series raise instead of returning zeros.
"""

import statistics

import numpy as np

from monitoring.baseline.models import BaselineRecord


def clean_values(values: list[float | None]) -> list[float]:
    """Drop missing observations (None/NaN); never silently substitute zero."""
    cleaned = []
    for value in values:
        if value is None:
            continue
        number = float(value)
        if number != number:  # NaN check without importing math
            continue
        cleaned.append(number)
    return cleaned


def percentiles(values: list[float]) -> tuple[float, float, float]:
    """Return (P50, P95, P99) with linear interpolation.

    P50 is the median of the distribution; mean latency and P95/P99 latency
    are deliberately different numbers — averages hide tail behavior while
    percentiles expose it, which is why latency SLOs use P95/P99.
    """
    arr = np.asarray(values, dtype=float)
    return (
        float(np.percentile(arr, 50)),
        float(np.percentile(arr, 95)),
        float(np.percentile(arr, 99)),
    )


def normal_bounds(
    mean: float, standard_deviation: float, multiplier: float, minimum: float
) -> tuple[float, float]:
    """Return ``(lower, upper)`` = mean ± multiplier × std.

    When every observation is non-negative (``minimum >= 0``), the lower
    bound is clamped at 0: utilizations, byte counts, and latencies cannot
    be negative, so a negative bound would be an invalid range.
    """
    lower = mean - multiplier * standard_deviation
    if minimum >= 0:
        lower = max(0.0, lower)
    return lower, mean + multiplier * standard_deviation


def deviation(current_value: float, mean: float) -> tuple[float, float]:
    """Return ``(deviation_from_mean, deviation_percentage)``.

    A zero mean yields 0.0 % instead of a division-by-zero error: with no
    baseline level, a relative deviation is undefined.
    """
    absolute = current_value - mean
    if mean == 0:
        return absolute, 0.0
    return absolute, (absolute / mean) * 100.0


def compute_baseline(
    *,
    metric_name: str,
    source: str,
    values: list[float],
    service_name: str | None = None,
    resource_id: str | None = None,
    labels: dict[str, str] | None = None,
    rolling_window: int = 20,
    stddev_multiplier: float = 3.0,
) -> BaselineRecord:
    """Calculate the full baseline for one chronological value series.

    Args:
        values: Oldest-first observations (NaN already removed).
        rolling_window: How many of the latest observations feed the
            moving average / rolling standard deviation.
        stddev_multiplier: Normal bounds are mean ± multiplier × std.

    Raises:
        ValueError: If no usable observations remain.
    """
    cleaned = clean_values(values)
    if not cleaned:
        raise ValueError(f"metric '{metric_name}' has no usable observations")

    mean = statistics.fmean(cleaned)
    median = statistics.median(cleaned)
    minimum = min(cleaned)
    maximum = max(cleaned)
    standard_deviation = (
        statistics.pstdev(cleaned) if len(cleaned) > 1 else 0.0
    )
    p50, p95, p99 = percentiles(cleaned)

    window = cleaned[-rolling_window:] if rolling_window > 0 else cleaned
    moving_average = statistics.fmean(window)
    rolling_standard_deviation = (
        statistics.pstdev(window) if len(window) > 1 else 0.0
    )

    lower, upper = normal_bounds(mean, standard_deviation, stddev_multiplier, minimum)
    current_value = cleaned[-1]
    absolute, percentage = deviation(current_value, mean)

    return BaselineRecord(
        metric_name=metric_name,
        service_name=service_name,
        source=source,
        resource_id=resource_id,
        labels=dict(labels or {}),
        observation_count=len(cleaned),
        mean=mean,
        median=median,
        minimum=minimum,
        maximum=maximum,
        standard_deviation=standard_deviation,
        p50=p50,
        p95=p95,
        p99=p99,
        moving_average=moving_average,
        rolling_standard_deviation=rolling_standard_deviation,
        normal_lower_bound=lower,
        normal_upper_bound=upper,
        current_value=current_value,
        deviation_from_mean=absolute,
        deviation_percentage=percentage,
    )