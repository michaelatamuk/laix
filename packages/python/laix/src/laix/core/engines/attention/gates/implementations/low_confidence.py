"""The host is not sure enough about the signal."""

from __future__ import annotations

from .....support.verbs import Verb
from ...input.context import Context
from ...input.signal import Signal
from ..result import GateResult
from ..reason import ReasonCode


def low_confidence(signal: Signal, context: Context, blocked: ReasonCode | None, delivered: int) -> GateResult | None:
    if signal.confidence < context.min_confidence:
        return GateResult(Verb.WAIT, ReasonCode.LOW_CONFIDENCE, False, False)
    return None

__all__ = ["low_confidence"]
