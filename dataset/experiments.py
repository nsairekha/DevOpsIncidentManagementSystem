"""Controlled experiment framework (STEP 8).

Each executed experiment records a :class:`Scenario` (id, type, window,
affected services) so labels trace to real windows — never to vibes.
Experiments that cannot run safely in an environment stay interface-only:
:func:`resource_stress_plan` documents how CPU/memory stress *would* run
later without fabricating any measurements.
"""

import json
import os

from dataset.labeling import Scenario, scenario_record

#: Anomaly types with a safe local/Docker execution path today.
EXECUTABLE_SCENARIOS = (
    "latency_anomaly",
    "dependency_failure",
    "cascading_failure",
    "service_failure",
    "traffic_anomaly",
    "error_rate_anomaly",
)

#: Anomaly types with interface + documentation only (no safe local runner).
INTERFACE_ONLY_SCENARIOS = (
    "cpu_anomaly",
    "memory_anomaly",
    "resource_exhaustion",
)


def resource_stress_plan(
    *, service: str, target: str, duration_seconds: int = 60
) -> dict:
    """Document (not execute) a container-level resource-stress experiment.

    A future runner would apply Docker ``--cpus``/``--memory`` limits or a
    bounded in-container stressor (e.g. ``stress-ng --cpu 1 --timeout``)
    against a *single* service container, with host safeguards, while the
    collection scripts record the window. Nothing is measured here.
    """
    if target not in ("cpu", "memory"):
        raise ValueError(f"unknown stress target '{target}'")
    return {
        "service": service,
        "target": target,
        "duration_seconds": duration_seconds,
        "method": (
            "container-level limits and/or bounded stress-ng run inside the "
            f"{service} container only; host system untouched"
        ),
        "label": "cpu_anomaly" if target == "cpu" else "memory_anomaly",
        "executed": False,
        "note": "interface only: no measurements were taken",
    }


def save_scenarios(scenarios: list[Scenario], path: str) -> None:
    """Store executed-scenario records as JSON."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            [scenario_record(scenario) for scenario in scenarios],
            handle,
            indent=2,
            sort_keys=True,
        )


def load_scenarios(path: str) -> list[dict]:
    """Load executed-scenario records."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)
