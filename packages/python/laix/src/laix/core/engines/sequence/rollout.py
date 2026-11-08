"""Greedy rollout planning for finite decision sequences.

CABB searches the whole chain exactly. Rollout keeps the chain readable when
the horizon grows: for every option at the current step it completes the rest
greedily, scores the completed chain with CABB's evaluator, and keeps the first
option of the best chain. It is bounded by the horizon and is not exact.
"""

from __future__ import annotations

from typing import Any

from .cabb import CABBPlanner
from .contract import DecisionPlan, DecisionScenario


class RolloutPlanner:
    """Approximate finite-horizon planning by one-step rollout."""

    name = "sequence.rollout.v1"

    def __init__(self, planner: CABBPlanner | None = None) -> None:
        self.planner = planner or CABBPlanner()

    def plan(self, scenario: DecisionScenario) -> DecisionPlan:
        if not scenario.steps:
            return DecisionPlan((), 0.0, 0.0, (), 0, True)
        best: DecisionPlan | None = None
        nodes = 0
        for option in scenario.steps[0].options:
            actions = self.planner.greedy_actions(scenario, (option.id,))
            if len(actions) != len(scenario.steps):
                continue
            try:
                result = self.planner.evaluate(scenario, actions)
            except ValueError:
                continue
            nodes += 1
            if (
                best is None
                or result.score > best.score
                or (
                    result.score == best.score
                    and result.actions < best.actions
                )
            ):
                best = result
        if best is None:
            return DecisionPlan((), 0.0, 0.0, (), nodes, False)
        return DecisionPlan(
            actions=best.actions,
            score=best.score,
            attention_spent=best.attention_spent,
            violations=best.violations,
            nodes=nodes,
            optimal=False,
        )


def rollout_decisions(scenario: DecisionScenario, **kwargs: Any) -> DecisionPlan:
    """Functional shortcut for one rollout plan."""
    return RolloutPlanner(**kwargs).plan(scenario)


__all__ = ["RolloutPlanner", "rollout_decisions"]
