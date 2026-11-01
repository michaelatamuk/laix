"""The one decision shape every policy returns, and conversions into it.

Keeping the shape separate from ``Layer`` makes the public contract easy to read
and lets the runtime, policies and adapters share it without importing the
orchestrator.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .contracts import Decision as CoreDecision
from .contracts import Situation
from .policies.registry import PolicyError


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
    confidence_source: str = ""
    calibrated: bool = False

    def __post_init__(self) -> None:
        if self.verb not in {"wait", "observe", "guide", "ask", "act", "verify", "escalate"}:
            raise ValueError(f"unknown verb: {self.verb!r}")
        object.__setattr__(self, "confidence", max(0.0, min(1.0, float(self.confidence))))

    def basis(self) -> tuple[dict[str, Any], ...]:
        """A host-neutral basis for a decision record or explain view."""
        rows: list[dict[str, Any]] = [
            {"kind": "reason", "ref": self.reason_code, "note": self.rationale}
        ]
        for item in self.evidence:
            rows.append(
                {
                    "kind": item.kind,
                    "ref": item.id,
                    "note": item.quote or "",
                    "source": item.source or "",
                }
            )
        if self.escalation is not None:
            rows.append(
                {
                    "kind": "escalation",
                    "ref": self.escalation.target,
                    "note": self.escalation.reason,
                }
            )
        return tuple(rows)

    def to_dict(self) -> dict[str, Any]:
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
    confidence: float | None = None
    confidence_source: str = ""
    calibrated: bool = False


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


def from_attention(decision: Any) -> Decision:
    """Convert an attention-policy decision without importing the attention package."""
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


def coerce(value: Any) -> Decision:
    """Normalise a policy result to the one layer decision shape."""
    if isinstance(value, Decision):
        return value
    if isinstance(value, CoreDecision):
        return from_core(value)
    if hasattr(value, "action") and hasattr(value, "reason"):
        return from_attention(value)
    if isinstance(value, dict):
        return Decision(
            verb=str(value.get("verb") or value.get("action") or "wait"),
            confidence=float(value.get("confidence", 0.0)),
            reason_code=str(value.get("reason_code") or value.get("reason") or "policy_rule"),
            rationale=str(value.get("rationale") or value.get("reason") or ""),
            decision_id=str(value.get("decision_id", "")),
            requires_approval=bool(value.get("requires_approval", False)),
            score=value.get("score"),
            trace_id=str(value.get("trace_id", "")),
            deliver=bool(value.get("deliver", True)),
            record=bool(value.get("record", True)),
        )
    raise PolicyError(f"policy returned an unsupported decision: {type(value).__name__}")


__all__ = [
    "Breakdown",
    "Decision",
    "DecisionRequest",
    "Escalation",
    "EvidenceRef",
    "Intent",
    "coerce",
    "from_attention",
    "from_core",
]
