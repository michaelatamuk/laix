"""A critical deadline passed the escalation window."""

from __future__ import annotations

from ....support.verbs import Verb
from ..model.context import Context
from ..model.signal import Signal
from .gate_result import GateResult
from ..timing import hours_until
from .reasons import ReasonCode


def overdue_escalation(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if context.escalate_after_hours is None or signal.severity != "critical":
        return None
    hours = hours_until(context.now, signal.due)
    if hours is not None and -hours > context.escalate_after_hours:
        return GateResult(Verb.ESCALATE, ReasonCode.OVERDUE_ESCALATION, True, True)
    # Critical with an escalation window but not overdue stays a guide;
    # it must not fall through to the act gate.
    return GateResult(Verb.GUIDE, ReasonCode.WORTH_SURFACING, True, True)

__all__ = ["overdue_escalation"]
