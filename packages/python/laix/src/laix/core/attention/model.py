"""Domain-neutral types for the attention policy.

Nothing in this file knows what the app is about. An app supplies signals; the
policy returns decisions; the app records outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ..contracts import VERBS, Breakdown, Escalation, Intent

SEVERITY_RANK: dict[str, int] = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
RESULTS: tuple[str, ...] = ("helped", "neutral", "hurt", "unknown")
FEEDBACK_STATES: tuple[str, ...] = ("accepted", "dismissed", "snoozed", "wrong", "assigned")
REASON_CODES: tuple[str, ...] = (
    "false_alarm",
    "design_change",
    "operational",
    "duplicate",
    "no_action",
    "data_error",
)


@dataclass(frozen=True, slots=True)
class Feedback:
    """What the user has already said about this signal.

    ``snoozed`` needs ``until``; ``accepted`` never suppresses; ``wrong`` and
    ``assigned`` and ``dismissed`` do.
    """

    state: str
    at: str | None = None
    until: str | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class Signal:
    """One thing that might deserve the user's attention."""

    id: str
    kind: str
    title: str = ""
    detail: str = ""
    severity: str = "low"
    confidence: float = 0.5
    due: str | None = None
    evidence_refs: tuple[str, ...] = ()
    group_key: str | None = None
    interruption_cost: float = 0.0
    requires_approval: bool = False
    #: The action the app is prepared to take. ``None`` means "guide only".
    intent: Intent | None = None
    #: Whether an executed action can be taken back.
    reversible: bool = False
    #: Who to escalate to when the signal stays overdue.
    escalation: Escalation | None = None


@dataclass(slots=True)
class Context:
    """Everything the policy needs that is not the signal itself."""

    now: datetime
    quiet_hours: tuple[str, str] | None = ("22:00", "06:00")
    mode: str = "shadow"
    stopped: bool = False
    min_severity: str = "high"
    min_confidence: float = 0.0
    muted_kinds: tuple[str, ...] = ()
    # Deliver at most this many signals per decision cycle. None means no cap.
    interruption_budget: int | None = None
    # Dedupe keys already delivered in this period, for example "signal-1:2026-11-14".
    sent: frozenset[str] = frozenset()
    # What the user already said, keyed by signal id.
    feedback: dict[str, Feedback] = field(default_factory=dict)
    # Escalate a critical signal that is older than this many hours. None disables it.
    escalate_after_hours: float | None = None
    # Learned per-kind point adjustment, supplied by the app or a bandit.
    learned: dict[str, float] = field(default_factory=dict)
    # When true and the signal carries a reversible intent, the policy may act
    # or ask instead of only notifying. Off by default.
    allow_act: bool = False


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


@dataclass(frozen=True, slots=True)
class AttentionOutcome:
    """What happened after an attention decision. The label the learner needs."""

    signal_id: str
    kind: str
    verb: str
    result: str
    reason_code: str | None = None
    score: float | None = None
    at: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "signal_id": self.signal_id,
            "kind": self.kind,
            "verb": self.verb,
            "result": self.result,
            "reason_code": self.reason_code,
            "score": self.score,
            "at": self.at,
        }
