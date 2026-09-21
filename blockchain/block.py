"""Blocks and hashing for the audit chain."""

import hashlib
import json
from dataclasses import dataclass

# Sentinel previous-hash for the genesis block.
GENESIS_PREVIOUS_HASH = "0" * 64


def compute_block_hash(
    index: int, timestamp: str, data: dict, previous_hash: str
) -> str:
    """Deterministic SHA-256 hash over a block's contents.

    ``data`` is serialised with sorted keys so the hash is independent of
    insertion order within the payload.
    """
    serialized = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    payload = f"{index}|{timestamp}|{serialized}|{previous_hash}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Block:
    """A single audited event in the chain."""

    index: int
    timestamp: str  # ISO-8601 UTC
    data: dict
    previous_hash: str
    hash: str

    @classmethod
    def create(
        cls, index: int, timestamp: str, data: dict, previous_hash: str
    ) -> "Block":
        """Build a block, computing its hash from the given contents."""
        return cls(
            index=index,
            timestamp=timestamp,
            data=data,
            previous_hash=previous_hash,
            hash=compute_block_hash(index, timestamp, data, previous_hash),
        )