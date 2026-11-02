"""The attention algorithm: one signal in, one AttentionDecision out.

This is the file to read first. ``decide_one`` applies the gates in fixed order
from ``gates.py``, then fills the decision from ``score.py``. ``decide_attention``
is only the loop around it.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from datetime import datetime

from .gates import ReasonCode, feedback_blocks, rank
from .model.context import Context
from .model.decision import AttentionDecision
from .model.signal import Signal
from .score import cost_of_waiting, score, undo_hint
from .timing import hours_until, is_quiet
from ...support.verbs import Verb


def dedupe_key(signal: Signal, now: datetime) -> str:
    """One interruption per signal per day, by default."""
    return f"{signal.id}:{now.date().isoformat()}"


def trace_id(signal: Signal, now: datetime, verb: str) -> str:
    raw = f"{signal.id}|{now.date().isoformat()}|{verb}".encode()
    return "tr-" + hashlib.sha1(raw).hexdigest()[:12]


def decide_one(signal: Signal, context: Context, delivered: int = 0) -> AttentionDecision:
    """Decide one signal. Gate order is the behaviour; score is the record."""
    breakdown = score(signal, context)
    blocked = feedback_blocks(context.feedback.get(signal.id), context.now)

    verb, reason_code, record, deliver = Verb.GUIDE, ReasonCode.WORTH_SURFACING, True, True
    delivered_now = delivered

    if context.stopped:
        verb, reason_code, record, deliver = Verb.WAIT, ReasonCode.KILL_SWITCH, False, False
    elif signal.kind in context.muted_kinds:
        verb, reason_code, record, deliver = Verb.WAIT, ReasonCode.MUTED, False, False
    elif blocked is not None:
        verb, reason_code, record, deliver = Verb.WAIT, blocked, False, False
    elif signal.confidence < context.min_confidence:
        verb, reason_code, record, deliver = Verb.WAIT, ReasonCode.LOW_CONFIDENCE, False, False
    elif rank(signal.severity) > rank(context.min_severity):
        verb, reason_code, record, deliver = Verb.WAIT, ReasonCode.BELOW_FLOOR, False, False
    elif dedupe_key(signal, context.now) in context.sent:
        verb, reason_code, record, deliver = Verb.WAIT, ReasonCode.ALREADY_SENT, False, False
    elif is_quiet(context.now, context.quiet_hours) and signal.severity != "critical":
        verb, reason_code, record, deliver = Verb.WAIT, ReasonCode.QUIET_HOURS, True, False
    elif context.interruption_budget is not None and delivered_now >= context.interruption_budget:
        verb, reason_code, record, deliver = Verb.WAIT, ReasonCode.BUDGET, False, False
    elif context.escalate_after_hours is not None and signal.severity == "critical":
        hours = hours_until(context.now, signal.due)
        if hours is not None and -hours > context.escalate_after_hours:
            verb, reason_code, record, deliver = Verb.ESCALATE, ReasonCode.OVERDUE_ESCALATION, True, True
    elif context.allow_act and signal.intent is not None and signal.reversible:
        verb, reason_code = Verb.ACT, ReasonCode.ACT
    else:
        delivered_now += 1

    return AttentionDecision(
        signal_id=signal.id,
        verb=verb,
        score=breakdown.total,
        reason_code=reason_code,
        confidence=signal.confidence,
        deliver=deliver,
        record=record,
        requires_approval=signal.requires_approval,
        evidence_refs=signal.evidence_refs,
        breakdown=breakdown,
        trace_id=trace_id(signal, context.now, verb),
        intent=signal.handover if verb == Verb.ESCALATE else (signal.intent if verb in {Verb.ACT, Verb.ASK} else None),
        cost_of_waiting=cost_of_waiting(signal, context),
        reversible=signal.reversible,
        undo_hint=undo_hint(verb, signal.reversible),
    )


def decide_attention(signals: Iterable[Signal], context: Context) -> list[AttentionDecision]:
    """Return one decision per signal, in input order."""
    out: list[AttentionDecision] = []
    delivered = 0
    for signal in signals:
        decision = decide_one(signal, context, delivered)
        if decision.deliver:
            delivered += 1
        out.append(decision)
    return out


def rollup(signals: Sequence[Signal], limit: int = 5) -> list[Signal]:
    """The most severe signals first, then the soonest due. Used for digests."""
    return sorted(signals, key=lambda s: (rank(s.severity), s.due or "9999"))[:limit]
