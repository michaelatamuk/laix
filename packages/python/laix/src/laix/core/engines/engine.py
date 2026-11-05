"""The decision-engine contract: a problem in, a plan out.

``EnginePolicy`` is the one adapter between an external solver (JEV, OR-Tools,
a POMDP library or a future LAIX planner) and the policy interface. The engine
owns the search; the policy owns the conversion to the one ``Decision`` shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..decisions import Decision, DecisionRequest, Intent


@dataclass(frozen=True, slots=True)
class DecisionProblem:
    """What an engine may use to solve one task."""

    subject: str
    at: str
    situation: Any = None
    options: tuple[Any, ...] = ()
    signals: tuple[Any, ...] = ()
    context: Any = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Plan:
    """The engine's answer, before it becomes a ``Decision``."""

    verb: str
    confidence: float
    reason_code: str
    rationale: str
    action_id: str | None = None
    intent: Intent | None = None
    requires_approval: bool = False
    reversible: bool = False
    undo_hint: str | None = None
    score: float | None = None
    alternatives: tuple[dict[str, Any], ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)


class DecisionEngine(Protocol):
    """An external or built-in solver behind ``EnginePolicy``."""

    def solve(self, problem: DecisionProblem) -> Plan:
        ...


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
            Decision(
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
                policy_version=self.name,
            )
        ]


__all__ = [
    "DecisionEngine",
    "DecisionProblem",
    "EnginePolicy",
    "Plan",
    "to_problem",
]
