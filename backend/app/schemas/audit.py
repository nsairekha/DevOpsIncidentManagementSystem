"""Schemas for the audit-trail endpoint."""

from pydantic import BaseModel


class BlockOut(BaseModel):
    """A single audited block as exposed by the API."""

    index: int
    timestamp: str
    event_type: str
    hash: str
    previous_hash: str


class AuditResponse(BaseModel):
    """The full audit trail plus its integrity verdict."""

    length: int
    valid: bool
    errors: list[str]
    last_hash: str
    blocks: list[BlockOut]