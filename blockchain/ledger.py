"""Append-only audit ledger with chained, tamper-evident blocks.

Events are appended as blocks. Each block commits to the hash of its
predecessor, so altering any historical block breaks the chain and is detected
by :meth:`AuditLedger.verify`.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from blockchain.block import GENESIS_PREVIOUS_HASH, Block, compute_block_hash


@dataclass(frozen=True)
class VerificationResult:
    """Outcome of a chain integrity check."""

    valid: bool
    errors: tuple[str, ...] = ()


class AuditLedger:
    """An append-only blockchain of audited events."""

    def __init__(self) -> None:
        self._chain: list[Block] = []
        self._append_genesis()

    # ------------------------------------------------------------------ #
    # Chain access
    # ------------------------------------------------------------------ #
    @property
    def length(self) -> int:
        return len(self._chain)

    @property
    def blocks(self) -> tuple[Block, ...]:
        return tuple(self._chain)

    @property
    def last_hash(self) -> str:
        return self._chain[-1].hash

    # ------------------------------------------------------------------ #
    # Writing
    # ------------------------------------------------------------------ #
    def append(self, event_type: str, payload: dict | None = None) -> Block:
        """Append an audited event to the chain.

        Args:
            event_type: A short label for the event (e.g. ``agent_result``).
            payload: JSON-serialisable event details.

        Returns:
            The newly appended block.

        Raises:
            TypeError: If ``payload`` is not a dict.
        """
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict (or None)")

        previous = self._chain[-1]
        timestamp = datetime.now(timezone.utc).isoformat()
        block = Block.create(
            index=len(self._chain),
            timestamp=timestamp,
            data={"event_type": event_type, "payload": payload},
            previous_hash=previous.hash,
        )
        self._chain.append(block)
        return block

    # ------------------------------------------------------------------ #
    # Integrity
    # ------------------------------------------------------------------ #
    def verify(self) -> VerificationResult:
        """Walk the chain and report any integrity violation."""
        errors: list[str] = []
        for i, block in enumerate(self._chain):
            if block.index != i:
                errors.append(
                    f"block {block.hash[:8]}: expected index {i}, got {block.index}"
                )
            if i == 0:
                if block.previous_hash != GENESIS_PREVIOUS_HASH:
                    errors.append("genesis block: unexpected previous_hash")
                continue

            previous = self._chain[i - 1]
            recomputed = compute_block_hash(
                block.index, block.timestamp, block.data, block.previous_hash
            )
            if block.hash != recomputed:
                errors.append(
                    f"block {block.index}: stored hash does not match its contents"
                )
            if block.previous_hash != previous.hash:
                errors.append(
                    f"block {block.index}: previous_hash does not match "
                    f"preceding block {previous.index}"
                )

        return VerificationResult(valid=not errors, errors=tuple(errors))

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def to_json(self) -> str:
        """Serialise the full chain to JSON."""
        return json.dumps([asdict(b) for b in self._chain])

    def save(self, path: str | Path) -> None:
        """Persist the chain to ``path``."""
        Path(path).write_text(self.to_json(), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "AuditLedger":
        """Reconstruct a ledger from a file written by :meth:`save`.

        Note: the chain is reconstructed as stored (hashes included) and is
        *not* re-validated here — call :meth:`verify` to check integrity.
        """
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not raw or raw[0]["index"] != 0:
            raise ValueError("invalid ledger file: missing genesis block")

        ledger = cls.__new__(cls)
        ledger._chain = [
            Block(
                index=b["index"],
                timestamp=b["timestamp"],
                data=b["data"],
                previous_hash=b["previous_hash"],
                hash=b["hash"],
            )
            for b in raw
        ]
        return ledger

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _append_genesis(self) -> None:
        genesis = Block.create(
            index=0,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data={"event_type": "GENESIS", "payload": {"message": "audit chain created"}},
            previous_hash=GENESIS_PREVIOUS_HASH,
        )
        self._chain.append(genesis)