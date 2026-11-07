"""Normalise any policy result into the one public ``Decision`` shape."""

from __future__ import annotations

from typing import Any, Iterable

from ..support.errors import DecisionPolicyError
from ..support.verbs import Verb
from .response import EvidenceRef, Intent, ScoreBreakdown
from .response.decision import Decision


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


def _breakdown(value: Any) -> ScoreBreakdown | None:
    if value is None:
        return None
    if isinstance(value, ScoreBreakdown):
        return value
    data = value if isinstance(value, dict) else getattr(value, "as_dict", lambda: {})()
    return ScoreBreakdown(
        severity=float(data.get("severity", 0.0)),
        due=float(data.get("due", 0.0)),
        confidence=float(data.get("confidence", 0.0)),
        interruption=float(data.get("interruption", 0.0)),
        learned=float(data.get("learned", 0.0)),
        total=float(data.get("total", 0.0)),
    )


def from_signal_attention(decision: Any) -> Decision:
    """Convert an ``SignalAttentionDecision`` without importing the attention package."""
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
        return from_signal_attention(value)
    if isinstance(value, dict):
        return Decision(
            verb=str(value.get("verb") or Verb.WAIT),
            confidence=float(value.get("confidence", 0.0)),
            reason_code=str(value.get("reason_code") or "policy_rule"),
            rationale=str(value.get("rationale") or ""),
            decision_id=str(value.get("decision_id") or ""),
            requires_approval=bool(value.get("requires_approval", False)),
            score=value.get("score"),
            trace_id=str(value.get("trace_id", "")),
            deliver=bool(value.get("deliver", True)),
            record=bool(value.get("record", True)),
            stream_id=str(value.get("stream_id", "")),
            event_time=value.get("event_time"),
            deadline=value.get("deadline"),
            valid_until=value.get("valid_until"),
            supersedes=value.get("supersedes"),
            revision=int(value.get("revision") or 0),
            status=str(value.get("status") or "final"),
            target=str(value.get("target") or "one"),
            recipients=tuple(value.get("recipients", ())),
        )
    raise DecisionPolicyError(f"policy returned an unsupported decision: {type(value).__name__}")


__all__ = ["coerce", "from_signal_attention"]
