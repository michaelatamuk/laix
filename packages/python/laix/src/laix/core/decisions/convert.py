"""Normalise any policy result into the one public ``Decision`` shape."""

from __future__ import annotations

from typing import Any, Iterable

from ..errors import PolicyError
from .breakdown import Breakdown
from .decision import Decision
from .escalation import Escalation
from .evidence_ref import EvidenceRef
from .intent import Intent


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


__all__ = ["coerce", "from_attention"]
