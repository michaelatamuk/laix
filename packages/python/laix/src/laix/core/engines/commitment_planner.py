"""Commitment-aware planning: promises are part of the decision state.

The planner keeps the ordinary utility score and adds the effect of an action
on open commitments: fulfilling a promise, breaking one, or creating a new one.
It is deliberately deterministic and training-free; the commitments and their
due times come from the host.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..decisions import ActionOption
from ..planning import Commitment, CommitmentLedger
from ..support.time import parse_iso
from ..support.values import clamp
from .engine import DecisionProblem, Plan
from .utility import (
    UtilityEngine,
    UtilityModel,
    _approval_required,
    _constraint_blocker,
)


@dataclass(frozen=True, slots=True)
class CommitmentWeights:
    """How much each commitment effect changes the utility score."""

    keep: float = 0.35
    violate: float = 1.0
    create: float = 0.10
    due: float = 0.25

    def __post_init__(self) -> None:
        for name in ("keep", "violate", "create", "due"):
            if getattr(self, name) < 0:
                raise ValueError(f"commitment weight {name!r} must not be negative")


@dataclass(frozen=True, slots=True)
class CommitmentEffect:
    """What one option does to the open commitments."""

    fulfills: tuple[str, ...] = ()
    violates: tuple[str, ...] = ()
    creates: tuple[str, ...] = ()
    hard: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "fulfills", _ids(self.fulfills))
        object.__setattr__(self, "violates", _ids(self.violates))
        object.__setattr__(self, "creates", _ids(self.creates))


@dataclass(frozen=True, slots=True)
class CommitmentScore:
    """The utility and commitment parts of one option's score."""

    utility: float
    commitment: float
    total: float
    fulfilled: tuple[str, ...] = ()
    violated: tuple[str, ...] = ()
    created: tuple[str, ...] = ()
    due_fulfilled: tuple[str, ...] = ()
    due_violated: tuple[str, ...] = ()
    blocked: str | None = None


def _ids(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Mapping):
        return (str(value.get("id", value)),)
    if isinstance(value, Iterable):
        return tuple(
            str(item.get("id", item)) if isinstance(item, Mapping) else str(item)
            for item in value
        )
    return (str(value),)


def commitment_effect(option: ActionOption) -> CommitmentEffect:
    """Read an option's commitment effect from ``params``.

    Supported shape::

        params={"commitments": {"fulfills": ["c1"], "violates": ["c2"]}}
        params={"fulfills": ["c1"], "creates": [{"id": "c3"}]}
    """
    params = getattr(option, "params", {}) or {}
    payload = params.get("commitments", params.get("commitment", params))
    if not isinstance(payload, Mapping):
        return CommitmentEffect()

    def pick(key: str) -> Any:
        value = payload.get(key)
        if value is None and payload is not params:
            value = params.get(key)
        return value

    return CommitmentEffect(
        fulfills=pick("fulfills"),
        violates=pick("violates"),
        creates=pick("creates"),
        hard=bool(pick("hard")),
    )


def _active_commitments(problem: DecisionProblem) -> dict[str, Commitment]:
    attributes = problem.attributes or {}
    raw = attributes.get("commitments")
    if raw is None:
        raw = attributes.get("commitment_ledger")
    if raw is None:
        return {}
    if isinstance(raw, CommitmentLedger):
        return {item.id: item for item in raw.open()}
    if isinstance(raw, Mapping):
        raw = raw.get("commitments", ())
    items: list[Commitment] = []
    for item in raw or ():
        if isinstance(item, Commitment):
            items.append(item)
        elif isinstance(item, Mapping):
            items.append(Commitment.from_dict(dict(item)))
    return {item.id: item for item in items if item.status == "open"}


def _now(problem: DecisionProblem) -> datetime:
    return parse_iso(problem.at) or datetime.now(timezone.utc)


def _score_option(
    option: ActionOption,
    model: UtilityModel,
    active: dict[str, Commitment],
    weights: CommitmentWeights,
    now: datetime,
) -> CommitmentScore:
    effect = commitment_effect(option)
    fulfilled = tuple(item for item in effect.fulfills if item in active)
    violated = tuple(item for item in effect.violates if item in active)
    created = tuple(item for item in effect.creates if item not in active)
    due_fulfilled = tuple(item for item in fulfilled if active[item].is_due(now))
    due_violated = tuple(item for item in violated if active[item].is_due(now))
    commitment = (
        weights.keep * len(fulfilled)
        + weights.due * len(due_fulfilled)
        - weights.violate * len(violated)
        - weights.due * len(due_violated)
        - weights.create * len(created)
    )
    blocked = (
        f"hard commitment: {', '.join(violated)}"
        if effect.hard and violated
        else None
    )
    utility = model.score(option)
    return CommitmentScore(
        utility=round(utility, 6),
        commitment=round(commitment, 6),
        total=round(utility + commitment, 6),
        fulfilled=fulfilled,
        violated=violated,
        created=created,
        due_fulfilled=due_fulfilled,
        due_violated=due_violated,
        blocked=blocked,
    )


