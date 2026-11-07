"""The signal is less severe than the context floor."""

from __future__ import annotations

from .....support.verbs import Verb
from ...input.signal_context import SignalContext
from ...input.signal import Signal
from ..result import GateResult
from ...input.severity import rank
from ..reason import ReasonCode


def below_floor(signal: Signal, context: SignalContext, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if rank(signal.severity) > rank(context.min_severity):
        return GateResult(Verb.WAIT, ReasonCode.BELOW_FLOOR, False, False)
    return None

__all__ = ["below_floor"]
