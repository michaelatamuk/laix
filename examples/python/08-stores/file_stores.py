"""Persist a stream checkpoint and a commitment ledger on disk."""

from __future__ import annotations

from tempfile import TemporaryDirectory

from laix import (
    Commitment,
    CommitmentLedger,
    Decision,
    DecisionRequest,
    FileCommitmentStore,
    FileStreamCheckpointStore,
    StreamSession,
)


def decider(request: DecisionRequest) -> list[Decision]:
    return [
        Decision(
            verb="guide",
            confidence=0.9,
            reason_code="worth_surfacing",
            rationale=request.subject,
            decision_id=f"DEC-{request.subject}",
        )
    ]


with TemporaryDirectory() as directory:
    checkpoints = FileStreamCheckpointStore(directory)
    session = StreamSession(decider, stream_id="stream-a")
    session.observe(DecisionRequest(subject="case", at="2026-11-01T10:00:00+00:00"))
    session.save(checkpoints, "case-1")

    restored = StreamSession(decider, stream_id="stream-a")
    restored.resume(checkpoints, "case-1")

    commitments = FileCommitmentStore(directory)
    ledger = CommitmentLedger(
        (Commitment(id="a", subject="send the draft", due="2026-11-01T09:00:00+00:00"),)
    )
    commitments.save("task-1", ledger)
    loaded = commitments.load("task-1")
    print(restored.pending, loaded.get("a").subject if loaded else "missing")
