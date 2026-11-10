"""Decide whether an earlier decision still holds."""

from __future__ import annotations

from dataclasses import replace

from ...contract.planner import Planner
from ...contract.planner_policy import PlannerInput, PlannerResult


def _previous_action(problem: PlannerInput) -> str | None:
    attributes = problem.attributes or {}
    raw = attributes.get("previous_decision") or attributes.get("previous")
    if isinstance(raw, PlannerResult):
        return raw.action_id
    if hasattr(raw, "action_id"):
        return getattr(raw, "action_id", None)
    if isinstance(raw, dict):
        value = raw.get("action_id", raw.get("actionId"))
        return str(value) if value is not None else None
    value = attributes.get("previous_action_id")
    return str(value) if value is not None else None


class RevalidationPlanner:
    """Re-run a planner and decide ``hold``, ``revise`` or ``escalate``."""

    name = "revalidation.v1"

    def __init__(
        self,
        planner: Planner,
        *,
        escalate_on_infeasible: bool = True,
    ) -> None:
        self.planner = planner
        self.escalate_on_infeasible = escalate_on_infeasible

    def solve(self, problem: PlannerInput) -> PlannerResult:
        previous = _previous_action(problem)
        current = self.planner.solve(problem)
        if previous is None:
            return replace(
                current,
                reason_code="revalidated_new",
                attributes={
                    **current.attributes,
                    "previous_action_id": None,
                    "current_action_id": current.action_id,
                },
            )
        if current.action_id == previous:
            return PlannerResult(
                verb="wait",
                confidence=current.confidence,
                reason_code="decision_held",
                rationale=f"{previous} is still the best action",
                action_id=previous,
                score=current.score,
                attributes={
                    **current.attributes,
                    "previous_action_id": previous,
                    "current_action_id": current.action_id,
                    "held": True,
                },
            )
        if (
            self.escalate_on_infeasible
            and current.reason_code in {"no_feasible_option", "no_options"}
        ):
            return PlannerResult(
                verb="escalate",
                confidence=1.0,
                reason_code="decision_escalated",
                rationale=f"{previous} is no longer feasible",
                action_id=previous,
                attributes={
                    **current.attributes,
                    "previous_action_id": previous,
                    "current_action_id": current.action_id,
                    "escalated": True,
                },
            )
        return replace(
            current,
            reason_code="decision_revised",
            attributes={
                **current.attributes,
                "previous_action_id": previous,
                "current_action_id": current.action_id,
            },
        )


__all__ = ["RevalidationPlanner"]
