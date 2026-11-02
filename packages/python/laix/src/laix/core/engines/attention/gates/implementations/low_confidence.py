"""The host is not sure enough about the signal."""

from __future__ import annotations

from .....support.verbs import Verb
from ...model.context import Context
from ...model.signal import Signal
from ..gate_result import GateResult
from ..reasons import ReasonCode


def low_confidence(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if signal.confidence < context.min_confidence:
        return GateResult(Verb.WAIT, ReasonCode.LOW_CONFIDENCE, False, False)
    return None

__all__ = ["low_confidence"]
