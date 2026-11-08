"""Aggregate events into tumbling windows before deciding."""

from __future__ import annotations

import asyncio

from laix import Decision, DecisionRequest, ManualClock, StreamSession


def decider(request: DecisionRequest) -> list[Decision]:
    return [
        Decision(
            verb="guide",
            confidence=0.9,
            reason_code="window_ready",
            rationale=request.subject,
            decision_id=f"DEC-{request.subject}",
        )
    ]


async def events():
    yield DecisionRequest(subject="a", at="2026-11-01T10:00:00.100+00:00")
    yield DecisionRequest(subject="b", at="2026-11-01T10:00:00.900+00:00")
    yield DecisionRequest(subject="c", at="2026-11-01T10:00:01.100+00:00")


def on_window(batch) -> DecisionRequest:
    return DecisionRequest(
        subject=f"{len(batch.events)} events",
        at=batch.end.isoformat(),
    )


async def main() -> list[Decision]:
    session = StreamSession(decider, clock=ManualClock())
    return [
        decision
        async for decision in session.feed_windows(
            events(),
            window_ms=1000,
            on_window=on_window,
        )
    ]


decisions = asyncio.run(main())
print([decision.rationale for decision in decisions])
