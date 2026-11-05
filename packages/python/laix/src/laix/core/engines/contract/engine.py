"""The decision-engine contract: a problem in, a plan out.

``EnginePolicy`` is the one adapter between an external solver (JEV, OR-Tools,
a POMDP library or a future LAIX planner) and the policy interface. The engine
owns the search; the policy owns the conversion to the one ``Decision`` shape.
"""

from __future__ import annotations

from ...decisions import Decision, DecisionRequest
from .decision_engine import DecisionEngine
from .decision_problem import DecisionProblem
from .plan import Plan


def to_problem(request: DecisionRequest) -> DecisionProblem:
    """Project the public request onto the engine's input."""
    return DecisionProblem(
        subject=request.subject,
        at=request.at,
        situation=request.situation,
        options=tuple(request.options),
        signals=tuple(request.signals),
        context=request.context,
        attributes=dict(request.attributes),
    )


def to_decision(
    plan: Plan,
    request: DecisionRequest,
    *,
    decision_id: str = "",
    trace_id: str = "",
    policy_version: str = "engine.v1",
) -> Decision:
    """Turn one plan into the public decision shape.

    This is the single conversion used by ``EnginePolicy``; an adapter that
    calls an engine directly can use it too, so every engine path returns the
    same shape.
    """
    return Decision(
        verb=plan.verb,
        confidence=plan.confidence,
        reason_code=plan.reason_code,
        rationale=plan.rationale,
        decision_id=decision_id,
        trace_id=trace_id,
        action_id=plan.action_id,
        intent=plan.intent,
        requires_approval=plan.requires_approval,
        reversible=plan.reversible,
        undo_hint=plan.undo_hint,
        score=plan.score,
        alternatives=tuple(plan.alternatives),
        attributes={**request.attributes, **plan.attributes},
        policy_version=policy_version,
    )


class EnginePolicy:
    """Wrap any ``DecisionEngine`` as a policy."""

    def __init__(self, engine: DecisionEngine, *, name: str = "engine.v1") -> None:
        self.engine = engine
        self.name = name
        self.version = name

    def decide(
        self,
        request: DecisionRequest,
        *,
        decision_id: str = "",
        trace_id: str = "",
    ) -> list[Decision]:
        plan = self.engine.solve(to_problem(request))
        return [
            to_decision(
                plan,
                request,
                decision_id=decision_id,
                trace_id=trace_id,
                policy_version=self.name,
            )
        ]


__all__ = [
    "DecisionEngine",
    "DecisionProblem",
    "EnginePolicy",
    "Plan",
    "to_decision",
    "to_problem",
]
