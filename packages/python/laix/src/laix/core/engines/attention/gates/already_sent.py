"""The same signal was already delivered today."""

from __future__ import annotations

from ....support.verbs import Verb
from ..model.context import Context
from ..model.signal import Signal
from .gate_result import GateResult
from .helpers import dedupe_key
from .reasons import ReasonCode


def already_sent(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if dedupe_key(signal, context.now) in context.sent:
        return GateResult(Verb.WAIT, ReasonCode.ALREADY_SENT, False, False)
    return None

__all__ = ["already_sent"]
