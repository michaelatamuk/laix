"""Show cooldown, per-window budget and replay in one stream."""

from __future__ import annotations

from datetime import datetime

from laix import Decision, DecisionRequest, ManualClock, StreamSession


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


clock = ManualClock()
session = StreamSession(
    decider,
    clock=clock,
    cooldown_ms=1000,
    max_decisions_per_window=1,
    budget_window_ms=2000,
)

clock.set(datetime.fromisoformat("2026-11-01T10:00:00+00:00"))
first = session.observe(DecisionRequest(subject="a", at="2026-11-01T10:00:00+00:00"))

clock.set(datetime.fromisoformat("2026-11-01T10:00:00.200+00:00"))
second = session.observe(DecisionRequest(subject="b", at="2026-11-01T10:00:00.200+00:00"))

clock.set(datetime.fromisoformat("2026-11-01T10:00:01.200+00:00"))
third = session.observe(DecisionRequest(subject="c", at="2026-11-01T10:00:01.200+00:00"))

replay_session = StreamSession(decider, clock=ManualClock())
replay = replay_session.replay(
    [
        DecisionRequest(subject="d", at="2026-11-01T10:00:10+00:00"),
        DecisionRequest(subject="e", at="2026-11-01T10:00:11+00:00"),
    ]
)
print(
    len(first),
    len(second),
    len(third),
    session.stats.throttled,
    session.stats.shed,
    [decision.rationale for decision in replay],
)
