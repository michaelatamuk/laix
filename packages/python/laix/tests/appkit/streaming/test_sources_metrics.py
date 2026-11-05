"""Transport sources, metrics export and the stream bench."""

from __future__ import annotations

import asyncio

from laix import (
    Decision,
    DecisionRequest,
    ManualClock,
    StreamSession,
    from_queue,
    from_sync,
    prometheus,
    run_stream_bench,
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


def test_from_sync_feeds_a_session() -> None:
    async def run() -> list[Decision]:
        session = StreamSession(_decider, clock=ManualClock())
        return [item async for item in session.feed(from_sync([_request("a", 0), _request("b", 1)]))]

    decisions = asyncio.run(run())
    assert [item.rationale for item in decisions] == ["a", "b"]


def test_from_queue_feeds_a_session() -> None:
    async def run() -> list[Decision]:
        queue: asyncio.Queue[DecisionRequest | None] = asyncio.Queue()
        await queue.put(_request("a", 0))
        await queue.put(None)
        session = StreamSession(_decider, clock=ManualClock())
        return [item async for item in session.feed(from_queue(queue))]

    decisions = asyncio.run(run())
    assert [item.rationale for item in decisions] == ["a"]


def test_prometheus_exports_counters() -> None:
    session = StreamSession(_decider, clock=ManualClock())
    session.observe(_request("a", 0))

    text = prometheus(session.stats)
    assert "# TYPE laix_stream_decided gauge" in text
    assert "laix_stream_decided 1" in text


def test_stream_bench_reports_throughput() -> None:
    session = StreamSession(_decider, clock=ManualClock())
    result = run_stream_bench(session, [_request("a", 0), _request("b", 1)])

    assert len(result.decisions) == 2
    assert result.elapsed_ms >= 0
    assert result.throughput_per_second >= 0
    assert result.stats["decided"] == 2
