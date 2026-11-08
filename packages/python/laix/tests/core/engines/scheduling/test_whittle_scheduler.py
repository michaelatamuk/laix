from __future__ import annotations

from laix import (
    WhittleCandidate,
    WhittleScheduler,
    WhittleTransition,
    whittle_index,
)


def _candidate(candidate_id: str, reward: float) -> WhittleCandidate:
    return WhittleCandidate(
        id=candidate_id,
        states=("bad", "good"),
        start="bad",
        active_transitions=(
            WhittleTransition(state="bad", next_state="good"),
            WhittleTransition(state="good", next_state="good"),
        ),
        passive_transitions=(
            WhittleTransition(state="bad", next_state="bad"),
            WhittleTransition(state="good", next_state="good"),
        ),
        active_reward={"bad": reward, "good": 0.2},
        passive_reward={"bad": 0.0, "good": 0.0},
        active_cost=0.1,
        review_cost=1.0,
        discount=0.9,
    )


def test_higher_active_reward_has_higher_index() -> None:
    high = whittle_index(_candidate("high", 1.0))
    low = whittle_index(_candidate("low", 0.1))

    assert high > low
    assert high > 0


def test_whittle_scheduler_allocates_by_index() -> None:
    schedule = WhittleScheduler().schedule(
        (_candidate("low", 0.1), _candidate("high", 1.0)),
        budget=1.0,
    )

    assert schedule.selected[0].candidate_id == "high"
    assert schedule.deferred[0].candidate_id == "low"
    assert schedule.spent == 1.0
