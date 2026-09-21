"""Event schemas for inter-service communication.

Services communicate via a standard :class:`EventEnvelope` carrying an event
type, the source service, and a payload. Event types are centralised as
constants so producers and consumers share one vocabulary.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone


class EventTypes:
    """Well-known event types exchanged between services."""

    TELEMETRY_INGESTED = "telemetry.ingested"
    ANOMALY_DETECTED = "anomaly.detected"
    INCIDENT_CREATED = "incident.created"
    AUDIT_RECORDED = "audit.recorded"
    SERVICE_HEALTH = "service.health"


@dataclass(frozen=True)
class EventEnvelope:
    """A self-describing event message for the service bus."""

    event_id: str
    event_type: str
    source_service: str
    timestamp: str
    payload: dict

    @classmethod
    def create(
        cls,
        event_type: str,
        source_service: str,
        payload: dict | None = None,
    ) -> "EventEnvelope":
        """Build a new event envelope with fresh id and UTC timestamp."""
        if not event_type or not event_type.strip():
            raise ValueError("event_type must be a non-empty string")
        if not source_service or not source_service.strip():
            raise ValueError("source_service must be a non-empty string")
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict (or None)")

        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            source_service=source_service,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload,
        )

    def as_dict(self) -> dict:
        """Return the envelope as a plain, serialisable dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source_service": self.source_service,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }