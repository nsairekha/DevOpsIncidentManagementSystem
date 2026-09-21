"""Append-only blockchain audit trail for event integrity."""

from blockchain.block import GENESIS_PREVIOUS_HASH, Block, compute_block_hash
from blockchain.ledger import AuditLedger, VerificationResult

__all__ = [
    "GENESIS_PREVIOUS_HASH",
    "Block",
    "compute_block_hash",
    "AuditLedger",
    "VerificationResult",
]