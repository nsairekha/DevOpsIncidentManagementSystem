"""Tests for the blockchain audit ledger."""

import json

import pytest

from agents import IncidentAnalysisAgent
from ai import ZScoreDetector
from blockchain import AuditLedger, Block, VerificationResult, compute_block_hash
from dataset import compute_signal_baseline


def test_ledger_starts_with_genesis_block() -> None:
    """A new ledger contains a single genesis block at index 0."""
    ledger = AuditLedger()

    assert ledger.length == 1
    assert ledger.blocks[0].index == 0
    assert ledger.blocks[0].data["event_type"] == "GENESIS"
    assert ledger.verify().valid


def test_append_creates_chained_blocks() -> None:
    """Appended events form a chained sequence with increasing indices."""
    ledger = AuditLedger()
    ledger.append("test_event", {"metric": "cpu", "value": 12.5})

    assert ledger.length == 2
    first, second = ledger.blocks
    assert second.index == 1
    assert second.previous_hash == first.hash
    assert second.hash != first.hash
    assert second.data == {"event_type": "test_event", "payload": {"metric": "cpu", "value": 12.5}}
    assert ledger.verify().valid


def test_append_records_agent_results() -> None:
    """Agent results are recorded as audited events end to end."""
    import numpy as np
    import pandas as pd

    reference = pd.DataFrame({"cpu": 15.0 + np.random.default_rng(0).normal(0, 1, 60)})
    agent = IncidentAnalysisAgent(
        ZScoreDetector(threshold=3.0).fit(reference),
        {"cpu": compute_signal_baseline(reference["cpu"])},
    )
    telemetry = pd.DataFrame({"cpu": [15.1, 15.0, 99.0, 14.9, 15.2]})
    result = agent.analyze(telemetry)

    ledger = AuditLedger()
    ledger.append("agent_result", result.as_dict())

    event = ledger.blocks[-1].data
    assert event["event_type"] == "agent_result"
    assert event["payload"]["n_findings"] == result.n_findings
    assert ledger.verify().valid


def test_invalid_payload_type_raises() -> None:
    """Appending a non-dict payload is rejected."""
    ledger = AuditLedger()
    with pytest.raises(TypeError, match="payload must be a dict"):
        ledger.append("bad_event", ["not", "a", "dict"])  # type: ignore[arg-type]


def test_tampering_with_data_is_detected() -> None:
    """Mutating a historical block's data breaks the chain."""
    ledger = AuditLedger()
    ledger.append("event_a", {"value": 10})
    ledger.append("event_b", {"value": 20})

    # Rewrite the first appended event with altered data (a tamperer's edit).
    original = ledger.blocks[1]
    forged = Block.create(
        index=original.index,
        timestamp=original.timestamp,
        data={"event_type": "event_a", "payload": {"value": 999}},
        previous_hash=original.previous_hash,
    )
    ledger._chain[1] = forged  # noqa: SLF001 - test accesses internals

    result = ledger.verify()

    assert not result.valid
    # Block.create() recomputes a self-consistent hash for the forged data,
    # so the next block's previous_hash no longer matches -> chain broken.
    assert any("previous_hash does not match" in e for e in result.errors)


def test_forged_hash_is_detected() -> None:
    """A block whose stored hash does not match its contents is caught."""
    ledger = AuditLedger()
    ledger.append("event_a", {"value": 10})
    block = ledger.blocks[1]

    forged = Block(
        index=block.index,
        timestamp=block.timestamp,
        data=block.data,
        previous_hash=block.previous_hash,
        hash="f" * 64,
    )
    ledger._chain[1] = forged  # noqa: SLF001 - test accesses internals

    result = ledger.verify()

    assert not result.valid
    assert any("stored hash does not match" in e for e in result.errors)


