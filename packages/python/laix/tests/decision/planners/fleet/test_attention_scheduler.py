from __future__ import annotations

from laix import AttentionCandidate, AttentionScheduler


def test_scheduler_prefers_urgent_high_risk_review() -> None:
    schedule = AttentionScheduler().schedule(
        (
            AttentionCandidate(
                id="urgent",
                risk=0.9,
                commitment=True,
                review_cost=1.0,
                deadline="2026-11-01T10:01:00+00:00",
            ),
            AttentionCandidate(
                id="routine",
                risk=0.1,
                review_cost=1.0,
                deadline="2026-11-01T11:00:00+00:00",
            ),
        ),
        now="2026-11-01T10:00:00+00:00",
        budget=1.0,
    )

    assert schedule.selected[0].candidate_id == "urgent"
    assert schedule.spent == 1.0
    assert schedule.deferred[0].candidate_id == "routine"


def test_scheduler_respects_budget_and_returns_reasons() -> None:
    schedule = AttentionScheduler().schedule(
        (
            AttentionCandidate(id="a", risk=0.8, review_cost=0.75),
            AttentionCandidate(id="b", risk=0.6, review_cost=0.75),
        ),
        now="2026-11-01T10:00:00+00:00",
        budget=1.0,
    )

    assert [row.candidate_id for row in schedule.selected] == ["a"]
    assert schedule.deferred[0].candidate_id == "b"
    assert schedule.deferred[0].reason == "attention budget exhausted"


def test_empty_schedule() -> None:
    schedule = AttentionScheduler().schedule((), now="2026-11-01T10:00:00+00:00")

    assert schedule.selected == ()
    assert schedule.deferred == ()
    assert schedule.spent == 0.0
