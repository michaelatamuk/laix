"""The planner contract: a problem in, a planner result out.

``PlannerPolicy`` is the one adapter between an external solver (JEV, OR-Tools,
a POMDP library or a future LAIX planner) and the policy interface. The planner
owns the search; the policy owns the conversion to the one ``Decision`` shape.
"""

from __future__ import annotations

from ...decisions import Decision, DecisionRequest
from .planner import Planner
from .planner_input import PlannerInput
from .planner_result import PlannerResult


def to_planner_input(request: DecisionRequest) -> PlannerInput:
    """Project the public request onto the planner's input."""
    return PlannerInput(
        subject=request.subject,
        at=request.at,
        situation=request.situation,
        options=tuple(request.options),
        signals=tuple(request.signals),
        context=request.context,
        attributes=dict(request.attributes),
    )


def to_decision(
    planner_result: PlannerResult,
    request: DecisionRequest,
    *,
    decision_id: str = "",
    trace_id: str = "",
    policy_version: str = "planner.v1",
) -> Decision:
    """Turn one plan into the public decision shape.

    This is the single conversion used by ``PlannerPolicy``; an adapter that
    calls a planner directly can use it too, so every planner path returns the
    same shape.
    """
    return Decision(
        verb=planner_result.verb,
        confidence=planner_result.confidence,
        reason_code=planner_result.reason_code,
        rationale=planner_result.rationale,
        decision_id=decision_id,
        trace_id=trace_id,
        action_id=planner_result.action_id,
        intent=planner_result.intent,
        requires_approval=planner_result.requires_approval,
        reversible=planner_result.reversible,
        undo_hint=planner_result.undo_hint,
        score=planner_result.score,
        alternatives=tuple(planner_result.alternatives),
        attributes={**request.attributes, **planner_result.attributes},
        policy_version=policy_version,
    )


class PlannerPolicy:
    """Wrap any ``Planner`` as a policy."""

    def __init__(self, planner: Planner, *, name: str = "planner.v1") -> None:
        self.planner = planner
        self.name = name
        self.version = name

    def decide(
        self,
        request: DecisionRequest,
        *,
        decision_id: str = "",
        trace_id: str = "",
    ) -> list[Decision]:
        planner_result = self.planner.solve(to_planner_input(request))
        return [
            to_decision(
                planner_result,
                request,
                decision_id=decision_id,
                trace_id=trace_id,
                policy_version=self.name,
            )
        ]


__all__ = [
    "Planner",
    "PlannerInput",
    "PlannerPolicy",
    "PlannerResult",
    "to_decision",
    "to_planner_input",
]
