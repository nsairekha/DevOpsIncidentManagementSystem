"""Baseline record: statistical behavior of one metric identity.

A baseline establishes statistical behavior only. Values outside the normal
bounds are reported as baseline *deviations* (``deviation_from_mean`` /
``deviation_percentage``); this step never classifies observations as
normal/anomaly/critical — later ML stages decide that.
"""

from pydantic import BaseModel


class BaselineRecord(BaseModel):
    """Statistical baseline for one (source, service, metric, resource, labels)."""

    metric_name: str
    service_name: str | None = None
    source: str
    resource_id: str | None = None
    labels: dict[str, str] = {}
    observation_count: int = 0
    mean: float
    median: float
    minimum: float
    maximum: float
    standard_deviation: float
    p50: float
    p95: float
    p99: float
    moving_average: float
    rolling_standard_deviation: float
    normal_lower_bound: float
    normal_upper_bound: float
    current_value: float
    deviation_from_mean: float
    deviation_percentage: float