@dataclass(frozen=True, slots=True)
class _Row:
    option: ActionOption
    score: CommitmentScore
    feasible: bool
    blocker: str | None


class CommitmentAwareEngine:
    """Choose the option with the best utility plus commitment effect."""

    name = "commitment.v1"

    def __init__(
        self,
        model: UtilityModel | None = None,
        weights: CommitmentWeights | None = None,
    ) -> None:
        self.model = model
        self.weights = weights or CommitmentWeights()
        self._utility = UtilityEngine(model)

    def solve(self, problem: DecisionProblem) -> Plan:
        options = list(problem.options)
        if not options:
            return self._wait("no_options", "there are no options to score")

        model = self._utility._model_for(problem)
        active = _active_commitments(problem)
        now = _now(problem)
        rows: list[_Row] = []
        for option in options:
            score = _score_option(option, model, active, self.weights, now)
            blocker = _constraint_blocker(problem, option)
            feasible = model.feasible(option) and blocker is None and score.blocked is None
            rows.append(
                _Row(
                    option=option,
                    score=score,
                    feasible=feasible,
                    blocker=score.blocked or blocker,
                )
            )

        feasible = [row for row in rows if row.feasible]
        if not feasible:
            return self._wait(
                "no_feasible_option",
                "every option breaks a hard limit or a hard commitment",
            )

        feasible.sort(key=lambda row: (-row.score.total, row.option.id))
        best = feasible[0]
        second = feasible[1].score.total if len(feasible) > 1 else None
        return Plan(
            verb=best.option.verb,
            confidence=self._confidence(best.score.total, second),
            reason_code="commitment_aware",
            rationale=(
                f"{best.option.id} balances utility {best.score.utility:.3f} "
                f"and commitment score {best.score.commitment:+.3f}"
            ),
            action_id=best.option.id,
            requires_approval=(
                best.option.requires_approval
                or best.option.destructive
                or _approval_required(problem)
            ),
            reversible=best.option.reversible,
            score=best.score.total,
            alternatives=self._alternatives(rows, best.option.id),
            attributes={
                "utility": best.score.utility,
                "commitment_score": best.score.commitment,
                "commitments_fulfilled": list(best.score.fulfilled),
                "commitments_violated": list(best.score.violated),
                "commitments_created": list(best.score.created),
                "commitments_due_fulfilled": list(best.score.due_fulfilled),
            },
        )

    @staticmethod
    def _alternatives(rows: list[_Row], best_id: str) -> tuple[dict[str, Any], ...]:
        payload: list[dict[str, Any]] = []
        for row in rows:
            if row.option.id == best_id:
                continue
            if not row.feasible:
                reason = (
                    f"blocked by {row.blocker}"
                    if row.blocker
                    else "outside the hard limits"
                )
            else:
                reason = "lower commitment-adjusted score"
            payload.append(
                {
                    "action_id": row.option.id,
                    "verb": row.option.verb,
                    "name": row.option.name,
                    "utility": row.score.utility,
                    "commitment": row.score.commitment,
                    "total": row.score.total,
                    "rejected_because": reason,
                }
            )
        payload.sort(key=lambda item: (-float(item["total"]), str(item["action_id"])))
        return tuple(payload)

    @staticmethod
    def _confidence(best: float, second: float | None) -> float:
        if second is None:
            return 1.0
        gap = max(0.0, best - second)
        return clamp(0.5 + 0.5 * (gap / max(abs(best), 1e-9)))

    @staticmethod
    def _wait(reason_code: str, rationale: str) -> Plan:
        return Plan(
            verb="wait",
            confidence=1.0,
            reason_code=reason_code,
            rationale=rationale,
            score=0.0,
        )


__all__ = [
    "CommitmentAwareEngine",
    "CommitmentEffect",
    "CommitmentScore",
    "CommitmentWeights",
    "commitment_effect",
]
