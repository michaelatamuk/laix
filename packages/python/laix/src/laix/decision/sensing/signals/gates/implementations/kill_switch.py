"""Stop everything when the product is switched off."""

from __future__ import annotations

from .....support.verbs import Verb
from ...input.signal_context import SignalContext
from ...input.signal import Signal
from ..result import GateResult
from ..reason import ReasonCode


def kill_switch(signal: Signal, context: SignalContext, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if context.stopped:
        return GateResult(Verb.WAIT, ReasonCode.KILL_SWITCH, False, False)
    return None

__all__ = ["kill_switch"]
