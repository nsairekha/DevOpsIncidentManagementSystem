"""Controlled labeling: scenarios → anomaly labels (STEP 8).

Labels never come from baselines or statistics. A label is applied only
when a row falls inside a recorded controlled-experiment window
(``scenario_start`` ≤ timestamp ≤ ``scenario_end``) for a matching service.
Observed behavior and controlled scenarios stay distinct: outside every
window rows are ``anomaly_label=0`` / ``anomaly_type="normal"``.
"""

from dataclasses import dataclass, field
from datetime import datetime

from dataset.schema import ANOMALY_TYPES, ANOMALOUS_LABEL, NORMAL_LABEL


@dataclass(frozen=True)
class Scenario:
    """One executed (or planned) controlled experiment window."""

    scenario_id: str
    scenario_type: str
    start_time: datetime
    end_time: datetime
    affected_services: tuple[str, ...] | None = None
    description: str = ""
    executed: bool = True

    def __post_init__(self) -> None:
        if self.scenario_type not in ANOMALY_TYPES or self.scenario_type == "normal":
            raise ValueError(f"scenario_type must be an anomaly type, got '{self.scenario_type}'")
        if self.end_time < self.start_time:
            raise ValueError("scenario end_time precedes start_time")

    def matches(self, timestamp: datetime, service: str | None) -> bool:
        """Whether a row belongs to this scenario window."""
        if not (self.start_time <= timestamp <= self.end_time):
            return False
        if self.affected_services is not None and service not in self.affected_services:
            return False
        return True


def apply_labels(df, scenarios: list[Scenario]):
    """Label rows inside scenario windows; everything else stays normal.

    Args:
        df: Feature table with ``timestamp`` and ``service_name`` columns.
        scenarios: Executed scenarios (``executed=False`` entries are
            skipped — planned but not run).

    Returns:
        A copy with ``anomaly_label``, ``anomaly_type``, ``scenario_id``,
        ``scenario_start``, ``scenario_end``, ``scenario_type`` filled.
    """
    labeled = df.copy()
    labeled["anomaly_label"] = NORMAL_LABEL
    labeled["anomaly_type"] = "normal"
    labeled["scenario_id"] = None
    labeled["scenario_start"] = None
    labeled["scenario_end"] = None
    labeled["scenario_type"] = None

    for scenario in scenarios:
        if not scenario.executed:
            continue
        mask = [
            scenario.matches(ts, service)
            for ts, service in zip(
                labeled["timestamp"], labeled["service_name"]
            )
        ]
        labeled.loc[mask, "anomaly_label"] = ANOMALOUS_LABEL
        labeled.loc[mask, "anomaly_type"] = scenario.scenario_type
        labeled.loc[mask, "scenario_id"] = scenario.scenario_id
        labeled.loc[mask, "scenario_start"] = scenario.start_time
        labeled.loc[mask, "scenario_end"] = scenario.end_time
        labeled.loc[mask, "scenario_type"] = scenario.scenario_type
    return labeled


def scenario_record(scenario: Scenario) -> dict:
    """Serialize a scenario for the executed-scenario registry."""
    return {
        "scenario_id": scenario.scenario_id,
        "scenario_type": scenario.scenario_type,
        "start_time": scenario.start_time.isoformat(),
        "end_time": scenario.end_time.isoformat(),
        "affected_services": list(scenario.affected_services or []),
        "description": scenario.description,
        "executed": scenario.executed,
    }