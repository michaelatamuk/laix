"""AADS exact Whittle index: binary-search the subsidy for each arm."""

from __future__ import annotations

from laix import (
    WhittleCandidate,
    WhittleScheduler,
    WhittleTransition,
    whittle_index,
)


def candidate(candidate_id: str, reward: float) -> WhittleCandidate:
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


high = candidate("high", 1.0)
low = candidate("low", 0.1)
schedule = WhittleScheduler().schedule((low, high), budget=1.0)

print(whittle_index(high), whittle_index(low))
print(schedule.selected[0].candidate_id, schedule.deferred[0].candidate_id)
