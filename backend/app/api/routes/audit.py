"""Audit-trail endpoint: expose the append-only ledger and its integrity."""

from fastapi import APIRouter, Depends, Request

from blockchain import AuditLedger
from backend.app.deps import get_ledger
from backend.app.schemas.audit import AuditResponse, BlockOut

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/audit", response_model=AuditResponse, summary="Inspect the audit trail")
def audit_route(
    request: Request,
    ledger: AuditLedger = Depends(get_ledger),
) -> AuditResponse:
    """Return every audited block and the chain's integrity verdict."""
    check = ledger.verify()
    return AuditResponse(
        length=ledger.length,
        valid=check.valid,
        errors=list(check.errors),
        last_hash=ledger.last_hash,
        blocks=[
            BlockOut(
                index=b.index,
                timestamp=b.timestamp,
                event_type=b.data.get("event_type", ""),
                hash=b.hash,
                previous_hash=b.previous_hash,
            )
            for b in ledger.blocks
        ],
    )