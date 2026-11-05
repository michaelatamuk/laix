"""Streaming session: event time, cadence, backpressure and revisions."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import pytest

from laix import (
    Decision,
    DecisionRequest,
    EvidenceRef,
    Intent,
    ManualClock,
    ScoreBreakdown,
    StreamSession,
)
from laix import TumblingWindow


UTC = timezone.utc


def at(second: int) -> str:
    return f"2026-11-01T10:00:{second:02d}+00:00"


def moment(second: int, microsecond: int = 0) -> datetime:
    return datetime(2026, 11, 1, 10, 0, second, microsecond, tzinfo=UTC)


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


async def collect(session: StreamSession) -> list[Decision]:
    return [decision async for decision in session.decisions()]


def test_observe_stamps_the_stream_fields() -> None:
    session = StreamSession(
        decider,
        stream_id="STR-1",
        capacity=4,
        clock=ManualClock(moment(0)),
    )
    out = session.observe(
        DecisionRequest(subject="a", at=at(0), deadline=at(5), valid_until=at(9))
    )

    assert len(out) == 1
    assert out[0].stream_id == "STR-1"
    assert out[0].event_time == at(0)
    assert out[0].deadline == at(5)
    assert out[0].valid_until == at(9)
    assert out[0].status == "final"
    assert session.pending == 1


def test_async_decisions_drain_and_close() -> None:
    async def run() -> list[Decision]:
        session = StreamSession(decider, capacity=4)
        session.observe(DecisionRequest(subject="a", at=at(0)))
        session.observe(DecisionRequest(subject="b", at=at(1)))
        session.close()
        return await collect(session)

    decisions = asyncio.run(run())
    assert [item.rationale for item in decisions] == ["a", "b"]


def test_late_event_is_dropped() -> None:
    session = StreamSession(decider, late="drop")
    assert len(session.observe(DecisionRequest(subject="new", at=at(5)))) == 1
    assert session.observe(DecisionRequest(subject="late", at=at(1))) == []
    assert session.stats.late == 1


def test_late_event_can_be_accepted() -> None:
    session = StreamSession(decider, late="accept")
    session.observe(DecisionRequest(subject="new", at=at(5)))
    assert len(session.observe(DecisionRequest(subject="late", at=at(1)))) == 1
    assert session.stats.late == 0


def test_cooldown_throttles_until_it_elapses() -> None:
    clock = ManualClock(moment(0))
    session = StreamSession(decider, cooldown_ms=1000, clock=clock)

    assert len(session.observe(DecisionRequest(subject="a", at=at(0)))) == 1
    clock.set(moment(0, 500_000))
    assert session.observe(DecisionRequest(subject="b", at=at(0))) == []
    assert session.stats.throttled == 1

    clock.set(moment(1, 100_000))
    assert len(session.observe(DecisionRequest(subject="c", at=at(1)))) == 1


def test_force_bypasses_the_cooldown() -> None:
    clock = ManualClock(moment(0))
    session = StreamSession(decider, cooldown_ms=1000, clock=clock)
    session.observe(DecisionRequest(subject="a", at=at(0)))
    clock.set(moment(0, 200_000))
    assert len(session.observe(DecisionRequest(subject="b", at=at(0)), force=True)) == 1


def test_latest_wins_replaces_the_buffer() -> None:
    session = StreamSession(decider, capacity=2, on_full="latest_wins")
    for index in range(5):
        session.observe(DecisionRequest(subject=str(index), at=at(index)))

    assert session.pending == 1
    assert session.stats.dropped == 4
    session.close()
    decisions = asyncio.run(collect(session))
    assert [item.rationale for item in decisions] == ["4"]


def test_drop_oldest_keeps_the_newest() -> None:
    session = StreamSession(decider, capacity=2, on_full="drop_oldest")
    for index in range(4):
        session.observe(DecisionRequest(subject=str(index), at=at(index)))

    assert session.pending == 2
    assert session.stats.dropped == 2
    session.close()
    decisions = asyncio.run(collect(session))
    assert [item.rationale for item in decisions] == ["2", "3"]


def test_drop_newest_keeps_the_first() -> None:
    session = StreamSession(decider, capacity=2, on_full="drop_newest")
    for index in range(4):
        session.observe(DecisionRequest(subject=str(index), at=at(index)))

    assert session.pending == 2
    assert session.stats.dropped == 2
    session.close()
    decisions = asyncio.run(collect(session))
    assert [item.rationale for item in decisions] == ["0", "1"]


def test_revision_supersedes_the_previous_decision() -> None:
    session = StreamSession(decider)
    first = session.observe(DecisionRequest(subject="a", at=at(0)))[0]
    revised = session.revise(first, DecisionRequest(subject="a", at=at(1)))

    assert len(revised) == 1
    assert revised[0].revision == 1
    assert revised[0].supersedes == first.decision_id
    assert revised[0].status == "final"
    assert session.stats.revised == 1


def test_provisional_decision_is_marked() -> None:
    session = StreamSession(decider)
    out = session.observe(DecisionRequest(subject="a", at=at(0)), status="provisional")

    assert out[0].status == "provisional"
    assert session.stats.provisional == 1


def test_missed_deadline_is_provisional_and_counted() -> None:
    clock = ManualClock(moment(5))
    session = StreamSession(decider, clock=clock)
    out = session.observe(DecisionRequest(subject="a", at=at(0), deadline=at(1)))

    assert out[0].status == "provisional"
    assert session.stats.expired == 1
    assert session.stats.provisional == 1


def test_hysteresis_suppresses_the_same_batch() -> None:
    clock = ManualClock(moment(0))
    session = StreamSession(decider, clock=clock, hysteresis_ms=1000)

    assert len(session.observe(DecisionRequest(subject="a", at=at(0)))) == 1
    clock.set(moment(0, 500_000))
    assert session.observe(DecisionRequest(subject="b", at=at(0))) == []
    assert session.stats.suppressed == 1

    clock.set(moment(2))
    assert len(session.observe(DecisionRequest(subject="c", at=at(2)))) == 1


def test_budget_sheds_after_the_limit() -> None:
    clock = ManualClock(moment(0))
    session = StreamSession(
        decider,
        clock=clock,
        max_decisions_per_window=1,
        budget_window_ms=1000,
    )

    assert len(session.observe(DecisionRequest(subject="a", at=at(0)))) == 1
    clock.set(moment(0, 500_000))
    assert session.observe(DecisionRequest(subject="b", at=at(0))) == []
    assert session.stats.shed == 1

    clock.set(moment(1, 1))
    assert len(session.observe(DecisionRequest(subject="c", at=at(1)))) == 1


def test_latency_percentiles_are_recorded() -> None:
    def slow(request: DecisionRequest) -> list[Decision]:
        time.sleep(0.005)
        return decider(request)

    session = StreamSession(slow, clock=ManualClock(moment(0)))
    session.observe(DecisionRequest(subject="a", at=at(0)))

    assert session.stats.latency_p50 > 0
    assert session.stats.latency_p95 >= session.stats.latency_p50


def test_feed_coalesces_a_busy_source() -> None:
    async def events():
        yield DecisionRequest(subject="a", at=at(0))
        await asyncio.sleep(0.001)
        yield DecisionRequest(subject="b", at=at(1))
        await asyncio.sleep(0.05)
        yield DecisionRequest(subject="c", at=at(2))
        await asyncio.sleep(0.05)

    async def run() -> tuple[list[Decision], int]:
        session = StreamSession(decider, clock=ManualClock(moment(0)))
        out: list[Decision] = []
        async for decision in session.feed(events(), coalesce_ms=20):
            out.append(decision)
        return out, session.pending

    decisions, pending = asyncio.run(run())
    assert [item.rationale for item in decisions] == ["b", "c"]
    assert pending == 0


def test_snapshot_restores_watermark_and_stats() -> None:
    session = StreamSession(decider, clock=ManualClock(moment(0)))
    decision = session.observe(DecisionRequest(subject="a", at=at(5)))[0]
    snapshot = session.snapshot()

    restored = StreamSession(decider, clock=ManualClock(moment(0)))
    restored.restore(snapshot)

    assert restored.stats.decided == 1
    assert restored.trace(decision.decision_id).events[0]["stage"] == "decided"
    assert restored.observe(DecisionRequest(subject="late", at=at(1))) == []
    assert restored.stats.late == 1


def test_snapshot_keeps_pending_decisions() -> None:
    session = StreamSession(decider, clock=ManualClock(moment(0)))
    session.observe(DecisionRequest(subject="a", at=at(0)))
    session.observe(DecisionRequest(subject="b", at=at(1)))

    restored = StreamSession(decider, clock=ManualClock(moment(0)))
    restored.restore(session.snapshot())
    restored.close()

    decisions = asyncio.run(collect(restored))
    assert [item.rationale for item in decisions] == ["a", "b"]


def test_duplicate_event_is_dropped() -> None:
    clock = ManualClock(moment(0))
    session = StreamSession(decider, clock=clock, dedupe_ms=1000)

    assert len(session.observe(DecisionRequest(subject="a", at=at(0), event_id="e1"))) == 1
    assert session.observe(DecisionRequest(subject="b", at=at(0), event_id="e1")) == []
    assert session.stats.duplicates == 1

    clock.set(moment(2))
    assert len(session.observe(DecisionRequest(subject="c", at=at(2), event_id="e1"))) == 1


def test_trace_and_recorder_are_kept() -> None:
    recorded: list[Decision] = []
    session = StreamSession(decider, clock=ManualClock(moment(0)), recorder=recorded.append)
    decision = session.observe(DecisionRequest(subject="a", at=at(0)))[0]

    assert decision.trace_id
    assert session.trace(decision.decision_id).events[0]["stage"] == "decided"
    assert recorded == [decision]


def test_refine_timeout_emits_the_provisional_as_final() -> None:
    async def refine(request: DecisionRequest) -> list[Decision]:
        await asyncio.sleep(0.05)
        return [
            Decision(
                verb="act",
                confidence=0.99,
                reason_code="deep_path",
                rationale="deep",
                decision_id="DEC-deep",
            )
        ]

    async def run() -> list[Decision]:
        session = StreamSession(decider, clock=ManualClock(moment(0)))
        return await session.observe_refined(
            DecisionRequest(subject="a", at=at(0)),
            refine,
            timeout_ms=5,
        )

    decisions = asyncio.run(run())
    assert decisions[0].status == "provisional"
    assert decisions[-1].status == "final"
    assert decisions[-1].supersedes == decisions[0].decision_id


def test_observe_wait_applies_backpressure() -> None:
    async def run() -> tuple[Decision, Decision]:
        session = StreamSession(decider, capacity=1)
        session.observe(DecisionRequest(subject="a", at=at(0)))
        waiting = asyncio.create_task(
            session.observe_wait(DecisionRequest(subject="b", at=at(1)))
        )
        await asyncio.sleep(0)
        assert not waiting.done()

        iterator = session.decisions()
        first = await anext(iterator)
        await waiting
        second = await anext(iterator)
        return first, second

    first, second = asyncio.run(run())
    assert first.rationale == "a"
    assert second.rationale == "b"


def test_tumbling_window_closes_on_next_window() -> None:
    window = TumblingWindow(10_000)
    assert window.add(DecisionRequest(subject="a", at=at(0))) == []
    assert window.add(DecisionRequest(subject="b", at=at(5))) == []
    batches = window.add(DecisionRequest(subject="c", at=at(11)))

    assert len(batches) == 1
    assert batches[0].start == moment(0)
    assert batches[0].end == moment(10)
    assert [item.subject for item in batches[0].events] == ["a", "b"]

    rest = window.flush()
    assert [item.subject for item in rest[0].events] == ["c"]


def test_tumbling_window_drops_late_events() -> None:
    window = TumblingWindow(10_000)
    window.add(DecisionRequest(subject="a", at=at(15)))

    assert window.add(DecisionRequest(subject="late", at=at(1))) == []
    assert window.pending == 1


def test_feed_windows_aggregates() -> None:
    async def events():
        for second in (0, 1, 11, 12):
            yield DecisionRequest(subject=f"e{second}", at=at(second))

    def on_window(batch) -> DecisionRequest:
        return DecisionRequest(subject=f"n{len(batch.events)}", at=batch.end.isoformat())

    async def run() -> list[Decision]:
        session = StreamSession(decider, clock=ManualClock(moment(0)))
        out: list[Decision] = []
        async for decision in session.feed_windows(events(), window_ms=10_000, on_window=on_window):
            out.append(decision)
        return out

    decisions = asyncio.run(run())
    assert [item.rationale for item in decisions] == ["n2", "n2"]


def test_decision_from_dict_round_trips() -> None:
    decision = Decision(
        verb="guide",
        confidence=0.9,
        reason_code="worth_surfacing",
        rationale="test",
        evidence=(EvidenceRef(id="e", quote="q"),),
        intent=Intent("notify", {"text": "hi"}),
        breakdown=ScoreBreakdown(total=0.9),
    )
    restored = Decision.from_dict(decision.to_dict())

    assert restored == decision


def test_observe_refined_emits_a_revision() -> None:
    async def refine(request: DecisionRequest) -> list[Decision]:
        await asyncio.sleep(0)
        return [
            Decision(
                verb="act",
                confidence=0.99,
                reason_code="deep_path",
                rationale="deep",
                decision_id="DEC-deep",
            )
        ]

    async def run() -> tuple[Decision, list[Decision]]:
        session = StreamSession(decider, clock=ManualClock(moment(0)))
        first, *rest = await session.observe_refined(
            DecisionRequest(subject="a", at=at(0)),
            refine,
        )
        return first, rest

    first, rest = asyncio.run(run())
    assert first.status == "provisional"
    assert rest[0].status == "final"
    assert rest[0].revision == 1
    assert rest[0].supersedes == first.decision_id


def test_replay_uses_event_time_and_does_not_fill_the_buffer() -> None:
    session = StreamSession(decider)
    requests = [
        DecisionRequest(subject="a", at=at(0)),
        DecisionRequest(subject="b", at=at(1)),
        DecisionRequest(subject="c", at=at(2)),
    ]

    decisions = session.replay(requests)

    assert [item.rationale for item in decisions] == ["a", "b", "c"]
    assert session.pending == 0
    assert session.stats.observed == 3
    assert session.stats.decided == 3


def test_unknown_policy_is_rejected() -> None:
    with pytest.raises(ValueError):
        StreamSession(decider, on_full="explode")
    with pytest.raises(ValueError):
        StreamSession(decider, late="hold")
    with pytest.raises(ValueError):
        StreamSession(decider, capacity=0)
