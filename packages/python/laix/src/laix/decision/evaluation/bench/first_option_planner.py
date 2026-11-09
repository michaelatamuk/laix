"""Naive baseline: take the first option the host offers."""

from __future__ import annotations

from .baseline_plans import baseline_plan, baseline_wait
from ...contract.planner_input import PlannerInput
from ...contract.planner_result import PlannerResult


class FirstOptionPlanner:
    """Naive baseline: take the first option the host offers."""

    name = "first.v1"

    def solve(self, problem: PlannerInput) -> PlannerResult:
        if not problem.options:
            return baseline_wait("no_options", "there are no options")
        option = problem.options[0]
        return baseline_plan(option, "first_option", "the first option was taken")


__all__ = ["FirstOptionPlanner"]
