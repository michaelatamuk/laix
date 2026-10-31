"""One public entry point for every LAIX decision.

An app describes what is happening and what it is allowed to do. ``Layer``
chooses one of its generic policies, returns the same decision shape every time,
and keeps the history needed to execute, measure and record that decision.

There is no app-specific branch here. The two built-in policies are generic
strategies:

* action selection: the app supplies a situation and the options it can afford;
* attention allocation: the app supplies signals and its limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from . import attention
from .contracts import Decision as CoreDecision
from .contracts import Situation
from .execution import ExecutionBridge
from .runtime import DecisionRuntime


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    id: str
    kind: str = "reference"
    quote: str | None = None
    source: str | None = None
    confidence: float | None = None


@dataclass(frozen=True, slots=True)
class Intent:
    capability: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Escalation:
    target: str
    reason: str = ""


@dataclass(frozen=True, slots=True)
class Breakdown:
    severity: float = 0.0
    due: float = 0.0
    confidence: float = 0.0
    interruption: float = 0.0
    learned: float = 0.0
    total: float = 0.0


@dataclass(frozen=True, slots=True)
class Decision:
    """The one decision shape returned by every policy."""

    verb: str
    confidence: float
    reason_code: str
    rationale: str
    decision_id: str = ""
    policy_version: str = ""
    action_id: str | None = None
    evidence: tuple[EvidenceRef, ...] = ()
    requires_approval: bool = False
    score: float | None = None
    breakdown: Breakdown | None = None
    intent: Intent | None = None
    escalation: Escalation | None = None
    cost_of_waiting: float = 0.0
    reversible: bool = False
    undo_hint: str | None = None
    trace_id: str = ""
    deliver: bool = True
    record: bool = True
    created_at: str | None = None

    def __post_init__(self) -> None:
        if self.verb not in {"wait", "observe", "guide", "ask", "act", "verify", "escalate"}:
            raise ValueError(f"unknown verb: {self.verb!r}")
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return asdict(self)


@dataclass(frozen=True, slots=True)
class DecisionRequest:
    """One request, whichever generic policy the app needs.

    Provide ``situation`` and ``options`` for action selection, or ``signals``
    and ``context`` for attention allocation. Both paths return ``Decision``.
    """

    subject: str
    at: str
    signals: tuple[Any, ...] = ()
    context: Any = None
    situation: Situation | None = None
    options: tuple[Any, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)


def _evidence(items: Iterable[Any] | None) -> tuple[EvidenceRef, ...]:
    out: list[EvidenceRef] = []
    for item in items or ():
        if isinstance(item, EvidenceRef):
            out.append(item)
        elif isinstance(item, str):
            out.append(EvidenceRef(id=item))
        elif isinstance(item, dict):
            out.append(EvidenceRef(**item))
        else:
            out.append(EvidenceRef(id=str(item)))
    return tuple(out)


def _intent(value: Any) -> Intent | None:
    if value is None:
        return None
    if isinstance(value, Intent):
        return value
    if isinstance(value, dict):
        return Intent(str(value.get("capability", "")), dict(value.get("args") or {}))
    return Intent(str(getattr(value, "capability", "")), dict(getattr(value, "args", {}) or {}))


def _escalation(value: Any) -> Escalation | None:
    if value is None:
        return None
    if isinstance(value, Escalation):
        return value
    if isinstance(value, dict):
        return Escalation(str(value.get("target", "")), str(value.get("reason", "")))
    return Escalation(str(getattr(value, "target", "")), str(getattr(value, "reason", "")))


def _breakdown(value: Any) -> Breakdown | None:
    if value is None:
        return None
    if isinstance(value, Breakdown):
        return value
    data = value if isinstance(value, dict) else getattr(value, "as_dict", lambda: {})()
    return Breakdown(
        severity=float(data.get("severity", 0.0)),
        due=float(data.get("due", 0.0)),
        confidence=float(data.get("confidence", 0.0)),
        interruption=float(data.get("interruption", 0.0)),
        learned=float(data.get("learned", 0.0)),
        total=float(data.get("total", 0.0)),
    )


def from_core(decision: CoreDecision) -> Decision:
    return Decision(
        verb=decision.verb,
        confidence=decision.confidence,
        reason_code="policy_rule",
        rationale=decision.rationale,
        decision_id=decision.id,
        policy_version=decision.policy_version,
        action_id=decision.action_id,
        requires_approval=decision.requires_approval,
        score=decision.utility,
        trace_id=decision.trace_id,
        created_at=decision.created_at,
    )


def from_attention(decision: attention.Decision) -> Decision:
    verb = "guide" if decision.action == "notify" else decision.action
    return Decision(
        verb=verb,
        confidence=decision.confidence,
        reason_code=decision.reason,
        rationale=decision.reason,
        evidence=_evidence(decision.evidence_refs),
        requires_approval=decision.requires_approval,
        score=decision.score,
        breakdown=_breakdown(decision.breakdown),
        intent=_intent(decision.intent),
        escalation=_escalation(decision.escalation),
        cost_of_waiting=decision.cost_of_waiting,
        reversible=decision.reversible,
        undo_hint=decision.undo_hint,
        trace_id=decision.trace_id,
        deliver=decision.deliver,
        record=decision.record,
    )


class Layer:
    """The single object an app talks to."""

    def __init__(self, runtime: DecisionRuntime | None = None) -> None:
        self.runtime = runtime or DecisionRuntime()
        self._core_decisions: dict[str, CoreDecision] = {}

    def decide(self, request: DecisionRequest) -> list[Decision]:
        if request.situation is not None or request.options:
            if request.situation is None:
                raise ValueError("action selection needs a situation")
            decision = self.runtime.decide(request.situation, request.options, attributes=request.attributes)
            self._core_decisions[decision.id] = decision
            return [from_core(decision)]
        if request.context is None:
            raise ValueError("attention allocation needs a context with now")
        decisions = attention.decide(request.signals, request.context)
        return [from_attention(item) for item in decisions]

    def execute(self, decision: Decision, *, actor: str, approver: str | None = None) -> Any:
        core = self._core_decisions.get(decision.decision_id)
        if core is None:
            raise ValueError("this decision has no executable action in this layer")
        return self.runtime.execute(core, actor=actor, approver=approver)

    def measure(self, decision: Decision, **kwargs: Any) -> Any:
        return self.runtime.measure(decision.decision_id, **kwargs)

    def bridge(self) -> ExecutionBridge:
        return self.runtime.bridge


__all__ = [
    "Breakdown",
    "Decision",
    "DecisionRequest",
    "Escalation",
    "EvidenceRef",
    "Intent",
    "Layer",
    "from_attention",
    "from_core",
]
