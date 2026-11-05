"""Persist a commitment ledger through a store."""

from __future__ import annotations

from laix import Commitment, CommitmentLedger, InMemoryCommitmentStore

ledger = CommitmentLedger(
    (Commitment(id="a", subject="send the draft", due="2026-11-01T09:00:00+00:00"),)
)
store = InMemoryCommitmentStore()
store.save("task-1", ledger)
restored = store.load("task-1")
print(restored.get("a").subject if restored else "missing")
