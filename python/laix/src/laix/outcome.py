"""Outcome learning: did the decision actually help?

This module records measured outcomes, not clicks.  Attribution is explicit:
``attributed=True`` means the host can defend that the action caused the change;
otherwise the label is still recorded but excluded from the attributed summary.

Metrics have a direction.  ``time_to_assessment`` improves when it falls;
``precision`` improves when it rises.  Without that, a faster decision would be
scored as a regression.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Protocol, runtime_checkable

from .contracts import OUTCOME_DIRECTIONS, OUTCOME_LABELS, Outcome, clamp, iso, new_id


@runtime_checkable
class OutcomeStore(Protocol):
    """What an app supplies when outcomes outlive one request."""

    def add(self, outcome: Outcome) -> Outcome:
        ...

    def for_decision(self, decision_id: str) -> list[Outcome]:
        ...

    def all(self) -> list[Outcome]:
        ...

    def summary(self) -> dict[str, Any]:
        ...


def _signed_gain(delta: float, direction: str) -> float:
    return delta if direction == "higher-better" else -delta


def _label(delta: float, tolerance: float, direction: str) -> str:
    gain = _signed_gain(delta, direction)
    if gain > tolerance:
        return "helped"
    if gain < -tolerance:
        return "hurt"
    return "neutral"


@dataclass
class OutcomeLedger:
    tolerance: float = 1e-9
    records: list[Outcome] = field(default_factory=list)

    def record(
        self,
        decision_id: str,
        *,
        metric: str,
        before: float,
        after: float,
        attributed: bool = False,
        direction: str = "higher-better",
        evidence: dict[str, Any] | None = None,
        note: str = "",
        label: str | None = None,
        measured_at: str | None = None,
        tolerance: float | None = None,
    ) -> Outcome:
        if direction not in OUTCOME_DIRECTIONS:
            raise ValueError(f"unknown outcome direction: {direction}")
        delta = round(float(after) - float(before), 6)
        resolved = label or _label(delta, tolerance if tolerance is not None else self.tolerance, direction)
        if resolved not in OUTCOME_LABELS:
            raise ValueError(f"unknown outcome label: {resolved}")
        outcome = Outcome(
            id=new_id("OUT"),
            decision_id=decision_id,
            metric=metric,
            before=float(before),
            after=float(after),
            delta=delta,
            label=resolved,
            attributed=bool(attributed),
            direction=direction,
            evidence=dict(evidence or {}),
            measured_at=measured_at or iso(),
            note=note,
        )
        self.records.append(outcome)
        return outcome

    def add(self, outcome: Outcome) -> Outcome:
        self.records.append(outcome)
        return outcome

    def for_decision(self, decision_id: str) -> list[Outcome]:
        return [item for item in self.records if item.decision_id == decision_id]

    def all(self) -> list[Outcome]:
        return list(self.records)

    def summary(self) -> dict[str, Any]:
        """Measured gain, with attribution coverage stated separately."""
        attributed = [item for item in self.records if item.attributed]
        improved = [item for item in attributed if item.label == "helped"]
        hurt = [item for item in attributed if item.label == "hurt"]
        gains = [_signed_gain(item.delta, item.direction) for item in attributed]
        return {
            "measured": len(self.records),
            "attributed": len(attributed),
            "attributionCoverage": round(len(attributed) / max(1, len(self.records)), 3),
            "helped": len(improved),
            "neutral": len([item for item in attributed if item.label == "neutral"]),
            "hurt": len(hurt),
            "meanGain": round(sum(gains) / len(gains), 6) if gains else 0.0,
            "precision": round(len(improved) / max(1, len(attributed)), 3),
        }

    def by_metric(self) -> dict[str, dict[str, Any]]:
        rows: dict[str, dict[str, Any]] = {}
        for item in self.records:
            bucket = rows.setdefault(
                item.metric,
                {"measured": 0, "attributed": 0, "helped": 0, "hurt": 0, "gain": 0.0},
            )
            bucket["measured"] += 1
            if item.attributed:
                bucket["attributed"] += 1
                bucket["helped"] += int(item.label == "helped")
                bucket["hurt"] += int(item.label == "hurt")
                bucket["gain"] += _signed_gain(item.delta, item.direction)
        for bucket in rows.values():
            bucket["gain"] = round(bucket["gain"], 6)
        return rows

    def extend(self, records: Iterable[Outcome]) -> None:
        self.records.extend(records)

    def to_dict(self) -> dict[str, Any]:
        return {"tolerance": self.tolerance, "records": [item.to_dict() for item in self.records], "summary": self.summary()}


@dataclass(frozen=True, slots=True)
class Arm:
    """One choice the learner can pick, with an optional prior."""

    id: str
    prior_mean: float = 0.5
    prior_weight: float = 1.0
    cost: float = 0.0
    risk: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(self, "prior_mean", clamp(self.prior_mean))
        object.__setattr__(self, "prior_weight", max(0.0, float(self.prior_weight)))

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return asdict(self)


def reward_for_label(label: str) -> float | None:
    """Map a measured outcome label to a reward in ``0..1``.

    ``unknown`` returns ``None``: the learner skips it rather than inventing a
    reward.
    """
    key = (label or "").strip().lower()
    return {"helped": 1.0, "neutral": 0.5, "hurt": 0.0}.get(key)


class UCBBandit:
    """A deterministic upper-confidence-bound learner over named arms.

    UCB is used instead of Thompson sampling so replay and tests are stable. The
    exploration term is the only knob. An arm that has never been pulled is
    explored first.
    """

    def __init__(self, arms: Iterable[Arm] = (), *, exploration: float = 1.4) -> None:
        self.exploration = max(0.0, float(exploration))
        self._arms: dict[str, Arm] = {}
        self._pulls: dict[str, int] = {}
        self._rewards: dict[str, float] = {}
        for arm in arms:
            self.add(arm)

    def add(self, arm: Arm) -> None:
        name = arm.id.strip()
        if not name:
            raise ValueError("arm id is required")
        self._arms[name] = arm
        self._pulls.setdefault(name, 0)
        self._rewards.setdefault(name, 0.0)

    def arms(self) -> tuple[Arm, ...]:
        return tuple(self._arms.values())

    def get(self, arm_id: str) -> Arm:
        try:
            return self._arms[arm_id]
        except KeyError as exc:
            raise KeyError(f"unknown arm {arm_id!r}") from exc

    def update(self, arm_id: str, reward: float) -> Arm:
        self.get(arm_id)
        self._pulls[arm_id] += 1
        self._rewards[arm_id] += clamp(reward)
        return self._arms[arm_id]

    def learn(self, outcomes: Iterable[Outcome], arm_of: Callable[[str], str]) -> int:
        """Update from labelled outcomes; return how many were used."""
        used = 0
        for outcome in outcomes:
            reward = reward_for_label(outcome.label)
            if reward is None:
                continue
            self.update(arm_of(outcome.decision_id), reward)
            used += 1
        return used

    def pulls(self, arm_id: str) -> int:
        self.get(arm_id)
        return self._pulls[arm_id]

    def mean(self, arm_id: str) -> float:
        arm = self.get(arm_id)
        pulls = self._pulls[arm_id]
        total = arm.prior_mean * arm.prior_weight + self._rewards[arm_id]
        return clamp(total / max(arm.prior_weight + pulls, 1e-9))

    def score(self, arm_id: str) -> float:
        arm = self.get(arm_id)
        pulls = self._pulls[arm_id]
        if pulls == 0:
            return float("inf")
        total = sum(self._pulls.values())
        bonus = self.exploration * math.sqrt(math.log(total + 1) / pulls)
        return self.mean(arm_id) + float(bonus)

    def choose(
        self,
        *,
        max_risk: float = 1.0,
        budget: float = float("inf"),
        exclude: Iterable[str] = (),
    ) -> Arm | None:
        blocked = set(exclude)
        candidates = [
            arm
            for arm in self._arms.values()
            if arm.id not in blocked and arm.risk <= max_risk and arm.cost <= budget
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda arm: self.score(arm.id))

    def to_dict(self) -> dict[str, Any]:
        return {
            "exploration": self.exploration,
            "arms": [
                {
                    **arm.to_dict(),
                    "pulls": self._pulls[arm.id],
                    "mean": round(self.mean(arm.id), 6),
                }
                for arm in self._arms.values()
            ],
        }


__all__ = ["Arm", "OutcomeLedger", "OutcomeStore", "UCBBandit", "reward_for_label"]
