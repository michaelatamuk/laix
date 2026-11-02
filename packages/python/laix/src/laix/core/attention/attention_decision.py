"""What the attention policy recommends for one signal, and why."""

from __future__ import annotations

from dataclasses import dataclass

from ..decisions import Breakdown, Escalation, Intent


@dataclass(frozen=True, slots=True)
class AttentionDecision:
    """What the attention policy recommends for one signal, and why."""

    signal_id: str
    verb: str
    score: float
    reason_code: str
    confidence: float
    deliver: bool
    record: bool
    requires_approval: bool
    evidence_refs: tuple[str, ...]
    breakdown: Breakdown
    trace_id: str
    #: Carried for ``act`` and ``ask``; None otherwise.
    intent: Intent | None = None
    #: Carried for ``escalate``; None otherwise.
    escalation: Escalation | None = None
    #: Points at stake per hour of silence. 0 when there is no deadline.
    cost_of_waiting: float = 0.0
    #: Whether the requested action can be taken back.
    reversible: bool = False
    #: What the app can offer: "withdraw", "cancel", or nothing.
    undo_hint: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "verb": self.verb,
            "score": round(self.score, 2),
            "reason_code": self.reason_code,
            "confidence": round(self.confidence, 3),
            "deliver": self.deliver,
            "record": self.record,
            "requires_approval": self.requires_approval,
            "evidence_refs": list(self.evidence_refs),
            "trace_id": self.trace_id,
            "breakdown": self.breakdown.as_dict(),
            "intent": self.intent.as_dict() if self.intent else None,
            "escalation": self.escalation.as_dict() if self.escalation else None,
            "cost_of_waiting": round(self.cost_of_waiting, 2),
            "reversible": self.reversible,
            "undo_hint": self.undo_hint,
        }


__all__ = ["AttentionDecision"]
