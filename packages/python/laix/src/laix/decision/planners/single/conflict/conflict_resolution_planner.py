"""Resolve explicit goal conflicts before normal planning."""

from __future__ import annotations

from typing import Any

from ....contract.planner import Planner
from ....contract.planner_policy import PlannerInput, PlannerResult


def _conflict_id(conflict: dict[str, Any]) -> str:
    explicit = conflict.get("id")
    if explicit is not None:
        return str(explicit)
    return f"{conflict.get('left')}:{conflict.get('right')}"


class ConflictResolutionPlanner:
    """Choose a conflict response, or delegate when there is no conflict."""

    name = "conflict_resolution.v1"

    def __init__(
        self,
        planner: Planner | None = None,
        *,
        severity_limit: float = 0.5,
        escalate_at: float = 0.8,
    ) -> None:
        if not 0.0 <= severity_limit <= 1.0:
            raise ValueError("severity_limit must be between zero and one")
        if not 0.0 <= escalate_at <= 1.0:
            raise ValueError("escalate_at must be between zero and one")
        self.planner = planner
        self.severity_limit = severity_limit
        self.escalate_at = escalate_at

    def solve(self, problem: PlannerInput) -> PlannerResult:
        attributes = problem.attributes or {}
        raw = attributes.get("goal_conflicts", ())
        conflicts = [
            dict(item)
            for item in raw
            if isinstance(item, dict)
            and float(item.get("severity", 0.0)) >= self.severity_limit
        ]
        if not conflicts:
            if self.planner is not None:
                return self.planner.solve(problem)
            return PlannerResult(
                verb="wait",
                confidence=1.0,
                reason_code="no_goal_conflict",
                rationale="no goal conflict needs resolution",
                score=0.0,
            )

        wanted = {_conflict_id(item) for item in conflicts}
        for option in problem.options:
            params = getattr(option, "params", {}) or {}
            resolves = {str(item) for item in params.get("resolves", ())}
            if wanted <= resolves:
                return PlannerResult(
                    verb=option.verb,
                    confidence=0.8,
                    reason_code="goal_conflict_resolved",
                    rationale=f"{option.id} resolves the active goal conflicts",
                    action_id=option.id,
                    attributes={"goal_conflicts": conflicts},
                )

        escalate = any(float(item.get("severity", 0.0)) >= self.escalate_at for item in conflicts)
        return PlannerResult(
            verb="escalate" if escalate else "ask",
            confidence=0.8,
            reason_code="goal_conflict" if escalate else "goal_conflict_needs_choice",
            rationale=f"{len(conflicts)} goal conflicts need a decision",
            attributes={"goal_conflicts": conflicts},
        )


__all__ = ["ConflictResolutionPlanner"]
