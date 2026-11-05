"""Naive baseline: take the option with the highest benefit."""

from __future__ import annotations

from .baseline_plans import baseline_plan, baseline_wait
from ..contract.decision_problem import DecisionProblem
from ..contract.plan import Plan


class HighestBenefitEngine:
    """Naive baseline: take the option with the highest benefit."""

    name = "benefit.v1"

    def solve(self, problem: DecisionProblem) -> Plan:
        if not problem.options:
            return baseline_wait("no_options", "there are no options")
        option = max(problem.options, key=lambda item: (item.expected_benefit, item.id))
        return baseline_plan(option, "highest_benefit", "the highest benefit was taken")


__all__ = ["HighestBenefitEngine"]
