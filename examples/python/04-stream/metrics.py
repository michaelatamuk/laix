"""Export stream counters in Prometheus text format."""

from __future__ import annotations

from laix import Decision, DecisionRequest, ManualClock, StreamSession, prometheus


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


session = StreamSession(decider, clock=ManualClock())
session.observe(DecisionRequest(subject="a", at="2026-11-01T10:00:00+00:00"))
text = prometheus(session.stats)
print(session.stats.decided, "laix_stream_decided 1" in text)
