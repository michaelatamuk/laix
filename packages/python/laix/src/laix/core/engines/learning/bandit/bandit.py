"""A deterministic upper-confidence-bound learner over named arms."""

from __future__ import annotations

import math
from typing import Any, Callable, Iterable

from ....support.values import clamp
from .arm import Arm
from ....domain.outcomes import Outcome
from .rewards import reward_for_label


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
        self.get(arm_id)
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


__all__ = ["UCBBandit"]
