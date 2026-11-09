"""Attention-aware decision scheduling (AADS).

A deterministic index policy for the fleet-level question: which pending
decisions should receive scarce human attention now?

The full method is a restless multi-armed bandit. This prototype ranks each
candidate by a Whittle-style index:

    expected gain * urgency - waiting cost
    --------------------------------------
                 review cost

It is deliberately cheap and explainable. The caller supplies the risk,
deadline, commitment flag, information value, waiting cost and review cost.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from ...support.time import parse_iso


def _as_datetime(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        parsed = parse_iso(value)
        if parsed is not None:
            return parsed
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class AttentionCandidate:
    """One pending decision competing for human attention."""

    id: str
    risk: float = 0.0
    value: float = 0.0
    commitment: bool = False
    information_value: float = 0.0
    waiting_cost: float = 0.0
    review_cost: float = 1.0
    change_probability: float = 0.5
    deadline: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AttentionScheduleRow:
    """The score and allocation for one candidate."""

    candidate_id: str
    index: float
    expected_gain: float
    urgency: float
    review_cost: float
    selected: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AttentionSchedule:
    """The ranked schedule and the budget it used."""

    now: str
    budget: float
    spent: float
    rows: tuple[AttentionScheduleRow, ...]
    selected: tuple[AttentionScheduleRow, ...]
    deferred: tuple[AttentionScheduleRow, ...]


class AttentionScheduler:
    """Rank pending decisions with an attention-aware index policy."""

    name = "aads.v1"

    def __init__(
        self,
        *,
        risk_weight: float = 1.0,
        commitment_weight: float = 0.5,
        information_weight: float = 0.5,
        urgency_horizon_seconds: float = 3600.0,
    ) -> None:
        self.risk_weight = risk_weight
        self.commitment_weight = commitment_weight
        self.information_weight = information_weight
        self.urgency_horizon_seconds = max(1.0, urgency_horizon_seconds)

    def schedule(
        self,
        candidates: list[AttentionCandidate] | tuple[AttentionCandidate, ...],
        *,
        now: str | datetime | None = None,
        budget: float = 1.0,
    ) -> AttentionSchedule:
        current = _as_datetime(now)
        limit = max(0.0, float(budget))
        ordered: list[tuple[AttentionCandidate, float, float, float]] = []

        for candidate in candidates:
            review_cost = max(1e-9, float(candidate.review_cost))
            stakes = (
                max(0.0, float(candidate.value))
                + self.risk_weight * max(0.0, float(candidate.risk))
                + self.commitment_weight * (1.0 if candidate.commitment else 0.0)
                + self.information_weight * max(0.0, float(candidate.information_value))
            )
            expected_gain = max(0.0, float(candidate.change_probability)) * stakes
            urgency = self._urgency(candidate.deadline, current)
            index = (expected_gain * urgency - max(0.0, float(candidate.waiting_cost))) / review_cost
            ordered.append((candidate, index, expected_gain, urgency))

        ordered.sort(key=lambda item: (-item[1], item[0].id))
        spent = 0.0
        rows: list[AttentionScheduleRow] = []
        for candidate, index, expected_gain, urgency in ordered:
            review_cost = max(1e-9, float(candidate.review_cost))
            selected = spent + review_cost <= limit + 1e-9
            if selected:
                spent += review_cost
                reason = "within attention budget"
            else:
                reason = "attention budget exhausted"
            rows.append(
                AttentionScheduleRow(
                    candidate_id=candidate.id,
                    index=round(index, 6),
                    expected_gain=round(expected_gain, 6),
                    urgency=round(urgency, 6),
                    review_cost=round(review_cost, 6),
                    selected=selected,
                    reason=reason,
                )
            )

        selected_rows = tuple(row for row in rows if row.selected)
        deferred_rows = tuple(row for row in rows if not row.selected)
        return AttentionSchedule(
            now=current.isoformat(),
            budget=round(limit, 6),
            spent=round(spent, 6),
            rows=tuple(rows),
            selected=selected_rows,
            deferred=deferred_rows,
        )

    def _urgency(self, deadline: str | None, now: datetime) -> float:
        if not deadline:
            return 1.0
        due = _as_datetime(deadline)
        seconds = (due - now).total_seconds()
        if seconds <= 0:
            return 1.0 + self.urgency_horizon_seconds
        return 1.0 + self.urgency_horizon_seconds / max(1.0, seconds)


__all__ = [
    "AttentionCandidate",
    "AttentionSchedule",
    "AttentionScheduleRow",
    "AttentionScheduler",
]
