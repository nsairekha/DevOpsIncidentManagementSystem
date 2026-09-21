"""Shared FastAPI dependencies."""

from fastapi import Request

from blockchain import AuditLedger


def get_ledger(request: Request) -> AuditLedger:
    """Return the application-wide audit ledger held in app state."""
    return request.app.state.ledger