def test_broken_previous_hash_is_detected() -> None:
    """Re-linking a block to the wrong predecessor is caught."""
    ledger = AuditLedger()
    ledger.append("event_a", {"value": 10})
    ledger.append("event_b", {"value": 20})

    block_b = ledger.blocks[2]
    forged = Block.create(
        index=block_b.index,
        timestamp=block_b.timestamp,
        data=block_b.data,
        previous_hash="0" * 64,
    )
    ledger._chain[2] = forged  # noqa: SLF001 - test accesses internals

    result = ledger.verify()

    assert not result.valid
    assert any("previous_hash does not match" in e for e in result.errors)


def test_index_sequence_violation_is_detected() -> None:
    """Blocks out of index order are reported."""
    ledger = AuditLedger()
    ledger.append("event_a", {"value": 10})

    block = ledger.blocks[1]
    forged = Block.create(
        index=99,
        timestamp=block.timestamp,
        data={"event_type": "event_a", "payload": {"value": 10}},
        previous_hash=block.previous_hash,
    )
    ledger._chain[1] = forged  # noqa: SLF001 - test accesses internals

    result = ledger.verify()

    assert not result.valid
    assert any("expected index" in e for e in result.errors)


def test_save_and_load_roundtrip(tmp_path) -> None:
    """A saved ledger reloads with identical integrity."""
    ledger = AuditLedger()
    ledger.append("event_a", {"value": 10})
    path = tmp_path / "ledger.json"
    ledger.save(path)

    loaded = AuditLedger.load(path)

    assert loaded.length == ledger.length
    assert loaded.last_hash == ledger.last_hash
    assert loaded.to_json() == ledger.to_json()
    assert loaded.verify().valid


def test_load_requires_genesis(tmp_path) -> None:
    """A file without a genesis block is rejected."""
    path = tmp_path / "broken.json"
    path.write_text(json.dumps([{"index": 5, "data": {}}]))
    with pytest.raises(ValueError, match="missing genesis"):
        AuditLedger.load(path)


def test_load_detects_tampered_file(tmp_path) -> None:
    """A tampered ledger file fails verification after loading."""
    ledger = AuditLedger()
    ledger.append("event_a", {"value": 10})
    path = tmp_path / "ledger.json"
    ledger.save(path)

    raw = json.loads(path.read_text())
    raw[1]["data"]["payload"]["value"] = 999
    path.write_text(json.dumps(raw))
    loaded = AuditLedger.load(path)

    assert not loaded.verify().valid


def test_append_defaults_payload_to_empty_dict() -> None:
    """Appending without a payload records an empty payload."""
    ledger = AuditLedger()
    ledger.append("heartbeat")

    assert ledger.blocks[-1].data == {"event_type": "heartbeat", "payload": {}}
    assert ledger.verify().valid


def test_tampered_genesis_is_detected() -> None:
    """A genesis block with an unexpected previous_hash is reported."""
    ledger = AuditLedger()
    genesis = ledger.blocks[0]
    forged = Block.create(
        index=0,
        timestamp=genesis.timestamp,
        data=genesis.data,
        previous_hash="1" * 64,
    )
    ledger._chain[0] = forged  # noqa: SLF001 - test accesses internals

    result = ledger.verify()

    assert not result.valid
    assert any("genesis block" in e for e in result.errors)


def test_verification_result_type() -> None:
    """verify() returns a VerificationResult with structured errors."""
    result = AuditLedger().verify()
    assert isinstance(result, VerificationResult)
    assert result.valid is True
    assert result.errors == ()


def test_hash_is_deterministic_and_content_sensitive() -> None:
    """Same contents hash identically; different contents differ."""
    h1 = compute_block_hash(1, "2026-01-01T00:00:00+00:00", {"a": 1, "b": 2}, "x" * 64)
    h2 = compute_block_hash(1, "2026-01-01T00:00:00+00:00", {"b": 2, "a": 1}, "x" * 64)
    h3 = compute_block_hash(1, "2026-01-01T00:00:00+00:00", {"a": 1, "b": 3}, "x" * 64)

    assert h1 == h2  # key order independent
    assert h1 != h3  # content sensitive