"""Choose which planner should answer one request."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace

from ....contract.planner import Planner
from ....contract.planner_policy import PlannerInput, PlannerResult
from ..commitment.commitment_planner import commitment_effect


def _default_selector(problem: PlannerInput) -> str:
    attributes = problem.attributes or {}
    hint = attributes.get("planner")
    if isinstance(hint, str):
        return hint
    options = tuple(problem.options)
    if (
        attributes.get("commitments")
        or attributes.get("commitment_ledger")
        or attributes.get("commitment_graph")
        or attributes.get("external_commitments")
        or any(
            commitment_effect(option).fulfills
            or commitment_effect(option).violates
            or commitment_effect(option).creates
            for option in options
        )
    ):
        return "commitment"
    if attributes.get("requires_approval") or any(
        option.requires_approval or option.destructive or option.risk >= 0.5
        for option in options
    ):
        return "execution"
    if (
        attributes.get("human_attention_budget")
        or attributes.get("attention_budget")
        or attributes.get("approval")
    ):
        return "human_attention"
    if attributes.get("mdp_model"):
        return "mdp"
    if attributes.get("pomdp_model"):
        return "pomdp"
    return "utility"


class PortfolioPlanner:
    """Select a planner from a named portfolio and delegate to it."""

    name = "portfolio.v1"

    def __init__(
        self,
        planners: Mapping[str, Planner],
        *,
        selector: Callable[[PlannerInput], str] | None = None,
        default: str | None = None,
    ) -> None:
        if not planners:
            raise ValueError("a portfolio needs at least one planner")
        self.planners = dict(planners)
        self.selector = selector or _default_selector
        self.default = default or next(iter(self.planners))
        if self.default not in self.planners:
            raise ValueError(f"unknown default planner: {self.default}")

    def solve(self, problem: PlannerInput) -> PlannerResult:
        selected = self.selector(problem)
        if selected not in self.planners:
            selected = self.default
        result = self.planners[selected].solve(problem)
        return replace(
            result,
            attributes={
                **result.attributes,
                "planner": selected,
                "portfolio": sorted(self.planners),
            },
        )


__all__ = ["PortfolioPlanner"]
