"""Decision timeline semantics: revisions, chains and late events."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from laix import (
    HumanAttentionBudget,
    Decision,
    DecisionRequest,
    DecisionTimeline,
    ManualClock,
    StreamSession,
    TimelineError,
)


def _at(second: int) -> str:
    return f"2026-11-01T10:00:{second:02d}+00:00"


def _moment(second: int) -> datetime:
    return datetime(2026, 11, 1, 10, 0, second, tzinfo=timezone.utc)


def _decider(request: DecisionRequest) -> list[Decision]:
    return [
        Decision(
            verb="guide",
            confidence=0.8,
            reason_code="stream",
            rationale="a stream decision",
            decision_id=f"DEC-{request.at}",
        )
    ]


def _decision(
    decision_id: str,
    *,
    revision: int = 0,
    supersedes: str | None = None,
    stream_id: str = "desk",
    event_time: str = "2026-11-01T10:00:00+00:00",
) -> Decision:
    return Decision(
        verb="guide",
        confidence=0.8,
        reason_code="stream",
        rationale="a stream decision",
        decision_id=decision_id,
        stream_id=stream_id,
        event_time=event_time,
        revision=revision,
        supersedes=supersedes,
    )


def test_root_and_revision_form_a_chain() -> None:
    timeline = DecisionTimeline()
    root = timeline.add(_decision("d1"))
    revised = timeline.add(
        _decision("d2", revision=1, supersedes="d1", event_time="2026-11-01T10:01:00+00:00")
    )

    assert timeline.history("d2") == (root, revised)
    assert timeline.current() == (revised,)
    assert timeline.is_superseded("d1") is True
    assert timeline.is_superseded("d2") is False
    report = timeline.report()
    assert report.valid is True
    assert report.decisions == 2
    assert report.chains == 1
    assert report.superseded == 1


def test_duplicate_id_is_rejected() -> None:
    timeline = DecisionTimeline([_decision("d1")])
    with pytest.raises(TimelineError):
        timeline.add(_decision("d1"))


def test_root_cannot_supersede() -> None:
    with pytest.raises(TimelineError):
        DecisionTimeline().add(_decision("d1", supersedes="d0"))


def test_revision_needs_a_known_predecessor() -> None:
    with pytest.raises(TimelineError):
        DecisionTimeline().add(_decision("d2", revision=1, supersedes="d1"))


def test_revision_must_be_the_next_number() -> None:
    timeline = DecisionTimeline([_decision("d1")])
    with pytest.raises(TimelineError):
        timeline.add(_decision("d2", revision=2, supersedes="d1"))


def test_streams_must_match() -> None:
    timeline = DecisionTimeline([_decision("d1", stream_id="desk")])
    with pytest.raises(TimelineError):
        timeline.add(
            _decision("d2", revision=1, supersedes="d1", stream_id="phone")
        )


def test_event_time_cannot_move_backwards() -> None:
    timeline = DecisionTimeline([_decision("d1")])
    with pytest.raises(TimelineError):
        timeline.add(
            _decision(
                "d2",
                revision=1,
                supersedes="d1",
                event_time="2026-11-01T09:59:00+00:00",
            )
        )


def test_late_events_are_reported() -> None:
    timeline = DecisionTimeline(
        [
            _decision("d1", event_time="2026-11-01T10:00:00+00:00"),
            _decision("d2", event_time="2026-11-01T10:05:00+00:00"),
        ]
    )

    assert timeline.late("2026-11-01T10:03:00+00:00") == (timeline.get("d1"),)


def test_stream_session_feeds_the_timeline() -> None:
    timeline = DecisionTimeline()
    session = StreamSession(
        _decider,
        stream_id="STR-1",
        clock=ManualClock(_moment(0)),
        timeline=timeline,
    )
    first = session.observe(DecisionRequest(subject="a", at=_at(0)))[0]
    second = session.revise(first, DecisionRequest(subject="a", at=_at(1)))[0]

    assert timeline.report().decisions == 2
    assert timeline.history(second.decision_id) == (first, second)


def test_timeline_round_trips_through_a_stream_snapshot() -> None:
    timeline = DecisionTimeline()
    session = StreamSession(
        _decider,
        stream_id="STR-1",
        clock=ManualClock(_moment(0)),
        timeline=timeline,
    )
    first = session.observe(DecisionRequest(subject="a", at=_at(0)))[0]
    snapshot = session.snapshot()

    restored = StreamSession(
        _decider,
        stream_id="STR-1",
        clock=ManualClock(_moment(1)),
    )
    restored.restore(snapshot)

    assert restored.timeline is not None
    assert restored.timeline.history(first.decision_id) == (first,)


def test_stream_session_spends_a_shared_human_attention_budget() -> None:
    def decider(request: DecisionRequest) -> list[Decision]:
        return [
            Decision(
                verb="guide",
                confidence=0.8,
                reason_code="stream",
                rationale="a stream decision",
                decision_id=f"DEC-{request.at}",
                attributes={"human_attention_cost": 0.4},
            )
        ]

    budget = HumanAttentionBudget(total=1.0)
    session = StreamSession(
        decider,
        stream_id="STR-1",
        clock=ManualClock(_moment(0)),
        human_attention_budget=budget,
    )
    session.observe(DecisionRequest(subject="a", at=_at(0)))
    session.observe(DecisionRequest(subject="b", at=_at(1)))

    assert round(budget.remaining(), 6) == 0.2
    snapshot = session.snapshot()
    restored = StreamSession(decider, stream_id="STR-1")
    restored.restore(snapshot)
    assert restored.human_attention_budget is not None
    assert round(restored.human_attention_budget.remaining(), 6) == 0.2


def test_timeline_round_trips() -> None:
    timeline = DecisionTimeline(
        [
            _decision("d1"),
            _decision("d2", revision=1, supersedes="d1"),
        ]
    )
    restored = DecisionTimeline.from_dict(timeline.to_dict())

    assert restored.report() == timeline.report()
    assert restored.history("d2") == timeline.history("d2")
