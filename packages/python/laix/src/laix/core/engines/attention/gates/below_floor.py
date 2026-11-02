"""The signal is less severe than the context floor."""

from __future__ import annotations

from ....support.verbs import Verb
from ..model.context import Context
from ..model.signal import Signal
from .gate_result import GateResult
from .helpers import rank
from .reasons import ReasonCode


def below_floor(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if rank(signal.severity) > rank(context.min_severity):
        return GateResult(Verb.WAIT, ReasonCode.BELOW_FLOOR, False, False)
    return None

__all__ = ["below_floor"]
