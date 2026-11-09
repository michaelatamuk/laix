"""Replan the remaining steps after some decisions were executed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..single.human_attention.human_attention_budget import HumanAttentionBudget
from .cabb import CABBPlanner
from .contract import DecisionScenario, DecisionStep


@dataclass(frozen=True, slots=True)
class ReplanResult:
    """The executed prefix and the newly planned suffix."""

    executed: tuple[str, ...]
    actions: tuple[str, ...]
    score: float
    attention_spent: float
    violations: tuple[str, ...]
    nodes: int
    optimal: bool
    reason: str


class ReplanPlanner:
    """Recompute the remaining chain from the state after a prefix."""

    name = "sequence.replan.v1"

    def __init__(self, planner: CABBPlanner | None = None) -> None:
        self.planner = planner or CABBPlanner()

    def replan(
        self,
        scenario: DecisionScenario,
        executed: tuple[str, ...],
        *,
        replacement_step: DecisionStep | None = None,
    ) -> ReplanResult:
        prefix = tuple(executed)
        if len(prefix) > len(scenario.steps):
            raise ValueError("the executed prefix is longer than the scenario")
        commitments, remaining = self.planner.advance(scenario, prefix)
        steps = list(scenario.steps[len(prefix):])
        if replacement_step is not None and steps:
            steps[0] = replacement_step
        if not steps:
            return ReplanResult(
                executed=prefix,
                actions=(),
                score=0.0,
                attention_spent=0.0,
                violations=(),
                nodes=0,
                optimal=True,
                reason="nothing left to replan",
            )
        budget = scenario.human_attention_budget
        next_budget = (
            None
            if budget is None
            else HumanAttentionBudget(
                total=budget.total,
                spent=max(0.0, budget.total - remaining),
            )
        )
        next_scenario = DecisionScenario(
            steps=tuple(steps),
            commitments=commitments,
            human_attention_budget=next_budget,
            open_penalty=scenario.open_penalty,
        )
        plan = self.planner.plan(next_scenario)
        return ReplanResult(
            executed=prefix,
            actions=plan.actions,
            score=plan.score,
            attention_spent=plan.attention_spent,
            violations=plan.violations,
            nodes=plan.nodes,
            optimal=plan.optimal,
            reason=f"replanned {len(steps)} remaining steps",
        )


def replan_decisions(
    scenario: DecisionScenario,
    executed: tuple[str, ...],
    **kwargs: Any,
) -> ReplanResult:
    """Functional shortcut for one replan."""
    return ReplanPlanner(**kwargs).replan(scenario, executed)


__all__ = ["ReplanPlanner", "ReplanResult", "replan_decisions"]
