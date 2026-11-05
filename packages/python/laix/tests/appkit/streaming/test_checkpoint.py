"""Durable stream checkpoints."""

from __future__ import annotations

from laix import (
    Decision,
    DecisionRequest,
    FileStreamCheckpointStore,
    InMemoryStreamCheckpointStore,
    ManualClock,
    StreamSession,
)


def _request(subject: str, second: int) -> DecisionRequest:
    return DecisionRequest(subject=subject, at=f"2026-11-01T10:00:{second:02d}+00:00")


def _decider(request: DecisionRequest) -> list[Decision]:
    return [
        Decision(
            verb="guide",
            confidence=0.9,
            reason_code="worth_surfacing",
            rationale=request.subject,
            decision_id=f"DEC-{request.subject}",
        )
    ]


def test_file_checkpoint_round_trips(tmp_path) -> None:
    store = FileStreamCheckpointStore(tmp_path)
    session = StreamSession(_decider, clock=ManualClock())
    session.observe(_request("a", 0))
    session.save(store, "case-1")

    restored = StreamSession(_decider, clock=ManualClock())
    assert restored.resume(store, "case-1") is True
    assert restored.pending == 1
    assert restored.stats.decided == 1

    store.delete("case-1")
    assert store.load("case-1") is None


def test_in_memory_checkpoint_round_trips() -> None:
    store = InMemoryStreamCheckpointStore()
    session = StreamSession(_decider, clock=ManualClock())
    session.observe(_request("a", 0))
    session.save(store, "case-2")

    restored = StreamSession(_decider, clock=ManualClock())
    assert restored.resume(store, "case-2") is True
    assert restored.pending == 1
