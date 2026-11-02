"""The decision shapes: request, decision and normalisation into one answer.

``Decision`` and ``DecisionRequest`` are the two shapes a host and a policy
exchange. ``coerce`` and ``from_attention`` normalise any policy result into
the one public ``Decision``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .contracts import (
    SCHEMA_VERSION,
    VERBS,
    ActionOption,
    Situation,
)
from .errors import PolicyError


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
    options: tuple[ActionOption, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    confidence: float | None = None
    confidence_source: str = ""
    calibrated: bool = False


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

    def as_dict(self) -> dict[str, Any]:
        return {"capability": self.capability, "args": dict(self.args)}


@dataclass(frozen=True, slots=True)
class Escalation:
    target: str
    reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {"target": self.target, "reason": self.reason}


@dataclass(frozen=True, slots=True)
class Breakdown:
    severity: float = 0.0
    due: float = 0.0
    confidence: float = 0.0
    interruption: float = 0.0
    learned: float = 0.0
    total: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            "severity": round(self.severity, 2),
            "due": round(self.due, 2),
            "confidence": round(self.confidence, 2),
            "interruption": round(self.interruption, 2),
            "learned": round(self.learned, 2),
            "total": round(self.total, 2),
        }


@dataclass(frozen=True, slots=True)
class Decision:
    """The one decision shape returned by every policy and by ``Layer``."""

    verb: str
    confidence: float
    reason_code: str
    rationale: str
    decision_id: str = ""
    situation_id: str = ""
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
    alternatives: tuple[dict[str, Any], ...] = ()
    constraints_applied: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.verb not in VERBS:
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
        for item in self.constraints_applied:
            rows.append({"kind": "constraint", "ref": item, "note": ""})
        return tuple(rows)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


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


def from_attention(decision: Any) -> Decision:
    """Convert an ``AttentionDecision`` without importing the attention package."""
    return Decision(
        verb=decision.verb,
        confidence=decision.confidence,
        reason_code=decision.reason_code,
        rationale=decision.reason_code,
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
    """Normalise a policy result to the one public decision shape."""
    if isinstance(value, Decision):
        return value
    if hasattr(value, "signal_id") and hasattr(value, "verb"):
        return from_attention(value)
    if isinstance(value, dict):
        return Decision(
            verb=str(value.get("verb") or "wait"),
            confidence=float(value.get("confidence", 0.0)),
            reason_code=str(value.get("reason_code") or "policy_rule"),
            rationale=str(value.get("rationale") or ""),
            decision_id=str(value.get("decision_id") or ""),
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
]
