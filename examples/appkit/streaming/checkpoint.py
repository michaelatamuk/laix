"""Save and resume a stream session through a checkpoint store."""

from __future__ import annotations

from laix import Decision, DecisionRequest, InMemoryStreamCheckpointStore, StreamSession


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


request = DecisionRequest(subject="case", at="2026-11-01T10:00:00+00:00")
store = InMemoryStreamCheckpointStore()
session = StreamSession(decider)
session.observe(request)
session.save(store, "case-1")

restored = StreamSession(decider)
print(restored.resume(store, "case-1"), restored.pending, restored.stats.decided)
