"""Counterfactual decisions across planners and commitment verification."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime

from ...contract.planner import Planner
from ...contract.planner_policy import PlannerInput
from ...domain.commitments import CommitmentGraph


@dataclass(frozen=True, slots=True)
class CounterfactualOutcome:
    """The decision under one counterfactual input."""

    name: str
    base_action_id: str | None
    counterfactual_action_id: str | None
    changed: bool


@dataclass(frozen=True, slots=True)
class DecisionCounterfactualResult:
    """The base action and the counterfactual outcomes that flip it."""

    base_action_id: str | None
    outcomes: tuple[CounterfactualOutcome, ...]

    @property
    def flips(self) -> tuple[CounterfactualOutcome, ...]:
        return tuple(item for item in self.outcomes if item.changed)


def decision_counterfactual(
    problem: PlannerInput,
    planner: Planner,
    candidates: Mapping[str, PlannerInput],
) -> DecisionCounterfactualResult:
    """Solve the base problem and each named counterfactual."""
    base = planner.solve(problem)
    outcomes = tuple(
        CounterfactualOutcome(
            name=name,
            base_action_id=base.action_id,
            counterfactual_action_id=(result := planner.solve(candidate)).action_id,
            changed=result.action_id != base.action_id,
        )
        for name, candidate in candidates.items()
    )
    return DecisionCounterfactualResult(
        base_action_id=base.action_id,
        outcomes=outcomes,
    )


def commitment_verification_counterfactual(
    problem: PlannerInput,
    planner: Planner,
    *,
    now: datetime | None = None,
) -> DecisionCounterfactualResult:
    """Show which external verification would change the decision."""
    attributes = problem.attributes or {}
    graph = attributes.get("commitment_graph")
    if not isinstance(graph, CommitmentGraph):
        return decision_counterfactual(problem, planner, {})

    timestamp = (now or datetime.fromisoformat(problem.at)).isoformat()
    candidates: dict[str, PlannerInput] = {}
    for item in graph.external:
        if item.trusted:
            continue
        replacement = replace(item, source="verified", verified_at=timestamp)
        external = tuple(
            replacement if other.key == item.key else other
            for other in graph.external
        )
        candidate_graph = CommitmentGraph(graph.local, external)
        name = f"{item.owner}/{item.id}"
        candidates[name] = replace(
            problem,
            attributes={**attributes, "commitment_graph": candidate_graph},
        )
    return decision_counterfactual(problem, planner, candidates)


__all__ = [
    "CounterfactualOutcome",
    "DecisionCounterfactualResult",
    "commitment_verification_counterfactual",
    "decision_counterfactual",
]
