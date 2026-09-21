"""Metric processing: normalize → validate → sort/dedupe → baselines.

The processor is decoupled from live sources: it accepts already-collected
:class:`MetricRecord` lists (from either collector) and returns
:class:`BaselineRecord` lists via the baseline service.
"""

from monitoring.baseline.models import BaselineRecord
from monitoring.baseline.service import BaselineService
from monitoring.models.metric import MetricRecord
from monitoring.normalization.normalizer import deduplicate, normalize_all
from monitoring.validation.validators import ValidationIssue, validate_records


class MetricProcessor:
    """Process raw records into baselines."""

    def __init__(self, baseline_service: BaselineService | None = None) -> None:
        self.baseline_service = baseline_service or BaselineService()

    def process(
        self, records: list[MetricRecord]
    ) -> tuple[list[BaselineRecord], list[ValidationIssue]]:
        """Normalize, validate, sort, deduplicate, then calculate baselines.

        Returns:
            ``(baselines, issues)`` — baselines for every group with usable
            values, plus validation issues (missing values, duplicates,
            ordering problems) found along the way.
        """
        normalized = normalize_all(records)
        issues = validate_records(normalized)
        usable = [record for record in normalized if record.value == record.value]
        ordered = sorted(usable, key=lambda record: record.timestamp)
        unique = deduplicate(ordered)
        return self.baseline_service.build_all(unique), issues