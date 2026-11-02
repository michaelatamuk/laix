"""A learned policy: choose the arm the outcomes say is working.

``BanditPolicy`` puts the UCB learner behind the policy interface. It reads
generic arms from ``DecisionRequest.attributes`` or from the bandit itself, picks
the best arm inside the risk and budget limits, and accepts outcome rewards so
the next decision improves.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from ....decisions import Decision, Intent
from ....outcome_learning import Arm, Outcome, UCBBandit
from .._support import decision, number, value


def _arm(item: Any) -> Arm:
    if isinstance(item, Arm):
        return item
    return Arm(
        id=str(item.get("id", "")),
        prior_mean=float(item.get("prior_mean", 0.5)),
        prior_weight=float(item.get("prior_weight", 1.0)),
        cost=float(item.get("cost", 0.0)),
        risk=float(item.get("risk", 0.0)),
    )


class BanditPolicy:
    name = "bandit.v1"
    version = "0.8.0"

    def __init__(
        self,
        bandit: UCBBandit | None = None,
        *,
        exploration: float = 1.4,
        max_risk: float = 1.0,
        budget: float = float("inf"),
    ) -> None:
        self.bandit = bandit or UCBBandit(exploration=exploration)
        self.max_risk = max_risk
        self.budget = budget

    def decide(self, request: Any) -> list[Decision]:
        for item in tuple(value(request, "arms", ()) or ()):
            self.bandit.add(_arm(item))

        if not self.bandit.arms():
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="no_arms",
                    rationale="the learner has no arm to choose",
                    confidence=0.5,
                )
            ]

        chosen = self.bandit.choose(
            max_risk=number(request, "max_risk", self.max_risk),
            budget=number(request, "budget", self.budget),
            exclude=tuple(value(request, "exclude", ()) or ()),
        )
        if chosen is None:
            return [
                decision(
                    policy=self.name,
                    verb="wait",
                    reason_code="no_arm_within_limits",
                    rationale="every arm breaks the risk or budget limit",
                    confidence=0.7,
                )
            ]

        mean = self.bandit.mean(chosen.id)
        return [
            decision(
                policy=self.name,
                verb="act",
                reason_code="bandit_choice",
                rationale=f"choose arm {chosen.id} with learned reward {mean:.2f}",
                confidence=min(0.98, 0.5 + mean * 0.4),
                intent=Intent("act", {"arm": chosen.id}),
                score=round(mean, 6),
                requires_approval=bool(value(request, "requires_approval", False)),
                action_id=chosen.id,
            )
        ]

    def record(self, arm_id: str, reward: float) -> Arm:
        """Record one reward in ``0..1`` for an arm."""
        return self.bandit.update(arm_id, reward)

    def learn(self, outcomes: Iterable[Outcome], arm_of: Callable[[str], str]) -> int:
        """Learn from labelled outcomes; ``arm_of`` maps a decision id to an arm."""
        return self.bandit.learn(outcomes, arm_of)


__all__ = ["BanditPolicy"]
