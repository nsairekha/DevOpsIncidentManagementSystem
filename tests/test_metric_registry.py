"""Tests for the metric registry metadata."""

from monitoring.pipeline.registry import (
    REGISTRY,
    get_definition,
    registered_names,
    sourced_names,
)


def test_known_definitions() -> None:
    """Registered metrics carry description, unit, and direction flags."""
    latency = get_definition("latency_p95")

    assert latency is not None
    assert latency.unit == "seconds"
    assert latency.metric_type == "latency"
    assert latency.higher_is_worse is True
    assert latency.lower_is_worse is False

    cpu = get_definition("cpu_utilization")

    assert cpu is not None
    assert cpu.unit == "percent"
    assert cpu.higher_is_worse is True


def test_unknown_name_returns_none() -> None:
    """Unregistered names return None (metadata only, no anomaly use)."""
    assert get_definition("not_a_metric") is None


def test_sourced_subset() -> None:
    """has_source distinguishes live metrics from future placeholders."""
    assert "cpu_utilization" in sourced_names()
    assert "request_count" in sourced_names()
    assert "memory_utilization" not in sourced_names()
    assert "restart_count" not in sourced_names()
    assert set(sourced_names()) <= set(registered_names())
    assert len(REGISTRY) >= 20