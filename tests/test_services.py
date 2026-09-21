"""Tests for the microservices scaffold (registry, service, events)."""

import json
import uuid

import pytest

from services import (
    EventEnvelope,
    EventTypes,
    Service,
    ServiceEndpoint,
    ServiceRegistry,
)


# ---------------------------------------------------------------------- #
# Registry
# ---------------------------------------------------------------------- #
def test_register_discover_and_address() -> None:
    """Services can be registered and looked up by name."""
    registry = ServiceRegistry()
    registry.register(ServiceEndpoint(name="backend", host="127.0.0.1", port=8000))

    assert "backend" in registry
    assert registry.get("backend").port == 8000
    assert registry.address("backend") == "127.0.0.1:8000"


def test_registry_rejects_invalid_status() -> None:
    """Unknown statuses are rejected at registration time."""
    registry = ServiceRegistry()
    with pytest.raises(ValueError, match="invalid status"):
        registry.register(
            ServiceEndpoint(name="svc", host="h", port=1, status="exploded")
        )


def test_registry_upsert_and_unregister() -> None:
    """Re-registering updates the endpoint; unregistering removes it."""
    registry = ServiceRegistry()
    registry.register(ServiceEndpoint(name="svc", host="a", port=1))
    registry.register(ServiceEndpoint(name="svc", host="b", port=2))

    assert registry.address("svc") == "b:2"

    registry.unregister("svc")
    assert "svc" not in registry
    assert registry.get("svc") is None
    assert registry.address("svc") is None


def test_registry_snapshot_and_length() -> None:
    """all() returns a snapshot; length reflects registered services."""
    registry = ServiceRegistry()
    registry.register(ServiceEndpoint(name="a", host="h", port=1))
    registry.register(ServiceEndpoint(name="b", host="h", port=2))

    assert len(registry) == 2
    assert {e.name for e in registry.all()} == {"a", "b"}


def test_service_endpoint_address() -> None:
    """ServiceEndpoint formats its host:port address."""
    assert ServiceEndpoint(name="s", host="10.0.0.5", port=9090).address() == "10.0.0.5:9090"


# ---------------------------------------------------------------------- #
# Service base
# ---------------------------------------------------------------------- #
def test_service_describes_and_registers_itself() -> None:
    """A Service reports an endpoint and can register with a registry."""
    registry = ServiceRegistry()
    service = Service(name="analyzer", port=8100, version="0.2.0").register(registry)

    endpoint = service.endpoint()
    assert endpoint.name == "analyzer"
    assert endpoint.port == 8100
    assert endpoint.version == "0.2.0"
    assert endpoint.status == "up"
    assert registry.get("analyzer") == endpoint


def test_service_status_override() -> None:
    """Subclasses can override the status reported."""

    class Degraded(Service):
        def status(self) -> str:
            return "unknown"

    endpoint = Degraded(name="worker").endpoint()
    assert endpoint.status == "unknown"


# ---------------------------------------------------------------------- #
# Events
# ---------------------------------------------------------------------- #
def test_event_envelope_create() -> None:
    """create() fills ids, timestamps, and validates inputs."""
    envelope = EventEnvelope.create(
        EventTypes.ANOMALY_DETECTED, "analyzer", {"n": 3}
    )

    assert uuid.UUID(envelope.event_id)
    assert envelope.event_type == EventTypes.ANOMALY_DETECTED
    assert envelope.source_service == "analyzer"
    assert envelope.payload == {"n": 3}
    assert envelope.timestamp


def test_event_envelope_default_payload() -> None:
    """A default empty payload is allowed."""
    envelope = EventEnvelope.create(EventTypes.SERVICE_HEALTH, "backend")
    assert envelope.payload == {}


def test_event_envelope_validation() -> None:
    """Empty event types / sources and non-dict payloads are rejected."""
    with pytest.raises(ValueError, match="event_type"):
        EventEnvelope.create("", "svc")
    with pytest.raises(ValueError, match="source_service"):
        EventEnvelope.create("a.b", " ")
    with pytest.raises(TypeError, match="payload must be a dict"):
        EventEnvelope.create("a.b", "svc", ["not", "a", "dict"])  # type: ignore[arg-type]


def test_event_envelope_as_dict_is_json_serialisable() -> None:
    """Envelopes serialise cleanly to JSON."""
    envelope = EventEnvelope.create(EventTypes.INCIDENT_CREATED, "backend", {"id": 1})

    payload = envelope.as_dict()
    assert json.dumps(payload)  # must not raise
    assert payload["event_id"] == envelope.event_id


def test_event_types_are_distinct() -> None:
    """All well-known event types are unique strings."""
    values = [
        EventTypes.TELEMETRY_INGESTED,
        EventTypes.ANOMALY_DETECTED,
        EventTypes.INCIDENT_CREATED,
        EventTypes.AUDIT_RECORDED,
        EventTypes.SERVICE_HEALTH,
    ]
    assert len(set(values)) == len(values)
    assert all(isinstance(v, str) and v for v in values)