"""Baseline service: from MetricRecords to BaselineRecords.

Configuration comes from the environment (never hard-coded)::

    BASELINE_ROLLING_WINDOW=20
    BASELINE_STDDEV_MULTIPLIER=3

Records are grouped by identity (source, service, metric, resource, labels),
sorted oldest-first — time-series order is preserved, never shuffled — and
one baseline is calculated per group. The service is decoupled from
Prometheus/boto3: it only ever sees :class:`MetricRecord` objects.
"""

import os

from monitoring.baseline import calculator
from monitoring.baseline.models import BaselineRecord
from monitoring.models.metric import MetricRecord


class BaselineConfig:
    """Baseline engine configuration with environment overrides."""

    def __init__(
        self,
        rolling_window: int | None = None,
        stddev_multiplier: float | None = None,
    ) -> None:
        self.rolling_window = (
            rolling_window
            if rolling_window is not None
            else int(os.environ.get("BASELINE_ROLLING_WINDOW", "20"))
        )
        self.stddev_multiplier = (
            stddev_multiplier
            if stddev_multiplier is not None
            else float(os.environ.get("BASELINE_STDDEV_MULTIPLIER", "3"))
        )
        if self.rolling_window <= 0:
            raise ValueError("BASELINE_ROLLING_WINDOW must be positive")
        if self.stddev_multiplier <= 0:
            raise ValueError("BASELINE_STDDEV_MULTIPLIER must be positive")


class BaselineService:
    """Calculate baselines for groups of metric records."""

    def __init__(self, config: BaselineConfig | None = None) -> None:
        self.config = config or BaselineConfig()

    @staticmethod
    def group_records(
        records: list[MetricRecord],
    ) -> dict[tuple, list[MetricRecord]]:
        """Group records by identity, each group sorted oldest-first."""
        groups: dict[tuple, list[MetricRecord]] = {}
        for record in records:
            groups.setdefault(record.identity(), []).append(record)
        for group in groups.values():
            group.sort(key=lambda record: record.timestamp)
        return groups

    def build_baseline(self, records: list[MetricRecord]) -> BaselineRecord:
        """Calculate one baseline for a non-empty record group.

        Raises:
            ValueError: If the group is empty or has no usable values.
        """
        if not records:
            raise ValueError("cannot build a baseline from no records")
        ordered = sorted(records, key=lambda record: record.timestamp)
        first = ordered[0]
        return calculator.compute_baseline(
            metric_name=first.metric_name,
            source=first.source,
            values=[record.value for record in ordered],
            service_name=first.service_name,
            resource_id=first.resource_id,
            labels=dict(first.labels),
            rolling_window=self.config.rolling_window,
            stddev_multiplier=self.config.stddev_multiplier,
        )

    def build_all(
        self, records: list[MetricRecord]
    ) -> list[BaselineRecord]:
        """Group records and calculate one baseline per group.

        Groups with no usable values are skipped (reported via the empty
        result, never with fabricated statistics).
        """
        baselines = []
        for group in self.group_records(records).values():
            try:
                baselines.append(self.build_baseline(group))
            except ValueError:
                continue
        return baselines