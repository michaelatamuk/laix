"""A hand-built integration baseline for fair comparison.

This is deliberately not part of the LAIX planner package. It models the kind of glue code a host
would write without a unified decision contract: hard gates, then commitments, then reversibility,
then attention, then utility.
"""

from __future__ import annotations

from typing import Any

from laix import PlannerResult
from laix.core.engines.planners.human_attention.human_attention_planner import (
    _remaining,
    approval_state,
    human_attention_effect,
)
from laix.core.engines.planners.commitment.commitment_planner import (
    _commitments,
    commitment_effect,
)
from laix.core.engines.planners.utility.utility_planner import (
    UtilityPlanner,
    _approval_required,
    _constraint_blocker,
)


class GlueBaseline:
    """Filter by each concern in order, then choose the highest utility."""

    name = "glue.v1"

    def solve(self, problem: Any) -> PlannerResult:
        options = list(problem.options)
        if not options:
            return self._wait("no_options", "there are no options")

        model = UtilityPlanner()._model_for(problem)
        active = _commitments(problem)
        remaining = _remaining(problem)

        candidates = [
            option
            for option in options
            if model.feasible(option) and _constraint_blocker(problem, option) is None
        ]
        if not candidates:
            return self._wait("no_feasible_option", "every option breaks a hard limit")

        if active:
            non_violating = [
                option
                for option in candidates
                if not (set(commitment_effect(option).violates) & set(active))
            ]
            if not non_violating:
                return self._wait("commitment_blocked", "every option violates an open promise")
            candidates = non_violating

        reversible = [option for option in candidates if option.reversible]
        if reversible:
            candidates = reversible

        approval = _approval_required(problem)
        affordable = []
        for option in candidates:
            effect = human_attention_effect(
                option,
                approval=approval,
                approval_state=approval_state(problem, option),
            )
            if effect.requires_attention and effect.cost > remaining:
                continue
            affordable.append(option)
        if not affordable:
            return self._wait("attention_exhausted", "every option needs more attention")
        candidates = affordable

        candidates.sort(key=lambda option: (-model.score(option), option.id))
        best = candidates[0]
        return PlannerResult(
            verb=best.verb,
            confidence=1.0,
            reason_code="glue_baseline",
            rationale=f"{best.id} survives the hard gates and has the highest utility",
            action_id=best.id,
            requires_approval=best.requires_approval or approval,
            reversible=best.reversible,
            score=model.score(best),
            attributes={"glue": True},
        )

    @staticmethod
    def _wait(reason_code: str, rationale: str) -> PlannerResult:
        return PlannerResult(
            verb="wait",
            confidence=1.0,
            reason_code=reason_code,
            rationale=rationale,
            score=0.0,
        )


__all__ = ["GlueBaseline"]
