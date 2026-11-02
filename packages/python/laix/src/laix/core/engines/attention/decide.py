"""The attention algorithm: one signal in, one AttentionDecision out.

This is the file to read first. ``decide_one`` applies the gates in fixed order
from ``gates.py``, then fills the decision from ``score.py``. ``decide_attention``
is only the loop around it.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from datetime import datetime

from .gates import GATE_RULES, GateResult, ReasonCode, dedupe_key, feedback_blocks, rank
from .input.context import Context
from .output.decision import AttentionDecision
from .input.signal import Signal
from .score import cost_of_waiting, score
from .output.undo import undo_hint
from ...support.verbs import Verb


def dedupe_key(signal: Signal, now: datetime) -> str:
    """One interruption per signal per day, by default."""
    return f"{signal.id}:{now.date().isoformat()}"


def trace_id(signal: Signal, now: datetime, verb: str) -> str:
    raw = f"{signal.id}|{now.date().isoformat()}|{verb}".encode()
    return "tr-" + hashlib.sha1(raw).hexdigest()[:12]


def decide_one(signal: Signal, context: Context, delivered: int = 0) -> AttentionDecision:
    """Decide one signal by walking ``GATE_RULES`` in order."""
    breakdown = score(signal, context)
    blocked = feedback_blocks(context.feedback.get(signal.id), context.now)

    result: GateResult | None = None
    for _gate, rule in GATE_RULES:
        result = rule(signal, context, blocked, delivered)  # type: ignore[operator]
        if result is not None:
            break
    if result is None:
        result = GateResult(Verb.GUIDE, ReasonCode.WORTH_SURFACING, True, True)

    return AttentionDecision(
        signal_id=signal.id,
        verb=result.verb,
        score=breakdown.total,
        reason_code=result.reason_code,
        confidence=signal.confidence,
        deliver=result.deliver,
        record=result.record,
        requires_approval=signal.requires_approval,
        evidence_refs=signal.evidence_refs,
        breakdown=breakdown,
        trace_id=trace_id(signal, context.now, result.verb),
        intent=(
            signal.handover
            if result.verb == Verb.ESCALATE
            else (signal.intent if result.verb in {Verb.ACT, Verb.ASK} else None)
        ),
        cost_of_waiting=cost_of_waiting(signal, context),
        reversible=signal.reversible,
        undo_hint=undo_hint(result.verb, signal.reversible),
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
