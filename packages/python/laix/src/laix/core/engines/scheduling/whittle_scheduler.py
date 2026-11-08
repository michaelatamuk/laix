"""Exact Whittle-index scheduling for a finite single-arm model.

The heuristic ``AttentionScheduler`` ranks a static snapshot. This module adds
the model-based version: each candidate is a small two-action MDP, and its index
is the subsidy at which waiting becomes as good as reviewing.

The index is computed by binary search over the subsidy and value iteration for
the single-arm MDP. It is exact for the supplied finite model, not for an
infinite fleet.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class WhittleTransition:
    """One transition for the active or passive action."""

    state: str
    next_state: str
    probability: float = 1.0


@dataclass(frozen=True, slots=True)
class WhittleCandidate:
    """A two-action restless arm: review (active) or defer (passive)."""

    id: str
    states: tuple[str, ...]
    start: str
    active_transitions: tuple[WhittleTransition, ...]
    passive_transitions: tuple[WhittleTransition, ...]
    active_reward: Mapping[str, float] = field(default_factory=dict)
    passive_reward: Mapping[str, float] = field(default_factory=dict)
    active_cost: float = 0.0
    review_cost: float = 1.0
    discount: float = 0.9


@dataclass(frozen=True, slots=True)
class WhittleRow:
    """The index and allocation for one candidate."""

    candidate_id: str
    index: float
    selected: bool
    review_cost: float
    reason: str


@dataclass(frozen=True, slots=True)
class WhittleSchedule:
    """The ordered Whittle schedule."""

    budget: float
    spent: float
    rows: tuple[WhittleRow, ...]
    selected: tuple[WhittleRow, ...]
    deferred: tuple[WhittleRow, ...]


def _rows(
    transitions: tuple[WhittleTransition, ...],
    state: str,
) -> tuple[WhittleTransition, ...]:
    return tuple(item for item in transitions if item.state == state)


def _validate(candidate: WhittleCandidate) -> None:
    if not candidate.states:
        raise ValueError("a Whittle candidate needs at least one state")
    if candidate.start not in candidate.states:
        raise ValueError(f"unknown start state: {candidate.start!r}")
    if not 0.0 <= candidate.discount <= 1.0:
        raise ValueError("discount must be between zero and one")
    for transitions in (candidate.active_transitions, candidate.passive_transitions):
        for item in transitions:
            if item.state not in candidate.states or item.next_state not in candidate.states:
                raise ValueError(f"transition refers to an unknown state: {item}")
            if not 0.0 <= item.probability <= 1.0:
                raise ValueError("transition probability must be between zero and one")
        for state in candidate.states:
            values = _rows(transitions, state)
            if values and abs(sum(item.probability for item in values) - 1.0) > 1e-6:
                raise ValueError(f"transitions for {state!r} do not sum to one")


def _expectation(
    transitions: tuple[WhittleTransition, ...],
    state: str,
    values: Mapping[str, float],
) -> float:
    return sum(
        item.probability * values.get(item.next_state, 0.0)
        for item in _rows(transitions, state)
    )


def _values(candidate: WhittleCandidate, subsidy: float) -> dict[str, float]:
    """Value iteration for the single arm with a passive subsidy."""
    values = {state: 0.0 for state in candidate.states}
    for _ in range(1000):
        updated: dict[str, float] = {}
        for state in candidate.states:
            active = (
                float(candidate.active_reward.get(state, 0.0))
                - candidate.active_cost
                + candidate.discount
                * _expectation(candidate.active_transitions, state, values)
            )
            passive = (
                float(candidate.passive_reward.get(state, 0.0))
                + subsidy
                + candidate.discount
                * _expectation(candidate.passive_transitions, state, values)
            )
            updated[state] = max(active, passive)
        if max(abs(updated[state] - values[state]) for state in candidate.states) < 1e-9:
            return updated
        values = updated
    return values


def _passive_is_better(candidate: WhittleCandidate, subsidy: float) -> bool:
    values = _values(candidate, subsidy)
    state = candidate.start
    active = (
        float(candidate.active_reward.get(state, 0.0))
        - candidate.active_cost
        + candidate.discount
        * _expectation(candidate.active_transitions, state, values)
    )
    passive = (
        float(candidate.passive_reward.get(state, 0.0))
        + subsidy
        + candidate.discount
        * _expectation(candidate.passive_transitions, state, values)
    )
    return passive >= active


def whittle_index(
    candidate: WhittleCandidate,
    *,
    lower: float = -10.0,
    upper: float = 10.0,
    iterations: int = 60,
) -> float:
    """Return the subsidy where passive becomes at least as good as active."""
    _validate(candidate)
    if _passive_is_better(candidate, lower):
        return round(lower, 6)
    if not _passive_is_better(candidate, upper):
        return round(upper, 6)
    low, high = lower, upper
    for _ in range(max(1, iterations)):
        mid = (low + high) / 2
        if _passive_is_better(candidate, mid):
            high = mid
        else:
            low = mid
    return round((low + high) / 2, 6)


class WhittleScheduler:
    """Rank candidates by their exact Whittle index and allocate attention."""

    name = "aads.whittle.v1"

    def __init__(
        self,
        *,
        lower: float = -10.0,
        upper: float = 10.0,
        iterations: int = 60,
    ) -> None:
        self.lower = lower
        self.upper = upper
        self.iterations = iterations

    def schedule(
        self,
        candidates: list[WhittleCandidate] | tuple[WhittleCandidate, ...],
        *,
        budget: float = 1.0,
    ) -> WhittleSchedule:
        limit = max(0.0, float(budget))
        rows = [
            (candidate, whittle_index(candidate, lower=self.lower, upper=self.upper, iterations=self.iterations))
            for candidate in candidates
        ]
        rows.sort(key=lambda item: (-item[1], item[0].id))
        spent = 0.0
        schedule: list[WhittleRow] = []
        for candidate, index in rows:
            review_cost = max(1e-9, float(candidate.review_cost))
            selected = spent + review_cost <= limit + 1e-9
            if selected:
                spent += review_cost
                reason = "within attention budget"
            else:
                reason = "attention budget exhausted"
            schedule.append(
                WhittleRow(
                    candidate_id=candidate.id,
                    index=index,
                    selected=selected,
                    review_cost=round(review_cost, 6),
                    reason=reason,
                )
            )
        selected_rows = tuple(row for row in schedule if row.selected)
        deferred_rows = tuple(row for row in schedule if not row.selected)
        return WhittleSchedule(
            budget=round(limit, 6),
            spent=round(spent, 6),
            rows=tuple(schedule),
            selected=selected_rows,
            deferred=deferred_rows,
        )


__all__ = [
    "WhittleCandidate",
    "WhittleRow",
    "WhittleSchedule",
    "WhittleScheduler",
    "WhittleTransition",
    "whittle_index",
]
