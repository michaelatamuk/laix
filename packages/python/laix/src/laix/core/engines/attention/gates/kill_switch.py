"""Stop everything when the product is switched off."""

from __future__ import annotations

from ....support.verbs import Verb
from ..model.context import Context
from ..model.signal import Signal
from .gate_result import GateResult
from .reasons import ReasonCode


def kill_switch(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if context.stopped:
        return GateResult(Verb.WAIT, ReasonCode.KILL_SWITCH, False, False)
    return None

__all__ = ["kill_switch"]
