"""The same signal was already delivered today."""

from __future__ import annotations

from .....support.verbs import Verb
from ...input.context import Context
from ...input.signal import Signal
from ..result import GateResult
from ...input.dedupe import dedupe_key
from ..reason import ReasonCode


def already_sent(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if dedupe_key(signal, context.now) in context.sent:
        return GateResult(Verb.WAIT, ReasonCode.ALREADY_SENT, False, False)
    return None

__all__ = ["already_sent"]
